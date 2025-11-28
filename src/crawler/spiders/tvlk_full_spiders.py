# import scrapy
# import json
# import os
# import time
# import re
# from datetime import datetime
# from scrapy_selenium import SeleniumRequest
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup

# class TvlkFullSpider(scrapy.Spider):
#     name = "tvlk_full"
    
#     # Set global untuk menghindari duplikasi hotel
#     seen_hotel_ids = set()

#     custom_settings = {
#         'DOWNLOAD_DELAY': 3,
#         'RANDOMIZE_DOWNLOAD_DELAY': True,
#         'CONCURRENT_REQUESTS': 1,
#         'DEFAULT_REQUEST_HEADERS': {
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#         },
#         'FEEDS': {
#             'data/output/data_hotel_final.jsonl': {
#                 'format': 'jsonlines',
#                 'encoding': 'utf8',
#                 'overwrite': True
#             },
#             'data/output/data_hotel_final.json': {
#                 'format': 'json',
#                 'encoding': 'utf8',
#                 'overwrite': True,
#                 'indent': 4
#             }
#         },
#         'LOG_LEVEL': 'INFO' 
#     }

#     def start_requests(self):
#         # --- MODE PENGUJIAN (Hardcoded URL) ---
#         # Komentar bagian JSON di bawah untuk menggunakan mode ini
#         test_urls = [
#             'https://www.traveloka.com/id-id/hotel/indonesia/city/subang-104594'
#         ]
        
#         for url in test_urls:
#             yield SeleniumRequest(
#                 url=url,
#                 callback=self.parse_list_page,
#                 wait_time=10,
#                 meta={'page_depth': 1}
#             )

#         # --- MODE PRODUKSI (Baca dari JSON) ---
#         # Uncomment kode di bawah ini jika sudah siap crawling massal
#         """
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
#         json_path = os.path.join(project_root, "config", "lokasi_traveloka.json")
        
#         if os.path.exists(json_path):
#             with open(json_path, 'r', encoding='utf-8') as f:
#                 raw_data = json.load(f)
            
#             urls_to_scrape = []
#             if isinstance(raw_data, list):
#                 for entry in raw_data:
#                     results = entry.get('organicResults', []) 
#                     for res in results:
#                         url = res.get('url')
#                         if url and "traveloka.com" in url and ("/city/" in url or "/region/" in url or "/area/" in url):
#                             clean_url = url.split('?')[0].split('#')[0]
#                             urls_to_scrape.append(clean_url)
            
#             urls_to_scrape = list(set(urls_to_scrape))
#             for url in urls_to_scrape:
#                 yield SeleniumRequest(
#                     url=url,
#                     callback=self.parse_list_page,
#                     wait_time=10,
#                     meta={'page_depth': 1}
#                 )
#         """

#     # --- UTILITY FUNCTIONS ---
#     def clean_text(self, text):
#         if not text: return ""
#         return ' '.join(text.split())

#     def parse_currency(self, value):
#         if not value: return 0
#         clean = re.sub(r'[^\d]', '', str(value))
#         return int(clean) if clean else 0

#     def get_next_data(self, page_source):
#         soup = BeautifulSoup(page_source, 'html.parser')
#         script = soup.find('script', id='__NEXT_DATA__')
#         if script:
#             return json.loads(script.string)
#         return {}

#     # --- PARSING KAMAR DARI DOM (Sesuai HTML User) ---
#     def extract_rooms_detailed(self, soup):
#         rooms = []
#         # Cari Group Kamar (Container utama per tipe kamar)
#         # Selector: div[data-testid="room_inventory_group_card"]
#         group_cards = soup.find_all('div', attrs={"data-testid": "room_inventory_group_card"})
        
#         for group in group_cards:
#             try:
#                 # 1. Nama Kamar Utama (Group)
#                 # Selector: h3[data-testid^="room-name-"]
#                 name_tag = group.find('h3', attrs={"data-testid": lambda x: x and x.startswith("room-name-")})
#                 group_name = self.clean_text(name_tag.text) if name_tag else "Kamar"
                
#                 # 2. Luas Kamar (Cari Icon Measure)
#                 # Logic: Cari SVG Measure -> Parent -> Sibling Div -> Text
#                 room_size = ""
#                 measure_icon = group.find('svg', attrs={"data-id": "IcHotelRoomMeasure"})
#                 if measure_icon:
#                     # Biasanya text ada di div sebelah icon (sibling)
#                     size_div = measure_icon.parent.find_next_sibling('div')
#                     if size_div:
#                         # Cari div text di dalamnya
#                         txt_node = size_div.find('div', dir="auto")
#                         if txt_node: room_size = txt_node.text.strip()

#                 # 3. Loop Varian/Opsi Kamar (Card di dalam Group)
#                 # Selector: div[data-testid="room_inventory_card"]
#                 variants = group.find_all('div', attrs={"data-testid": "room_inventory_card"})
                
#                 for variant in variants:
#                     # Nama Varian (e.g., Room only, Breakfast included)
#                     var_name_tag = variant.find('div', attrs={"data-testid": "room_inventory_name"})
#                     var_name = self.clean_text(var_name_tag.text) if var_name_tag else group_name
                    
#                     # Info Makan (Breakfast)
#                     meal_tag = variant.find('div', attrs={"data-testid": "room_inventory_breakfast"})
#                     meal_info = self.clean_text(meal_tag.text) if meal_tag else "Tanpa info makan"
                    
#                     # Info Kasur
#                     bed_tag = variant.find('div', attrs={"data-testid": "room_inventory_bed_type"})
#                     bed_info = self.clean_text(bed_tag.text) if bed_tag else "-"
                    
#                     # Kebijakan Pembatalan
#                     policy_tag = variant.find('div', attrs={"data-testid": "text_cancellation_policy"})
#                     policy_info = self.clean_text(policy_tag.text) if policy_tag else "-"

#                     # Harga
#                     price_tag = variant.find('div', attrs={"data-testid": "room_inventory_cheapest_rate"})
#                     # Fallback jika harga cheapest tidak ada (biasanya ada original rate)
#                     if not price_tag:
#                         price_tag = variant.find('div', attrs={"data-testid": lambda x: x and x.startswith("inv-original-rate-")})
                    
#                     raw_price = price_tag.text.strip() if price_tag else "0"
#                     price_int = self.parse_currency(raw_price)
                    
#                     if price_int > 0:
#                         rooms.append({
#                             "tipe_kamar": var_name, # Nama spesifik varian
#                             "kategori_kamar": group_name, # Nama grup kamar
#                             "harga": price_int,
#                             "luas": room_size,
#                             "kasur": bed_info,
#                             "makan": meal_info,
#                             "kebijakan": policy_info
#                         })
#             except Exception as e:
#                 continue
#         return rooms

#     # --- PARSING HALAMAN LIST (STRICT SCOPING) ---
#     def parse_list_page(self, response):
#         driver = response.meta['driver']
#         depth = response.meta.get('page_depth', 1)
        
#         self.logger.info(f"[*] Processing List Page {depth}: {response.url}")

#         # Scroll untuk trigger lazy load
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(3)
        
#         soup = BeautifulSoup(driver.page_source, 'html.parser')
        
#         # --- STRICT SCOPING ---
#         # Hanya cari di dalam container list utama: div[data-testid="popular-hotel-list"]
#         # Ini MENCEGAH pengambilan data dari "Rekomendasi" atau "Hotel Serupa" di bawah
#         main_list_container = soup.find('div', attrs={"data-testid": "popular-hotel-list"})
        
#         hotel_list = []
        
#         if main_list_container:
#             # Cari card hanya di dalam container ini
#             cards = main_list_container.find_all('div', attrs={"data-testid": lambda x: x and x.startswith("popular-hotel-card-container-")})
            
#             for card in cards:
#                 # Ambil ID dari testid
#                 h_id = card.get('data-testid').replace('popular-hotel-card-container-', '')
                
#                 # Ambil Link
#                 link_tag = card.find('a', href=True)
#                 if link_tag and h_id:
#                     full_url = "https://www.traveloka.com" + link_tag['href'] if link_tag['href'].startswith('/') else link_tag['href']
#                     # Bersihkan URL
#                     full_url = full_url.split('?')[0]
                    
#                     if h_id not in self.seen_hotel_ids:
#                         self.seen_hotel_ids.add(h_id)
#                         hotel_list.append(full_url)
#         else:
#             self.logger.warning("[!] Container popular-hotel-list tidak ditemukan! Mungkin struktur berubah atau IP terblokir.")

#         self.logger.info(f"[+] Halaman {depth}: Ditemukan {len(hotel_list)} hotel valid.")

#         # Crawl Detail Hotel
#         for url in hotel_list:
#             yield SeleniumRequest(
#                 url=url,
#                 callback=self.parse_detail_page,
#                 wait_time=10 # Tunggu detail load
#             )

#         # --- PAGINATION LOGIC ---
#         # Cek tombol Next
#         if len(hotel_list) > 0:
#             next_btn = soup.find('div', attrs={"data-testid": "next-page-btn"})
#             is_active = next_btn and next_btn.get('aria-disabled') != 'true'
            
#             if is_active:
#                 current_url = response.url
#                 match = re.search(r'/(\d+)$', current_url)
                
#                 # Cek apakah URL diakhiri angka halaman (1-3 digit)
#                 # Hindari menganggap ID kota (6 digit) sebagai halaman
#                 if match and len(match.group(1)) <= 3:
#                     next_page = int(match.group(1)) + 1
#                     next_url = re.sub(r'/\d+$', f'/{next_page}', current_url)
#                 else:
#                     # Jika belum ada nomor halaman
#                     next_url = f"{current_url.rstrip('/')}/2"
                
#                 self.logger.info(f"[->] Lanjut ke Halaman {depth + 1}")
#                 yield SeleniumRequest(
#                     url=next_url,
#                     callback=self.parse_list_page,
#                     wait_time=10,
#                     meta={'page_depth': depth + 1}
#                 )
#             else:
#                 self.logger.info("[|] Pagination Selesai.")

#     # --- PARSING HALAMAN DETAIL ---
#     def parse_detail_page(self, response):
#         driver = response.meta['driver']
        
#         # Scroll Agresif untuk Load Kamar & Review
#         try:
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
#             time.sleep(1)
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
#             time.sleep(1)
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#             time.sleep(2)
#         except: pass
        
#         soup = BeautifulSoup(driver.page_source, 'html.parser')
#         next_data = self.get_next_data(driver.page_source)
        
#         try:
#             hotel_data = next_data.get('props', {}).get('pageProps', {}).get('hotel', {})
#             if not hotel_data:
#                 return

#             # --- 1. DATA UTAMA (JSON) ---
#             item = {
#                 "hotel_id": int(hotel_data.get('id', 0)),
#                 "nama_akomodasi": hotel_data.get('displayName'),
#                 "tipe_akomodasi": hotel_data.get('accomPropertyType', 'Hotel'),
#                 "sumber_url": response.url,
#                 "alamat_lengkap": hotel_data.get('address'),
#                 "kota": hotel_data.get('city'),
#                 "region": hotel_data.get('region'),
#                 "koordinat": {
#                     "lat": float(hotel_data.get('latitude', 0) or 0),
#                     "lon": float(hotel_data.get('longitude', 0) or 0)
#                 },
#                 "bintang_rating": float(hotel_data.get('starRating', 0)),
#                 "rating_review": 0.0,
#                 "jumlah_ulasan": 0,
#                 "harga_min": 0,
#                 "fasilitas": {},
#                 "kamar": [],
#                 "kebijakan": [],
#                 "lokasi_sekitar": [],
#                 "deskripsi_akomodasi": "",
#                 "konteks_rag": ""
#             }

#             # Review
#             rev = hotel_data.get('reviewSummary', {}).get('ugcReviewSummary', {})
#             item['rating_review'] = float(rev.get('userRating', 0) or 0)
#             item['jumlah_ulasan'] = int(rev.get('numReviews', 0) or 0)
#             item['teks_rating'] = rev.get('userRatingInfo', '')

#             # Fasilitas (Dari JSON lebih lengkap)
#             cats = hotel_data.get('hotelFacilitiesCategoriesDisplay', [])
#             for cat in cats:
#                 item['fasilitas'][cat.get('name')] = [x.get('name') for x in cat.get('hotelFacilityDisplays', [])]

#             # --- 2. DATA DETAIL (DOM - Sesuai Request HTML User) ---
            
#             # A. Deskripsi (About)
#             # Selector: div[data-testid="about-content"]
#             about_div = soup.find('div', attrs={"data-testid": "about-content"})
#             if about_div:
#                 # Ambil text bersih dari HTML deskripsi
#                 item['deskripsi_akomodasi'] = self.clean_text(about_div.get_text(separator=' '))
#             else:
#                 item['deskripsi_akomodasi'] = self.clean_text(hotel_data.get('attribute', {}).get('description', ''))

#             # B. Kamar (Room List) - Pake fungsi baru
#             item['kamar'] = self.extract_rooms_detailed(soup)
            
#             # Set Harga Min dari data kamar
#             if item['kamar']:
#                 item['harga_min'] = min([k['harga'] for k in item['kamar']])
#             else:
#                 # Fallback JSON
#                 rate = hotel_data.get('rateDisplay', {})
#                 item['harga_min'] = self.parse_currency(rate.get('totalFare') or rate.get('baseFare'))

#             # C. Lokasi Sekitar (Nearby)
#             # Selector: div[data-testid="section-location"]
#             loc_section = soup.find('div', attrs={"data-testid": "section-location"})
#             if loc_section:
#                 # Cari kategori (Landmark, Culinary, dll)
#                 # Selector: div[data-testid^="location-landmark-category-"]
#                 cats = loc_section.find_all('div', attrs={"data-testid": lambda x: x and x.startswith("location-landmark-category-")})
#                 for cat in cats:
#                     # Ambil nama kategori dari header di dalamnya jika ada, atau ID
#                     # Loop item di dalamnya
#                     # Item biasanya ada di div dengan class css-cens5h (nama) dan css-1w9mtv9 (jarak)
#                     # Karena class acak, kita pake struktur relatif
#                     rows = cat.find_all('div', attrs={"class": "css-1dbjc4n r-zo7nv5 r-18u37iz r-1wtj0ep"}) # Row container
#                     for row in rows:
#                         cols = row.find_all('div', recursive=False)
#                         if len(cols) >= 2:
#                             place_name = cols[0].get_text().strip()
#                             distance_txt = cols[1].get_text().strip()
                            
#                             # Parse jarak
#                             dist_val = 0.0
#                             if 'km' in distance_txt:
#                                 dist_val = float(re.sub(r'[^\d\.]', '', distance_txt))
#                             elif 'm' in distance_txt:
#                                 dist_val = float(re.sub(r'[^\d\.]', '', distance_txt)) / 1000
                            
#                             item['lokasi_sekitar'].append({
#                                 "nama": place_name,
#                                 "jarak_km": dist_val
#                             })
            
#             # D. Kebijakan (Policy)
#             # Selector: div[data-testid="section-policy"]
#             # Ambil Waktu Check-in/out dari tabel
#             policy_section = soup.find('div', attrs={"data-testid": "section-policy"})
#             if policy_section:
#                 # Cari tabel
#                 rows = policy_section.find_all('tr')
#                 for r in rows:
#                     cols = r.find_all('td')
#                     if len(cols) == 2:
#                         key = self.clean_text(cols[0].text)
#                         val = self.clean_text(cols[1].text)
#                         item['kebijakan'].append(f"{key}: {val}")

#             # --- 3. RAG CONTEXT ---
#             fac_summary = ", ".join(list(item['fasilitas'].keys())[:4])
#             nearby_summary = ", ".join([p['nama'] for p in item['lokasi_sekitar'][:3]])
            
#             item['konteks_rag'] = (
#                 f"{item['nama_akomodasi']} adalah {item['tipe_akomodasi']} bintang {item['bintang_rating']} "
#                 f"di {item['kota']}. Harga mulai Rp {item['harga_min']:,}. "
#                 f"Fasilitas unggulan: {fac_summary}. "
#                 f"Dekat dengan: {nearby_summary}. "
#                 f"Alamat: {item['alamat_lengkap']}. "
#                 f"Deskripsi: {item['deskripsi_akomodasi'][:200]}..."
#             )

#             yield item

#         except Exception as e:
#             self.logger.error(f"Error Detail {response.url}: {e}")


import scrapy
import json
import os
import time
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


class SeleniumRequest(scrapy.Request):
    """
    Custom Request class untuk Selenium
    """
    def __init__(self, url, callback=None, wait_time=3, wait_until=None, 
                 screenshot=False, script=None, **kwargs):
        # Set meta selenium flag
        meta = kwargs.get('meta', {})
        meta['selenium'] = True
        meta['wait_time'] = wait_time
        
        if wait_until:
            meta['wait_until'] = wait_until
        if screenshot:
            meta['screenshot'] = screenshot
        if script:
            meta['script'] = script
        
        kwargs['meta'] = meta
        super().__init__(url, callback, **kwargs)


class TvlkFullSpider(scrapy.Spider):
    name = "tvlk_full"
    
    # Set global untuk menghindari duplikasi hotel
    seen_hotel_ids = set()

    custom_settings = {
        'FEEDS': {
            'data/output/data_hotel_final.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'overwrite': True
            },
            'data/output/data_hotel_final.json': {
                'format': 'json',
                'encoding': 'utf8',
                'overwrite': True,
                'indent': 4
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reset seen_hotel_ids saat spider baru dibuat
        TvlkFullSpider.seen_hotel_ids.clear()

    def start_requests(self):
        # --- MODE PENGUJIAN (Hardcoded URL) ---
        test_urls = [
            'https://www.traveloka.com/id-id/hotel/indonesia/city/subang-104594'
        ]
        
        for url in test_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_list_page,
                wait_time=10,
                dont_filter=True,
                meta={'page_depth': 1}
            )

        # --- MODE PRODUKSI (Baca dari JSON) ---
        # Uncomment kode di bawah ini jika sudah siap crawling massal
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        json_path = os.path.join(project_root, "config", "lokasi_traveloka.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            urls_to_scrape = []
            if isinstance(raw_data, list):
                for entry in raw_data:
                    results = entry.get('organicResults', []) 
                    for res in results:
                        url = res.get('url')
                        if url and "traveloka.com" in url and ("/city/" in url or "/region/" in url or "/area/" in url):
                            clean_url = url.split('?')[0].split('#')[0]
                            urls_to_scrape.append(clean_url)
            
            urls_to_scrape = list(set(urls_to_scrape))
            self.logger.info(f"[INIT] Total URL dari JSON: {len(urls_to_scrape)}")
            
            for url in urls_to_scrape:
                yield SeleniumRequest(
                    url=url,
                    callback=self.parse_list_page,
                    wait_time=10,
                    dont_filter=True,
                    meta={'page_depth': 1}
                )
        else:
            self.logger.error(f"[INIT] File JSON tidak ditemukan: {json_path}")
        """

    # --- UTILITY FUNCTIONS ---
    def clean_text(self, text):
        """Membersihkan text dari whitespace berlebih"""
        if not text: 
            return ""
        return ' '.join(text.split())

    def parse_currency(self, value):
        """Mengubah string harga ke integer"""
        if not value: 
            return 0
        clean = re.sub(r'[^\d]', '', str(value))
        return int(clean) if clean else 0

    def get_next_data(self, page_source):
        """Mengambil data JSON dari __NEXT_DATA__"""
        soup = BeautifulSoup(page_source, 'html.parser')
        script = soup.find('script', id='__NEXT_DATA__')
        if script:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError as e:
                self.logger.error(f"[ERROR] JSON decode error: {e}")
                return {}
        return {}

    # --- PARSING KAMAR DARI DOM ---
    def extract_rooms_detailed(self, soup):
        """Ekstrak detail kamar dari halaman detail hotel"""
        rooms = []
        
        group_cards = soup.find_all('div', attrs={"data-testid": "room_inventory_group_card"})
        
        self.logger.debug(f"[ROOM] Ditemukan {len(group_cards)} group kamar")
        
        for idx, group in enumerate(group_cards):
            try:
                # 1. Nama Kamar Utama (Group)
                name_tag = group.find('h3', attrs={"data-testid": lambda x: x and x.startswith("room-name-")})
                group_name = self.clean_text(name_tag.text) if name_tag else f"Kamar {idx+1}"
                
                # 2. Luas Kamar
                room_size = ""
                measure_icon = group.find('svg', attrs={"data-id": "IcHotelRoomMeasure"})
                if measure_icon:
                    size_div = measure_icon.parent.find_next_sibling('div')
                    if size_div:
                        txt_node = size_div.find('div', dir="auto")
                        if txt_node: 
                            room_size = txt_node.text.strip()

                # 3. Loop Varian/Opsi Kamar
                variants = group.find_all('div', attrs={"data-testid": "room_inventory_card"})
                
                self.logger.debug(f"[ROOM] Group '{group_name}' memiliki {len(variants)} varian")
                
                for var_idx, variant in enumerate(variants):
                    try:
                        # Nama Varian
                        var_name_tag = variant.find('div', attrs={"data-testid": "room_inventory_name"})
                        var_name = self.clean_text(var_name_tag.text) if var_name_tag else group_name
                        
                        # Info Makan
                        meal_tag = variant.find('div', attrs={"data-testid": "room_inventory_breakfast"})
                        meal_info = self.clean_text(meal_tag.text) if meal_tag else "Tanpa info makan"
                        
                        # Info Kasur
                        bed_tag = variant.find('div', attrs={"data-testid": "room_inventory_bed_type"})
                        bed_info = self.clean_text(bed_tag.text) if bed_tag else "-"
                        
                        # Kebijakan Pembatalan
                        policy_tag = variant.find('div', attrs={"data-testid": "text_cancellation_policy"})
                        policy_info = self.clean_text(policy_tag.text) if policy_tag else "-"

                        # Harga
                        price_tag = variant.find('div', attrs={"data-testid": "room_inventory_cheapest_rate"})
                        if not price_tag:
                            price_tag = variant.find('div', attrs={"data-testid": lambda x: x and x.startswith("inv-original-rate-")})
                        
                        raw_price = price_tag.text.strip() if price_tag else "0"
                        price_int = self.parse_currency(raw_price)
                        
                        if price_int > 0:
                            rooms.append({
                                "tipe_kamar": var_name,
                                "kategori_kamar": group_name,
                                "harga": price_int,
                                "luas": room_size,
                                "kasur": bed_info,
                                "makan": meal_info,
                                "kebijakan": policy_info
                            })
                            self.logger.debug(f"[ROOM] Added: {var_name} - Rp {price_int:,}")
                    
                    except Exception as e:
                        self.logger.warning(f"[ROOM] Error parsing variant {var_idx}: {e}")
                        continue
                        
            except Exception as e:
                self.logger.warning(f"[ROOM] Error parsing group {idx}: {e}")
                continue
        
        return rooms

    # --- PARSING HALAMAN LIST ---
    def parse_list_page(self, response):
        """Parse halaman list hotel"""
        driver = response.meta['driver']
        depth = response.meta.get('page_depth', 1)
        
        self.logger.info(f"[LIST] ========================================")
        self.logger.info(f"[LIST] Processing Page {depth}")
        self.logger.info(f"[LIST] URL: {response.url}")
        self.logger.info(f"[LIST] Driver URL: {driver.current_url}")
        self.logger.info(f"[LIST] ========================================")

        # Tunggu container utama muncul
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="popular-hotel-list"]'))
            )
            self.logger.info("[LIST] Container popular-hotel-list loaded")
        except Exception as e:
            self.logger.error(f"[LIST] Timeout waiting for container: {e}")
            return

        # Scroll untuk trigger lazy load
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        except Exception as e:
            self.logger.warning(f"[LIST] Error saat scroll: {e}")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # --- STRICT SCOPING ---
        main_list_container = soup.find('div', attrs={"data-testid": "popular-hotel-list"})
        
        hotel_list = []
        
        if main_list_container:
            cards = main_list_container.find_all('div', attrs={"data-testid": lambda x: x and x.startswith("popular-hotel-card-container-")})
            
            self.logger.info(f"[LIST] Ditemukan {len(cards)} card hotel")
            
            for card in cards:
                try:
                    h_id = card.get('data-testid', '').replace('popular-hotel-card-container-', '')
                    link_tag = card.find('a', href=True)
                    
                    if link_tag and h_id:
                        full_url = "https://www.traveloka.com" + link_tag['href'] if link_tag['href'].startswith('/') else link_tag['href']
                        full_url = full_url.split('?')[0].split('#')[0]
                        
                        url_hotel_id = full_url.split('/')[-1].split('-')[-1] if '/' in full_url else h_id
                        
                        if url_hotel_id not in self.seen_hotel_ids:
                            self.seen_hotel_ids.add(url_hotel_id)
                            hotel_list.append(full_url)
                            self.logger.debug(f"[LIST] Added hotel: {url_hotel_id} -> {full_url}")
                        else:
                            self.logger.debug(f"[LIST] Skipped duplicate: {url_hotel_id}")
                
                except Exception as e:
                    self.logger.warning(f"[LIST] Error parsing card: {e}")
                    continue
        else:
            self.logger.warning("[LIST] Container popular-hotel-list tidak ditemukan!")

        self.logger.info(f"[LIST] Total hotel unik di halaman {depth}: {len(hotel_list)}")

        # Crawl Detail Hotel
        for url in hotel_list:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_detail_page,
                wait_time=10,
                dont_filter=True
            )

        # --- PAGINATION LOGIC ---
        if len(hotel_list) > 0:
            next_btn = soup.find('div', attrs={"data-testid": "next-page-btn"})
            is_active = next_btn and next_btn.get('aria-disabled') != 'true'
            
            if is_active:
                current_url = response.url
                match = re.search(r'/(\d+)$', current_url)
                
                if match and len(match.group(1)) <= 3:
                    next_page = int(match.group(1)) + 1
                    next_url = re.sub(r'/\d+$', f'/{next_page}', current_url)
                else:
                    next_url = f"{current_url.rstrip('/')}/2"
                
                self.logger.info(f"[LIST] -> Lanjut ke Halaman {depth + 1}: {next_url}")
                
                yield SeleniumRequest(
                    url=next_url,
                    callback=self.parse_list_page,
                    wait_time=10,
                    dont_filter=True,
                    meta={'page_depth': depth + 1}
                )
            else:
                self.logger.info("[LIST] Pagination selesai (tombol Next disabled)")
        else:
            self.logger.info("[LIST] Tidak ada hotel ditemukan, pagination dihentikan")

    # --- PARSING HALAMAN DETAIL ---
    def parse_detail_page(self, response):
        """Parse halaman detail hotel"""
        driver = response.meta['driver']
        
        self.logger.info(f"[DETAIL] ========================================")
        self.logger.info(f"[DETAIL] Parsing: {response.url}")
        self.logger.info(f"[DETAIL] Driver URL: {driver.current_url}")
        
        # Pastikan driver berada di URL yang benar
        if driver.current_url != response.url:
            self.logger.warning(f"[DETAIL] URL Mismatch! Expected: {response.url}")
            self.logger.warning(f"[DETAIL] Got: {driver.current_url}")
            self.logger.info("[DETAIL] Forcing navigation to correct URL...")
            
            try:
                driver.get(response.url)
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"[DETAIL] Error navigating to URL: {e}")
                return
        
        # Tunggu elemen kunci muncul
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'script#__NEXT_DATA__'))
            )
            self.logger.info("[DETAIL] __NEXT_DATA__ loaded")
        except Exception as e:
            self.logger.error(f"[DETAIL] Timeout waiting for __NEXT_DATA__: {e}")
            return
        
        time.sleep(2)
        
        # Scroll Agresif
        try:
            self.logger.debug("[DETAIL] Starting scroll sequence...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
            time.sleep(1.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
            time.sleep(1.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            self.logger.debug("[DETAIL] Scroll sequence completed")
        except Exception as e:
            self.logger.warning(f"[DETAIL] Error during scroll: {e}")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        next_data = self.get_next_data(driver.page_source)
        
        try:
            hotel_data = next_data.get('props', {}).get('pageProps', {}).get('hotel', {})
            
            if not hotel_data:
                self.logger.warning(f"[DETAIL] No hotel data found at {response.url}")
                return

            hotel_id = int(hotel_data.get('id', 0))
            hotel_name = hotel_data.get('displayName', 'Unknown')
            
            self.logger.info(f"[DETAIL] Extracted: ID={hotel_id}, Name={hotel_name}")
            
            if hotel_id == 0:
                self.logger.warning(f"[DETAIL] Invalid hotel ID (0) for {hotel_name}")
                return

            # --- DATA UTAMA ---
            item = {
                "hotel_id": hotel_id,
                "nama_akomodasi": hotel_name,
                "tipe_akomodasi": hotel_data.get('accomPropertyType', 'Hotel'),
                "sumber_url": response.url,
                "alamat_lengkap": hotel_data.get('address', ''),
                "kota": hotel_data.get('city', ''),
                "region": hotel_data.get('region', ''),
                "koordinat": {
                    "lat": float(hotel_data.get('latitude', 0) or 0),
                    "lon": float(hotel_data.get('longitude', 0) or 0)
                },
                "bintang_rating": float(hotel_data.get('starRating', 0) or 0),
                "rating_review": 0.0,
                "jumlah_ulasan": 0,
                "teks_rating": "",
                "harga_min": 0,
                "fasilitas": {},
                "kamar": [],
                "kebijakan": [],
                "lokasi_sekitar": [],
                "deskripsi_akomodasi": "",
                "konteks_rag": ""
            }

            # Review
            rev = hotel_data.get('reviewSummary', {}).get('ugcReviewSummary', {})
            item['rating_review'] = float(rev.get('userRating', 0) or 0)
            item['jumlah_ulasan'] = int(rev.get('numReviews', 0) or 0)
            item['teks_rating'] = rev.get('userRatingInfo', '')

            # Fasilitas
            cats = hotel_data.get('hotelFacilitiesCategoriesDisplay', [])
            for cat in cats:
                cat_name = cat.get('name', 'Lainnya')
                facilities = [x.get('name') for x in cat.get('hotelFacilityDisplays', []) if x.get('name')]
                if facilities:
                    item['fasilitas'][cat_name] = facilities

            # Deskripsi
            about_div = soup.find('div', attrs={"data-testid": "about-content"})
            if about_div:
                item['deskripsi_akomodasi'] = self.clean_text(about_div.get_text(separator=' '))
            else:
                item['deskripsi_akomodasi'] = self.clean_text(hotel_data.get('attribute', {}).get('description', ''))

            # Kamar
            item['kamar'] = self.extract_rooms_detailed(soup)
            
            if item['kamar']:
                item['harga_min'] = min([k['harga'] for k in item['kamar']])
                self.logger.info(f"[DETAIL] Ditemukan {len(item['kamar'])} kamar, harga min: Rp {item['harga_min']:,}")
            else:
                rate = hotel_data.get('rateDisplay', {})
                item['harga_min'] = self.parse_currency(rate.get('totalFare') or rate.get('baseFare'))
                self.logger.warning(f"[DETAIL] Tidak ada data kamar, fallback: Rp {item['harga_min']:,}")

            # Lokasi Sekitar
            loc_section = soup.find('div', attrs={"data-testid": "section-location"})
            if loc_section:
                cats = loc_section.find_all('div', attrs={"data-testid": lambda x: x and x.startswith("location-landmark-category-")})
                
                for cat in cats:
                    try:
                        rows = cat.find_all('div', attrs={"class": "css-1dbjc4n r-zo7nv5 r-18u37iz r-1wtj0ep"})
                        
                        for row in rows:
                            cols = row.find_all('div', recursive=False)
                            if len(cols) >= 2:
                                place_name = cols[0].get_text().strip()
                                distance_txt = cols[1].get_text().strip()
                                
                                dist_val = 0.0
                                if 'km' in distance_txt.lower():
                                    dist_val = float(re.sub(r'[^\d\.]', '', distance_txt))
                                elif 'm' in distance_txt.lower():
                                    dist_val = float(re.sub(r'[^\d\.]', '', distance_txt)) / 1000
                                
                                if place_name and dist_val > 0:
                                    item['lokasi_sekitar'].append({
                                        "nama": place_name,
                                        "jarak_km": dist_val
                                    })
                    except Exception as e:
                        self.logger.debug(f"[DETAIL] Error parsing lokasi sekitar: {e}")
                        continue
                
                self.logger.info(f"[DETAIL] Ditemukan {len(item['lokasi_sekitar'])} lokasi sekitar")
            
            # Kebijakan
            policy_section = soup.find('div', attrs={"data-testid": "section-policy"})
            if policy_section:
                rows = policy_section.find_all('tr')
                for r in rows:
                    cols = r.find_all('td')
                    if len(cols) == 2:
                        key = self.clean_text(cols[0].text)
                        val = self.clean_text(cols[1].text)
                        if key and val:
                            item['kebijakan'].append(f"{key}: {val}")
                
                self.logger.info(f"[DETAIL] Ditemukan {len(item['kebijakan'])} kebijakan")

            # RAG Context
            fac_summary = ", ".join(list(item['fasilitas'].keys())[:4]) if item['fasilitas'] else "Tidak ada info fasilitas"
            nearby_summary = ", ".join([p['nama'] for p in item['lokasi_sekitar'][:3]]) if item['lokasi_sekitar'] else "Tidak ada info lokasi sekitar"
            
            item['konteks_rag'] = (
                f"{item['nama_akomodasi']} adalah {item['tipe_akomodasi']} bintang {item['bintang_rating']} "
                f"di {item['kota']}. Harga mulai Rp {item['harga_min']:,}. "
                f"Rating: {item['rating_review']}/10 dari {item['jumlah_ulasan']} ulasan. "
                f"Fasilitas unggulan: {fac_summary}. "
                f"Dekat dengan: {nearby_summary}. "
                f"Alamat: {item['alamat_lengkap']}. "
                f"Deskripsi: {item['deskripsi_akomodasi'][:200]}..."
            )

            self.logger.info(f"[DETAIL] ✓ Successfully parsed: {hotel_name}")
            self.logger.info(f"[DETAIL] ========================================")
            
            yield item

        except Exception as e:
            self.logger.error(f"[DETAIL] Error parsing {response.url}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())