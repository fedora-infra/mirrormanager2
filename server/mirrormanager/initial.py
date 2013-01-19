from sqlobject.dberrors import DuplicateEntryError
from mirrormanager.model import User, Group

def user_group_setup():
    try:
        Group(group_name='user', display_name='User')
    except DuplicateEntryError:
        pass
    try:
        Group(group_name='sysadmin', display_name='Admin')
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
    except DuplicateEntryError:
        pass
    
    a.addGroup(Group.by_group_name('user'))
    a.addGroup(Group.by_group_name('sysadmin'))
        
user_group_setup()
