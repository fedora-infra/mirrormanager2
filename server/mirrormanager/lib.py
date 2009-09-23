import types, os, sys

def createErrorString(tg_errors):
    """
        Creates and returns an string representation of tg_errors
        tg_errors(list): List of turbogears generated errors
    """
    errors = []
    if type(tg_errors) == types.DictType:

        for param, inv in tg_errors.items():
            if type(inv) == types.StringType:
                errors.append("%s: %s"%(param, inv))
            else:
                errors.append("%s(%s): %s"%(param, inv.value, inv.msg))
    else:
        errors.append(tg_errors)
    
    return "Error:" + ", ".join(errors)

def uniqueify(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def remove_pidfile(pidfile):
    os.unlink(pidfile)

def write_pidfile(pidfile, pid):
    try:
        f = open(pidfile, 'w')
    except:
        return 1
    f.write(str(pid))
    f.close()
    return 0

def manage_pidfile(pidfile):
    """returns 1 if another process is running that is named in pidfile,
    otherwise creates/writes pidfile and returns 0."""
    pid = os.getpid()
    try:
        f = open(pidfile, 'r')
    except IOError, err:
        if err.errno == 2: # No such file or directory
            return write_pidfile(pidfile, pid)
        return 1

    oldpid=f.read()
    f.close()

    # is the oldpid process still running?
    try:
        os.kill(int(oldpid), 0)
    except OSError, err:
        if err.errno == 3: # No such process
            return write_pidfile(pidfile, pid)
    return 1
