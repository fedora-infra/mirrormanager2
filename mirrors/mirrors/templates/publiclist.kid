<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'static.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Public Active Mirrors</title>
</head>
<body>
<h2>The Fedora Mirror System</h2>
<p>
Fedora is distributed to millions of systems globally.  This would not
be possible without the donations of time, disk space, and bandwidth
by hundreds of volunteer system administrators and their companies or
institutions.  Your fast download experience is made possible by these
donations.
This list is dynamically generated every hour, listing only up-to-date mirrors.
</p>
<p>
You may trim the selection through the links below, or see the <a
href="${tg.url('/publiclist')}">whole list</a>.
</p>
<div py:strip="" py:for="p in products">
  <table class="product">
  <tr>
  <th><a href="${tg.url('/publiclist/' + p.name + '/')}"><span py:replace="p.name">Product Name</span></a></th>
  <div py:strip="" py:for="v in p.versions">
<?python
vername=v.name
if vername == u'development':
    vername=u'rawhide'
?>
    <td>
      <strong><a href="${tg.url('/publiclist/' + p.name + '/' + v.name + '/')}"><span py:replace="vername">Version</span></a></strong>
      <ul>
        <li py:for="a in arches"><a href="${tg.url('/publiclist/' + p.name + '/' + v.name + '/' + a + '/')}"><span py:replace="a">Arch</span></a></li>
      </ul>
    </td>
  </div>
  </tr>
  </table>
</div>
<h2>${title} Public Active Mirrors (${numhosts})</h2>
<table class="mirrors">
<tr><th>Country</th><th>Site</th><th>Host</th><th>Content</th><th>Bandwidth</th><th>Comments</th></tr>
<tr py:for="host in hosts">
<td><span py:if="host.country is not None" py:replace="host.country.upper()">Country</span></td>
<td><a href="${host.site.orgUrl}"><span py:replace="host.site.name">Site Name</span></a></td>
<td><span py:replace="host.name">Host Name</span></td>
<td>
<table>
<tr py:for="hc in host.categories" py:if="hc.category.publiclist and (valid_categories is None or hc.category.name in valid_categories)">
<td><span py:replace="hc.category.name">Category name</span></td>
<?python
http=None
ftp=None
rsync=None
for u in hc.urls:
    if not u.private:
        if u.url.startswith('http:'):
	    http=u.url
        elif u.url.startswith('ftp:'):
	    ftp=u.url
        elif u.url.startswith('rsync:'):
	    rsync=u.url
?>
<td><span py:if="http is not None"><a href="${http}">http</a></span></td>
<td><span py:if="ftp is not None"><a href="${ftp}">ftp</a></span></td>
<td><span py:if="rsync is not None"><a href="${rsync}">rsync</a></span></td>
</tr>
</table>
</td>
<td><span py:replace="host.bandwidth">Bandwidth</span></td>
<td><span py:replace="host.comment">Comment</span></td>
</tr>
</table>

<P>
To become a public Fedora mirror, please see <a
href="http://fedoraproject.org/wiki/Infrastructure/Mirroring">http://fedoraproject.org/wiki/Infrastructure/Mirroring</a>.
</P>

</body>
</html>
