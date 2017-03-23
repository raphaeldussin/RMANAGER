#!/usr/bin/env python

import libmanager as rr
import sys

#--------------------------------------------------------------------------------------------------------------#
# import notice : before running this tool, you need to set environment variables in your .bashrc (.cshrc ,...) 
# csh :
# setenv RMANAGERPATH /path/to/RMANAGER
# setenv PYTHONPATH ${PYTHONPATH}:${RMANAGERPATH}/src/python
# bash :
# export RMANAGERPATH=/path/to/RMANAGER
# export PYTHONPATH=${PYTHONPATH}:${RMANAGERPATH}/src/python
#--------------------------------------------------------------------------------------------------------------#

# my personal information
# write here the complete path to the directory containing your runs.archive
# typically $HOME/RMANAGER/user/yourself
my_archive = '/Users/raphael/TOOLS/RMANAGER/user/raphael'
my_run = 'UPWELLING-TESTINSTALL'

# submission parameters dictionary
# this contains informations ti customize your submission script
submission_opts = {}
# options when you use yellowstone
#submission_opts['subcmd']      = 'bsub < ./'  # batch scheduler command : bsub, srun, llsubmit,...
#submission_opts['walltime']    = '10:00'      # walltime
#submission_opts['projectcode'] = 'ABCD1234'  # project code for accounting
#submission_opts['queue']       = 'regular'
# options when you use triton16 or triton24
#submission_opts['subcmd']      = 'sbatch < ./'  # batch scheduler command : bsub, srun, llsubmit,...
#submission_opts['walltime']    = '12:00:00'     # walltime
#submission_opts['projectcode'] = ''             # project code for accounting
#submission_opts['queue']       = ''
# options when you use your workstation
submission_opts['subcmd']      = './'           # batch scheduler command : bsub, srun, llsubmit,...
submission_opts['walltime']    = ''             # walltime (irrelevant)
submission_opts['projectcode'] = ''             # project code for accounting (irrelevant)
submission_opts['queue']       = ''

# init of the run object
# give the name of the simulation as defined in runs.archive
run = rr.run_manager(my_run, my_archive,submission_opts)

# secondary namelists : put here the name of the files that need to be copied
# to the run directory.
# those files can be varinfo.dat, ice.in, bio.in,...
#nam_files = ['varinfo.dat','ice.in','bio.in','fish.in','fleet.in','pred.in','nemsan.in']
nam_files = ['varinfo.dat']

# directory where namelist files listed above are stored
# ideally, create a directory with the same name as your run
# where you put your *.in and a subdirectory src where you put your *.h
dir_nam_files = my_archive + '/' + my_run

# run length
lastjob=2

# job duration (1y/6m/3m/1m)
jobduration='2d'

#------------------------------------------------------------------------------------#
# nothing to be customized below

# get input arguments (job number)
args = sys.argv

# test the presence of args
if len(args) != 2:
	print 'you must give the job number as an input argument to this script' 
	print 'to start a new simulation, type 0 else your job number' ; exit()
else:
	# define year (to be change by job number)
	job = int(args[-1])

# stop condition
if job > lastjob:
	# tidy and exit
	tidy = rr.tidy_your_run(job,run.run_opts,run.sub_opts)
	tidy()
        print 'We are done' ; exit()

# rewrite full path of namelist files
nam_files = [dir_nam_files + '/' + item for item in nam_files]

# run the job with no restart only the first time
if job == 0:
        run(job,duration=jobduration,infiles=nam_files,restart=False)
else:
	#before job 1 to N, clean previous job
	tidy = rr.tidy_your_run(job,run.run_opts,run.sub_opts)
	tidy()
	# then run job
        run(job,duration=jobduration,infiles=nam_files,restart=True)

