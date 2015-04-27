Crawler -- mm2_crawler
======================

Overview
--------

The crawler scans all available mirrors if their content is up to date. The
crawler only scans mirrors which are not disabled (host.user_active,
host.admin_active, site.user_active, site.admin_active).

The crawler retrieves the list of active mirrors from the database and
spawns a thread for each host. The crawling of a host consists of a loop
over all categories which have been configured for this host and one category
is crawled after another.

The crawler has the possibility to crawl a category via HTTP, FTP or RSYNC.
For each category the protocol to crawl is selected from the available
category protocols. RSYNC has the highest priority and is followed by HTTP
and the protocol used last (if no other protocol is available) is FTP.

After the crawl has finished (successful or unsuccessful) the duration
and the timestamp of the crawl is recorded in the host. After the crawl of
each category the files which are up to date in the category are stored
in the database. Crawl failures (timeouts, network problems) usually result
in a complete 'marked-as-not-up-to-date' of that mirror. Multiple consecutive
crawl failures (default 4) will disable the host completely (host.user_active).

The crawler requires enormous amounts of memory and for 40 threads crawling
mirrors in parallel at least 32GB of memory are required. At the end of
each crawl thread the garbage collector is explicitly called in the hope
that some unused memory is freed again. Fedora's MirrorManager installation
has right now (April 2015) around 250 active mirrors which are crawled.

Crawling protocol
-----------------

As previously mentioned the crawler uses either RSYNC, HTTP or FTP to crawl
a connected mirror. As also already mentioned the crawler spawns a thread
for each host it has to crawl and then starts crawling one category configured
after another. The protocol decision is made for each category so that it is
possible to crawl different categories with different protocols.

If the category supports RSYNC the whole category is scanned using RSYNC with
a single network connection. If it was able to find all files the category
is marked as up to date and the next category follows. If no RSYNC URL is
available the crawler uses FTP or HTTP. FTP requires one network connection
per directory and using HTTP each file is crawled separately. Depending on
the configuration of the remote host this can mean one network connection
per file or, if the remote host supports HTTP keep-alive, one connection
for multiple files or the whole category. This depends again on the
configuration of the remote host and is detected automatically.

Using HTTP most of the files are only read via HTTP HEAD. Not the actual data
of the file is downloaded. Only the metadata is downloaded. Only files with
the name 'repomd.xml' are actually completed downloaded and their SHA256 sum
is compared to the one in the database.

Timeouts
--------

The crawler tries to use timeouts at different points during its runtime.
There is the per host timeout (default 120 minutes) and the RSYNC timeout
of 4 hours. The RSYNC timeout is used as '--timeout=14400'. According
to RSYNC's man-page this means:

   This  option  allows  you  to set a maximum I/O timeout in seconds.
   If no data is transferred for the specified time then rsync will exit.

In contrast to the other timeouts in the crawler this has no direct influence
on the crawl duration. This only cleans up old RSYNC processes if they might
have stalled.

The per host timeout is enforced after each network operation. After each
HTTP and FTP the timeout check function is called and if the timeout is
reached a timeout exception is raised. This has again the consequence that
all categories of this host are marked as not being up to date and (default)
4 consecutive timeout failures will auto disable this host (host.user_active).

Additionally each FTP and HTTP connection have the default timeout specified
while instantiating the corresponding transport class (ftplib, httplib).
According to the python documentation this timeout works as follows:

    If the optional timeout parameter is given, blocking operations
    (like connection attempts) will timeout after that many seconds.

In combination with the different ways of crawling (FTP - whole directories,
HTTP - single files or multiple files using HTTP keepalive) the behaviour
of the timeout values depends on the host configuration and the URLs
provided as possible crawl URLs.

Additional discussion about timeouts can be found here:

   https://github.com/fedora-infra/mirrormanager2/pull/53
