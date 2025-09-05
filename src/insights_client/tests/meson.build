pytest = find_program('pytest', 'pytest-3')

env = environment()
env.append('PYTHONPATH', meson.source_root() / 'src')

test_sources = files('test_client.py', 'test_commands.py')

test('test',
  pytest,
  args: test_sources,
  env: env
)
