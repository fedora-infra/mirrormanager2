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

</body>
</html>
