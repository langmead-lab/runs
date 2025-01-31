#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# based on http://stackoverflow.com/questions/4632028/how-to-create-a-temporary-directory
WORKDIR=$(mktemp -d)

# deletes the temp directory
function cleanup {
  rm -rf $WORKDIR
  echo "Deleted temp working directory $WORKDIR"
}

# register the cleanup function to be called on the EXIT signal
trap cleanup EXIT
cat tcga_batch_6.manifest | python $DIR/true_manifest.py --cgc-auth-token /Users/eterna/cgcauth.txt >$WORKDIR/tcga_batch_6.manifest
rail-rna prep elastic -m $WORKDIR/tcga_batch_6.manifest --profile dbgap --secure-stack-name dbgap-us-east-1d --core-instance-type c3.2xlarge --master-instance-type c3.2xlarge -o s3://sb-rail-rna-mapreduce/tcga_prep_batch_6 -c 48 --core-instance-bid-price 0.5 --master-instance-bid-price 0.5 -f --max-task-attempts 10 --skip-bad-records --do-not-check-manifest --name TCGA_prep_batch_6_job_flow

