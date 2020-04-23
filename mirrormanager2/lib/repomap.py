import re

def is_development(path):
    development_re = r'\/?development\/((\d+))/'
    m = re.search(re.compile(development_re), path)
    if m is not None:
        return m.group(1)
    return None

def centos_prefix(path):
    choices = (u'os', u'updates', u'extras', u'centosplus',
               u'contrib', u'fasttrack', u'cr', u'addons', u'xen4')
    for c in choices:
        pattern = u'/' + c + u'/'
        if pattern in path:
            return c
    return None

def repo_prefix(path, category, ver):

    prefix = None
    # we don't set prefix on repos that happen to be under 'test'
    # as we don't provide repo files for them on the mirrormanager.
    isTest = u'test/' in path
    if isTest:
        return None
    # assign shortnames to repositories like yum default mirrorlists expects
    isDebug = u'debug' in path
    isRawhide = u'rawhide' in path
    isDevelopment = is_development(path) is not None
    isSource = u'source' in path or u'SRPMS' in path
    isUpdatesTesting = u'updates/testing' in path
    isPlayground = u'playground' in path
    isTesting = u'testing' in path
    isReleases = u'releases' in path
    isUpdatesReleased = False
    if not isUpdatesTesting:
        isUpdatesReleased = u'updates' in path
    isAtomic = u'atomic' in path
    isEverything = u'Everything' in path
    isFedora = u'Fedora' in path
    isServer = u'Server' in path
    isModular = u'Modular' in path


    isEpel = (category.name == u'Fedora EPEL')
    isFedoraLinux = (category.name == u'Fedora Linux')
    isFedoraSecondary = (category.name == u'Fedora Secondary Arches')
    isFedoraArchive = (category.name == u'Fedora Archive')

    isRrpmfusionFreeEl = (category.name == u'RPMFUSION free EL')
    isRrpmfusionFreeFedora = (category.name == u'RPMFUSION free Fedora')
    isRrpmfusionNonfreeEl = (category.name == u'RPMFUSION nonfree EL')
    isRrpmfusionNonfreeFedora = (category.name == u'RPMFUSION nonfree Fedora')
    isCentOS = (category.name == u'CentOS')
    isRhel = (category.name == u'RHEL')

    isCodecs = (category.name == u'Fedora Codecs')

    version = u'unknown'
    if not isRawhide and ver is not None:
        version = ver.name
    if isDevelopment:
        version = is_development(path)

    if isEpel:
        # epel-
        modular = u''
        if isModular:
            modular = u'modular-'
        if isTesting:
            # testing-
            if isDebug:
                prefix = u'testing-%sdebug-epel%s' % (modular, version)
            elif isSource:
                prefix = u'testing-%ssource-epel%s' % (modular, version)
            elif isSource:
                prefix = u'testing-%ssource-epel%s' % (modular, version)
            else:
                prefix = u'testing-%sepel%s' % (modular, version)
        elif isPlayground:
            if isDebug:
                prefix = u'playground-%sdebug-epel%s' % (modular, version)
            elif isSource:
                prefix = u'playground-%ssource-epel%s' % (modular, version)
            else:
                prefix = u'playground-%sepel%s' % (modular, version)
        else:
            if isDebug:
                prefix = u'epel-%sdebug-%s' % (modular, version)
            elif isSource:
                prefix = u'epel-%ssource-%s' % (modular, version)
            else:
                prefix = u'epel-%s%s' % (modular, version)

    elif isFedoraLinux or isFedoraSecondary or isFedoraArchive:
        if isReleases or isDevelopment:
            if isEverything:
                if isRawhide:
                    # rawhide
                    if isDebug:
                        prefix = u'rawhide-debug'
                    elif isSource:
                        prefix = u'rawhide-source'
                    else:
                        prefix = u'rawhide'
                # fedora-
                elif isDebug:
                    prefix = u'fedora-debug-%s' % version
                elif isSource:
                    prefix = u'fedora-source-%s' % version
                else:
                    prefix=u'fedora-%s' % version
            elif isModular:
                # fedora-modular-
                if isDebug:
                    prefix = u'fedora-modular-debug-%s' % version
                elif isSource:
                    prefix = u'fedora-modular-source-%s' % version
                else:
                    prefix=u'fedora-modular-%s' % version
            elif isFedora:
                if isDebug or isSource:
                    # ignore releases/$version/Fedora/$arch/debug/
                    # ignore releases/$version/Fedora/source/SRPMS/
                    prefix = None
                else:
                    # fedora-install-
                    prefix = u'fedora-install-%s' % version
        elif isModular:
            if isUpdatesReleased:
                # updates-released-modular-
                if isDebug:
                    prefix = u'updates-released-modular-debug-f%s' % version
                elif isSource:
                    prefix = u'updates-released-modular-source-f%s' % version
                else:
                    prefix = u'updates-released-modular-f%s' % version
            elif isUpdatesTesting:
                # updates-testing-modular-
                if isDebug:
                    prefix = u'updates-testing-modular-debug-f%s' % version
                elif isSource:
                    prefix = u'updates-testing-modular-source-f%s' % version
                else:
                    prefix = u'updates-testing-modular-f%s' % version
            elif isRawhide:
                # rawhide-modular
                if isDebug:
                    prefix = u'rawhide-modular-debug'
                elif isSource:
                    prefix = u'rawhide-modular-source'
                else:
                    prefix = u'rawhide-modular'
            # fedora-modular-
            elif isDebug:
                prefix = u'fedora-modular-debug-%s' % version
            elif isSource:
                prefix = u'fedora-modular-source-%s' % version
            else:
                prefix=u'fedora-modular-%s' % version

        elif isAtomic:
            # atomic
            prefix = u'atomic-%s' % version
        elif isUpdatesReleased and isEverything:
            # updates-released-
            if isDebug:
                prefix = u'updates-released-debug-f%s' % version
            elif isSource:
                prefix = u'updates-released-source-f%s' % version
            else:
                prefix = u'updates-released-f%s' % version
        elif isUpdatesTesting and isEverything:
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

    elif isRhel:
        isBeta = u'beta' in path
        isOptional= u'optional' in path
        isCS = u'ClusteredStorage' in path
        isHA = u'HighAvailability' in path
        isLFS = u'LargeFileSystem' in path
        isLB = u'LoadBalance' in path

        if isCS:
            prefix = u'rhel-%s-clusteredstorage' % version
        elif isHA:
            prefix = u'rhel-%s-highavailability' % version
        elif isLFS:
            prefix = u'rhel-%s-largefilesystem' % version
        elif isLB:
            prefix = u'rhel-%s-loadbalance' % version
        elif isOptional:
            if isSource:
                prefix = u'rhel-optional-source-%s' % version
            elif isDebug:
                prefix = u'rhel-optional-debug-%s' % version
            else:
                prefix = u'rhel-optional-%s' % version
        else:
            if isDebug:
                prefix = u'rhel-debug-%s' % version
            elif isSource:
                prefix = u'rhel-source-%s' % version
            else:
                prefix = u'rhel-%s' % version

        if prefix and isBeta:
            prefix = u'%s-beta' % prefix

    elif isCentOS:
        prefix = centos_prefix(path)

    elif isCodecs:
        debug = u''
        if isDebug:
            debug = u'debug-'
        prefix = 'fedora-cisco-openh264-%s%s' % (debug, version)

    return prefix
