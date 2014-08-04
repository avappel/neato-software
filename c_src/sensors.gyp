{
  'targets': [
    {
      'target_name': 'swig_pru',
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
        'pru.c',
        'pru_wrap.c',
      ],
      'actions': [
        {
          'action_name': 'swig',
          'inputs': [
            'pru.i',
          ],
          'outputs': [
            'pru_wrap.c',
            'pru.py',
          ],
          'action': ['swig', '-python', '<@(_inputs)'],
        },
      ],
    },
  ],
}
