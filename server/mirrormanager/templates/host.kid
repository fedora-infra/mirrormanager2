<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<?python
is_siteadmin = False
admin_group = tg.config('mirrormanager.admin_group', 'sysadmin')
if admin_group in tg.identity.groups:
   is_siteadmin = True
else:	
   if values is not None and not action.endswith('create'):
      is_siteadmin = values.site.is_siteadmin_byname(tg.identity.user_name)
?> 
</head>
<body>
<p>
Back to <a href="${tg.url('/site/' + str(site.id))}"><span
py:replace="site.name">Site Name</span></a>
</p>
<h2>${title}</h2>

${form(value=values, action=tg.url(action), disabled_fields=disabled_fields)}
<p>* = Required</p>

<div py:if="values is not None and action.endswith('update')">
Last Checked In: ${values.lastCheckedIn}<br></br>
Last Crawled: ${values.lastCrawled}<br></br>


<div py:if="is_siteadmin">
<h3>Master rsync server Access Control List IPs</h3>
 These host DNS names and/or IP addresses will be allowed to rsync
 from the master rsync/ftp servers.  List here all
 the machines that you use for pulling.<br/>
		  <a href="${tg.url('/host_acl_ip/0/new?hostid=' + str(values.id))}">[Add]</a><br/>
		  <ul>
		  <li py:for="a in values.acl_ips">
		  <span py:replace="a.ip">ACL IP</span>
		  <a href="${tg.url('/host_acl_ip/' + str(a.id) + '/delete')}">[Delete]</a>
		  </li>
		  </ul>

<h3>Site-local Netblocks</h3>
		  Netblocks are used to try to guide and end user to a
		  site-specific mirror.  For example, a university
		  might list their netblocks, and the mirrorlist CGI
		  would return the university-local mirror rather than
		  a country-local mirror.
		  Format is one of 18.0.0.0/255.0.0.0, 18.0.0.0/8, 
		  an IPv6 prefix/length, or a DNS hostname.<br/>
<a href="${tg.url('/host_netblock/0/new?hostid=' + str(values.id))}">[Add]</a><br/>
	<ul>
	<li py:for="a in values.netblocks">
		  <span py:replace="a.netblock">Netblock</span><a
	          href="${tg.url('/host_netblock/' + str(a.id) + '/delete')}">[Delete]</a>
        </li>
        </ul>
</div>
<h3>Countries Allowed</h3>
	Some mirrors need to restrict themselves to serving only end
	users from their country.  If you're one of these, list the
	2-letter ISO code for the countries you will allow end users
	to be from.  The mirrorlist CGI will honor this.<br/>
	<span py:if="is_siteadmin">
	<a href="${tg.url('/host_country_allowed/0/new?hostid=' + str(values.id))}">[Add]</a>
	</span>
	<ul>
	<li py:for="a in values.countries_allowed">
		  <span py:replace="a.country">Country</span>
		  <a href="${tg.url('/host_country_allowed/' + str(a.id) + '/delete')}">[Delete]</a>
        </li>
        </ul>


<hr></hr>
<h2>Categories Carried</h2>
<div py:if="is_siteadmin">
<a href="${tg.url('/host_category/0/new?hostid=' + str(values.id))}">[Add Category]</a>
</div>
<p>
Hosts carry categories of software.  Example Fedora categories include Fedora Core and Fedora Extras.
</p>
<div py:if="values.categories is not None">
<ul>
<li py:for="c in values.categories">
    <a href="${tg.url('/host_category/' + str(c.id))}"><span
    py:replace="c.category.name">Category Name</span></a>
    <span py:if="is_siteadmin"><a
    href="${tg.url('/host_category/' + str(c.id) + '/delete')}">[Delete]</a></span>
    <ul>
    <li py:for="u in c.urls">
    <a href="${u.url}"><span py:replace="u.url">URL</span></a>
    <span py:if="u.private">(Mirrors)</span>
    <!--
    <span py:if="is_siteadmin">
    <a href="${tg.url('/host_category_url/' + str(u.id) + '/delete')}">[Delete]</a>
    </span>
    --> 
    </li>
    </ul>

</li>
</ul>
</div>
<hr />
<p>
<span py:if="is_siteadmin">
<a href="${tg.url('/host/' + str(values.id) + '/delete')}">[Delete Host]</a>
</span>
</p>
</div>
</body>
</html>
