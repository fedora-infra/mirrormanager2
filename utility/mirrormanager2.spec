# This package depends on automagic byte compilation
# https://fedoraproject.org/wiki/Changes/No_more_automagic_Python_bytecompilation_phase_2
%global _python_bytecompile_extra 1

%if (0%{?rhel} && 0%{?rhel} <= 7)
# Since the Python 3 stack in EPEL is missing too many dependencies,
# we're sticking with Python 2 there for now.
%global __python %{__python2}
%global python_pkgversion %{nil}
%else
# Default to Python 3 when not EL
%global __python %{__python3}
%global python_pkgversion %{python3_pkgversion}
%endif

Name:           mirrormanager2
Version:        0.14
Release:        1%{?dist}
Summary:        Mirror management application

# Most MirrorManager files are licensed under the MIT license. Some
# imported/derivated parts like zebra-dump-parser or the the script
# to generate the worldmaps are licensed under GPLv2 and GPLv2+
License:        MIT and GPLv2+ and GPLv2
URL:            https://github.com/fedora-infra/mirrormanager2/
Source0:        %{url}/archive/%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python%{python_pkgversion}-devel
BuildRequires:  python%{python_pkgversion}-flask
BuildRequires:  python%{python_pkgversion}-flask-admin
BuildRequires:  python%{python_pkgversion}-flask-xml-rpc
BuildRequires:  python%{python_pkgversion}-flask-wtf
BuildRequires:  python%{python_pkgversion}-wtforms
BuildRequires:  python%{python_pkgversion}-IPy
BuildRequires:  python%{python_pkgversion}-dns
BuildRequires:  python%{python_pkgversion}-fedora >= 0.3.33
BuildRequires:  python%{python_pkgversion}-fedora-flask >= 0.3.33
BuildRequires:  python%{python_pkgversion}-setuptools
BuildRequires:  python%{python_pkgversion}-psutil
BuildRequires:  python%{python_pkgversion}-alembic
BuildRequires:  protobuf-compiler
# Mirrorlist
BuildRequires:  python%{python_pkgversion}-geoip2
BuildRequires:  python%{python_pkgversion}-webob
BuildRequires:  systemd
BuildRequires:  python%{python_pkgversion}-sqlalchemy >= 0.7
# Testing
BuildRequires:  python%{python_pkgversion}-fedmsg-core
BuildRequires:  python%{python_pkgversion}-mock
BuildRequires:  python%{python_pkgversion}-blinker
BuildRequires:  rsync
BuildRequires:  python%{python_pkgversion}-pyrpmmd

%if 0%{?rhel} && 0%{?rhel} <= 7
BuildRequires:  python2-rpm-macros
BuildRequires:  py-radix
BuildRequires:  protobuf-python
Requires:  mod_wsgi
%else
BuildRequires:  python%{python_pkgversion}-protobuf
BuildRequires:  python%{python_pkgversion}-py-radix
Requires:  python%{python3_pkgversion}-mod_wsgi
%endif
# Testing
BuildRequires:  python%{python_pkgversion}-nose
BuildRequires:  python%{python_pkgversion}-coverage

Requires:  python%{python_pkgversion}-flask
Requires:  python%{python_pkgversion}-flask-admin
Requires:  python%{python_pkgversion}-flask-xml-rpc
Requires:  python%{python_pkgversion}-flask-wtf
Requires:  python%{python_pkgversion}-wtforms
Requires:  python%{python_pkgversion}-fedora >= 0.3.33
Requires:  python%{python_pkgversion}-fedora-flask >= 0.3.33
Requires:  python%{python_pkgversion}-setuptools
Requires:  python%{python_pkgversion}-psutil
Requires:  python%{python_pkgversion}-alembic

Requires:  %{name}-lib = %{version}-%{release}
Requires:  %{name}-filesystem = %{version}-%{release}

%description
MirrorManager keeps track of the public and private mirrors, that carry
Fedora, EPEL, and RHEL content. It is used by the Fedora infrastructure as
well as rpmfusion.org, a third-party repository.
It automatically selects the “best” mirror for a given user based on a set
of fallback heuristics (such as network, country or continent).


%package lib
Summary:        Library to interact with MirrorManager's database
BuildArch:      noarch

Requires:  %{name}-filesystem = %{version}-%{release}
Requires:  python%{python_pkgversion}-IPy
Requires:  python%{python_pkgversion}-dns
Requires:  python%{python_pkgversion}-sqlalchemy >= 0.7
Requires:  python%{python_pkgversion}-pyrpmmd
%if 0%{?rhel} && 0%{?rhel} <= 7
Requires:  protobuf-python
%else
Requires:  python%{python_pkgversion}-protobuf
%endif

%description lib
Library to interact with MirrorManager's database


%package mirrorlist
Summary:        MirrorList serving mirrors to yum/dnf
BuildArch:      noarch

Requires:  %{name}-filesystem = %{version}-%{release}
Requires:  python%{python_pkgversion}-geoip2
Requires:  python%{python_pkgversion}-webob
Requires:  python%{python_pkgversion}-IPy
Requires:  httpd
%if 0%{?rhel} && 0%{?rhel} <= 7
Requires:  py-radix
Requires:  mod_wsgi
Requires:  protobuf-python
%else
Requires:  python%{python_pkgversion}-py-radix
Requires:  python%{python_pkgversion}-mod_wsgi
Requires:  python%{python_pkgversion}-protobuf
%endif
Requires:  systemd
Requires(pre):  shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description mirrorlist
Sub-part of mirrormanager serving mirrors to yum/dnf


%package crawler
Summary:        Crawler for MirrorManager
BuildArch:      noarch

Requires:  %{name}-filesystem = %{version}-%{release}
Requires:  %{name}-lib = %{version}-%{release}
Requires:  python%{python_pkgversion}-geoip2
Requires:  logrotate
Requires(pre):  shadow-utils

%description crawler
Install the crawler for MirrorManager, crawling all the mirrors to find out
if they are up to date or not


%package backend
Summary:        Backend scripts for MirrorManager
BuildArch:      noarch

Requires:  %{name}-filesystem = %{version}-%{release}
Requires:  %{name}-lib = %{version}-%{release}
Requires(pre):  shadow-utils

%description backend
Install a number of utility scripts to be used manually or in cron jobs to
run MirrorManager.

%package client
Summary:        Fedora mirror management system downstream mirror tools
BuildArch:      noarch

Requires:  %{name}-filesystem = %{version}-%{release}
Requires:  logrotate
Requires:  systemd

Obsoletes: mirrormanager-client <= 1.4.4-6
Provides:  mirrormanager-client = %{version}-%{release}

%description client
Client-side, run on each downstream mirror, to report back to the
MirrorManager database a description of the content carried by that
mirror.

%package statistics
Summary:        Scripts to generate MirrorManager statistics
BuildArch:      noarch

Requires:  %{name}-filesystem = %{version}-%{release}
Requires:  %{name}-lib = %{version}-%{release}
Requires:  python%{python_pkgversion}-geoip2
Requires:  python%{python_pkgversion}-matplotlib
Requires:  python%{python_pkgversion}-basemap

%description statistics
A collection of different statistics script which are analyzing
MirrorManager content or log files. It contains scripts to analyze
the mirrorlist server connections, draws maps of all available mirrors
and can also visualize how fast the master data propagates to all the
mirrors. As it depends on matplotlib it has a rather large dependency
tree.

%package filesystem
Summary:        Base directories used by multiple subpackages
BuildArch:      noarch

%description filesystem
Base directories used by multiple subpackages


%prep
%setup -q


%build
# Recreating protobuf output
protoc --python_out=mirrorlist mirrormanager.proto
protoc --python_out=mirrormanager2/lib mirrormanager.proto
%py_build


%install
%py_install

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
install -m 644 mirrorlist/mirrormanager_pb2.py \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrormanager_pb2.py

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

# Install the client files
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/mirrormanager-client
install -m 0644 client/report_mirror.conf \
    $RPM_BUILD_ROOT/%{_sysconfdir}/mirrormanager-client/report_mirror.conf

# Install the country_continent file from MaxMind
install -m 0644 utility/country_continent.csv \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/country_continent.csv

# Fix the shebang for various scripts
sed -e "s|#!/usr/bin/env python|#!%{__python}|" -i \
    $RPM_BUILD_ROOT/%{_bindir}/* \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/*.py \
    $RPM_BUILD_ROOT/%{python_sitelib}/mirrormanager2/lib/umdl.py

# Switch interpreter for systemd units
sed -e "s|/usr/bin/python|%{__python}|g" -i $RPM_BUILD_ROOT/%{_unitdir}/*.service


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

%post mirrorlist
%systemd_post mirrorlist-server.service

%preun mirrorlist
%systemd_preun mirrorlist-server.service

%postun mirrorlist
%systemd_postun_with_restart mirrorlist-server.service

%check
# Exclude test_ui_app.py as it requires network connectivity
MM2_SKIP_NETWORK_TESTS=1 ./runtests.sh -v

%files
%doc README.rst doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/mirrormanager.conf
%config(noreplace) %{_sysconfdir}/mirrormanager/mirrormanager2.cfg

%dir %{_sysconfdir}/mirrormanager/
%dir %{python_sitelib}/%{name}/
%if ! (0%{?rhel} && 0%{?rhel} <= 7)
%dir %{python_sitelib}/%{name}/__pycache__
%endif

%{_sysconfdir}/mirrormanager/alembic.ini

%{_datadir}/mirrormanager2/mirrormanager2.wsgi
%{_datadir}/mirrormanager2/mirrormanager2_createdb.py*
%if ! (0%{?rhel} && 0%{?rhel} <= 7)
%{_datadir}/mirrormanager2/__pycache__/mirrormanager2_createdb.*.py*
%endif
%{_datadir}/mirrormanager2/alembic/

%{python_sitelib}/%{name}/*.py*
%if ! (0%{?rhel} && 0%{?rhel} <= 7)
%{python_sitelib}/%{name}/__pycache__/*
%endif
%{python_sitelib}/%{name}/templates/
%{python_sitelib}/%{name}/static/
%{python_sitelib}/%{name}*.egg-info

%files filesystem
%license LICENSE-MIT-X11 LICENSE-GPLv2
%dir %{python_sitelib}/%{name}
%dir %{_datadir}/mirrormanager2
%if ! (0%{?rhel} && 0%{?rhel} <= 7)
%dir %{_datadir}/mirrormanager2/__pycache__
%endif
%{_datadir}/mirrormanager2/country_continent.csv

%files lib
%{python_sitelib}/%{name}/lib/
%{python_sitelib}/%{name}/__init__.py*
%if ! (0%{?rhel} && 0%{?rhel} <= 7)
%{python_sitelib}/%{name}/__pycache__/__init__.*.py*
%endif


%files mirrorlist
%config(noreplace) %{_sysconfdir}/httpd/conf.d/mirrorlist-server.conf
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/run/mirrormanager
%attr(755,mirrormanager,mirrormanager) %dir %{_localstatedir}/lib/mirrormanager/
%{_tmpfilesdir}/%{name}-mirrorlist.conf
%{_unitdir}/mirrorlist-server.service
%{_datadir}/mirrormanager2/mirrorlist_client.wsgi
%{_datadir}/mirrormanager2/mirrorlist_server.py*
%{_datadir}/mirrormanager2/weighted_shuffle.py*
%{_datadir}/mirrormanager2/mirrormanager_pb2.py*
%if ! (0%{?rhel} && 0%{?rhel} <= 7)
%{_datadir}/mirrormanager2/__pycache__/mirrorlist_server.*.py*
%{_datadir}/mirrormanager2/__pycache__/weighted_shuffle.*.py*
%{_datadir}/mirrormanager2/__pycache__/mirrormanager_pb2.*.py*
%endif


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
%{_bindir}/mm2_emergency-expire-repo
%{_bindir}/mm2_get_global_netblocks
%{_bindir}/mm2_get_internet2_netblocks
%{_bindir}/mm2_move-devel-to-release
%{_bindir}/mm2_move-to-archive
%{_bindir}/mm2_refresh_mirrorlist_cache
%{_bindir}/mm2_update-EC2-netblocks
%{_bindir}/mm2_update-master-directory-list
%{_bindir}/mm2_umdl2
%{_bindir}/mm2_update-mirrorlist-server
%{_bindir}/mm2_create_install_repo
%{_bindir}/mm2_upgrade-install-repo


%files client
%dir %{_sysconfdir}/mirrormanager-client
%config(noreplace) %{_sysconfdir}/mirrormanager-client/report_mirror.conf
%{_bindir}/report_mirror

%files statistics
%{_bindir}/mm2_generate-worldmap
%{_bindir}/mm2_propagation
%{_bindir}/mirrorlist_statistics

%changelog
* Sun Jun 14 2020 Adrian Reber <adrian@lisas.de> - 0.14-1
- Hide last crawled/checked-in if private/public
- Only block report_mirror for private Hosts
- Add support to handle fedora-cisco-openh264-*

* Fri Mar 20 2020 Adrian Reber <adrian@lisas.de> - 0.13-1
- Fix https crawling
- Revert removal of jquery

* Mon Feb 24 2020 Adrian Reber <adrian@lisas.de> - 0.12-1
- Handle modular in EPEL
- Disable report_mirror for public mirrors
  https://github.com/fedora-infra/mirrormanager2/pull/281
- Fix typo in propagation URL
  https://github.com/fedora-infra/mirrormanager2/pull/280
- Fix WTForms deprecation warnings
  https://github.com/fedora-infra/mirrormanager2/pull/279
- umdl: skip certain paths for version detection
  https://github.com/fedora-infra/mirrormanager2/pull/278
- Disallow users accessing other hosts and sites
  https://github.com/fedora-infra/mirrormanager2/pull/277
- Remove jquery which was brought in for fedmenu
  https://github.com/fedora-infra/mirrormanager2/pull/274
- Only query database once for mirrorlist export
  https://github.com/fedora-infra/mirrormanager2/pull/273

* Fri Oct 04 2019 Adrian Reber <adrian@lisas.de> - 0.11-1
- Update to 0.11
- Offer protobuf output in refresh mirrorlist cache script

* Thu Oct 03 2019 Adrian Reber <adrian@lisas.de> - 0.10-1
- Update to 0.10
- crawler: correctly auto-disable mirrors
  https://github.com/fedora-infra/mirrormanager2/pull/265
- Use protobuf instead of pickle for backend - mirrorlist data exchange
  https://github.com/fedora-infra/mirrormanager2/pull/266
- Fix report_mirror with python3
  https://github.com/fedora-infra/mirrormanager2/pull/269
- repomap: add playground support
  https://github.com/fedora-infra/mirrormanager2/pull/270

* Tue Jan 15 2019 Adrian Reber <adrian@lisas.de> - 0.9.0-1
- Update to 0.9.0
- crawler: Correctly calculate the remaining time
  https://github.com/fedora-infra/mirrormanager2/pull/244
- repomap: more modular repository detection logic
  https://github.com/fedora-infra/mirrormanager2/pull/243
- crawler: correctly handle keep-alive for HTTPS
  https://github.com/fedora-infra/mirrormanager2/pull/245
- crawler: only update directories of the current category
  https://github.com/fedora-infra/mirrormanager2/pull/250
- python3 compatibility
  https://github.com/fedora-infra/mirrormanager2/pull/185
- rpmmd: switch from yum.repoMDObject pyrpmmd
  https://github.com/fedora-infra/mirrormanager2/pull/254
- Migrate to new geoip API
  https://github.com/fedora-infra/mirrormanager2/pull/253
- Use InputRequired() instead of Required()
  https://github.com/fedora-infra/mirrormanager2/pull/256
- Enable MirrorManager2 to be built using Python 3 for Fedora
  https://github.com/fedora-infra/mirrormanager2/pull/260
- Fix tests with python3
  https://github.com/fedora-infra/mirrormanager2/pull/261
- Toggle private
  https://github.com/fedora-infra/mirrormanager2/pull/257

* Sun Mar 04 2018 Adrian Reber <adrian@lisas.de> - 0.8.4-1
- Update to 0.8.4
- Sync with Fedora's specfile
- Explicitly specify 'python2' wherever calling the python
  interpreter
- Correctly handle Fedora 28 modular layout
  https://github.com/fedora-infra/mirrormanager2/pull/242
- Use "site", "host" and "mirror" consistently
  https://github.com/fedora-infra/mirrormanager2/pull/241
- crawler: support https only hosts
  https://github.com/fedora-infra/mirrormanager2/pull/240
- Make mm2_get_internet2_netblocks work again
  https://github.com/fedora-infra/mirrormanager2/pull/234
- crawler: use timeout also on rsync crawls
  https://github.com/fedora-infra/mirrormanager2/pull/229
- Fix existing test cases and re-enable tests on commits
- Enable tests in the %%check section
- publiclist: hide disabled arches and products
  https://github.com/fedora-infra/mirrormanager2/pull/223

* Tue Sep 26 2017 Adrian Reber <adrian@lisas.de> - 0.8.3-1
- Update to 0.8.3
- umdl: fix 'modular' repository detection
  https://github.com/fedora-infra/mirrormanager2/pull/221

* Sun Sep 24 2017 Adrian Reber <adrian@lisas.de> - 0.8.2-1
- Update to 0.8.2
- detect and setup mirrorlist/metalinks for modular Fedora
  https://github.com/fedora-infra/mirrormanager2/pull/220
- umdl: only create repositories for 'Everything'
  https://github.com/fedora-infra/mirrormanager2/pull/219
- Correctly detect repositories
  https://github.com/fedora-infra/mirrormanager2/pull/218

* Mon Aug 07 2017 Adrian Reber <adrian@lisas.de> - 0.8.1-1
- Update to 0.8.1
- Revert namespace changes
  https://github.com/fedora-infra/mirrormanager2/pull/214
- move-devel-to-release: fix the script to work with f26
  https://github.com/fedora-infra/mirrormanager2/pull/213
- Initial conversion to Fedora Bootstrap
  https://github.com/fedora-infra/mirrormanager2/pull/204
- umdl: various fixes found in production
  https://github.com/fedora-infra/mirrormanager2/pull/211

* Fri Jun 02 2017 Adrian Reber <adrian@lisas.de> - 0.8-1
- Update to 0.8
- Specify rel="noopener noreferrer" to link including target='_blank'
- Improve the runserver script
- Make the propagation script more robust
- crawler: also crawl https-only mirrors
  https://github.com/fedora-infra/mirrormanager2/issues/183
- mm2_move-devel-to-release: adapt to latest repository layout
  https://github.com/fedora-infra/mirrormanager2/issues/195
- Private URLs are now restricted to admins
  https://github.com/fedora-infra/mirrormanager2/issues/149
- mirrorlist: at least 5 mirrors should be returned for country/continent
  https://github.com/fedora-infra/mirrormanager2/issues/194
- Remove 'Master rsync server Access Control List IPs' section
  https://github.com/fedora-infra/mirrormanager2/issues/145
- mirrorlist: add pkl generation time to pkl
  https://github.com/fedora-infra/mirrormanager2/issues/184
- restrict non-admin users to certain netblock sizes
  https://github.com/fedora-infra/mirrormanager2/issues/71
- Change all references from fedorahosted.org to use the github area
- umdl: add fullfiletimelist-* based master scanning
  https://github.com/fedora-infra/mirrormanager2/issues/206

* Sat Oct 08 2016 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.7.3-2
- Remove <0.80 requirement on IPy

* Thu Jun 23 2016 Adrian Reber <adrian@lisas.de> - 0.7.3-1
- Update to 0.7.3
- Allow submission of checkin information via json (Patrick Uiterwijk)
  https://github.com/fedora-infra/mirrormanager2/issues/170
- Add logging to checkin code (Patrick Uiterwijk)
- mm2_crawler: Add missing field to stats dict
  https://github.com/fedora-infra/mirrormanager2/issues/176
- mirrolist: fix &redirect=1
  https://github.com/fedora-infra/mirrormanager2/issues/178

* Wed Jun 15 2016 Adrian Reber <adrian@lisas.de> - 0.7.2-1
- Update to 0.7.2
- Fix propagation diagram creation
- Use yesterday's date in get_global_netblocks
- Mark path containing /stage/ as testing
- Added an option with which the user can define the preferred
  protocol)
- Adjust repomap for the new repo layout (Pierre-Yves Chibon)
- Typo fix in readme (Taranjeet)

* Mon Feb 01 2016 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.7.1-1
- Update to 0.7.1
- Fixes to the emergency script (Adrian Reber and Patrick Uiterwijk)

* Wed Jan 13 2016 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.7-1
- Update to 0.7
- Fix various matplotlib problems in the statitics (Adrian Reber)
- Make green be synced and red be older in the propagation page (Patrick
  Uiterwijk)
- Add the possibility to clear all old files from a repo (to ensure users have
  only up to date mirrors) (Patrick Uiterwijk)
- Do not load the host config until it's asked (Drops the memory usage and
  increase the speed of the application) (Adrian Reber)

* Thu Dec 17 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6.1-1
- Update to 0.6.1
- Fix mirrorlist to access info from the just loaded pickle (Patrick Uiterwijk)

* Wed Dec 16 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6-1
- Update to 0.6
- Really ensure that new host is admin_active (Seth Jennings)
- Add the possibility to kill rsync after some time
- Add headers to the table listing the mirrors
- Cascade deletion and bring back the rsyncFilter endpoint
- Fix to the crawler (Adrian Reber)
- Improved documentation and validation
- Optionally exclude certain protocols from MM (Adrian Reber)
- Import generate-worldmap from MM1 (Adrian Reber)
- Optionally display mirrorlist statistics (Adrian Reber)
- mirrorlist: Remove --debug option (Adrian Reber)
- More mirrorlist statistics changes and spec file integration (Adrian Reber)
- Switch the MirrorList server to use threading rather than forking (Patrick
  Uiterwijk)

* Mon Sep 07 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5.1-1
- Update to 0.5.1
- Deleting URLs if site or host is removed (avoids the situation where a host is
  removed and then someone tries to re-add it) (Adrian Reber)
- Ensure that new host and new site are admin_active

* Fri Sep 04 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5-1
- Update to 0.5
- Add order option to get_file_detail() (Adrian Reber)
- Remove all whitespaces around the mirror URLs (Adrian Reber)
- Sort metalinks alternates by timestamps descending (Adrian Reber)
- Rewrite the UMDL2 into a UMDL2
- Add code to graph repomd.xml propagation (Adrian Reber)
- Rotate crawler logs once per week (Adrian Reber)
- Update the UMDL1 to share code with the UMDL2 (Adrian Reber)
- Remove trailing slash of site and host_category_url

* Thu Jul 30 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.2-1
- Update to 0.4.2
- Create the -client subpackage containing the report_mirror script and
  configuration file (Adrian Reber)

* Tue Jul 28 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.1-1
- Update to 0.4.1
- If the host has no categories do not auto-disable it (Adrian Reber)
- Different small umdl and crawler fixe (Adrian Reber)

* Wed Jul 22 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.0-1
- Update to 0.4.0
- Add utility script to update the MM2 DB for a single file (light-weight UMDL
  for a single file) (Ralph Bean)
- Add support to gracefully shutdown the crawler (Adrian Reber)
- Add support to limit crawling by continent (Adrian Reber)
- Fix the crawler to work properly with MM2
- Fix the repomap to create properly development repos
- Fix new repository detection and creation in UMDL (Adrian Reber)

* Thu Jul 02 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.1-1
- Update to 0.3.1
- Fix for broken logging output in the UMDL (Adrian Reber)
- Fix mm2_move-to-archive (Adrian Reber)

* Wed Jun 24 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.0-1
- Update to 0.3.0
- Fix the --delete action of the umdl (Adrian Reber)
- If the user is not an admin, keep the existing admin_active settings
- Only MM2 admins are allowed to change the always_up2date flag of a mirror
- Also fix the mm2_crawler logrotate script like the one for umdl (Adrian Reber)

* Thu Jun 11 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.1-1
- Update to 0.2.1
- Fix the mm2_move-devel-to-release script to work properly with MM2 and our
  products (Adrian Reber)

* Fri Jun 05 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.0-1
- Update to 0.2.0
- Include the background header file in MM2 itself (Adrian Reber)
- Support always update hosts which are unreachable in the crawler (Adrian
  Reber)
- Adjust the spec file to the systemd packaging guidelines for Fedora
- Multiple improvements to the crawler, including a start of a canary mode
  (Adrian Reber)
- Offer possibility to sort by product, bringing back MM1 behavior (Adrian
  Reber)
- Couple of UI fixes about who is allowed to access what
- Fix peer ASNs (in the same spirit, who can access)
- Create noauthed master for mirror publiclist so that it can be cached in
  memcachd (Patrick Uiterwijk)
- Fix the report_mirror to correctly catch the xmlrpclib.ProtocolError
- Add a new utility script to upgrade repo from -alpha or -beta to release
- Adjust the logrotate configuration to fix the permission denied error
- Create 2 API endpoints, one for zodbot's .mirroradmin and one for nagios

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
