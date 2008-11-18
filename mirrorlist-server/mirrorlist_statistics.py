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
mirrors = {}
real_mirrors = {}
requests = {}
i = 0
http_sum = 0
http_real_sum = 0
http_all_requests = 0
ftp_sum = 0
ftp_real_sum = 0
ftp_all_requests = 0
rsync_real_sum = 0
rsync_all_requests = 0

dest = '/ftp/info/breakdown/'
dest = './'

# HTTP
for line in open('2'):
	arguments = line.split()
	try:
		countries[arguments[5][:2]] += 1
	except:
		countries[arguments[5][:2]] = 1
	accesses += 1
	continue

print sort_dict(countries)


pylab.figure(1, figsize=(8,8))
ax =  pylab.axes([0.1, 0.1, 0.8, 0.8])

labels = []
fracs = []
rest = 0

for country in countries.keys():
	frac = countries[country]

	if (float(frac)/float(accesses) > 0.01):
		labels.append(country)
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
#title = 'ftp-stud.hs-esslingen.de - mirror traffic (%d-%02d-%02d)' % (y1, m1, d1)
#pylab.title(title, bbox={'facecolor':'0.8', 'pad':5})
pylab.savefig('%s%d-%02d-%02d.png' % (dest, y1, m1, d1))

sys.exit(0)

html = open('%s%d-%02d-%02d.txt' % (dest, y1, m1, d1), 'w')
html.write('<img src="/info/breakdown/%d-%02d-%02d.png" border="0" alt="alt"/>\n' % (y1, m1, d1))
html.write('<h2>Details</h2>\n')
html.write('<table align="center" width="80%">\n')
html.write('<tr><th class="statusth">Mirror Name</th><th class="statusth">%</th>')
html.write('<th class="statusth">Data Transmitted</th><th class="statusth">Data Requested</th>\n')
html.write('<th class="statusth">#Requests</th></tr>\n')

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

toggle = False

for item in sort_dict(real_mirrors):
	size = item[0]
	toggle = background(html, 'grey', toggle)
	html.write('<td>%s</td>\n' % (item[1]))
	html.write('\t<td align="right">%05.4lf %%</td>\n' % ((float(size)/float(real_sum))*100))
	html.write('\t<td align="right">\n')
	write_size(html, size)
	html.write('</td><td align="right">\n')
	write_size(html, mirrors[item[1]])
	html.write('</td><td align="right">')
	html.write('%d' % (requests[item[1]]))
	html.write('</td></tr>\n')

# RSYNC only
background(html, 'rsync', True)
html.write('<td>RSYNC</td><td></td><td align="right">\n');
write_size(html, rsync_real_sum)
html.write('</td><td align="right">\n');
write_size(html, rsync_real_sum)
html.write('</td><td align="right">%d' % (rsync_all_requests))
html.write('</td></tr>\n');

# FTP only
background(html, 'ftp', True)
html.write('<td>FTP</td><td></td><td align="right">\n');
write_size(html, ftp_real_sum)
html.write('</td><td align="right">\n');
write_size(html, ftp_sum)
html.write('</td><td align="right">%d' % (ftp_all_requests))
html.write('</td></tr>\n');

# HTTP only
background(html, 'http', True)
html.write('<td>HTTP</td><td></td><td align="right">\n');
write_size(html, http_real_sum)
html.write('</td><td align="right">\n');
write_size(html, http_sum)
html.write('</td><td align="right">%d' % (http_all_requests))
html.write('</td></tr>\n');

# print the overall information
background(html, 'total', True)
html.write('<td>Total</td><td></td><td align="right">\n');
write_size(html, real_sum)
html.write('</td><td align="right">\n');
write_size(html, sum)
html.write('</td><td align="right">%d' % (all_requests))
html.write('</td></tr>\n');

html.write('</table>\n')
end = time.clock()
html.write('<p>Last updated: %s GMT' % time.strftime("%a, %d %b %Y %H:%M:%S",time.gmtime()))
html.write(' (runtime %ss)</p>\n' % (end-start))
