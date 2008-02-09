from mirrors.model import *
import sys
import pickle
import pprint


def validate_config(config):
    message = ''
    if type(config) != dict:
        message += 'config file is not a dict.\nPlease update your copy of report_mirror.\n'
        return (False, message)
    if not config.has_key('version'):
        message += 'config file has no version field.\n'
        return (False, message)
    # this field is an integer
    if config['version'] != 0:
        message += 'config file version is not 0, is %s.\n' % (config['version'])
        return (False, message)

    for section in ['global', 'site', 'host']:
        if not config.has_key(section):
            message += 'config file missing section %s.\n' % (section)
            return (False, message)

    g = config['global']
    # this field is a string as it comes from the config file
    if not g.has_key('enabled') or g['enabled'] != '1':
        message += 'config file section [global] not enabled.\n'
        return (False, message)

    site = config['site']
    required_options = [ 'name', 'password' ]
    for o in required_options:
        if not site.has_key(o):
            message += 'config file [site] missing required option %s.\n' % (o)
            return (False, message)

    host = config['host']
    required_options = [ 'name' ]
    for o in required_options:
        if not host.has_key(o):
            message +=  'section [host] missing required option %s.\n' % (o)
            return (False, message)

    required_options = [ 'dirtree' ]
    for category in config.keys():
        if category in ['global', 'site', 'host', 'version', 'stats']:
            continue
                                                                           
        for o in required_options:
            if not config[category].has_key(o):
                message += 'section [%s] missing required option %s.\n' % (category, o)
                return (False, message)
    return (True, message)

def read_host_config(config):
    rc, message = validate_config(config)
    if not rc:
        return (None, message + 'Invalid config file provided, please check your report_mirror.conf.')
        
    csite = config['site']
    chost = config['host']

    try:
        site = Site.byName(csite['name'])
    except SQLObjectNotFound:
        return (None, 'Config file site name or password incorrect.\n')

    if csite['password'] != site.password:
        return (None, 'Config file site name or password incorrect.\n')

    h = Host.selectBy(name=chost['name'], site=site)
    if h.count() != 1:
        return (None, 'Config file host name for site not found.\n')
    host = h[0]
    message = host.checkin(config)
    return (True, message)
