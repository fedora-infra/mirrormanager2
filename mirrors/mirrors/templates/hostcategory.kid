<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">


    


<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Host Category</title>
</head>
<body>
${form(value=values, action=action, disabled_fields=disabled_fields)}
<div py:if="values is not None">
<h3>URLs serving this content</h3>
<P>
The same content may be served by multiple means: http, ftp, and rsync
are common examples.  Content may also be served via a 'private' URL
only visible to other mirror admins.  Such private URLs usually
include a nonstandard rsync port, and/or a username and password.
Admins from Mirror Sites on your SiteToSite list can see these private URLs.
</P>


	<a href="${tg.url('/host_category_url/0/new?hcid=' + str(values.id))}">[Add]</a>
<ul>
	  <li py:for="url in values.urls">
	  <span py:replace="url.url">URL</span> <a
	  href="${tg.url('/host_category_url/' + str(url.id) + '/delete')}">[Delete]</a>
	  </li>
</ul>

<h3>Up-to-Date Directories this host carries</h3>
<UL>
<LI py:for="dir in values.dirs" py:if="dir.up2date">
    <span py:replace="dir.path">Path</span>
</LI>
</UL>
</div>
</body>
</html>
