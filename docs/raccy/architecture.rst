.. _architecture:

Architecture Overview
======================

UrlDownloaderWorker
--------------------

Resonsible for downloading item(s) to be scraped urls and enqueue(s) them in **ItemUrlQueue**

ItemUrlQueue
------------------

Receives item urls from **UrlDownloaderWorker** and enqueues them for feeding them to **CrawlerWorker**

CrawlerWorker
--------------

Fetches item web pages and scrapes or extract data from them and enqueues the data in **DatabaseQueue**

DatabaseQueue
------------------

Receives scraped item data from **CrawlerWorker(s)** and enques them for feeding them to **DatabaseWorker**.

DatabaseWorker
---------------

Receives scraped data from **DatabaseQueue** and stores it in a persistent database.
