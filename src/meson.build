insights_client_sources = [
  'insights-client.in',
]

if get_option('redhat_access_insights')
  insights_client_sources += 'redhat-access-insights.in'
endif

foreach source : insights_client_sources
  configure_file(
    input: source,
    output: '@BASENAME@',
    configuration: config_data,
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x'
  )
endforeach

subdir('insights_client')
