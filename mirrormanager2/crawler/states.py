from enum import Enum


class CrawlStatus(Enum):
    OK = "OK"
    TIMEOUT = "TIMEOUT"
    FAILURE = "FAILURE"
    DISABLE = "DISABLE"
    UNKNOWN = "UNKNOWN"


class SyncStatus(Enum):
    UP2DATE = "up2date"
    NOT_UP2DATE = "not_up2date"
    UNCHANGED = "unchanged"
    UNREADABLE = "unreadable"
    UNKNOWN = "unknown"
    CREATED = "created"
    DELETED = "deleted"


# Keep this in sync with the fields in models.PropagationStat
class PropagationStatus(Enum):
    SAME_DAY = "same_day"
    ONE_DAY = "one_day"
    TWO_DAY = "two_day"
    OLDER = "older"
    NO_INFO = "no_info"
