# from shutil import which

# BOT_NAME = 'traveloka_bot'

# SPIDER_MODULES = ['crawler.spiders']
# NEWSPIDER_MODULE = 'crawler.spiders'

# # --- 1. IDENTITAS KONSISTEN ---
# # Pastikan User-Agent di sini SAMA dengan yang ada di Selenium Arguments
# # Menggunakan UA Windows 10 agar terlihat seperti PC biasa
# USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# ROBOTSTXT_OBEY = False

# # --- 2. PENGATURAN KONKURENSI (PENTING UNTUK SELENIUM) ---
# # Jangan set 16 jika pakai Selenium! 16 browser Chrome terbuka bersamaan akan menghabiskan RAM.
# # Mulai dari 2 atau 4.
# CONCURRENT_REQUESTS = 4 
# DOWNLOAD_DELAY = 3 # Jeda sopan

# # Output Encoding
# FEED_EXPORT_ENCODING = 'utf-8'

# # --- 3. KONFIGURASI ASYNCIO (WAJIB UNTUK SCRAPY BARU) ---
# # Scrapy modern + Selenium membutuhkan reactor Asyncio agar tidak bentrok
# TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# # --- 4. KONFIGURASI SELENIUM ---
# SELENIUM_DRIVER_NAME = 'chrome'
# SELENIUM_DRIVER_EXECUTABLE_PATH = which('chromedriver')
# SELENIUM_DRIVER_ARGUMENTS = [
#     # Gunakan '--headless=new' (Chrome > 109) alih-alih '--headless' biasa.
#     # Mode 'new' jauh lebih sulit dideteksi sebagai bot daripada headless lama.
#     '--headless=new', 
    
#     '--no-sandbox',
#     '--disable-gpu',
#     '--disable-dev-shm-usage', # Mencegah crash memori di container/linux
#     '--disable-blink-features=AutomationControlled', # Sembunyikan status "navigator.webdriver"
#     f'--user-agent={USER_AGENT}', # Gunakan variabel USER_AGENT di atas agar konsisten
#     '--window-size=1920,1080',
#     '--ignore-certificate-errors',
#     '--allow-running-insecure-content',
#     '--start-maximized', # Buka layar penuh agar elemen tidak tersembunyi (responsive layout)
#     '--enable-javascript', # Pastikan JS nyala
# ]

# DOWNLOADER_MIDDLEWARES = {
#     # 'scrapy_selenium.SeleniumMiddleware': 800,  <-- HAPUS/KOMENTARI INI
#     'crawler.middlewares.Selenium4Middleware': 800, # <-- GUNAKAN INI
# }

from shutil import which

BOT_NAME = 'traveloka_bot'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# --- 1. IDENTITAS KONSISTEN ---
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

ROBOTSTXT_OBEY = False

# --- 2. PENGATURAN KONKURENSI ---
CONCURRENT_REQUESTS = 2  # Turunkan untuk Selenium (hemat RAM)
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# Auto Throttle (Optimal untuk web scraping)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Output Encoding
FEED_EXPORT_ENCODING = 'utf-8'

# --- 3. KONFIGURASI ASYNCIO (WAJIB) ---
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# --- 4. KONFIGURASI SELENIUM ---
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = which('chromedriver')

SELENIUM_DRIVER_ARGUMENTS = [
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    f'--user-agent={USER_AGENT}',
    '--window-size=1920,1080',
    '--ignore-certificate-errors',
    '--allow-running-insecure-content',
    '--start-maximized',
    '--disable-extensions',
    '--disable-infobars',
    '--disable-notifications',
    '--disable-popup-blocking',
]

# Chrome Options (Tambahan untuk anti-detection)
SELENIUM_BROWSER_EXECUTABLE_PATH = None  # Gunakan Chrome default

# --- 5. DOWNLOADER MIDDLEWARES ---
DOWNLOADER_MIDDLEWARES = {
    'crawler.middlewares.Selenium4Middleware': 800,
}

# --- 6. REQUEST HEADERS ---
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# --- 7. COOKIES & REDIRECTS ---
COOKIES_ENABLED = True
REDIRECT_ENABLED = True

# --- 8. RETRY SETTINGS ---
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# --- 9. LOGGING ---
LOG_LEVEL = 'INFO'
LOG_ENCODING = 'utf-8'

# --- 10. ITEM PIPELINE (Jika ada) ---
# ITEM_PIPELINES = {
#     'crawler.pipelines.TravelokaBotPipeline': 300,
# }

# --- 11. CACHE (Optional - untuk development) ---
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'