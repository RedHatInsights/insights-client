%define _binaries_in_noarch_packages_terminate_build 0

%global __python %{_libexecdir}/platform-python

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


%description
Sends insightful information to Red Hat for automated analysis

%prep
{{{ git_dir_setup_macro }}}


%build
%{meson} -Dpython=%{__python}
%{meson_build}


%install
%{meson_install}

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

%systemd_post insights-register.path
%systemd_post insights-unregister.path
%systemd_post 80-insights.preset


%preun
%systemd_preun %{name}.timer
%systemd_preun %{name}.service
%systemd_preun insights-register.path
%systemd_preun insights-unregister.path
%systemd_preun insights-client-boot.service

%postun
%systemd_postun %{name}.timer
%systemd_postun %{name}.service
%systemd_postun insights-register.path
%systemd_postun insights-unregister.path
%systemd_postun insights-client-boot.service

# Clean up files created by insights-client that are unowned by the RPM
if [ $1 -eq 0 ]; then
    systemctl unmask insights-register.path
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

%doc
%defattr(-, root, root)
%{_mandir}/man8/*.8.gz
%{_mandir}/man5/*.5.gz


%changelog
{{{ git_dir_changelog }}}
