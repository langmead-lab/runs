#!/usr/bin/env python
"""
phylop.py

Computes mean phyloP scores +/- N bases from 3' and 5' splice sites for 
annotated/unannotated junctions in >= K samples.

Requires pyBigWig v0.2.7 (https://github.com/dpryan79/pyBigWig)
"""
import gzip
import tempfile
import atexit
import shutil
import multiprocessing
import glob
import time
import itertools
import shutil
import sys
import os
import subprocess
from collections import defaultdict
import math

def subprocess_wrapper(command):
    """ Wraps subprocess.check_call so exceptions can be handled cleanly.

        command: command to run

        Return value: 0 if successful; else error
    """
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        return '"{}" returned exit code {}.'.format(command, e.returncode)
    return 0

def write_incidence_file(input_file, min_samples, sort_exe):
    """ Writes number of samples in which each splice site is found

        input_file: file with coordinate as first field and comma-separated
            list of sample indexes as second field
        min_samples: minimum number of samples in which splice site should
            appear to be analyzed
        sort_exe: path to sort executable

        No return value.
    """
    try:
        prefix = '\t'.join(os.path.basename(input_file).split('.')[:-1])
        with open(
                input_file
            ) as input_stream, open(
                input_file + '.incidence', 'w'
            ) as output_stream:
            for key, group in itertools.groupby(
                            input_stream, key=lambda x: x.split('\t')[0]
                        ):
                samples = set()
                for line in group:
                    samples.update(line.split('\t')[1].split(','))
                sample_count = len(samples)
                if sample_count >= min_samples:
                    print >>output_stream, '\t'.join(
                                            [str(len(samples)), prefix, key]
                                        )
        subprocess.check_call('{} -T {} -k1,1nr {} >{}'.format(
                                        sort_exe,
                                        os.path.dirname(input_file),
                                        input_file + '.incidence',
                                        input_file + '.incidence.sorted'
                                    ), shell=True)
        os.remove(input_file + '.incidence')
    except Exception as e:
        return e.message
    return 0

if __name__ == '__main__':
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('--junctions', type=str, required=True,
            help='junctions file; this should be intropolis.v2.hg38.tsv.gz'
        )
    parser.add_argument('--phylop-bw', type=str, required=True,
            help='phylop bigwigs; should be one of '
                 'hg38.phyloP100way.bw, hg38.phyloP20way.bw, '
                 'hg38.phyloP100way.bw'
        )
    parser.add_argument('--temp-dir', type=str, required=False,
            default=None,
            help='path to where temporary files should be stored'
        )
    parser.add_argument('--annotation', type=str, required=True,
            help=('path to annotated_junctions.tsv.gz; defined in '
                  'annotation_definition.md')
        )
    parser.add_argument('--out', type=str, required=True,
            help='output basename'
        )
    parser.add_argument('--sort', type=str, required=False,
            help='path to sort executable'
        )
    parser.add_argument('-p', '--num-processes', type=int, required=False,
            default=1,
            help='maximum number of processes to run simultaneously'
        )
    parser.add_argument('--extension', type=int, required=False,
            default=50,
            help='number of bases on either side of splice site to study'
        )
    parser.add_argument('--min-samples', type=int, required=False,
            default=100,
            help=('min number of sample in which splice site should appear to '
                  'be analyzed')
        )
    args = parser.parse_args()
    temp_dir = tempfile.mkdtemp(dir=args.temp_dir)
    #atexit.register(shutil.rmtree, temp_dir, ignore_errors=True)
    # First count number of samples in which each splice site is found
    handles = {}
    print >>sys.stderr, '\x1b[KDistributing splice sites across tasks...'
    try:
        with gzip.open(args.junctions) as junction_stream:
            for k, line in enumerate(junction_stream):
                print >>sys.stderr, (
                        'Processed {} junctions...\r'.format(k)
                    ),
                tokens = line.strip().split('\t')
                strand = tokens[3]
                for left_or_right, index in [('l', 1), ('r', 2)]:
                    try:
                        print >>handles[(tokens[0], left_or_right
                                                    + strand)], '\t'.join(
                                                    [tokens[index],
                                                        tokens[6]]
                                                )
                    except KeyError:
                        handles[(tokens[0], left_or_right
                                            + strand)] = open(
                                            os.path.join(temp_dir,
                                                    '.'.join([
                                                        tokens[0],
                                                        left_or_right,
                                                        strand,
                                                        'unsorted'
                                                ])
                                            ), 'w'
                                        )
                        print >>handles[(tokens[0], left_or_right
                                                    + strand)], '\t'.join(
                                                    [tokens[index],
                                                        tokens[6]]
                                                )
    finally:
        for handle in handles:
            handles[handle].close()
    pool = multiprocessing.Pool(args.num_processes)
    return_values = []
    to_sort = glob.glob(os.path.join(temp_dir, '*.unsorted'))
    total_files = len(to_sort)
    for unsorted_file in to_sort:
        pool.apply_async(
                subprocess_wrapper,
                args=(
                    '{sort_exe} -T {temp_dir} -k1,1 {unsorted} >{dest}'.format(
                        sort_exe=args.sort,
                        temp_dir=temp_dir,
                        unsorted=unsorted_file,
                        dest='.'.join(
                                unsorted_file.split('.')[:-1] + ['sorted']
                            )
                    ),), callback=return_values.append
            )
    print >>sys.stderr, '\x1b[KDone. Sorting tasks...'
    while len(return_values) < total_files:
        print >>sys.stderr, '\x1b[K{}/{} tasks complete.\r'.format(
                len(return_values),
                total_files
            ),
        if not all([return_value == 0 for return_value in return_values]):
            for return_value in return_values:
                if return_value != 0:
                    raise RuntimeError('Error during sorting: "{}".'.format(
                                                return_value
                                            ))
        time.sleep(4)
    if not all([return_value == 0 for return_value in return_values]):
        for return_value in return_values:
            if return_value != 0:
                raise RuntimeError('Error during sorting: "{}".'.format(
                                            return_value
                                        ))
    for unsorted_file in to_sort:
        os.remove(unsorted_file)
    print >>sys.stderr, (
            '\x1b[KCompleted sorting. Computing splice site incidences...'
        )
    return_values = []
    to_incidence = glob.glob(os.path.join(temp_dir, '*.sorted'))
    total_files = len(to_incidence)
    for sorted_file in to_incidence:
        pool.apply_async(
                write_incidence_file,
                args=(sorted_file, args.min_samples, args.sort),
                callback=return_values.append
            )
    while len(return_values) < total_files:
        print >>sys.stderr, '\x1b[K{}/{} tasks complete.\r'.format(
                len(return_values),
                total_files
            ),
        if not all([return_value == 0 for return_value in return_values]):
            for return_value in return_values:
                if return_value != 0:
                    raise RuntimeError('Error during incidence computation: '
                                       '"{}".'.format(
                                                return_value
                                            ))
        time.sleep(4)
    if not all([return_value == 0 for return_value in return_values]):
        for return_value in return_values:
            if return_value != 0:
                raise RuntimeError('Error during incidence computation: '
                                   '"{}".'.format(
                                            return_value
                                        ))
    pool.close()
    pool.join()
    allincidence = os.path.join(temp_dir, 'allincidence.temp')
    print >>sys.stderr, '\x1b[KDone. Merging splice site incidence files...'
    subprocess.check_call('{} -T {} -m -k1,1nr {} >{}'.format(
                                args.sort,
                                temp_dir,
                                os.path.join(temp_dir, '*.incidence.sorted'),
                                os.path.join(temp_dir, 'allincidence.temp')
                            ), shell=True)
    print >>sys.stderr, '\x1b[KDone. Reading annotated splice sites...'
    annotated_5p = set()
    annotated_3p = set()
    with gzip.open(args.annotation) as annotated_stream:
        for line in annotated_stream:
            tokens = line.strip().split('\t')
            if tokens[3] == '+':
                annotated_5p.add((tokens[0], int(tokens[1]) - 1))
                annotated_3p.add((tokens[0], int(tokens[2]) - 1))
            elif tokens[3] == '-':
                annotated_3p.add((tokens[0], int(tokens[1]) - 1))
                annotated_5p.add((tokens[0], int(tokens[2]) - 1))
            else:
                raise RuntimeError(
                        'Invalid line in annotation file: "{}".'.format(line)
                    )
    unannotated_fivep_splice_site_counts = defaultdict(int)
    unannotated_threep_splice_site_counts = defaultdict(int)
    annotated_fivep_splice_site_counts = defaultdict(int)
    annotated_threep_splice_site_counts = defaultdict(int)
    from bx.bbi.bigwig_file import BigWigFile
    bw = BigWigFile(open(args.phylop_bw, 'rb'))
    print >>sys.stderr, '\x1b[KDone. Computing/writing matrix elements...'
    with open(
            allincidence
        ) as incidence_stream, open(
            args.out, 'w'
        ) as output_stream:
        unannotated_line_counts = defaultdict(int)
        annotated_line_counts = defaultdict(int)
        splice_sites = 0
        for key, group in itertools.groupby(
                                incidence_stream, lambda x: x.split('\t')[0]
                            ):
            for line in group:
                print >>sys.stderr, (
                        'Processed {} splice sites...\r'.format(
                                                                splice_sites
                                                            )
                    ),
                splice_sites += 1
                tokens = line.strip().split('\t')
                _, chrom, left_or_right, strand, coordinate = tokens
                coordinate = int(coordinate) - 1
                if (left_or_right == 'l' and strand == '+'
                    or left_or_right == 'r' and strand == '-'):
                    # 5' site
                    if (chrom, coordinate) in annotated_5p:
                        fivep_splice_site_counts = (
                                annotated_fivep_splice_site_counts
                            )
                        line_counts = annotated_line_counts
                    else:
                        fivep_splice_site_counts = (
                                unannotated_fivep_splice_site_counts
                            )
                        line_counts = unannotated_line_counts
                    if strand == '+':
                        bwvals = bw.get_as_array(
                                    chrom,
                                    coordinate - args.extension,
                                    coordinate + args.extension
                                )
                        if bwvals is None:
                            continue
                        for i, j in enumerate(
                                        xrange(-args.extension, args.extension)
                                    ):
                            if not math.isnan(bwvals[i]):
                                fivep_splice_site_counts[j] += bwvals[i]
                                line_counts[j] += 1
                    elif strand == '-':
                        bwvals = bw.get_as_array(
                                    chrom,
                                    coordinate - (args.extension - 1),
                                    coordinate + (args.extension + 1)
                                )
                        if bwvals is None:
                            continue
                        for i, j in enumerate(
                                        xrange(-args.extension, args.extension)
                                    ):
                            if not math.isnan(bwvals[-i-1]):
                                fivep_splice_site_counts[j] += bwvals[-i-1]
                                line_counts[j] += 1
                    else:
                        raise RuntimeError(
                                'Strand {} is neither + nor -.'.format(
                                        strand
                                    )
                            )
                else:
                    # 3' site
                    if (chrom, coordinate) in annotated_3p:
                        threep_splice_site_counts = (
                                annotated_threep_splice_site_counts
                            )
                        line_counts = annotated_line_counts
                    else:
                        threep_splice_site_counts = (
                                unannotated_threep_splice_site_counts
                            )
                        line_counts = unannotated_line_counts
                    if strand == '+':
                        bwvals = bw.get_as_array(
                                    chrom,
                                    coordinate - (args.extension - 1),
                                    coordinate + (args.extension + 1)
                                )
                        if bwvals is None:
                            continue
                        for i, j in enumerate(
                                        xrange(-args.extension, args.extension)
                                    ):
                            if not math.isnan(bwvals[i]):
                                threep_splice_site_counts[j] += bwvals[i]
                                line_counts[j] += 1
                    elif strand == '-':
                        bwvals = bw.get_as_array(
                                    chrom,
                                    coordinate - args.extension,
                                    coordinate + args.extension
                                )
                        if bwvals is None:
                            continue
                        for i, j in enumerate(
                                        xrange(-args.extension, args.extension)
                                    ):
                            if not math.isnan(bwvals[-i-1]):
                                threep_splice_site_counts[j] += bwvals[-i-1]
                                line_counts[j] += 1
            # Print only if we won't get a ZeroDivisionError
            try:
                print >>output_stream, '\t'.join([key + '.3p'] + [
                            str(float(unannotated_threep_splice_site_counts[i])
                                / unannotated_line_counts[i])
                        for i in xrange(
                            -args.extension, args.extension
                        )])
                print >>output_stream, '\t'.join([key + '.5p'] + [
                            str(float(unannotated_fivep_splice_site_counts[i])
                                / unannotated_line_counts[i])
                        for i in xrange(
                            -args.extension, args.extension
                        )])
            except ZeroDivisionError:
                pass
        try:
            # Print only if we won't get a ZeroDivisionError
            print >>output_stream, '\t'.join(['annotated.3p'] + [
                        str(float(annotated_threep_splice_site_counts[i])
                             / annotated_line_counts[i])
                    for i in xrange(
                        -args.extension, args.extension
                    )])
            print >>output_stream, '\t'.join(['annotated.5p'] + [
                        str(float(annotated_fivep_splice_site_counts[i])
                            / annotated_line_counts[i])
                    for i in xrange(
                        -args.extension, args.extension
                    )])
        except ZeroDivisionError:
            pass
    print >>sys.stderr, '\x1b[KDone.'
