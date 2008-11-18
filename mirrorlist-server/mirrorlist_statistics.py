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

def optimize_mirror_name(mirror):
	result = True

	if mirror == 'fedora.redhat.com':
		mirror = 'fedora'
	elif mirror.startswith('..'):
		mirror = 'undef'
	elif mirror.startswith('glib2'):
		mirror = 'undef'
	elif mirror.startswith('?C'):
		mirror = 'undef'
	elif mirror.startswith('rpmfusion'):
		mirror = 'rpmfusion.org'
	elif mirror == 'archive.download.redhat.com':
		mirror = 'redhat archive'
	elif mirror == 'sources.redhat.com':
		mirror = 'sourceware.org'
	elif mirror == 'sources':
		mirror = 'sourceware.org'
	elif mirror == 'Mandrake':
		mirror = 'mandriva'
	elif mirror == 'mandrake':
		mirror = 'mandriva'
	elif mirror == 'openbsd':
		mirror = 'OpenBSD'
	elif mirror == '':
		mirror = 'undef'
	elif mirror == 'Mandrake-devel':
		mirror = 'undef'
	elif mirror == 'MISSING-FILES':
		mirror = 'undef'
	elif mirror == '?C=S':
		mirror = 'undef'
	elif mirror == '?C=N;O=D':
		mirror = 'undef'
	elif mirror == 'rlo':
		mirror = 'livna'
	elif mirror == '?C=D;O=A':
		mirror = 'undef'
	elif mirror == '?C=S;O=A':
		mirror = 'undef'
	elif mirror == '?C=N;O=A':
		mirror = 'undef'
	elif mirror == 'asp-linux':
		mirror = 'undef'
	elif mirror == 'Mandrakelinux':
		mirror = 'undef'
	elif mirror == 'Mirrors':
		mirror = 'undef'
	elif mirror == 'kernel':
		mirror = 'kernel.org'
	elif mirror == 'debian-cd':
		mirror = 'debian'
	elif mirror == 'linux-kernel':
		mirror = 'kernel.org'
	elif mirror == 'adobe':
		mirror = 'undef'
	elif mirror == 'eclipse.old':
		mirror = 'undef'
	elif mirror == 'debian-cd':
		mirror = 'debian'
	elif mirror == '?C=D;O=D':
		mirror = 'undef'
	elif mirror == '?C=S;O=D':
		mirror = 'undef'
	elif mirror == 'knoppix-dvd':
		mirror = 'knoppix'
	elif mirror == 'ubuntu.releases':
		mirror = 'ubuntu'
	elif mirror == 'gentoo-portage':
		mirror = 'gentoo'
	elif mirror == 'freshrpms':
		mirror = 'freshrpms.net'
	elif mirror == 'ooodev':
		mirror = 'openoffice'
	elif mirror == 'internal-gopher-menu':
		mirror = 'undef'
	elif mirror == '?C=M;O=D':
		mirror = 'undef'
	elif mirror == '?C=M;O=A':
		mirror = 'undef'
	else:
		result = False

	return mirror, result

start = time.clock()

y1, m1, d1, x1, x2, x3, x4, x5, x6 = time.localtime()

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
#dest = './'

shortcuts =   [ '/debian', '/dag', '/pub/fedora', '/pub/OpenBSD', '/debian-cd', '/ubuntu', '/atrpms', '/debian-security', '/pub/linux', '/pub/CPAN', '/pub/suse', '/pub/epel', '/info', '/pub/.3/fedora.redhat.com', '/pub/Mirrors/Mandrakelinux', '/Mirrors/Mandrivalinux', '/Mirrors/Mandrakelinux', '/pub/Mirrors/Mandrivalinux', '/pub/.3/ftp.kernel.org', '/pub/.2/Mandrakelinux', '/pub/Mirrors/sources.redhat.com', '/pub/.3/ubuntu', '/pub/.3/atrpms', '/pub/.5/gentoo', '/pub/freshrpms', '/pub/fedora-secondary', '/pub/Mirrors/fedora-secondary']
mirrornames = [ 'debian' , 'dag' , 'fedora'     , 'OpenBSD'     , 'debian'    , 'ubuntu' , 'atrpms' , 'debian'          , 'kernel.org', 'CPAN'     , 'suse'     , 'epel'     , 'info' , 'fedora'                   , 'mandriva'                  , 'mandriva'              , 'mandriva'              , 'mandriva'                  , 'kernel.org'            , 'mandriva'             , 'sourceware.org'                 , 'ubuntu'        , 'atrpms'        , 'gentoo'        , 'freshrpms.net', 'fedora-secondary',       'fedora-secondary']

#rsync
i = 0
rsync = {}

for line in open('/var/log/messages'):
    parts = line.split()
    month = parts[0]
    day  = parts[1]
    daemonstring = parts[4]    
    
    if daemonstring.find('rsync') == 0:
        pid = int(daemonstring[7:-2])
        rest = ''.join(line.split(':')[3:]).strip()
        
        if rest.startswith('rsync on'):
            mirror = rest.split()[2].split('/')[0]

            mirror, result = optimize_mirror_name(mirror)
            
            rsync[pid] = mirror
        elif rest.startswith('sent'):
            if int(day) == d1: # log is being rotated so it is unlikely we match the wrong month -
                          # checking the month would be a pain as it is a string, so as it is not
                          # strictly necessary we'll just skip that
                size = int(rest.split()[1])
                if size > 0:
                    try:
                        mirror = rsync[pid]
                        mirror, result = optimize_mirror_name(mirror)
                        #rsync[pid] = (mirror, size)
                        rsync_real_sum += size
                        rsync_all_requests += 1
            
                        try:
                            real_mirrors[mirror] += size
                            mirrors[mirror] += size  # doesn't make that much sense,
                                                     # but we'll assume what we sent has also been requested 
                            requests[mirror] += 1
                        except:
                            real_mirrors[mirror] = size
                            mirrors[mirror] = size  # doesn't make that much sense,
                                                    # but we'll assume what we sent has also been requested 
                            requests[mirror] = 1

                    except:
                        pass

# FTP
for line in open('/var/log/xferlog'):
    arguments = line.split()

    month = arguments[1]
    day = arguments[2]
    year = arguments[4]
    y, m, d, h, min, s, a, b ,c  = time.strptime(day+"/"+month+"/"+year, '%d/%b/%Y')

    # only look at entries from today
    if (y != y1) or (m != m1) or (d != d1):
        continue
    
    isMirror = False
    url = arguments[8]
    mirror = 'undef'

    for i in xrange(0, len(shortcuts)):
        if url.startswith(shortcuts[i]):
            isMirror = True
            mirror = mirrornames[i]

    if not isMirror:
        mirrorspos = url.find('/Mirrors')

        if mirrorspos < 0:
            mirrorspos = url.find('/pub/.1')
            if mirrorspos >= 0:
                mirrorspos = 4
        
        if mirrorspos < 0:
            mirrorspos = url.find('/pub/.2')
            if mirrorspos >= 0:
                mirrorspos = 4
        
        if mirrorspos < 0:
            mirrorspos = url.find('/pub/.3')
            if mirrorspos >= 0:
                mirrorspos = 4
        
        if mirrorspos < 0:
            mirrorspos = url.find('/pub/.4')
            if mirrorspos >= 0:
                mirrorspos = 4
        
        if mirrorspos < 0:
            mirrorspos = url.find('/pub/.5')
            if mirrorspos >= 0:
                mirrorspos = 4
        
        if mirrorspos < 0:
            mirrorspos = url.find('/pub/.6')
            if mirrorspos >= 0:
                mirrorspos = 4
        
        if mirrorspos >= 0:
            isMirror = True
            try:
                mirror = url[mirrorspos:].split('/')[2]
                
                mirror, result = optimize_mirror_name(mirror)

                if not result:
                    mirrorparts = mirror.split('.')
                    
                    if len(mirrorparts) > 2:
                        if len(mirrorparts[1]) > 2:
                            mirror = mirrorparts[1]
            
                mirror, result = optimize_mirror_name(mirror)

            except:
                continue

    try:
        size = int(arguments[7])
        transmitted = int(arguments[7])
        ftp_sum += size
        ftp_real_sum += transmitted
        ftp_all_requests += 1

        try:
            mirrors[mirror] += size
            real_mirrors[mirror] += transmitted
            requests[mirror] += 1
        except:
            mirrors[mirror] = size
            real_mirrors[mirror] = transmitted
            requests[mirror] = 1

    except:
        pass

# HTTP
for line in open('/var/log/httpd/ftp_access_log'):
    arguments = line.split()
    date = arguments[3]
    y, m, d, h, min, s, a, b ,c  = time.strptime(date[1:12], '%d/%b/%Y')

    # only look at entries from today
    if (y != y1) or (m != m1) or (d != d1):
        continue

    code = arguments[8]

    if code == '404':
        continue

    isMirror = False
    url = arguments[6]
    mirror = 'undef'
    
    for i in xrange(0, len(shortcuts)):
        if url.startswith(shortcuts[i]):
            isMirror = True
            mirror = mirrornames[i]
    
    if not isMirror:
        mirrorspos = url.find('/Mirrors')
        
        if mirrorspos >= 0:
            isMirror = True
            try:
                mirror = url[mirrorspos:].split('/')[2]
                
                mirror, result = optimize_mirror_name(mirror)

                if not result:
                    mirrorparts = mirror.split('.')
                    
                    if len(mirrorparts) > 2:
                        if len(mirrorparts[1]) > 2:
                            mirror = mirrorparts[1]

                mirror, result = optimize_mirror_name(mirror)

            except:
                continue


    try:
        size = int(arguments[9])
        transmitted = int(arguments[12])
        http_sum += size
        http_real_sum += transmitted
        http_all_requests += 1

        try:
            mirrors[mirror] += size
            real_mirrors[mirror] += transmitted
            requests[mirror] += 1
        except:
            mirrors[mirror] = size
            real_mirrors[mirror] = transmitted
            requests[mirror] = 1

    except:
        pass

# kernel.org
mirror = 'kernel.org'
for line in open('/var/log/httpd/kernel_access_log'):
	arguments = line.split()
	date = arguments[3]
	y, m, d, h, min, s, a, b ,c  = time.strptime(date[1:12], '%d/%b/%Y')

	# only look at entries from today
	if (y != y1) or (m != m1) or (d != d1):
		continue

	code = arguments[8]

	if code == '404':
		continue

	try:
		size = int(arguments[9])
		transmitted = int(arguments[12])
		http_sum += size
		http_real_sum += transmitted
		http_all_requests += 1

		try:
			mirrors[mirror] += size
			real_mirrors[mirror] += transmitted
			requests[mirror] += 1
		except:
			mirrors[mirror] = size
			real_mirrors[mirror] = transmitted
			requests[mirror] = 1

	except:
		pass
    
sum = ftp_sum + http_sum + rsync_real_sum
real_sum = ftp_real_sum + http_real_sum + rsync_real_sum
all_requests = ftp_all_requests + http_all_requests + rsync_all_requests

pylab.figure(1, figsize=(8,8))
ax =  pylab.axes([0.1, 0.1, 0.8, 0.8])

labels = []
fracs = []
rest = 0

for mirror in real_mirrors.keys():
	frac = real_mirrors[mirror]

	if (float(frac)/float(real_sum) > 0.01):
		labels.append(mirror)
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
