#!/usr/bin/env python
# encoding: utf-8


import random
import sys
import os


def sample(filepath, n=100):
    blocks = ['# %s_%07d\n%s' %(os.path.basename(filepath), i, b) for i, b in
              enumerate(open(filepath).read().split('\n\n'), 1)]
    print '\n\n'.join(random.sample(blocks, n))


if __name__ == '__main__':
    sample(sys.argv[1])
