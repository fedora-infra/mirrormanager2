<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Edit Mirror ${mirror.hostname} Releases</title>
<script type="text/javascript">
	function toggleDisableRelease(id, force_disable)
	{
		nodeWalk(getElement("release_"+id), function (node)
												{
													if (node.tagName == "INPUT")
													{
														if ( !node.disabled || force_disable )
															node.disabled = true;
														else
															node.disabled = false;
													}
													
													return node.childNodes;
												});
	}	

</script>

</head>
<body>
<form action="updateMirrorReleases" method="post">
<input type="hidden" name="hostname" value="${mirror.hostname}" />

<div class="head">
	Mirror Hostname: ${mirror.hostname}
</div>

<fieldset py:for="i,release in enumerate(releases)" >
<legend>Release ${release.name}</legend>

<div>
	<label for="has_release_${i}">Has Release:</label>
	<span><input id="has_release_${i}" name="has_release_${i}" type="checkbox" value="${release.name}" checked="${(None, '') [release_to_mirror_release.has_key(release)]}" /></span>
</div>

<div id="release_${i}">
	<div>
		<label for="release_path_${i}">Release Path: </label>
		<?python
	#use default path, if it's first time we don't have this release
	if release_to_mirror_release.has_key(release):
		value = release_to_mirror_release[release][0].release_path
	else:
		value = release.default_path
		?>
		<span><input id="release_path_${i}" name="release_path_${i}" value="${value}" /></span>
	</div>
	
	<div>
		Architectures:
		<ul py:for="j,arch in enumerate(release.archs)">
			<li>
				<label for="release_arch_${i}_${j}">${arch.name} </label> 
				<?python
checked = False
if release_to_mirror_release.has_key(release) and arch in release_to_mirror_release[release][1]:
	checked = True
				?>
				<span><input type="checkbox" id="release_arch_${i}_${j}" name="release_arch_${i}_${j}" value="${arch.name}" checked="${(None,'')[checked]}" /></span> 
			</li>
		</ul>
	</div>
	<script>
	if(${('true', 'false')[release_to_mirror_release.has_key(release)]})
		toggleDisableRelease(${i}, true);
	
	connect('has_release_${i}', 'onclick', function(event) {logDebug("Called");toggleDisableRelease(${i}); });
	</script>
	
</div>

</fieldset>

<div>
	<button style="left:-100px"> Update </button>
</div>
</form>

</body>
</html>
