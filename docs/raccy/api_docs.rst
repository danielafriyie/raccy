API Documentation
=================================

This document specifies Raccy's APIs.

UrlDownloaderWorker API
-------------------------

**class UrlDownloaderWorker** (driver, \*args, \**kwargs):

        **Parameters**
                * **driver** - selenium webdriver object
                * **\*args** - arguments to pass to python threading.Thread class
                * **\**kwargs** - keyword arguments to to pass to python threading.Thread class

        | **start_url** - this is the initial url to make request from
        | **scheduler** - ``ItemUrlScheduler`` object
        | **mutex** - python threading.Lock object
        | **urls_scraped** - total url downloaded
        | **max_url_download** - maximum number of urls to download
        | **log** - raccy.logger.logger.logger object
        | **pre_job**
        |       This method is called before job method is called.
        |       In case you want to do authentication or perform some action before doing the actual scraping, overwrite this method.
        | **post_job**
        |       This method is called after job method is called, when all the scraping is done
        | **wait** (xpath, secs=5, condition=None, action=None)
        |       Wrapper method acround selenium webdriver wait
        | **follow** (xpath=None, url=None, callback=None, \*cbargs, \**cbkwargs)
        |       Follows the url or the button to click to go to the next page
        | **job**
        |       This is where the actual scraping takes place.
        | **close_driver**
        |       Calls driver.quit() on the selenium driver object


CrawlerWorker API
-------------------

**class CrawlerWorker** (driver, \*args, \**kwargs):

        **Parameters**
                * **driver** - selenium webdriver object
                * **\*args** - arguments to pass to python threading.Thread class
                * **\**kwargs** - keyword arguments to to pass to python threading.Thread class

        | **url_wait_timeout** - how long to wait for urls from ``ItemUrlScheduler``
        | **scheduler** - ItemUrlScheduler object
        | **db_scheduler** - DatabaseScheduler object
        | **log** - raccy.logger.logger.logger object
        | **pre_job**
        |       This method is called before parse method is called.
        |       In case you want to do authentication or perform some action before doing the actual scraping, overwrite this method.
        | **post_job**
        |       This method is called after parse method is called, when all the scraping is done
        | **wait** (xpath, secs=5, condition=None, action=None)
        |       Wrapper method acround selenium webdriver wait
        | **parse**
        |       This is where the actual scraping takes place.
        | **close_driver**
        |       Calls driver.quit() on the selenium driver object


DatabaseWorker API
-------------------

**class DatabaseWorker**:

        | **wait_timeout** - how long to wait for data from ``DatabaseScheduler``
        | **db_scheduler** - ``DatabaseScheduler`` object
        | **log** - raccy.logger.logger.logger object
        | **pre_job**
        |       This method is called before save method is called.
        | **post_job**
        |       This method is called after save method is called.
        | **save**
        |       This method is called to save data to a database


ORM API
---------

**class Config**:

        | **DATABASE**
        | **DBMAPPER**


**class PrimaryKeyField**:


**class CharField** (max_length=None, null=True, unique=False, default=None):


**class TextField** (null=True, default=None):


**class IntegerField** (null=True, default=None):


**class FloatField** (null=True, default=None):


**class BooleanField** (null=True, default=None):


**class DateField** (null=True, default=None):


**class DateTimeField** (null=True, default=None):


**class ForeignKeyField** (model, on_field):


**class Model**:

        | **class Meta**:
        |       **abstract** = False
        |       **table_name** = None
        |       **create_table** = True