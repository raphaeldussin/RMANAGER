# This file is part of RMANAGER.
#
# RMANAGER is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# RMANAGER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RMANAGER.  If not, see <http://www.gnu.org/licenses/>.

###########################################################################################################
#                                                                                                         #
#   RMANAGER main library                                                                                 #
#   Author : Raphael Dussin 2014-                                                                         #
#                                                                                                         #
###########################################################################################################

import ConfigParser
import netCDF4 as nc
import datetime as dt
import numpy as np
from RMANAGER import os_utils

###########################################################################################################

class RunManager():

	def __init__(self,runid,userspace,sub_opts):
		'''run_manager(runid): manage a run with roms '''

		# store input args
		self.run_opts = {}
		self.run_opts['runid']     = runid
		self.run_opts['userspace'] = userspace
		
		# open the parser and read the info on the run
		config = ConfigParser.ConfigParser()
		config.read(self.run_opts['userspace'] + '/runs.archive')

		for item in config.options(self.run_opts['runid']):
			self.run_opts[item] = config.get(self.run_opts['runid'],item) 

		# store submission options dict
		self.sub_opts = sub_opts

		return None

	def __call__(self,current_job,duration='1y',infiles=[],restart=False):

		self.run_opts['restart']      = restart
		self.run_opts['current_job']  = current_job
		self.run_opts['duration']     = duration

		#--- compute how many cores are needed ---#
		self.run_opts['ncores'] = self.compute_ncores()
		
		#--- namelist ---#
		nam = namelist_maker(self.run_opts)
		nam()

		#--- runtime script ---#
		script = script_maker(self.run_opts,self.sub_opts)
		script()

		#--- hostfile (if no batch scheduler ---#
		#if self.run_opts['machine'] in self.noscheduler:
			# command
			#print '<RMANAGER> Creating hostfile for mpirun...'
			#h = hostfile_maker(self.run_opts,self.sub_opts)
			#print 'Running without the scheduler is BAD !!!!'
			#exit()

		#--- copy files to run directory ---#
		self.copy2rundir(nam,script,infiles)

		#--- run the code ---#
		self.run(script)

		#--- check for blowing-up ---#
		#if self.run_opts['machine'] in self.noscheduler:
		#	self.check_blowup()

		#--- post-processing ---#
		#if self.run_opts['machine'] in self.noscheduler:
		#	tidy = tidy_your_run(self.run_opts,self.sub_opts)
		#	tidy()

		return None

	def compute_ncores(self):
		ncores = int(self.run_opts['ntilei']) * int(self.run_opts['ntilej'])
		return ncores

	def copy2rundir(self,namlist,scrpt,infiles):
		rundir = self.run_opts['output_dir']
		# namelist
		os_utils.execute('mv ' + namlist.namelist_current + ' ' + rundir +'/.')
		# script
		os_utils.execute('mv ' + scrpt.script_name + ' ' + rundir +'/.')
		# varinfo.dat and all other files ice.in, bio.in,...
		for infile in infiles:
			os_utils.execute('cp ' + infile + ' ' + rundir )
		return None

	def dry_run(self,scrpt):
		# go to run directory command
		cdcmd  = ' cd ' + self.run_opts['output_dir']
		# run the script command
		runcmd = self.sub_opts['subcmd'] + scrpt.script_name
		# call system : this is where all the magic happens
		print cdcmd + ' ; ' + runcmd 
		return None

	def run(self,scrpt):
		# go to run directory command
		cdcmd  = ' cd ' + self.run_opts['output_dir']
		# run the script command
		runcmd = self.sub_opts['subcmd'] + scrpt.script_name
		# call system : this is where all the magic happens
		os_utils.execute( cdcmd + ' ; ' + runcmd )
		return None

	def check_blowup(self):
		logfile = self.run_opts['output_dir'] + '/' + 'log.' + str( self.run_opts['current_job'] )
		out = os_utils.get_output('grep Blowing-up ' + logfile)
		print '<RMANAGER> checking for blowup in ' + logfile + '...'
		if ( len(out) == 0):
			print '<RMANAGER> log seems normal'
			pass
		else:
			print ''
			print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
			print '!!! RUN BLEW UP , EMERGENCY STOP                             !!!' 
			print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
			exit()

###########################################################################################################
