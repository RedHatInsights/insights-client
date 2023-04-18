insights_client_sources = [
  'insights-client.in',
  'redhat-access-insights.in'
]

foreach source : insights_client_sources
  configure_file(
    input: source,
    output: '@BASENAME@',
    configuration: config_data,
    install_dir: get_option('bindir')
  )
endforeach

subdir('insights_client')
