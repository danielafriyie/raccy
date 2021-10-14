from raccy import (
    model, UrlDownloaderWorker, CrawlerWorker, DatabaseWorker
)
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from shutil import which

config = model.Config()
config.DATABASE = model.SQLiteDatabase('your database path eg.(path/db.sqlite3)')
DOWNLOAD_PATH = "your download path"


class Product(model.Model):
    url = model.CharField(max_length=255)
    name = model.CharField()
    brand = model.CharField()
    price = model.CharField()
    discounted_price = model.CharField()
    discount = model.CharField()
    image_path = model.CharField(max_length=255)
    ratings = model.CharField()
    category = model.CharField()


class UrlDownloader(UrlDownloaderWorker):
    start_url = 'https://www.jumia.com.gh/mobile-phones/'
    max_url_download = 6

    def pre_job(self):
        self.wait(
            xpath="//button[@aria-label='newsletter_popup_close-cta']",
            action="click",
            condition=EC.element_to_be_clickable
        )

    def job(self):
        url = self.driver.current_url
        self.url_queue.put(url)
        self.follow(xpath="//a[@aria-label='Next Page']", callback=self.job)


class Crawler(CrawlerWorker):
    url_wait_timeout = 30

    def parse(self, url):
        self.driver.get(url)
        self.wait(
            xpath="//button[@aria-label='newsletter_popup_close-cta']",
            action="click",
            condition=EC.element_to_be_clickable
        )
        products = self.driver.find_elements_by_xpath("//article[@class='prd _fb col c-prd']")
        for product in products:
            product_url = product.find_element_by_xpath(".//a").get_attribute('href')
            self.parse_product(product_url)

    def _get_data(self, xpath):
        try:
            return self.driver.find_element_by_xpath(xpath).text
        except:
            return ""

    def parse_product(self, product_url):
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(product_url)
        img_url = self.driver.find_element_by_xpath("//div[@id='imgs']/a").get_attribute('href')
        data = dict(
            url=product_url,
            name=self._get_data("//h1[@class='-fs20 -pts -pbxs']"),
            brand=self._get_data("//div[@class='-pvxs']"),
            price=self._get_data("(//span[@dir='ltr'])[2]"),
            discounted_price=self._get_data("(//span[@dir='ltr'])[1]"),
            discount=self._get_data("//span[@class='tag _dsct _dyn -mls']"),
            image_path=self.download_image(img_url, DOWNLOAD_PATH),
            ratings=self._get_data("//div[@class='-fs29 -yl5 -pvxs']/span"),
            category='mobile phones'
        )
        self.log.info(data)
        self.db_queue.put(data)
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])


class Db(DatabaseWorker):
    data_wait_timeout = 60

    def save(self, data):
        Product.objects.create(**data)


def get_driver():
    driver_path = which('your driver path')
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    return driver


if __name__ == '__main__':
    workers = []
    urldownloader = UrlDownloader(get_driver())
    urldownloader.start()
    workers.append(urldownloader)

    for _ in range(5):
        crawler = Crawler(get_driver())
        crawler.start()
        workers.append(crawler)

    db = Db()
    db.start()
    workers.append(db)

    for worker in workers:
        worker.join()

    print('Done scraping...........')
