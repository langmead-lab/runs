#!/bin/sh

ITYPE="cc2.8xlarge"
BID=0.32
INSTANCES="--core-instance-bid-price ${BID}   --core-instance-type ${ITYPE}
           --task-instance-bid-price ${BID}   --task-instance-type ${ITYPE}
           --master-instance-bid-price ${BID} --master-instance-type ${ITYPE}"
REGION="us-east-1"
BUCKET="langmead-encode100-2017"
NM="encode15"
MANIFEST="s3://${BUCKET}/${NM}/manifest/${NM}.manifest"
KEYPAIR_NAME="default"

aws s3 cp "${NM}.manifest" "${MANIFEST}"

python $HOME/git/rail-langmead/src prep elastic \
    --do-not-check-manifest \
    -m ${MANIFEST} \
    -o s3://${BUCKET}/${NM}/preproc \
    --region ${REGION} \
    ${INSTANCES} \
    --ec2-key-name "${KEYPAIR_NAME}" \
    -c 3
