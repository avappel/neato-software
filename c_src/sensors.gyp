{
  'targets': [
    {
      'target_name': 'swig_sensors',
      'type': 'shared_library',
      'cflags': [
        '-fPIC',
        '-I"/usr/include/python2.7"',
      ],
      'ldflags': [
        '-lpruio',
        '-lpthread',
        '-lprussdrv',
        '-ltermcap',
        '-lsupc++',
        '-L"/usr/local/lib/freebasic"',
        '-lfbpic',
      ],
      'sources': [
        'sensors.c',
        'sensors_wrap.c',
      ],
      'actions': [
        {
          'action_name': 'swig',
          'inputs': [
            'sensors.i',
          ],
          'outputs': [
            'sensors_wrap.c',
            'sensors.py',
          ],
          'action': ['swig', '-python', '<@(_inputs)'],
        },
      ],
    },
  ],
}
