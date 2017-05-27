#!/bin/sh

BUCKET="langmead-mouseling-2017"
NM="mouseling"

mkdir -p "${NM}_output"
aws s3 cp --recursive s3://${BUCKET}/${NM}/output/ ${NM}_output/
