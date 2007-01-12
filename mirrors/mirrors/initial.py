from mirrors.model import *
import socket
import re

redhat = None
core = None
fedora = None
rhel = None


def make_directories():
    testfiles = {'core':'../fedora-test-data/fedora-linux-core-dirsonly.txt', 'extras': '../fedora-test-data/fedora-linux-extras-dirsonly.txt'}
    for category, file in testfiles.iteritems():
        f = open(file, 'r')
        try:
            for line in f:
                line = line.strip()
                if re.compile('^\.$').match(line):
                    name = 'pub/fedora/linux/%s' % (category)
                    Directory(name=name)
                else:
                    name = 'pub/fedora/linux/%s/%s' % (category, line)
                    parent = None
                    index = name.rfind('/')
                    if index > 0:
                        parentname = name[:index]
                        parent = Directory.select(Directory.q.name==parentname)
                        if parent.count():
                            parent = parent[0]

                        child = Directory(name=name)
                        DirectoryTree(parent=parent, child=child)
                    
        finally:
            f.close()

def trim_os_from_dirname(dirname):
    # trim the /os off the name
    index = dirname.rfind('/os')
    if index > 0:
        dirname = dirname[:index]
    return dirname

def rename_SRPMS_source(l):
    rc = []
    for i in l:
        if i == 'source':
            pass
        elif i == 'SRPMS':
            rc.append('source')
        else:
            rc.append(i)
    return rc

def guess_ver_arch_from_path(category, path):
    arch = None
    for a in Arch.select():
        if path.find(a.name) != -1:
            arch = a
    if path.find('SRPMS') != -1:
        arch = Arch.select(Arch.q.name=='source')

    ver = None
    for v in Version.select(Version.q.productID==category.product.id):
        s = '/%s' % (v.name)
        if path.find(s) != -1:
            ver = v

    return (ver, arch)

        


# lines look like
# -rw-r--r--         951 2007/01/10 14:17:39 updates/testing/6/SRPMS/repodata/repomd.xml
def make_repositories():
    testfiles = {'core':'../fedora-test-data/fedora-linux-core.txt', 'extras': '../fedora-test-data/fedora-linux-extras.txt'}
    for category, file in testfiles.iteritems():
        f = open(file, 'r')
        try:
            for line in f:
                line = line.strip()
                index = line.find('/repodata/repomd.xml')
                if index > 0:
                    path = line.split()[4]
                    index = path.find('/repodata/repomd.xml')
                    path = path[:index]
                    cat = Category.select(Category.q.name==category)[0]
                    (ver, arch) = guess_ver_arch_from_path(cat, path)
                    path = trim_os_from_dirname(path)
                    dirname = 'pub/fedora/linux/%s/%s'  % (category, path)
                    name=path.split('/')
                    name = rename_SRPMS_source(name)
                    name='-'.join(name)
                    name='%s-%s-%s' % (cat.product.name, category, name)
                    dirs = Directory.select(Directory.q.name==dirname)
                    dir = None
                    if dirs.count() > 0:
                        dir = dirs[0]
                    Repository(name=name, category=cat, version=ver, arch=arch, directory=dir)

        finally:
            f.close()
        


def make_sites():
    testfiles = {'core':'../fedora-test-data/mirror-hosts-core.txt', 'extras': '../fedora-test-data/mirror-hosts-extras.txt'}
    for category, file in testfiles.iteritems():
        # These are all fedora-core-6 mirrors, but they may not carry all arches or content.
        # That's ok, we'll figure out what they've got.
        # Turns out these all also carry fc5 too.
        f = open(file, 'r')
        try:
            for line in f:
                line = line.strip()
                s = line.split('/')
                index = line.find('://')
                protocol = line[:(index+3)]
                name = s[2]
                path = s[3:]
                    
                if Site.select(Site.q.name==name).count() == 0:
                    site = Site(name=name)
                else:
                    site = Site.select(Site.q.name==name)[0]

                ip = socket.gethostbyname(name)
                if ip is not None:
                    SiteIP(site=site, address=ip)

                host = Host(site=site, name=name, pull_from=redhat)
                path = '/'.join(path)
                index = path.find('/6/$ARCH')
                path = path[:index]
                url = '%s%s%s' % (protocol, name, path)
                hc = HostCategory(host=host, category=Category.select(Category.q.name==category)[0])
                HostCategoryURL(hostcategory=hc, protocol=protocol, path=path)

        finally:
            f.close()

def mirrordir_to_url(mirrorDirectory):
    url = mirrorDirectory.url
    hostcategory = url.hostcategory
    category = hostcategory.category
    cdir = category.directory
    # fixme not sure what I should be doing here...
    # this sucks
    
    
    
    
    

                
# fixme!!
def make_mirrors_subdirs(host, path, directory):
    """Recursively walk the directory tree from this point down
    adding new Mirrors"""
    for s in DirectoryTree.select(DirectoryTree.q.parent==directory):
       # Mirror(host=cu.host, path='something', directory=s.child)
        pass


def make_mirrors():
    for host in Host.select():
        for cu in host.categoryURLs:
            directory    = Directory.get(cu.category.directory.id)
            # fixme find path below cu.path that matches directory
            path = '%s/%s' % (cu.url, 'something')
            MirrorDirectory(directory=directory, url=cu, path=path)
#            make_mirrors_subdirs(cu.host, cu.path, directory)
                



def make_versions():
    # create our default versions
    versions = []
    for ver in range(1,7):
        versions.append(str(ver))
    versions.append('development')
    for ver in versions:
        Version(name=ver, product=fedora)
    Version(name='6.90', product=fedora, isTest=True)

    for ver in ['4', '5']:
        Version(name=ver, product=rhel)



#check if a configuration already exists. Create one if it doesn't
if not Arch.select().count():
    print "Creating Arches"
    Arch(name='source')
    Arch(name='i386')
    Arch(name='x86_64')
    Arch(name='ppc')


if not Site.select().count() and not Host.select().count():
    print "Creating Sites and Hosts"
    redhat = Site(name='Red Hat', admin_active=True, user_active=True)
    Host(name='master', pull_from=None, site=redhat)
    Host(name='download1.fedora.redhat.com', pull_from=redhat, site=redhat)
    Host(name='download2.fedora.redhat.com', pull_from=redhat, site=redhat)
    Host(name='download3.fedora.redhat.com', pull_from=redhat, site=redhat)

    dell = Site(name='Dell', admin_active=True, user_active=True, private=True)
    Host(name='humbolt.us.dell.com', pull_from=redhat, site=dell)
    Host(name='linuxlib.us.dell.com', pull_from=dell, site=dell)

    korg = Site(name='kernel.org', admin_active=True, user_active=True)
    Host(name='mirrors.kernel.org', pull_from=redhat, site=korg)
    

if not SiteAdmin.select().count():
    SiteAdmin(username='mdomsch', site=redhat)
    SiteAdmin(username='mdomsch', site=dell)
    SiteAdmin(username='hpa', site=korg)

# create our default products
rhel = Product(name='rhel')
fedora = Product(name='fedora')


if not Version.select().count():
    make_versions()

if not Directory.select().count():
    make_directories()

# create our default Repositories
core = Category(name='core',
                product = fedora,
                directory = Directory.select(Directory.q.name=='pub/fedora/linux/core')[0])

extras = Category(name='extras',
                  product = fedora,
                  directory = Directory.select(Directory.q.name=='pub/fedora/linux/extras')[0])


# release = Category(name='release',
#                    product = fedora,
#                    directory = Directory.select(Directory.q.name=='pub/fedora/linux/release')[0])

# epel = Category(name='epel',
#                 product = rhel,
#                 directory = Directory.select(Directory.q.name=='pub/epel/')[0])

                



if not Repository.select().count():
    make_repositories()

make_sites()
#make_mirrors()
