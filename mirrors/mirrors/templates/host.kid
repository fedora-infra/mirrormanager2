<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
</head>
<body>
<h2>${title}</h2>
<?python
downstream_siteadmin=False
if values is not None:
   downstream_siteadmin=values.site.is_downstream_siteadmin_byname(tg.identity.user.user_name)
?> 
 
${form(value=values, action=action, disabled_fields=disabled_fields)}


<div py:if="values is not None and action.endswith('update')">
Last Checked In: ${values.timestamp}
<UL>
	<LI>
	<label for="countries_allowed">Countries Allowed: </label>
	<span py:if="not downstream_siteadmin">
	<a href="/host_country_allowed/0/new?hostid=${values.id}">[Add]</a>
	</span>
	<ul>
	<li py:for="a in values.countries_allowed">
		  <span py:replace="a.country">Country</span>
		  <span py:if="downstream_siteadmin">
		  <a
		  href="/host_country_allowed/${a.id}/delete">[Delete]</a>
		  </span>
        </li>
        </ul>
	</LI>
	<div py:if="not downstream_siteadmin">

	     <LI>
	          <label for="acl_ips">ACL IPs: </label>
		  <a href="/host_acl_ip/0/new?hostid=${values.id}">[Add]</a>
		  <ul>
		  <li py:for="a in values.acl_ips">
		  <span py:replace="a.ip">ACL IP</span><a href="/host_acl_ip/${a.id}/delete">[Delete]</a>
		  </li>
		  </ul>
	     </LI>
     	<LI>
	<label for="netblocks">Netblocks: </label> <a href="/host_netblock/0/new?hostid=${values.id}">[Add]</a>
	<ul>
	<li py:for="a in values.netblocks">
		  <span py:replace="a.netblock">Netblock</span><a href="/host_netblock/${a.id}/delete">[Delete]</a>
        </li>
        </ul>
	</LI>
     </div>
</UL>
<hr></hr>
<h2>Categories Carried</h2>
<div py:if="not downstream_siteadmin">
<a href="/host_category/0/new?hostid=${values.id}">[Add Category]</a>
</div>

<div py:if="values.categories is not None">
<UL>
<LI py:for="c in values.categories">
    <a href="/host_category/${c.id}"><span
    py:replace="c.category.name">Category Name</span></a>
    <span py:if="not downstream_siteadmin"><a href="/host_category/${c.id}/delete">[Delete]</a></span>
    <UL>
    <LI py:for="u in c.urls">
    <div py:if="u.private">(Mirrors)</div>
    <a href="${u.url}"><span py:replace="u.url">URL</span></a>
    <span py:if="not downstream_siteadmin">
    <a href="/host_category_url/${u.id}/delete">[Delete]</a>
    </span>
    </LI>
    </UL>

</LI>
</UL>
</div>
<P>
<span py:if="not downstream_siteadmin">
<a href="/host/${values.id}/delete">[Delete Host]</a>
</span>
</P>
</div>
</body>
</html>
