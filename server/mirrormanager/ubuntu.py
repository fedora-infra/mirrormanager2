from mirrormanager.model import Product, Category, Arch, Directory

productname = 'Ubuntu'
categories = {'Ubuntu Archive':('ubuntu','http://archive.ubuntu.com'),
              'Ubuntu CD Images':('releases', 'http://releases.ubuntu.com'),
              'Ubuntu Ports Archive':('ports', 'http://ports.ubuntu.com'),
              'Ubuntu Security Archive':('security', 'http://security.ubuntu.com'),
              }
primary_arches = ('i386', 'amd64')
secondary_arches = ('armel', 'powerpc', 'ia64', 'sparc', 'hppa', 'lpia')

def setup_ubuntu():
    product = Product(name=productname)

    for name, (dirname, canonicalhost) in categories.iteritems():
        d = Directory(name=dirname)
        Category(product=product, name=name, canonicalhost=canonicalhost, topdir=d)

    for a in primary_arches:
        Arch(name=a, primaryArch=True)
    for a in secondary_arches:
        Arch(name=a, primaryArch=False)
