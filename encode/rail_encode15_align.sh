#!/bin/sh

INSTANCE_TYPE="cc2.8xlarge"
PRICE="0.32"
INSTANCES="--core-instance-bid-price ${PRICE} --core-instance-type ${INSTANCE_TYPE}
           --task-instance-bid-price ${PRICE} --task-instance-type ${INSTANCE_TYPE}
           --master-instance-bid-price ${PRICE} --master-instance-type ${INSTANCE_TYPE}"
REGION="us-east-1"
BUCKET="langmead-encode100-2017"
NM="encode15"
MANIFEST="s3://${BUCKET}/${NM}/manifest/${NM}.manifest"
PREPROC="s3://${BUCKET}/${NM}/preproc"
KEYPAIR_NAME="default"

python $HOME/git/rail/src align elastic \
    -m ${MANIFEST} \
    -i s3://${BUCKET}/${NM}/preproc \
    --intermediate s3://${BUCKET}/${NM}/intermediate \
    -o s3://${BUCKET}/${NM}/output \
    -a hg38 \
    --drop-deletions \
    --region ${REGION} \
    ${INSTANCES} \
    -c 3 \
    --ec2-key-name "${KEYPAIR_NAME}" \
    --name "Encode 15 align"
