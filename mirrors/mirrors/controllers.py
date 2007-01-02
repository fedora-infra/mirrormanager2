from turbogears.identity.exceptions import IdentityFailure
import logging

import cherrypy

import turbogears
from turbogears import controllers, expose, validate, redirect, widgets, validators, error_handler, exception_handler
from turbogears import identity
from tgfastdata import DataController
import sqlobject

from mirrors import json
from mirrors import my_validators
from mirrors.model import Release, Config, Arch, Mirror, Protocol, MirrorRelease, MirrorArch, IP
from mirrors.identity_models import User, Group
from mirrors.lib import createErrorString

log = logging.getLogger("mirrors.controllers")

class MirrorException(Exception):
    pass

class ArchController(controllers.Controller, identity.SecureResource):  
    require = identity.in_group("admin")
      
    @expose(template="mirrors.templates.arch.new_arch")
    def newArch(self, arch_name="", comment="", tg_errors=None):
        if tg_errors:
            turbogears.flash(createErrorString(tg_errors))

        return {"arch_name":arch_name, "comment":comment}

    @expose()
    @error_handler(newArch)
    @validate(validators={"arch_name":validators.PlainText(not_empty=True),
                          "comment":validators.String()})
    def addArch(self, arch_name, comment, tg_errors=None):
        try:
            Arch.byName(str(arch_name))
            turbogears.flash("Error:Arch %s Already Exists"%arch_name)
            raise redirect("/arch/newArch", {"arch_name":arch_name, "comment":comment})
        except sqlobject.SQLObjectNotFound:
            pass

        arch = Arch(name=arch_name, comment=comment)
        turbogears.flash("Arch %s Added Successfully"%arch_name)
    
        raise redirect("/arch/listArchs")

    @expose(template="mirrors.templates.arch.list_archs")
    def listArchs(self):
        archs = Arch.select(orderBy=Arch.q.name)
        return dict(archs=archs)

    @expose(template="mirrors.templates.arch.edit_arch")
    def editArch(self, arch_name, tg_errors=None, tg_exceptions=None):
        if tg_errors:
            turbogears.flash(createErrorString(tg_errors))
        elif tg_exceptions:
            turbogears.flash("Error:" + str(tg_exceptions))
            
        arch = Arch.byName(str(arch_name))    
        return {"arch":arch}
    
    @expose()
    @error_handler(editArch)
    @validate(validators={"arch_name":validators.PlainText(not_empty=True),
                          "comment":validators.String()})
    def updateArch(self, old_arch_name, arch_name, comment):
        #arch name might be change
        if old_arch_name != arch_name:
            try:
                Arch.byName(str(arch_name))
                turbogears.flash("Error:Arch %s Already Exists"%arch_name)
                raise redirect("/arch/editArch", {"arch_name":old_arch_name})
            except sqlobject.SQLObjectNotFound:
                pass
        
        arch = Arch.byName(str(old_arch_name))
        arch.set(name = arch_name, comment = comment)
        turbogears.flash("Arch %s Updated Successfully"%arch_name)

        raise redirect("/arch/listArchs")
        
    @expose()
    def deleteArch(self, arch_name):
        arch = Arch.byName(str(arch_name))
        arch.destroySelf()
        raise redirect("/arch/listArchs")



class ReleaseController(controllers.Controller, identity.SecureResource):
    require = identity.in_group("admin")
    
    @expose(template="mirrors.templates.release.new_release")
    def newRelease(self, tg_errors=None, release_name="", canonical="", default_path="", comment=""):
        if tg_errors:
            turbogears.flash(createErrorString(tg_errors))
            release_name, canonical, default_path, comment = map(cherrypy.request.input_values.get, ["release_name", "canonical", "default_path", "comment"])
            
        return {"release_name":release_name, "comment":comment, "canonical":canonical, "default_path":default_path}

    @expose()
    @error_handler(newRelease)
    @validate(validators={"release_name":validators.String(not_empty=True),
                          "comment":validators.String(),
                          "canonical":my_validators.URLWithArchValidator(not_empty=True)})
    def addRelease(self, release_name, comment, canonical, default_path, tg_errors=None):
        try:
            Release.byName(str(release_name))
            turbogears.flash("Error:Release %s Already Exists"%release_name)
            raise redirect("/release/newRelease", {"release_name":release_name, "comment":comment, "canonical":canonical, default_path:"default_path"})
        except sqlobject.SQLObjectNotFound:
            pass

        config = Config.get(1)
        
        release = Release(name=release_name, comment=comment, config=config, canonical=canonical, default_path=default_path)
        turbogears.flash("Release %s Added Successfully"%release_name)
    
        raise redirect("/release/listReleases")

    @expose(template="mirrors.templates.release.list_releases")
    def listReleases(self):
        releases = Release.select(orderBy=Release.q.name)
        return dict(releases=releases)

    @expose(template="mirrors.templates.release.edit_release")
    def editRelease(self, release_name, tg_errors=None, tg_exceptions=None):
        if tg_errors:
            turbogears.flash(createErrorString(tg_errors))
        elif tg_exceptions:
            turbogears.flash("Error:" + str(tg_exceptions))
            
        release = Release.byName(str(release_name))    
        return {"release":release}
    
    @expose()
    @error_handler(editRelease)
    @validate(validators={"release_name":validators.String(not_empty=True),
                          "comment":validators.String(),
                          "canonical":my_validators.URLWithArchValidator(not_empty=True)})
    def updateRelease(self, old_release_name, release_name, canonical, default_path, comment):
        #release name might be change
        if old_release_name != release_name:
            try:
                Release.byName(str(release_name))
                turbogears.flash("Error:Release %s Already Exists"%release_name)
                raise redirect("/release/editRelease", {"release_name":old_release_name})
            except sqlobject.SQLObjectNotFound:
                pass
        
        release = Release.byName(str(old_release_name))
        release.set(name = release_name, canonical=canonical, comment = comment, default_path=default_path)
        turbogears.flash("Release %s Updated Successfully"%release_name)

        raise redirect("/release/listReleases")
        
    @expose()
    def deleteRelease(self, release_name):
        release = Release.byName(str(release_name))
        release.destroySelf()
        raise redirect("/release/listReleases")

    @expose(template="mirrors.templates.release.edit_release_archs")
    def editReleaseArchs(self, release_name):
        release = Release.byName(str(release_name))
        archs = Arch.select(orderBy=Arch.q.name)
        
        return {"release":release, "archs":archs}
    
    @expose()
    def updateReleaseArchs(self, release_name, **kargs):
        release = Release.byName(str(release_name))
        selected_archs = []
        for name, value in kargs.items():
            if name.startswith("arch_"):
                arch_id = int(value)
                arch = Arch.get(arch_id)
                selected_archs.append(arch)
        
        #remove unselected archs
        for arch in release.archs:
            if arch not in selected_archs:
                release.removeArch(arch)
        
        #add newly selected archs
        for arch in selected_archs:
            if arch not in release.archs:
                release.addArch(arch)
 
        turbogears.flash("Archs for Release %s Updated Successfully"%release_name)
        raise redirect("/release/listReleases")

class MirrorController(controllers.Controller):
    
    def __checkAccessToMirror(self, hostname):
        if not "admin" in identity.current.groups:
            mirror = Mirror.byHostname(str(hostname))
            if identity.current.user != mirror.user:
                raise IdentityFailure("You don't have access to mirror %s"%hostname)
    
    @expose(template="mirrors.templates.mirror.new_mirror")
    @identity.require(identity.in_any_group("admin", "user"))
    def newMirror(self, hostname="", user_active=False, comment="", tg_errors=None, **input_values):
        if tg_errors:
            turbogears.flash(createErrorString(tg_errors))
            hostname, user_active, comment = map(cherrypy.request.input_values.get, ["hostname", "user_active", "comment"])
            input_values = cherrypy.request.input_values
            
        return {"hostname":hostname, "comment":comment, "user_active":user_active, "protocols":Protocol.select(), "input_values":input_values}

    @expose()
    @error_handler(newMirror)
    @validate(validators={"hostname":validators.String(not_empty=True),
                          "comment":validators.String(),
                          "user_active":validators.Bool(default=True)})
    @identity.require(identity.in_any_group("admin", "user"))
    def addMirror(self, hostname, comment, user_active=False, tg_errors=None, **kwargs):
        hostname = str(hostname)
        try:
            Mirror.byHostname(hostname)
            turbogears.flash("Error:Mirror %s Already Exists"%hostname)
            dic = {"hostname":hostname, "user_active":user_active, "comment":comment}
            dic.update(kwargs)
            raise redirect("/mirror/newMirror", dic)
        except sqlobject.SQLObjectNotFound:
            pass

        mirror = Mirror(hostname=hostname, comment=str(comment), user_active=user_active, user=identity.current.user)
        self.__updateMirrorProtocols(mirror, **kwargs)
        
        turbogears.flash("Mirror %s Added Successfully"%hostname)
    
        raise redirect("/mirror/myMirrors")

    @expose(template="mirrors.templates.mirror.my_mirrors")
    @identity.require(identity.in_any_group("admin", "user"))
    def myMirrors(self):
        if "admin" in identity.current.groups:
            return {"mirrors":Mirror.select()}
        else:
            return {"mirrors":Mirror.selectBy(user=identity.current.user)}
    
    @expose(template="mirrors.templates.mirror.view_mirror")    
    @identity.require(identity.in_any_group("admin", "user"))
    def viewMirror(self, hostname):
        self.__checkAccessToMirror(hostname)
        return {"mirror":Mirror.byHostname(str(hostname))}

    @expose(template="mirrors.templates.mirror.edit_mirror")
    @identity.require(identity.in_any_group("admin", "user"))
    def editMirror(self, hostname, tg_errors=None, tg_exceptions=None):
        if tg_errors:
            turbogears.flash(createErrorString(tg_errors))
        elif tg_exceptions:
            turbogears.flash("Error:" + str(tg_exceptions))
            
        self.__checkAccessToMirror(hostname)

        mirror = Mirror.byHostname(str(hostname))    
        return {"mirror":mirror, "protocols":Protocol.select()}
    
    @expose()
    @error_handler(editMirror)
    @validate(validators={"hostname":validators.String(not_empty=True),
                          "comment":validators.String(),
                          "user_active":validators.Bool(default=False),
                          "minimum_uptime_percentage":validators.Int(),
                          "admin_active":validators.Bool(default=False),
                          "private":validators.Bool(default=False)})
    @identity.require(identity.in_any_group("admin", "user"))
    def updateMirror(self, old_hostname, hostname, comment, user_active=False, **kwargs):
        #release name might be change
        if old_hostname != hostname:
            try:
                Mirror.byHostname(str(hostname))
                turbogears.flash("Error:Mirror %s Already Exists"%hostname)
                raise redirect("/mirror/editMirror", {"hostname":old_hostname})
            except sqlobject.SQLObjectNotFound:
                pass
        
        self.__checkAccessToMirror(old_hostname)

        mirror = Mirror.byHostname(str(old_hostname))
        update_dic = dict(hostname=hostname, user_active=user_active, comment = comment)
        
        if "admin" in identity.current.groups:

            for key in ["admin_active", "private", "minimum_uptime_percentage"]:
                update_dic[key] = kwargs[key]
        
        mirror.set(**update_dic)
        self.__updateMirrorProtocols(mirror, **kwargs)
        
        turbogears.flash("Mirror %s Updated Successfully"%hostname)

        raise redirect("/mirror/viewMirror",hostname=hostname)

    def __updateMirrorProtocols(self, mirror, **kwargs):
        """
            Update Mirror Protocols by finding all protocol inputs in kwargs
        """
        selected_protocols = []
        
        for name, value in kwargs.items():
            if name.startswith("protocol"):
                protocol = Protocol.byName(str(value))
                selected_protocols.append(protocol)
        
        for protocol in mirror.protocols:
            if protocol not in selected_protocols:
                mirror.removeProtocol(protocol)
        
        for protocol in selected_protocols:
            if protocol not in mirror.protocols:
                mirror.addProtocol(protocol)
        
    @expose(template="mirrors.templates.mirror.edit_mirror_releases")    
    @identity.require(identity.in_any_group("admin", "user"))
    def editMirrorReleases(self, hostname):
        self.__checkAccessToMirror(hostname)
        mirror = Mirror.byHostname(str(hostname))
        
        #create a dic of release=>mirror_release,archs_list
        release_to_mirror_release = {}
        for mirror_release in mirror.mirror_releases:
            
            #a list of archs in a release of mirror
            mirror_archs = []
            for mirror_arch in mirror_release.mirror_archs:
                mirror_archs.append(mirror_arch.arch)
                
            release_to_mirror_release[mirror_release.release] = (mirror_release, mirror_archs)
        
        return {"mirror":mirror, "releases":Release.select(), "release_to_mirror_release":release_to_mirror_release}
    
    @expose()
    @identity.require(identity.in_any_group("admin", "user"))
    def updateMirrorReleases(self, hostname, **kwargs):
        self.__checkAccessToMirror(hostname)
        mirror = Mirror.byHostname(str(hostname))
        
        #find enable releases, release=>releat_path, list_of_enabled_archs
        enabled_releases = {}
        for name,value in kwargs.items():
            if name.startswith("has_release_"):
                release = Release.byName(str(value))
                release_id = int(name[name.rfind("_")+1:])
                
                #find this release archs
                enabled_archs = []
                release_path = ""
                for sname, svalue in kwargs.items():
                    if sname.startswith("release_arch_%d"%release_id):
                        arch = Arch.byName(str(svalue))
                        enabled_archs.append(arch)
                        
                    elif sname == "release_path_%d"%release_id:
                        release_path = svalue
                
                enabled_releases[release] = (release_path, enabled_archs)
        
        
        
        for mirror_release in mirror.mirror_releases:
            
            #if release removed
            if not enabled_releases.has_key(mirror_release.release):
                
                #delete all mirror release archs
                for mirror_arch in mirror_release.mirror_archs:
                    mirror_arch.destroySelf()
                
                #delete mirror release
                mirror_release.destroySelf()
    
        
        for release, (release_path, archs) in enabled_releases.items():
            
            mirror_release_result = MirrorRelease.selectBy(release=release, mirror=mirror)
            
            #if release already exists, check for changed release path and mirror archs
            if mirror_release_result.count():
                mirror_release = mirror_release_result[0]
                
                mirror_release.set(release_path=release_path)
                
                mirror_archs = [mirror_arch.arch for mirror_arch in mirror_release.mirror_archs]
                    
                #check for deleted mirror archs
                for mirror_arch in mirror_release.mirror_archs:
                    if mirror_arch.arch not in archs:
                        mirror_arch.destroySelf()
                
                #check for newly added archs
                for arch in archs:
                    if arch not in mirror_archs:
                        MirrorArch(arch=arch, mirror_release=mirror_release)
                
            
            #add new mirror release and mirror arch
            else:
                mirror_release = MirrorRelease(mirror=mirror, release_path=str(release_path), release=release)
            
                for arch in archs:
                    mirror_arch = MirrorArch(arch=arch, mirror_release=mirror_release)

        turbogears.flash("Mirror %s Releases Updated Successfully"%hostname)

        raise redirect("/mirror/viewMirror",hostname=hostname)

            
    @expose(template="mirrors.templates.mirror.edit_rsync_ips")
    @identity.require(identity.in_any_group("admin", "user"))
    def editRsyncIPs(self, hostname, tg_exceptions=None):
        self.__checkAccessToMirror(hostname)
        mirror = Mirror.byHostname(str(hostname))
        
        return {"mirror":mirror}
      
    def updateRsyncIPsExceptionHandler(self, tg_exceptions=None):
        if tg_exceptions:
            turbogears.flash("Error:" + str(tg_exceptions))

        raise redirect("/mirror/editRsyncIPs", hostname=str(cherrypy.request.params["hostname"]))

    
    @expose()
    @exception_handler(updateRsyncIPsExceptionHandler)
    @identity.require(identity.in_any_group("admin", "user"))
    def updateRsyncIPs(self, hostname, **kwargs):
        self.__checkAccessToMirror(hostname)
        mirror = Mirror.byHostname(str(hostname))
        
        rsync_ips = []
        for name, value in kwargs.items():
            if name.startswith("rsync_ip_"):
                value = str(value).strip()
                if value:
                    self.__validateIPAddr(value)
                    rsync_ips.append(value)
        
        if len(rsync_ips) > 4:
            raise "Mirror can't have more than 4 ip addresses"
        
        to_add_ips = []
        for ipaddr in rsync_ips:
            try:
                ip_obj = IP.byIPAddr(ipaddr)
                
                if ip_obj.mirror != mirror:
                    raise MirrorException("IP %s is registered for another mirror"%ipaddr)
                
            except sqlobject.SQLObjectNotFound:
                #don't add an ip before all checkings are done
                to_add_ips.append(ipaddr)
                
                
        for ipaddr in to_add_ips:
            IP(mirror=mirror, ip_addr=ipaddr)
        
        for ip_obj in mirror.ips:
            if ip_obj.ip_addr not in rsync_ips:
                ip_obj.destroySelf()

        turbogears.flash("Mirror %s Releases Updated Successfully"%hostname)

        raise redirect("/mirror/viewMirror",hostname=hostname)
        
        
    def __validateIPAddr(self, ipaddr):
        """
            Validate IP Adress and raise exception
        """
        sp = ipaddr.split(".")
        
        if len(sp) != 4:
            raise MirrorException("Invalid IP Address %s"%ipaddr)
        
        for ip_part in sp:
            try:
                ip_part = int(ip_part)
            except ValueError:
                raise MirrorException("Invalid IP Address %s"%ipaddr)
            
            if ip_part <0 or ip_part>255:
                raise MirrorException("Invalid IP Address %s"%ipaddr)

    @expose()
    @identity.require(identity.in_any_group("admin", "user"))
    def deleteMirror(self, hostname):
        self.__checkAccessToMirror(hostname)
        mirror = Mirror.byHostname(str(hostname))
        
        #delete mirror release and mirror archs
        for mirror_release in mirror.mirror_releases:
            for mirror_arch in mirror_release.mirror_archs:
                mirror_arch.destroySelf()
            
            mirror_release.destroySelf()
        
        #delete mirror ips
        for ip in mirror.ips:
            ip.destroySelf()
        
        #delete mirror itself
        mirror.destroySelf()
        
        raise redirect("/mirror/myMirrors")

class Root(controllers.RootController):
    release = ReleaseController()
    arch = ArchController()
    mirror = MirrorController()
    
    @expose(template="mirrors.templates.welcome")
    @identity.require(identity.in_any_group("admin", "user"))
    def index(self):
        return dict()

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
            msg=_("You must provide your credentials before accessing "
                   "this resmailource.")
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
        
        raise redirect("/mirror/newMirror")
        