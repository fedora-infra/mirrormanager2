#import os
## Set the environment variable pointing to the configuration file
#os.environ['MM2_CONFIG'] = '/etc/mirrormanager/mirrormanager.cfg'

## The following is only needed if you did not install mirrormanager2
## as a python module (for example if you run it from a git clone).
#import sys
#sys.path.insert(0, '/path/to/mirrormanager2/')


## The most import line to make the wsgi working
#from mirrormanager2 import APP as application

## Turn on the debug mode to get more information in the logs about internal
## errors
#application.debug = True
