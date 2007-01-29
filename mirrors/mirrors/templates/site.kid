<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
</head>
<body>
<?python
disabled_fields = []
if 'admin' not in tg.identity.groups:
   disabled_fields.append('admin_active')
?>

${form(value=values, action=action, disabled_fields=disabled_fields)}

<div py:if="values is not None">
<div py:if="action.endswith('update')">
	<label for="admins">Admins: </label> <a href="/siteadmin/0/new?siteid=${values.id}">[Add]</a>
	<ul>
	<li py:for="a in values.admins">
		  <span py:replace="a.username">User Name</span><a href="/siteadmin/${a.id}/delete">[Delete]</a>
        </li>
        </ul>
</div>
<a href="/site/${values.id}/delete">[Delete Site]</a>
</div>
</body>
</html>
