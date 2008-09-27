<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>${title}</title>
</head>
<body>
<p>
Back to <a href="${tg.url('/site/' + str(host.site.id))}"><span
py:replace="host.site.name">Site Name</span></a> / 
<a href="${tg.url('/host/' + str(host.id))}"><span
py:replace="host.name">Host Name</span></a>
</p>

${form(value=values, action=action)}
</body>
</html>
