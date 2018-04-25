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

class SetupSimulation():

	def __init__(self,model=None):

		self.model = model
		# define machine on which we run
		self.list_machine = ['workstation','yellowstone','triton16','triton24']
		self.machine = ''
		print 'Machines available are :', self.list_machine 	
		while self.machine not in self.list_machine:
			self.machine = raw_input('On which supercomputer are we running ? \n >>> ')

		self.scratch = os_utils.get_envvar('RMANAGER_SCRATCH')
		if self.scratch is None:
			exit('SCRATCH environment variable misssing, please add to .bashrc or .cshrc')
		else:
			print 'RMANAGER_SCRATCH set to ', self.scratch

		# find where RMANAGER is installed
		try:
			self.rmanager_root = os_utils.get_envvar('RMANAGERPATH')
		except:
			self.rmanager_root = RMANAGER.__path__[0]

		if self.rmanager_root is None:
			print 'Unable to find out where RMANAGER is installed or incorrect install'
			exit()
		else:
			print 'RMANAGER is installed in : ', self.rmanager_root 
			print 'If this seems incorrect, please check your install, paths,...'
		# define where user will create the run folder
		self.myrmanager = os_utils.get_output('pwd')[0]
		print 'Your run environment will be created in ', self.myrmanager
		print 'You can now run setup()'
		return None

	def __call__(self):
		self._run_naming()
		self._create_run_directory()
		self._create_script()
		self._create_archive_entry()
		self._create_build_script()
		print 'Setup Complete'
		return None

	def _run_naming(self):
		''' define a run name based on given informations '''
		model_app = ''
		while model_app == '':
			model_app = raw_input('What is the configuration/application name (CCS1, NWA, ASTE,...) ? \n >>> ')
		self.model_app = model_app

		newname = ''
		while newname == '':
			newname = raw_input('Please define the name of the new simulation \n >>> ')
		self.runname = newname

		print 'Final name is : ', self.runname
		return None

	def _create_run_directory(self):
		self.tmpdir = self.scratch + '/RUNS_' + self.model + '/tmpdir_'+ self.runname
		# create the appropriate directories
		os_utils.execute('mkdir ' + self.myrmanager + '/' + self.runname)
		os_utils.execute('mkdir ' + self.myrmanager + '/' + self.runname + '/input')
		if self.model == 'ROMS':
			os_utils.execute('mkdir ' + self.myrmanager + '/' + self.runname + '/src')
		elif self.model == 'MITgcm':
			os_utils.execute('mkdir ' + self.myrmanager + '/' + self.runname + '/code')
		os_utils.execute('mkdir -p ' + self.tmpdir )
                return None

        def _create_script(self):
                '''create control script for one run '''
                fidr = open( self.rmanager_root + '/templates/template_script_ctl.py', 'r' )
                fidw = open( self.myrmanager + '/' + self.runname + '/' + self.runname + '_ctl.py', 'w' )
                for line in fidr.readlines():
                        fidw.write( line.replace( '<MY_RMANAGER>', self.myrmanager ).replace( '<MY_RUN>', self.runname ) )
                fidr.close()
                fidw.close()
		os_utils.execute('chmod +x ' + self.myrmanager + '/' + self.runname + '/' + self.runname + '_ctl.py' )
                return None

	def _create_archive_entry(self):
                '''add an entry in runs.archive for one run '''
                fidr = open( self.rmanager_root + '/templates/runs.archive.' + self.model + '.template', 'r' )
                fidw = open( self.myrmanager + '/' + self.runname + '/' + 'runs.archive', 'w' )
                for line in fidr.readlines():
                        fidw.write( line.replace( '<MACHINE>', self.machine ).replace( '<MY_RUN>', self.runname ).replace( '<MY_TMPDIR>', self.tmpdir ).replace( '<INPUTDIR>', self.scratch + '/RUNS_' + self.model ) )
		fidr.close()
		fidw.close()
                return None
		
	def _create_build_script(self):
		'''create custom build.bash script '''
		self.model_dir = ''
		while self.model_dir == '':
			self.model_dir = raw_input('Where is the ' + self.model + ' code installed ? \n >>> ')

                fidr = open( self.rmanager_root + '/templates/build.' + self.model + '.template', 'r' )
                fidw = open( self.myrmanager + '/' + self.runname + '/build.' + self.model + '.bash', 'w' )
                for line in fidr.readlines():
                        fidw.write( line.replace( '<MODEL_APP>', self.model_app ).replace( '<MODEL_DIR>', self.model_dir ).replace( '<MY_TMPDIR>', self.tmpdir ) )
		fidr.close()
		fidw.close()
		os_utils.execute('chmod +x ' + self.myrmanager + '/' + self.runname + '/build.' + self.model + '.bash' )
		return None
