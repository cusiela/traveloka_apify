# src/crawler/middlewares.py
from scrapy import signals
from scrapy_selenium import SeleniumMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class Selenium4Middleware(SeleniumMiddleware):
    """
    Middleware khusus untuk menangani Selenium v4.10+ 
    yang mewajibkan penggunaan Service object.
    """
    def __init__(self, driver_name, driver_executable_path, driver_arguments, browser_executable_path):
        # Setup Chrome Options
        chrome_options = Options()
        for argument in driver_arguments:
            chrome_options.add_argument(argument)
        
        if browser_executable_path:
            chrome_options.binary_location = browser_executable_path

        # --- PERBAIKAN UTAMA DI SINI ---
        # Menggunakan Service object untuk executable_path
        service = Service(executable_path=driver_executable_path)
        
        # Inisialisasi Driver dengan cara baru
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    @classmethod
    def from_crawler(cls, crawler):
        # Mengambil konfigurasi dari settings.py
        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if not driver_name or not driver_executable_path:
            raise ValueError('Selenium settings not valid')

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments,
            browser_executable_path=browser_executable_path
        )
        
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware