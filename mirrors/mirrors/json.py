# This module provides helper functions for the JSON part of your
# view, if you are providing a JSON-based API for your app.

# Here's what most rules would look like:
# @jsonify.when("isinstance(obj, YourClass)")
# def jsonify_yourclass(obj):
#     return [obj.val1, obj.val2]
# The goal is to break your objects down into simple values:
# lists, dicts, numbers and strings

from turbojson.jsonify import jsonify

from turbojson.jsonify import jsonify_sqlobject
from mirrors.model import User, Group, Permission

@jsonify.when('isinstance(obj, Group)')
def jsonify_group(obj):
    result = jsonify_sqlobject( obj )
    result["users"] = [u.user_name for u in obj.users]
    result["permissions"] = [p.permission_name for p in obj.permissions]
    return result

@jsonify.when('isinstance(obj, User)')
def jsonify_user(obj):
    result = jsonify_sqlobject( obj )
    del result['password']
    result["groups"] = [g.group_name for g in obj.groups]
    result["permissions"] = [p.permission_name for p in obj.permissions]
    return result

@jsonify.when('isinstance(obj, Permission)')
def jsonify_permission(obj):
    result = jsonify_sqlobject( obj )
    result["groups"] = [g.group_name for g in obj.groups]
    return result
