unit_sources = [
  'insights-client-boot.service',
  'insights-client.service',
  'insights-client.timer',
]

preset_sources = [
  '80-insights.preset'
]

unit_inputs = [
  'insights-client-results.service.in',
  'insights-client-results.path.in'
]

if get_option('auto_registration').enabled()
  unit_inputs += [
    'insights-register.service.in',
    'insights-register.path.in',
    'insights-unregister.service.in',
    'insights-unregister.path.in',
  ]
  preset_sources += '80-insights-register.preset'
endif

if get_option('checkin').enabled()
  unit_inputs += [
    'insights-client-checkin.service.in'
  ]
  unit_sources += 'insights-client-checkin.timer'
endif

foreach unit_input : unit_inputs
  unit_sources += configure_file(
    input: unit_input,
    output: '@BASENAME@',
    configuration: config_data,
  )
endforeach

install_data(
  unit_sources,
  install_dir: systemd.get_variable('systemdsystemunitdir')
)

install_data(
  preset_sources,
  install_dir: systemd.get_variable('systemdsystempresetdir')
)
