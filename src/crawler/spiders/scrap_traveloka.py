import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union

class TravelokaParser:
    def __init__(self):
        self.base_url = "https://www.traveloka.com"

    def clean_html_text(self, html_text: str) -> str:
        """Membersihkan tag HTML untuk deskripsi teks bersih (RAG friendly)."""
        if not html_text: return ""
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ')
        # Membersihkan spasi berlebih
        return ' '.join(text.split())

    def parse_currency(self, value: str) -> int:
        """Mengubah string harga (Rp 1.500.000) menjadi integer."""
        if not value: return 0
        # Hapus 'Rp', titik, spasi, dan karakter non-digit
        clean_str = re.sub(r'[^\d]', '', str(value))
        return int(clean_str) if clean_str else 0

    def parse_next_data(self, html_content: str) -> dict:
        """Mengekstrak JSON __NEXT_DATA__ dari HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        script = soup.find('script', id='__NEXT_DATA__')
        if script:
            return json.loads(script.string)
        return {}

    def parse_list_page(self, html_content: str) -> List[Dict]:
        """Analisa Halaman 1 (List Hotel)."""
        data = self.parse_next_data(html_content)
        results = []
        
        # Navigasi ke path data hotel list (sesuai struktur Traveloka)
        # Fallback ke parsing DOM jika JSON tidak memiliki list inventory langsung
        # (Seringkali list inventory ada di DOM untuk SEO)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Mencari container hotel berdasarkan analisis sebelumnya
        cards = soup.find_all('div', attrs={"data-testid": lambda x: x and x.startswith("popular-hotel-card-container-")})
        
        for card in cards:
            try:
                # Extract ID from testid
                hotel_id_raw = card.get('data-testid', '').replace('popular-hotel-card-container-', '')
                
                # Extract Basic Info
                name_tag = card.find(attrs={"data-testid": "popular-hotel-card-name"})
                name = name_tag.text.strip() if name_tag else "Unknown"
                
                type_tag = card.find(attrs={"data-testid": "popular-hotel-accommodation-type"})
                acc_type = type_tag.text.strip() if type_tag else "Hotel"
                
                rating_tag = card.find(attrs={"data-testid": "popular-hotel-rating"})
                rating = float(rating_tag.text.strip()) if rating_tag else 0.0
                
                review_count_tag = card.find(attrs={"data-testid": "popular-hotel-total-review"})
                review_count = int(re.sub(r'[^\d]', '', review_count_tag.text)) if review_count_tag else 0
                
                price_tag = card.find(attrs={"data-testid": "popular-hotel-price"})
                price = self.parse_currency(price_tag.text) if price_tag else 0
                
                # Link Detail
                link_tag = card.find('a', href=True)
                detail_url = self.base_url + link_tag['href'] if link_tag else ""

                results.append({
                    "hotel_id": int(hotel_id_raw) if hotel_id_raw.isdigit() else hotel_id_raw,
                    "name": name,
                    "type": acc_type,
                    "rating": rating,
                    "total_reviews": review_count,
                    "price_per_night": price,
                    "detail_url": detail_url
                })
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue
                
        return results

    def parse_detail_page(self, html_content: str) -> Dict:
        """Analisa Halaman 2 (Detail Hotel) - Ekstraksi Deep Data."""
        json_data = self.parse_next_data(html_content)
        
        # Navigasi ke objek utama hotel di JSON
        # Path biasanya: props -> pageProps -> hotel
        try:
            hotel_data = json_data.get('props', {}).get('pageProps', {}).get('hotel', {})
        except AttributeError:
            return {"error": "Invalid JSON Structure"}

        if not hotel_data:
            return {"error": "Hotel data not found in JSON"}

        # 1. Informasi Dasar
        basic_info = {
            "hotel_id": hotel_data.get('id'),
            "name": hotel_data.get('displayName'),
            "type": hotel_data.get('accomPropertyType', 'Hotel'),
            "star_rating": float(hotel_data.get('starRating', 0)),
            "address": hotel_data.get('address'),
            "postal_code": hotel_data.get('postalCode'),
            "coordinates": {
                "latitude": float(hotel_data.get('latitude', 0) or 0),
                "longitude": float(hotel_data.get('longitude', 0) or 0)
            }
        }

        # 2. Fasilitas (Dikelompokkan)
        # Mengambil dari hotelFacilitiesCategoriesDisplay agar terstruktur
        facilities = {}
        raw_cats = hotel_data.get('hotelFacilitiesCategoriesDisplay', [])
        for cat in raw_cats:
            cat_name = cat.get('name')
            items = [item.get('name') for item in cat.get('hotelFacilityDisplays', [])]
            facilities[cat_name] = items

        # 3. Kebijakan (Check-in/Out)
        policies = {
            "check_in_time": hotel_data.get('properties', {}).get('checkInTime'),
            "check_out_time": hotel_data.get('properties', {}).get('checkOutTime'),
            "instructions": []
        }
        # Mengambil instruksi check-in dari bagian policy
        raw_policies = hotel_data.get('hotelPolicy', {}).get('policies', [])
        for pol in raw_policies:
            if pol.get('policyTitle'):
                policies['instructions'].append({
                    "title": pol.get('policyTitle'),
                    "description": self.clean_html_text(pol.get('policyDescription', ''))
                })

        # 4. Deskripsi (Sangat penting untuk RAG context)
        description = self.clean_html_text(hotel_data.get('attribute', {}).get('description', ''))
        # Fallback ke overview jika description kosong
        if not description:
            description = self.clean_html_text(hotel_data.get('attribute', {}).get('overview', ''))

        # 5. Review Summary
        review_data = hotel_data.get('reviewSummary', {}).get('ugcReviewSummary', {})
        reviews = {
            "score": float(review_data.get('userRating', 0) or 0),
            "count": int(review_data.get('numReviews', 0) or 0),
            "summary_text": review_data.get('userRatingInfo')
        }

        # 6. Room Types & Prices (Ekstraksi dari JSON atau Fallback ke Text)
        # Pada JSON yang dikirim, list kamar eksplisit di 'inventory' mungkin kosong (dynamic load).
        # Kita akan mencoba mengambil dari bagian 'seoDiscoverContent' jika tersedia, 
        # atau membiarkannya kosong agar diisi oleh proses booking engine nanti.
        # Namun, di HTML Anda ada teks "Tipe kamar yang tersedia...".
        # Kita coba ambil harga dasar.
        base_rate = hotel_data.get('rateDisplay', {})
        price_min = self.parse_currency(base_rate.get('totalFare') or base_rate.get('baseFare'))

        # Construct Final JSON
        final_data = {
            **basic_info,
            "rating_data": reviews,
            "price_info": {
                "price_min_per_night": price_min,
                "currency": "IDR" # Asumsi default berdasarkan HTML lang
            },
            "facilities_grouped": facilities,
            "policies": policies,
            "description_text": description,
            # Data tambahan untuk RAG context building
            "context_string": f"{basic_info['name']} adalah {basic_info['type']} bintang {basic_info['star_rating']} yang berlokasi di {basic_info['address']}. {description}"
        }

        return final_data
