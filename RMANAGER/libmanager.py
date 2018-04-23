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
import libdatetag4roms as dtroms
import os_utils

###########################################################################################################
### namelist maker : auto fills a namelist from template
###########################################################################################################

class namelist_maker():

	def __init__(self,run_opts):
		''' namelist_maker(run_opts)
		run_opts : are the run options from runs.archive + additions'''

		self.run_opts = run_opts

		# for clarity : put useful values in local variables
		for item in self.run_opts.keys():
			exec( "self." + str(item) + " = self.run_opts['" + str(item) + "']")

		self.prev_job = self.current_job - 1

		# define name of current namelist
		self.namelist_current = self.namelist_skel.replace('template',str(self.current_job))

		# define name of previous namelist if needed
		if self.run_opts['restart'] is True:
			self.namelist_prevjob = self.namelist_skel.replace('template',str(self.prev_job))

		# define the name of the restart file
		#self.restart_file = self.output_dir + '/' + self.runid + '_rst.nc'
		self.restart_file = self.output_dir + '/' + self.confcase + '_rst.nc'

	def __call__(self):

		print '<RMANAGER> Creating namelist : ', self.namelist_current

		# copy namelist skel into a tmp file
		self.copy_skel()

		# compute some useful numbers
		self.compute_startday()
		self.compute_currentyear()
		self.compute_number_timesteps()

		# editing the tmp namelist
		self.edit_namelist()

		# finalize, move tmp namelist into final namelist
		self.finalize_namelist()

		return None

	def copy_skel(self):
		'''copy into a tmp file'''
		os_utils.execute('cp ' + self.userspace + '/' + self.namelist_skel + ' namelist.tmp1')
		return None

	def finalize_namelist(self):
		'''copy into the final file'''
		os_utils.execute('mv namelist.tmp1 ' + self.namelist_current)
		return None

	def set_value(self,textToSearch, textToReplace):
		'''replace <VALUE> by its value '''
		fidr = open( 'namelist.tmp1', 'r' )
		fidw = open( 'namelist.tmp2', 'w' )
		for line in fidr.readlines():
			fidw.write( line.replace( textToSearch, textToReplace ) )
		fidr.close()
		fidw.close()
		os_utils.execute('mv namelist.tmp2 namelist.tmp1')
		return None

	def read_in_namelist(self,namlist,parameter):
		'''find a value in the namelist'''
		fid = open( namlist, 'r')
		lines = fid.readlines()
		fid.close()
		parameter = ' ' + parameter + ' =='
		for line in lines:
			 if line.find(parameter) != -1:
				out = line.split()[-1].replace('d','')
		return out

	def read_ocean_time(self,ncfile):
		'''read ocean_time into a netcdf file'''
		fid = nc.Dataset(ncfile,'r')
		ref_step = str(fid.variables['ocean_time'].units).split()[0]
                # RD : assuming units are in the format " something since 1900-01-01 0:00:00 "
		date_string = str(fid.variables['ocean_time'].units).split()[2]
		time_string = str(fid.variables['ocean_time'].units).split()[3]
		ref_string = date_string + ' ' + time_string
		if ref_step == 'days':
			factor = 86400
		elif ref_step == 'seconds':
			factor = 1
		else:
			print 'ERROR : not coded yet' ; exit()

		# handle files written with reference different from 1900-01-01
		fmt = '%Y-%m-%d %H:%M:%S'
		ref = dt.datetime.strptime(ref_string,fmt)

		delta = fid.variables['ocean_time'][:] 
		#time = ref + dt.timedelta(seconds= factor * delta[-1]) # take the last frame (restart)
		time = ref + dt.timedelta(seconds= factor * delta.max()) # with recycle restart, need to take larger number
		fid.close()

		return time, ref

	def compute_startday(self):
		'''set the DSTART of namelist in days from 1900-01-01'''
		# read the initial conditions timestamp 
		try:
			startdate, ref = self.read_ocean_time(self.init_file)
			self.startdate = startdate
			self.ref = ref
			self.startday = (startdate - ref).days + (startdate - ref).seconds / 86400.
		except:
			print 'Read initial time from IC file failed, assuming analytical case'
			self.startday = 0.
			self.startdate = dt.datetime(0001,1,1,0,0)
			self.ref = dt.datetime(0001,1,1,0,0)
		return None

	def compute_currentyear(self):

		if self.restart is True:
			self.job_startdate, reftime = self.read_ocean_time(self.restart_file)
		else:
			self.job_startdate = self.startdate
		self.current_year = self.job_startdate.year
		return None

	def is_this_year_leap(self):
		'''obvious'''
		import calendar
		out = calendar.isleap(self.current_year)
		return out

	def compute_number_timesteps(self):
		'''compute the number of timesteps to run in one job'''
		self.dt = int(float(self.read_in_namelist(self.userspace + '/' + self.namelist_skel,'DT')))
		if self.restart is True:
			run_duration = self.job_startdate - self.startdate
			run_duration_sec = run_duration.days * 86400. + run_duration.seconds
			self.prev_nsteps = int(run_duration_sec / self.dt)
		else:
			self.prev_nsteps = 0

		# number of leap days to add
		leap=0
		if self.use_leap_years:
			if self.is_this_year_leap():
				leap=1

		# read duration in a smarter way
		duration_number=self.duration[0:-1]
		duration_unit=self.duration[-1]

		if duration_unit not in ['d','m','y']:
			exit('You must provide units in days,month or year (d,m,y)')

		if duration_unit == 'd':
			ndays_to_run = int(duration_number)
		elif duration_unit == 'm':
			ndays_to_run = 30 * int(duration_number)
		elif duration_unit == 'y':
			ndays_to_run = 365 * int(duration_number)
		else:
			exit('run_duration has not a valid unit')

		self.nsteps   = self.prev_nsteps + ( ndays_to_run * 86400 / self.dt )
		self.nrestart = ndays_to_run * 86400 / self.dt
		return None

	def edit_namelist(self):
		'''main editing function for namelist'''
		self.set_value('<CONFCASE>', self.confcase )
		self.set_value('<NSTEPS>',str(self.nsteps))
		self.set_value('<NRESTART>',str(self.nrestart))
		self.set_value('<STARTDAY>',str(self.startday))
		self.set_value('<GRID>',self.grid_file)
		if self.restart is False:
			self.set_value('<INIT>',self.init_file)
		else:
			self.set_value('<INIT>',self.restart_file)

		if self.restart is False:
			self.set_value('<RESTART>','0')
			self.set_value('<LDEFOUT>','T')
		else:
			self.set_value('<RESTART>','-1')
			self.set_value('<LDEFOUT>','F')

		self.set_value('<CLMFILE>',self.nudging_file.replace('YYYY',str(self.current_year)) )
		self.set_value('<CLMFILEP1>',self.nudging_file.replace('YYYY',str(self.current_year+1)) )
		self.set_value('<CLMFILEM1>',self.nudging_file.replace('YYYY',str(self.current_year-1)) )
		self.set_value('<BRYFILE>',self.bdry_file.replace('YYYY',str(self.current_year)) )
		self.set_value('<BRYFILEP1>',self.bdry_file.replace('YYYY',str(self.current_year+1)) )
		self.set_value('<BRYFILEM1>',self.bdry_file.replace('YYYY',str(self.current_year-1)) )
		self.set_value('<SSS_RESTORING_FILE>',self.sssr_file)
		self.set_value('<RUNOFF_FILE>',self.runoff_file)
		self.set_value('<TIDES_FILE>',self.tide_file)
		self.set_value('<OUTPUTDIR>',self.output_dir)
		self.set_value('<FORCINGDIR>',self.forcing_dir)

		self.set_value('<YYYY>',str(self.current_year))
		self.set_value('<YYP1>',str(self.current_year+1))
		self.set_value('<YYM1>',str(self.current_year-1))
		self.set_value('<NXX>',str(self.ntilei))
		self.set_value('<NYY>',str(self.ntilej))
		return None

###########################################################################################################
### hostfile maker : create a hostfile to run with MPI
###########################################################################################################

# this will be obsolete

class hostfile_maker():

	def __init__(self,run_opts,sub_opts):
		''' hostfile_maker(runid): create the hostfile needed to run '''
	
		self.run_opts = run_opts
		self.sub_opts = sub_opts

		self.compute_nnodes()
		self.create_hostfile()

		return None

	def compute_nnodes(self):
		# hardcoded number of nodes
		if self.run_opts['machine'] in ['triton16']:
			self.core_per_nodes = 16 # can be put in RC file after
		else:
			print 'ERROR : Unknown machine for hostfile maker' ; exit()

		ntilei = self.run_opts['ntilei']
		ntilej = self.run_opts['ntilej']

		self.cores_needed   = int(ntilei) * int(ntilej)
		self.nodes_needed   = np.ceil( self.cores_needed / self.core_per_nodes )
		return None

	def create_hostfile(self):
		self.fileout = 'hostfile.' + self.run_opts['runid']
		offset = int( self.sub_opts['host_offset'] )
		fid = open(self.fileout,'w')
		for kp in np.arange(self.nodes_needed):
			fid.write('node' + str(int(kp+offset+1)) + ' slots=16 max_slots=16 \n') # 16 harcoded
		fid.close()

		# move this directly to run directory
		rundir = self.run_opts['output_dir']
		os_utils.execute('mv ' + self.fileout + ' ' + rundir + '/.')
		return None

###########################################################################################################
### script maker 
###########################################################################################################

class script_maker():

	def __init__(self,run_opts,sub_opts):
		''' script_maker(run_opts,sub_opts) : create the script '''

		# for clarity : put useful values in local variables
		for item in run_opts.keys():
			exec( "self." + str(item) + " = run_opts['" + str(item) + "']")

		for item in sub_opts.keys():
			exec( "self." + str(item) + " = sub_opts['" + str(item) + "']")

		self.script_dir   = os_utils.get_envvar('RMANAGERPATH') + '/src/run/' 
		self.template     = self.script_dir + 'Run.' + self.machine + '.template' 
		return None

	def __call__(self):

		# define name of current namelist
		self.namelist_current = self.namelist_skel.replace('template',str(self.current_job))

		# create the script 
		self.create_script()

		return None

	def create_script(self):
		''' create the script '''

		self.script_name = 'Run.' + self.runid + '.' + str(self.current_job)

		fidt = open(self.template,'r')
		lines = fidt.readlines()
		fidt.close()

		cdir = self.userspace
		fid = open(self.script_name,'w')

		for line in lines:
			line = line.replace('<NCORES>',str(self.ncores))
			line = line.replace('<CASE>',str(self.confcase))
			line = line.replace('<JOB>',str(self.current_job))
			line = line.replace('<NAMELIST>',str(self.namelist_current))
			line = line.replace('<CDIR>',str(cdir))
			line = line.replace('<WALLTIME>',str(self.walltime))
			line = line.replace('<PROJECTCODE>',str(self.projectcode))
			line = line.replace('<QUEUE>',str(self.queue))
			fid.write(line)
		fid.close()

		os_utils.execute('chmod +x ' + self.script_name)

		return None

###########################################################################################################
### run manager 
###########################################################################################################

class run_manager():

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

		# list of machine without batch scheduler
		#self.noscheduler = ['triton16-noslurm']
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
### outputs redirection
###########################################################################################################

class tidy_your_run():

        def __init__(self,current_job,run_opts,sub_opts):
                ''' tidy_your_run(run_opts,sub_opts) : move output files '''

                # for clarity : put useful values in local variables
                for item in run_opts.keys():
                        exec( "self." + str(item) + " = run_opts['" + str(item) + "']")

                for item in sub_opts.keys():
                        exec( "self." + str(item) + " = sub_opts['" + str(item) + "']")

		self.current_job = current_job
		self.previous_job = current_job - 1
		self.list_ftypes = ['avg','his','dia']

		# save copy of restarts
		self.rootrst = self.output_dir + '/restarts'
		self.rstdir = self.rootrst + '/' + str(self.previous_job)

		# define the name of the restart file
                self.restart_file = self.confcase + '_rst.nc'

		# short term archive directory
		self.sarchive_dir = self.output_dir + '/outputs'

		return None

	def __call__(self):
		# rename ROMS files using isoformat date tag
		for filetype in self.list_ftypes:
			self.tags_files(ftype=filetype)
		# find out which years we have
		self.create_list_years()
		# check existence of archive directories or create them if needed
		self.create_archive_dir()
		# save restarts
		self.archive_rst()
		# move outputs files
		self.archive_output()

		# write logs
		self.write_log_timeline()

		return None

	def create_archive_dir(self):
		''' check existence of directories for restart and outputs
		and create them if needed'''
		#--- restarts directory
		inq_restart = os_utils.execute('test -d ' + self.rootrst)
		if inq_restart == 0:
			pass
		else:
			print '<RMANAGER> creating ' + self.rootrst
			status = os_utils.execute('mkdir ' + self.rootrst)
		#--- this restart
		inq_restart = os_utils.execute('test -d ' + self.rstdir)
		if inq_restart == 0:
			pass
		else:
			print '<RMANAGER> creating ' + self.rstdir
			status = os_utils.execute('mkdir ' + self.rstdir)
		#--- output directory
		inq_arch = os_utils.execute('test -d ' + self.sarchive_dir)
		if inq_arch == 0:
			pass
		else:
			print '<RMANAGER> creating ' + self.sarchive_dir
			status = os_utils.execute('mkdir ' + self.sarchive_dir)
		#---- by year
		for year in self.list_years:
			inq_arch = os_utils.execute('test -d ' + self.sarchive_dir + '/' + str(year))
			if inq_arch == 0:
				pass
			else:
				print '<RMANAGER> creating ' + self.sarchive_dir + '/' + str(year)
				status = os_utils.execute('mkdir ' + self.sarchive_dir + '/' + str(year))
		return None

	def archive_rst(self):
		'''copy restart in a safe place'''
		rstin = self.restart_file
		rstout = self.restart_file.replace('.nc','.nc' + '.' + str(self.previous_job))
		status = os_utils.execute('rsync -av ' + self.output_dir + '/' + rstin + ' ' + self.rstdir + '/' + rstout)
		# tidal filter files
		list_filtered = os_utils.get_output('ls ' + self.output_dir + ' | grep ocean_fil*nc')
		if len(list_filtered) > 0:
			status = os_utils.execute('rsync -av ' + self.output_dir + '/ocean_fil*nc' + ' ' + self.rstdir + '/.')
		else:
			pass
		return None

	def tags_files(self,ftype='avg'):
		'''rename roms files with a proper datetime tag'''
		list_files = os_utils.get_output('ls ' + self.output_dir + ' | grep ' + ftype + ' | grep nc')
		for myfile in list_files:
			tag = dtroms.tagfile(self.output_dir + '/' + myfile)
			if self.use_leap_years == 'True':
				tag()
			elif self.use_leap_years == 'False':
				tag(leap=False)
			else:
				# do not rename files
				pass
		return None

	def create_list_years(self):
		'''look at output files and find out what years are currently present'''
		list_files = os_utils.get_output('ls ' + self.output_dir + ' | grep :')
		list_years = []
		for myfile in list_files:
			tmp2 = myfile.replace(self.confcase,'').replace('_',' ').replace('-',' ').split()[1]
			list_years.append(tmp2)
		self.list_years = list(set(list_years))
		return None

	def archive_output(self):
		'''move outputs files'''
		list_files = os_utils.get_output('ls ' + self.output_dir + ' | grep :')
		for myfile in list_files:
			year = myfile.replace(self.confcase,'').replace('_',' ').replace('-',' ').split()[1]
			status = os_utils.execute('mv ' + self.output_dir + '/' + myfile + ' ' + self.sarchive_dir + '/' + str(year) + '/.')
		return None

	def write_log_timeline(self):
		''' write the current status of run time line in a log file '''
		ftimeline = self.sarchive_dir + '/timeline_run'
		# if file already exists, load it
		check = os_utils.execute('test -f ' + ftimeline )
		if check ==0:
			f = open(ftimeline,'r') ; lines = f.readlines() ; f.close()
			list_timeline = []
			for line in lines:
				list_timeline.append(line.split()[0])
			print 'already in timeline_run :', list_timeline
			# update timeline
			list_timeline.extend(self.list_years)
			list_timeline = list(set(list_timeline))
			print 'timeline updated :', list_timeline
		else:
			list_timeline = self.list_years
			list_timeline = list(set(list_timeline))
			print 'new timeline_run', list_timeline
		# overwrite with the new list
		f = open(ftimeline,'w')
		for year in list_timeline:
			f.write( year + '\n')
		f.close()
		return None

###########################################################################################################

class long_term_archive():
        ''' A class to archive outputs from scratch to workdir '''

        def __init__(self,runid,userspace):
                '''get info to init instance '''

                # store input args
                self.run_opts = {}
                self.run_opts['runid']     = runid
                self.run_opts['userspace'] = userspace

                # open the parser and read the info on the run
                config = ConfigParser.ConfigParser()
                config.read(self.run_opts['userspace'] + '/runs.archive')

                for item in config.options(self.run_opts['runid']):
                        self.run_opts[item] = config.get(self.run_opts['runid'],item)

		return None

	def __call__(self,myworkdir):
		self.myworkdir = myworkdir
		self.storagedir = myworkdir + '/storage_' + self.run_opts['runid'] + '/'
		''' execute long term archiving '''
		# check everything exists
		self._prepare_transfer()
		# then transfer
		#self.transfer_outputs()
		self.transfer_restarts()
		return None

	def _stop(self,reason):
		import sys
		sys.exit(reason)

	def _prepare_transfer(self):
		''' check presence of directories on workdir '''

		check = os_utils.execute('test -d ' + self.run_opts['output_dir'] )
		if check != 0:
			self._stop('Error : the tmpdir for this run does not exist on the scrath')

		check = os_utils.execute('test -d ' + self.myworkdir )
		if check != 0:
			self._stop('Error : the workdir does not exist or path is wrong')

		check = os_utils.execute('test -d ' + self.storagedir )
		if check != 0:
			os_utils.execute('mkdir '+ self.storagedir )

		check = os_utils.execute('test -d ' + self.storagedir + 'outputs' )
		if check != 0:
			os_utils.execute('mkdir '+ self.storagedir + 'outputs' )
		
		check = os_utils.execute('test -d ' + self.storagedir + 'restarts' )
		if check != 0:
			os_utils.execute('mkdir '+ self.storagedir + 'restarts' )
		return None

	def compute_md5sum(self,myfile):
		md5sum = os_utils.get_output('md5sum ' + myfile )[0]
		return md5sum

	def check_existence_file(self,myfile):
		exist=True
		check = os_utils.execute('test -f ' + myfile)
		if check != 0:
			exist=False
		return exist

	def check_existence_dir(self,mydir):
		exist=True
		check = os_utils.execute('test -d ' + mydir)
		if check != 0:
			exist=False
		return exist

	def make_dir(self,dir):
		os_utils.execute('mkdir ' + dir)
		return None

	def run_copy(self,file,fromdir,todir):
		check = os_utils.execute('nice -0 rsync -av ' + fromdir + file + ' ' + todir + file )
		return check

	def transfer_one_file(self,file,fromdir,todir):
		exit_code = 0 # 0 normal, 1 problem
		checksum = 0
		check = 0
		# first check if file already on storage
		exist = self.check_existence_file(todir + file)
		# verify it is the same file
		if exist:
			sum_original = self.compute_md5sum(fromdir + file)
			sum_copy = self.compute_md5sum(todir + file)
			# or copy to a different file
			if sum_original != sum_copy:
				datenow = dt.datetime.now()
				os_utils.execute('mv ' + todir + file + ' ' + todir + file + '.' + datenow.isoformat() )
				checksum = 1

		self.run_copy(file,fromdir,todir)

		if (check != 0) or (checksum != 0):
			exit_code = 1	

		return exit_code

	def transfer_outputs(self):
		# get list of years
		list_years = os_utils.get_output('ls ' + self.run_opts['output_dir'] + '/outputs' )
		for year in list_years:
			my_todir = self.storagedir + 'outputs/' + year + '/'
			if not self.check_existence_dir(my_todir):
				self.make_dir(my_todir)

			my_fromdir = self.run_opts['output_dir'] + '/outputs/' + year + '/'
			list_files = os_utils.get_output('ls ' + my_fromdir )
			for file in list_files:
				error = self.transfer_one_file(file,my_fromdir,my_todir)
				if error != 0:
					print 'An error has occured while transfering file ', file

		return None

	def transfer_restarts(self):
		# get list of restarts
		list_restarts = os_utils.get_output('ls ' + self.run_opts['output_dir'] + '/restarts' )
		for restart in list_restarts:
			my_todir = self.storagedir + 'restarts/' + restart + '/'
			if not self.check_existence_dir(my_todir):
				self.make_dir(my_todir)

			my_fromdir = self.run_opts['output_dir'] + '/restarts/' + restart + '/'
			list_files = os_utils.get_output('ls ' + my_fromdir )
			for file in list_files:
				error = self.transfer_one_file(file,my_fromdir,my_todir)
				if error != 0:
					print 'An error has occured while transfering file ', file

		return None







