# CHANGELOG

Track changes in raccy versions and releases.

### 1.2.6

- Refactored `UrlDownloaderWorker`
- Added `follow` method to `CrawlerWorker`
- Refactored `worker.py` module


### 1.2.5

- Deleted scheduler package and moved it's code to `core/queue_.py` module
- Renamed `DatabaseScheduler`, `BaseScheduler`, and `ItemUrlScheduler` class to `DatabaseQueue`, `BaseQueue`, `ItemUrlQueue`
- Renamed `SchedulerError` class to `QueueError`
- Moved log data from root directory to logs directory
- Added `kill` method to `BaseWorker` class to kill running worker threads
