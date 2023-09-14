project('insights-client',
  version: '3.2.2',
  meson_version: '>=0.58.0'
)

python = import('python')

python_installation = python.find_installation(get_option('python'))
systemd = dependency('systemd', version: '>=231', required: false)

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
  'PYTHON': python_installation.full_path(),
  'pythondir': python_installation.get_install_dir(),
  'SBINDIR': get_option('prefix') / get_option('sbindir'),
  'SYSCONFDIR': '/' / get_option('sysconfdir'),
  'sysconfdir': '/' / get_option('sysconfdir'),
  'top_srcdir': meson.project_source_root()
})

run_target('update-egg', command: 'scripts/01-upgrade-egg.sh')

subdir('data')
subdir('docs')
subdir('src')

summary({
  'python': get_option('python'),
  'auto_registration': get_option('auto_registration'),
  'checkin': get_option('checkin'),
}, section: 'Configuration')
