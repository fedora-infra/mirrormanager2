<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Welcome to Fedora Mirror Manager</title>
</head>
<body>
<div id="Sites">
<h3>My Sites and Hosts</h3>
<a href="/site/0/new/">[Add Site]</a>
<ul>
	  <li py:for="site in sites">
	  <a href="${'/site/'+str(site.id)}"><span py:replace="site.name">Site Name</span></a>
	  
	  <UL>
	  <LI py:for="h in site.hosts">
	  <a href="${'/host/'+str(h.id)}"><span
	  py:replace="h.name">Host Name</span></a>
	  </LI>
	  </UL>
	  </li>
</ul>
</div>
<div id="RSYNC ACL">
<h3><a href="/rsync_acl">rsync acl</a></h3>
</div>
<div id="adminstuff" py:if="'sysadmin' in tg.identity.groups">
<div id="categories">
<h3>Categories</h3>
<ul>
	  <li py:for="c in categories">
	  <span py:replace="c.name">Category Name</span>&nbsp;
	  <span py:replace="c.directory.name">Directory Name</span>
	  </li>
</ul>
</div>
<div id="Arches">
<h3>Arches</h3>
<ul>
	  <li py:for="arch in arches">
	  <span py:replace="arch.name">Arch Name</span>	
	  </li>
</ul>
</div>
<div id="Products">
<h3>Products</h3>
<ul>
	  <li py:for="p in products">
	  <span py:replace="p.name">Host Name</span>	
	  </li>
</ul>
</div>
<div id="Versions">
<h3>Versions</h3>
<ul>
	  <li py:for="v in versions">
	  <span py:replace="v.product.name">Product Name</span>	
	  <span py:replace="v.name">Version Name</span>	
	  </li>
</ul>
</div>
<div id="Repositories">
<h3>Repositories</h3>
<ul>
	  <li py:for="r in repositories">
  	  <span py:replace="r.name">Repository Name</span>	
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
<ul>
	  <li py:for="cc in embargoed_countries">
  	  <span py:replace="cc.country_code">Country Code</span>	
	  </li>
</ul>
</div>
</div>
</body>
</html>
