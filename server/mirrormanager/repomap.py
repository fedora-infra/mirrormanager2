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
# hint - this isn't actually used by anything right now
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

    u'rawhide' : (u'Fedora', u'Fedora Linux'),
    u'rawhide-debug' : (u'Fedora', u'Fedora Linux'),
    u'rawhide-source' : (u'Fedora', u'Fedora Linux'),

    u'extras-' : (u'Fedora', u'Fedora Extras'),
    u'extras-debug-' : (u'Fedora', u'Fedora Extras'),
    u'extras-source-' : (u'Fedora', u'Fedora Extras'),

    u'extras-devel' : (u'Fedora', u'Fedora Extras'),
    u'extras-devel-debug' : (u'Fedora', u'Fedora Extras'),
    u'extras-devel-source' : (u'Fedora', u'Fedora Extras'),

    u'epel-' : (u'EPEL', u'Fedora EPEL'),
    u'epel-debug-' : (u'EPEL', u'Fedora EPEL'),
    u'epel-source-' : (u'EPEL', u'Fedora EPEL'),
    }

def repo_prefix(path, category, ver):

    prefix = None
    # we don't set prefix on repos that happen to be under 'test'
    # as we don't provide repo files for them on the mirrormanager.
    isTest = u'test/' in path
    if isTest:
        return None
    # assign shortnames to repositories like yum default mirrorlists expects
    isDebug = u'debug' in path
    isRawhide = u'development' in path
    isSource = u'source' in path or u'SRPMS' in path
    isUpdatesTesting = u'updates/testing' in path
    isTesting = u'testing' in path
    isReleases = u'releases' in path
    isUpdatesReleased = False
    if not isUpdatesTesting:
        isUpdatesReleased = u'updates' in path
    isEverything = u'Everything' in path
    

    isCore = (category.name == u'Fedora Core')
    isExtras = (category.name == u'Fedora Extras')
    isEpel = (category.name == u'Fedora EPEL')
    isFedoraLinux = (category.name == u'Fedora Linux')
    isFedoraSecondary = (category.name == u'Fedora Secondary Arches')

    isRrpmfusionFreeEl = (category.name == u'RPMFUSION free EL')
    isRrpmfusionFreeFedora = (category.name == u'RPMFUSION free Fedora')
    isRrpmfusionNonfreeEl = (category.name == u'RPMFUSION nonfree EL')
    isRrpmfusionNonfreeFedora = (category.name == u'RPMFUSION nonfree Fedora')

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
            # Core rawhide is dead.
            prefix = None
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
            # extras-development is dead.
            prefix = None
        else:
            # extras-
            if isDebug:
                prefix = u'extras-debug-%s' % version
            elif isSource:
                prefix = u'extras-source-%s' % version
            else:
                prefix = u'extras-%s' % version

    elif isEpel:
        # epel-
        if isTesting:
            # testing-
            if isDebug:
                prefix = u'testing-debug-epel%s' % version
            elif isSource:
                prefix = u'testing-source-epel%s' % version
            else:
                prefix = u'testing-epel%s' % version
        else:
            if isDebug:
                prefix = u'epel-debug-%s' % version
            elif isSource:
                prefix = u'epel-source-%s' % version
            else:
                prefix = u'epel-%s' % version

    elif isFedoraLinux or isFedoraSecondary:
        if isReleases:
            if not isEverything:
                prefix = None
            # fedora-
            elif isDebug:
                prefix = u'fedora-debug-%s' % version
            elif isSource:
                prefix = u'fedora-source-%s' % version
            else:
                prefix=u'fedora-%s' % version
            
        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = u'updates-released-debug-f%s' % version
            elif isSource:
                prefix = u'updates-released-source-f%s' % version
            else:
                prefix = u'updates-released-f%s' % version
        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = u'updates-testing-debug-f%s' % version
            elif isSource:
                prefix = u'updates-testing-source-f%s' % version
            else:
                prefix = u'updates-testing-f%s' % version
        elif isRawhide:
            # rawhide
            if isDebug:
                prefix = u'rawhide-debug'
            elif isSource:
                prefix = u'rawhide-source'
            else:
                prefix = u'rawhide'

    elif isRrpmfusionFreeEl:
        if isReleases:
            if not isEverything:
                prefix = None
            # free-el
            elif isDebug:
                prefix = u'free-el-debug-%s' % version
            elif isSource:
                prefix = u'free-el-source-%s' % version
            else:
                prefix=u'free-el-%s' % version
            
        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = u'free-el-updates-released-debug-%s' % version
            elif isSource:
                prefix = u'free-el-updates-released-source-%s' % version
            else:
                prefix = u'free-el-updates-released-%s' % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = u'free-el-updates-testing-debug-%s' % version
            elif isSource:
                prefix = u'free-el-updates-testing-source-%s' % version
            else:
                prefix = u'free-el-updates-testing-%s' % version
        
    elif isRrpmfusionNonfreeEl:
        if isReleases:
            if not isEverything:
                prefix = None
            # nonfree-el
            elif isDebug:
                prefix = u'nonfree-el-debug-%s' % version
            elif isSource:
                prefix = u'nonfree-el-source-%s' % version
            else:
                prefix=u'nonfree-el-%s' % version
            
        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = u'nonfree-el-updates-released-debug-%s' % version
            elif isSource:
                prefix = u'nonfree-el-updates-released-source-%s' % version
            else:
                prefix = u'nonfree-el-updates-released-%s' % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = u'nonfree-el-updates-testing-debug-%s' % version
            elif isSource:
                prefix = u'nonfree-el-updates-testing-source-%s' % version
            else:
                prefix = u'nonfree-el-updates-testing-%s' % version

    elif isRrpmfusionFreeFedora:
        if isReleases:
            if not isEverything:
                prefix = None
            # free-fedora
            elif isDebug:
                prefix = u'free-fedora-debug-%s' % version
            elif isSource:
                prefix = u'free-fedora-source-%s' % version
            else:
                prefix=u'free-fedora-%s' % version
            
        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = u'free-fedora-updates-released-debug-%s' % version
            elif isSource:
                prefix = u'free-fedora-updates-released-source-%s' % version
            else:
                prefix = u'free-fedora-updates-released-%s' % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = u'free-fedora-updates-testing-debug-%s' % version
            elif isSource:
                prefix = u'free-fedora-updates-testing-source-%s' % version
            else:
                prefix = u'free-fedora-updates-testing-%s' % version
        elif isRawhide:
            # rawhide
            if isDebug:
                prefix = u'free-fedora-rawhide-debug'
            elif isSource:
                prefix = u'free-fedora-rawhide-source'
            else:
                prefix = u'free-fedora-rawhide'

    elif isRrpmfusionNonfreeFedora:
        if isReleases:
            if not isEverything:
                prefix = None
            # nonfree-fedora
            elif isDebug:
                prefix = u'nonfree-fedora-debug-%s' % version
            elif isSource:
                prefix = u'nonfree-fedora-source-%s' % version
            else:
                prefix=u'nonfree-fedora-%s' % version
            
        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = u'nonfree-fedora-updates-released-debug-%s' % version
            elif isSource:
                prefix = u'nonfree-fedora-updates-released-source-%s' % version
            else:
                prefix = u'nonfree-fedora-updates-released-%s' % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = u'nonfree-fedora-updates-testing-debug-%s' % version
            elif isSource:
                prefix = u'nonfree-fedora-updates-testing-source-%s' % version
            else:
                prefix = u'nonfree-fedora-updates-testing-%s' % version
        elif isRawhide:
            # rawhide
            if isDebug:
                prefix = u'nonfree-fedora-rawhide-debug'
            elif isSource:
                prefix = u'nonfree-fedora-rawhide-source'
            else:
                prefix = u'nonfree-fedora-rawhide'
        
    return prefix
