# SCRAWLER
Multithreaded web scraping library based on selenium.

### ARCHITECTURE

- **Url Downloader Worker**: responsible for downloading urls of items to be scraped.
<br><br>
- **Item Url Scheduler**: receives item urls from url downloader worker and enqueues them for feeding them to Crawler Worker(s).
<br><br>
- **Crawler Worker**: fetches item web pages and scrapes data from them for feeding them to database scheduler.
<br><br>
- **Database Scheduler**: receives scraped item data from item downloader workers and enqueues them for feeding them to Database Worker.
<br><br>
- **Database Worker**: receives scraped data from database scheduler and stores it in a persistent database.

### TUTORIAL

```python
from scrawler import (
    UrlDownloaderWorker, CrawlerWorker
)
from selenium import webdriver


def get_driver(filename=None, headless=True):
    driver_path = 'your driver path'
    options = webdriver.FirefoxOptions()
    options.headless = headless
    options.add_argument("--start-maximized")
    driver = webdriver.Firefox(executable_path=driver_path, options=options)
    driver.set_page_load_timeout(10)
    if filename:
        driver.save_screenshot(filename)
    return driver


class UrlDownloader(UrlDownloaderWorker):
    MAX_ITEM_DOWNLOAD = 20
    start_url = 'http://quotes.toscrape.com/' 
    next_btn = "//a[contains(text(), 'Next')]"

    def get_urls(self):
        url = self.driver.current_url
        yield url
        
        
class Crawler(CrawlerWorker):

    def parse(self, url, n):
        divs = self.driver.find_elements_by_xpath("//div[@class='quote']")
        quote_xpath = "(//div[@class='quote']/span)[1]"
        by_xpath = "(//div[@class='quote']/span)[2]/small"

        for div in divs:
            self._logger.info(f'{self.name} parsing {n} - {url}')
            quote = {
                'quote': div.find_element_by_xpath(quote_xpath).text,
                'by': div.find_element_by_xpath(by_xpath).text
            }
            self._logger.info(quote)
            
            
if __name__ == '__main__':
    url = UrlDownloader(driver=get_driver(headless=True))
    url.start()
    for _ in range(2):
        cw = Crawler(driver=get_driver(headless=True))
        cw.start()

```        

### PROJECT STRUCTURE
- **scrawler**
    - `__init__.py`
    - **logger**
        - `__init__.py`
        - logger.py
    - **scheduler**
        - `__init__.py`
        - scheduler.py
    - **utils**
        - `__init__.py`
        - config.py
        - driver.py
        - meta.py
        - utils.py
    - **worker**
        - `__init__.py`
        - crawler.py
        - database.py
        - downloader.py
- **tests**
- README.md
- req.txt
- setup.py

### Prerequisites
1. python3 
2. pip3
3. lxml
4. selenium
5. urllib3

### Author

* **Afriyie Daniel**

Hope You Enjoy Using It !!!!
