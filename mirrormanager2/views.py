import datetime
import glob
import os
import re

import flask
import werkzeug
from sqlalchemy.exc import SQLAlchemyError

from mirrormanager2 import forms, login_forms
from mirrormanager2 import lib as mmlib
from mirrormanager2.lib import model
from mirrormanager2.lib.notifications import fedmsg_publish
from mirrormanager2.perms import (
    admin_required,
    is_mirrormanager_admin,
    is_site_admin,
    login_required,
)

views = flask.Blueprint("base", __name__)


@views.route("/")
def index():
    """Displays the index page."""
    # publiclist=True filters out all results which have
    # publiclist set to False
    products = mmlib.get_products(flask.g.db, publiclist=True)
    arches = mmlib.get_arches(flask.g.db, publiclist=True)
    arches_name = [arch.name for arch in arches]

    return flask.render_template(
        "index.html",
        products=products,
        arches=arches_name,
    )


@views.route("/mirrors")
@views.route("/mirrors/<p_name>")
@views.route("/mirrors/<p_name>/<p_version>")
@views.route("/mirrors/<p_name>/<p_version>/<p_arch>")
def list_mirrors(p_name=None, p_version=None, p_arch=None):
    """Displays the page listing all mirrors."""
    version_id = None
    arch_id = None
    product_id = None
    if p_name and p_version:
        version = mmlib.get_version_by_name_version(flask.g.db, p_name, p_version)
        if version:
            version_id = version.id
    elif p_name:
        product = mmlib.get_product_by_name(flask.g.db, p_name)
        if product:
            product_id = product.id

    if p_arch:
        arch = mmlib.get_arch_by_name(flask.g.db, p_arch)
        if arch:
            arch_id = arch.id

    mirrors = mmlib.get_mirrors(
        flask.g.db,
        private=False,
        site_private=False,
        admin_active=True,
        user_active=True,
        site_admin_active=True,
        site_user_active=True,
        # last_checked_in=True,
        # last_crawled=True,
        up2date=True,
        host_category_url_private=False,
        version_id=version_id,
        arch_id=arch_id,
        product_id=product_id,
    )

    return flask.render_template(
        "mirrors.html",
        mirrors=mirrors,
    )


@views.route("/site/mine")
@login_required
def mysite():
    """Return the list of site managed by the user."""
    sites = mmlib.get_user_sites(flask.g.db, flask.g.fas_user.username)
    return flask.render_template(
        "my_sites.html",
        tag="mysites",
        username="%s's" % flask.g.fas_user.username,
        sites=sites,
    )


@views.route("/admin/all_sites")
@admin_required
def all_sites():
    """Return the list of all sites for the admins."""
    sites = mmlib.get_all_sites(flask.g.db)
    return flask.render_template(
        "my_sites.html",
        tag="allsites",
        username="Admin - List all",
        sites=sites,
    )


@views.route("/site/new", methods=["GET", "POST"])
@login_required
def site_new():
    """Create a new site."""
    form = forms.AddSiteForm()
    if form.validate_on_submit():
        site = model.Site()
        flask.g.db.add(site)
        form.populate_obj(obj=site)
        site.admin_active = True
        site.created_by = flask.g.fas_user.username
        if site.org_url.endswith("/"):
            site.org_url = site.org_url[:-1]

        try:
            flask.g.db.flush()
            flask.flash("Site added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # Site table. So the only situation where it could fail is a
            # failure at the DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not create the new site")
            flask.current_app.logger.debug("Could not create the new site")
            flask.current_app.logger.exception(err)
            return flask.redirect(flask.url_for("base.index"))

        try:
            msg = mmlib.add_admin_to_site(flask.g.db, site, flask.g.fas_user.username)
            flask.flash(msg)
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this because the code check before adding the
            # new SiteAdmin and therefore the only situation where it could
            # fail is a failure at the DB server level itself.
            flask.g.db.rollback()
            flask.current_app.logger.debug(
                f'Could not add admin "{flask.g.fas_user.username}" to site "{site}"'
            )
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.index"))

    return flask.render_template(
        "site_new.html",
        form=form,
    )


@views.route("/site/<int:site_id>", methods=["GET", "POST"])
@login_required
def site_view(site_id):
    """View information about a given site."""
    siteobj = mmlib.get_site(flask.g.db, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (
        is_site_admin(flask.g.fas_user, siteobj)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddSiteForm(obj=siteobj)
    if form.validate_on_submit():
        admin_active = siteobj.admin_active
        private = siteobj.private
        form.populate_obj(obj=siteobj)

        # If the user is *not* an admin, keep the current admin_active flag
        if not is_mirrormanager_admin(flask.g.fas_user):
            siteobj.admin_active = admin_active

        # If the private flag has been changed, invalidate mirrors
        if siteobj.private != private:
            for host in siteobj.hosts:
                host.set_not_up2date(flask.g.db)

        try:
            flask.g.db.flush()
            flask.flash("Site Updated")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this because the code check before adding the
            # new SiteAdmin and therefore the only situation where it could
            # fail is a failure at the DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not update the Site")
            flask.current_app.logger.debug("Could not update the Site")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.index"))

    return flask.render_template(
        "site.html",
        site=siteobj,
        form=form,
    )


@views.route("/site/<int:site_id>/drop", methods=["POST"])
@login_required
def site_drop(site_id):
    """Drop a given site."""
    topic = "site.deleted"
    siteobj = mmlib.get_site(flask.g.db, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (
        is_site_admin(flask.g.fas_user, siteobj)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.ConfirmationForm()
    site_name = siteobj.name
    if form.validate_on_submit():
        message = dict(
            site_id=siteobj.id, site_name=siteobj.name, org_url=siteobj.org_url
        )

        flask.g.db.delete(siteobj)
        try:
            flask.g.db.commit()
            flask.flash('Site "%s" dropped' % site_name)
            fedmsg_publish(topic, message)
        except SQLAlchemyError as err:
            flask.g.db.rollback()
            flask.flash("Could not delete this site")
            flask.current_app.logger.debug("Could not delete this site")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.index"))


@views.route("/host/<int:site_id>/new", methods=["GET", "POST"])
@login_required
def host_new(site_id):
    """Create a new host."""

    topic = "host.added"
    siteobj = mmlib.get_site(flask.g.db, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (
        is_site_admin(flask.g.fas_user, siteobj)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostForm()
    if form.validate_on_submit():
        host = model.Host()
        flask.g.db.add(host)
        host.site_id = siteobj.id
        form.populate_obj(obj=host)
        host.admin_active = True

        host.bandwidth_int = int(host.bandwidth_int)
        host.asn = None if not host.asn else int(host.asn)
        message = dict(site_id=host.site_id, bandwidth=host.bandwidth_int, asn=host.asn)

        try:
            flask.g.db.flush()
            flask.flash("Host added")
            fedmsg_publish(topic, message)
        except SQLAlchemyError as err:
            flask.g.db.rollback()
            flask.flash("Could not create the new host")
            flask.current_app.logger.debug("Could not create the new host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.site_view", site_id=site_id))

    return flask.render_template(
        "host_new.html",
        form=form,
        site=siteobj,
    )


@views.route("/host/<int:host_id>/drop", methods=["POST"])
@login_required
def host_drop(host_id):
    """Drop a given site."""
    topic = "host.deleted"
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Site not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    site_id = hostobj.site.id
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        message = dict(
            site_id=hostobj.site_id,
            host_id=host_id,
            bandwidth=hostobj.bandwidth_int,
            asn=hostobj.asn,
        )

        flask.g.db.delete(hostobj)
        try:
            flask.g.db.commit()
            flask.flash("Host dropped")
            fedmsg_publish(topic, message)
        except SQLAlchemyError as err:
            flask.g.db.rollback()
            flask.flash("Could not delete this host")
            flask.current_app.logger.debug("Could not delete this host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.site_view", site_id=site_id))


@views.route("/site/<int:site_id>/admin/new", methods=["GET", "POST"])
@login_required
def siteadmin_new(site_id):
    """Create a new site_admin."""
    siteobj = mmlib.get_site(flask.g.db, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (
        is_site_admin(flask.g.fas_user, siteobj)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = login_forms.LostPasswordForm()
    if form.validate_on_submit():
        site_admin = model.SiteAdmin()
        flask.g.db.add(site_admin)
        site_admin.site_id = siteobj.id
        form.populate_obj(obj=site_admin)

        try:
            flask.g.db.flush()
            flask.flash("Site Admin added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # Site table. So the only situation where it could fail is a
            # failure at the DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not add Site Admin")
            flask.current_app.logger.debug("Could not add Site Admin")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.site_view", site_id=site_id))

    return flask.render_template(
        "site_admin_new.html",
        form=form,
        site=siteobj,
    )


@views.route("/site/<int:site_id>/admin/<int:admin_id>/delete", methods=["POST"])
@login_required
def siteadmin_delete(site_id, admin_id):
    """Delete a site_admin."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        siteobj = mmlib.get_site(flask.g.db, site_id)

        if siteobj is None:
            flask.abort(404, "Site not found")

        if not (
            is_site_admin(flask.g.fas_user, siteobj)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        siteadminobj = mmlib.get_siteadmin(flask.g.db, admin_id)

        if siteadminobj is None:
            flask.abort(404, "Site Admin not found")

        if siteadminobj not in siteobj.admins:
            flask.abort(404, "Site Admin not related to this Site")

        if len(siteobj.admins) <= 1:
            flask.flash("There is only one admin set, you cannot delete it.", "error")
            return flask.redirect(flask.url_for("base.site_view", site_id=site_id))

        flask.g.db.delete(siteadminobj)

        try:
            flask.g.db.commit()
            flask.flash("Site Admin deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            flask.g.db.rollback()
            flask.flash("Could not delete Site Admin", "error")
            flask.current_app.logger.debug("Could not delete Site Admin")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.site_view", site_id=site_id))


@views.route("/host/<host_id>", methods=["GET", "POST"])
@login_required
def host_view(host_id):
    """Create a new host."""
    topic = "host.updated"
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostForm(obj=hostobj)
    if form.validate_on_submit():
        admin_active = hostobj.admin_active
        private = hostobj.private
        form.populate_obj(obj=hostobj)
        hostobj.bandwidth_int = int(hostobj.bandwidth_int)
        hostobj.asn = None if not hostobj.asn else int(hostobj.asn)

        # If the user is *not* an admin, keep the current admin_active flag
        if not is_mirrormanager_admin(flask.g.fas_user):
            hostobj.admin_active = admin_active

        # If the private flag has been changed, invalidate mirrors
        if hostobj.private != private:
            hostobj.set_not_up2date(flask.g.db)

        message = dict(
            site_id=hostobj.site_id,
            host_id=host_id,
            bandwidth=hostobj.bandwidth_int,
            asn=hostobj.asn,
        )

        try:
            flask.g.db.flush()
            flask.flash("Host updated")
            fedmsg_publish(topic, message)
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this because the code updates data therefore
            # the only situation where it could fail is a failure at the
            # DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not update the host")
            flask.current_app.logger.debug("Could not update the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

    return flask.render_template(
        "host.html",
        form=form,
        host=hostobj,
    )


@views.route("/host/<host_id>/host_acl_ip/new", methods=["GET", "POST"])
@login_required
def host_acl_ip_new(host_id):
    """Create a new host_acl_ip."""
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostAclIpForm()
    if form.validate_on_submit():
        host_acl = model.HostAclIp()
        flask.g.db.add(host_acl)
        host_acl.host_id = hostobj.id
        form.populate_obj(obj=host_acl)

        try:
            flask.g.db.flush()
            flask.flash("Host ACL IP added")
        except SQLAlchemyError as err:
            flask.g.db.rollback()
            flask.flash("Could not add ACL IP to the host")
            flask.current_app.logger.debug("Could not add ACL IP to the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

    return flask.render_template(
        "host_acl_ip_new.html",
        form=form,
        host=hostobj,
    )


@views.route("/host/<host_id>/host_acl_ip/<host_acl_ip_id>/delete", methods=["POST"])
@login_required
def host_acl_ip_delete(host_id, host_acl_ip_id):
    """Delete a host_acl_ip."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        hostobj = mmlib.get_host(flask.g.db, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostaclobj = mmlib.get_host_acl_ip(flask.g.db, host_acl_ip_id)

        if hostaclobj is None:
            flask.abort(404, "Host ACL IP not found")
        else:
            flask.g.db.delete(hostaclobj)
        try:
            flask.g.db.flush()
            flask.flash("Host ACL IP deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            flask.g.db.rollback()
            flask.flash("Could not add ACL IP to the host")
            flask.current_app.logger.debug("Could not add ACL IP to the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/netblock/new", methods=["GET", "POST"])
@login_required
def host_netblock_new(host_id):
    """Create a new host_netblock."""
    hostobj = mmlib.get_host(flask.g.db, host_id)
    flask.g.is_mirrormanager_admin = is_mirrormanager_admin(flask.g.fas_user)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostNetblockForm()
    if form.validate_on_submit():
        host_netblock = model.HostNetblock()
        flask.g.db.add(host_netblock)
        host_netblock.host_id = hostobj.id
        form.populate_obj(obj=host_netblock)

        try:
            flask.g.db.flush()
            flask.flash("Host netblock added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # table. So the only situation where it could fail is a failure
            # at the DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not add netblock to the host")
            flask.current_app.logger.debug("Could not add netblock to the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

    return flask.render_template(
        "host_netblock_new.html",
        form=form,
        host=hostobj,
    )


@views.route(
    "/host/<host_id>/host_netblock/<host_netblock_id>/delete", methods=["POST"]
)
@login_required
def host_netblock_delete(host_id, host_netblock_id):
    """Delete a host_netblock."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        hostobj = mmlib.get_host(flask.g.db, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostnetbobj = mmlib.get_host_netblock(flask.g.db, host_netblock_id)

        if hostnetbobj is None:
            flask.abort(404, "Host netblock not found")
        else:
            flask.g.db.delete(hostnetbobj)
        try:
            flask.g.db.commit()
            flask.flash("Host netblock deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            flask.g.db.rollback()
            flask.flash("Could not delete netblock of the host")
            flask.current_app.logger.debug("Could not delete netblock of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/asn/new", methods=["GET", "POST"])
@admin_required
def host_asn_new(host_id):
    """Create a new host_peer_asn."""
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostAsnForm()
    if form.validate_on_submit():
        host_asn = model.HostPeerAsn()
        flask.g.db.add(host_asn)
        host_asn.host_id = hostobj.id
        form.populate_obj(obj=host_asn)
        host_asn.asn = int(host_asn.asn)

        try:
            flask.g.db.flush()
            flask.flash("Host Peer ASN added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # table. So the only situation where it could fail is a failure
            # at the DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not add Peer ASN to the host")
            flask.current_app.logger.debug("Could not add Peer ASN to the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

    return flask.render_template(
        "host_asn_new.html",
        form=form,
        host=hostobj,
    )


@views.route("/host/<host_id>/host_asn/<host_asn_id>/delete", methods=["POST"])
@admin_required
def host_asn_delete(host_id, host_asn_id):
    """Delete a host_peer_asn."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        hostobj = mmlib.get_host(flask.g.db, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostasnobj = mmlib.get_host_peer_asn(flask.g.db, host_asn_id)

        if hostasnobj is None:
            flask.abort(404, "Host Peer ASN not found")
        else:
            flask.g.db.delete(hostasnobj)

        try:
            flask.g.db.commit()
            flask.flash("Host Peer ASN deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            flask.g.db.rollback()
            flask.flash("Could not delete Peer ASN of the host")
            flask.current_app.logger.debug("Could not delete Peer ASN of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/country/new", methods=["GET", "POST"])
@login_required
def host_country_new(host_id):
    """Create a new host_country."""
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostCountryForm()
    if form.validate_on_submit():
        country_name = form.country.data
        country = mmlib.get_country_by_name(flask.g.db, country_name)
        if country is None:
            flask.flash("Invalid country code")
            return flask.render_template(
                "host_country_new.html",
                form=form,
                host=hostobj,
            )

        host_country = model.HostCountry()
        host_country.host_id = hostobj.id
        host_country.country_id = country.id
        flask.g.db.add(host_country)

        try:
            flask.g.db.flush()
            flask.flash("Host Country added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # table. So the only situation where it could fail is a failure
            # at the DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not add Country to the host")
            flask.current_app.logger.debug("Could not add Country to the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

    return flask.render_template(
        "host_country_new.html",
        form=form,
        host=hostobj,
    )


@views.route(
    "/host/<host_id>/host_country/<host_country_id>/delete",
    methods=["POST"],
)
@login_required
def host_country_delete(host_id, host_country_id):
    """Delete a host_country."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        hostobj = mmlib.get_host(flask.g.db, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostcntobj = mmlib.get_host_country(flask.g.db, host_country_id)

        if hostcntobj is None:
            flask.abort(404, "Host Country not found")
        else:
            flask.g.db.delete(hostcntobj)

        try:
            flask.g.db.commit()
            flask.flash("Host Country deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            flask.g.db.rollback()
            flask.flash("Could not delete Country of the host")
            flask.current_app.logger.debug("Could not delete Country of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/category/new", methods=["GET", "POST"])
@login_required
def host_category_new(host_id):
    """Create a new host_category."""
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    categories = mmlib.get_categories(
        flask.g.db,
        not is_mirrormanager_admin(flask.g.fas_user),
    )

    form = forms.AddHostCategoryForm(categories=categories)

    if flask.request.method == "POST":
        try:
            id_found = False
            form.category_id.data = int(form.category_id.data)
            for cat in categories:
                if cat.id == form.category_id.data:
                    id_found = True
                    break
            if not id_found:
                form.category_id.data = -1
        except (ValueError, TypeError):
            form.category_id.data = -1

    if form.validate_on_submit():
        host_category = model.HostCategory()
        host_category.host_id = hostobj.id
        form.populate_obj(obj=host_category)
        host_category.category_id = int(host_category.category_id)
        flask.g.db.add(host_category)

        try:
            flask.g.db.commit()
            flask.flash("Host Category added")
            return flask.redirect(
                flask.url_for(
                    "base.host_category", host_id=hostobj.id, hc_id=host_category.id
                )
            )
        except SQLAlchemyError as err:
            flask.g.db.rollback()
            flask.flash("Could not add Category to the host")
            flask.current_app.logger.debug("Could not add Category to the host")
            flask.current_app.logger.exception(err)

    return flask.render_template(
        "host_category_new.html",
        form=form,
        host=hostobj,
    )


@views.route("/host/<host_id>/category/<hc_id>/delete", methods=["GET", "POST"])
@login_required
def host_category_delete(host_id, hc_id):
    """Delete a host_category."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        hostobj = mmlib.get_host(flask.g.db, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hcobj = mmlib.get_host_category(flask.g.db, hc_id)

        if hcobj is None:
            flask.abort(404, "Host/Category not found")
        host_cat_ids = [cat.id for cat in hostobj.categories]

        if hcobj.id not in host_cat_ids:
            flask.abort(404, "Category not associated with this host")
        else:
            for url in hcobj.urls:
                flask.g.db.delete(url)
            for dirs in hcobj.directories:
                flask.g.db.delete(dirs)
            flask.g.db.delete(hcobj)

        try:
            flask.g.db.commit()
            flask.flash("Host Category deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            flask.g.db.rollback()
            flask.flash("Could not delete Category of the host")
            flask.current_app.logger.debug("Could not delete Category of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/category/<hc_id>", methods=["GET", "POST"])
@login_required
def host_category(host_id, hc_id):
    """View a host_category."""
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    hcobj = mmlib.get_host_category(flask.g.db, hc_id)

    if hcobj is None:
        flask.abort(404, "Host/Category not found")

    host_cat_ids = [cat.id for cat in hostobj.categories]

    if hcobj.id not in host_cat_ids:
        flask.abort(404, "Category not associated with this host")

    form = forms.EditHostCategoryForm(obj=hcobj)

    if form.validate_on_submit() and is_mirrormanager_admin(flask.g.fas_user):
        form.populate_obj(obj=hcobj)

        try:
            flask.g.db.flush()
            flask.flash("Host Category updated")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this because the code check before updating
            # and therefore the only situation where it could fail is a
            # failure at the DB server level itself.
            flask.g.db.rollback()
            flask.flash("Could not update Category to the host")
            flask.current_app.logger.debug("Could not update Category to the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(
            flask.url_for("base.host_category", host_id=hostobj.id, hc_id=hcobj.id)
        )

    return flask.render_template(
        "host_category.html",
        form=form,
        host=hostobj,
        hostcategory=hcobj,
    )


@views.route("/host/<host_id>/category/<hc_id>/url/new", methods=["GET", "POST"])
@login_required
def host_category_url_new(host_id, hc_id):
    """Create a new host_category_url."""
    hostobj = mmlib.get_host(flask.g.db, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site)
        or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    hcobj = mmlib.get_host_category(flask.g.db, hc_id)

    if hcobj is None:
        flask.abort(404, "Host/Category not found")

    host_cat_ids = [cat.id for cat in hostobj.categories]

    if hcobj.id not in host_cat_ids:
        flask.abort(404, "Category not associated with this host")

    form = forms.AddHostCategoryUrlForm()
    form.url.validators[2].regex = re.compile(
        flask.current_app.config.get("MM_PROTOCOL_REGEX", ""), re.IGNORECASE
    )

    if form.validate_on_submit():
        host_category_u = model.HostCategoryUrl()
        private = host_category_u.private
        host_category_u.host_category_id = hcobj.id
        form.populate_obj(obj=host_category_u)

        url = form.url.data.strip()
        if url.endswith("/"):
            url = url[:-1]
        host_category_u.url = url

        # If the user is *not* an admin, keep the current private flag
        if not is_mirrormanager_admin(flask.g.fas_user):
            host_category_u.private = private

        flask.g.db.add(host_category_u)

        try:
            flask.g.db.flush()
            flask.flash("Host Category URL added")
        except SQLAlchemyError as err:
            flask.g.db.rollback()
            flask.flash("Could not add Category URL to the host")
            flask.current_app.logger.debug("Could not add Category URL to the host")
            flask.current_app.logger.exception(err)

        flask.g.db.commit()
        return flask.redirect(
            flask.url_for("base.host_category", host_id=host_id, hc_id=hc_id)
        )

    return flask.render_template(
        "host_category_url_new.html",
        form=form,
        host=hostobj,
        hostcategory=hcobj,
    )


@views.route(
    "/host/<host_id>/category/<hc_id>/url/<host_category_url_id>/delete",
    methods=["POST"],
)
@login_required
def host_category_url_delete(host_id, hc_id, host_category_url_id):
    """Delete a host_category_url."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        hostobj = mmlib.get_host(flask.g.db, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hcobj = mmlib.get_host_category(flask.g.db, hc_id)

        if hcobj is None:
            flask.abort(404, "Host/Category not found")

        host_cat_ids = [cat.id for cat in hostobj.categories]

        if hcobj.id not in host_cat_ids:
            flask.abort(404, "Category not associated with this host")

        hostcaturlobj = mmlib.get_host_category_url_by_id(
            flask.g.db, host_category_url_id
        )

        if hostcaturlobj is None:
            flask.abort(404, "Host category URL not found")

        host_cat_url_ids = [url.id for url in hcobj.urls]

        if hostcaturlobj.id not in host_cat_url_ids:
            flask.abort(404, "Category URL not associated with this host")
        else:
            flask.g.db.delete(hostcaturlobj)

        try:
            flask.g.db.commit()
            flask.flash("Host category URL deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            flask.g.db.rollback()
            flask.flash("Could not delete category URL of the host")
            flask.current_app.logger.debug("Could not delete category URL of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(
        flask.url_for("base.host_category", host_id=host_id, hc_id=hc_id)
    )


@views.route("/rsyncFilter")
@views.route("/rsyncFilter/")
def rsyncFilter():
    """Returns the filter to use in your rsync job."""

    def parents(folder):
        path = []
        splitpath = folder.split("/")
        for i in range(1, len(splitpath)):
            path.append("/".join(splitpath[:i]))
        return path

    def strip_prefix(to_strip, folder):
        splitdir = folder.split("/")
        splitdir = splitdir[to_strip:]
        folder = "/".join(splitdir)
        return folder

    def num_prefix_components(prefix):
        splitprefix = prefix.split("/")
        return len(splitprefix)

    # by setting excludes here, we cause the filter rules to
    # not transfer anything if there is no new content or if
    # a mistake was made in the URL.
    message = None
    excludes = ["*"]
    cat = flask.request.args.get("categories")
    since = flask.request.args.get("since")
    stripprefix = flask.request.args.get("stripprefix")

    if cat is None or since is None or stripprefix is None:
        message = "Missing categories, since, or stripprefix arguments"
        return flask.render_template(
            "rsync_filter.html", excludes=excludes, message=message
        )

    num_prefix = num_prefix_components(stripprefix)
    try:
        since = int(since)
    except (ValueError, TypeError):
        message = "value of argument since is not an integer"
        return flask.render_template(
            "rsync_filter.html", excludes=excludes, message=message
        )

    includes = set()
    categories_requested = cat.split(",")
    newer_dirs = mmlib.get_rsync_filter_directories(
        flask.g.db, categories_requested, since
    )

    for i in range(len(newer_dirs)):
        newer_dirs[i] = strip_prefix(num_prefix, newer_dirs[i])

    includes.update(newer_dirs)
    for n in newer_dirs:
        includes.update(parents(n))

    includes = sorted(includes)
    # add trailing slash as rsync wants it
    for i in range(len(includes)):
        includes[i] += "/"

    return flask.render_template(
        "rsync_filter.html", includes=includes, excludes=excludes, message=message
    )


def statistics_file_name(date, cat, ext):
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")
    name = f"{year}/{month}/{cat}-"
    name = f"{name}{year}-{month}-{day}.{ext}"
    return name


def check_for_statistics(date, cat):
    try:
        stat_file = flask.current_app.config["STATISTICS_BASE"]
        stat_file = os.path.join(stat_file, statistics_file_name(date, cat, "txt"))
        if os.access(stat_file, os.R_OK):
            return stat_file
    except Exception:
        pass
    return None


@views.route("/statistics")
@views.route("/statistics/<date>")
@views.route("/statistics/<date>/<cat>")
def statistics(date=None, cat="countries"):
    if cat not in ["countries", "archs", "repositories"]:
        cat = "countries"

    try:
        today = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    today_file = check_for_statistics(today, cat)
    if not check_for_statistics(yesterday, cat):
        yesterday = None
    if not check_for_statistics(tomorrow, cat):
        tomorrow = None

    try:
        with open(today_file) as data:
            table = data.read()
    except (OSError, TypeError):
        table = "N/A"

    return flask.render_template(
        "statistics.html",
        table=table,
        yesterday=yesterday,
        today=today,
        tomorrow=tomorrow,
        image=statistics_file_name(today, cat, "png"),
        cat=cat,
    )


@views.route("/maps")
def maps():
    return flask.render_template("maps.html")


@views.route("/propgation")
def propgation():
    """Redirect for the old URL with typo."""
    return flask.redirect(flask.url_for("base.propagation"))


@views.route("/propagation")
@views.route("/propagation/<prefix>")
def propagation(prefix="development"):
    """Display propagation statistics. The files displayed
    are generated by mm2_propagation which generates output files
    like this <prefix>-repomd-propagation.svg.
    It also generates these files with that date included. For now
    only the files without the date are displayed.
    """

    prefix = os.path.basename(prefix)
    # Right now propagation statistics are only generated
    # for the 'development' prefix and 'fxx_updates' prefix.
    if (
        not prefix.startswith("f")
        and not prefix.startswith("d")
        and not prefix.startswith("epel")
        and not prefix.startswith("centos")
    ):
        prefix = "development"

    prop_base = flask.current_app.config["PROPAGATION_BASE"]
    stat_file = werkzeug.utils.secure_filename(prefix + "-repomd-propagation.svg")
    stat_file = os.path.join(prop_base, stat_file)

    if not os.access(stat_file, os.R_OK):
        prefix = "oops"

    props = glob.glob(os.path.join(prop_base, "[cdef]*-repomd-propagation.svg"))

    for i, prop in enumerate(props):
        try:
            props[i] = os.path.basename(prop).split("-")[0]
        except (ValueError, TypeError):
            pass

    return flask.render_template("propagation.html", props=props, prefix=prefix)
