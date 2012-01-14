<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<?python import sitetemplate ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="sitetemplate">
  <head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>MirrorManager</title>
    <link rel="stylesheet" type="text/css" media="all"
    py:attrs="{'href': tg.config('mirrormanager.cssroot', '/mirrormanager/static/css/') + 'fedora.css'}"/>
    <link rel="stylesheet" type="text/css" media="all"
    py:attrs="{'href': tg.config('mirrormanager.cssroot', '/mirrormanager/static/css/') + 'main.css'}"/>
    <link rel="stylesheet" type="text/css" media="all"
    py:attrs="{'href': tg.config('mirrormanager.cssroot', '/mirrormanager/static/css/') + 'style.css'}"/>
    <!--[if lt IE 7]>
    <style type="text/css">
      #wrapper
      {
      height: 100%;
      }
    </style>
    <![endif]-->
    <script type="text/javascript">
      if (typeof(fedora) == 'undefined') {
        fedora = {};
      }
      fedora.identity = {anonymous: true};
      /* Remove token and trailing slash */
      fedora.baseurl = "${tg.url('/')}".replace(/\/?(\?[^?]+)?$/, '');
    </script>
    <script type="text/javascript" py:if="not tg.identity.anonymous">
      fedora.identity = {
        token: "${tg.identity.csrf_token}",
        anonymous: false
      };
    </script>
</head>
  <body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">
  <div id="wrapper">
    <div id="head">
      <h1><a py:attrs="{'title' : tg.config('mirrormanager.projectname', 'Fedora') + _(' Project homepage'),
                        'href' : tg.config('mirrormanager.projectweb', 'http://fedoraproject.org')}">
           ${tg.config('mirrormanager.projectname','Fedora')}</a>
      </h1>
    </div>
    <div id="wrapper2">
      <div id="sidebar">
        <div id="nav">
          <h2>Navigation</h2>
          <ul>
            <li><a href="${tg.url('/')}" py:attrs="{'title': _('Mirror Manager main page')}">Main</a></li>
            <li><a href="${tg.url('/adminview')}" py:attrs="{'title': _('Mirror Manager Admin View')}">Admin View</a></li>
            <li><a href="${tg.url('/help')}" py:attrs="{'title': _('Mirror Manager Help')}">Help</a></li>
          </ul>
          <h2>${tg.config('mirrormanager.projectname','Fedora')} websites</h2>
          <ul>
            <li><a href="http://fedoraproject.org/" py:attrs="{'title': _('Fedora Project homepage')}">Fedora Home</a></li>
            <li><a href="http://docs.fedoraproject.org/" py:attrs="{'title': _('Fedora documentation')}">Docs</a>
              <span class="navnote">Fedora documentation</span></li>
              <li><a href="http://fedoraproject.org/wiki/" py:attrs="{'title': _('Collaborative knowledge')}">Wiki</a>
              <span class="navnote">Collaborative knowledge</span></li>
              <li><a href="http://planet.fedoraproject.org/" py:attrs="{'title': _('The voices of the community')}">Planet</a>
              <span class="navnote">The voices of the community</span></li>
              <li><a href="http://fedorapeople.org/" py:attrs="{'title': _('Community webpages')}">People</a>
              <span class="navnote">Community webpages</span></li>
          </ul>
          <div py:if="tg.config('identity.on')" id="pageLogin">
            <span py:if="tg.identity.anonymous">
            <h2>Login</h2>
            <a href="${tg.url('/login')}">Login</a>
            </span>
            <span py:if="not tg.identity.anonymous">
              <h2>Logged in</h2>
              Welcome ${tg.identity.user_name}.
              <ul><li><a href="${tg.url('/logout')}">Logout</a></li></ul>
            </span>
          </div>
        </div>
      </div>
      <div id="content">
          <div py:if="tg_flash" class="notice">
            <div py:if="not tg_flash.startswith('Error:')" py:replace="tg_flash" />
            <div py:if="tg_flash.startswith('Error:')" py:content="tg_flash" class="error_flash"></div>
          </div>
        <div py:replace="[item.text]+item[:]"/>
      </div>
    </div>
    <div id="bottom">
      <div py:if="tg.config('mirrormanager.copyright', 'fedora') == 'fedora'" id="footer">
        <p class="copy">Copyright &copy; 2007 Red Hat, Inc. and others.  All Rights Reserved.
        Please send any comments or corrections to the <a href="mailto:webmaster@fedoraproject.org">websites team</a>.
        </p>
        <p class="disclaimer">
        The Fedora Project is maintained and driven by the community and sponsored by Red Hat.  This is a community maintained site.  Red Hat is not responsible for content.
        </p>
        <ul>
          <li class="first"><a href="http://fedoraproject.org/wiki/Legal">Legal</a></li>
          <li><a href="http://fedoraproject.org/wiki/Legal/TrademarkGuidelines">Trademark Guidelines</a></li>
        </ul>
      </div>
      <div py:if="tg.config('mirrormanager.copyright', 'fedora') != 'fedora'" id="footer">
        Some other copyright???
      </div>
    </div>
  </div>
</body>
</html>
