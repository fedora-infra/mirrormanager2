<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Welcome to ${tg.config('mirrormanager.projectname','Fedora')} Mirror Manager</title>
<?python
admin_group = tg.config('mirrormanager.admin_group', 'sysadmin')
?>
</head>
<body>

<h1 class="icon48 download">Welcome to ${tg.config('mirrormanager.projectname','Fedora')} Mirror Manager</h1>

<h2 class="icon16">Workflow</h2>

Create:
<ol>
<li> a new Site</li>
<li> a new Host in your Site</li>
<li> a new ACL IP for your Host (DNS name preferred, IP ok too)</li>
<li> a new Category entry for your Host, for Fedora Linux (Fedora 7
  and newer).</li>
<li> For each of FC and FE, one or more URLs by which end users can get
  at your data (HTTP, FTP, and rsync).  If you also make your content
  available for other mirrors via a private rsync URL, create one of
  those too.</li>
</ol>

<h2 class="icon16">Overview</h2>
<p>
<strong>Sites</strong> are the administrative container.  Sites have
<strong>SiteAdmins</strong> which are usernames in the Fedora Account System.
Such people may edit the details of their Sites.  Sites, via <strong>SiteToSite</strong> can also give
read-only access to admins of other Sites, for purposes of seeing the
site-private URLs among other things.  Sites may be marked Private
(e.g. for a company-internal mirror).  As such, they won't appear on
the public lists.  Sites can be temporarily marked
inactive, e.g. if you need to take a host down for maintenance.
</p>
<p>
Sites have one or more <strong>Hosts</strong>, which are machines serving
content to end users.  Hosts may also be marked Private.  Hosts get
their data by pulling from one of the master rsync servers.  The master
rsync servers require a DNS name or IP address to be in their Access
Control List.  As such, each Host should create one or more <strong>ACL
IPs</strong>.  Hosts can also be temporarily marked inactive.
</p>
<p>
Hosts carry content by <strong>Category</strong>.  Fedora's categories include
Fedora Linux (Fedora 7 and newer).  Hosts expose a Category via one or
more <strong>URLs</strong> (public URLs for anonymous http/ftp/rsync, or private URLs
for use by other mirrors only).
</p>
<p>
A HTTP/FTP crawler will scan the public active sites every few hours
to update its database of who has what.  That crawler reports its
User-Agent as mirrormanager-crawler.
</p>

<div id="Sites">
<h3>My Sites and Hosts</h3>
<a href="${tg.url('/site/0/new/')}">[Add Site]</a>
<ul>
	  <li py:for="site in sites">
	  <a href="${tg.url('/site/'+str(site.id))}"><span py:replace="site.name">Site Name</span></a>
	  
	  <ul>
	  <li py:for="h in site.hosts">
	  <a href="${tg.url('/host/'+str(h.id))}"><span
	  py:replace="h.name">Host Name</span></a>
	  </li>
	  </ul>
	  </li>
</ul>
</div>
<div id="RSYNC ACL">
<h3><a href="${tg.url('/rsync_acl')}">rsync acl</a></h3>
</div>

<div id="adminstuff" py:if="admin_group in tg.identity.groups">
<h3><a href="${tg.url('/adminview')}">Admin view</a></h3>
</div>
</body>
</html>
