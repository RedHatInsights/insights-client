%if 0%{?rhel} != 8
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%endif
%define _binaries_in_noarch_packages_terminate_build 0

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.0.9
Release:                1%{?dist}
Source0:                https://github.com/redhatinsights/insights-client/archive/insights-client-%{version}.tar.gz
Epoch:                  0
License:                GPLv2+
URL:                    http://cloud.redhat.com/insights
Group:                  Applications/System
Vendor:                 Red Hat, Inc.

Provides: redhat-access-insights = 1.0.13-3
Provides: redhat-access-insights = %{version}-%{release}%{?dist}

Obsoletes: redhat-access-insights
Obsoletes: redhat-access-proactive

Requires: tar
Requires: gpg
Requires: pciutils
BuildArch: noarch

# RHEL 8
%if 0%{?rhel} == 8
%{?__python3:Requires: %{__python3}}
Requires: platform-python-setuptools
Requires: python3-requests >= 2.6
Requires: python3-PyYAML
Requires: python3-magic
Requires: python3-six
BuildRequires: python3-devel
BuildRequires: python3-six
BuildRequires: python3-setuptools

# RHEL 6-7
%else
Requires: python
Requires: python-setuptools
Requires: python-requests >= 2.6
Requires: PyYAML
Requires: libcgroup
Requires: python-magic
Requires: python-six >= 1.9.0
BuildRequires: python2-devel
BuildRequires: python-six
BuildRequires: python-setuptools
%endif

# systemd/RHEL 6 deps
%if 0%{?rhel} == 6
Requires: python-argparse
%else
%{?systemd_requires}
Requires: systemd
BuildRequires: systemd
%endif

%description
Sends insightful information to Red Hat for automated analysis

%prep
%setup -q

%install
rm -rf ${RPM_BUILD_ROOT}
%if 0%{?rhel} == 8
%{__python3} setup.py install --root=${RPM_BUILD_ROOT} $PREFIX
pathfix.py -pni "%{__python3}" %{buildroot}%{python3_sitelib}/insights_client/{__init__.py,major_version.py,run.py}
pathfix.py -pni "%{__python3}" %{buildroot}%{_bindir}/insights-client-run
pathfix.py -pni "%{__python3}" %{buildroot}%{_bindir}/insights-client
pathfix.py -pni "%{__python3}" %{buildroot}%{_bindir}/redhat-access-insights
%else
%{__python} setup.py install --root=${RPM_BUILD_ROOT} $PREFIX
%endif

%post

%if 0%{?rhel} != 6
%systemd_post %{name}.timer
%endif

# Only perform migration from redhat-access-insights to insights-client
if  [ $1 -eq 1  ]; then
    #Migrate existing machine-id
    if  [ -f "/etc/redhat_access_proactive/machine-id" ]; then
        cp /etc/redhat_access_proactive/machine-id /etc/insights-client/machine-id
    fi
    #Migrate OTHER existing machine-id
    if [ -f "/etc/redhat-access-insights/machine-id" ]; then
        cp /etc/redhat-access-insights/machine-id /etc/insights-client/machine-id
    fi
    #Migrate existing config
    if [ -f "/etc/redhat-access-insights/redhat-access-insights.conf" ]; then
        cp /etc/redhat-access-insights/redhat-access-insights.conf /etc/insights-client/insights-client.conf
        sed -i 's/\[redhat-access-insights\]/\[insights-client\]/' /etc/insights-client/insights-client.conf
    fi
    #Migrate registration record
    if [ -f "/etc/redhat-access-insights/.registered" ]; then
        cp /etc/redhat-access-insights/.registered /etc/insights-client/.registered
    fi
    if [ -f "/etc/redhat-access-insights/.unregistered" ]; then
        cp /etc/redhat-access-insights/.unregistered /etc/insights-client/.unregistered
    fi
    #Migrate last upload record
    if [ -f "/etc/redhat-access-insights/.lastupload" ]; then
        cp /etc/redhat-access-insights/.lastupload /etc/insights-client/.lastupload
    fi
    #Migrate remove.conf
    if [ -f "/etc/redhat-access-insights/remove.conf" ]; then
        cp /etc/redhat-access-insights/remove.conf /etc/insights-client/remove.conf
    fi
    # Symlink new cron job if the old one exists. Remove the old one
    if [ -f "/etc/cron.daily/redhat-access-insights" ]; then
        rm -f /etc/cron.daily/redhat-access-insights
        %if 0%{?rhel} == 6
            ln -sf /etc/insights-client/insights-client.cron /etc/cron.daily/insights-client                               
        %else
            %_bindir/systemctl start insights-client.timer
        %endif
    fi 
fi

# if the logging directory isnt created then make it
if ! [ -d "/var/log/insights-client" ]; then
mkdir -m 640 /var/log/insights-client
fi

# if the library directory for eggs and such isn't present
# make it
if ! [ -d "/var/lib/insights" ]; then
mkdir -m 644 /var/lib/insights
fi

%if 0%{?rhel} == 8
#Link motd into place. Only do so if motd file doesn't exist and insights hasn't been used
if [ ! -e /etc/motd.d/insights-client -a ! -L /etc/motd.d/insights-client ]; then
    mkdir -p /etc/motd.d
    if [ -e /var/lib/insights/newest.egg ]; then
        ln -sn /dev/null /etc/motd.d/insights-client
    else
        ln -sn /etc/insights-client/insights-client.motd /etc/motd.d/insights-client
    fi
fi
%endif

# always perform legacy symlinks
%posttrans
# remove all ACLs on upgrade, forever and always
setfacl -Rb /var/lib/insights
setfacl -Rb /var/log/insights-client
setfacl -Rb /etc/insights-client

%preun
%if 0%{?rhel} != 6
%systemd_preun %{name}.timer
%systemd_preun %{name}.service
%endif

%postun
if [ "$1" -eq 0 ]; then
# One run on removal, not upgrade
%if 0%{?rhel} != 6
%_bindir/systemctl daemon-reload > /dev/null 2>&1
%endif
rm -f /etc/cron.daily/insights-client
rm -f /etc/cron.weekly/insights-client
rm -f /etc/insights-client/.cache*
rm -f /etc/insights-client/.registered
rm -f /etc/insights-client/.unregistered
rm -f /etc/insights-client/.lastupload
rm -f /etc/insights-client/rpm.egg
rm -f /etc/insights-client/rpm.egg.asc
rm -f /etc/insights-client/.insights-core*.etag
rm -rf /var/lib/insights
# keep these to remove from previous install
rm -f /etc/ansible/facts.d/insights.fact
rm -f /etc/ansible/facts.d/insights_machine_id.fact
%if 0%{?rhel} == 8
rm -f /etc/motd.d/insights-client
%endif
fi

%clean
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT

%files
%defattr(0600, root, root)
%config(noreplace) /etc/insights-client/*.conf
/etc/insights-client/.fallback.json
/etc/insights-client/.fallback.json.asc
/etc/insights-client/.exp.sed
%if 0%{?rhel} == 8
%config(noreplace) %attr(644,root,root) /etc/insights-client/insights-client.motd
%endif

%if 0%{?rhel} != 6
%attr(644,root,root) %{_unitdir}/insights-client.service
%attr(644,root,root) %{_unitdir}/insights-client.timer
%endif

%attr(440,root,root) /etc/insights-client/*.pem
%attr(440,root,root) /etc/insights-client/redhattools.pub.gpg

%attr(755,root,root) %{_bindir}/insights-client
%attr(755,root,root) %{_bindir}/redhat-access-insights
%attr(755,root,root) %{_bindir}/insights-client-run

%if 0%{?rhel} == 6
%attr(755,root,root) /etc/insights-client/insights-client.cron
%config(noreplace) %attr(644,root,root) /etc/sysconfig/insights-client
%endif

%attr(644,root,root) /etc/insights-client/rpm.egg
%attr(644,root,root) /etc/insights-client/rpm.egg.asc

%if 0%{?rhel} == 8
%attr(755,root,root) %{python3_sitelib}/insights_client*.egg-info
%attr(644,root,root) %{python3_sitelib}/insights_client*.egg-info/*
%attr(644,root,root) %{python3_sitelib}/insights_client/*.py*
%attr(744,root,root) %{python3_sitelib}/insights_client/__pycache__
%else
%attr(755,root,root) %{python_sitelib}/insights_client*.egg-info
%attr(644,root,root) %{python_sitelib}/insights_client*.egg-info/*
%attr(644,root,root) %{python_sitelib}/insights_client/*.py*
%endif

%attr(640,root,root) /var/log/insights-client
%attr(644,root,root) /var/lib/insights

%doc
%defattr(-, root, root)
/usr/share/man/man8/*.8.gz
/usr/share/man/man5/*.5.gz

%changelog
* Thu Jan 18 2018 Kyle Lape <klape@redhat.com> - 3.0.3-1
- RHEL 7 RPM now uses systemd service and timer instead of cron
- Addition of IO and CPU cgroup constraints
- Fixed memory cgroup constraint

* Wed Oct 18 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.2-2
- Resolves BZ1498650, BZ1500008, BZ1501545, BZ1501552, BZ1501556, BZ1501561, BZ1501565, BZ1501566
- Fixes version migration logic
- Fixes symlink issues to old binary
- Fixes short ID analysis for images and containers
- Fixes Docker library detection
- Fixes image and container detection
- Fixes registration execution flow
- Fixes --version flag to print to stdout and include additional versioning information
- Includes Insights Core 3.0.3-1

* Wed Oct 4 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.1-5
- Resolves BZ1498581
- Fixes sys.path issues
- Includes Insights Core 3.0.2-6

* Wed Sep 27 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.0-4
- Initial build
