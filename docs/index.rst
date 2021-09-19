RACCY
=================================

Raccy is a multithreaded web scraping library based on selenium with
built in ORM. It can be used for web automation, web scraping, and
data mining. Currently the ORM feature supports only SQLite Database.

REQUIREMENTS
=============

* Python 3.7+
* Works on Windows, Linux, and Mac

ARCHITECTURE OVERVIEW
======================

* **UrlDownloaderWorker:** resonsible for downloading item(s) to be scraped urls and enqueue(s) them in ItemUrlScheduler

* **ItemUrlScheduler:** receives item urls from UrlDownloaderWorker and enqueues them
    for feeding them to CrawlerWorker

* **CrawlerWorker:** fetches item web pages and scrapes or extract data from them and enqueues the data in DatabaseScheduler

* **DatabaseScheduler:** receives scraped item data from CrawlerWorker(s) and enques them
    for feeding them to DatabaseWorker.

* **DatabaseWorker:** receives scraped data from DatabaseScheduler and stores it in a persistent database.

INSTALLATION
=============

Raccy requires python 3.7+. It is actually built with python 3.7. You can install the latest version hosted on PyPI with:

.. code-block:: console

    pip install raccy



.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
