from mirrormanager.model import Repository, Directory, Arch
import hashlib

def fill_filedetail():    
    for r in Repository.select():
        d = r.directory
        try:
            d = Directory.byName("%s/repodata" % (d.name))
        except:
            print "warning: Repository at Directory %s missing repodata subdir" % d.name
            continue
        for fd in d.fileDetails:
            if fd.filename == 'repomd.xml':
                try:
                    fname = "/%s/repomd.xml" % (d.name)
                    f = open(fname, 'rb')
                    s = f.read()
                    f.close()
                    h  = hashlib.sha256(s).hexdigest()
                    print "sha256=%s" % h
                    fd.sha256 =h
                    fd.sha512 = hashlib.sha512(s).hexdigest()
                    fd.sync()
                    del s
                except:
                    print "warning: couldn't update sha checksums for %s" % fname
                # only add to the most recent one
                break

def fill_arch():
    primary = ('i386', 'x86_64', 'ppc')
    for a in Arch.select():
        a.publiclist = (a.name != 'source')
        a.primaryArch = (a.name in primary)

def update():
    fill_filedetail()
    fill_arch()
