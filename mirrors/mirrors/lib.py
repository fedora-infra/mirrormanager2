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