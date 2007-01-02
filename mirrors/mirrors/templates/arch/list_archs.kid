<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>List Archs</title>
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
					Comment
				</th>
				<th>
					Edit
				</th>
				<th>
					Delete
				</th>
			</tr>		
		</thead>
		<tr py:for="i,arch in enumerate(archs)" class="${i%2 and 'odd' or 'even'}">
			<td>
				${i+1}
			</td>
			<td>
				${arch.name}
			</td>
			<td>
				${arch.comment}
			</td>
			<td>
				<a href="${tg.url('/arch/editArch', arch_name=arch.name)}">
					E
				</a>
			</td>
			<td>
				<a href="${tg.url('/arch/deleteArch', arch_name=arch.name)}" class="delete_link">
					D
				</a>
			</td>
		</tr>
	</table>
	<div class="links">
		<ul>
			<li> 
				<a href="${tg.url('/arch/newArch')}"> New Arch</a>
			</li>
			<li> 
				<a href="${tg.url('/release/listReleases')}"> List Releases </a>
			</li>
		</ul>
		
	</div>

</body>
</html>
