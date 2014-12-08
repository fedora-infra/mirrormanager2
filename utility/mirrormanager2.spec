%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           mirrormanager2
Version:        2.0.1
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
# Mirrorlist
BuildRequires:  python-GeoIP
BuildRequires:  py-radix
BuildRequires:  python-webob

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

%description mirrorlist
Sub-part of mirrormanager serving mirrors to yum/dnf


%package crawler
Summary:        Crawler for MirrorManager
Group:          Development/Tools
BuildArch:      noarch

Requires:  mirrormanager-lib == %{version}

%description crawler
Install the crawler for MirrorManager, crawling all the mirrors to find out
if they are up to date or not


%package backend
Summary:        Backend scripts for MirrorManager
Group:          Development/Tools
BuildArch:      noarch

Requires:  mirrormanager-lib == %{version}

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
# for .wsgi files mainly
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2
# Stores temp files (.sock & co)
mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/mirrormanager
# Lock files
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/lock/mirrormanager
# Stores lock and pid info
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/run/mirrormanager

# Install apache configuration file
install -m 644 mirrorlist/apache/mirrorlist-server.conf \
    $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/mirrorlist-server.conf
install -m 644 utility/mirrormanager.conf.sample \
    $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/mirrormanager.conf

# Install configuration file
install -m 644 utility/mirrormanager2.cfg.sample \
    $RPM_BUILD_ROOT/%{_sysconfdir}/mirrormanager/mirrormanager2.cfg

# Install WSGI file
install -m 644 utility/mirrormanager2.wsgi \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrormanager2.wsgi
install -m 644 mirrorlist/mirrorlist_client.wsgi \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrorlist_client.wsgi


# Install the createdb script
install -m 644 createdb.py \
    $RPM_BUILD_ROOT/%{_datadir}/mirrormanager2/mirrormanager2_createdb.py



%check
# One day we will have unit-tests to run here

%files
%doc README.rst LICENSE-MIT-X11 doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/mirrormanager.conf
%config(noreplace) %{_sysconfdir}/mirrormanager/mirrormanager2.cfg

%dir %{_sysconfdir}/mirrormanager/
%dir %{python_sitelib}/%{name}/

%{_datadir}/mirrormanager2/mirrormanager2.wsgi
%{_datadir}/mirrormanager2/mirrormanager2_createdb.py*

%{python_sitelib}/%{name}/*.py*
%{python_sitelib}/%{name}/templates/
%{python_sitelib}/%{name}/static/
%{python_sitelib}/%{name}*.egg-info


%files lib
%{python_sitelib}/%{name}/lib/


%files mirrorlist
%config(noreplace) %{_sysconfdir}/httpd/conf.d/mirrorlist-server.conf
%dir %{_localstatedir}/run/mirrormanager
%{_datadir}/mirrormanager2/mirrorlist_client.wsgi


%files crawler
%{_bindir}/mm2_crawler


%files backend
%dir %{_localstatedir}/lock/mirrormanager
%{_bindir}/mm2_get_global_netblocks
%{_bindir}/mm2_get_internet2_netblocks
%{_bindir}/mm2_move-devel-to-release
%{_bindir}/mm2_move-to-archive
%{_bindir}/mm2_refresh_mirrorlist_cache
%{_bindir}/mm2_update-EC2-netblocks
%{_bindir}/mm2_update-master-directory-list
%{_bindir}/mm2_update-mirrorlist-server

%changelog
* Sat Dec 06 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 2.0.1-1
- Initial packaging work for Fedora
