#!/bin/sh

# Instance types and bid prices
INSTANCE_TYPE="c4.8xlarge"
PRICE="0.50"
INSTANCES="--core-instance-bid-price ${PRICE} --core-instance-type ${INSTANCE_TYPE}"
INSTANCES="${INSTANCES} --task-instance-bid-price ${PRICE} --task-instance-type ${INSTANCE_TYPE}"
INSTANCES="${INSTANCES} --master-instance-bid-price ${PRICE} --master-instance-type ${INSTANCE_TYPE}"

# Instance counts
INSTANCES="${INSTANCES} --master-instance-count 1"
INSTANCES="${INSTANCES} --core-instance-count 64"
INSTANCES="${INSTANCES} --task-instance-count 0"

# Other EC2 config
EC2_CONFIG="--ec2-subnet-id subnet-96ef5d9a"

# EBS config
EBS_CONFIG="--use-ebs --ebs-volume-type gp2 --ebs-volumes-per-instance 6 --ebs-gb 250"

REGION="us-east-1"
NM="encode"
LNM="encode_1159"
BUCKET="langmead-${NM}-2017"
MANIFEST="s3://${BUCKET}/${LNM}/manifest/${NM}.manifest"
PREPROC="s3://${BUCKET}/${LNM}/preproc_01"  # will edit the JSON to point to 10 dirs
KEYPAIR_NAME="default"
PID_ARGS="--thread-ceiling 32"

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
    ${EC2_CONFIG} \
    ${EBS_CONFIG} \
    --ec2-key-name "${KEYPAIR_NAME}" \
    --intermediate-lifetime 30 \
    --name "ENCODE full align" \
    --transcriptome-bowtie2-args "${PID_ARGS} --thread-piddir /tmp/transcriptome-bowtie2-pid-tmp" \
    --bowtie2-args "${PID_ARGS} --thread-piddir /tmp/bowtie2-pid-tmp" \
    --max-task-attempts 6 \
    $*
