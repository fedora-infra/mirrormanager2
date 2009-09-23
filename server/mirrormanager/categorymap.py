# Some Categories only exist for certain Product-Version combinations.
# e.g. Fedora Extras doesn't exist for Fedora <= 3.
# and Fedora Core and Fedora Extras don't exist for Fedora >= 7.

import mirrormanager.model
from math import ceil
import sys

def categorymap(productname, vername):
    categories = []
    categoriesToDrop = set()

    if productname is None: # want all categories
        return [c.name for c in mirrormanager.model.Category.select()]

    vernum = sys.maxint
    if vername is not None:
        try:
            if u'development' in vername:
                vernum = sys.maxint
            elif '.' in vername:
                vernum = int(ceil(float(vername)))
            else:
                vernum = int(vername)
        except:
            pass

    try:
        product = mirrormanager.model.Product.byName(productname)
        categories = [c.name for c in product.categories]
    except:
        # given an unknown product name, therefore no categories
        return []

    if productname == u'Fedora' and vername is not None:
        if vernum < 3:
            categoriesToDrop.add(u'Fedora Extras')
        if vernum > 6:
            c = (u'Fedora Core', u'Fedora Extras')
            for e in c:
                categoriesToDrop.add(e)
                
    for c in categoriesToDrop:
        try:
            categories.remove(c)
        except KeyError:
            pass

    return categories
