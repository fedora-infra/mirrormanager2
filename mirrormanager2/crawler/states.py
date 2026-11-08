from enum import Enum


class CrawlStatus(Enum):
    OK = "OK"
    TIMEOUT = "TIMEOUT"
    FAILURE = "FAILURE"
    DISABLE = "DISABLE"
    UNKNOWN = "UNKNOWN"


class DirStatus(Enum):
    """What a connector found out about one directory on a mirror."""

    # Every file the master has in this directory is there with the right size.
    UP2DATE = "up2date"
    # The directory exists on the mirror, but its content does not match the
    # master. The distinction from ABSENT matters: a stale directory keeps its
    # HostCategoryDir with up2date set to False, an absent one must not have
    # a HostCategoryDir at all.
    STALE = "stale"
    # The directory does not exist on the mirror.
    ABSENT = "absent"
    # The directory exists on the mirror but holds no files on the master, so
    # there is nothing to compare. Whether it is up to date is decided from
    # its child directories after the whole category has been scanned.
    PRESENT = "present"
    # The check could not tell, for example because of a temporary server
    # error. The database is left unchanged for this directory.
    UNKNOWN = "unknown"


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
