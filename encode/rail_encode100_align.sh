#!/bin/sh

INSTANCES="--core-instance-bid-price 0.46 --core-instance-type c3.8xlarge
           --task-instance-bid-price 0.46 --task-instance-type c3.8xlarge
           --master-instance-bid-price 0.46 --master-instance-type c3.8xlarge"
REGION="us-east-1"
BUCKET="langmead-encode100-2017"
NM="encode100"
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
    --name "Encode 100 align"
