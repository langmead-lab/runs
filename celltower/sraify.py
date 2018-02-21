#!/usr/bin/env python

from __future__ import print_function
import sys

for ln in sys.stdin:
    toks = ln.rstrip().split('\t')
    if len(toks) == 0:
	continue
    if toks[0].startswith('sra:'):
	print(ln, end='')
    srr = toks[-1].split('-')[1]
    assert srr[1:3] == 'RR'
    print('\t'.join(['sra:' + srr, '0', toks[-1]]))
