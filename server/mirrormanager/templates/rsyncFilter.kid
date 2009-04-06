<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<body>
# rsync --include-from=(this file)
# includes
<div py:for="i in includes">+ <span py:replace="i">pattern</span>
</div>
# excludes
<div py:for="e in excludes">- <span py:replace="e">pattern</span>
</div>
# end of list
</body>
</html>
