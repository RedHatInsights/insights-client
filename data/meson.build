sysconf_sources = [
  '.exp.sed',
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
if systemd.found()
  subdir('systemd')
else
  subdir('cron')
endif
