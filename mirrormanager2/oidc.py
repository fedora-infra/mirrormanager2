import json
import time
import warnings
from functools import wraps
from urllib.parse import quote_plus

from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, abort, flash, g, redirect, request, session, url_for

auth_routes = Blueprint("fedora_auth", __name__)


@auth_routes.route("/login")
def login():
    redirect_uri = url_for("fedora_auth.authorize", _external=True)
    session["next"] = request.args.get("next", request.root_url)
    return g._fedora_auth.authorize_redirect(redirect_uri)


@auth_routes.route("/authorize")
def authorize():
    try:
        token = g._fedora_auth.authorize_access_token()
    except OAuthError as e:
        abort(401, str(e))
    profile = g._fedora_auth.userinfo(token=token)
    session["fedora_auth_token"] = token
    session["fedora_auth_profile"] = profile
    try:
        return_to = session["next"]
        del session["next"]
    except KeyError:
        return_to = request.root_url
    return redirect(return_to)


@auth_routes.route("/logout")
def logout():
    """
    Request the browser to please forget the cookie we set, to clear the
    current session.

    Note that as described in [1], this will not log out in the case of a
    browser that doesn't clear cookies when requested to, and the user
    could be automatically logged in when they hit any authenticated
    endpoint.

    [1]: https://github.com/puiterwijk/flask-oidc/issues/5#issuecomment-86187023

    .. versionadded:: 1.0
    """
    session.pop("fedora_auth_token", None)
    session.pop("fedora_auth_profile", None)
    reason = request.args.get("reason")
    if reason == "expired":
        flash("Your session expired, please reconnect.")
    else:
        flash("You were successfully logged out.")
    return_to = request.args.get("next", request.root_url)
    return redirect(return_to)


class WarningDescriptor:
    def __init__(self, value, message, class_):
        self.value = value
        self.message = message
        self.class_ = class_

    def __get__(self, obj, objtype=None):
        warnings.warn(self.message, self.class_, stacklevel=2)
        return self.value

    def __set__(self, obj, value):
        self.value = value


class FedoraAuth:
    def __init__(self, app=None, prefix=None):
        self._prefix = prefix
        self.oauth = OAuth()
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        for required_conf in ("FEDORA_CLIENT_ID", "FEDORA_CLIENT_SECRET"):
            if required_conf not in app.config:
                app.logger.warning(
                    f"You must define the {required_conf} configuration value."
                )
        scopes = app.config.setdefault(
            "FEDORA_SCOPES",
            [
                "openid",
                "email",
                "profile",
                "https://id.fedoraproject.org/scope/groups",
                "https://id.fedoraproject.org/scope/agreements",
            ],
        )
        if "openid" not in app.config["FEDORA_SCOPES"]:
            raise ValueError('The value "openid" must be in the FEDORA_SCOPES')
        provider_url = app.config.setdefault(
            "FEDORA_PROVIDER_URL", "https://id.fedoraproject.org/openidc/"
        )
        app.config.setdefault("FEDORA_INTROSPECTION_AUTH_METHOD", "client_secret_post")
        app.register_blueprint(auth_routes, url_prefix=self._prefix)
        self.oauth.init_app(app)
        self.oauth.register(
            "fedora",
            client_kwargs={
                "scope": " ".join(scopes),
                "token_endpoint_auth_method": app.config[
                    "FEDORA_INTROSPECTION_AUTH_METHOD"
                ],
            },
            server_metadata_url=f"{provider_url}.well-known/openid-configuration",
        )
        app.before_request(self._store_oauth)

    def _store_oauth(self):
        g._fedora_auth = self.oauth.fedora

    def _check_token_expiry(self):
        token = session.get("fedora_auth_token")
        if not token:
            return
        if token["expires_at"] - 60 < int(time.time()):
            return redirect("{}?reason=expired".format(url_for("fedora_auth.logout")))

    @property
    def is_logged_in(self):
        """
        Returns whether the user is currently logged in.

        Returns:
            bool: Whether the user is logged in.
        """
        return session.get("fedora_auth_token") is not None

    def require_login(self, view_func):
        """
        Use this to decorate view functions that require a user to be logged
        in. If the user is not already logged in, they will be sent to the
        Provider to log in, after which they will be returned.
        """

        @wraps(view_func)
        def decorated(*args, **kwargs):
            if session.get("fedora_auth_token") is None:
                redirect_url = "{login}?next={here}".format(
                    login=url_for("fedora_auth.login"),
                    here=quote_plus(request.url),
                )
                return redirect(redirect_url)
            return view_func(*args, **kwargs)

        return decorated


class FedoraAuthCompat:
    def __init__(self, app=None, prefix=None):
        self.auth = FedoraAuth()
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        secrets = self.load_secrets(
            app.config.get("OIDC_CLIENT_SECRETS", "client_secrets.json")
        )
        client_secrets = list(secrets.values())[0]

        app.config.setdefault("OIDC_VALID_ISSUERS", client_secrets["issuer"])
        app.config.setdefault("OIDC_CLIENT_ID", client_secrets["client_id"])
        app.config.setdefault("OIDC_CLIENT_SECRET", client_secrets["client_secret"])
        app.config.setdefault("OIDC_USERINFO_URL", client_secrets["userinfo_uri"])
        app.config.setdefault("OIDC_INTROSPECTION_AUTH_METHOD", "client_secret_post")
        app.config.setdefault("OIDC_CALLBACK_ROUTE", "/oidc_callback")

        app.config.setdefault("OIDC_SCOPES", "openid profile email")
        if "openid" not in app.config["OIDC_SCOPES"]:
            raise ValueError('The value "openid" must be in the OIDC_SCOPES')

        for varname in ("CLIENT_ID", "CLIENT_SECRET", "INTROSPECTION_AUTH_METHOD"):
            app.config[f"FEDORA_{varname}"] = app.config[f"OIDC_{varname}"]
        app.config["FEDORA_PROVIDER_URL"] = f"{app.config['OIDC_VALID_ISSUERS']}/"

        self.auth.init_app(app)
        app.route(app.config["OIDC_CALLBACK_ROUTE"])(self._oidc_callback)
        app.before_request(self._store_token)

    def load_secrets(self, content_or_file):
        # Load client_secrets.json to pre-initialize some configuration
        if isinstance(content_or_file, dict):
            return content_or_file
        else:
            with open(content_or_file) as f:
                return json.load(f)

    def _store_token(self):
        g.oidc_id_token = WarningDescriptor(
            session.get("fedora_auth_token"),
            "The g.oidc_id_token property is deprecated, please use session['fedora_auth_token']",
            DeprecationWarning,
        )

    def _oidc_callback(self):
        warnings.warn(
            "The /oidc_callback route is deprecated, please use /authorize",
            DeprecationWarning,
            stacklevel=2,
        )
        return redirect(url_for("fedora_auth.authorize"))

    @property
    def user_loggedin(self):
        """
        Represents whether the user is currently logged in.

        Returns:
            bool: Whether the user is logged in with Flask-OIDC.

        .. versionadded:: 1.0
        """
        warnings.warn(
            "The user_loggedin property has been replaced with is_logged_in",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.auth.is_logged_in

    def require_login(self, view_func):
        """
        Use this to decorate view functions that require a user to be logged
        in. If the user is not already logged in, they will be sent to the
        Provider to log in, after which they will be returned.

        .. versionadded:: 1.0
           This was :func:`check` before.
        """
        return self.auth.require_login(view_func)

    def logout(self, return_to):
        """
        Request the browser to please forget the cookie we set, to clear the
        current session.

        Note that as described in [1], this will not log out in the case of a
        browser that doesn't clear cookies when requested to, and the user
        could be automatically logged in when they hit any authenticated
        endpoint.

        [1]: https://github.com/puiterwijk/flask-oidc/issues/5#issuecomment-86187023

        .. versionadded:: 1.0
        """
        return redirect(url_for("fedora_auth.logout", next=return_to))

    def user_getfield(self, field, access_token=None):
        """
        Request a single field of information about the user.

        :param field: The name of the field requested.
        :type field: str
        :returns: The value of the field. Depending on the type, this may be
            a string, list, dict, or something else.
        :rtype: object

        .. versionadded:: 1.0
        """
        return self.user_getinfo([field]).get(field)

    def user_getinfo(self, fields, access_token=None):
        warnings.warn(
            "The user_getinfo method is deprecated, please use session['fedora_auth_profile']",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.auth.is_logged_in:
            raise Exception("User was not authenticated")
        return session.get("fedora_auth_profile", {})

    def get_access_token(self):
        """Method to return the current requests' access_token.

        :returns: Access token or None
        :rtype: str

        .. versionadded:: 1.2
        """
        return session.get("fedora_auth_token", {}).get("access_token")

    def get_refresh_token(self):
        """Method to return the current requests' refresh_token.

        :returns: Access token or None
        :rtype: str

        .. versionadded:: 1.2
        """
        return session.get("fedora_auth_token", {}).get("refresh_token")
