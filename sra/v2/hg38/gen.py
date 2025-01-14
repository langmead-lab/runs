#!/usr/bin/env python
"""
gen.py

Uses SraRunInfo.csv to creates manifest files and scripts for running Rail-RNA
on SRA RNA-seq data. SraRunInfo.csv was obtained by searching SRA
(http://www.ncbi.nlm.nih.gov/sra) for

(((((("platform illumina"[Properties]) AND "strategy rna seq"[Properties]) AND "human"[Organism])) AND "cluster public"[Properties]) AND "biomol rna"[Properties])

, as depicted in SRA_RNA-seq_search_screenshot_3.33.19_PM_ET_02.03.2016.png. By
default, 100 batches are created. Sample labels are exactly SRA run accession 
numbers. There are two scripts for analyzing the samples in each manifest
file: one for Rail's preprocess job flow, and the other for Rail's align job
flow.

We ran

python gen.py --s3-bucket s3://rail-sra-hg38 --region us-east-1
    --key useast1

and used Rail-RNA v0.2.2 . We executed each prep_gtex_batch_<index>.sh script
and waited for the job flow to finish before executing the corresponding
align_gtex_batch_<index>.sh script.
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
            default=0.25,
            help='bid price for each m3.xlarge instance; this instance '
                 'type is used for preprocessing data'
        )
    parser.add_argument('--c3-8xlarge-bid-price', type=float, required=False,
            default=1.70,
            help='bid price for each c3.2xlarge instance; this instance '
                 'type is used for aligning data'
        )
    parser.add_argument('--seed', type=int, required=False,
            default=12390423,
            help=('seed for random number generator; random.shuffle is used '
                  'to shuffle the SRA samples before dividing them up into '
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
    parser.add_argument('--key', type=str, required=False,
            default=None,
            help=('EC2 key name; do not specify if SSHing to cluster is '
                  'unnecessary')
        )
    parser.add_argument('--batch-count', type=int, required=False,
            default=100,
            help='number of batches to create; batches are designed to be '
                 'of approximately equal size'
        )
    args = parser.parse_args()
    manifest_lines = []
    import csv
    with open(args.run_info_path) as run_info_stream:
        run_info_stream.readline() # header line
        reader = csv.reader(run_info_stream)
        for tokens in reader:
            if not any(["http://sra-download.ncbi.nlm.nih.gov/srapub" in token
                        for token in tokens]):
                # no URL specified; ignore
                continue
            if tokens == ['']: break
            bases = int(tokens[4])
            manifest_lines.append((bases, '\t'.join(
                    ['sra:' + tokens[0], '0', tokens[0]]
                )))
    random.seed(args.seed)
    random.shuffle(manifest_lines)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    '''Write all manifest files; files in each manifest are listed in order of
    descending # of MB so biggest samples are downloaded first'''
    manifest_files = [[] for i in xrange(args.batch_count)]
    for i, manifest_index in enumerate(cycle(range(args.batch_count))):
        try:
            manifest_files[manifest_index].append(manifest_lines[i])
        except IndexError:
            # No more manifest lines
            break
    for i, manifest_file in enumerate(manifest_files):
        with open('sra_batch_{}.manifest'.format(i), 'w') as manifest_stream:
            for spots, line in sorted(
                                manifest_file, key=lambda x: x[0], reverse=True
                            ):
                print >>manifest_stream, line
    # Write all prep and align scripts
    for i in xrange(args.batch_count):
        with open('prep_sra_batch_{}.sh'.format(i), 'w') as prep_stream:
            print >>prep_stream, '#!/usr/bin/env bash'
            print >>prep_stream, (
                    'DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"'
                )
            print >>prep_stream, (
                    'rail-rna prep elastic -m $DIR/{manifest_file} '
                    '--skip-bad-records ' # precaution: bad records last run
                    '--ignore-missing-sra-samples '
                    '--core-instance-type m3.xlarge '
                    '--master-instance-type m3.xlarge '
                    '-o {s3_bucket}/sra_prep_batch_{batch_number} '
                    '-c 20 --core-instance-bid-price {core_price} '
                    '--master-instance-bid-price {core_price} -f '
                    '--max-task-attempts 6 '
                    '--region {region}'
                    '{key_name}'
                ).format(manifest_file='sra_batch_{}.manifest'.format(i),
                            s3_bucket=args.s3_bucket,
                            batch_number=i,
                            core_price=args.m3_xlarge_bid_price,
                            region=args.region,
                            key_name=((' --ec2-key-name ' + args.key)
                                        if args.key is not None else ''))
        with open('align_sra_batch_{}.sh'.format(i), 'w') as align_stream:
            print >>align_stream, '#!/usr/bin/env bash'
            print >>align_stream, (
                    'DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"'
                )
            print >>align_stream, (
                    'rail-rna align elastic -m $DIR/{manifest_file} '
                    '--core-instance-type c3.8xlarge '
                    '--master-instance-type c3.8xlarge '
                    '--junction-criteria .01,-1 '
                    '-c 80 -e --core-instance-bid-price {core_price} '
                    '--master-instance-bid-price {core_price} '
                    '-i {s3_bucket}/sra_prep_batch_{batch_number} '
                    '-o {s3_bucket}/sra_results_batch_{batch_number} '
                    '-a hg38 -f -d jx,tsv,bed,bw,idx '
                    '--max-task-attempts 6 '
                    '--region {region}'
                    '{key_name}'
                ).format(manifest_file='sra_batch_{}.manifest'.format(i),
                            s3_bucket=args.s3_bucket,
                            batch_number=i,
                            core_price=args.c3_8xlarge_bid_price,
                            region=args.region,
                            key_name=((' --ec2-key-name ' + args.key)
                                        if args.key is not None else ''))
