<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Update Release Architectures</title>
</head>
<body>
<form action="updateReleaseArchs" method="post">

<fieldset >
<legend>Update Release Architectures</legend>
<div>
	<label for="release_name">Release Name:</label>
	<span id="release_name">${release.name}</span>
	<input type="hidden" name="release_name" value="${release.name}" />
</div>

<div py:for="arch in archs">
	<span><input type="checkbox" id="arch_${arch.id}" name="arch_${arch.id}" value="${arch.id}" checked="${(None, '') [arch in release.archs]}"/></span>
	<label for="arch_${arch.id}">${arch.name}</label>
</div>

<div >
	<button> Update </button>
</div>

</fieldset>
</form>

</body>
</html>
