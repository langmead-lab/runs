#!/usr/bin/env python

# See instructions here: http://www.ebi.ac.uk/ena/browse/read-download

import sys

for ln in sys.stdin:
    # ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR594/SRR594397/SRR594397_1.fastq.gz
    # sra:SRR594397
    ln = ln.rstrip()
    toks = ln.split('\t')
    srr = toks[0][4:]
    srr_pre = srr[:6]
    if len(srr) == 10:
        srr00 = '00' + srr[-1]
        url = 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/%s/%s/%s/%s' % (srr_pre, srr00, srr, srr)
        print('\t'.join([url + '_1.fastq.gz', '0', url + '_2.fastq.gz', '0', toks[-1]]))
    else:
        url = 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/%s/%s/%s' % (srr_pre, srr, srr)
        print('\t'.join([url + '_1.fastq.gz', '0', url + '_2.fastq.gz', '0', toks[-1]]))
