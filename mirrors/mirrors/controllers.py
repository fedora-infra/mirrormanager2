from turbogears.identity.exceptions import IdentityFailure
import logging
import cherrypy


import turbogears
from turbogears import controllers, expose, validate, redirect, widgets, validators, error_handler, exception_handler
from turbogears import identity
from tgfastdata import DataController
import sqlobject
from sqlobject.sqlbuilder import *

from mirrors import my_validators
from mirrors.model import *
from mirrors.lib import createErrorString


log = logging.getLogger("mirrors.controllers")

def siteadmin_check(site, identity):
    if not site.is_siteadmin(identity):
        turbogears.flash("Error:You are not an admin for Site %s" % site.name)
        raise redirect("/")

def downstream_siteadmin_check(site, identity):
    if not site.is_siteadmin(identity) and not site.is_downstream_siteadmin(identity):
        turbogears.flash("Error:You are not an admin for Site %s or for a Site immediately downstream from Site %s" % (site.name, site.name))
        raise redirect("/")



# From the TurboGears book
class content:
    @turbogears.expose()
    def default(self, *vpath, **params):
        if len(vpath) == 1:
            identifier = vpath[0]
            action = self.read
            verb = 'read'
        elif len(vpath) == 2:
            identifier, verb = vpath
            verb = verb.replace('.','_')
            action = getattr(self, verb, None)
            if not action:
                raise cherrypy.NotFound
            if not action.exposed:
                raise cherrypy.NotFound
        else:
            raise cherrypy.NotFound


        if verb == "new":
            return action(**params)
        elif verb == "create":
            return action(**params)
        else:
            try:
                item=self.get(identifier)
            except sqlobject.SQLObjectNotFound:
                raise cherrypy.NotFound

            return action(item['values'], **params)




class SiteFields(widgets.WidgetsList):
    licensesAccepted = widgets.CheckBox(label="I agree to the Fedora Legal policies linked above")
    name     = widgets.TextField(validator=validators.NotEmpty, label="Site Name")
    password = widgets.TextField(validator=validators.NotEmpty, label="Site Password")
    orgUrl   = widgets.TextField(label="Organization URL", validator=validators.URL, attrs=dict(size='30'))
    private  = widgets.CheckBox()
    admin_active = widgets.CheckBox("admin_active",default=True)
    user_active = widgets.CheckBox(default=True)


site_form = widgets.TableForm(fields=SiteFields(),
                              submit_text="Save Site")


class SiteController(controllers.Controller, identity.SecureResource, content):
    require = identity.not_anonymous()

    def disabled_fields(self, site=None):
        disabled_fields = []
        if not identity.in_group("sysadmin"):
            disabled_fields.append('admin_active')
        if site is not None:
            if not site.is_siteadmin(identity):
                for a in ['password', 'user_active', 'private']:
                    disabled_fields.append(a)
            
        return disabled_fields

    def get(self, id):
        site = Site.get(id)
        return dict(values=site, disabled_fields=self.disabled_fields(site=site))
    
    @expose(template="mirrors.templates.site")
    def read(self, site):
        downstream_siteadmin_check(site, identity)
        submit_action = "/site/%s/update" % site.id
        return dict(form=site_form, values=site, action=submit_action, disabled_fields=self.disabled_fields(site=site))

    @expose(template="mirrors.templates.site")
    def new(self, **kwargs):
        submit_action = "/site/0/create"
        return dict(form=site_form, values=None, action=submit_action, disabled_fields=self.disabled_fields())
    
    @expose(template="mirrors.templates.site")
    @error_handler(new)
    @validate(form=site_form)
    def create(self, **kwargs):
        if not kwargs.has_key('licensesAccepted') or not kwargs['licensesAccepted']:
            turbogears.flash("Error:You must accept the license agreements to create a Site")
            raise turbogears.redirect("/")
        if not identity.in_group("sysadmin") and kwargs.has_key('admin_active'):
            del kwargs['admin_active']
        kwargs['licensesAcceptedBy'] = identity.current.user_name
        kwargs['createdBy'] = identity.current.user_name
        try:
            site = Site(**kwargs)
            site.accept_licenses(identity)
            SiteAdmin(site=site, username=identity.current.user_name)
        except: # probably sqlite IntegrityError but we can't catch that for some reason... 
            turbogears.flash("Error:Site %s already exists" % kwargs['name'])
        turbogears.flash("Site created.")
        raise turbogears.redirect("/")

    @expose(template="mirrors.templates.site")
    @validate(form=site_form)
    def update(self, site, **kwargs):
        siteadmin_check(site, identity)
        if kwargs.has_key('licensesAccepted') and kwargs['licensesAccepted']:
            kwargs['licensesAcceptedBy'] = identity.current.user_name
        else:
            turbogears.flash("Error:You must accept the license agreements to update a Site")
            return dict(form=site_form, values=site, action = "/site/%s/update" % site.id,
                        disabled_fields=self.disabled_fields())

        # in case we ever have to reset the licensesAccepted field for everyone
        # we drop it here as we're not letting them uncheck it anyow.
        if kwargs.has_key('licensesAccepted'):
            del kwargs['licensesAccepted']
        if not identity.in_group("sysadmin") and kwargs.has_key('admin_active'):
            del kwargs['admin_active']
        site.set(**kwargs)
        if not site.licensesAccepted:
            site.accept_licenses(identity)
        site.sync()
        turbogears.flash("Site Updated")
        raise turbogears.redirect("/")

    @expose(template="mirrors.templates.site")
    def delete(self, site, **kwargs):
        siteadmin_check(site, identity)
        site.destroySelf()
        raise turbogears.redirect("/")

    @expose(template="mirrors.templates.site")
    def s2s_delete(self, site, **kwargs):
        siteadmin_check(site, identity)
        dsite = Site.get(kwargs['dsite'])
        site.del_downstream_site(dsite)
        raise turbogears.redirect("/site/%s" % site.id)


##############################################
class SiteAdminFields(widgets.WidgetsList):
    username = widgets.TextField(validator=validators.NotEmpty)


siteadmin_form = widgets.TableForm(fields=SiteAdminFields(),
                              submit_text="Create Site Admin")


class SiteAdminController(controllers.Controller, identity.SecureResource, content):
    require = identity.not_anonymous()

    def get(self, id):
        return dict(values=SiteAdmin.get(id))
    
    @expose(template="mirrors.templates.boringform")
    def new(self, **kwargs):
        siteid=kwargs['siteid']
        try:
            site = Site.get(siteid)
        except sqlobject.SQLObjectNotFound:
            raise redirect("/")

        siteadmin_check(site, identity)
        submit_action = "/siteadmin/0/create?siteid=%s" % siteid
        return dict(form=siteadmin_form, values=None, action=submit_action, title="New Site Admin")
    
    @expose(template="mirrors.templates.siteadmin")
    @error_handler(new)
    @validate(form=siteadmin_form)
    def create(self, **kwargs):
        if not kwargs.has_key('siteid'):
            turbogears.flash("Error: form didn't provide siteid")
            raise redirect("/")
        siteid = kwargs['siteid']

        try:
            site = Site.get(siteid)
        except sqlobject.SQLObjectNotFound:
            turbogears.flash("Error: Site %s does not exist" % siteid)
            raise redirect("/")

        siteadmin_check(site, identity)
        username = kwargs['username']
        try:
            siteadmin = SiteAdmin(site=site, username=username)
        except: # probably sqlite IntegrityError but we can't catch that for some reason... 
            turbogears.flash("Error:SiteAdmin %s already exists" % kwargs['username'])
        raise turbogears.redirect("/site/%s" % siteid)

    @expose(template="mirrors.templates.siteadmin")
    def delete(self, siteadmin, **kwargs):
        site = siteadmin.my_site()
        siteadmin_check(site, identity)
        siteadmin.destroySelf()
        raise turbogears.redirect("/site/%s" % site.id)


##############################################
class SiteToSiteFields(widgets.WidgetsList):
    def get_sites_options():
        return [(s.id, s.name) for s in Site.select()]

    sites = widgets.MultipleSelectField(options=get_sites_options, size=15)
                                        

site_to_site_form = widgets.TableForm(fields=SiteToSiteFields(),
                                      submit_text="Add Downstream Site")


class SiteToSiteController(controllers.Controller, identity.SecureResource, content):
    require = identity.not_anonymous()

    def get(self, id):
        return dict(values=SiteToSite.get(id))
    
    @expose(template="mirrors.templates.boringform")
    def new(self, **kwargs):
        siteid=kwargs['siteid']
        try:
            site = Site.get(siteid)
        except sqlobject.SQLObjectNotFound:
            raise redirect("/")

        siteadmin_check(site, identity)
        submit_action = "/site2site/0/create?siteid=%s" % siteid
        return dict(form=site_to_site_form, values=None, action=submit_action, title="Add Downstream Site")
    
    @expose()
    @error_handler(new)
    @validate(form=site_to_site_form)
    def create(self, **kwargs):
        if not kwargs.has_key('siteid'):
            turbogears.flash("Error: form didn't provide siteid")
            raise redirect("/")
        siteid = kwargs['siteid']

        try:
            site = Site.get(siteid)
        except sqlobject.SQLObjectNotFound:
            turbogears.flash("Error: Site %s does not exist" % siteid)
            raise redirect("/")

        siteadmin_check(site, identity)
        sites = kwargs['sites']
        print sites
        for dssite in sites:
            if dssite == site.id:
                continue
            try:
                site2site = SiteToSite(upstream_site=site, downstream_site=dssite)
            except: 
                pass
        raise turbogears.redirect("/site/%s" % siteid)

    @expose()
    def delete(self, site2site, **kwargs):
        site = site2site.my_site()
        siteadmin_check(site, identity)
        site2site.destroySelf()
        raise turbogears.redirect("/site/%s" % site.id)


class HostFields(widgets.WidgetsList):
    name = widgets.TextField(validator=validators.NotEmpty, attrs=dict(size='30'), label="Host Name")
    admin_active = widgets.CheckBox("admin_active")
    user_active = widgets.CheckBox(default=True)
    country = widgets.TextField()
    private = widgets.CheckBox()
    robot_email = widgets.TextField(validator=validators.Email)
    


host_form = widgets.TableForm(fields=HostFields(),
                              submit_text="Save Host")

class HostController(controllers.Controller, identity.SecureResource, content):
    require = identity.not_anonymous()

    def disabled_fields(self, host=None):
        disabled_fields = []
        if not identity.in_group("sysadmin"):
            disabled_fields.append('admin_active')

        if host is not None:
            site = host.my_site()
            if not site.is_siteadmin(identity):
                for a in ['user_active', 'private', 'robot_email']:
                    disabled_fields.append(a)
        return disabled_fields


    def get(self, id):
        host = Host.get(id)
        return dict(values=host)

    @expose(template="mirrors.templates.host")
    def new(self, **kwargs):
        try:
            siteid=kwargs['siteid']
            site = Site.get(siteid)
        except sqlobject.SQLObjectNotFound:
            raise redirect("/")
        submit_action = "/host/0/create?siteid=%s" % siteid
        return dict(form=host_form, values=None, action=submit_action, disabled_fields=self.disabled_fields(),
                    title="Create Host")

    @expose(template="mirrors.templates.host")
    @error_handler()
    @validate(form=host_form)
    def create(self, **kwargs):
        if not identity.in_group("sysadmin") and kwargs.has_key('admin_active'):
            del kwargs['admin_active']
        site = Site.get(kwargs['siteid'])
        del kwargs['siteid']
        try:
            host = Host(site=site, **kwargs)
            submit_action = "/host/%s/update" % host.id
        except: # probably sqlite IntegrityError but we can't catch that for some reason... 
            turbogears.flash("Error:Host %s already exists" % kwargs['name'])
            submit_action = "/host/0/create?siteid=%s" % site.id
        raise turbogears.redirect("/")


    @expose(template="mirrors.templates.host")
    def read(self, host):
        downstream_siteadmin_check(host.my_site(), identity)
        submit_action = "/host/%s/update" % host.id
        return dict(form=host_form, values=host, action=submit_action,
                    disabled_fields=self.disabled_fields(host=host), title="Host")

    @expose(template="mirrors.templates.host")
    @validate(form=host_form)
    def update(self, host, **kwargs):
        siteadmin_check(host.my_site(), identity)
        if not identity.in_group("sysadmin") and kwargs.has_key('admin_active'):
            del kwargs['admin_active']
        host.set(**kwargs)
        host.sync()
        turbogears.flash("Host Updated")
        raise turbogears.redirect("/")

    @expose()
    def delete(self, host, **kwargs):
        siteadmin_check(host.my_site(), identity)
        host.destroySelf()
        raise turbogears.redirect("/")


##################################################################33
# HostCategory
##################################################################33
class HostCategoryFieldsNew(widgets.WidgetsList):
    def get_category_options():
        return [(c.id, c.name) for c in Category.select()]
    category = widgets.SingleSelectField(options=get_category_options)
    admin_active = widgets.CheckBox(default=True)
    user_active = widgets.CheckBox(default=True)
    path = widgets.TextField(validator=validators.NotEmpty, label="Path on your disk", attrs=dict(size='30'), help_text='e.g. /var/ftp/pub/fedora/linux/core')
    upstream = widgets.TextField(attrs=dict(size='30'), help_text='e.g. rsync://download.fedora.redhat.com/fedora-linux-core')

class LabelObjName(widgets.Label):
        template = """
        <label xmlns:py="http://purl.org/kid/ns#"
        id="${field_id}"
        class="${field_class}"
        py:content="value.name"
        />
        """                             

class HostCategoryFieldsRead(widgets.WidgetsList):
    category = LabelObjName()
    admin_active = widgets.CheckBox(default=True)
    user_active = widgets.CheckBox(default=True)
    path = widgets.TextField(validator=validators.NotEmpty, label="Path on your disk", attrs=dict(size='30'), help_text='e.g. /var/ftp/pub/fedora/linux/core')
    upstream = widgets.TextField(attrs=dict(size='30'), help_text='e.g. rsync://download.fedora.redhat.com/fedora-linux-core')

host_category_form_new = widgets.TableForm(fields=HostCategoryFieldsNew(),
                                       submit_text="Save Host Category")

host_category_form_read = widgets.TableForm(fields=HostCategoryFieldsRead(),
                                            submit_text="Save Host Category")



class HostCategoryController(controllers.Controller, identity.SecureResource, content):
    require = identity.not_anonymous()

    def disabled_fields(self, host=None):
        disabled_fields = []
        if not identity.in_group("sysadmin"):
            disabled_fields.append('admin_active')
        return disabled_fields

    def get(self, id):
        return dict(values=HostCategory.get(id))

    @expose(template="mirrors.templates.hostcategory")
    def new(self, **kwargs):

        try:
            hostid=kwargs['hostid']
            host = Host.get(hostid)
        except sqlobject.SQLObjectNotFound:
            raise redirect("/")
        siteadmin_check(host.my_site(), identity)
        submit_action = "/host_category/0/create?hostid=%s" % hostid
        return dict(form=host_category_form_new, values=None, action=submit_action, disabled_fields=self.disabled_fields())
    
    
    @expose(template="mirrors.templates.hostcategory")
    def read(self, hostcategory):
        downstream_siteadmin_check(hostcategory.my_site(), identity)
        submit_action = "/host_category/%s/update" % hostcategory.id
        disabled_fields=self.disabled_fields()
        return dict(form=host_category_form_read, values=hostcategory, action=submit_action, disabled_fields=self.disabled_fields())

    @expose(template="mirrors.templates.hostcategory")
    @error_handler(new)
    @validate(form=host_category_form_new)
    def create(self, **kwargs):
        if not kwargs.has_key('hostid'):
            turbogears.flash("Error: form didn't provide hostid")
            raise redirect("/")
        hostid = kwargs['hostid']
        del kwargs['hostid']
        host = Host.get(hostid)
        category = Category.get(kwargs['category'])
        del kwargs['category']
#            submit_action = "/host_category/%s/update" % id
        try:
            hostcategory = HostCategory(host=host, category=category, **kwargs)
        except:
            turbogears.flash("Error: Host already has category %s.  Try again." % category.name)
#            submit_action = "/host_category/0/create"
            raise turbogears.redirect("/host_category/0/create?hostid=%s" % hostid)
        raise turbogears.redirect("/host/%s" % hostid)


    @expose(template="mirrors.templates.hostcategory")
    @validate(form=host_category_form_read)
    def update(self, hostcategory, **kwargs):
        siteadmin_check(hostcategory.my_site(), identity)
        hostcategory.set(**kwargs)
        hostcategory.sync()
        turbogears.flash("HostCategory Updated")
        raise turbogears.redirect("/")

    @expose(template="mirrors.templates.hostcategory")
    def delete(self, hostcategory, **kwargs):
        siteadmin_check(hostcategory.my_site(), identity)
        hostcategory.destroySelf()
        raise turbogears.redirect("/host/%s" % hostcategory.host.id)


class HostListitemController(controllers.Controller, identity.SecureResource, content):
    require = identity.not_anonymous()
    title = ""
    form = None

    def get(self, id):
        return self.do_get(id)
    
    @expose(template="mirrors.templates.boringform")
    def new(self, **kwargs):
        try:
            hostid=kwargs['hostid']
            host = Host.get(hostid)
        except sqlobject.SQLObjectNotFound:
            raise redirect("/")

        siteadmin_check(host.my_site(), identity)
        submit_action = "%s/0/create?hostid=%s" % (self.submit_action_prefix, hostid)
        return dict(form=self.form, values=None, action=submit_action, title=self.title)
    
    @expose(template="mirrors.templates.boringform")
    @error_handler(new)
    @validate(form=form)
    def create(self, **kwargs):
        if not kwargs.has_key('hostid'):
            turbogears.flash("Error: form didn't provide siteid")
            raise redirect("/")
        hostid = kwargs['hostid']

        try:
            host = Host.get(hostid)
        except sqlobject.SQLObjectNotFound:
            turbogears.flash("Error: Host %s does not exist" % hostid)
            raise redirect("/")

        downstream_siteadmin_check(host.my_site(), identity)

        try:
            self.do_create(host, kwargs)
        except: # probably sqlite IntegrityError but we can't catch that for some reason... 
            turbogears.flash("Error: entity already exists")
        raise turbogears.redirect("/host/%s" % host.id)

    @expose(template="mirrors.templates.boringform")
    def delete(self, thing, **kwargs):
        host = thing.host
        siteadmin_check(host.my_site(), identity)
        thing.destroySelf()
        raise turbogears.redirect("/host/%s" % host.id)



class HostAclIPFields(widgets.WidgetsList):
    ip = widgets.TextField(label="IP", validator=validators.NotEmpty)

host_acl_ip_form = widgets.TableForm(fields=HostAclIPFields(),
                                     submit_text="Create Host ACL IP")

class HostAclIPController(HostListitemController):
    submit_action_prefix="/host_acl_ip"
    title = "New Host ACL IP"
    form = host_acl_ip_form

    def do_get(self, id):
        return dict(values=HostAclIp.get(id))

    def do_create(self, host, kwargs):
        HostAclIp(host=host, ip=kwargs['ip'])



class HostNetblockFields(widgets.WidgetsList):
    netblock = widgets.TextField(validator=validators.NotEmpty)

host_netblock_form = widgets.TableForm(fields=HostNetblockFields(),
                                       submit_text="Create Host Netblock")

class HostNetblockController(HostListitemController):
    submit_action_prefix="/host_netblock"
    title = "New Host Netblock"
    form = host_netblock_form

    def do_get(self, id):
        return dict(values=HostNetblock.get(id))

    def do_create(self, host, kwargs):
        HostNetblock(host=host, netblock=kwargs['netblock'])

class HostCountryAllowedFields(widgets.WidgetsList):
    country = widgets.TextField(validator=validators.NotEmpty)

host_country_allowed_form = widgets.TableForm(fields=HostCountryAllowedFields(),
                                              submit_text="Create Country Allowed")

class HostCountryAllowedController(HostListitemController):
    submit_action_prefix="/host_country_allowed"
    title = "New Host Country Allowed"
    form = host_country_allowed_form

    def do_get(self, id):
        return dict(values=HostCountryAllowed.get(id))

    def do_create(self, host, kwargs):
        HostCountryAllowed(host=host, country=kwargs['country'])



#########################################################3
# HostCategoryURL
#########################################################3
class HostCategoryUrlFields(widgets.WidgetsList):
    url = widgets.TextField(attrs=dict(size='30'))
    private  = widgets.CheckBox(default=False, label="For other mirrors only")

host_category_url_form = widgets.TableForm(fields=HostCategoryUrlFields(),
                                               submit_text="Create URL")

class HostCategoryUrlController(controllers.Controller, identity.SecureResource, content):
    require = identity.not_anonymous()
    title = "Host Category URL"
    form = host_category_url_form

    def get(self, id):
        return dict(values=HostCategoryUrl.get(id))
    
    @expose(template="mirrors.templates.boringform")
    def new(self, **kwargs):
        try:
            hcid=kwargs['hcid']
            host_category = HostCategory.get(hcid)
        except sqlobject.SQLObjectNotFound:
            raise redirect("/")

        host = host_category.host
        siteadmin_check(host.my_site(), identity)
            
        submit_action = "/host_category_url/0/create?hcid=%s" % hcid
        return dict(form=self.form, values=None, action=submit_action, title=self.title)

    @expose(template="mirrors.templates.boringform")
    @error_handler(new)
    @validate(form=form)
    def create(self, **kwargs):
        if not kwargs.has_key('hcid'):
            turbogears.flash("Error: form didn't provide hcid")
            raise redirect("/")
        hcid = kwargs['hcid']

        try:
            hc = HostCategory.get(hcid)
        except sqlobject.SQLObjectNotFound:
            turbogears.flash("Error: HostCategory %s does not exist" % hcid)
            raise redirect("/")

        siteadmin_check(hc.my_site(), identity)

        try:
            del kwargs['hcid']
            HostCategoryUrl(host_category=hc, **kwargs)
        except: # probably sqlite IntegrityError but we can't catch that for some reason... 
            turbogears.flash("Error: entity already exists")
        raise turbogears.redirect("/host_category/%s" % hcid)

    @expose(template="mirrors.templates.boringform")
    def read(self, hcurl):
        downstream_siteadmin_check(hcurl.my_site(), identity)
        submit_action = "/host_category_url/%s/update" % hcurl.id
        return dict(form=self.form, values=hcurl, action=submit_action, title=self.title)
        
    @expose(template="mirrors.templates.boringform")
    def update(self, hcurl, **kwargs):
        siteadmin_check(hcurl.my_site(), identity)
        hcurl.set(**kwargs)
        hcurl.sync()
        submit_action = "/host_category_url/%s/update" % hcurl.id
        return dict(form=self.form, values=hcurl, action=submit_action, title=self.title)
        
            
    

    @expose(template="mirrors.templates.boringform")
    def delete(self, hcurl, **kwargs):
        hc = hcurl.host_category
        siteadmin_check(hcurl.my_site(), identity)
        hcurl.destroySelf()
        raise turbogears.redirect("/host_category/%s" % hc.id)


# This exports the /pub/fedora/linux/core/... directory tree.
# For each directory requested, it returns the mirrors of that directory.

class PubController(controllers.Controller):
    @expose(template="mirrors.templates.mirrorlist", format="plain", content_type="text/plain")
    def default(self, *vpath, **params):
        path = 'pub/' + '/'.join(vpath)
        country = None
        include_private=False
        if params.has_key('country'):
            country = params['country']
        if params.has_key('include_private'):
            include_private = params['include_private']
        urls = directory_mirror_urls(path, country=country, include_private=include_private)
        for u, country in urls:
            if not u.startswith('http://') and not u.startswith('ftp://'):
                urls.remove((u, country))
        return dict(values=[u for u, country in urls])

#fixme - this is just a stub
class PublicListController(controllers.Controller):
    @expose(template="mirrors.templates.publiclist")
    def index(self, *vpath, **params):
        return dict()

#http://mirrors.fedoraproject.org/mirrorlist?repo=core-$releasever&arch=$basearch
#http://mirrors.fedoraproject.org/mirrorlist?repo=core-debug-$releasever&arch=$basearch
    @expose(template="mirrors.templates.mirrorlist", format="plain", content_type="text/plain")
    def mirrorlist(self, repo=None, arch=None, country=None):
        pass


        

class Root(controllers.RootController):
    site = SiteController()
    siteadmin = SiteAdminController()
    host = HostController()
    pub = PubController()
    host_country_allowed = HostCountryAllowedController()
    host_acl_ip = HostAclIPController()
    host_netblock = HostNetblockController()
    host_category = HostCategoryController()
    host_category_url = HostCategoryUrlController()
    site2site = SiteToSiteController()
    from mirrors.xmlrpc import XmlrpcController
    xmlrpc = XmlrpcController()
#    public = PublicListController()
    
    @expose(template="mirrors.templates.welcome")
    @identity.require(identity.not_anonymous())
    def index(self):
        if "sysadmin" in identity.current.groups:
            sites = Site.select()
        else:
            sites = user_sites(identity)

            
        if "sysadmin" in identity.current.groups:
            return {"sites":sites,
                    "arches":Arch.select(),
                    "products":Product.select(),
                    "versions":Version.select(),
                    "directories":Directory.select(),
                    "categories":Category.select(),
                    "repositories":Repository.select(),
                    "embargoed_countries":EmbargoedCountry.select(),
                    }
        else:
            return {"sites":sites}

    @expose(template="mirrors.templates.rsync_acl", format="plain", content_type="text/plain")
    def rsync_acl(self):
        rsync_acl_list = []
        for h in Host.select():
            if h.is_active():
                for n in h.acl_ips:
                    rsync_acl_list.append(n.ip)
        return dict(values=rsync_acl_list)

    @expose(template="mirrors.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):

        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            raise redirect(forward_url)

        forward_url=None
        previous_url= cherrypy.request.path

        if identity.was_login_attempted():
            msg=_("The credentials you supplied were not correct or "
                   "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg=_("You must provide your Fedora Account System credentials before accessing "
                   "this resource.")
        else:
            msg=_("Please log in.")
            forward_url= cherrypy.request.headers.get("Referer", "/")
        cherrypy.response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=cherrypy.request.params,
                    forward_url=forward_url)

    @expose()
    def logout(self):
        identity.current.logout()
        raise redirect("/")
    
    @expose(template="mirrors.templates.register")
    def register(self, username="", display_name="", email_address="", tg_errors=None):
        if tg_errors:
            turbogears.flash(createErrorString(tg_errors))
            username, display_name, email_address = map(cherrypy.request.input_values.get, ["username", "display_name", "email_address"])
                    
        return dict(username=username, display_name=display_name, email_address=email_address)

    @expose()
    @error_handler(register)
    @validate(validators=my_validators.RegisterSchema)
    def doRegister(self, username, display_name, password1, password2, email_address):
        username = str(username)
        email_address = str(email_address)
        redirect_to_register = lambda:redirect("/register", {"username":username, "display_name":display_name, "email_address":email_address})
        
        try:
            User.by_user_name(username)
        except sqlobject.SQLObjectNotFound:
            pass
        else:
            turbogears.flash("Error:User %s Already Exists"%username)
            raise redirect_to_register()
        
        
        try:
            User.by_email_address(email_address)
        except sqlobject.SQLObjectNotFound:
            pass
        else:
            turbogears.flash("Error:Email-Address %s Already Exists"%username)
            raise redirect_to_register()
        
        #create user
        user = User(user_name=username, email_address=email_address, display_name=str(display_name), password=str(password1))
        
        #add user to user group
        user.addGroup(Group.by_group_name("user"))
        
        raise redirect("/")
        

