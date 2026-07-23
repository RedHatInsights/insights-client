%define _binaries_in_noarch_packages_terminate_build 0

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.8.0
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

%prep
{{{ git_dir_setup_macro }}}


%build
%{meson} \
    -Dpython=%{__python3} \
%if (0%{?rhel} && 0%{?rhel} < 10)
    -Dredhat_access_insights=true \
%endif
    %{nil}
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
%systemd_post %{name}-boot.service
if [ -d %{_sysconfdir}/motd.d ]; then
    if [ ! -e %{_sysconfdir}/motd.d/insights-client -a ! -L %{_sysconfdir}/motd.d/insights-client ]; then
        if [ -e %{_localstatedir}/lib/insights/newest.egg ]; then
            ln -sn /dev/null %{_sysconfdir}/motd.d/insights-client
        else
            ln -sn %{_sysconfdir}/insights-client/insights-client.motd %{_sysconfdir}/motd.d/insights-client
        fi
    fi
fi

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

%files
%config(noreplace) %{_sysconfdir}/insights-client/*.conf
%{_sysconfdir}/insights-client/insights-client.motd
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


%changelog
{{{ git_dir_changelog }}}
