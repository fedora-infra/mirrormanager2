<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">


    


<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Host Category</title>
</head>
<body>

${form(value=values, action=action)}
<div py:if="values is not None">
<h3>URLs serving this content</h3>
<ul>
	  <li py:for="url in values.urls">
	  <a href="${'/host_category_url/'+str(url.id)}"><span py:replace="url.url">URL</span></a>
	  </li>
	  </ul>
</div>
</body>
</html>
