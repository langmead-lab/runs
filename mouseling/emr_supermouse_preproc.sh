#!/bin/sh

INSTANCE_TYPE="cc2.8xlarge"
PRICE="0.335"
INSTANCES="--core-instance-bid-price ${PRICE} --core-instance-type ${INSTANCE_TYPE}
           --task-instance-bid-price ${PRICE} --task-instance-type ${INSTANCE_TYPE}
           --master-instance-bid-price ${PRICE} --master-instance-type ${INSTANCE_TYPE}"
REGION="us-east-1"
BUCKET="langmead-supermouse-2017"
NM="supermouse"
MANIFEST="s3://${BUCKET}/${NM}/manifest/${NM}.manifest"
KEYPAIR_NAME="default"

aws s3 cp "${NM}.manifest" "${MANIFEST}"

python $HOME/git/rail-langmead/src prep elastic \
    -m ${MANIFEST} \
    -o s3://${BUCKET}/${NM}/preproc \
    --region ${REGION} \
    --do-not-check-manifest \
    ${INSTANCES} \
    --ec2-key-name "${KEYPAIR_NAME}" \
    -c 4
