insights_client_sources = [
  '__init__.py',
  'run.py',
  'utc.py'
]

insights_client_sources += configure_file(
  input: 'constants.py.in',
  output: '@BASENAME@',
  configuration: config_data
)

python_installation.install_sources(insights_client_sources, subdir: 'insights_client')

subdir('tests')
