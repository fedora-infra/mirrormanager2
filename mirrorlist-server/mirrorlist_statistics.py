#!/usr/bin/env python
#
# Copyright (C) 2008 by Alexander Koenig
# Copyright (C) 2008 by Adrian Reber
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, pylab, time

def sort_dict(dict):
    """ Sort dictionary by values and reverse. """
    items=dict.items()
    sorteditems=[[v[1],v[0]] for v in items ]
    sorteditems.sort()
    sorteditems.reverse()
    return sorteditems

start = time.clock()

y1, m1, d1, x1, x2, x3, x4, x5, x6 = time.localtime()

countries = {}
accesses = 0
repositories = {}
archs = {}
i = 0

dest = '/ftp/info/breakdown/'
dest = './'

# HTTP
for line in open(sys.argv[1]):
	arguments = line.split()
	try:
		countries[arguments[5][:2]] += 1
	except:
		countries[arguments[5][:2]] = 1
	try:
		archs[arguments[9]] += 1
	except:
		archs[arguments[9]] = 1
	try:
		repositories[arguments[7][:len(arguments[7])-1]] += 1
	except:
		repositories[arguments[7][:len(arguments[7])-1]] = 1
	accesses += 1
	continue

print sort_dict(countries)
print sort_dict(archs)
print sort_dict(repositories)


def do_pie(prefix, dict, accesses):
	pylab.figure(1, figsize=(8,8))
	ax =  pylab.axes([0.1, 0.1, 0.8, 0.8])

	labels = []
	fracs = []
	rest = 0

	for item in dict.keys():
		frac = dict[item]

		if (float(frac)/float(accesses) > 0.01):
			labels.append(item)
			fracs.append(frac)
		else:
			rest += frac

	i = 0
	changed = False
	for x in labels:
		if x == 'undef':
			fracs[i] += rest
			labels[i] = 'other'
			changed = True
		i += 1

	if changed == False:
		labels.append('other')
		fracs.append(rest)

	pylab.pie(fracs, labels=labels, autopct='%1.1f%%', pctdistance=0.75, shadow=True)
	pylab.savefig('%s%s-%d-%02d-%02d.png' % (dest, prefix, y1, m1, d1))
	pylab.close(1)


def write_size(html, size):
	if size/1024 <= 0:
		html.write('%.2f Bytes'  % (size))
	elif size/1024/1024 <= 0:
		html.write('%.2f KB'  % (size/1024.00))
	elif size/1024/1024/1024 <= 0:
		html.write('%.2f MB'  % (size/1024.00/1024.00))
	elif size/1024/1024/1024/1024 <= 0:
		html.write('%.2f GB'  % (size/1024.00/1024.00/1024.00))
	else:
		html.write('%.2f TB'  % (size/1024.00/1024.00/1024.00/1024.00))

def background(html, css_class, toggle):
	html.write('\t<tr')
	if toggle:
		html.write(' class="%s"' % css_class)
		toggle = False
	else:
		toggle = True
	html.write('>\n\t')
	return toggle

def do_html(prefix, dict, accesses):
	html = open('%s%s-%d-%02d-%02d.txt' % (dest, prefix, y1, m1, d1), 'w')
	html.write('<img src="%s-%d-%02d-%02d.png" border="0" alt="alt"/>\n' % (prefix, y1, m1, d1))
	html.write('<h2>Details</h2>\n')
	html.write('<table align="center" width="80%">\n')
	html.write('<tr><th class="statusth">Mirror Name</th><th class="statusth">%</th>')
	html.write('<th class="statusth">#Requests</th></tr>\n')

	toggle = False

	for item in sort_dict(dict):
		size = item[0]
		toggle = background(html, 'grey', toggle)
		html.write('<td>%s</td>\n' % (item[1]))
		html.write('\t<td align="right">%05.4lf %%</td>\n' % ((float(size)/float(accesses))*100))
		html.write('<td align="right">')
		html.write('%d' % (size))
		html.write('</td></tr>\n')

	# print the overall information
	background(html, 'total', True)
	html.write('<td>Total</td><td></td><td>\n');
	html.write('</td><td align="right">%d' % (accesses))
	html.write('</td></tr>\n');

	html.write('</table>\n')
	end = time.clock()
	html.write('<p>Last updated: %s GMT' % time.strftime("%a, %d %b %Y %H:%M:%S",time.gmtime()))
	html.write(' (runtime %ss)</p>\n' % (end-start))

do_pie('countries', countries, accesses)
do_pie('archs', archs, accesses)
do_pie('repositories', repositories, accesses)

do_html('countries', countries, accesses)
do_html('archs', archs, accesses)
do_html('repositories', repositories, accesses)
