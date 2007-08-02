<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<?python import sitetemplate ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="sitetemplate">
  <head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <title py:replace="''">Your title goes here</title>
    <link rel="stylesheet" type="text/css" media="all" href="http://fedoraproject.org/style.css" />
    <!--[if lt IE 7]>
    <style type="text/css">
      #wrapper
      {
      height: 100%;
      }
    </style>
    <![endif]-->
    <style type="text/css">
      table
      {
        font-size: 1.4ex;
      }

      ol, ul {
        padding-left: 3ex;
      }

      table.mirrors
      {
        margin: 1ex 0;
        width: 98%
      }

      #content
      {
        margin-left: 2ex!important;
      }

      th, td
      {
        width: 10ex;
      }
    </style>
  </head>
  <body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">
    <div id="wrapper">
      <div id="head">
        <h1><a href="http://fedoraproject.org/index.html">Fedora</a></h1>
      </div>
      <div id="content">
        <div id="menu">
          <div id="welcome"></div>
          <div id="menu_links"></div>
        </div>
        <div py:replace="[item.text]+item[:]"/>
      </div>
    </div>
    <div id="bottom">
      <div id="footer">
        <p class="copy">
        Copyright &copy; 2007 Red Hat, Inc. and others.  All Rights Reserved.
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
    </div>
  </body>
</html>
