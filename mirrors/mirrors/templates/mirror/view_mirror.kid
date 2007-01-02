<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>View Mirror</title>
</head>
<body>

<fieldset >
<legend>Mirror ${mirror.hostname}</legend>
	<div>
		<div class="label">
			HostName:
		</div>
		
		<div class="value">
			${mirror.hostname}
		</div>
	</div>

	<div>
		<div class="label">
			Owner User:
		</div>
		
		<div class="value">
			${mirror.user.user_name}
		</div>
	</div>
		
	<div>
		<div class="label">
			Comment:
		</div>
		
		<div class="value">
			${mirror.comment}
		</div>
	</div>
	
	<div>
		<div class="label">
			System Active Status:
		</div>
		
		<div class="value">
			${mirror.active}
		</div>
	</div>
	
	<div>
		<div class="label">
			User Active Status:
		</div>
		
		<div class="value">
			${mirror.user_active}
		</div>
	</div>
	
	<div>
		<div class="label">
			Admin Active Status:
		</div>
		
		<div class="value">
			${mirror.admin_active}
		</div>
	</div>
	
	<div>
		<div class="label">
			Private:
		</div>
		
		<div class="value">
			${mirror.private}
		</div>
	</div>

	<div>
		<div class="label">
			Uptime Percentage:
		</div>
		
		<div class="value">
			${mirror.uptime_percentage}
		</div>
	</div>
	
	<div>
		<div class="label">
			Minimum Uptime Percentage:
		</div>
		
		<div class="value">
			${mirror.minimum_uptime_percentage}
		</div>
	</div>	
	
	<div>
		<div class="label">
			Releases:
		</div>
		
		<div class="value">
			<ul>
				<li py:for="mirror_release in mirror.mirror_releases">
						${mirror_release.release.name} 
						<div>
							<div class="label">path:</div> 
							<div class="value">${mirror_release.release_path}</div>
						</div>
						<div>
							<div class="label">Architectures:</div> 
						</div>
						<ul>
							<li py:for="mirror_arch in mirror_release.mirror_archs">
								${mirror_arch.arch.name}
								<div>
									<div class="label">Is Up To Date:</div>
									<div class="value">${mirror_arch.is_uptodate}</div>
								</div>
								
								<div>
									<div class="label">Last Failure:</div>
									<div class="value">${mirror_arch.last_failure}</div>
								</div>

								<div>
									<div class="label">Last Failure Reason:</div>
									<div class="value">${mirror_arch.last_failure_reason}</div>
								</div>
							</li>
						</ul>
				</li>
			</ul>
		</div>
	</div>
	
	<div>
		<div class="label">
			Protocols:
		</div>
		
		<div class="value">
			<ul>
				<li py:for="protocol in mirror.protocols">
					${protocol.name}
				</li>
			</ul>
		</div>
	</div>
	
	<div>
		<div class="label">
			Rsync Downloader IPs:
		</div>
		
		<div class="value">
			<ul>
				<li py:for="ip in mirror.ips">
					${ip.ip_addr}
				</li>
			</ul>
		</div>
	</div>

</fieldset>

<div class="links">
	<ul>
		<li> 
			<a href="${tg.url('/mirror/editMirror', hostname=mirror.hostname)}"> Edit Mirror </a>
		</li>
		<li> 
			<a href="${tg.url('/mirror/editMirrorReleases', hostname=mirror.hostname)}"> Update Releases </a>
		</li>
		<li> 
			<a href="${tg.url('/mirror/editRsyncIPs', hostname=mirror.hostname)}"> Update Rsync IPs </a>
		</li>
		<li> 
			<a href="${tg.url('/mirror/deleteMirror', hostname=mirror.hostname)}" class="delete_link"> Delete Mirror </a>
		</li>		
	</ul>
</div>

</body>
</html>