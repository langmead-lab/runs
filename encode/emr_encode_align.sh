#!/bin/sh

INSTANCE_TYPE="cc2.8xlarge"
MASTER_PRICE="2.10"
PRICE="0.35"
# (0.35 + 0.27) * 32 = $20
INSTANCES="--core-instance-bid-price ${PRICE} --core-instance-type ${INSTANCE_TYPE}
           --task-instance-bid-price ${PRICE} --task-instance-type ${INSTANCE_TYPE}
           --master-instance-bid-price ${MASTER_PRICE} --master-instance-type ${INSTANCE_TYPE}"
REGION="us-east-1"
NM="encode"
LNM="encode_1159"
BUCKET="langmead-${NM}-2017"
MANIFEST="s3://${BUCKET}/${LNM}/manifest/${NM}.manifest"
PREPROC="s3://${BUCKET}/${LNM}/preproc_01"  # will edit the JSON to point to 10 dirs
KEYPAIR_NAME="default"
PID_ARGS="--thread-ceiling 32"
NWORKERS=64  # ~2000 cores

aws s3 cp "${LNM}.manifest" "${MANIFEST}"

# This doesn't seem ready for prime time yet
#    --genome-bowtie1-args "${PID_ARGS} --thread-piddir /tmp/genome-bowtie1-pid-tmp" \

python $HOME/git/rail-langmead/src align elastic \
    -m ${MANIFEST} \
    -i ${PREPROC} \
    --intermediate s3://${BUCKET}/${LNM}/intermediate \
    -o s3://${BUCKET}/${LNM}/output \
    -a hg38 \
    --drop-deletions \
    --region ${REGION} \
    ${INSTANCES} \
    -c ${NWORKERS} \
    --ec2-key-name "${KEYPAIR_NAME}" \
    --intermediate-lifetime 30 \
    --name "ENCODE align" \
    --transcriptome-bowtie2-args "${PID_ARGS} --thread-piddir /tmp/transcriptome-bowtie2-pid-tmp" \
    --bowtie2-args "${PID_ARGS} --thread-piddir /tmp/bowtie2-pid-tmp" \
    --max-task-attempts 6 \
    $*
