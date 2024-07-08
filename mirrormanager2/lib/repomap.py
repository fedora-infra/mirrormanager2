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
                    prefix = f"fedora-debug-{version}"
                elif isSource:
                    prefix = f"fedora-source-{version}"
                else:
                    prefix = f"fedora-{version}"
            elif isModular:
                # fedora-modular-
                if isDebug:
                    prefix = f"fedora-modular-debug-{version}"
                elif isSource:
                    prefix = f"fedora-modular-source-{version}"
                else:
                    prefix = f"fedora-modular-{version}"
            elif isFedora:
                if isDebug or isSource:
                    # ignore releases/$version/Fedora/$arch/debug/
                    # ignore releases/$version/Fedora/source/SRPMS/
                    prefix = None
                else:
                    # fedora-install-
                    prefix = f"fedora-install-{version}"
        elif isModular:
            if isUpdatesReleased:
                # updates-released-modular-
                if isDebug:
                    prefix = f"updates-released-modular-debug-f{version}"
                elif isSource:
                    prefix = f"updates-released-modular-source-f{version}"
                else:
                    prefix = f"updates-released-modular-f{version}"
            elif isUpdatesTesting:
                # updates-testing-modular-
                if isDebug:
                    prefix = f"updates-testing-modular-debug-f{version}"
                elif isSource:
                    prefix = f"updates-testing-modular-source-f{version}"
                else:
                    prefix = f"updates-testing-modular-f{version}"
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
                prefix = f"fedora-modular-debug-{version}"
            elif isSource:
                prefix = f"fedora-modular-source-{version}"
            else:
                prefix = f"fedora-modular-{version}"

        elif isAtomic:
            # atomic
            prefix = f"atomic-{version}"
        elif isUpdatesReleased and isEverything:
            # updates-released-
            if isDebug:
                prefix = f"updates-released-debug-f{version}"
            elif isSource:
                prefix = f"updates-released-source-f{version}"
            else:
                prefix = f"updates-released-f{version}"
        elif isUpdatesTesting and isEverything:
            # updates-testing-
            if isDebug:
                prefix = f"updates-testing-debug-f{version}"
            elif isSource:
                prefix = f"updates-testing-source-f{version}"
            else:
                prefix = f"updates-testing-f{version}"
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
                prefix = f"free-el-debug-{version}"
            elif isSource:
                prefix = f"free-el-source-{version}"
            else:
                prefix = f"free-el-{version}"

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = f"free-el-updates-released-debug-{version}"
            elif isSource:
                prefix = f"free-el-updates-released-source-{version}"
            else:
                prefix = f"free-el-updates-released-{version}"

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = f"free-el-updates-testing-debug-{version}"
            elif isSource:
                prefix = f"free-el-updates-testing-source-{version}"
            else:
                prefix = f"free-el-updates-testing-{version}"

    elif isRrpmfusionNonfreeEl:
        if isReleases:
            if not isEverything:
                prefix = None
            # nonfree-el
            elif isDebug:
                prefix = f"nonfree-el-debug-{version}"
            elif isSource:
                prefix = f"nonfree-el-source-{version}"
            else:
                prefix = f"nonfree-el-{version}"

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = f"nonfree-el-updates-released-debug-{version}"
            elif isSource:
                prefix = f"nonfree-el-updates-released-source-{version}"
            else:
                prefix = f"nonfree-el-updates-released-{version}"

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = f"nonfree-el-updates-testing-debug-{version}"
            elif isSource:
                prefix = f"nonfree-el-updates-testing-source-{version}"
            else:
                prefix = f"nonfree-el-updates-testing-{version}"

    elif isRrpmfusionFreeFedora:
        if isReleases:
            if not isEverything:
                prefix = None
            # free-fedora
            elif isDebug:
                prefix = f"free-fedora-debug-{version}"
            elif isSource:
                prefix = f"free-fedora-source-{version}"
            else:
                prefix = f"free-fedora-{version}"

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = f"free-fedora-updates-released-debug-{version}"
            elif isSource:
                prefix = f"free-fedora-updates-released-source-{version}"
            else:
                prefix = f"free-fedora-updates-released-{version}"

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = f"free-fedora-updates-testing-debug-{version}"
            elif isSource:
                prefix = f"free-fedora-updates-testing-source-{version}"
            else:
                prefix = f"free-fedora-updates-testing-{version}"
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
                prefix = f"nonfree-fedora-debug-{version}"
            elif isSource:
                prefix = f"nonfree-fedora-source-{version}"
            else:
                prefix = f"nonfree-fedora-{version}"

        elif isUpdatesReleased:
            # updates-released-
            if isDebug:
                prefix = f"nonfree-fedora-updates-released-debug-{version}"
            elif isSource:
                prefix = f"nonfree-fedora-updates-released-source-{version}"
            else:
                prefix = f"nonfree-fedora-updates-released-{version}"

        elif isUpdatesTesting:
            # updates-testing-
            if isDebug:
                prefix = f"nonfree-fedora-updates-testing-debug-{version}"
            elif isSource:
                prefix = f"nonfree-fedora-updates-testing-source-{version}"
            else:
                prefix = f"nonfree-fedora-updates-testing-{version}"
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
            prefix = f"rhel-{version}-clusteredstorage"
        elif isHA:
            prefix = f"rhel-{version}-highavailability"
        elif isLFS:
            prefix = f"rhel-{version}-largefilesystem"
        elif isLB:
            prefix = f"rhel-{version}-loadbalance"
        elif isOptional:
            if isSource:
                prefix = f"rhel-optional-source-{version}"
            elif isDebug:
                prefix = f"rhel-optional-debug-{version}"
            else:
                prefix = f"rhel-optional-{version}"
        else:
            if isDebug:
                prefix = f"rhel-debug-{version}"
            elif isSource:
                prefix = f"rhel-source-{version}"
            else:
                prefix = f"rhel-{version}"

        if prefix and isBeta:
            prefix = f"{prefix}-beta"

    elif isCentOS:
        prefix = centos_prefix(path)

    elif isCodecs:
        debug = ""
        if isDebug:
            debug = "debug-"
        prefix = f"fedora-cisco-openh264-{debug}{version}"

    return prefix
