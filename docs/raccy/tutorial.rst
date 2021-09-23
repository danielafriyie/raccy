.. _tutorial:

Tutorial
=========

Raccy Tutorial
---------------

In this tutorial, we are going to scrape quotes.toscrape.com, a website that lists quotes from famous authors.
We strongly recommend that you install **raccy** in a virtual environment to avoid conflict with your system packages.
The source code for this tutorial is uploaded to github. You can find it from this link https://github.com/danielafriyie/raccy/blob/main/examples/quotes.py

This is the code we will use. Save it in a file called ``quotes.py``::

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


Now all you have to do is run the code above and you are done!

Diving into the code
----------------------

Models
*******

The models are designed is such a way that, the tables are created immediately
you subclass the ``model.Model`` class without creating any object or instances or calling any create method.
The tables will be created automatically when you run your code. The idea behind this is that, in web scraping,
most of the time you'll be inserting data into a database. So instead of writing code to define your models and
and also writing code to create them, you just define your models and start inserting data into them. Off course this behaviour
can be turned off. You can read more in the API Documentation.

In our model defined above ``Quote``, there are just three fields:

**quote_id** represents the primary key field for our table.

**quote** this field stores the actual quote that we will scrape.

**author** this field stores the name of the author who created the quote.

UrlDownloader
**************

As you can see, this class subclass the ``UrlDownloaderWorker`` class. This class is responsible
for downloading the urls of items, in this case quotes, that we will scrape. Let us take a look
at the attributes and methods defined:

    * *start_url:* this is the initial url our ``UrlDownloader`` will request from.

    * *max_url_download:* this defines the maximum number of urls the ``UrlDownloader`` is supposed to donwload.

    * *job:* this method is called to handle url extraction and also puts the extracted url into ``ItemUrlScheduler``

Crawler
********

This class subclass ``CrawlerWorker`` class. This class is responsible for fetching web pages of the items we want to scrape.
In our case quotes. The class receives url from ``ItemUrlScheduler``, fetches the web page and scrape or extract data from it.
Let us take a look at the methods defined:

    * *parse:* this method is called to fetch web pages and scrape or extract data from them. The url parameter is the url received from ``ItemUrlScheduler``. The data is then put into ``DatabaseScheduler``.

Db
***

This class subclass ``DatabaseWorker`` class. This class is responsible for storing scraped data into persistent database.
Let us take a look at some of the methods defined:

    * *save:* this method is called to handle the process of storing scraped data into a database. The data parameter is the data received from ``DatabaseScheduler``.
