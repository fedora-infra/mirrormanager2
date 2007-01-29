<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
</head>
<body>
${form(value=values, action=action)}
<h2>Host Data</h2>
To edit this data, you must run report_mirror on the actual host.
These may be blank for any host that hasn't checked in yet.
<P>
<UL>
<LI>Country: ${values.country}</LI>
<LI>Last Checked In: ${values.timestamp}</LI>
<LI>Robot Email: ${values.robot_email}</LI>
<LI>Private: ${values.private}</LI>
<?python import pprint
   pp = pprint.PrettyPrinter(indent=4)
   config = pp.pformat(values.config) ?>

<LI>Config: ${config}</LI>
</UL>
</P>
</body>
</html>
