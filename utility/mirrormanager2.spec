%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           mirrormanager2
Version:        0.1.0
Release:        1%{?dist}
Summary:        Mirror management application

License:        MIT
URL:            http://fedorahosted.org/mirrormanager/
Source0:        https://fedorahosted.org/releases/m/i/mirrormanager/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  python-flask-admin
BuildRequires:  python-flask-xml-rpc
BuildRequires:  python-flask-wtf
BuildRequires:  python-wtforms
BuildRequires:  python-IPy < 0.80
BuildRequires:  python-dns
BuildRequires:  python-fedora >= 0.3.33
BuildRequires:  python-fedora-flask >= 0.3.33
BuildRequires:  python-setuptools
BuildRequires:  python-psutil
BuildRequires:  python-alembic
# Mirrorlist
BuildRequires:  python-GeoIP
BuildRequires:  py-radix
BuildRequires:  python-webob

BuildRequires:  systemd-devel

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
BuildRequires:  python-sqlalchemy0.7
%else
BuildRequires:  python-sqlalchemy >= 0.7
%endif

Requires:  python-flask
Requires:  python-flask-admin
Requires:  python-flask-xml-rpc
Requires:  python-flask-wtf
Requires:  python-wtforms
Requires:  python-fedora >= 0.3.33
Requires:  python-fedora-flask >= 0.3.33
Requires:  python-setuptools
Requires:  python-psutil
Requires:  python-alembic

Requires:  %{name}-lib == %{version}
Requires:  mod_wsgi

%description
MirrorManager keeps track of the public and private mirrors, that carry
Fedora, EPEL, and RHEL content. It is used by the Fedora infrastructure as
well as rpmfusion.org, a third-party repository.
It automatically selects the “best” mirror for a given user based on a set
of fallback heuristics (such as network, country or continent).


%package lib
Summary:        Library to interact with MirrorManager's database
Group:          Development/Tools
BuildArch:      noarch

Requires:  python-IPy < 0.80
Requires:  python-dns

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
Requires:  python-sqlalchemy0.7
%else
Requires:  python-sqlalchemy >= 0.7
%endif

%description lib
Library to interact with MirrorManager's database


%package mirrorlist
Summary:        MirrorList serving mirrors to yum/dnf
Group:          Development/Tools
BuildArch:      noarch

Requires:  python-GeoIP
Requires:  py-radix
Requires:  python-webob
Requires:  python-IPy
Requires:  systemd
Requires(pre):  shadow-utils

%description mirrorlist
Sub-part of mirrormanager serving mirrors to yum/dnf


%package crawler
Summary:        Crawler for MirrorManager
Group:          Development/Tools
BuildArch:      noarch

Requires:  %{name}-lib == %{version}
Requires(pre):  shadow-utils

%description crawler
Install the crawler for MirrorManager, crawling all the mirrors to find out
if they are up to date or not


%package backend
Summary:        Backend scripts for MirrorManager
Group:          Development/Tools
BuildArch:      noarch

Requires:  %{name}-lib == %{version}
Requires(pre):  shadow-utils

%description backend
Install a number of utility scripts to be used manually or in cron jobs to
run MirrorManager.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Create directories needed
# Apache configuration files
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
# MirrorManager configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/mirrormanager
# MirrorManager crawler log rotation
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d
# for .wsgi files mainly
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2
# Stores temp files (.sock & co)
mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/mirrormanager
# Results and homedir
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/lib/mirrormanager
# Lock files
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/lock/mirrormanager
# Stores lock and pid info
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/run/mirrormanager
# Log files
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/log/mirrormanager/crawler
# Stores the service file for systemd
mkdir -p $RPM_BUILD_ROOT/%{_unitdir}

# Install apache configuration file
install -m 644 mirrorlist/apache/mirrorlist-server.conf \
    $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/mirrorlist-server.conf
install -m 644 utility/mirrormanager.conf.sample \
    $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/mirrormanager.conf

# Install configuration file
install -m 644 utility/mirrormanager2.cfg.sample \
    $RPM_BUILD_ROOT/%{_sysconfdir}/mirrormanager/mirrormanager2.cfg

# Install crawler logrotate definition
install -m 644 utility/mm2_crawler.logrotate \
    $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/mm2_crawler

# Install umdl logrotate definition
install -m 644 utility/mm2_umdl.logrotate \
    $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/mm2_umdl

# Install WSGI file
install -m 644 utility/mirrormanager2.wsgi \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrormanager2.wsgi
install -m 644 mirrorlist/mirrorlist_client.wsgi \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrorlist_client.wsgi

# Install the mirrorlist server
install -m 644 mirrorlist/mirrorlist_server.py \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrorlist_server.py
install -m 644 mirrorlist/weighted_shuffle.py \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/weighted_shuffle.py

# Install the createdb script
install -m 644 createdb.py \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrormanager2_createdb.py

# Install the tmpfile creating the /run/mirrormanager folder upon reboot
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 0644 mirrorlist/systemd/mirrormanager_tempfile.conf \
    $RPM_BUILD_ROOT/%{_tmpfilesdir}/%{name}-mirrorlist.conf
install -m 0644 utility/backend_tempfile.conf \
    $RPM_BUILD_ROOT/%{_tmpfilesdir}/%{name}-backend.conf

# Install the systemd service file
install -m 644 mirrorlist/systemd/mirrorlist-server.service \
    $RPM_BUILD_ROOT/%{_unitdir}/mirrorlist-server.service

# Install the alembic files
cp -r alembic $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/
install -m 644 utility/alembic.ini $RPM_BUILD_ROOT/%{_sysconfdir}/mirrormanager/alembic.ini

# Install the zebra-dump-parser perl module
cp -r utility/zebra-dump-parser $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/

%pre mirrorlist
getent group mirrormanager >/dev/null || groupadd -r mirrormanager
getent passwd mirrormanager >/dev/null || \
    useradd -r -g mirrormanager -d %{_localstatedir}/lib/mirrormanager -s /sbin/nologin \
    -c "MirrorManager" mirrormanager
exit 0

%pre crawler
getent group mirrormanager >/dev/null || groupadd -r mirrormanager
getent passwd mirrormanager >/dev/null || \
    useradd -r -g mirrormanager -d %{_localstatedir}/lib/mirrormanager -s /sbin/nologin \
    -c "MirrorManager" mirrormanager
exit 0

%pre backend
getent group mirrormanager >/dev/null || groupadd -r mirrormanager
getent passwd mirrormanager >/dev/null || \
    useradd -r -g mirrormanager -d %{_localstatedir}/lib/mirrormanager -s /sbin/nologin \
    -c "MirrorManager" mirrormanager
exit 0

%check
# One day we will have unit-tests to run here

%files
%doc README.rst LICENSE-MIT-X11 doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/mirrormanager.conf
%config(noreplace) %{_sysconfdir}/mirrormanager/mirrormanager2.cfg

%dir %{_sysconfdir}/mirrormanager/
%dir %{python_sitelib}/%{name}/

%{_sysconfdir}/mirrormanager/alembic.ini

%{_datadir}/mirrormanager2/mirrormanager2.wsgi
%{_datadir}/mirrormanager2/mirrormanager2_createdb.py*
%{_datadir}/mirrormanager2/alembic/

%{python_sitelib}/%{name}/*.py*
%{python_sitelib}/%{name}/templates/
%{python_sitelib}/%{name}/static/
%{python_sitelib}/%{name}*.egg-info


%files lib
%{python_sitelib}/%{name}/lib/
%{python_sitelib}/%{name}/__init__.py*


%files mirrorlist
%config(noreplace) %{_sysconfdir}/httpd/conf.d/mirrorlist-server.conf
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/run/mirrormanager
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/lib/mirrormanager/
%{_tmpfilesdir}/%{name}-mirrorlist.conf
%{_unitdir}/mirrorlist-server.service
%{_datadir}/mirrormanager2/mirrorlist_client.wsgi
%{_datadir}/mirrormanager2/mirrorlist_server.py*
%{_datadir}/mirrormanager2/weighted_shuffle.py*


%files crawler
%config(noreplace) %{_sysconfdir}/logrotate.d/mm2_crawler
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/lib/mirrormanager
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/log/mirrormanager
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/log/mirrormanager/crawler
%{_bindir}/mm2_crawler


%files backend
%config(noreplace) %{_sysconfdir}/logrotate.d/mm2_umdl
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/lock/mirrormanager
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/lib/mirrormanager
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/log/mirrormanager
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/run/mirrormanager
%{_tmpfilesdir}/%{name}-backend.conf
%{_datadir}/mirrormanager2/zebra-dump-parser/
%{_bindir}/mm2_get_global_netblocks
%{_bindir}/mm2_get_internet2_netblocks
%{_bindir}/mm2_move-devel-to-release
%{_bindir}/mm2_move-to-archive
%{_bindir}/mm2_refresh_mirrorlist_cache
%{_bindir}/mm2_update-EC2-netblocks
%{_bindir}/mm2_update-master-directory-list
%{_bindir}/mm2_update-mirrorlist-server
%{_bindir}/mm2_create_install_repo


%changelog
* Thu May 07 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Update 0.1.0
- Add the possibilities to delete a site or a host
- Do not only create /var/lock/mirrormanager on installation (Adrian Reber)

* Tue May 05 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.10-1
- Update to 0.0.10
- Install the mm2_create_install_repo script
- Fix version handling on mm2_create_install_repo (Adrian Reber)
- Fix pickle generation when several repositories point to the same directory

* Mon May 04 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.9-1
- Update to 0.0.9
- Include and install alembic files
- Try explicit garbage collection in the crawler (Adrian Reber)
- Use defined timeout also for HTTP/FTP connections (Adrian Reber)
- Add documentation about the crawler (Adrian Reber)
- Also add a /var/run directory for the backend (Adrian Reber)
- Add fedmenu integration
- Add new utility script to be used to create the fedora-install-X repositories
- Added last-sync script as mm2_last-sync (Adrian Reber)

* Thu Apr 23 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.8-1
- Update to 0.0.8
- Make MM2 a little prettier on high-res display
- Add a Location tag for static (Patrick Uiterwijk)
- Fix the DB session issue on the crawler (Adrian Reber)
- Add some documentation on how MirrorManager works
- Decrease time required for set_not_up2date() (Adrien Reber)
- Add support to auto disable mirrors (Adrien Reber)
- Auto disable hosts which have a URL configured but which does not exist
  (Adrian Reber)
- crawl_duration is a host specific property (Adrian Reber)
- Handle lighttpd returing a content length for directories (Adrian Reber)
- Scan the directories which are supposed to be on each mirror (Adrian Reber)
- Use Yesterday's date on mm2_get_internet2_netblocks to avoid TZ issue (Adrian
  Reber)
- Fix logging in the UMDL script (Adrian Reber)
- Allow the UMDL to crawl only a specified category (Adrian Reber)
- Fix example fedmsg config (Ralph Bean)

* Mon Apr 13 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.7-1
- Update to 0.0.7
- Add missing import on mm2_update-EC2-netblocks
- Have the cron jobs running under a ``mirrormanager`` user (Adrian Reber)
- Update the last_crawled and last_crawled_duration correctly (Adrian Reber)
- Fix systemd's tempfile.conf for mirrormanager2
- Fix link to the crawler log file (Adrian Reber)
- Close per thread logging correctly (Adrian Reber)
- Add more informations to the log output (Adrian Reber)
- Start crawling the hosts which require the most time (Adrian Reber)
- Filters the hosts to crawl at the DB level to save time and memory (Adrian
  Reber)
- Fix the xmlrpc endpoint (Adrian Reber)
- Adjust Build Requires to include systemd-devel instead of just systemd
- Close session at the end and make the session permanent
- Add new columns to the host table to store extra infos (Adrian Reber)
- Use urllib2 instead of urlgrabber in the crawler (Adrian Reber)
- Fix crawler timeout (Adrian Reber)
- run_rsync() returns a temporary file which needs to be closed (Adrian Reber)

* Wed Mar 18 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.6-1
- Update to 0.0.6
- Drop the Locations in the hosts (no longer used)
- Add unit-tests
  - To the frontend
  - To some of the backend scripts
- Add dependency to python-IPy
- Fix ExecStart instruction for systemd
- Fix apache configuration file for mirrorlist
- Fix host selection logic in the crawler (Adrian Reber)
- Log the rsync command (Adrian Reber)
- Add the possibility to specify the rsync argument via the configuration file
  (Adrian Reber)
- Add and install a tempfile.d file for systemd to re-create
  /var/run/mirrormanager upon reboot

* Mon Dec 15 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.5-1
- Update to 0.0.5
- Include zebra-dump-parser in the backend sub-package
- Install weighted_shuffle and include it in the mirrorlist sub-package

* Mon Dec 15 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.4-1
- Update to 0.0.4
- Fix  typos in the script to point them to the correct configuration file by
  default
- Install the mirrorlist_server
- Move mirrorlist to rely on systemd instead of supervisor
- Install zebra-dump-parser user by mm2_get_internet2_netblocks
- Remove debugging statement for mm2_refresh_mirrorlist_cache, no need to output
  something if everything ran fine

* Mon Dec 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.3-1
- Update to 0.0.3
- Fix the import in the createdb script

* Mon Dec 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.2-1
- Update to 0.0.2
- Move the flask application to mirrormanager2/app.py and put a module
  place holder in mirrormanager2/__init__.py that we can extract when
  splitting the module in -lib

* Mon Dec 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.1-2
- Fix the package name in the Requires, using %%{name} fixes things

* Mon Dec 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.0.1-1
- Initial packaging work for Fedora
