%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define _binaries_in_noarch_packages_terminate_build 0

%global insights_user  insights
%global insights_group %{insights_user}

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.0.3
Release:                1%{?dist}
Source0:                https://github.com/redhatinsights/insights-client/archive/insights-client-%{version}.tar.gz
Epoch:                  0
License:                GPLv2+
URL:                    http://access.redhat.com/insights
Group:                  Applications/System
Vendor:                 Red Hat, Inc.

Provides: redhat-access-insights = 1.0.13-3
Provides: redhat-access-insights = %{version}-%{release}%{?dist}

Obsoletes: redhat-access-insights <= 1.0.13-2%{?dist}
Obsoletes: redhat-access-proactive <= 0.3.3-0%{?dist}

Requires: python
Requires: python-setuptools
Requires: python-requests >= 2.6
Requires: PyYAML
Requires: pyOpenSSL
Requires: libcgroup
Requires: tar
Requires: gpg
Requires: pciutils
Requires: python-magic
Requires: python-six
%if 0%{?rhel} && 0%{?rhel} == 6
Requires: python-argparse
%else
%{?systemd_requires}
Requires: systemd
%endif
BuildArch: noarch

BuildRequires: python2-devel
BuildRequires: python-setuptools
%if 0%{?rhel} != 6
BuildRequires: systemd
%endif

%description
Sends insightful information to Red Hat for automated analysis

%prep
%setup -q

%install
rm -rf ${RPM_BUILD_ROOT}
%{__python} setup.py install --root=${RPM_BUILD_ROOT} $PREFIX

%pre
getent group insights > /dev/null || /usr/sbin/groupadd -r %{insights_group}
getent passwd insights > /dev/null || \
    /usr/sbin/useradd -g insights -r --shell /sbin/nologin %{insights_user} \
    -c "Red Hat Insights" -d /var/lib/insights

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
    if ! [ -d "/etc/redhat-access-insights" ]; then
        mkdir /etc/redhat-access-insights
    fi
    # Symlink new cron job if the old one exists. Remove the old one
    if [ -f "/etc/cron.daily/redhat-access-insights" ]; then
        rm -f /etc/cron.daily/redhat-access-insights
        %if 0%{?rhel} && 0%{?rhel} == 6
            ln -sf /etc/insights-client/insights-client.cron /etc/cron.daily/insights-client                               
        %else
            %_bindir/systemctl start insights-client.timer
        %endif
    fi 
fi

# if the logging directory isnt created then make it
# and set the ACLs
if ! [ -d "/var/log/insights-client" ]; then
mkdir /var/log/insights-client
fi
setfacl -Rd -m g:insights:rwX /var/log/insights-client
setfacl -m g:insights:rwX /var/log/insights-client

# if the library directory for eggs and such isn't present
# make it AND
# set the ACLs
if ! [ -d "/var/lib/insights" ]; then
mkdir /var/lib/insights
fi
setfacl -Rd -m g:insights:rwX /var/lib/insights
setfacl -R -m g:insights:rwX /var/lib/insights

# set some more ACLs
setfacl -Rd -m g:insights:rwX -m m:rw /etc/insights-client
setfacl -R -m g:insights:rwX -m m:rw /etc/insights-client
setfacl -m g:insights:r -m m:r /etc/insights-client/*.pem
setfacl -m g:insights:r -m m:r /etc/insights-client/redhattools.pub.gpg
setfacl -m g:insights:rw -m m:rw /etc/insights-client/insights-client.conf
setfacl -m g:insights:r -m m:r /etc/insights-client/rpm.egg
setfacl -m g:insights:r -m m:r /etc/insights-client/rpm.egg.asc
setfacl -m g:insights:rwx /etc/insights-client

# if ansible is present
# make the fact directory AND
# the fact file AND
# set the ACLs
if [ -d "/etc/ansible" ]; then
if ! [ -d "/etc/ansible/facts.d" ]; then
mkdir /etc/ansible/facts.d
fi
fi
if [ -d "/etc/ansible/facts.d" ]; then
touch /etc/ansible/facts.d/insights.fact
touch /etc/ansible/facts.d/insights_machine_id.fact
setfacl -m g:insights:rw /etc/ansible/facts.d/insights.fact
setfacl -m g:insights:rw /etc/ansible/facts.d/insights_machine_id.fact
fi


# always perform legacy symlinks
%posttrans
mkdir -p /etc/redhat-access-insights
ln -sf /etc/insights-client/insights-client.conf /etc/redhat-access-insights/redhat-access-insights.conf
ln -sf /etc/insights-client/insights-client.cron /etc/redhat-access-insights/redhat-access-insights.cron
ln -sf /etc/insights-client/.registered /etc/redhat-access-insights/.registered
ln -sf /etc/insights-client/.unregistered /etc/redhat-access-insights/.unregistered
ln -sf /etc/insights-client/.lastupload /etc/redhat-access-insights/.lastupload
ln -sf /etc/insights-client/machine-id /etc/redhat-access-insights/machine-id
if [ -f "/etc/insights-client/.lastupload" ]; then
    setfacl -m g:insights:rwx /etc/insights-client/.lastupload
fi
if [ -f "/etc/insights-client/.registered" ]; then
    setfacl -m g:insights:rwx /etc/insights-client/.registered
fi
if [ -f "/etc/insights-client/.unregistered" ]; then
    setfacl -m g:insights:rwx /etc/insights-client/.unregistered
fi

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
rm -rf /var/lib/insights
rm -f /etc/ansible/facts.d/insights.fact
rm -f /etc/ansible/facts.d/insights_machine_id.fact
# remove symlink to old name on uninstall
rm -f %{_bindir}/redhat-access-insights
# remove symlinks to old configs
rm -rf /etc/redhat-access-insights/
rm -f /etc/cron.daily/redhat-access-insights
rm -f /etc/cron.weekly/redhat-access-insights
fi

%clean
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT

%files
%defattr(0600, root, root)
%config(noreplace) /etc/insights-client/*.conf
/etc/insights-client/.fallback.json
/etc/insights-client/.fallback.json.asc
/etc/insights-client/.exp.sed

%if 0%{?rhel} != 6
%attr(644,root,root) %{_unitdir}/insights-client.service
%attr(644,root,root) %{_unitdir}/insights-client.timer
%endif

%attr(440,root,root) /etc/insights-client/*.pem
%attr(440,root,root) /etc/insights-client/redhattools.pub.gpg

%attr(755,root,root) %{_bindir}/insights-client
%attr(755,root,root) %{_bindir}/redhat-access-insights
%attr(755,root,root) %{_bindir}/insights-client-run

%if 0%{?rhel} && 0%{?rhel} == 6
%attr(755,root,root) /etc/insights-client/insights-client.cron
%endif

%attr(644,root,root) /etc/insights-client/rpm.egg
%attr(644,root,root) /etc/insights-client/rpm.egg.asc

%attr(755,root,root) %dir %{python_sitelib}/insights_client*.egg-info
%attr(644,root,root) %{python_sitelib}/insights_client*.egg-info/*
%attr(644,root,root) %{python_sitelib}/insights_client/*.py*

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
