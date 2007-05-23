from mirrors.model import *
import sys
import pickle
import pprint


def errorprint(error):
    print >> sys.stderr, error

def validate_config(config):
    if type(config) != dict:
        errorprint('config file is not a dict')
        return False
    if not config.has_key('version'):
        errorprint('no version')
        return False
    # this field is an integer
    if config['version'] != 0:
        errorprint('version %s not 0' % (config['version']))
        return False

    for section in ['global', 'site', 'host']:
        if not config.has_key(section):
            errorprint('missing section %s' % (section))
            return False

    g = config['global']
    # this field is a string as it comes from the config file
    if not g.has_key('enabled') or g['enabled'] != '1':
        errorprint('section [global] not enabled')
        return False

    site = config['site']
    required_options = [ 'name', 'password' ]
    for o in required_options:
        if not site.has_key(o):
            errorprint('section [site] missing required option %s' % o)
            return False

    host = config['host']
    required_options = [ 'name' ]
    for o in required_options:
        if not host.has_key(o):
            errorprint('section [host] missing required option %s' % o)
            return False

    required_options = [ 'dirtree' ]
    for category in config.keys():
        if category in ['global', 'site', 'host', 'version', 'stats']:
            continue
                                                                           
        for o in required_options:
            if not config[category].has_key(o):
                errorprint('section [%s] missing required option %s' % (category, o))
                return False
    return True

def read_host_config(config):
        if not validate_config(config):
            return None
        
        csite = config['site']
        chost = config['host']

        try:
            site = Site.byName(csite['name'])
        except SQLObjectNotFound:
            return None

        if csite['password'] != site.password:
            return None

        h = Host.selectBy(name=chost['name'], site=site)
        if h.count() != 1:
            return None
        host = h[0]
        host.config = config

        return (site, host, config)
