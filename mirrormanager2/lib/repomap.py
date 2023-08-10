import re


def is_development(path):
    development_re = r"\/?development\/((\d+))/"
    m = re.search(re.compile(development_re), path)
    if m is not None:
        return m.group(1)
    return None


def centos_prefix(path):
    choices = (
        "os",
        "updates",
        "extras",
        "centosplus",
        "contrib",
        "fasttrack",
        "cr",
        "addons",
        "xen4",
    )
    for c in choices:
        pattern = "/" + c + "/"
        if pattern in path:
            return c
    return None


def repo_prefix(path, category, ver):
    prefix = None
    # we don't set prefix on repos that happen to be under 'test'
    # as we don't provide repo files for them on the mirrormanager.
    isTest = "test/" in path
    if isTest:
        return None
    # assign shortnames to repositories like yum default mirrorlists expects
    isDebug = "debug" in path
    isRawhide = "rawhide" in path
    isDevelopment = is_development(path) is not None
    isSource = "source" in path or "SRPMS" in path
    isUpdatesTesting = "updates/testing" in path
    isPlayground = "playground" in path
    isTesting = "testing" in path
    isReleases = "releases" in path
    isUpdatesReleased = False
    if not isUpdatesTesting:
        isUpdatesReleased = "updates" in path
    isAtomic = "atomic" in path
    isEverything = "Everything" in path
    isFedora = "Fedora" in path
    isModular = "Modular" in path

    isEpel = category.name == "Fedora EPEL"
    isFedoraLinux = category.name == "Fedora Linux"
    isFedoraSecondary = category.name == "Fedora Secondary Arches"
    isFedoraArchive = category.name == "Fedora Archive"

    isRrpmfusionFreeEl = category.name == "RPMFUSION free EL"
    isRrpmfusionFreeFedora = category.name == "RPMFUSION free Fedora"
    isRrpmfusionNonfreeEl = category.name == "RPMFUSION nonfree EL"
    isRrpmfusionNonfreeFedora = category.name == "RPMFUSION nonfree Fedora"
    isCentOS = category.name == "CentOS"
    isRhel = category.name == "RHEL"

    isCodecs = category.name == "Fedora Codecs"

    version = "unknown"
    if not isRawhide and ver is not None:
        version = ver.name
    if isDevelopment:
        version = is_development(path)

    if isEpel:
        # epel-
        modular = ""
        if isModular:
            modular = "modular-"
        if isTesting:
            # testing-
            if isDebug:
                prefix = f"testing-{modular}debug-epel{version}"
            elif isSource:
                prefix = f"testing-{modular}source-epel{version}"
            elif isSource:
                prefix = f"testing-{modular}source-epel{version}"
            else:
                prefix = f"testing-{modular}epel{version}"
        elif isPlayground:
            if isDebug:
                prefix = f"playground-{modular}debug-epel{version}"
            elif isSource:
                prefix = f"playground-{modular}source-epel{version}"
            else:
                prefix = f"playground-{modular}epel{version}"
        else:
            if isDebug:
                prefix = f"epel-{modular}debug-{version}"
            elif isSource:
                prefix = f"epel-{modular}source-{version}"
            else:
                prefix = f"epel-{modular}{version}"

    elif isFedoraLinux or isFedoraSecondary or isFedoraArchive:
        if isReleases or isDevelopment:
            if isEverything:
                if isRawhide:
                    # rawhide
                    if isDebug:
                        prefix = "rawhide-debug"
                    elif isSource:
                        prefix = "rawhide-source"
                    else:
                        prefix = "rawhide"
                # fedora-
                elif isDebug:
                    prefix = "fedora-debug-%s" % version
                elif isSource:
                    prefix = "fedora-source-%s" % version
                else:
                    prefix = "fedora-%s" % version
            elif isModular:
                # fedora-modular-
                if isDebug:
                    prefix = "fedora-modular-debug-%s" % version
                elif isSource:
                    prefix = "fedora-modular-source-%s" % version
                else:
                    prefix = "fedora-modular-%s" % version
            elif isFedora:
                if isDebug or isSource:
                    # ignore releases/$version/Fedora/$arch/debug/
                    # ignore releases/$version/Fedora/source/SRPMS/
                    prefix = None
                else:
                    # fedora-install-
                    prefix = "fedora-install-%s" % version
        elif isModular:
            if isUpdatesReleased:
                # updates-released-modular-
                if isDebug:
                    prefix = "updates-released-modular-debug-f%s" % version
                elif isSource:
                    prefix = "updates-released-modular-source-f%s" % version
                else:
                    prefix = "updates-released-modular-f%s" % version
            elif isUpdatesTesting:
                # updates-testing-modular-
                if isDebug:
                    prefix = "updates-testing-modular-debug-f%s" % version
                elif isSource:
                    prefix = "updates-testing-modular-source-f%s" % version
                else:
                    prefix = "updates-testing-modular-f%s" % version
            elif isRawhide:
                # rawhide-modular
                if isDebug:
                    prefix = "rawhide-modular-debug"
                elif isSource:
                    prefix = "rawhide-modular-source"
                else:
                    prefix = "rawhide-modular"
            # fedora-modular-
            elif isDebug:
                prefix = "fedora-modular-debug-%s" % version
            elif isSource:
                prefix = "fedora-modular-source-%s" % version
            else:
                prefix = "fedora-modular-%s" % version

        elif isAtomic:
            # atomic
            prefix = "atomic-%s" % version
        elif isUpdatesReleased and isEverything:
            # updates-released-
            if isDebug:
                prefix = "updates-released-debug-f%s" % version
            elif isSource:
                prefix = "updates-released-source-f%s" % version
            else:
                prefix = "updates-released-f%s" % version
        elif isUpdatesTesting and isEverything:
            # updates-testing-
            if isDebug:
                prefix = "updates-testing-debug-f%s" % version
            elif isSource:
                prefix = "updates-testing-source-f%s" % version
            else:
                prefix = "updates-testing-f%s" % version
        elif isRawhide:
            # rawhide
            if isDebug:
                prefix = "rawhide-debug"
            elif isSource:
                prefix = "rawhide-source"
            else:
                prefix = "rawhide"

    elif isRrpmfusionFreeEl:
        if isReleases:
            if not isEverything:
                prefix = None
            # free-el
            elif isDebug:
                prefix = "free-el-debug-%s" % version
            elif isSource:
                prefix = "free-el-source-%s" % version
            else:
                prefix = "free-el-%s" % version

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = "free-el-updates-released-debug-%s" % version
            elif isSource:
                prefix = "free-el-updates-released-source-%s" % version
            else:
                prefix = "free-el-updates-released-%s" % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = "free-el-updates-testing-debug-%s" % version
            elif isSource:
                prefix = "free-el-updates-testing-source-%s" % version
            else:
                prefix = "free-el-updates-testing-%s" % version

    elif isRrpmfusionNonfreeEl:
        if isReleases:
            if not isEverything:
                prefix = None
            # nonfree-el
            elif isDebug:
                prefix = "nonfree-el-debug-%s" % version
            elif isSource:
                prefix = "nonfree-el-source-%s" % version
            else:
                prefix = "nonfree-el-%s" % version

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = "nonfree-el-updates-released-debug-%s" % version
            elif isSource:
                prefix = "nonfree-el-updates-released-source-%s" % version
            else:
                prefix = "nonfree-el-updates-released-%s" % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = "nonfree-el-updates-testing-debug-%s" % version
            elif isSource:
                prefix = "nonfree-el-updates-testing-source-%s" % version
            else:
                prefix = "nonfree-el-updates-testing-%s" % version

    elif isRrpmfusionFreeFedora:
        if isReleases:
            if not isEverything:
                prefix = None
            # free-fedora
            elif isDebug:
                prefix = "free-fedora-debug-%s" % version
            elif isSource:
                prefix = "free-fedora-source-%s" % version
            else:
                prefix = "free-fedora-%s" % version

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = "free-fedora-updates-released-debug-%s" % version
            elif isSource:
                prefix = "free-fedora-updates-released-source-%s" % version
            else:
                prefix = "free-fedora-updates-released-%s" % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = "free-fedora-updates-testing-debug-%s" % version
            elif isSource:
                prefix = "free-fedora-updates-testing-source-%s" % version
            else:
                prefix = "free-fedora-updates-testing-%s" % version
        elif isRawhide:
            # rawhide
            if isDebug:
                prefix = "free-fedora-rawhide-debug"
            elif isSource:
                prefix = "free-fedora-rawhide-source"
            else:
                prefix = "free-fedora-rawhide"

    elif isRrpmfusionNonfreeFedora:
        if isReleases:
            if not isEverything:
                prefix = None
            # nonfree-fedora
            elif isDebug:
                prefix = "nonfree-fedora-debug-%s" % version
            elif isSource:
                prefix = "nonfree-fedora-source-%s" % version
            else:
                prefix = "nonfree-fedora-%s" % version

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = "nonfree-fedora-updates-released-debug-%s" % version
            elif isSource:
                prefix = "nonfree-fedora-updates-released-source-%s" % version
            else:
                prefix = "nonfree-fedora-updates-released-%s" % version

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = "nonfree-fedora-updates-testing-debug-%s" % version
            elif isSource:
                prefix = "nonfree-fedora-updates-testing-source-%s" % version
            else:
                prefix = "nonfree-fedora-updates-testing-%s" % version
        elif isRawhide:
            # rawhide
            if isDebug:
                prefix = "nonfree-fedora-rawhide-debug"
            elif isSource:
                prefix = "nonfree-fedora-rawhide-source"
            else:
                prefix = "nonfree-fedora-rawhide"

    elif isRhel:
        isBeta = "beta" in path
        isOptional = "optional" in path
        isCS = "ClusteredStorage" in path
        isHA = "HighAvailability" in path
        isLFS = "LargeFileSystem" in path
        isLB = "LoadBalance" in path

        if isCS:
            prefix = "rhel-%s-clusteredstorage" % version
        elif isHA:
            prefix = "rhel-%s-highavailability" % version
        elif isLFS:
            prefix = "rhel-%s-largefilesystem" % version
        elif isLB:
            prefix = "rhel-%s-loadbalance" % version
        elif isOptional:
            if isSource:
                prefix = "rhel-optional-source-%s" % version
            elif isDebug:
                prefix = "rhel-optional-debug-%s" % version
            else:
                prefix = "rhel-optional-%s" % version
        else:
            if isDebug:
                prefix = "rhel-debug-%s" % version
            elif isSource:
                prefix = "rhel-source-%s" % version
            else:
                prefix = "rhel-%s" % version

        if prefix and isBeta:
            prefix = "%s-beta" % prefix

    elif isCentOS:
        prefix = centos_prefix(path)

    elif isCodecs:
        debug = ""
        if isDebug:
            debug = "debug-"
        prefix = f"fedora-cisco-openh264-{debug}{version}"

    return prefix
