from selenium import webdriver
from shutil import which
from scrawler import BaseCrawlerWorker
from scrawler.utils.driver import close_driver, driver_wait
from scrawler.utils.utils import random_delay


def get_driver():
    driver_path = which('.\\chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    return driver


class FacebookInvites(BaseCrawlerWorker):
    fb_home = 'https://web.facebook.com/'
    page_url = 'your facebook page url'
    username = "your facebook username"
    password = "your facebook password"

    def job(self):
        self.driver.get(self.fb_home)

        # Login
        self.driver.find_element_by_xpath("//input[@id='email']").send_keys(self.username)
        self.driver.find_element_by_xpath("//input[@id='pass']").send_keys(self.password)
        self.driver.find_element_by_xpath("//button[contains(text(), 'Log In')]").click()

        # Uncomment the code below if two factor authentication is enabled
        # code = input("Enter two factor authentication code: ")
        # self.driver.find_element_by_xpath("//input[@id='approvals_code']").send_keys(code)
        # self.driver.find_element_by_xpath("//button[contains(text(), 'Continue')]").click()

        random_delay(1, 5)
        self.driver.find_element_by_xpath("//button[contains(text(), 'Continue')]")
        random_delay(1, 5)
        self.driver.get(self.page_url)
        random_delay(1, 5)

        number_of_people_to_invite = 250
        people_invited = 0
        while True:
            if people_invited >= number_of_people_to_invite:
                break
            self.driver.find_element_by_xpath("//span[contains(text(), 'See All Friends')]/parent::node()/parent::node()/parent::node()/parent::node()/parent::node()").click()
            driver_wait(
                self.driver,
                xpath="//span[contains(text(), 'Send Invites')]/parent::node()/parent::node()/parent::node()/parent::node()/parent::node()",
                secs=50,
                method="element_to_be_clickable"
            )

            for i in range(10):
                self.driver.find_element_by_xpath(f"(//div[@class='']/i[@data-visualcompletion='css-img'])[{i + 4}]").click()
                people_invited += 1

            self.driver.find_element_by_xpath("//input[@name='checkbox']").click()
            self.driver.find_element_by_xpath("//span[contains(text(), 'Send Invites')]/parent::node()/parent::node()/parent::node()/parent::node()/parent::node()").click()

        self.log.info("Job done, closing......................")
        close_driver(self.driver)


if __name__ == '__main__':
    fb_invites = FacebookInvites(get_driver())
    fb_invites.start()
    fb_invites.join()
