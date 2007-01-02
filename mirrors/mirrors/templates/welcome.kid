<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Welcome to Fedora Mirrors</title>
</head>
<body>
<div id="main_content">
  <div id="getting_started">
    <ul id="getting_started_steps">
      <li class="getting_started">
        <h3>Mirrors</h3>
        <ul>
        	<li>
        		<a href="${tg.url('/mirror/myMirrors')}"> My Mirrors </a>
        	</li>
        	<li>
        		<a href="${tg.url('/mirror/newMirror')}"> Add New Mirror </a>
        	</li>
        </ul>
      </li>
      
      <li class="getting_started" py:if="'admin' in tg.identity.groups">
        <h3>Releases</h3>
        <ul>
        	<li>
        		<a href="${tg.url('/release/listReleases')}"> List Releases </a>
        	</li>
        	<li>
        		<a href="${tg.url('/release/newRelease')}"> Add New Release </a>
        	</li>
        </ul>
      </li>
      <li class="getting_started" py:if="'admin' in tg.identity.groups">
        <h3>Architectures</h3>
        <ul>
        	<li>
        		<a href="${tg.url('/arch/listArchs')}"> List Archs </a>
        	</li>
        	<li>
        		<a href="${tg.url('/arch/newArch')}"> Add New Arch </a>
        	</li>
        </ul>
	</li>
	</ul>
  </div>
  <!-- End of getting_started -->
</div>
</body>
</html>
