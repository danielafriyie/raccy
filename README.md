# RACCY

### OVERVIEW
Raccy is a multithreaded web scraping library based on selenium with 
built in ORM feature. It can be used for a wide range of purposes, from data mining to 
monitoring and automated testing.
Currently the ORM feature supports only SQLite Database.

### REQUIREMENTS
- Python 3.7+ 
- Works on Linux, Windows

### ARCHITECTURE OVERVIEW
* **UrlDownloaderWorker:** resonsible for downloading item(s) to be scraped urls and enqueue(s) them in ItemUrlScheduler

* **ItemUrlScheduler:** receives item urls from UrlDownloaderWorker and enqueues the
    for feeding them to CrawlerWorker
    
* **CrawlerWorker:** fetches item web pages and scrapes or extract data from them and enqueues the data in DatabaseScheduler

* **DatabaseScheduler:** receives scraped item data from CrawlerWorker(s) and enques them
    for feeding them to DatabaseWorker.
    
* **DatabaseWorker:** receives scraped data from DatabaseScheduler and stores it in a persistent database.

### INSTALL

```shell script
pip install raccy
```

### TUTORIAL

```python
from raccy import (
    model, UrlDownloaderWorker, CrawlerWorker, DatabaseWorker
)
from selenium import webdriver
from shutil import which

config = model.Config()
config.DATABASE = model.SQLiteDatabase('quotes.sqlite3')


class Quote(model.Model):
    quote_id = model.PrimaryKeyField()
    quote = model.TextField()
    author = model.CharField(max_length=100)


class UrlDownloader(UrlDownloaderWorker):
    start_url = 'https://quotes.toscrape.com/page/1/'
    max_url_download = 10

    def job(self):
        url = self.driver.current_url
        self.scheduler.put(url)
        self.follow(xpath="//a[contains(text(), 'Next')]", callback=self.job)


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

```

### Author

* **Afriyie Daniel**

Hope You Enjoy Using It !!!!
