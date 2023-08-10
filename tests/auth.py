from contextlib import contextmanager


@contextmanager
def user_set(client, user):
    """Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask_fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    # app.before_request_funcs[None] = []
    with client.session_transaction() as session:
        session["fedora_auth_token"] = "TOKEN"
        session["fedora_auth_profile"] = {
            "nickname": user.username,
            "email": user.email,
            "zoneinfo": None,
            "groups": user.groups,
        }
    yield


class FakeFasUser:
    """Fake FAS user used for the tests."""

    id = 100
    username = "pingou"
    cla_done = True
    groups = ["packager", "signed_fpca"]
    email = "pingou@fp.o"


class AnotherFakeFasUser:
    """Fake FAS user used for the tests."""

    id = 110
    username = "kevin"
    cla_done = True
    groups = ["packager", "signed_fpca"]
    email = "kevin@fp.o"
    signed_fpca = True


class FakeFasUserAdmin:
    """Fake FAS user used for the tests."""

    id = 1000
    username = "admin"
    cla_done = True
    email = "admin@fp.o"
    groups = ["packager", "sysadmin-main", "signed_fpca"]
