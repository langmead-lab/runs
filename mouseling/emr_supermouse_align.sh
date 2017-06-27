#!/bin/sh

INSTANCE_TYPE="cc2.8xlarge"
PRICE="0.35"
# (0.35 + 0.27) * 32 = $20
INSTANCES="--core-instance-bid-price ${PRICE} --core-instance-type ${INSTANCE_TYPE}
           --task-instance-bid-price ${PRICE} --task-instance-type ${INSTANCE_TYPE}
           --master-instance-bid-price ${PRICE} --master-instance-type ${INSTANCE_TYPE}"
REGION="us-east-1"
NM="supermouse"
BUCKET="langmead-${NM}-2017"
MANIFEST="s3://${BUCKET}/${NM}/manifest/${NM}.manifest"
PREPROC="s3://${BUCKET}/${NM}/preproc"
KEYPAIR_NAME="default"
PID_ARGS="--thread-ceiling 32"
NWORKERS=31

aws s3 cp "${NM}.manifest" "${MANIFEST}"

# This doesn't seem ready for prime time yet
#    --genome-bowtie1-args "${PID_ARGS} --thread-piddir /tmp/genome-bowtie1-pid-tmp" \

python $HOME/git/rail/src align elastic \
    -m ${MANIFEST} \
    -i s3://${BUCKET}/${NM}/preproc \
    --intermediate s3://${BUCKET}/${NM}/intermediate \
    -o s3://${BUCKET}/${NM}/output \
    -a mm10 \
    --drop-deletions \
    --region ${REGION} \
    ${INSTANCES} \
    -c ${NWORKERS} \
    --ec2-key-name "${KEYPAIR_NAME}" \
    --intermediate-lifetime -1 \
    --name "Supermouse align" \
    --transcriptome-bowtie2-args "${PID_ARGS} --thread-piddir /tmp/transcriptome-bowtie2-pid-tmp" \
    --bowtie2-args "${PID_ARGS} --thread-piddir /tmp/bowtie2-pid-tmp" \
    $*
