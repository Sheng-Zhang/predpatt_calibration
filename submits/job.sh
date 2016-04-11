#!/bin/bash

# Name your job. Unless you use the -o and -e options, output will
# go to a unique file name.ojob_id for each job.
#$ -N reservoir_sample_xxx

# The SGE batch system uses the current directory as working directory.
# Both files (output.dat and error.dat) will be placed in the current
# directory. The batch system assumes to find the executable in this directory.
# -wd /export/a06/sheng/

# Redirect output stream to this file.
#$ -o /export/a06/sheng/data/gigaword/log/log_xxx

# Redirect error stream to this file.
#$ -e error.dat

#$ -j yes

# For example an additional script file to be executed in the current
# working directory. In such a case assure that script.sh has
# execute permission (chmod +x script.sh).
echo "Working directory is $PWD"
python /home/zhangsheng/projects/calib_predpatt/sample.py 1000 /home/zhangsheng/projects/calib_predpatt/temp /export/a04/sheng/data/cag-4.6.10/fullest/ /export/a06/sheng/data/gigaword/sample/ xxx
