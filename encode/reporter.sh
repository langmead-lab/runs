#!/bin/sh

# Example output from `iostat -dmx 1`

# Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await  svctm  %util
# xvda              0.00     4.00    0.00    2.00     0.00     0.02    24.00     0.00    0.00   0.00   0.00
# xvdd              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00   0.00   0.00
# xvde              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00   0.00   0.00
# xvdb              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00   0.00   0.00
# xvdc              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00   0.00   0.00
# xvdf              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00   0.00   0.00
# xvdg              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00   0.00   0.00
#

S3DST=s3://langmead-encode-2017/encode_1159/output.logs/j-22TY2XT6YBXLJ/Langmead/
KEY=encode-20170630.pem
SSH_CMD="ssh -i ${HOME}/${KEY} -o StrictHostKeyChecking=no"

fn="snapshots.txt"
echo > ${fn}
while true ; do
	dt=`date +"%m-%d-%y-%H-%M-%S"`
	workers=`hdfs dfsadmin -report | grep Name | awk '{print $2}' | sed 's/\:.*//'`
	jobid=`mapred job -list | grep '\sjob_' | awk '{print $1}'`
	echo $jobid >> ${fn}
cat >".reporter_helper.sh" <<EOF
#!/bin/bash

# How much disk is free on ephemeral EBS volumes
df -h | grep mnt | awk '{print \$(NF-1),\$NF}' | sed "s/^/$jobid $dt df /"

# Aggrgate CPU, MEM, IO usage
vmstat | sed "s/^/$jobid $dt vmstat /"

# More detail on IO, broken out by volume
iostat -dmx 1 2 | grep xvd | awk '\$1 == "xvda" {n += 1} n >= 2 {print}' | sed "s/^/$jobid $dt iostat /"

# Current mapreduce job (step)
mapred job -status ${jobid} | sed "s/^/$jobid $dt mapred_status /"
EOF
	for i in ${workers} ; do
		${SSH_CMD} $i "bash -s" < ".reporter_helper.sh"
	done | tee -a ${fn}
	gzip -c < ${fn} > ${fn}.gz
	aws s3 cp ${fn}.gz ${S3DST}
	sleep 5
done
