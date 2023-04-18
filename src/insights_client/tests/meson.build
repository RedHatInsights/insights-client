pytest = find_program('pytest', 'pytest-3')
sed = find_program('sed')

env = environment()
env.append('PYTHONPATH', meson.project_source_root() / 'src', meson.project_source_root() / 'data' / 'rpm.egg')

test_sources = files('test_client.py', 'test_commands.py')

test_sources += configure_file(
  input: 'test_sed.py.in',
  output: '@BASENAME@',
  configuration: config_data
)

test('test',
  pytest,
  args: test_sources,
  env: env
)
