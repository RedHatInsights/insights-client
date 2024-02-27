pytest = find_program('pytest', 'pytest-3')

env = environment()
env.append('PYTHONPATH', meson.source_root() / 'src', meson.source_root() / 'data' / 'rpm.egg')

test_sources = files('test_client.py', 'test_commands.py', 'test_sed.py')

test('test',
  pytest,
  args: test_sources,
  env: env
)
