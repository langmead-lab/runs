#!/bin/sh

INSTANCE_TYPE="cc2.8xlarge"
PRICE="0.32"
INSTANCES="--core-instance-bid-price ${PRICE} --core-instance-type ${INSTANCE_TYPE}
           --task-instance-bid-price ${PRICE} --task-instance-type ${INSTANCE_TYPE}
           --master-instance-bid-price ${PRICE} --master-instance-type ${INSTANCE_TYPE}"
REGION="us-east-1"
BUCKET="langmead-mouseling-2017"
NM="mouseling"
MANIFEST="s3://${BUCKET}/${NM}/manifest/${NM}.manifest"
PREPROC="s3://${BUCKET}/${NM}/preproc"
KEYPAIR_NAME="default"
PID_ARGS="--thread-ceiling 32 --thread-piddir /tmp/rail-pid-tmp"

aws s3 cp "${NM}.manifest" "${MANIFEST}"

python $HOME/git/rail/src align elastic \
    -m ${MANIFEST} \
    -i s3://${BUCKET}/${NM}/preproc \
    --intermediate s3://${BUCKET}/${NM}/intermediate \
    -o s3://${BUCKET}/${NM}/output \
    -a mm10 \
    --drop-deletions \
    --region ${REGION} \
    ${INSTANCES} \
    -c 5 \
    --ec2-key-name "${KEYPAIR_NAME}" \
    --genome-bowtie1-args ${PID_ARGS} \
    --transcriptome-bowtie2-args ${PID_ARGS} \
    --bowtie2-args ${PID_ARGS} \
    --name "MouseLing align"
