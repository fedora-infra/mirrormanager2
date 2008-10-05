<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<?python import sitetemplate ?>
<?python from turbogears import config ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="sitetemplate">
  <head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title py:replace="''">Your title goes here</title>
    <link rel="stylesheet" type="text/css" media="all"
       py:attrs="href=config.get('mirrormanager.cssroot', '/mirrormanager/static/css/') + 'fedora.css'"/>
    <link rel="stylesheet" type="text/css" media="all"
       py:attrs="href=config.get('mirrormanager.cssroot', '/mirrormanager/static/css/') + 'main.css'"/>
    <link rel="stylesheet" type="text/css" media="all"
       py:attrs="href=config.get('mirrormanager.cssroot', '/mirrormanager/static/css/') + 'style.css'"/>
    <!--[if lt IE 7]>
    <style type="text/css">
      #wrapper
      {
      height: 100%;
      }
    </style>
    <![endif]-->
  </head>
  <body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">
    <div id="wrapper">
    <div id="head">
      <h1><a href="http://fedoraproject.org/" py:attrs="title=_('Fedora Project homepage')">Fedora</a></h1>
    </div>
    <div id="wrapper2">
      <div id="sidebar">
        <div id="nav">
          <h2>Navigation</h2>
          <ul>
            <li><a href="/publiclist/" py:attrs="title=_('Public mirror list')">Public list</a></li>
          </ul>
          <h2>Fedora websites</h2>
          <ul>
            <li><a href="http://fedoraproject.org/" py:attrs="title=_('Fedora Project homepage')">Fedora Home</a></li>
            <li><a href="http://docs.fedoraproject.org/" py:attrs="title=_('Fedora documentation')">Docs</a>
              <span class="navnote">Fedora documentation</span></li>
            <li><a href="http://fedoraproject.org/wiki/" py:attrs="title=_('Collaborative knowledge')">Wiki</a>
              <span class="navnote">Collaborative knowledge</span></li>
            <li><a href="http://planet.fedoraproject.org/" py:attrs="title=_('The voices of the community')">Planet</a>
              <span class="navnote">The voices of the community</span></li>
            <li><a href="http://fedorapeople.org/" title="_('Community webpages')">People</a>
              <span class="navnote">Community webpages</span></li>
          </ul>
        </div>
      </div>
      <div id="content">
        <div py:replace="[item.text]+item[:]"/>
      </div>
    </div> <!-- wrapper2 -->

  </div>
</body>
</html>
