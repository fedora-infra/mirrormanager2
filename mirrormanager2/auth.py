from dataclasses import dataclass, field

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

from mirrormanager2 import local_auth, login_forms
from mirrormanager2.app import OIDC

views = Blueprint("auth", __name__)


@dataclass
class User:
    username: str
    email: str
    timezone: str
    cla_done: bool
    groups: list[str] = field(default_factory=list)


# pylint: disable=W0613
@views.before_app_request
def before_request():
    """Set the flask session as permanent."""
    session.permanent = True

    if current_app.config.get("MM_AUTHENTICATION") == "fas":
        if OIDC.user_loggedin:
            if not hasattr(session, "fas_user") or not session.fas_user:
                userinfo = session.get("oidc_auth_profile")
                session.fas_user = User(
                    username=userinfo.get("nickname"),
                    email=userinfo.get("email"),
                    timezone=userinfo.get("zoneinfo"),
                    # Rocky: changed from signed_fpca to signed_rosca
                    # Source: mirrormanager-rocky/Containerfile line 32
                    # RUN sed -e 's/signed_fpca/signed_rosca/' -i mirrormanager2/auth.py
                    cla_done=("signed_rosca" in (userinfo.get("groups") or [])),
                    groups=userinfo.get("groups"),
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
        local_auth._send_session_cookie(response)
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
        form = login_forms.LoginForm()
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
