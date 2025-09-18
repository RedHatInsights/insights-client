sysconf_sources = [
  'cert-api.access.redhat.com.pem',
  'insights-client.conf',
  'insights-client.motd',
  'redhattools.pub.gpg'
]

install_data(
  sysconf_sources,
  install_dir: get_option('sysconfdir') / 'insights-client'
)

subdir('logrotate.d')
subdir('systemd')
subdir('tmpfiles.d')
