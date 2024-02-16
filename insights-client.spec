%define _binaries_in_noarch_packages_terminate_build 0

# This conditional build macro adds a "--with ros" commandline option to
# rpmbuild. The default behavior is to build without it.
%bcond_with ros

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                {{{ git_dir_version lead=3.2 }}}
Release:                0%{?dist}
Source:                 {{{ git_dir_pack }}}
License:                GPLv2+
URL:                    http://console.redhat.com/insights
Group:                  Applications/System
Vendor:                 Red Hat, Inc.

Provides: redhat-access-insights = %{version}-%{release}%{?dist}

Obsoletes: redhat-access-insights <= 1.0.13-2
Obsoletes: redhat-access-proactive <= 1.0.13-2

BuildArch: noarch

Requires: tar
Requires: gpg
Requires: pciutils

%{?__python3:Requires: %{__python3}}
%{?systemd_requires}
Requires: python3-requests >= 2.6
Requires: python3-PyYAML
Requires: python3-magic
Requires: python3-six
Requires: python3dist(setuptools)
Requires: coreutils

Requires: subscription-manager

BuildRequires: wget
BuildRequires: binutils
BuildRequires: python3-devel
BuildRequires: systemd
BuildRequires: pam
BuildRequires: meson
BuildRequires: python3-pytest
BuildRequires: systemd-rpm-macros


%description
Sends insightful information to Red Hat for automated analysis

%if %{with ros}
%package ros
Requires: pcp-zeroconf
Summary: The subpackage for Insights resource optimization service

%description ros

The ros subpackage add ros_collect configuration parameter to insights-client.conf file,
the parameter is set to True by default. The system starts sending PCP archives to
Resource Optimization service upon modifying ros_collect parameter to True.
%endif

%prep
{{{ git_dir_setup_macro }}}


%build
%{meson} -Dpython=%{__python3}
%{meson_build}


%install
%{meson_install}

# Create different insights directories in /var
mkdir -p %{buildroot}%{_localstatedir}/log/insights-client/
mkdir -p %{buildroot}%{_localstatedir}/lib/insights/
mkdir -p %{buildroot}%{_localstatedir}/cache/insights/
mkdir -p %{buildroot}%{_localstatedir}/cache/insights-client/

%post
%systemd_post %{name}.timer
if [ -d %{_sysconfdir}/motd.d ]; then
    if [ ! -e %{_sysconfdir}/motd.d/insights-client -a ! -L %{_sysconfdir}/motd.d/insights-client ]; then
        if [ -e %{_localstatedir}/lib/insights/newest.egg ]; then
            ln -sn /dev/null %{_sysconfdir}/motd.d/insights-client
        else
            ln -sn %{_sysconfdir}/insights-client/insights-client.motd %{_sysconfdir}/motd.d/insights-client
        fi
    fi
fi

%if %{with ros}
%post ros
rm -f /var/lib/pcp/config/pmlogger/config.ros
sed -i "/PCP_LOG_DIR\/pmlogger\/ros/d" /etc/pcp/pmlogger/control.d/local

if grep -qv "^ros_collect" %{_sysconfdir}/insights-client/insights-client.conf; then
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
%systemd_preun insights-client-boot.service

%postun
%systemd_postun %{name}.timer
%systemd_postun %{name}.service
%systemd_postun insights-client-boot.service

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
%{_sysconfdir}/insights-client/.fallback.json*
%{_sysconfdir}/insights-client/.exp.sed
%{_sysconfdir}/insights-client/rpm.egg*
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
