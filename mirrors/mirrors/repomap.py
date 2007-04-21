# The various name permutations for mirrorlist files are:
# core-6-US-i386.txt and  core-6-global-i386.txt
# core-source-6-global-i386.txt (no per-country)
# core-debug-6-global-i386.txt (no per-country)
# extras-6-US-i386.txt and extras-6-glboal-i386.txt
# extras-source-6-global-i386.txt (no per-country)
# extras-debug-6-global-i386.txt (no per-country)
# rawhide-US-i386.txt
# updates-released-6-US-i386.txt 
# updates-released-debug-fc6-US-i386.txt
# updates-released-
#
# country or global is usually appended
# basearch is always appended coming from the mirrorlist cgi
# to the key, the value $releasever is always appended, except for rawhide and development
repomap = {
    u'core-' : (u'Fedora', u'Fedora Core'),
    u'core-debug-' : (u'Fedora', u'Fedora Core'),
    u'core-source-' : (u'Fedora', u'Fedora Core'),

    u'updates-released-' : (u'Fedora', u'Fedora Core'),
    u'updates-released-debug-' : (u'Fedora', u'Fedora Core'),
    u'updates-released-source-' : (u'Fedora', u'Fedora Core'),

    u'updates-testing-' : (u'Fedora', u'Fedora Core'),
    u'updates-testing-debug-' : (u'Fedora', u'Fedora Core'),
    u'updates-testing-source-' : (u'Fedora', u'Fedora Core'),

    u'rawhide' : (u'Fedora', u'Fedora Core'),
    u'rawhide-debug' : (u'Fedora', u'Fedora Core'),
    u'rawhide-source' : (u'Fedora', u'Fedora Core'),

    u'extras-' : (u'Fedora', u'Fedora Extras'),
    u'extras-debuginfo-' : (u'Fedora', u'Fedora Extras'),
    u'extras-source-' : (u'Fedora', u'Fedora Extras'),

    u'extras-development' : (u'Fedora', u'Fedora Extras'),
    u'extras-development-debuginfo' : (u'Fedora', u'Fedora Extras'),
    u'extras-development-source' : (u'Fedora', u'Fedora Extras'),

    u'epel-' : (u'RHEL', u'Fedora EPEL'),
    u'epel-debuginfo-' : (u'RHEL', u'Fedora EPEL'),
    u'epel-source-' : (u'RHEL', u'Fedora EPEL'),
    }

def repo_prefix(path, category, ver):

    prefix = None
    # we don't set prefix on repos that happen to be under 'test'
    # as we don't provide repo files for them on the mirrors.
    isTest = u'test/' in path
    if isTest:
        return None
    # assign shortnames to repositories like yum default mirrorlists expects
    isDebug = u'debug' in path
    isRawhide = u'development' in path
    isSource = u'source' in path or u'SRPMS' in path
    isUpdatesTesting = u'updates/testing' in path
    isUpdatesReleased = False
    if not isUpdatesTesting:
        isUpdatesReleased = u'updates' in path
    

    isCore = (category.name == u'Fedora Core')
    isExtras = (category.name == u'Fedora Extras')
    isEpel = (category.name == u'Fedora EPEL')

    version = u'unknown'
    if not isRawhide and ver is not None:
        version = ver.name

    if isCore:
        if isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = u'updates-released-debug-fc%s' % version
            elif isSource:
                prefix = u'updates-released-source-fc%s' % version
            else:
                prefix = u'updates-released-fc%s' % version
        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = u'updates-testing-debug-fc%s' % version
            elif isSource:
                prefix = u'updates-testing-source-fc%s' % version
            else:
                prefix = u'updates-testing-fc%s' % version
        elif isRawhide:
            # rawhide
            if isDebug:
                prefix = u'rawhide-debug'
            elif isSource:
                prefix = u'rawhide-source'
            else:
                prefix = u'rawhide'
        else:
            # core-
            if isDebug:
                prefix = u'core-debug-%s' % version
            elif isSource:
                prefix = u'core-source-%s' % version
            else:
                prefix = u'core-%s' % version
        
    elif isExtras:
        if isRawhide:
            # extras-development
            if isDebug:
                prefix = u'extras-development-debuginfo'
            elif isSource:
                prefix = u'extras-development-source'
            else:
                prefix = u'extras-development'
        else:
            # extras-
            if isDebug:
                prefix = u'extras-debuginfo-%s' % version
            elif isSource:
                prefix = u'extras-source-%s' % version
            else:
                prefix = u'extras-%s' % version

    elif isEpel:
            # epel-
            if isDebug:
                prefix = u'epel-debuginfo-%s' % version
            elif isSource:
                prefix = u'epel-source-%s' % version
            else:
                prefix = u'epel-%s' % version
        

    return prefix
