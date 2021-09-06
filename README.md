# SCRAWLER
Multithreaded web scraping library based on selenium with built in orm feature.

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

### Prerequisites
1. python3 
2. pip3
3. lxml
4. selenium
5. urllib3

### Author

* **Afriyie Daniel**

Hope You Enjoy Using It !!!!
