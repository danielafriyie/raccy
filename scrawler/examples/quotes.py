from scrawler import (
    model, UrlDownloaderWorker, CrawlerWorker, DatabaseWorker
)
from scrawler.utils.driver import next_btn_handler, close_driver
from selenium import webdriver
from shutil import which

config = model.Config()
config.DATABASE = model.SQLiteDatabase('quotes.sqlite3')


class Quote(model.Model):
    quote_id = model.PrimaryKeyField()
    quote = model.TextField()
    author = model.CharField(max_length=100)

    class Meta:
        db_name = 'quote_table'


class UrlDownloader(UrlDownloaderWorker):
    start_url = 'https://quotes.toscrape.com/page/1/'
    urls_scraped = 0

    def job(self):
        while True:
            url = self.driver.current_url
            self.scheduler.put(url)
            next_btn_handler(self.driver, "//a[contains(text(), 'Next')]")

            if self.urls_scraped > 10:
                self.log.info('Closing................')
                break

            with self.mutex:
                self.urls_scraped += 1
        close_driver(self.driver, self.log)


class Crawler(CrawlerWorker):

    def parse(self, url):
        self.driver.get(url)
        quotes = self.driver.find_elements_by_xpath("//div[@class='quote']")
        for q in quotes:
            quote = q.find_element_by_xpath(".//span[@class='text']").text
            author = q.find_element_by_xpath(".//span/small").text

            data = {
                'quote': quote,
                'author': author
            }
            self.log.info(data)
            self.db_scheduler.put(data)


class Db(DatabaseWorker):

    def save(self, data):
        Quote.objects.create(**data)


def get_driver():
    driver_path = which('.\\chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
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
