<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>User Registeration</title>
</head>
<body>
<form action="/doRegister" method="post">

<fieldset >
<legend>Register New User</legend>
<div>
	<label for="username">Username: </label>
	<span><input id="username" name="username" value="${username}" /></span>
</div>

<div>
	<label for="display_name">Display Name: </label>
	<span><input id="display_name" name="display_name" value="${display_name}" /></span>
</div>

<div>
	<label for="email_address">Email: </label>
	<span><input id="email_address" name="email_address" value="${email_address}" /></span>
</div>

<div>
	<label for="password1">Password: </label>
	<span><input id="password1" name="password1" type="password" value="" /></span>
</div>

<div>
	<label for="password2">Password(Confirm): </label>
	<span><input id="password2" name="password2" type="password" value="" /></span>
</div>

<div>
	<button> Add </button>
</div>

</fieldset>
</form>

</body>
</html>
