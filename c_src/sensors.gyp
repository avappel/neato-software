{
  'targets': [
    {
      'target_name': 'sensors',
      'type': 'executable',
      'ldflags': [
        '-lpruio',
        '-L"/usr/local/lib/freebasic/"',
        '-lfb',
        '-lpthread',
        '-lprussdrv',
        '-ltermcap',
        '-lsupc++',
      ],
      'sources': [
        'sensors.c',
      ],
    },
  ],
}
