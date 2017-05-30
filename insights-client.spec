Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.0.0
Release:                0%{?dist}
Source0:                insights-client
Source1:                etc
Epoch:                  0
License:                GPLv2+
URL:                    http://access.redhat.com/insights
Group:                  Applications/System
Vendor:                 Red Hat, Inc.
BuildArch:              noarch

%description
Sends insightful information to Red Hat for automated analysis

Provides: redhat-access-insights

Obsoletes: redhat-access-proactive
Obsoletes: redhat-access-insights

Requires: python
Requires: python-setuptools
Requires: python-requests >= 2.6
Requires: pyOpenSSL
Requires: libcgroup
Requires: tar
Requires: gpg
Requires: pciutils
%if 0%{?rhel} && 0%{?rhel} > 6
Requires: libcgroup-tools
%endif

BuildRequires: python2-devel
BuildRequires: python-setuptools

%install
mkdir -p %{buildroot}%{_bindir}
cp %{SOURCE0} %{buildroot}%{_bindir}/
mkdir -p %{buildroot}/etc/insights-client
cp %{SOURCE1}/insights-client/insights_action_plugin.py %{buildroot}/etc/insights-client/
cp %{SOURCE1}/insights-client/insights_ansible_module.py %{buildroot}/etc/insights-client/
cp %{SOURCE1}/insights-client/redhat.gpg %{buildroot}/etc/insights-client/

%files
%{_bindir}/insights-client
%exclude /etc/insights-client/*.pyc
%exclude /etc/insights-client/*.pyo

%defattr(0600, root, root)
%dir /etc/insights-client
/etc/insights-client/insights_action_plugin.py
/etc/insights-client/insights_ansible_module.py
/etc/insights-client/redhat.gpg

%changelog
* Fri May 19 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.0-0
- Initial build