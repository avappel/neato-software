{
  'targets': [
    {
      'target_name': 'sensors',
      'type': 'shared_library',
      'cflags': [
        '-fPIC',
      ],
      'ldflags': [
        '-lpruio',
        '-lpthread',
        '-lprussdrv',
        '-ltermcap',
        '-lsupc++',
      ],
      'sources': [
        'sensors.c',
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
