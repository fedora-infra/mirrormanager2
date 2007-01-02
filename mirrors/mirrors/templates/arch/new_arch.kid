<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>New Arch</title>
</head>
<body>
<form action="addArch" method="post">

<fieldset >
<legend>Add New Arch</legend>
<div>
	<label for="arch_name">Arch Name:</label>
	<span><input id="arch_name" name="arch_name" value="${arch_name}" /></span>
</div>

<div>
	<label for="comment" class="textarea">Comment:</label>
	<span><textarea id="comment" name="comment" ><span py:replace="comment" py:strip="True">Comment</span></textarea></span>
</div>

<div >
	<button> Add </button>
</div>

</fieldset>
</form>

</body>
</html>
