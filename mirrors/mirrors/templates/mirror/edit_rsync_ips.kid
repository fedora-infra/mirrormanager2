<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>New Mirror</title>
<script>
	function addNewRsyncIP()
	{
		ip_id = 0;
		if(window.last_ip_id != undefined)
		{
			if(!getElement('rsync_ip_' + window.last_ip_id).value)
				return;

			ip_id = window.last_ip_id + 1;
		}
		
		window.last_ip_id = ip_id;
		var obj = LI(null, INPUT({'type':'text', 'name':'rsync_ip_'+ip_id, 'id':'rsync_ip_'+ip_id}));
		appendChildNodes('rsync_ips', obj);
	}
</script>
</head>
<body>
<form action="updateRsyncIPs" method="post">
<input name="hostname" value="${mirror.hostname}" type="hidden" />

<fieldset >
<legend>Update Mirror Rsync IPs</legend>
<div>
	<label>Host Name: </label>
	<span>${mirror.hostname}</span>
</div>
	<div>
		<div class="label">
			Rsync Downloader IPs:
		</div>
		
		<div class="value">

			<ul id="rsync_ips">
				<li py:for="ip_id,ip in enumerate(mirror.ips)">
					<input type="text" name="rsync_ip_${ip_id}" id="rsync_ip_${ip_id}" value="${ip.ip_addr}" />

					<span py:if="ip_id == len(mirror.ips)-1">
						<script>
							window.last_ip_id=${ip_id};
						</script>	
					</span>
				</li>
			</ul>
			<a href="#" onclick="addNewRsyncIP(); return false;">+</a>
		</div>
	</div>

<div>
	<button> Update </button>
</div>

</fieldset>
</form>

</body>
</html>
