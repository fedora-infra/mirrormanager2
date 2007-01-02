<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>My Mirrors</title>
</head>
<body>
	<table class="list">
		<thead>
			<tr>
				<th>
					Row
				</th>
				<th>
					Hostname
				</th>
				<th>
					Comment
				</th>
				<th>
					System Active
				</th>
				<th>
					User Active
				</th>
				<th>
					Admin Active
				</th>
				<th>
					Uptime Percentage
				</th>
				<th>
					Min Uptime Percentage
				</th>
				<th>
					Private
				</th>
				<th>
					Releases
				</th>
				<th>
					Protocols
				</th>
				<th>
					View
				</th>
			</tr>		
		</thead>
		<tr py:for="i,mirror in enumerate(mirrors)" class="${i%2 and 'odd' or 'even'}">
			<td>
				${i+1}
			</td>
			<td>
				${mirror.hostname}
			</td>
			<td>
				${mirror.comment}
			</td>			
			<td>
				${mirror.active}
			</td>			
			<td>
				${mirror.user_active}
			</td>			
			<td>
				${mirror.admin_active}
			</td>			
			<td>
				${mirror.uptime_percentage}
			</td>			
			<td>
				${mirror.minimum_uptime_percentage}
			</td>			
			<td>
				${mirror.private}
			</td>			
			<td>
				<ul>
					<li py:for="mirror_release in mirror.mirror_releases">
						${mirror_release.release.name}
					</li>
				</ul>
			</td>
			<td>
				<ul>
					<li py:for="protocol in mirror.protocols">
						${protocol.name}
					</li>
				</ul>
			</td>
			<td>
				<a href="${tg.url('/mirror/viewMirror', hostname=mirror.hostname)}">
					V
				</a>
			</td>
		</tr>
	</table>
	<div class="links">
		<ul>
			<li> 
				<a href="${tg.url('/mirror/newMirror')}"> New Mirror </a>
			</li>
		</ul>
	</div>

</body>
</html>
