project('insights-client',
  version: '3.10.1',
  meson_version: '>=0.49'
)

python = import('python')

python_installation = python.find_installation(get_option('python'))

python_exec = '/usr/bin/python3'

systemd = dependency('systemd', version: '>=231')

config_data = configuration_data({
  'bindir': get_option('prefix') / get_option('bindir'),
  'BINDIR': get_option('prefix') / get_option('bindir'),
  'DATADIR': get_option('prefix') / get_option('datadir'),
  'DATAROOTDIR':get_option('prefix') / get_option('datadir'),
  'DOCDIR': get_option('prefix') / get_option('datadir') / 'doc' / meson.project_name(),
  'LIBEXECDIR': get_option('prefix') / get_option('libexecdir'),
  'LOCALSTATEDIR': get_option('localstatedir'),
  'PACKAGE': meson.project_name(),
  'PACKAGE_VERSION': meson.project_version(),
  'pkgsysconfdir': '/' / get_option('sysconfdir') / meson.project_name(),
  'PREFIX': get_option('prefix'),
  'PYTHON': python_exec,
  'pythondir': python_installation.get_install_dir(),
  'SBINDIR': get_option('prefix') / get_option('sbindir'),
  'SYSCONFDIR': '/' / get_option('sysconfdir'),
  'sysconfdir': '/' / get_option('sysconfdir'),
  'top_srcdir': meson.source_root(),
  'CORE_SELINUX_POLICY': get_option('core_selinux_policy'),
})

run_target('update-egg', command: 'scripts/01-upgrade-egg.sh')

subdir('data')
subdir('docs')
subdir('src')

configuration = '**Configuration**\n'
configuration += '\tpython\t\t\t: ' + get_option('python') + '\n'
if get_option('checkin').enabled()
 configuration += '\tcheckin\t: ' + 'enabled' + '\n'
else
 configuration += '\tcheckin\t: ' + 'disabled' + '\n'
endif
if get_option('auto_registration').enabled()
  configuration += '\tauto_registration\t: ' + 'enabled' + '\n'
else 
  configuration += '\tauto_registration\t: ' + 'disabled' + '\n'
endif
if get_option('core_selinux_policy') != ''
  configuration += '\tSELinux policy for insights-core\t: ' + get_option('core_selinux_policy') + '\n'
else
  configuration += '\tSELinux policy for insights-core\t: ' + 'disabled' + '\n'
endif
message(configuration)
