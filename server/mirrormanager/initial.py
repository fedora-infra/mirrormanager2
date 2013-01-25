from sqlobject.dberrors import DuplicateEntryError
from mirrormanager.model import User, Group, Arch

def user_group_setup():
    try:
        Group(group_name='user', display_name='User')
        print "created group 'user'"
    except DuplicateEntryError:
        pass
    try:
        Group(group_name='sysadmin', display_name='Admin')
        print "created group 'sysadmin'"
    except DuplicateEntryError:
        pass
    try:
        # fixme cannot create a user and set a password this way
        # as long as we're using an identity provider.
        a = User(
            user_name='admin', 
            email_address='admin@example.com', 
            display_name='Admin',
            password='admin'
            )
        print "created user 'admin', password 'admin'.  You will want to change that."
        a.addGroup(Group.by_group_name('user'))
        a.addGroup(Group.by_group_name('sysadmin'))
    except DuplicateEntryError:
        pass

def create_arches():
    def _do_create(arch, primary):
        try:
            a = Arch(name=arch)
            print "created architecture %s" % arch
        except DuplicateEntryError:
            pass

    primary_arches = (u'i386', u'x86_64', u'source')
    secondary_arches = (u'ppc', u'ppc64', u'sparc', u'sparc64', u'arm', u'armhfp', u's390', u's390x', u'ia64')
    for arch in primary_arches:
        _do_create(arch, True)
    for arch in secondary_arches:
        _do_create(arch, False)
