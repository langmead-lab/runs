#!/bin/sh

REGION="us-east-1"
BUCKET="langmead-encode100-2017"
NM="encode100"
MANIFEST="s3://${BUCKET}/${NM}/manifest/${NM}.manifest"

aws s3 mb s3://${BUCKET} --region ${REGION}

aws s3 cp encode100.manifest ${MANIFEST}
