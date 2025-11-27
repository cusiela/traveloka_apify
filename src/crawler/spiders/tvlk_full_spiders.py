import scrapy
import json
import os
import time
from datetime import datetime
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

from crawler.items import AkomodasiItem

class TvlkFullSpider(scrapy.Spider):
    name = "tvlk_full"
    
    # --- KONFIGURASI ---
    CITY_LIST_PATH = "../../data/output/list_kota_traveloka.json"
    MAX_HOTELS_PER_CITY = 50 
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2, 
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
        },
        'FEEDS': {
            '../../data/output/data_hotel_final.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True
            },
            '../../data/output/data_hotel_final.csv': {
                'format': 'csv',
                'encoding': 'utf-8-sig',
                'overwrite': True
            }
        },
        # Matikan log yang terlalu berisik agar terminal tidak hang
        'LOG_LEVEL': 'INFO' 
    }

    def start_requests(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        json_path = os.path.join(project_root, "data", "output", "list_kota_traveloka.json")
        
        self.logger.info(f"[*] Membaca sumber kota: {json_path}")

        if not os.path.exists(json_path):
            self.logger.error("[-] FILE JSON TIDAK DITEMUKAN!")
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                city_data = json.load(f)
            
            self.logger.info(f"[*] Berhasil memuat {len(city_data)} kota.")
            
            for item in city_data:
                url = item.get('url')
                if url:
                    if url.startswith("/"): url = "https://www.traveloka.com" + url
                    yield SeleniumRequest(
                        url=url,
                        callback=self.parse_list_page,
                        wait_time=5,
                        meta={'city_url': url}
                    )
        except Exception as e:
            self.logger.error(f"[-] Error Init: {e}")

    def parse_list_page(self, response):
        driver = response.meta['driver']
        self.logger.info(f"[*] List Page: {response.url}")

        try:
            # Set timeout agar tidak stuck selamanya
            driver.set_page_load_timeout(30)
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        except Exception as e: 
            self.logger.warning(f"[-] List scroll warning: {str(e)[:100]}")

        sel = scrapy.Selector(text=driver.page_source)
        hotel_links = sel.css('div[data-testid^="popular-hotel-card-container"] a::attr(href)').getall()
        
        self.logger.info(f"[+] Ditemukan {len(hotel_links)} hotel.")

        for i, link in enumerate(hotel_links):
            if i >= self.MAX_HOTELS_PER_CITY: break
            yield SeleniumRequest(
                url=response.urljoin(link),
                callback=self.parse_detail_page,
                dont_filter=True,
                meta={'hotel_idx': i} # Untuk tracking
            )

    def parse_detail_page(self, response):
        driver = response.meta['driver']
        url = response.url
        idx = response.meta.get('hotel_idx', 0)
        
        self.logger.info(f"[{idx}] Processing: {url}")

        # --- SAFETY VALVE 1: Global Try-Except untuk mencegah Spider berhenti ---
        try:
            # Set Timeout Load Halaman (30 detik max)
            driver.set_page_load_timeout(30)

            # --- SMART WAITING ---
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="overview_cheapest_price"]'))
                )
                # self.logger.info("[V] Harga ready.") 
            except TimeoutException:
                self.logger.warning(f"[{idx}] Timeout menunggu harga, lanjut...")
            
            # Scroll interactions
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
                time.sleep(0.5)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
                time.sleep(1)
            except: pass

            # --- AMBIL DATA ---
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'lxml')
            sel = scrapy.Selector(text=html_content)

            item = AkomodasiItem()
            item['sumber_url'] = url
            item['tanggal_crawling'] = datetime.now().isoformat()

            # A. JSON Parsing
            script = soup.find("script", {"id": "__NEXT_DATA__"})
            json_data = None
            
            if script:
                try:
                    full_json = json.loads(script.string)
                    json_data = self.get_val(full_json, "props.pageProps.hotel") or \
                                self.get_val(full_json, "props.pageProps.property") or \
                                self.get_val(full_json, "props.pageProps.initialData.hotel")
                    
                    if json_data:
                        item['hotel_id'] = self.get_val(json_data, "id")
                        item['nama_akomodasi'] = self.get_val(json_data, "displayName")
                        item['tipe_akomodasi'] = self.get_val(json_data, "accomPropertyType")
                        item['alamat_lengkap'] = self.get_val(json_data, "globalAddressString")
                        item['region'] = self.get_val(json_data, "region")
                        item['kota'] = self.get_val(json_data, "city")
                        item['bintang_rating'] = self.get_val(json_data, "starRating")
                        item['fasilitas'] = self.get_val(json_data, "showedFacilityTypesString")

                except Exception as e:
                    self.logger.error(f"[{idx}] JSON Error: {str(e)[:100]}") # Log pendek saja

            # B. HTML Fallback & Logic
            
            # Harga
            price_html = sel.css('div[data-testid="overview_cheapest_price"]::text').get()
            if price_html:
                item['harga_min'] = price_html
            elif json_data:
                item['harga_min'] = self.get_val(json_data, "lowRate")

            # Rating
            rating_html = sel.css('div[data-testid="tvat-ratingScore"]::text').get()
            if not rating_html:
                rating_html = sel.css('div[aria-label*="rating"]::text').get()
            
            if rating_html:
                item['rating_review'] = rating_html
            elif json_data:
                item['rating_review'] = self.get_val(json_data, "userRating")

            # Jumlah Review
            rev_count_html = sel.css('div[data-testid="summary-review-ugc"] div[dir="auto"]::text').get()
            if rev_count_html and "ulasan" in rev_count_html.lower():
                item['jumlah_review'] = rev_count_html
            elif json_data:
                item['jumlah_review'] = self.get_val(json_data, "numReviews")

            # Kamar
            room_names = sel.css('h3[data-testid^="room-name-"]::text').getall()
            room_prices = sel.css('div[data-testid="room_inventory_cheapest_rate"]::text').getall()
            if room_names: item['tipe_kamar'] = room_names
            if room_prices: item['harga_per_tipe_kamar'] = room_prices

            # --- PENGAMBILAN LOKASI/FASILITAS SEKITAR (XPATH) ---
            # Selector khusus untuk mengambil teks di bawah area "Lokasi"
            poi_list = []
            
            # Coba 1: List POI Highlight
            poi_elements = sel.css('div[data-testid="summary-location-highlight-list"] div[dir="auto"]::text').getall()
            if poi_elements:
                poi_list = poi_elements
            else:
                # Coba 2: XPath mencari sibling dari Alamat
                # Mencari elemen yang memiliki pola jarak (km/m)
                poi_list = sel.xpath('//div[@data-testid="summary-location"]//following-sibling::div//div[@dir="auto"]/text()').getall()

            # Cleaning
            clean_poi = [p.strip() for p in poi_list if len(p.strip()) > 2]
            
            # Jika HTML gagal, coba fallback ke JSON
            if not clean_poi and json_data:
                poi_names = self.get_val(json_data, "nearestPointOfInterests[*].name")
                poi_dists = self.get_val(json_data, "nearestPointOfInterests[*].distance")
                if poi_names and poi_dists:
                    clean_poi = [f"{n} ({d})" for n, d in zip(poi_names, poi_dists)]

            item['lokasi_sekitar'] = clean_poi[:10] # Batasi 10 biar tidak overflow

            yield item

        except Exception as e:
            # Log error tapi JANGAN CRASH, lanjut ke hotel berikutnya
            self.logger.error(f"[{idx}] GAGAL MEMPROSES HOTEL: {str(e)[:100]}")
            return

    def get_val(self, data, path):
        if not data or not path: return None
        if "[*]" in path:
            head, tail = path.split("[*].", 1)
            parent = self.get_val(data, head)
            if isinstance(parent, list):
                results = []
                for item in parent:
                    val = self.get_val(item, tail)
                    if val: results.append(val)
                return results
            return None

        keys = path.split('.')
        value = data
        try:
            for k in keys:
                if isinstance(value, dict): value = value.get(k, {})
                else: return None
            return value if value and value != {} else None
        except: return None

