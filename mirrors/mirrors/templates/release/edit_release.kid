<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Edit Release ${release.name}</title>
</head>
<body>
<form action="updateRelease" method="post">
<input type="hidden" name="old_release_name" value="${release.name}" />

<fieldset >
<legend>Update Release ${release.name}</legend>
<div>
	<label for="release_name">Release Name:</label>
	<span><input id="release_name" name="release_name" value="${release.name}" /></span>
</div>

<div>
	<label for="canonical">Canonical URL(with $$ARCH):</label>
	<span><input id="canonical" name="canonical" value="${release.canonical}" /></span>
</div>

<div>
	<label for="default_path">Mirrors Default Path:</label>
	<span><input id="default_path" name="default_path" value="${release.default_path}" /></span>
</div>

<div>
	<label for="comment" class="textarea">Comment:</label>
	<span><textarea id="comment" name="comment" ><span py:replace="release.comment" py:strip="True">Comment</span></textarea></span>
</div>

<div >
	<button> Update </button>
</div>

</fieldset>
</form>

</body>
</html>
