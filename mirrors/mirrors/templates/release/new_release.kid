<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>New Release</title>
</head>
<body>
<form action="addRelease" method="post">

<fieldset >
<legend>Add New Release</legend>
<div>
	<label for="release_name">Release Name: </label>
	<span><input id="release_name" name="release_name" value="${release_name}" /></span>
</div>

<div>
	<label for="canonical">Canonical URL(with $$ARCH):</label>
	<span><input id="canonical" name="canonical" value="${canonical}" /></span>
</div>

<div>
	<label for="default_path">Mirrors Default Path:</label>
	<span><input id="default_path" name="default_path" value="${default_path}" /></span>
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
