#!/bin/sh

cat mouseling_raw.csv | sed 's/["]//g' | awk -v FS=',' -v OFS='\t' '$1 != "SRA.Accession" {print "sra:"$1,0,$3}'
