#!/bin/sh

INSTANCES="--core-instance-bid-price 0.46 --core-instance-type c3.8xlarge
           --task-instance-bid-price 0.46 --task-instance-type c3.8xlarge
           --master-instance-bid-price 0.46 --master-instance-type c3.8xlarge"
REGION="us-east-1"
BUCKET="langmead-encode100-2017"
NM="encode100"
MANIFEST="s3://${BUCKET}/${NM}/manifest/${NM}.manifest"
KEYPAIR_NAME="default"

python $HOME/git/rail/src prep elastic \
    --do-not-check-manifest \
    -m ${MANIFEST} \
    -o s3://${BUCKET}/${NM}/preproc \
    --region ${REGION} \
    ${INSTANCES} \
    --ec2-key-name "${KEYPAIR_NAME}" \
    -c 3
