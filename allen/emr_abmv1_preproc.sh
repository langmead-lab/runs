#!/bin/sh

set -ex

# Profile
PROFILE="dlt-langmead"
AWS="aws --profile ${PROFILE}"

# Instance types and bid prices
INSTANCE_TYPE="c4.8xlarge"
PRICE="0.55"
INSTANCES="--core-instance-bid-price ${PRICE} --core-instance-type ${INSTANCE_TYPE}"
INSTANCES="${INSTANCES} --task-instance-bid-price ${PRICE} --task-instance-type ${INSTANCE_TYPE}"
INSTANCES="${INSTANCES} --master-instance-bid-price ${PRICE} --master-instance-type ${INSTANCE_TYPE}"

# Instance counts
INSTANCES="${INSTANCES} --master-instance-count 1"
INSTANCES="${INSTANCES} --core-instance-count 3"
INSTANCES="${INSTANCES} --task-instance-count 0"

# Other EC2 config -- using CC1 account
US_EAST_1A="subnet-74d3b710"
US_EAST_1B="subnet-32c91c1d"
US_EAST_1C="subnet-635fc928"
US_EAST_1D="subnet-6ee62833"
US_EAST_1E="subnet-f169d7ce"
US_EAST_1F="subnet-e46c60e8"
US_EAST_2A="subnet-05f5016d"
US_EAST_2B="subnet-77ebc00c"
US_EAST_2C="subnet-473a500a"

REGION="us-east-1"
EC2_CONFIG="--ec2-subnet-id ${US_EAST_1A}"

# EBS config
EBS_CONFIG="--use-ebs --ebs-volume-type gp2 --ebs-volumes-per-instance 8 --ebs-gb 100"

NM="abmv1"
LNM="abmv1"
BUCKET="langmeadlab-public-allen"
MANIFEST="s3://${BUCKET}/${LNM}/manifest/${NM}.manifest"
PREPROC="s3://${BUCKET}/${LNM}/preproc"
KEYPAIR_NAME="abmv1"

if ! ${AWS} s3api head-object --bucket ${BUCKET} --key "${LNM}/manifest/${NM}.manifest" 2>/dev/null ; then
	echo "Copying manifest"
	${AWS} s3 cp --region ${REGION} "${LNM}.manifest" "${MANIFEST}"
fi

python $HOME/git/rail-langmead/src prep elastic \
    --profile ${PROFILE} \
    -m ${MANIFEST} \
    -o ${PREPROC} \
    --region ${REGION} \
    ${INSTANCES} \
    ${EC2_CONFIG} \
    ${EBS_CONFIG} \
    --name "Allen preproc" \
    --skip-bad-records \
    --ec2-key-name "${KEYPAIR_NAME}" \
    --visible-to-all-users \
    --emr-debug \
    $*
