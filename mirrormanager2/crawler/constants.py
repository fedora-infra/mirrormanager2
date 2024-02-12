# hard coded list of continents; let's hope this does not change all the time
# this is according to GeoIP
CONTINENTS = ["AF", "AN", "AS", "EU", "NA", "OC", "SA", "--"]

REPODATA_DIR = "repodata"
REPODATA_FILE = "repomd.xml"

# number of minutes to wait if a signal is received to shutdown the crawler
SHUTDOWN_TIMEOUT = 5

THREAD_TIMEOUT = 30 * 60  # seconds

HTTP_TIMEOUT = 10  # seconds
