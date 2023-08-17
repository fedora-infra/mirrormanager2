import munch
from flask import (
    Blueprint,
    current_app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from mirrormanager2 import forms, local_auth
from mirrormanager2.app import OIDC

views = Blueprint("auth", __name__)


# pylint: disable=W0613
@views.before_app_request
def before_request():
    """Set the flask session as permanent."""
    session.permanent = True

    if current_app.config.get("MM_AUTHENTICATION") == "fas":
        if OIDC.user_loggedin:
            if not hasattr(session, "fas_user") or not session.fas_user:
                session.fas_user = munch.Munch(
                    {
                        "username": OIDC.user_getfield("nickname"),
                        "email": OIDC.user_getfield("email"),
                        "timezone": OIDC.user_getfield("zoneinfo"),
                        "cla_done": "signed_fpca"
                        in (OIDC.user_getfield("groups") or []),
                        "groups": OIDC.user_getfield("groups"),
                    }
                )
            g.fas_user = session.fas_user
        else:
            session.fas_user = None
            g.fas_user = None
    elif current_app.config.get("MM_AUTHENTICATION") == "local":
        local_auth._check_session_cookie()


@views.after_app_request
def after_request(response):
    if current_app.config.get("MM_AUTHENTICATION") == "local":
        local_auth._send_session_cookie()
    return response


@views.route("/login", methods=["GET", "POST"])
def login():  # pragma: no cover
    """Login mechanism for this application."""
    next_url = url_for("base.index")
    if "next" in request.values:
        next_url = request.values["next"]

    if next_url == url_for("auth.login"):
        # Avoid loops
        next_url = url_for("base.index")

    if current_app.config.get("MM_AUTHENTICATION", None) == "fas":
        return redirect(f"{url_for('oidc_auth.login')}?next={next_url}")
    elif current_app.config.get("MM_AUTHENTICATION", None) == "local":
        form = forms.LoginForm()
        return render_template(
            "login.html",
            next_url=next_url,
            form=form,
        )


@views.route("/logout")
def logout():
    """Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    """
    next_url = url_for("base.index")

    if current_app.config.get("MM_AUTHENTICATION", None) == "fas":
        if hasattr(g, "fas_user") and g.fas_user is not None:
            return redirect(f"{url_for('oidc_auth.logout')}?next={next_url}")
    elif current_app.config.get("MM_AUTHENTICATION", None) == "local":
        local_auth.logout()
    return redirect(next_url)
