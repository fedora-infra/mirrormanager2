from mirrorsmanager.model import *
import socket
import re
import pickle
import bz2

redhat = None
core = None
fedora = None
epel = None

def add_test_groups_and_users():
    Group(group_name='user', display_name='User')
    Group(group_name='sysadmin', display_name='Admin')
    u = User(user_name='test', email_address='test@fedoraproject.org', display_name='Test', password='test')
    u.addGroup(Group.by_group_name('user'))
    test2 = User(user_name='test2', email_address='test2@fedoraproject.org', display_name='Test2', password='test')
    test2.addGroup(Group.by_group_name('user'))
    a = User(user_name='admin', email_address='admin@fedoraproject.org', display_name='Admin', password='admin')
    a.addGroup(Group.by_group_name('user'))
    a.addGroup(Group.by_group_name('sysadmin'))


def make_directories():
    testfiles = {'Fedora Core':'../fedora-test-data/fedora-linux-core-dirsonly.txt', 'Fedora Extras': '../fedora-test-data/fedora-linux-extras-dirsonly.txt'}
    for cname, file in testfiles.iteritems():
        f = open(file, 'r')
        try:
            category = Category.byName(cname)
        except:
            category = None
        try:
            for line in f:
                line = line.strip()
                if re.compile('^\.$').match(line):
                    name = 'pub/fedora/linux/%s' % (cname)
                    # Directory(name=name, category=category) was made already
                else:
                    name = 'pub/fedora/linux/%s/%s' % (cname, line)
                    child = Directory(name=name)
                    child.addCategory(category)
                    
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
    if 'SRPMS' in path:
        arch = Arch.byName('source')
    else:
        for a in Arch.select():
            s = '.*(^|/)%s(/|$).*' % (a.name)
            if re.compile(s).match(path):
                arch = a
                break

    ver = None
    for v in Version.selectBy(product=category.product):
        s = '.*(^|/)%s(/|$).*' % (v.name)
        if re.compile(s).match(path):
            ver = v
            break

    return (ver, arch)


# lines look like
# -rw-r--r--         951 2007/01/10 14:17:39 updates/testing/6/SRPMS/repodata/repomd.xml
def make_repositories():
    testfiles = {'Fedora Core':'../fedora-test-data/fedora-linux-core.txt', 'Fedora Extras': '../fedora-test-data/fedora-linux-extras.txt'}
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
                    cat = Category.byName(category)
                    (ver, arch) = guess_ver_arch_from_path(cat, path)
                    path = trim_os_from_dirname(path)
                    dirname = 'pub/fedora/linux/%s/%s'  % (category, path)
                    name=path.split('/')
                    name = rename_SRPMS_source(name)
                    name='-'.join(name)
                    name='%s-%s-%s' % (cat.product.name, category, name)
                    shortname = '%s-%s' % (category, ver)
                    dir = Directory.byName(dirname)
                    Repository(name=name, category=cat, version=ver, arch=arch, directory=dir)

        finally:
            f.close()
    # assign shortnames to repositories like yum default mirrorlists expects
    
        


def make_sites():
    testfiles = {'Fedora Core':'../fedora-test-data/mirror-hosts-core.txt', 'Fedora Extras': '../fedora-test-data/mirror-hosts-extras.txt'}
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
                    site = Site(name=name, password="password", private=False)
                else:
                    site = Site.select(Site.q.name==name)[0]

                if Host.select(Host.q.name==name).count() == 0:
                    host = Host(site=site, name=name)

        finally:
            f.close()



def make_versions():
    # create our default versions
    versions = []
    for ver in range(1,8):
        versions.append(str(ver))
    versions.append('development')
    for ver in versions:
        Version(name=ver, product=fedora)
    Version(name='6.90', product=fedora, isTest=True)

    for ver in ['4', '5']:
        Version(name=ver, product=epel)

def make_embargoed_countries():
    for cc in ['cu', 'ir', 'iq', 'kp', 'sd', 'sy' ]:
        EmbargoedCountry(country_code=cc)



#check if a configuration already exists. Create one if it doesn't
if not Arch.select().count():
    print "Creating Arches"
    for a in ['source', 'i386', 'x86_64', 'ppc', 'ppc64', 'sparc', 'ia64']:
        Arch(name=a)


if not Site.select().count() and not Host.select().count():
    print "Creating Sites and Hosts"
    redhat = Site(name='Red Hat', password="password", orgUrl="http://www.redhat.com", private=True)
    Host(name='master', site=redhat)
    for n in range(1,4):
        host = Host(name='download%s.fedora.redhat.com' % n, site=redhat)
    pt = Host(name='publictest7.fedora.redhat.com', site=redhat)
    HostAclIp(host=pt, ip='publictest7.fedora.redhat.com')

    dell = Site(name='Dell', private=True, password="password", orgUrl="http://www.dell.com")
    Host(name='linuxlib.us.dell.com', site=dell)
    humbolt = Host(name='humbolt.us.dell.com', site=dell)
    f = open('../fedora-test-data/humbolt-pickle.bz2')
    pbz = f.read()
    f.close()
    humbolt.config = pickle.loads(bz2.decompress(pbz))
    
    



if not SiteAdmin.select().count():
    SiteAdmin(username='mdomsch', site=redhat)
    SiteAdmin(username='mdomsch', site=dell)

# create our default products
epel = Product(name='EPEL')
fedora = Product(name='Fedora')


if not Version.select().count():
    make_versions()

if not EmbargoedCountry.select().count():
    make_embargoed_countries()

# create our default Categories
directory = Directory(name='pub/fedora/linux/core')
core = Category(name='Fedora Core',
                product = fedora,
                topdir = directory)
directory.addCategory(core)

directory = Directory(name='pub/fedora/linux/extras')
extras = Category(name='Fedora Extras',
                  product = fedora,
                  topdir = directory)
directory.addCategory(extras)

directory = Directory(name='pub/fedora/linux/releases')
releases = Category(name='Fedora Releases',
                   product = fedora,
                   topdir = directory)
directory.addCategory(releases)

directory = Directory(name='pub/epel')
epel = Category(name='Fedora EPEL',
                product = epel,
                topdir=directory)
directory.addCategory(epel)


#make_directories()

#if not Repository.select().count():
#    make_repositories()

#make_sites()
#make_mirrors()
#add_test_groups_and_users()
