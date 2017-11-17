#!/usr/bin/env python

"""
Author: Ben Langmead
  Date: 6/5/2017

Given a list of run accessions and corresponding run names on standard in, e.g.:

---
SRR32128090 SRP071321-PCells-16
SRR32128140 SRP071321-PCells-17
SRR32128150 SRP071321-PCells-18
---

...this script generates a manifest file with URLs for each, preferring ENA over
SRA where possible.  Prints manifest to standard out and a metadata table to
standard error.

TODO:
- Get MD5s if available

For instructions on how to turn a run accession into a valid ENA URL, see:
http://www.ebi.ac.uk/ena/browse/read-download
"""

from __future__ import print_function
import subprocess
import os
import sys
import requests

query = []

def url_exists(url_dir, verbose=False):
    cmd = "curl " + url_dir + "/ 2>/dev/null | awk '{print $NF}' >.tmp.txt"
    if verbose:
        print(cmd, file=sys.stderr)
    ret = os.system(cmd)
    if ret != 0:
        return []
    rec = [None, None, None]
    with open('.tmp.txt') as fh:
        for ln in fh:
            ln = ln.rstrip()
            if ln.endswith('_1.fastq.gz'):
                rec[1] = url_dir + '/' + ln
            elif ln.endswith('_2.fastq.gz'):
                rec[2] = url_dir + '/' + ln
            else:
                assert ln.endswith('.fastq.gz')
                rec[0] = url_dir + '/' + ln
    return rec


for ln in sys.stdin:
    ln = ln.rstrip()
    toks = ln.split()
    srr = toks[0]
    if srr.startswith('sra:'):
        srr = srr[4:]
    query.append(srr)
    srr_pre = srr[:6]
    if len(srr) == 10:
        srr00 = '00' + srr[-1]
        url = 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/%s/%s/%s' % (srr_pre, srr00, srr)
    else:
        url = 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/%s/%s' % (srr_pre, srr)
    rec = url_exists(url)
    if len(rec) > 0 and (rec[0] is not None or rec[1] is not None):
        if rec[1] is not None:
            assert rec[2] is not None
            print('\t'.join([rec[1], '0', rec[2], '0', toks[-1]]))
        else:
            print('\t'.join([rec[0], '0', toks[-1]]))
    else:
        print('\t'.join(['sra:' + srr, '0', toks[-1]]))

batch_size = 50

i = 0
sra_url = 'https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi'
while i < len(query):
    #keep header if first pass chunk
    if i == 0:
        cmd = "curl -s '%s?save=efetch&db=sra&rettype=runinfo&term=%s' | grep -v -e '^$'" % (sra_url, '|'.join(query[i:i+batch_size]))
    #dump header and any empty lines for 2nd* chunks
    else:
        cmd = "curl -s '%s?save=efetch&db=sra&rettype=runinfo&term=%s' | grep -v -e 'Run,ReleaseDate,LoadDate,spots,bases' | grep -v -e '^$'" % (sra_url, '|'.join(query[i:i+batch_size]))
    o, e = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    sys.stderr.write(o)
    i += batch_size
