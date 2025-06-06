sysconf_sources = [
  '.fallback.json',
  '.fallback.json.asc',
  'cert-api.access.redhat.com.pem',
  'insights-client.conf',
  'insights-client.motd',
  'redhattools.pub.gpg',
  'rpm.egg',
  'rpm.egg.asc'
]

install_data(
  sysconf_sources,
  install_dir: get_option('sysconfdir') / 'insights-client'
)

subdir('logrotate.d')
subdir('systemd')
subdir('tmpfiles.d')
