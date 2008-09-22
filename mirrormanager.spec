#fixme use setuptools or similar to do the installaion in Makefile

Name:           mirrormanager
Version:        1.2.1
Release:        1%{?dist}
Summary:        Fedora mirror management system

Group:          Applications/Internet
License:        MIT and GPLv2
URL:            http://fedorahosted.org/mirrormanager
Source0:        https://fedorahosted.org/releases/m/i/%{name}/%{name}-%{version}.tar.bz2
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:  python

%package server
Requires:       python, TurboGears, python-IPy, python-GeoIP, python-psycopg2, mod_wsgi

%description server
MirrorManager tracks all the content provided on a master mirror
server, and that of all public and private mirrors of that content.

%package client
Requires:       python

%description python
Client-side, run on each downstream mirror, to report back to the
MirrorManager database a description of the content carried by that
mirror.

%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files server
%defattr(-,root,root,-)
%dir %{_localstatedir}/lib/%{name}/
%dir %{_localstatedir}/run%{name}/
%dir %{_localstatedir}/log/%{name}/
%dir %{_localstatedir}/lock/%{name}/
%{_datadir}/%{name}
%doc LICENSE LICENSES LICENSE_generate-worldmap

%files client
%defattr(-,root,root,-)
%{_bindir}/report_mirror
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/report_mirror.conf
%doc LICENSE


%changelog
* Fri Sep 19 2008 Matt Domsch <mdomsch@fedoraproject.org> - 1.2.1-1
- initial package attempt

