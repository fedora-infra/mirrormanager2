<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Fedora Mirror Manager Admin View</title>
<?python
admin_group = tg.config('mirrormanager.admin_group', 'sysadmin')
?>
</head>
<body>

<div py:if="admin_group not in tg.identity.groups">
Nothing to see here, move along.
</div>

<div id="adminview" py:if="admin_group in tg.identity.groups">

<div id="categories">
<h3>Categories <a href="${tg.url('/category/new')">[Add]</a></h3>
<ul>
	  <li py:for="c in categories">
	  <span py:replace="c.name">Category Name</span>&nbsp;
	  <span py:replace="c.topdir.name">Directory Name</span>
	  </li>
</ul>
</div>
<div id="Arches">
<h3>Arches <a href="${tg.url('/arch/0/new')}">[Add]</a></h3>

<ul>
	  <li py:for="arch in arches">
	  <span py:replace="arch.name">Arch Name</span>	 <a href="${tg.url('/arch/'+str(arch.id)+'/delete')}">[Delete]</a>
	  </li>
</ul>
</div>
<div id="Products">
<h3>Products <a href="${tg.url('/product/0/new')}">[Add]</a></h3>
<ul>
	  <li py:for="p in products">
	  <span py:replace="p.name">Product</span> <a href="${tg.url('/product/'+str(p.id)+'/delete')}">[Delete]</a>
	  </li>
</ul>
</div>
<div id="Versions">
<h3>Versions <a href="${tg.url('/version/0/new')}">[Add]</a></h3>
<ul>
	  <li py:for="v in versions">
	  <a href="${tg.url('/version/'+str(v.id)+'/')}">
	  <span py:replace="v.product.name">Product Name</span>	
	  <span py:replace="v.name">Version Name</span>
	  </a>
	   <a href="${tg.url('/version/'+str(v.id)+'/delete')}">[Delete]</a>	
	  </li>
</ul>
</div>
<div id="Repositories">
    <h3>Repositories</h3>
    <ul>
    	  <li py:for="r in repositories">
    	  <a href="${tg.url('/repository/'+str(r.id)+'/')}">
         	  <span py:replace="r.directory.name">Repository Name
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
<h3>Embargoed Counries <a href="${tg.url('/embargoed_country/0/new')}">[Add]</a></h3>
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
<div id="Repository Redirects">
<h3>Repository Redirects</h3>
<ul>
	  <li py:for="r in repository_redirects">
	  <a href="${tg.url('/repository_redirect/'+str(r.id)+'/')}"><span py:replace="r.fromRepo">from
	  Repo</span> -&gt; <span py:replace="r.toRepo">to Repo</span></a> 
	  </li>
</ul>
</div>
<div id="Country Continent Redirects">
<h3>Country Continent Redirects</h3>
<ul>
	  <li py:for="c in country_continent_redirects">
	  <a href="${tg.url('/country_continent_redirect/'+str(c.id)+'/')}"><span py:replace="c.country">Country</span></a> -&gt; <span py:replace="c.continent">Continent</span>
	  </li>
</ul>
</div>
<div id="Locations">
<h3>Locations <a href="${tg.url('/location/new')}">[Add]</a></h3>
<ul>
	  <li py:for="l in locations"> <a href="${tg.url('/location/'+str(l.id)+'/')}"><span py:replace="l.name">Location</span></a>
	    <a href="${tg.url('/location/%s/delete' % (l.id))}">[Delete]</a>

	    <UL>
	      <li py:for="h in l.hosts">
	      	<a href="${tg.url('/host/' + str(h.id))}"><span py:replace="h.name">Host name</span></a>
	      	<a href="${tg.url('/location/%s/%s/delete' % (l.id,h.id))}">[Delete]</a>
	      </li>
	    </UL>
	  </li>
</ul>
</div>
</div>
</body>
</html>
