%define _binaries_in_noarch_packages_terminate_build 0

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

%package ros
Requires: pcp-zeroconf
Summary: The subpackage for Resource Optimization Service
Source1: ros.conf

%description ros

The ros subpackage provides configuration file including parameter ros_collect,
the parameter is set to True by default. The system starts sending PCP archives to
Resource Optimization service upon modifying ros_collect parameter to True.

%prep
{{{ git_dir_setup_macro }}}


%build
%{meson} -Dpython=%{__python3}
%{meson_build}


%install
%{meson_install}
# Create directory and copy file to new directory for Resource Optimization service
install -d -m0750 %{_sysconfdir}/insights_client/insights-client.conf.d
install -m0644  %{SOURCE1} %{_sysconfdir}/insights_client/insights-client.conf.d/ros.conf

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

%post ros
echo
echo "Removing custom PCP configuration required for Resource Optimization service!"
echo
rm -f /var/lib/pcp/config/pmlogger/config.ros
sed -i "/PCP_LOG_DIR\/pmlogger\/ros/d" /etc/pcp/pmlogger/control.d/local

%preun
%systemd_preun %{name}.timer
%systemd_preun %{name}.service
%systemd_preun insights-client-boot.service

%postun
%systemd_postun %{name}.timer
%systemd_postun %{name}.service
%systemd_postun insights-client-boot.service

%postun ros
echo
echo "Removing the Resource Optimization service configuration file!"
rm -f %{_sysconfdir}/insights_client/insights-client.conf.d/ros.conf

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


%files
%config(noreplace) %{_sysconfdir}/insights-client/*.conf
%{_sysconfdir}/insights-client/insights-client.motd
%{_sysconfdir}/insights-client/.fallback.json*
%{_sysconfdir}/insights-client/.exp.sed
%{_sysconfdir}/insights-client/rpm.egg*
%{_bindir}/*
%{_unitdir}/*
%{_presetdir}/*
%attr(444,root,root) %{_sysconfdir}/insights-client/*.pem
%attr(444,root,root) %{_sysconfdir}/insights-client/redhattools.pub.gpg
%{_defaultdocdir}/%{name}
%{python3_sitelib}/insights_client/
%{_sysconfdir}/logrotate.d/insights-client
%{_tmpfilesdir}/insights-client.conf

%files ros
%config(noreplace)
%{_sysconfdir}/insights_client/insights-client.conf.d/ros.conf

%doc
%defattr(-, root, root)
%{_mandir}/man8/*.8.gz
%{_mandir}/man5/*.5.gz


%changelog
{{{ git_dir_changelog }}}
