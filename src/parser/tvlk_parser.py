# import os
# import json
# import yaml
# import pandas as pd
# from bs4 import BeautifulSoup
# from glob import glob

# # --- KONFIGURASI PATH ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CONFIG_PATH = os.path.join(BASE_DIR, "../../config/config.yaml")
# # Kita akan scan kedua folder karena isinya tercampur
# CLUSTERED_DIR = "../../data/clustered_pages"
# SCAN_DIRS = ["cluster_0", "cluster_1", "cluster_2"] 
# OUTPUT_DIR = "../../data/output"

# # Load Config
# try:
#     with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
#         CONFIG = yaml.safe_load(f)
# except FileNotFoundError:
#     print(f"[-] Config file tidak ditemukan di {CONFIG_PATH}")
#     exit()

# def get_json_value(data, path):
#     """Helper untuk mengambil data nested (support dot notation)"""
#     if not path or not data:
#         return None
    
#     keys = path.split('.')
#     value = data
#     try:
#         for key in keys:
#             if isinstance(value, list):
#                 value = value[int(key)] if key.isdigit() else None
#             else:
#                 value = value.get(key)
#             if value is None:
#                 return None
#         return value
#     except:
#         return None

# def parse_html(filepath):
#     """
#     Fungsi ini sekarang 'Agnostic'. Dia tidak diberi tahu tipe halamannya.
#     Dia akan mengecek sendiri isi JSON-nya.
#     """
#     try:
#         with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: 
#             content = f.read()
#             soup = BeautifulSoup(content, 'lxml')
        
#         # 1. Ambil Metadata Bahasa
#         html_tag = soup.find('html')
#         html_lang = html_tag.get('lang', 'unknown') if html_tag else 'unknown'

#         # 2. Ambil JSON Utama
#         script = soup.find("script", {"id": "__NEXT_DATA__"})
#         if not script: return None # Bukan halaman Traveloka valid
        
#         full_json = json.loads(script.string)
        
#         # --- LOGIKA DETEKSI TIPE HALAMAN ---
        
#         # Cek apakah ini Halaman Detail Hotel?
#         # Kita cek apakah key 'props.pageProps.hotel' ada isinya
#         hotel_data = get_json_value(full_json, CONFIG['data_schema']['detail_page']['validation_key'])
        
#         if hotel_data:
#             # >>> INI ADALAH HALAMAN DETAIL HOTEL <<<
#             schema = CONFIG['data_schema']['detail_page']
            
#             extracted = {}
#             for key, json_path in schema['items'].items():
#                 # Handler Khusus
#                 if json_path == "HTML_LANG_ATTR":
#                     extracted[key] = html_lang
#                 elif json_path == "RAW_APP_CONTEXT_LANG":
#                     context = get_json_value(full_json, "props.pageProps.rawAppContext")
#                     extracted[key] = context.get('languageTag') if context else None
                
#                 # Handler Standar
#                 else:
#                     # Karena target_root = props.pageProps.hotel, dan hotel_data sudah menunjuk ke situ
#                     # Maka kita ambil value relatif dari hotel_data, BUKAN full_json
#                     # Kecuali jika path dimulai dari root (opsional, disini kita asumsi relative terhadap root_data)
                    
#                     # Koreksi Logic: Config Anda menunjuk field dalam 'hotel'.
#                     # Jadi kita ambil langsung dari variabel `hotel_data` yang sudah kita temukan.
#                     val = get_json_value(hotel_data, get_relative_path(json_path))
                    
#                     if isinstance(val, list):
#                         val = ", ".join([str(v) for v in val])
#                     extracted[key] = val

#             # Fallback Rating (Kadang null di object utama)
#             if not extracted.get('rating_review'):
#                 # Ambil dari reviewSummary yang sejajar dengan object hotel
#                 review_summary = get_json_value(full_json, "props.pageProps.reviewSummary.ugcReviewSummary")
#                 if review_summary:
#                     extracted['rating_review'] = review_summary.get('userRating')
#                     if not extracted.get('jumlah_review'):
#                         extracted['jumlah_review'] = review_summary.get('numReviews')

#             extracted['source_file'] = os.path.basename(filepath)
#             extracted['tipe_halaman'] = 'detail_hotel' # Marker
#             return extracted

#         # Cek apakah ini Halaman Review? (Untuk sekadar info logging)
#         elif get_json_value(full_json, "props.pageProps.reviewDataProps"):
#              # Ini halaman review, kita skip (return None) atau return object kosong bertanda
#              return {"tipe_halaman": "review_page"}
        
#         else:
#             return {"tipe_halaman": "unknown"}

#     except Exception as e:
#         # print(f"Error {filepath}: {e}") 
#         return None

# def get_relative_path(full_path):
#     """
#     Config Anda menulis 'rateDisplay.totalFare' (misalnya).
#     Karena `hotel_data` sudah berada di dalam object hotel, kita gunakan path itu langsung.
#     Fungsi ini hanya placeholder jika Anda mengubah struktur config di masa depan.
#     """
#     return full_path

# def run_parser_smart():
#     if not os.path.exists(OUTPUT_DIR):
#         os.makedirs(OUTPUT_DIR)

#     valid_hotels = []
#     stats = {"detail_hotel": 0, "review_page": 0, "unknown": 0, "error": 0}

#     print(f"[*] Memulai Smart Parsing di folder: {SCAN_DIRS}")

#     for folder in SCAN_DIRS:
#         cluster_path = os.path.join(CLUSTERED_DIR, folder)
#         if not os.path.exists(cluster_path): continue
            
#         files = glob(os.path.join(cluster_path, "*.html"))
#         print(f"[*] Scanning {folder} ({len(files)} files)...")

#         for filepath in files:
#             result = parse_html(filepath)
            
#             if result:
#                 page_type = result.get('tipe_halaman', 'error')
#                 stats[page_type] = stats.get(page_type, 0) + 1
                
#                 if page_type == 'detail_hotel':
#                     valid_hotels.append(result)
#             else:
#                 stats['error'] += 1

#     # Laporan Statistik
#     print("\n" + "="*30)
#     print("LAPORAN HASIL PARSING")
#     print("="*30)
#     print(f"Total File Diproses : {sum(stats.values())}")
#     print(f"- Halaman Detail Hotel: {stats['detail_hotel']} (Data Diambil)")
#     print(f"- Halaman Review      : {stats['review_page']} (Diabaikan)")
#     print(f"- Tidak dikenali/Error: {stats['unknown'] + stats['error']}")
    
#     # Simpan Data
#     if valid_hotels:
#         df = pd.DataFrame(valid_hotels)
#         # Hapus kolom internal
#         if 'tipe_halaman' in df.columns: del df['tipe_halaman']
        
#         output_csv = os.path.join(OUTPUT_DIR, CONFIG['settings']['output_file'])
#         df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
#         print(f"\n[+] SUKSES! Data tersimpan di: {output_csv}")
#         print(df[['nama_akomodasi', 'rating_review', 'bahasa_html']].head())
#     else:
#         print("\n[-] Tidak ditemukan halaman detail hotel yang valid.")

# if __name__ == "__main__":
#     run_parser_smart()

import os
import json
import yaml
import pandas as pd
from bs4 import BeautifulSoup
from glob import glob
from datetime import datetime

# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "../../config/config.yaml")
CLUSTERED_DIR = "../../data/clustered_pages"
# Scan semua folder karena kita pakai Content-Based Detection
SCAN_DIRS = ["cluster_0", "cluster_1", "cluster_2"] 
OUTPUT_DIR = "../../data/output"

# Load Config
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print(f"[-] Config file tidak ditemukan di {CONFIG_PATH}")
    exit()

def get_json_value(data, path):
    """
    Helper sakti untuk mengambil data nested.
    Support list comprehension dengan sintaks [*].
    Contoh: "roomTypes[*].name" mengambil semua nama room.
    """
    if not path or data is None:
        return None
    
    # Handle Wildcard untuk List (Array)
    if "[*]" in path:
        head, tail = path.split("[*].", 1)
        # Ambil list parent (misal: roomTypes)
        parent_list = get_json_value(data, head)
        
        if isinstance(parent_list, list):
            results = []
            for item in parent_list:
                # Rekursif untuk setiap item di list
                val = get_json_value(item, tail)
                # Jika val adalah list (nested list), ratakan (flatten) atau append
                if isinstance(val, list):
                    results.extend(val)
                elif val is not None:
                    results.append(val)
            return results
        return None

    # Handle Dot Notation standard
    keys = path.split('.')
    value = data
    try:
        for key in keys:
            if isinstance(value, list):
                value = value[int(key)] if key.isdigit() else None
            else:
                value = value.get(key)
            
            if value is None:
                return None
        return value
    except:
        return None

def parse_html(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: 
            content = f.read()
            soup = BeautifulSoup(content, 'lxml')
        
        # 1. Ambil Bahasa
        html_tag = soup.find('html')
        html_lang = html_tag.get('lang', 'unknown') if html_tag else 'unknown'

        # 2. Ambil JSON Utama
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script: return None
        
        full_json = json.loads(script.string)
        
        # 3. Deteksi Halaman Detail Hotel
        schema = CONFIG['data_schema']['detail_page']
        hotel_data = get_json_value(full_json, schema['validation_key'])
        
        if hotel_data:
            # Halaman Valid! Mulai Ekstraksi
            extracted = {}
            
            # Inject rawAppContext agar bisa diakses jika perlu
            if 'rawAppContext' in full_json['props']['pageProps']:
                hotel_data['rawAppContext'] = full_json['props']['pageProps']['rawAppContext']
            
            # Inject canonical URL dari Full JSON ke dalam hotel_data agar bisa diambil
            if 'resource' in full_json['props']['pageProps']:
                # Cari canonical di meta tags (sedikit tricky di JSON, tapi biasanya ada di seoData)
                seo_data = full_json['props']['pageProps'].get('seoData', {})
                meta_tag = seo_data.get('metaTag', {})
                hotel_data['canonicalUrl'] = meta_tag.get('canonical')

            for key, json_path in schema['items'].items():
                # Handler Khusus
                if json_path == "HTML_LANG_ATTR":
                    extracted[key] = html_lang
                elif json_path == "RAW_APP_CONTEXT_LANG":
                    context = full_json['props']['pageProps'].get('rawAppContext', {})
                    extracted[key] = context.get('languageTag')
                else:
                    # Ambil data normal
                    val = get_json_value(hotel_data, json_path)
                    
                    # Format List menjadi String rapi (dipisahkan pipa | atau koma)
                    if isinstance(val, list):
                        # Bersihkan list dari None
                        val = [str(v) for v in val if v is not None]
                        # Gunakan ' | ' sebagai pemisah untuk list panjang (kamar/harga)
                        val = " | ".join(val)
                        
                    extracted[key] = val

            # Fallback Rating jika null
            if not extracted.get('rating_review'):
                rev_sum = get_json_value(full_json, "props.pageProps.reviewSummary.ugcReviewSummary")
                if rev_sum:
                    extracted['rating_review'] = rev_sum.get('userRating')
                    extracted['jumlah_review'] = rev_sum.get('numReviews')

            # Metadata Tambahan
            extracted['source_file'] = os.path.basename(filepath)
            extracted['tanggal_crawling'] = datetime.now().isoformat()
            extracted['tahun_data'] = datetime.now().year
            
            return extracted

        return None # Bukan halaman detail

    except Exception as e:
        # print(f"Error parsing {filepath}: {e}")
        return None

def run_parser_v2():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    valid_data = []
    print(f"[*] Memulai Parsing Cerdas di folder: {SCAN_DIRS}")

    for folder in SCAN_DIRS:
        cluster_path = os.path.join(CLUSTERED_DIR, folder)
        if not os.path.exists(cluster_path): continue
            
        files = glob(os.path.join(cluster_path, "*.html"))
        print(f"[*] Scanning {folder} ({len(files)} files)...")

        for filepath in files:
            result = parse_html(filepath)
            if result:
                valid_data.append(result)

    if valid_data:
        df = pd.DataFrame(valid_data)
        
        output_csv = os.path.join(OUTPUT_DIR, CONFIG['settings']['output_file'])
        
        # Opsi: Simpan juga versi JSON agar mirip format yang Anda minta
        output_json = output_csv.replace('.csv', '.json')
        
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        df.to_json(output_json, orient='records', indent=4, force_ascii=False)
        
        print("\n" + "="*30)
        print(f"[+] SUKSES! {len(df)} data hotel berhasil diekstrak.")
        print(f"    CSV  : {output_csv}")
        print(f"    JSON : {output_json}")
        print("="*30)
        
        # Preview kolom penting
        cols = ['nama_akomodasi', 'rating_review', 'harga_min', 'tipe_kamar']
        print(df[cols].head(2))
    else:
        print("\n[-] Tidak ditemukan halaman detail hotel yang valid.")

if __name__ == "__main__":
    run_parser_v2()