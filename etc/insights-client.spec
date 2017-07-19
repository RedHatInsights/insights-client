%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define _binaries_in_noarch_packages_terminate_build 0

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.0.0
Release:                0%{?dist}
Source0:                https://github.com/redhatinsights/insights-client/archive/insights-client-%{version}.tar.gz
Epoch:                  0
License:                GPLv2+
URL:                    http://access.redhat.com/insights
Group:                  Applications/System
Vendor:                 Red Hat, Inc.

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
BuildArch: noarch

BuildRequires: python2-devel
BuildRequires: python-setuptools

%description
Sends insightful information to Red Hat for automated analysis

%prep
%setup -q

%install
rm -rf ${RPM_BUILD_ROOT}
%{__python} setup.py install --root=${RPM_BUILD_ROOT} $PREFIX

%post
#Migrate existing machine-id
if  [ -f "/etc/redhat_access_proactive/machine-id" ]; then
mv /etc/redhat_access_proactive/machine-id /etc/insights-client/machine-id
fi
#Migrate OTHER existing machine-id
if [ -f "/etc/redhat-access-insights/machine-id" ]; then
mv /etc/redhat-access-insights/machine-id /etc/insights-client/machine-id
fi
#Migrate existing config
if [ -f "/etc/redhat-access-insights/redhat-access-insights.conf" ]; then
mv /etc/redhat-access-insights/redhat-access-insights.conf /etc/insights-client/insights-client.conf
sed -i 's/\[redhat-access-insights\]/\[insights-client\]/' /etc/insights-client/insights-client.conf
fi
#Migrate registration record
if [ -f "/etc/redhat-access-insights/.registered" ]; then
mv /etc/redhat-access-insights/.registered /etc/insights-client/.registered
fi
#Migrate last upload record
if [ -f "/etc/redhat-access-insights/.lastupload" ]; then
mv /etc/redhat-access-insights/.lastupload /etc/insights-client/.lastupload
fi
# Create symlinks to old name
ln -sf %{_bindir}/insights-client %{_bindir}/redhat-access-insights
if ! [ -d "/etc/redhat-access-insights" ]; then
mkdir /etc/redhat-access-insights
fi
ln -sf /etc/insights-client/insights-client.conf /etc/redhat-access-insights/redhat-access-insights.conf
ln -sf /etc/insights-client/insights-client.cron /etc/redhat-access-insights/redhat-access-insights.cron
ln -sf /etc/cron.daily/insights-client /etc/cron.daily/redhat-access-insights
ln -sf /etc/cron.weekly/insights-client /etc/cron.weekly/redhat-access-insights
ln -sf /etc/insights-client/.registered /etc/redhat-access-insights/.registered
ln -sf /etc/insights-client/.unregistered /etc/redhat-access-insights/.unregistered
ln -sf /etc/insights-client/machine-id /etc/redhat-access-insights/machine-id

%postun
if [ "$1" -eq 0 ]; then
rm -f /etc/cron.daily/insights-client
rm -f /etc/cron.weekly/insights-client
rm -f /etc/insights-client/.cache*
rm -f /etc/insights-client/.registered
rm -f /etc/insights-client/.unregistered
rm -f /etc/insights-client/.lastupload
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
%defattr(755,root,root)
%{_bindir}/insights-client
%{_bindir}/insights-client-run
/etc/insights-client/insights-client.cron

%defattr(0600, root, root)
%dir /etc/insights-client
%config(noreplace) /etc/insights-client/*.conf
/etc/insights-client/.exp.sed
/etc/insights-client/*.pem
/etc/insights-client/.fallback.json
/etc/insights-client/.fallback.json.asc
/etc/insights-client/redhattools.pub.gpg

%defattr(-,root,root)
%{python_sitelib}/insights_client*.egg-info
%{python_sitelib}/insights_client/*.py*

%doc
/usr/share/man/man8/*.8.gz
/usr/share/man/man5/*.5.gz

%changelog
* Wed Jul 12 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.0-0
- Initial build
