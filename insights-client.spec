%define _binaries_in_noarch_packages_terminate_build 0

# This conditional build macro adds a "--with ros" commandline option to
# rpmbuild. The default behavior is to build without it.
%bcond_with ros
%bcond_with checkin
%bcond_with auto_registration

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.10.2
Release:                0%{?dist}
Source:                 {{{ git_dir_pack }}}
License:                GPL-2.0-or-later
URL:                    https://console.redhat.com/insights
Group:                  Applications/System
Vendor:                 Red Hat, Inc.

BuildArch: noarch

Requires: tar
Requires: gpg
Requires: pciutils

%{?__python3:Requires: %{__python3}}
%{?systemd_requires}
Requires: python3-requests >= 2.6
Requires: python3-PyYAML
Requires: python3-six
Requires: coreutils
Requires: insights-core >= 3.6.7

Requires: subscription-manager

BuildRequires: wget
BuildRequires: binutils
BuildRequires: python3-devel
BuildRequires: systemd
BuildRequires: pam
BuildRequires: python3-pytest
BuildRequires: systemd-rpm-macros

%description
Sends insightful information to Red Hat for automated analysis

%if %{with ros}
%package ros
Requires: pcp-zeroconf
Requires: insights-client

Summary: The subpackage for Insights resource optimization service

%description ros

The ros subpackage add ros_collect configuration parameter to insights-client.conf file,
the parameter is set to True by default. The system starts sending PCP archives to
Resource Optimization service upon modifying ros_collect parameter to True.
%endif

%prep
{{{ git_dir_setup_macro }}}

%build
sed -e "s|@PYTHON@|%{__python3}|g" -e "s|@pythondir@|%{python3_sitelib}|g" \
    src/insights-client.in > insights-client

sed -e "s|@PACKAGE@|%{name}|g" \
    -e "s|@PACKAGE_VERSION@|%{version}|g" \
    -e "s|@CORE_SELINUX_POLICY@||g" \
    src/insights_client/constants.py.in > src/insights_client/constants.py

%install

# ./src/
install -d -m 755 %{buildroot}%{_bindir}/
install -m 755 insights-client %{buildroot}%{_bindir}/
install -d -m 755 %{buildroot}%{python3_sitelib}/insights_client/
cp -pr src/insights_client/* %{buildroot}%{python3_sitelib}/insights_client/
rm -rf %{buildroot}%{python3_sitelib}/insights_client/tests
rm -f %{buildroot}%{python3_sitelib}/insights_client/constants.py.in

# ./data/
install -d -m 755 %{buildroot}%{_sysconfdir}/insights-client/
install -m 644 data/cert-api.access.redhat.com.pem %{buildroot}%{_sysconfdir}/insights-client/cert-api.access.redhat.com.pem
install -m 644 data/insights-client.conf %{buildroot}%{_sysconfdir}/insights-client/insights-client.conf
install -m 644 data/insights-client.motd %{buildroot}%{_sysconfdir}/insights-client/insights-client.motd
install -m 644 data/redhattools.pub.gpg %{buildroot}%{_sysconfdir}/insights-client/redhattools.pub.gpg

# ./data/logrotate.d/
install -d -m 755 %{buildroot}%{_sysconfdir}/logrotate.d/
install -m 644 data/logrotate.d/insights-client %{buildroot}%{_sysconfdir}/logrotate.d/insights-client

# ./data/systemd/
install -d -m 755 %{buildroot}%{_unitdir}/
install -d -m 755 %{buildroot}%{_presetdir}/
install -m 644 data/systemd/insights-client-boot.service %{buildroot}%{_unitdir}/insights-client-boot.service
install -m 644 data/systemd/insights-client.service %{buildroot}%{_unitdir}/insights-client.service
install -m 644 data/systemd/insights-client.timer %{buildroot}%{_unitdir}/insights-client.timer
install -m 644 data/systemd/80-insights.preset %{buildroot}%{_presetdir}/80-insights.preset
install -m 644 data/systemd/insights-client-results.service %{buildroot}%{_unitdir}/insights-client-results.service
install -m 644 data/systemd/insights-client-results.path %{buildroot}%{_unitdir}/insights-client-results.path

# ./data/tmpfiles.d/
install -d -m 755 %{buildroot}%{_tmpfilesdir}/
install -m 644 data/tmpfiles.d/insights-client.conf %{buildroot}%{_tmpfilesdir}/insights-client.conf

# ./docs/
install -d -m 755 %{buildroot}%{_mandir}/man5/
install -d -m 755 %{buildroot}%{_mandir}/man8/
install -m 644 docs/insights-client.conf.5 %{buildroot}%{_mandir}/man5/
install -m 644 docs/insights-client.8 %{buildroot}%{_mandir}/man8/

install -d -m 755 %{buildroot}%{_defaultdocdir}/%{name}/
install -m 644 docs/file-redaction.yaml.example %{buildroot}%{_defaultdocdir}/%{name}/
install -m 644 docs/file-content-redaction.yaml.example %{buildroot}%{_defaultdocdir}/%{name}/

# Conditionally install other files
%if %{with auto_registration}
install -m 644 data/systemd/insights-register.service %{buildroot}%{_unitdir}/insights-register.service
install -m 644 data/systemd/insights-register.path %{buildroot}%{_unitdir}/insights-register.path
install -m 644 data/systemd/insights-unregister.service %{buildroot}%{_unitdir}/insights-unregister.service
install -m 644 data/systemd/insights-unregister.path %{buildroot}%{_unitdir}/insights-unregister.path
install -m 644 data/systemd/80-insights-register.preset %{buildroot}%{_presetdir}/80-insights-register.preset
%endif

%if %{with checkin}
install -m 644 data/systemd/insights-client-checkin.timer %{buildroot}%{_unitdir}/insights-client-checkin.timer
install -m 644 data/systemd/insights-client-checkin.service %{buildroot}%{_unitdir}/insights-client-checkin.service
%endif

# Create different insights directories in /var
mkdir -p %{buildroot}%{_localstatedir}/log/insights-client/
mkdir -p %{buildroot}%{_localstatedir}/lib/insights/
mkdir -p %{buildroot}%{_localstatedir}/cache/insights/
mkdir -p %{buildroot}%{_localstatedir}/cache/insights-client/

%post
%systemd_post %{name}.timer
%systemd_post %{name}-boot.service

# Remove legacy egg files from previous installations
rm -f %{_sysconfdir}/insights-client/rpm.egg
rm -f %{_sysconfdir}/insights-client/rpm.egg.asc
rm -f %{_localstatedir}/lib/insights/*.egg
rm -f %{_localstatedir}/lib/insights/*.egg.asc

# Symlink the message of the day if the system has not been registered with Insights
_SHOULD_WRITE_MOTD=1
# MOTD directory doesn't exist for some reason; don't even try
if [ ! -d %{_sysconfdir}/motd.d ]; then _SHOULD_WRITE_MOTD=0; fi
# Message shouldn't be displayed if the system has ever been registered
if [ -e %{_sysconfdir}/insights-client/.registered ]; then _SHOULD_WRITE_MOTD=0; fi
if [ -e %{_sysconfdir}/insights-client/.unregistered ]; then _SHOULD_WRITE_MOTD=0; fi
# Message file is already in place (as a file, or as a symlink)
if [ -e %{_sysconfdir}/motd.d/insights-client -o -L %{_sysconfdir}/motd.d/insights-client ]; then _SHOULD_WRITE_MOTD=0; fi
if [ "$_SHOULD_WRITE_MOTD" -eq 1 ]; then
    ln -sn %{_sysconfdir}/insights-client/insights-client.motd %{_sysconfdir}/motd.d/insights-client
fi

%if %{with ros}
%post ros
rm -f /var/lib/pcp/config/pmlogger/config.ros
sed -i "/PCP_LOG_DIR\/pmlogger\/ros/d" /etc/pcp/pmlogger/control.d/local

if ! grep -q "^ros_collect" %{_sysconfdir}/insights-client/insights-client.conf; then
cat <<EOF >> %{_sysconfdir}/insights-client/insights-client.conf
### Begin insights-client-ros ###
ros_collect=True
### End insights-client-ros ###
EOF
fi
%endif

%preun
%systemd_preun %{name}.timer
%systemd_preun %{name}.service
%systemd_preun %{name}-boot.service

%postun
%systemd_postun %{name}.timer
%systemd_postun %{name}.service
%systemd_postun %{name}-boot.service

# Clean up files created by insights-client that are unowned by the RPM
if [ $1 -eq 0 ]; then
    rm -f %{_sysconfdir}/cron.daily/insights-client
    rm -f %{_sysconfdir}/ansible/facts.d/insights.fact
    rm -f %{_sysconfdir}/ansible/facts.d/insights_machine_id.fact
    rm -f %{_sysconfdir}/motd.d/insights-client
    rm -rf %{_localstatedir}/lib/insights
    rm -rf %{_localstatedir}/log/insights-client
    rm -f %{_sysconfdir}/insights-client/.*.etag
fi

%if %{with ros}
%postun ros
sed -i '/### Begin insights-client-ros ###/,/### End insights-client-ros ###/d;/ros_collect=True/d' %{_sysconfdir}/insights-client/insights-client.conf
%endif

%files
%config(noreplace) %{_sysconfdir}/insights-client/*.conf
%{_sysconfdir}/insights-client/insights-client.motd
%{_bindir}/*
%{_unitdir}/*
%attr(444,root,root) %{_sysconfdir}/insights-client/*.pem
%attr(444,root,root) %{_sysconfdir}/insights-client/redhattools.pub.gpg
%{python3_sitelib}/insights_client/
%{_defaultdocdir}/%{name}
%{_presetdir}/*.preset
%attr(700,root,root) %dir %{_localstatedir}/log/insights-client/
%attr(700,root,root) %dir %{_localstatedir}/cache/insights-client/
%attr(750,root,root) %dir %{_localstatedir}/cache/insights/
%attr(750,root,root) %dir %{_localstatedir}/lib/insights/
%{_sysconfdir}/logrotate.d/insights-client
%{_tmpfilesdir}/insights-client.conf

%doc
%defattr(-, root, root)
%{_mandir}/man8/*.8.gz
%{_mandir}/man5/*.5.gz

%if %{with ros}
%files ros
%endif

%changelog
{{{ git_dir_changelog }}}
