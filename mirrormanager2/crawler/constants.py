# hard coded list of continents; let's hope this does not change all the time
# this is according to GeoIP
CONTINENTS = ["AF", "AN", "AS", "EU", "NA", "OC", "SA", "--"]

REPODATA_DIR = "repodata"
REPODATA_FILE = "repomd.xml"

DEFAULT_GLOBAL_TIMEOUT = 360  # minutes

# number of minutes to wait if a signal is received to shutdown the crawler
SHUTDOWN_TIMEOUT = 5

CONNECTION_TIMEOUT = 10  # seconds

# Number of times to retry a connection
RETRIES = 10
RETRIES_MAX_INTERVAL = 10  # in seconds
