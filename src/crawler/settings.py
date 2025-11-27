# BOT_NAME = 'traveloka_bot'

# SPIDER_MODULES = ['crawler.spiders']
# NEWSPIDER_MODULE = 'crawler.spiders'

# # Identitas User-Agent (Penting agar tidak diblokir firewall)
# USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'

# # Hormati robots.txt
# ROBOTSTXT_OBEY = False

# # Pengaturan Kecepatan (Concurrent)
# CONCURRENT_REQUESTS = 16
# DOWNLOAD_DELAY = 5 # Delay 0.5 detik agar server tidak down

# # Output Encoding
# FEED_EXPORT_ENCODING = 'utf-8'

# # Tambahkan/Update di settings.py

# # Konfigurasi Scrapy-Selenium
# from shutil import which

# SELENIUM_DRIVER_NAME = 'chrome'
# SELENIUM_DRIVER_EXECUTABLE_PATH = which('chromedriver')
# SELENIUM_DRIVER_ARGUMENTS = [
#     '--headless',  # Jalankan tanpa membuka window (opsional, matikan jika ingin lihat prosesnya)
#     '--no-sandbox',
#     '--disable-gpu',
#     '--disable-blink-features=AutomationControlled', # PENTING: Sembunyikan status otomatisasi
#     '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#     '--window-size=1920,1080'
# ]

# DOWNLOADER_MIDDLEWARES = {
#     'scrapy_selenium.SeleniumMiddleware': 800,
# }

from shutil import which

BOT_NAME = 'traveloka_bot'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# --- 1. IDENTITAS KONSISTEN ---
# Pastikan User-Agent di sini SAMA dengan yang ada di Selenium Arguments
# Menggunakan UA Windows 10 agar terlihat seperti PC biasa
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

ROBOTSTXT_OBEY = False

# --- 2. PENGATURAN KONKURENSI (PENTING UNTUK SELENIUM) ---
# Jangan set 16 jika pakai Selenium! 16 browser Chrome terbuka bersamaan akan menghabiskan RAM.
# Mulai dari 2 atau 4.
CONCURRENT_REQUESTS = 4 
DOWNLOAD_DELAY = 3 # Jeda sopan

# Output Encoding
FEED_EXPORT_ENCODING = 'utf-8'

# --- 3. KONFIGURASI ASYNCIO (WAJIB UNTUK SCRAPY BARU) ---
# Scrapy modern + Selenium membutuhkan reactor Asyncio agar tidak bentrok
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# --- 4. KONFIGURASI SELENIUM ---
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = which('chromedriver')
SELENIUM_DRIVER_ARGUMENTS = [
    # Gunakan '--headless=new' (Chrome > 109) alih-alih '--headless' biasa.
    # Mode 'new' jauh lebih sulit dideteksi sebagai bot daripada headless lama.
    '--headless=new', 
    
    '--no-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage', # Mencegah crash memori di container/linux
    '--disable-blink-features=AutomationControlled', # Sembunyikan status "navigator.webdriver"
    f'--user-agent={USER_AGENT}', # Gunakan variabel USER_AGENT di atas agar konsisten
    '--window-size=1920,1080',
    '--ignore-certificate-errors',
    '--allow-running-insecure-content',
    '--start-maximized', # Buka layar penuh agar elemen tidak tersembunyi (responsive layout)
    '--enable-javascript', # Pastikan JS nyala
]

DOWNLOADER_MIDDLEWARES = {
    # 'scrapy_selenium.SeleniumMiddleware': 800,  <-- HAPUS/KOMENTARI INI
    'crawler.middlewares.Selenium4Middleware': 800, # <-- GUNAKAN INI
}