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
KEYPAIR_NAME="default"

aws s3 cp "${NM}.manifest" "${MANIFEST}"

python $HOME/git/rail/src prep elastic \
    -m ${MANIFEST} \
    -o s3://${BUCKET}/${NM}/preproc \
    --region ${REGION} \
    ${INSTANCES} \
    --ec2-key-name "${KEYPAIR_NAME}" \
    -c 5
