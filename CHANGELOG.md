# CHANGELOG

Track changes in raccy versions and releases.

### 2.0.0
- Removed built-in ORM
- Removed logger module
- Removed some utility functions

### 1.3.0
- Refactored `worker.py` module
- Added workers manager class
- Added signals `(before/after) - (insert, update, delete)`
- Refacored `orm` package

### 1.2.6

- Refactored `UrlDownloaderWorker`
- Added `follow` method to `CrawlerWorker`
- Refactored `worker.py` module
- Added `download` method to `CrawlerWorker`
- Added `download_image` method to `CrawlerWorker`


### 1.2.5

- Deleted scheduler package and moved it's code to `core/queue_.py` module
- Renamed `DatabaseScheduler`, `BaseScheduler`, and `ItemUrlScheduler` class to `DatabaseQueue`, `BaseQueue`, `ItemUrlQueue`
- Renamed `SchedulerError` class to `QueueError`
- Moved log data from root directory to logs directory
- Added `kill` method to `BaseWorker` class to kill running worker threads
