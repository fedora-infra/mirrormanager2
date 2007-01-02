<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>List Releases</title>
</head>
<body>
	<table class="list">
		<thead>
			<tr>
				<th>
					Row
				</th>
				<th>
					Name
				</th>
				<th>
					Canonical URL
				</th>
				<th>
					Default Path
				</th>
				<th>
					Comment
				</th>
				<th>
					Architectures
				</th>
				<th>
					Update Architectures
				</th>
				<th>
					Edit
				</th>
				<th>
					Delete
				</th>
			</tr>		
		</thead>
		<tr py:for="i,release in enumerate(releases)" class="${i%2 and 'odd' or 'even'}">
			<td>
				${i+1}
			</td>
			<td>
				${release.name}
			</td>
			<td>
				${release.canonical}
			</td>			
			<td>
				${release.default_path}
			</td>
			<td>
				${release.comment}
			</td>
			<td>
				<ul>
					<li py:for="arch in release.archs">
						${arch.name}
					</li>
				</ul>
			</td>
			<td>
				<a href="${tg.url('/release/editReleaseArchs', release_name=release.name)}">
					U
				</a>
			</td>
			<td>
				<a href="${tg.url('/release/editRelease', release_name=release.name)}">
					E
				</a>
			</td>
			<td>
				<a href="${tg.url('/release/deleteRelease', release_name=release.name)}" class="delete_link">
					D
				</a>
			</td>
		</tr>
	</table>
	<div class="links">
		<ul>
			<li> 
				<a href="${tg.url('/release/newRelease')}"> New Release </a>
			</li>
			<li> 
				<a href="${tg.url('/arch/listArchs')}"> List Architectures </a>
			</li>
		</ul>
	</div>

</body>
</html>
