from raccy import (
    UrlDownloaderWorker, CrawlerWorker, DatabaseWorker, WorkersManager
)
import ro as model
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from shutil import which

config = model.Config()
config.DATABASE = model.SQLiteDatabase('your database path eg.(path/db.sqlite3)')


class NflModel(model.Model):
    year = model.CharField()
    team = model.CharField()
    att = model.CharField()
    cmp = model.CharField()
    cmp_pct = model.CharField()
    yds_att = model.CharField()
    pass_yds = model.CharField()
    td = model.CharField()
    int = model.CharField()
    rate = model.CharField()
    first = model.CharField()
    first_pct = model.CharField()
    twenty_plus = model.CharField()
    forty_plus = model.CharField()
    lng = model.CharField()
    sck = model.CharField()
    scky = model.CharField()


class UrlDownloader(UrlDownloaderWorker):
    start_url = 'https://www.nfl.com/stats/team-stats/offense/passing/1970/reg/all'

    def job(self):
        year = 1970
        for _ in range(10):
            url = f'https://www.nfl.com/stats/team-stats/offense/passing/{year}/reg/all'
            self.url_queue.put(url)
            year += 1


class Crawler(CrawlerWorker):

    def parse(self, url):
        self.driver.get(url)
        rows = self.driver.find_elements_by_xpath("//table/tbody/tr")
        select = Select(self.driver.find_element_by_xpath("//select"))

        for row in rows:
            data = {
                'year': select.first_selected_option.text,
                'team': row.find_element_by_xpath(".//td/div/div[contains(@class,'shortname')]").text,
                'att': row.find_element_by_xpath("(.//td)[2]").text,
                'cmp': row.find_element_by_xpath("(.//td)[3]").text,
                'cmp_pct': row.find_element_by_xpath("(.//td)[4]").text,
                'yds_att': row.find_element_by_xpath("(.//td)[5]").text,
                'pass_yds': row.find_element_by_xpath("(.//td)[6]").text,
                'td': row.find_element_by_xpath("(.//td)[7]").text,
                'int': row.find_element_by_xpath("(.//td)[8]").text,
                'rate': row.find_element_by_xpath("(.//td)[9]").text,
                'first': row.find_element_by_xpath("(.//td)[10]").text,
                'first_pct': row.find_element_by_xpath("(.//td)[11]").text,
                'twenty_plus': row.find_element_by_xpath("(.//td)[12]").text,
                'forty_plus': row.find_element_by_xpath("(.//td)[13]").text,
                'lng': row.find_element_by_xpath("(.//td)[14]").text,
                'sck': row.find_element_by_xpath("(.//td)[15]").text,
                'scky': row.find_element_by_xpath("(.//td)[16]").text
            }
            self.log.info(data)
            self.db_queue.put(data)


class Db(DatabaseWorker):

    def save(self, data):
        NflModel.objects.create(**data)


def get_driver():
    driver_path = which('your driver path')
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    return driver


if __name__ == '__main__':
    manager = WorkersManager()
    manager.add_driver(get_driver)
    manager.start()
