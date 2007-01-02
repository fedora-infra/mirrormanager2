<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Edit Mirror ${mirror.hostname}</title>
</head>
<body>
<form action="updateMirror" method="post">
<input type="hidden" name="old_hostname" value="${mirror.hostname}" />

<fieldset >
<legend>Edit Mirror ${mirror.hostname}</legend>
<div>
	<label for="hostname">Host Name: </label>
	<span><input id="hostname" name="hostname" value="${mirror.hostname}" /></span>
</div>

<div>
	<label for="user_active">Mirror Is Active:</label>
	<span><input id="user_active" name="user_active" type="checkbox" checked="${(None, '') [mirror.user_active==True]}" /></span>
</div>

<div >
	<label for="comment" class="textarea">Comment:</label>
	<span><textarea id="comment" name="comment" ><span py:replace="mirror.comment" py:strip="True">Comment</span></textarea></span>
</div>


<div>
	Selected Protocols:
	<ul>
	<li py:for="i,protocol in enumerate(protocols)">
		<label for="protocol_${i}">${protocol.name}</label>
		<span><input type="checkbox" name="protocol_${i}" id="protocol_${i}" value="${protocol.name}" checked="${(None, '') [protocol in mirror.protocols]}" /></span>
	</li>
	</ul>
</div>

<div py:if="'admin' in tg.identity.groups">
	<div>
		<label for="admin_active">Mirror Is Administratively Active:</label>
		<span><input id="admin_active" name="admin_active" type="checkbox" checked="${(None, '') [mirror.admin_active==True]}" /></span>	
	</div>

	<div>
		<label for="private">Mirror Is Private:</label>
		<span><input id="private" name="private" type="checkbox" checked="${(None, '') [mirror.private==True]}" /></span>	
	</div>

	<div>
		<label for="minimum_uptime_percentage">Minimum Uptime Percentage:</label>
		<span><input id="minimum_uptime_percentage" name="minimum_uptime_percentage" value="${mirror.minimum_uptime_percentage}" /></span>
	</div>
</div>

<div>
	<button> Update </button>
</div>

</fieldset>
</form>

</body>
</html>
