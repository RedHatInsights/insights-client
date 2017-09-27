%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define _binaries_in_noarch_packages_terminate_build 0

%global insights_user  insights
%global insights_group %{insights_user}

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.0.0
Release:                2%{?dist}
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
Requires: PyYAML
Requires: pyOpenSSL
Requires: libcgroup
Requires: tar
Requires: gpg
Requires: pciutils
%if 0%{?rhel} && 0%{?rhel} == 6
Requires: python-argparse
%endif
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

%pre
getent group insights > /dev/null || /usr/sbin/groupadd -r %{insights_group}
getent passwd insights > /dev/null || \
    /usr/sbin/useradd -g insights -r --shell /sbin/nologin %{insights_user} \
    -c "Red Hat Insights" -d /var/lib/insights

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
# Symlink new cron job if the old one exists. Remove the old one
if [ -f "/etc/cron.daily/redhat-access-insights" ]; then
rm -f /etc/cron.daily/redhat-access-insights
ln -sf /etc/insights-client/insights-client.cron /etc/cron.daily/insights-client                               
fi 
ln -sf /etc/insights-client/insights-client.conf /etc/redhat-access-insights/redhat-access-insights.conf
ln -sf /etc/insights-client/insights-client.cron /etc/redhat-access-insights/redhat-access-insights.cron
ln -sf /etc/insights-client/.registered /etc/redhat-access-insights/.registered
ln -sf /etc/insights-client/.unregistered /etc/redhat-access-insights/.unregistered
ln -sf /etc/insights-client/machine-id /etc/redhat-access-insights/machine-id

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

%postun
if [ "$1" -eq 0 ]; then
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

%attr(440,root,root) /etc/insights-client/*.pem
%attr(440,root,root) /etc/insights-client/redhattools.pub.gpg

%attr(755,root,root) %{_bindir}/insights-client
%attr(755,root,root) %{_bindir}/insights-client-run
%attr(755,root,root) /etc/insights-client/insights-client.cron

%attr(644,root,root) /etc/insights-client/rpm.egg
%attr(644,root,root) /etc/insights-client/rpm.egg.asc

%attr(755,root,root) %dir %{python_sitelib}/insights_client*.egg-info
%attr(644,root,root) %{python_sitelib}/insights_client*.egg-info/*
%attr(644,root,root) %{python_sitelib}/insights_client/*.py*

%doc
/usr/share/man/man8/*.8.gz
/usr/share/man/man5/*.5.gz

%changelog
* Wed Sep 27 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.0-2
- Initial build
