<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Welcome to Fedora Mirror Manager</title>
</head>
<body>
<h2>Workflow</h2>

Create:
<OL>
<LI> a new Site</LI>
<LI> a new Host in your Site</LI>
<LI> a new ACL IP for your Host (DNS name preferred, IP ok too)</LI>
<LI>two new Category entries for your Host, one for Fedora Core, and one
  for Fedora Extras if you carry it.</LI>
<LI> For each of FC and FE, one or more URLs by which end users can get
  at your data (HTTP, FTP, and rsync).  If you also make your content
  available for other mirrors via a private rsync URL, create one of
  those too.</LI>
</OL>

<h2>Overview</h2>
<P>
<b>Sites</b> are the administrative container.  Sites have
<b>SiteAdmins</b> which are usernames in the Fedora Account System.
Such people may edit the details of their Sites.  Sites, via <b>SiteToSite</b> can also give
read-only access to admins of other Sites, for purposes of seeing the
site-private URLs among other things.  Sites may be marked Private
(e.g. for a company-internal mirror).  As such, they won't appear on
the public lists.  Sites can be temporarily marked
inactive, e.g. if you need to take a host down for maintenance.
</P>
<P>
Sites have one or more <b>Hosts</b>, which are machines serving
content to end users.  Hosts may also be marked Private.  Hosts get
their data by pulling from one of the master rsync servers.  The master
rsync servers require a DNS name or IP address to be in their Access
Control List.  As such, each Host should create one or more <b>ACL
IPs</b>.  Hosts can also be temporarily marked inactive.
</P>
<P>
Hosts carry content by <b>Category</b>.  Fedora's categories include
Fedora Core and Fedora Extras.  Hosts expose a Category via one or
more <b>URLs</b> (public URLs for anonymous http/ftp/rsync, or private URLs
for use by other mirrors only).
</P>
<P>
A HTTP/FTP crawler will scan the public active sites every few hours
to update its database of who has what.  That crawler current runs
from publictest7.fedora.redhat.com.
</P>

<div id="Sites">
<h3>My Sites and Hosts</h3>
<a href="${tg.url('/site/0/new/')}">[Add Site]</a>
<ul>
	  <li py:for="site in sites">
	  <a href="${tg.url('/site/'+str(site.id))}"><span py:replace="site.name">Site Name</span></a>
	  
	  <UL>
	  <LI py:for="h in site.hosts">
	  <a href="${tg.url('/host/'+str(h.id))}"><span
	  py:replace="h.name">Host Name</span></a>
	  </LI>
	  </UL>
	  </li>
</ul>
</div>
<div id="PublicList">
<h3><a href="${tg.url('/publiclist')}">public list</a></h3>
</div>
<div id="RSYNC ACL">
<h3><a href="${tg.url('/rsync_acl')}">rsync acl</a></h3>
</div>
<div id="adminstuff" py:if="'sysadmin' in tg.identity.groups">
<div id="categories">
<h3>Categories</h3>
<ul>
	  <li py:for="c in categories">
	  <span py:replace="c.name">Category Name</span>&nbsp;
	  <span py:replace="c.topdir.name">Directory Name</span>
	  </li>
</ul>
</div>
<div id="Arches">
<h3>Arches</h3>
<a href="${tg.url('/arch/0/new')}">[Add]</a>

<ul>
	  <li py:for="arch in arches">
	  <span py:replace="arch.name">Arch Name</span>	 <a href="${tg.url('/arch/'+str(arch.id)+'/delete')}">[Delete]</a>
	  </li>
</ul>
</div>
<div id="Products">
<h3>Products</h3>
<a href="${tg.url('/product/0/new')}">[Add]</a>
<ul>
	  <li py:for="p in products">
	  <span py:replace="p.name">Product</span> <a href="${tg.url('/product/'+str(p.id)+'/delete')}">[Delete]</a>
	  </li>
</ul>
</div>
<div id="Versions">
<h3>Versions</h3>
<a href="${tg.url('/version/0/new')}">[Add]</a>
<ul>
	  <li py:for="v in versions">
	  <span py:replace="v.product.name">Product Name</span>	
	  <span py:replace="v.name">Version Name</span>
	   <a href="${tg.url('/version/'+str(v.id)+'/delete')}">[Delete]</a>	
	  </li>
</ul>
</div>
<div id="Repositories">
<h3>Repositories</h3>
<ul>
	  <li py:for="r in repositories">
	  <a href="${tg.url('/repository/'+str(r.id)+'/')}">
     	  <span py:replace="r.name">Repository Name
	   </span></a>	
	   <a href="${tg.url('/repository/'+str(r.id)+'/delete')}">[Delete]</a>	
	  </li>
</ul>
</div>
<div id="Directories">
<h3>Directories</h3>
<ul>
	  <li py:for="d in directories">
	  <span py:replace="d.name">Directory Name</span>	
	  </li>
</ul>
</div>
<div id="Embargoed Countries">
<h3>Embargoed Counries</h3>
<a href="${tg.url('/embargoed_country/0/new')}">[Add]</a>
<ul>
	  <li py:for="cc in embargoed_countries">
  	  <span py:replace="cc.country_code">Country Code</span>	   <a href="${tg.url('/embargoed_country/'+str(cc.id)+'/delete')}">[Delete]</a>	
	
	  </li>
</ul>
</div>
<div id="Netblocks">
<h3>Netblocks</h3>
<ul>
	  <li py:for="n in netblocks">
	  <a href="${tg.url('/host/'+str(n.host.id)+'/')}"><span py:replace="n.host.name">Host Name</span></a> 
 	  <span py:replace="n.netblock">Netblock</span>
	  </li>
</ul>
</div>
</div>
</body>
</html>
