"""
gen.py

Uses SraRunInfo.csv to creates manifest files and scripts for running Rail-RNA
on GTEx RNA-seq data. SraRunInfo.csv was obtained by searching SRA for the GTEx
project number, (SRP012682) AND "strategy rna seq"[Properties], as depicted in
SRA_GTEx_search_screenshot_6.37.16_PM_ET_11.21.2015.png . This returns some
mmPCR samples, which are removed from consideration in the code here.
By default, 30 batches are created. Sample labels contain gender and tissue
metadata. There are two scripts for analyzing the samples in each manifest
file: one for Rail's preprocess job flow, and the other for Rail's align job
flow.

We ran

python gen.py --s3-bucket s3://dbgap-stack-361204003210 --region us-east-1
    --m3-xlarge-bid-price 0.25 --c3-8xlarge-bid-price 1.20
    --dbgap-key /Users/eterna/gtex/prj_8716.ngc
    --prep-stack-names dbgap-1 dbgap-2 dbgap-3 dbgap-4
    --align-stack-names dbgap-3
.

Use Rail-RNA v0.2.0a .
"""
import random
import sys
import os
from itertools import cycle
import re

if __name__ == '__main__':
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('--s3-bucket', type=str, required=True,
            help=('path to S3 bucket in which preprocessed data and junction '
                  'data will be dumped; should be a secure bucket created '
                  'by following the instructions at '
                  'http://docs.rail.bio/dbgap/; ours was s3://rail-dbgap')
        )
    parser.add_argument('--region', type=str, required=True,
            help='AWS region in which to run job flows; we used us-east-1'
        )
    parser.add_argument('--m3-xlarge-bid-price', type=float, required=False,
            default=0.20,
            help='bid price for each m3.xlarge instance; this instance '
                 'type is used for preprocessing data'
        )
    parser.add_argument('--c3-8xlarge-bid-price', type=float, required=False,
            default=1.20,
            help='bid price for each c3.2xlarge instance; this instance '
                 'type is used for aligning data'
        )
    parser.add_argument('--prep-stack-names', type=str, required=False,
            default='dbgap', nargs='+',
            help='stack name(s) for prep job flow; cycle through them'
        )
    parser.add_argument('--align-stack-names', type=str, required=False,
            default='dbgap', nargs='+',
            help='stack name(s) for align job flow; cycle through them'
        )
    parser.add_argument('--seed', type=int, required=False,
            default=4523,
            help=('seed for random number generator; random.shuffle is used '
                  'to shuffle the GTEx samples before dividing them up into '
                  '--batch-count batches')
        )
    parser.add_argument('--run-info-path', type=str, required=False,
            default=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'SraRunInfo.csv'
                ),
            help=('path to SraRunInfo.csv generated by searching SRA '
                  'as depicted in the screenshot '
                  'SRA_GTEx_search_screenshot_6.37.16_PM_ET_11.21.2015.png')
        )
    parser.add_argument('--batch-count', type=int, required=False,
            default=30,
            help='number of batches to create; batches are designed to be '
                 'of approximately equal size'
        )
    parser.add_argument('--dbgap-key', type=str, required=True,
            help='path to dbGaP key giving access to GTEx project; this '
                 'should be an NGC file'
        )
    args = parser.parse_args()
    manifest_lines = []
    with open(args.run_info_path) as run_info_stream:
        run_info_stream.readline() # header line
        for line in run_info_stream:
            if '_rep1' in line or '_rep2' in line:
                # mmPCR sample
                continue
            tokens = line.strip().split(',')
            if tokens == ['']: break
            spots = int(tokens[5])
            manifest_lines.append((spots, '\t'.join(
                    ['dbgap:' + tokens[0], '0', 
                     '_'.join([tokens[0], tokens[26], tokens[12],
                                tokens[36],
                                re.sub('[^a-zA-Z\d:]+', '.',
                                            tokens[42].lower().strip()
                                            ).strip('.')])]
                )))
    random.seed(args.seed)
    random.shuffle(manifest_lines)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    '''Write all manifest files; files in each manifest are listed in order of
    descending # of spots so biggest samples are downloaded first'''
    manifest_files = [[] for i in xrange(args.batch_count)]
    for i, manifest_index in enumerate(cycle(range(args.batch_count))):
        try:
            manifest_files[manifest_index].append(manifest_lines[i])
        except IndexError:
            # No more manifest lines
            break
    for i, manifest_file in enumerate(manifest_files):
        with open('gtex_batch_{}.manifest'.format(i), 'w') as manifest_stream:
            for spots, line in sorted(
                                manifest_file, key=lambda x: x[0], reverse=True
                            ):
                print >>manifest_stream, line
    # Write all prep and align scripts
    prep_stack_name_cycle = cycle(args.prep_stack_names)
    align_stack_name_cycle = cycle(args.align_stack_names)
    for i in xrange(args.batch_count):
        with open('prep_gtex_batch_{}.sh'.format(i), 'w') as prep_stream:
            print >>prep_stream, '#!/usr/bin/env bash'
            print >>prep_stream, (
                    'DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"'
                )
            print >>prep_stream, (
                    'rail-rna prep elastic -m $DIR/{manifest_file} '
                    '--profile dbgap --secure-stack-name {stack_name} '
                    '--dbgap-key {dbgap_key} --core-instance-type m3.xlarge '
                    '--master-instance-type m3.xlarge '
                    '-o {s3_bucket}/gtex_prep_batch_{batch_number} '
                    '-c 20 --core-instance-bid-price {core_price} '
                    '--master-instance-bid-price {core_price} -f '
                    '--max-task-attempts 6'
                ).format(manifest_file='gtex_batch_{}.manifest'.format(i),
                            dbgap_key=args.dbgap_key,
                            s3_bucket=args.s3_bucket,
                            batch_number=i,
                            core_price=args.m3_xlarge_bid_price,
                            stack_name=next(prep_stack_name_cycle))
        with open('align_gtex_batch_{}.sh'.format(i), 'w') as align_stream:
            print >>align_stream, '#!/usr/bin/env bash'
            print >>align_stream, (
                    'DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"'
                )
            print >>align_stream, (
                    'rail-rna align elastic -m $DIR/{manifest_file} '
                    '--profile dbgap --secure-stack-name {stack_name} '
                    '--core-instance-type c3.8xlarge '
                    '--master-instance-type c3.8xlarge '
                    '-c 80 --core-instance-bid-price {core_price} '
                    '--master-instance-bid-price {core_price} '
                    '-i {s3_bucket}/gtex_prep_batch_{batch_number} '
                    '-o {s3_bucket}/gtex_align_batch_{batch_number} '
                    '-a hg38 -f -d jx,tsv,bed,bw,idx '
                    '--max-task-attempts 6'
                ).format(manifest_file='gtex_batch_{}.manifest'.format(i),
                            s3_bucket=args.s3_bucket,
                            batch_number=i,
                            core_price=args.c3_8xlarge_bid_price,
                            stack_name=next(align_stack_name_cycle))