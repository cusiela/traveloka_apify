# # src/crawler/middlewares.py
# from scrapy import signals
# from scrapy_selenium import SeleniumMiddleware
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options

# class Selenium4Middleware(SeleniumMiddleware):
#     """
#     Middleware khusus untuk menangani Selenium v4.10+ 
#     yang mewajibkan penggunaan Service object.
#     """
#     def __init__(self, driver_name, driver_executable_path, driver_arguments, browser_executable_path):
#         # Setup Chrome Options
#         chrome_options = Options()
#         for argument in driver_arguments:
#             chrome_options.add_argument(argument)
        
#         if browser_executable_path:
#             chrome_options.binary_location = browser_executable_path

#         # --- PERBAIKAN UTAMA DI SINI ---
#         # Menggunakan Service object untuk executable_path
#         service = Service(executable_path=driver_executable_path)
        
#         # Inisialisasi Driver dengan cara baru
#         self.driver = webdriver.Chrome(service=service, options=chrome_options)

#     @classmethod
#     def from_crawler(cls, crawler):
#         # Mengambil konfigurasi dari settings.py
#         driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
#         driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
#         browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
#         driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

#         if not driver_name or not driver_executable_path:
#             raise ValueError('Selenium settings not valid')

#         middleware = cls(
#             driver_name=driver_name,
#             driver_executable_path=driver_executable_path,
#             driver_arguments=driver_arguments,
#             browser_executable_path=browser_executable_path
#         )
        
#         crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
#         return middleware

"""
Custom Selenium Middleware untuk Scrapy
File: crawler/middlewares.py
"""

from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging
import time


class Selenium4Middleware:
    """
    Middleware untuk handling Selenium 4 dengan Scrapy
    """
    
    def __init__(self, driver_name, driver_executable_path, 
                 driver_arguments, browser_executable_path=None):
        """
        Inisialisasi middleware
        """
        self.driver_name = driver_name
        self.driver_executable_path = driver_executable_path
        self.driver_arguments = driver_arguments or []
        self.browser_executable_path = browser_executable_path
        self.driver = None
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory method untuk membuat instance dari crawler settings
        """
        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME', 'chrome')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS', [])
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        
        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments,
            browser_executable_path=browser_executable_path
        )
        
        # Connect signals
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        
        return middleware

    def spider_opened(self, spider):
        """
        Dipanggil saat spider dibuka - inisialisasi driver
        """
        self.logger.info(f'[Selenium4Middleware] Initializing {self.driver_name} driver...')
        
        try:
            if self.driver_name.lower() == 'chrome':
                chrome_options = Options()
                
                # Tambahkan arguments dari settings
                for argument in self.driver_arguments:
                    chrome_options.add_argument(argument)
                
                # Anti-detection settings
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Tambahkan preferences
                prefs = {
                    "profile.default_content_setting_values.notifications": 2,  # Block notifications
                    "profile.default_content_settings.popups": 0,  # Block popups
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False
                }
                chrome_options.add_experimental_option("prefs", prefs)
                
                # Set binary location jika ada
                if self.browser_executable_path:
                    chrome_options.binary_location = self.browser_executable_path
                
                # Buat service
                if self.driver_executable_path:
                    service = Service(executable_path=self.driver_executable_path)
                else:
                    service = Service()  # Akan mencari chromedriver di PATH
                
                # Buat driver
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Set timeouts
                self.driver.set_page_load_timeout(60)
                self.driver.implicitly_wait(10)
                
                # Anti-detection: Hapus navigator.webdriver flag
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': '''
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    '''
                })
                
                self.logger.info('[Selenium4Middleware] Driver initialized successfully')
            else:
                raise ValueError(f"Unsupported driver: {self.driver_name}")
                
        except Exception as e:
            self.logger.error(f'[Selenium4Middleware] Failed to initialize driver: {e}')
            raise

    def spider_closed(self, spider):
        """
        Dipanggil saat spider ditutup - cleanup driver
        """
        if self.driver:
            self.logger.info('[Selenium4Middleware] Closing driver...')
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f'[Selenium4Middleware] Error closing driver: {e}')

    def process_request(self, request, spider):
        """
        Process setiap request
        Hanya process request yang memiliki meta 'selenium' atau merupakan SeleniumRequest
        """
        # Check jika request membutuhkan Selenium
        if not request.meta.get('selenium', False):
            # Bukan SeleniumRequest, skip
            return None
        
        if not self.driver:
            self.logger.error('[Selenium4Middleware] Driver not initialized!')
            return None
        
        try:
            self.logger.debug(f'[Selenium4Middleware] Processing: {request.url}')
            
            # Navigate ke URL
            self.driver.get(request.url)
            
            # Wait time dari meta (default 3 detik)
            wait_time = request.meta.get('wait_time', 3)
            time.sleep(wait_time)
            
            # Wait for specific condition jika ada
            wait_until = request.meta.get('wait_until')
            if wait_until:
                try:
                    WebDriverWait(self.driver, 10).until(wait_until)
                except TimeoutException:
                    self.logger.warning(f'[Selenium4Middleware] Timeout waiting for condition')
            
            # Ambil page source
            body = self.driver.page_source.encode('utf-8')
            
            # Buat HtmlResponse
            response = HtmlResponse(
                url=self.driver.current_url,
                body=body,
                encoding='utf-8',
                request=request
            )
            
            # Tambahkan driver ke meta untuk digunakan di callback
            response.meta['driver'] = self.driver
            
            self.logger.debug(f'[Selenium4Middleware] ✓ Success: {request.url}')
            
            return response
            
        except WebDriverException as e:
            self.logger.error(f'[Selenium4Middleware] WebDriver error: {e}')
            return None
        except Exception as e:
            self.logger.error(f'[Selenium4Middleware] Unexpected error: {e}')
            return None

    def process_exception(self, request, exception, spider):
        """
        Process exceptions
        """
        self.logger.error(f'[Selenium4Middleware] Exception for {request.url}: {exception}')
        return None


class SpiderMiddleware:
    """
    Spider middleware untuk Traveloka bot
    """
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)