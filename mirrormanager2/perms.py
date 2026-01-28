from functools import wraps

from flask import current_app, flash, g, redirect, request, url_for


def is_mirrormanager_admin(user):
    """Is the user a mirrormanager admin."""
    if not user:
        return False
    auth_method = current_app.config.get("MM_AUTHENTICATION", None)

    if auth_method == "fas":
        # Rocky: changed from signed_fpca to signed_rosca
        # Source: mirrormanager-rocky/Containerfile line 32
        # RUN sed -e 's/signed_fpca/signed_rosca/' -i mirrormanager2/perms.py
        if "signed_rosca" not in user.groups:
            return False

    if auth_method in ("fas", "local"):
        admins = current_app.config["ADMIN_GROUP"]
        if isinstance(admins, str):
            admins = [admins]
        admins = set(admins)

        return len(admins.intersection(set(user.groups))) > 0
    else:
        return user.username in current_app.config["ADMIN_GROUP"]


def is_site_admin(user, site):
    """Is the user an admin of this site."""
    if not user:
        return False

    admins = [admin.username for admin in site.admins]

    return user.username in admins


def is_authenticated():
    """Returns whether the user is currently authenticated or not."""
    return hasattr(g, "fas_user") and g.fas_user is not None


def login_required(function):
    """Flask decorator to ensure that the user is logged in."""

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """Wrapped function actually checking if the user is logged in."""
        if not is_authenticated():
            return redirect(url_for("auth.login", next=request.url))
        return function(*args, **kwargs)

    return decorated_function


def admin_required(function):
    """Flask decorator to ensure that the user is logged in."""

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """Wrapped function actually checking if the user is logged in."""
        if not is_authenticated():
            return redirect(url_for("auth.login", next=request.url))
        elif not is_mirrormanager_admin(g.fas_user):
            flash("You are not an admin", "error")
            return redirect(url_for("base.index"))
        return function(*args, **kwargs)

    return decorated_function
