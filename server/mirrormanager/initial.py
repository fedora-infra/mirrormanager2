import turbogears
import turbogears.identity
from mirrormanager.model import User, Group

def user_group_setup():
    Group(group_name='user', display_name='User')
    Group(group_name='sysadmin', display_name='Admin')
    a = User(
        user_name='admin', 
        email_address='admin@example.com', 
        display_name='Admin', 
        password='admin'
        )
    a.addGroup(Group.by_group_name('user'))
    a.addGroup(Group.by_group_name('sysadmin'))

    b = User(
        user_name='test', 
        email_address='test@example.com', 
        display_name='Test', 
        password='test'
        )
    b.addGroup(Group.by_group_name('user'))

user_group_setup()
