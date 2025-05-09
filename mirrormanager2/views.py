import datetime
import os
import re
from urllib.parse import urlsplit

import flask
from mirrormanager_messages.host import (
    HostAddedV1,
    HostAddedV2,
    HostDeletedV1,
    HostDeletedV2,
    HostUpdatedV1,
    HostUpdatedV2,
)
from mirrormanager_messages.site import SiteDeletedV1, SiteDeletedV2
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_helpers.flask_ext import get_or_404

from mirrormanager2 import forms, login_forms
from mirrormanager2 import lib as mmlib
from mirrormanager2.database import DB
from mirrormanager2.lib import model
from mirrormanager2.lib.notifications import (
    fedmsg_publish,
    host_to_message_body,
    site_to_message_body,
)
from mirrormanager2.perms import (
    admin_required,
    is_mirrormanager_admin,
    is_site_admin,
    login_required,
)
from mirrormanager2.utility.pagination import PaginationArgs

views = flask.Blueprint("base", __name__)


@views.route("/")
def index():
    """Displays the index page."""
    # publiclist=True filters out all results which have
    # publiclist set to False
    products = mmlib.get_products(DB.session, publiclist=True)
    arches = mmlib.get_arches(DB.session, publiclist=True)
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
        version = mmlib.get_version_by_name_version(DB.session, p_name, p_version)
        if version:
            version_id = version.id
    elif p_name:
        product = mmlib.get_product_by_name(DB.session, p_name)
        if product:
            product_id = product.id

    if p_arch:
        arch = mmlib.get_arch_by_name(DB.session, p_arch)
        if arch:
            arch_id = arch.id

    mirrors = mmlib.get_mirrors(
        DB.session,
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
        pagination=PaginationArgs(),
    )

    return flask.render_template(
        "mirrors.html",
        mirrors=mirrors,
    )


@views.route("/site/mine")
@login_required
def mysite():
    """Return the list of site managed by the user."""
    sites = mmlib.get_user_sites(DB.session, flask.g.fas_user.username)
    return flask.render_template(
        "my_sites.html",
        tag="mysites",
        username=f"{flask.g.fas_user.username}'s",
        sites=sites,
    )


@views.route("/admin/all_sites")
@admin_required
def all_sites():
    """Return the list of all sites for the admins."""
    sites = mmlib.get_all_sites(DB.session)
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
        DB.session.add(site)
        form.populate_obj(obj=site)
        site.admin_active = True
        site.created_by = flask.g.fas_user.username
        if site.org_url.endswith("/"):
            site.org_url = site.org_url[:-1]

        try:
            DB.session.flush()
            flask.flash("Site added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # Site table. So the only situation where it could fail is a
            # failure at the DB server level itself.
            DB.session.rollback()
            flask.flash("Could not create the new site", "error")
            flask.current_app.logger.debug("Could not create the new site")
            flask.current_app.logger.exception(err)
            return flask.redirect(flask.url_for("base.index"))

        try:
            msg = mmlib.add_admin_to_site(DB.session, site, flask.g.fas_user.username)
            flask.flash(msg)
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this because the code check before adding the
            # new SiteAdmin and therefore the only situation where it could
            # fail is a failure at the DB server level itself.
            DB.session.rollback()
            flask.current_app.logger.debug(
                f'Could not add admin "{flask.g.fas_user.username}" to site "{site}"'
            )
            flask.current_app.logger.exception(err)

        DB.session.commit()
        return flask.redirect(flask.url_for("base.index"))

    return flask.render_template(
        "site_new.html",
        form=form,
    )


@views.route("/site/<int:site_id>", methods=["GET", "POST"])
@login_required
def site_view(site_id):
    """View information about a given site."""
    siteobj = mmlib.get_site(DB.session, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (is_site_admin(flask.g.fas_user, siteobj) or is_mirrormanager_admin(flask.g.fas_user)):
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
                host.set_not_up2date(DB.session)

        try:
            DB.session.flush()
            flask.flash("Site Updated")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this because the code check before adding the
            # new SiteAdmin and therefore the only situation where it could
            # fail is a failure at the DB server level itself.
            DB.session.rollback()
            flask.flash("Could not update the Site", "error")
            flask.current_app.logger.debug("Could not update the Site")
            flask.current_app.logger.exception(err)

        DB.session.commit()
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
    siteobj = mmlib.get_site(DB.session, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (is_site_admin(flask.g.fas_user, siteobj) or is_mirrormanager_admin(flask.g.fas_user)):
        flask.abort(403, "Access denied")

    form = forms.ConfirmationForm()
    site_name = siteobj.name
    if form.validate_on_submit():
        DB.session.delete(siteobj)
        try:
            DB.session.commit()
        except SQLAlchemyError as err:
            DB.session.rollback()
            flask.flash("Could not delete this site", "error")
            flask.current_app.logger.debug("Could not delete this site")
            flask.current_app.logger.exception(err)
        else:
            flask.flash(f'Site "{site_name}" dropped')
            if flask.current_app.config["USE_FEDORA_MESSAGING"]:
                message_v1 = SiteDeletedV1(
                    topic="mirrormanager.site.deleted",
                    body=dict(site_id=siteobj.id, site_name=siteobj.name, org_url=siteobj.org_url),
                )
                fedmsg_publish(message_v1)
                message_v2 = SiteDeletedV2(
                    topic="mirrormanager.site.deleted.v2",
                    body={
                        "site": site_to_message_body(siteobj),
                        "agent": flask.g.fas_user.username,
                    },
                )
                fedmsg_publish(message_v2)

    return flask.redirect(flask.url_for("base.index"))


@views.route("/host/<int:site_id>/new", methods=["GET", "POST"])
@login_required
def host_new(site_id):
    """Create a new host."""
    siteobj = mmlib.get_site(DB.session, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (is_site_admin(flask.g.fas_user, siteobj) or is_mirrormanager_admin(flask.g.fas_user)):
        flask.abort(403, "Access denied")

    form = forms.AddHostForm()
    if form.validate_on_submit():
        host = model.Host()
        DB.session.add(host)
        host.site_id = siteobj.id
        form.populate_obj(obj=host)
        host.admin_active = True

        host.bandwidth_int = int(host.bandwidth_int)
        host.asn = None if not host.asn else int(host.asn)

        try:
            DB.session.commit()
        except SQLAlchemyError as err:
            DB.session.rollback()
            flask.flash("Could not create the new host", "error")
            flask.current_app.logger.debug("Could not create the new host")
            flask.current_app.logger.exception(err)
        else:
            flask.flash("Host added")
            if flask.current_app.config["USE_FEDORA_MESSAGING"]:
                message_v1 = HostAddedV1(
                    topic="mirrormanager.host.added",
                    body={
                        "site_id": host.site_id,
                        "host_id": host.id,
                        "bandwidth": host.bandwidth_int,
                        "asn": host.asn,
                    },
                )
                fedmsg_publish(message_v1)
                message_v2 = HostAddedV2(
                    topic="mirrormanager.host.added.v2",
                    body={
                        "site": site_to_message_body(host.site),
                        "host": {
                            **host_to_message_body(host),
                            "url": flask.url_for("base.host_view", host_id=host.id, _external=True),
                        },
                        "agent": flask.g.fas_user.username,
                    },
                )
                fedmsg_publish(message_v2)

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
    host = mmlib.get_host(DB.session, host_id)

    if host is None:
        flask.abort(404, "Site not found")

    if not (is_site_admin(flask.g.fas_user, host.site) or is_mirrormanager_admin(flask.g.fas_user)):
        flask.abort(403, "Access denied")

    site = host.site
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        DB.session.delete(host)
        try:
            DB.session.commit()
        except SQLAlchemyError as err:
            DB.session.rollback()
            flask.flash("Could not delete this host", "error")
            flask.current_app.logger.debug("Could not delete this host")
            flask.current_app.logger.exception(err)
        else:
            flask.flash("Host dropped")
            if flask.current_app.config["USE_FEDORA_MESSAGING"]:
                message_v1 = HostDeletedV1(
                    topic="mirrormanager.host.deleted",
                    body={
                        "site_id": host.site_id,
                        "host_id": host.id,
                        "bandwidth": host.bandwidth_int,
                        "asn": host.asn,
                    },
                )
                fedmsg_publish(message_v1)
                message_v2 = HostDeletedV2(
                    topic="mirrormanager.host.deleted.v2",
                    body={
                        "site": site_to_message_body(site),
                        "host": {
                            **host_to_message_body(host),
                            "url": flask.url_for("base.host_view", host_id=host.id, _external=True),
                        },
                        "agent": flask.g.fas_user.username,
                    },
                )
                fedmsg_publish(message_v2)

    return flask.redirect(flask.url_for("base.site_view", site_id=site.id))


@views.route("/site/<int:site_id>/admin/new", methods=["GET", "POST"])
@login_required
def siteadmin_new(site_id):
    """Create a new site_admin."""
    siteobj = mmlib.get_site(DB.session, site_id)

    if siteobj is None:
        flask.abort(404, "Site not found")

    if not (is_site_admin(flask.g.fas_user, siteobj) or is_mirrormanager_admin(flask.g.fas_user)):
        flask.abort(403, "Access denied")

    form = login_forms.LostPasswordForm()
    if form.validate_on_submit():
        site_admin = model.SiteAdmin()
        DB.session.add(site_admin)
        site_admin.site_id = siteobj.id
        form.populate_obj(obj=site_admin)

        try:
            DB.session.flush()
            flask.flash("Site Admin added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # Site table. So the only situation where it could fail is a
            # failure at the DB server level itself.
            DB.session.rollback()
            flask.flash("Could not add Site Admin", "error")
            flask.current_app.logger.debug("Could not add Site Admin")
            flask.current_app.logger.exception(err)

        DB.session.commit()
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
        siteobj = mmlib.get_site(DB.session, site_id)

        if siteobj is None:
            flask.abort(404, "Site not found")

        if not (
            is_site_admin(flask.g.fas_user, siteobj) or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        siteadminobj = mmlib.get_siteadmin(DB.session, admin_id)

        if siteadminobj is None:
            flask.abort(404, "Site Admin not found")

        if siteadminobj not in siteobj.admins:
            flask.abort(404, "Site Admin not related to this Site")

        if len(siteobj.admins) <= 1:
            flask.flash("There is only one admin set, you cannot delete it.", "error")
            return flask.redirect(flask.url_for("base.site_view", site_id=site_id))

        DB.session.delete(siteadminobj)

        try:
            DB.session.commit()
            flask.flash("Site Admin deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            DB.session.rollback()
            flask.flash("Could not delete Site Admin", "error")
            flask.current_app.logger.debug("Could not delete Site Admin")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.site_view", site_id=site_id))


@views.route("/host/<host_id>", methods=["GET", "POST"])
@login_required
def host_view(host_id):
    """Create a new host."""
    host = mmlib.get_host(DB.session, host_id)

    if host is None:
        flask.abort(404, "Host not found")

    if not (is_site_admin(flask.g.fas_user, host.site) or is_mirrormanager_admin(flask.g.fas_user)):
        flask.abort(403, "Access denied")

    form = forms.AddHostForm(obj=host)
    if form.validate_on_submit():
        admin_active = host.admin_active
        private = host.private
        form.populate_obj(obj=host)
        host.bandwidth_int = int(host.bandwidth_int)
        host.asn = None if not host.asn else int(host.asn)

        # If the user is *not* an admin, keep the current admin_active flag
        if not is_mirrormanager_admin(flask.g.fas_user):
            host.admin_active = admin_active

        # If the private flag has been changed, invalidate mirrors
        if host.private != private:
            host.set_not_up2date(DB.session)

        try:
            DB.session.commit()
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this because the code updates data therefore
            # the only situation where it could fail is a failure at the
            # DB server level itself.
            DB.session.rollback()
            flask.flash("Could not update the host", "error")
            flask.current_app.logger.debug("Could not update the host")
            flask.current_app.logger.exception(err)
        else:
            flask.flash("Host updated")
            if flask.current_app.config["USE_FEDORA_MESSAGING"]:
                message_v1 = HostUpdatedV1(
                    topic="mirrormanager.host.updated",
                    body={
                        "site_id": host.site_id,
                        "host_id": host.id,
                        "bandwidth": host.bandwidth_int,
                        "asn": host.asn,
                    },
                )
                fedmsg_publish(message_v1)
                message_v2 = HostUpdatedV2(
                    topic="mirrormanager.host.updated.v2",
                    body={
                        "site": site_to_message_body(host.site),
                        "host": {
                            **host_to_message_body(host),
                            "url": flask.url_for("base.host_view", host_id=host.id, _external=True),
                        },
                        "agent": flask.g.fas_user.username,
                    },
                )
                fedmsg_publish(message_v2)

        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

    return flask.render_template(
        "host.html",
        form=form,
        host=host,
    )


@views.route("/host/<host_id>/host_acl_ip/new", methods=["GET", "POST"])
@login_required
def host_acl_ip_new(host_id):
    """Create a new host_acl_ip."""
    hostobj = mmlib.get_host(DB.session, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site) or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostAclIpForm()
    if form.validate_on_submit():
        host_acl = model.HostAclIp()
        DB.session.add(host_acl)
        host_acl.host_id = hostobj.id
        form.populate_obj(obj=host_acl)

        try:
            DB.session.flush()
            flask.flash("Host ACL IP added")
        except SQLAlchemyError as err:
            DB.session.rollback()
            flask.flash("Could not add ACL IP to the host", "error")
            flask.current_app.logger.debug("Could not add ACL IP to the host")
            flask.current_app.logger.exception(err)

        DB.session.commit()
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
        hostobj = mmlib.get_host(DB.session, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostaclobj = mmlib.get_host_acl_ip(DB.session, host_acl_ip_id)

        if hostaclobj is None:
            flask.abort(404, "Host ACL IP not found")
        else:
            DB.session.delete(hostaclobj)
        try:
            DB.session.flush()
            flask.flash("Host ACL IP deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            DB.session.rollback()
            flask.flash("Could not add ACL IP to the host", "error")
            flask.current_app.logger.debug("Could not add ACL IP to the host")
            flask.current_app.logger.exception(err)

        DB.session.commit()
    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/netblock/new", methods=["GET", "POST"])
@login_required
def host_netblock_new(host_id):
    """Create a new host_netblock."""
    hostobj = mmlib.get_host(DB.session, host_id)
    flask.g.is_mirrormanager_admin = is_mirrormanager_admin(flask.g.fas_user)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site) or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostNetblockForm()
    if form.validate_on_submit():
        host_netblock = model.HostNetblock()
        DB.session.add(host_netblock)
        host_netblock.host_id = hostobj.id
        form.populate_obj(obj=host_netblock)

        try:
            DB.session.flush()
            flask.flash("Host netblock added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # table. So the only situation where it could fail is a failure
            # at the DB server level itself.
            DB.session.rollback()
            flask.flash("Could not add netblock to the host", "error")
            flask.current_app.logger.debug("Could not add netblock to the host")
            flask.current_app.logger.exception(err)

        DB.session.commit()
        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

    return flask.render_template(
        "host_netblock_new.html",
        form=form,
        host=hostobj,
    )


@views.route("/host/<host_id>/host_netblock/<host_netblock_id>/delete", methods=["POST"])
@login_required
def host_netblock_delete(host_id, host_netblock_id):
    """Delete a host_netblock."""
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        hostobj = mmlib.get_host(DB.session, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostnetbobj = mmlib.get_host_netblock(DB.session, host_netblock_id)

        if hostnetbobj is None:
            flask.abort(404, "Host netblock not found")
        else:
            DB.session.delete(hostnetbobj)
        try:
            DB.session.commit()
            flask.flash("Host netblock deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            DB.session.rollback()
            flask.flash("Could not delete netblock of the host", "error")
            flask.current_app.logger.debug("Could not delete netblock of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/asn/new", methods=["GET", "POST"])
@admin_required
def host_asn_new(host_id):
    """Create a new host_peer_asn."""
    hostobj = mmlib.get_host(DB.session, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site) or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostAsnForm()
    if form.validate_on_submit():
        host_asn = model.HostPeerAsn()
        DB.session.add(host_asn)
        host_asn.host_id = hostobj.id
        form.populate_obj(obj=host_asn)
        host_asn.asn = int(host_asn.asn)

        try:
            DB.session.flush()
            flask.flash("Host Peer ASN added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # table. So the only situation where it could fail is a failure
            # at the DB server level itself.
            DB.session.rollback()
            flask.flash("Could not add Peer ASN to the host", "error")
            flask.current_app.logger.debug("Could not add Peer ASN to the host")
            flask.current_app.logger.exception(err)

        DB.session.commit()
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
        hostobj = mmlib.get_host(DB.session, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostasnobj = mmlib.get_host_peer_asn(DB.session, host_asn_id)

        if hostasnobj is None:
            flask.abort(404, "Host Peer ASN not found")
        else:
            DB.session.delete(hostasnobj)

        try:
            DB.session.commit()
            flask.flash("Host Peer ASN deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            DB.session.rollback()
            flask.flash("Could not delete Peer ASN of the host", "error")
            flask.current_app.logger.debug("Could not delete Peer ASN of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/country/new", methods=["GET", "POST"])
@login_required
def host_country_new(host_id):
    """Create a new host_country."""
    hostobj = mmlib.get_host(DB.session, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site) or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    form = forms.AddHostCountryForm()
    if form.validate_on_submit():
        country_name = form.country.data
        country = mmlib.get_country_by_name(DB.session, country_name)
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
        DB.session.add(host_country)

        try:
            DB.session.flush()
            flask.flash("Host Country added")
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot check this as there is no unique constraint in the
            # table. So the only situation where it could fail is a failure
            # at the DB server level itself.
            DB.session.rollback()
            flask.flash("Could not add Country to the host", "error")
            flask.current_app.logger.debug("Could not add Country to the host")
            flask.current_app.logger.exception(err)

        DB.session.commit()
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
        hostobj = mmlib.get_host(DB.session, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hostcntobj = mmlib.get_host_country(DB.session, host_country_id)

        if hostcntobj is None:
            flask.abort(404, "Host Country not found")
        else:
            DB.session.delete(hostcntobj)

        try:
            DB.session.commit()
            flask.flash("Host Country deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            DB.session.rollback()
            flask.flash("Could not delete Country of the host", "error")
            flask.current_app.logger.debug("Could not delete Country of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/category/new", methods=["GET", "POST"])
@login_required
def host_category_new(host_id):
    """Create a new host_category."""
    hostobj = mmlib.get_host(DB.session, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site) or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    categories = mmlib.get_categories(
        DB.session,
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
        DB.session.add(host_category)

        try:
            DB.session.commit()
            flask.flash("Host Category added")
            return flask.redirect(flask.url_for("base.host_view", host_id=host_id))
        except SQLAlchemyError as err:
            DB.session.rollback()
            flask.flash("Could not add Category to the host", "error")
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
        hostobj = mmlib.get_host(DB.session, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hcobj = mmlib.get_host_category(DB.session, hc_id)

        if hcobj is None:
            flask.abort(404, "Host/Category not found")
        host_cat_ids = [cat.id for cat in hostobj.categories]

        if hcobj.id not in host_cat_ids:
            flask.abort(404, "Category not associated with this host")
        else:
            for url in hcobj.urls:
                DB.session.delete(url)
            for dirs in hcobj.directories:
                DB.session.delete(dirs)
            DB.session.delete(hcobj)

        try:
            DB.session.commit()
            flask.flash("Host Category deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            DB.session.rollback()
            flask.flash("Could not delete Category of the host", "error")
            flask.current_app.logger.debug("Could not delete Category of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


@views.route("/host/<host_id>/category/<hc_id>/url/new", methods=["GET", "POST"])
@login_required
def host_category_url_new(host_id, hc_id):
    """Create a new host_category_url."""
    hostobj = mmlib.get_host(DB.session, host_id)

    if hostobj is None:
        flask.abort(404, "Host not found")

    if not (
        is_site_admin(flask.g.fas_user, hostobj.site) or is_mirrormanager_admin(flask.g.fas_user)
    ):
        flask.abort(403, "Access denied")

    hcobj = mmlib.get_host_category(DB.session, hc_id)

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

        if url in [url.url for url in hcobj.urls]:
            flask.flash(f"URL Not Added: {url} already exists on {hcobj.category.name}", "error")
            return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

        # If the user is *not* an admin, keep the current private flag
        if not is_mirrormanager_admin(flask.g.fas_user):
            host_category_u.private = private

        DB.session.add(host_category_u)

        try:
            DB.session.flush()
            flask.flash("Host Category URL added")
        except SQLAlchemyError as err:
            DB.session.rollback()
            flask.flash("Could not add Category URL to the host", "error")
            flask.current_app.logger.debug("Could not add Category URL to the host")
            flask.current_app.logger.exception(err)

        DB.session.commit()
        return flask.redirect(flask.url_for("base.host_view", host_id=host_id))

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
        hostobj = mmlib.get_host(DB.session, host_id)

        if hostobj is None:
            flask.abort(404, "Host not found")

        if not (
            is_site_admin(flask.g.fas_user, hostobj.site)
            or is_mirrormanager_admin(flask.g.fas_user)
        ):
            flask.abort(403, "Access denied")

        hcobj = mmlib.get_host_category(DB.session, hc_id)

        if hcobj is None:
            flask.abort(404, "Host/Category not found")

        host_cat_ids = [cat.id for cat in hostobj.categories]

        if hcobj.id not in host_cat_ids:
            flask.abort(404, "Category not associated with this host")

        hostcaturlobj = mmlib.get_host_category_url_by_id(DB.session, host_category_url_id)

        if hostcaturlobj is None:
            flask.abort(404, "Host category URL not found")

        host_cat_url_ids = [url.id for url in hcobj.urls]

        if hostcaturlobj.id not in host_cat_url_ids:
            flask.abort(404, "Category URL not associated with this host")
        else:
            DB.session.delete(hostcaturlobj)

        try:
            DB.session.commit()
            flask.flash("Host category URL deleted")
        except SQLAlchemyError as err:  # pragma: no cover
            # We check everything before deleting so the only error we could
            # run in is DB server related, and that we can't fake in our
            # tests
            DB.session.rollback()
            flask.flash("Could not delete category URL of the host", "error")
            flask.current_app.logger.debug("Could not delete category URL of the host")
            flask.current_app.logger.exception(err)

    return flask.redirect(flask.url_for("base.host_view", host_id=host_id))


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
        return flask.render_template("rsync_filter.html", excludes=excludes, message=message)

    num_prefix = num_prefix_components(stripprefix)
    try:
        since = int(since)
    except (ValueError, TypeError):
        message = "value of argument since is not an integer"
        return flask.render_template("rsync_filter.html", excludes=excludes, message=message)

    includes = set()
    categories_requested = cat.split(",")
    newer_dirs = mmlib.get_rsync_filter_directories(DB.session, categories_requested, since)

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

    stats = mmlib.get_statistics(DB.session, today, cat)

    if not mmlib.get_statistics(DB.session, yesterday, cat):
        yesterday = None
    if not mmlib.get_statistics(DB.session, tomorrow, cat):
        tomorrow = None

    total = sum(stat.requests for stat in stats)

    labels = [stat.name for stat in stats]
    dataset = {
        "label": "Percent",
        "data": [stat.percent for stat in stats],
    }

    return flask.render_template(
        "statistics.html",
        stats=stats,
        total=total,
        yesterday=yesterday,
        today=today,
        tomorrow=tomorrow,
        cat=cat,
        graph_labels=labels,
        graph_dataset=dataset,
    )


@views.route("/maps")
def maps():
    return flask.render_template("maps_interactive.html")


@views.route("/maps/interactive")
def maps_interactive():
    return flask.redirect(flask.url_for("base.maps"))


@views.route("/propgation")
def propgation():
    """Redirect for the old URL with typo."""
    return flask.redirect(flask.url_for("base.propagation_all"))


@views.route("/propagation/")
def propagation_all():
    repos = mmlib.get_propagation_repos(DB.session)
    return flask.render_template("propagation.html", repos=repos, repo_id=None)


@views.route("/propagation/<int:repo_id>")
def propagation(repo_id):
    """Display propagation statistics. The files displayed
    are generated by mm2_propagation which generates output files
    like this <prefix>-repomd-propagation.svg.
    It also generates these files with that date included. For now
    only the files without the date are displayed.
    """
    repos = mmlib.get_propagation_repos(DB.session)
    repo = get_or_404(model.Repository, repo_id, "Repository not found")
    propagation = mmlib.get_propagation(DB.session, repo.id)
    labels = [stat.datetime.strftime(r"%Y-%m-%d %H:%M") for stat in propagation]

    def _get_background_color(border_color):
        return border_color.replace("rgb(", "rgba(").replace(")", ", 0.5)")

    series = [
        # Colors are in https://github.com/chartjs/Chart.js/blob/master/src/plugins/plugin.colors.ts
        ("synced", "same_day", "rgb(75, 192, 192)"),
        ("synced - 1", "one_day", "rgb(255, 205, 86)"),
        ("synced - 2", "two_day", "rgb(255, 159, 64)"),
        ("older", "older", "rgb(255, 99, 132)"),
        ("N/A", "no_info", "rgb(201, 203, 207)"),
    ]
    datasets = []
    for label, attr, color in series:
        datasets.append(
            {
                "label": label,
                "data": [getattr(stat, attr) for stat in propagation],
                "borderWidth": 1,
                "borderColor": color,
                "backgroundColor": _get_background_color(color),
            }
        )
    return flask.render_template(
        "propagation.html", repos=repos, repo=repo, labels=labels, datasets=datasets
    )


@views.route("/map/mirrors_location.txt")
def mirrors_location():
    results = []
    tracking = []
    for hcurl in mmlib.get_host_category_url(DB.session):
        host = hcurl.host_category.host
        if host.private or host.site.private:
            continue
        if host.latitude is None or host.longitude is None:
            continue
        scheme, hostname = urlsplit(hcurl.url)[:2]
        if not scheme.startswith("http"):
            continue
        if hostname in tracking:
            continue
        url = f"{scheme}://{hostname}"
        results.append(
            {
                "host": host,
                "url": url,
                "host_name": hostname,
            }
        )
        tracking.append(hostname)
    return flask.render_template("mirrors_location.txt", mirrors=results), {
        "Content-Type": "text/plain"
    }


@views.route("/crawler/<int:host_id>.log")
def crawler_log(host_id):
    crawler_log_dir = os.path.join(flask.current_app.config["MM_LOG_DIR"], "crawler")
    return flask.helpers.send_from_directory(crawler_log_dir, f"{host_id}.log", max_age=None)
