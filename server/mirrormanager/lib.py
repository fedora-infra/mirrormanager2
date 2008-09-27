import types

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
