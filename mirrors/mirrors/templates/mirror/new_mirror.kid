<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>New Mirror</title>
</head>
<body>
<form action="addMirror" method="post">

<fieldset >
<legend>Add New Mirror</legend>
<div>
	<label for="hostname">Host Name: </label>
	<span><input id="hostname" name="hostname" value="${hostname}" /></span>
</div>

<div>
	<label for="user_active">Mirror Is Active:</label>
	<span><input id="user_active" name="user_active" type="checkbox" checked="${(None, '') [user_active==True]}" /></span>
</div>

<div>
	<label for="comment" class="textarea">Comment:</label>
	<span><textarea id="comment" name="comment" ><span py:replace="comment" py:strip="True">Comment</span></textarea></span>
</div>

<div>
	Selected Protocols: ${input_values}
	<ul>
	<li py:for="i,protocol in enumerate(protocols)">
		<label for="protocol_${protocol.name}">${protocol.name}</label>
		<span><input type="checkbox" name="protocol_${protocol.name}" id="protocol_${protocol.name}" value="${protocol.name}" 
					checked="${(None, '') ['protocol_%s'%protocol.name in input_values]}" /></span>
	</li>
	</ul>
</div>

<div>
	<button> Add </button>
</div>

</fieldset>
</form>

</body>
</html>
