from mirrors.model import *
import socket
import re


def make_content(ver, category, arch):
    reponame = '%s-%s-%s-%s' % (ver.product.name, category.name, ver.name, arch.name)
    path = re.sub('\$VERSION', ver.name, category.path)
    path = re.sub('\$ARCH', arch.name, path)
    sourcepkgpath = re.sub('\$VERSION', ver.name, category.sourcepkgpath)
    if category.sourceisopath is not None:
        sourceisopath = re.sub('\$VERSION', ver.name, category.sourceisopath)
    print "Content(name=%s)" % (reponame)
    if arch.name == 'source':
        Content(name=reponame, version=ver, arch=arch,
                category=category,
                path=sourcepkgpath)
    else:
        Content(name=reponame, version=ver, arch=arch,
                category=category,
                path=path)


#check if a configuration already exists. Create one if it doesn't
if not Arch.select().count():
    print "Creating Arches"
    Arch(name='source')
    Arch(name='i386')
    Arch(name='x86_64')
    Arch(name='ppc')


redhat = None

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


# create our default Categories
core = Category(name='core', path='pub/fedora/linux/core/$VERSION/$ARCH/',
                canonicalhost='http://download.fedora.redhat.com',
                sourcepkgpath='pub/fedora/linux/core/$VERSION/source/SRPMS/',
                sourceisopath='pub/fedora/linux/core/$VERSION/source/iso/')

updates = Category(name='updates',
                   path='pub/fedora/linux/core/updates/$VERSION/$ARCH/',
                   canonicalhost='http://download.fedora.redhat.com',
                   sourcepkgpath='pub/fedora/linux/core/updates/$VERSION/SRPMS/')

updates_testing = Category(name='updates-testing',
                           path='pub/fedora/linux/core/updates/testing/$VERSION/$ARCH/',
                           canonicalhost='http://download.fedora.redhat.com',
                           sourcepkgpath='pub/fedora/linux/core/updates/testing/$VERSION/SRPMS/')
extras = Category(name='extras',
                  path='pub/fedora/linux/extras/$VERSION/$ARCH/',
                  canonicalhost='http://download.fedora.redhat.com',
                  sourcepkgpath='pub/fedora/linux/extras/$VERSION/SRPMS/')
test = Category(name='test',
                path='pub/fedora/linux/core/test/$VERSION/$ARCH/',
                canonicalhost='http://download.fedora.redhat.com',
                sourcepkgpath='pub/fedora/linux/core/test/$VERSION/source/SRPMS/',
                sourceisopath='pub/fedora/linux/core/test/$VERSION/source/iso/')
epel = Category(name='epel',
                path='pub/epel/$VERSION/$ARCH',
                canonicalhost='http://download.fedora.redhat.com',
                sourcepkgpath='pub/epel/$VERSION/SRPMS/')
                

# create our default versions
versions = []
for ver in range(1,7):
    versions.append(str(ver))
versions.append('development')
for ver in versions:
    ProductVersion(name=ver, product=fedora)
ProductVersion(name='6.90', product=fedora, isTest=True)

for ver in ['4', '5']:
    ProductVersion(name=ver, product=rhel)



if not Content.select().count():
    # do Fedora major versions
    for ver in ProductVersion.select():
        if ver.product.name != 'fedora' or ver.isTest:
            continue
        for arch in Arch.select():
            for category in Category.select():
                if category.name not in [ 'epel', 'test' ]:
                    make_content(ver, category, arch)
                    
    # do Fedora test
    for ver in ProductVersion.select():
        if ver.product.name == 'fedora' and ver.isTest:
            for arch in Arch.select():
                make_content(ver, test, arch)

    # do RHEL EPEL
    for ver in ProductVersion.select():
        if ver.product.name == 'rhel':
            for arch in Arch.select():
                for category in Category.select(Category.q.name=='epel'):
                    make_content(ver, category, arch)

# These are all fedora-core-6 mirrors, but they may not carry all arches or content.
# That's ok, we'll figure out what they've got.
# Turns out these all also carry fc5 too.
initial_mirror_list = [
'http://redhat.download.fedoraproject.org/pub/fedora/linux/core/6/$ARCH/os/',
'http://ftp.fi.muni.cz/pub/linux/fedora-core/6/$ARCH/os/',
'ftp://ftp.tu-chemnitz.de/pub/linux/fedora-core/6/$ARCH/os/',
'ftp://ftp.wsisiz.edu.pl/pub/linux/fedora/linux/core/6/$ARCH/os/',
'http://ftp.ale.org/mirrors/fedora/linux/core/6/$ARCH/os/',
'http://ftp.uninett.no/pub/linux/Fedora/core/6/$ARCH/os/',
'http://ftp.tu-chemnitz.de/pub/linux/fedora-core/6/$ARCH/os/',
'http://sunsite.informatik.rwth-aachen.de/ftp/pub/linux/fedora-core/6/$ARCH/os/',
'ftp://ftp.tecnoera.com/pub/fedora/linux/core/6/$ARCH/os/',
'ftp://redhat.taygeta.com/pub/RedHat/fedora/core/6/$ARCH/os/',
'http://fr2.rpmfind.net/linux/fedora/core/6/$ARCH/os/',
'http://ftp.riken.jp/Linux/fedora/core/6/$ARCH/os/',
'http://zeniv.linux.org.uk/pub/distributions/fedora/linux/core/6/$ARCH/os/',
'http://zeniiia.linux.org.uk/pub/distributions/fedora/linux/core/6/$ARCH/os/',
'ftp://ftp.wicks.co.nz/pub/linux/dist/fedora/6/$ARCH/os/',
'ftp://ftp.rhd.ru/pub/fedora/linux/core/6/$ARCH/os/',
'http://ftp.rhd.ru/pub/fedora/linux/core/6/$ARCH/os/',
'ftp://ftp.ipex.cz/pub/linux/fedora/core/6/$ARCH/os/',
'http://fedora.cat.pdx.edu/linux/core/6/$ARCH/os/',
'ftp://falkor.skane.se/pub/mirrors/fedora/core/6/$ARCH/os/',
'ftp://ftp.cica.es/fedora/linux/core/6/$ARCH/os/',
'ftp://ftp.free.fr/mirrors/fedora.redhat.com/fedora/linux/core/6/$ARCH/os/',
'http://ftp.ussg.iu.edu/linux/fedora/linux/core/6/$ARCH/os/',
'http://ftp.surfnet.nl/ftp/pub/os/Linux/distr/fedora/6/$ARCH/os/',
'http://ftp.nluug.nl/ftp/pub/os/Linux/distr/fedora/6/$ARCH/os/',
'ftp://ftp.net.usf.edu/pub/fedora/linux/core/6/$ARCH/os/',
'http://www.muug.mb.ca/pub/fedora/linux/core/6/$ARCH/os/',
'http://mirror.eas.muohio.edu/fedora/linux/core/6/$ARCH/os/',
'http://sunsite.mff.cuni.cz/pub/fedora/6/$ARCH/os/',
'http://mirror.linux.duke.edu/pub/fedora/linux/core/6/$ARCH/os/',
'http://distro.ibiblio.org/pub/linux/distributions/fedora/linux/core/6/$ARCH/os/',
'http://mirror.hiwaay.net/redhat/fedora/linux/core/6/$ARCH/os/',
'ftp://mirrors.hpcf.upr.edu/pub/Mirrors/redhat/download.fedora.redhat.com/6/$ARCH/os/',
'http://redhat.secsup.org/fedora/core/6/$ARCH/os/',
'ftp://ftp.dc.aleron.net/pub/linux/fedora/linux/core/6/$ARCH/os/',
'ftp://mirror.newnanutilities.org/pub/fedora/linux/core/6/$ARCH/os/',
'ftp://ftp.software.umn.edu/pub/linux/fedora/core/6/$ARCH/os/',
'http://www.gtlib.gatech.edu/pub/fedora.redhat/linux/core/6/$ARCH/os/',
'ftp://fedora.mirrors.tds.net/pub/fedora-core/6/$ARCH/os/',
'http://fedora.cs.wisc.edu/pub/mirrors/linux/download.fedora.redhat.com/pub/fedora/linux/core/6/$ARCH/os/',
'http://ftp.ndlug.nd.edu/pub/fedora/linux/core/6/$ARCH/os/',
'http://fedora.server4you.net/fedora/core/6/$ARCH/os/',
'ftp://mirrors.ptd.net/fedora/core/6/$ARCH/os/',
'ftp://fedora.bu.edu/fedora/core/6/$ARCH/os/',
'http://mirror.pacific.net.au/linux/fedora/linux/core/6/$ARCH/os/',
'http://ftp.dulug.duke.edu/pub/fedora/linux/core/6/$ARCH/os/',
'http://mirrors.kernel.org/fedora/core/6/$ARCH/os/',
'http://ftp1.skynet.cz/pub/linux/fedora/6/$ARCH/os/',
'http://ftp.iij.ad.jp/pub/linux/fedora/core/6/$ARCH/os/',
'ftp://mirror.switch.ch/mirror/fedora/linux/core/6/$ARCH/os/',
'http://mirror.switch.ch/ftp/mirror/fedora/linux/core/6/$ARCH/os/',
'http://srl.cs.jhu.edu/YUM/fedora/core/6/$ARCH/os/',
'http://ftp.gui.uva.es/sites/fedora.redhat.com/core/6/$ARCH/os/',
'ftp://alviss.et.tudelft.nl/pub/fedora/core/6/$ARCH/os/',
'http://mirror.aarnet.edu.au/pub/fedora/linux/core/6/$ARCH/os/',
'ftp://ftp.funet.fi/pub/mirrors/ftp.redhat.com/pub/fedora/linux/core/6/$ARCH/os/',
'ftp://thales.memphis.edu/fedora/linux/core/6/$ARCH/os/',
'http://ftp-stud.fht-esslingen.de/pub/fedora/linux/core/6/$ARCH/os/',
]

for m in initial_mirror_list:
    s = m.split('/')
    name = s[2]
    path = s[3:]

    if Site.select(Site.q.name==name).count() == 0:
        site = Site(name=name)
    else:
        sites = Site.select(Site.q.name==name)
        site = sites[0]

    ip = socket.gethostbyname(name)
    if ip is not None:
        SiteIP(site=site, address=ip)

    host = Host(site=site, name=name, pull_from=redhat)
    path = '/'.join(path)

    for content in Content.select():
        if content.category.name != 'core':
            continue
        print 'Mirror(host=%s, content=%s)' % (host.name, content.name)
        mirror = Mirror(host=host, content=content)

        ver = '/%s/' % (content.version.name)
        verpath = re.sub('/6/', ver, path)

        archpath = re.sub('\$ARCH', content.arch.name, verpath)
        urlpath = '%s//%s/%s' % (s[0], name, archpath)
        print 'MirrorURL(path=%s)' % (urlpath)
        MirrorURL(mirror=mirror, path=urlpath)
