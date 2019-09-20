# Copyright (c) 2008,2013 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

from __future__ import print_function
from functools import total_ordering

import random
import bisect


@total_ordering
class WeightedListItem:
    def __init__(self, weight, data, start=0):
        self.data = data
        self.start = start
        self.weight = weight

        if type(weight) != int:
            self.weight = 1
        elif weight < 1:
            self.weight = 1

    def __contains__(self, val):
        return (val >= self.start and val < (self.start + self.weight))

    def __eq__(self, other):
        if other.start in self:
            return false
        return (self.start == other.start)

    def __ne__(self, other):
        return not (self.start == other.start)

    def __lt__(self, other):
        if other.start in self:
            return False
        return ((self.start, self.weight) < (other.start, other.weight))

    def __repr__(self):
        return "(%s, %s)" % (self.start, self.weight)


class WeightedList(list):
    def _assign(self):
        start = 0
        for item in self.__iter__():
            item.start = start
            start += item.weight

    def _max(self):
        value = 0
        self._assign()
        len = self.__len__()
        if len > 0:
            item = self.__getitem__(len-1)
            value = item.start + item.weight
        return value

    def additem(self, weight, data):
        a = WeightedListItem(weight, data)
        list.append(self, a)

    def choose(self):
        length = self.__len__()
        if length == 0:
            return None
        if length == 1:
            return 0
        r = random.randrange(0, self._max())
        li = WeightedListItem(1, None, start=r)
        return bisect.bisect_left(self, li)


def weighted_shuffle(l):
    """
    prerequisite: invoke random.seed() before calling this function.
    input: a list, whose items are a tuple (weight, data)
           where weight is an int, and data can be anything
    output: a list of these tuples after being shuffled based on the weight
    """
    wl = WeightedList()
    for (weight, data) in l:
        wl.additem(weight, data)

    returnlist = []
    while len(wl) > 0:
        a = wl.choose()
        if a is not None:
            item = wl[a]
            returnlist.append((item.weight, item.data))
            del wl[a]
    return returnlist


def unit_test():
    random.seed()
    while 1:
        l = [(1000, 1), (1000, 2), (100, 3), (100, 4), (10, 5), (10, 6), (10, 7), (10, 8)]
        newlist = weighted_shuffle(l)
        print(newlist)
