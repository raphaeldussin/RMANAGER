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
#   RMANAGER additional library                                                                           #
#   rename roms files according to their time and date from ocean_time                                    #
#   Author : Raphael Dussin 2014-                                                                         #
#                                                                                                         #
###########################################################################################################

import datetime as dt
import netCDF4 as nc
import numpy as np
import os_utils

class tagfile():

	def __init__(self,filename):
		self.filein = filename
		self.fail=False
		return None

	def __call__(self,leap=True):
		# read time in netcdf
		time, timeunits = self.read_time(self.filein)
		if self.fail is False:
			# create the date tag
			if leap:
				tag = self.create_tag(time, timeunits)
			else:
				tag = self.create_tag_noleap(time, timeunits)
			# define a new filename
			self.create_new_filename(tag)
			# rename file
			self.rename_file()
		else:
			pass
		return None

	def read_time(self,filein):
		''' read ocean_time variable and units in netcdf file'''
		try:
			fid = nc.Dataset(filein,'r')
		except:
			print 'could not open file ', filein
		time = fid.variables['ocean_time'][:]
		timeunits = fid.variables['ocean_time'].units
		fid.close()
		if len(time) > 1:
			print '>>> error : multiple values in time array\n>>> skipping file ' + filein
			self.fail=True
		else:
			time = time[0]
		return time, timeunits

	def create_tag(self,time, timeunits):
		''' create a datetime object from reference date and ocean_time'''
		delta_type = timeunits.split()[0]
                # RD : assuming units are in the format " something since 1900-01-01 0:00:00 "
                date_string = timeunits.split()[2]
                time_string = timeunits.split()[3]
                ref_string = date_string + ' ' + time_string
                # handle files written with reference different from 1900-01-01
                fmt = '%Y-%m-%d %H:%M:%S'
                dateref = dt.datetime.strptime(ref_string,fmt)
		# create a datetime object for current time
		if delta_type == 'seconds':
			tag = dateref + dt.timedelta(seconds=time)
                elif delta_type == 'days':
			tag = dateref + dt.timedelta(days=time)
		return tag

	def create_tag_noleap(self, time, timeunits):
		''' create a datetime object from reference date and ocean_time (noleap version)'''
		# first we need to figure out how many seconds are ellaped between ref_date
		# and start date of the run
		delta_type  = timeunits.split()[0]
		date_string = timeunits.split()[2]
		time_string = timeunits.split()[3]
		ref_string = date_string + ' ' + time_string
		fmt = '%Y-%m-%d %H:%M:%S'
		dateref_dstart = dt.datetime.strptime(ref_string,fmt)

		if delta_type == 'seconds':
			seconds_from_init = float(time)
		elif delta_type == 'days':
			seconds_from_init = float(time) * 86400.

		nyear  = int(np.floor(seconds_from_init / 365 / 86400))
		rm     = np.remainder(seconds_from_init,365*86400)
		ndays  = int(np.floor(rm / 86400))
		rm2    = np.remainder(rm,86400)
		nhours = int(np.floor(rm2 / 3600))
		rm3    = np.remainder(rm2,3600)
		nmin   = int(np.floor(rm3 / 60))
		nsec   = int(np.remainder(rm3,60))

		# pick a year we are sure is not a leap year
		fakeref  = dt.datetime(1901,1,1,0,0)
		fakedate = fakeref + dt.timedelta(days=ndays)
		month    = fakedate.month
		day      = fakedate.day

		tag=dt.datetime(nyear + dateref_dstart.year,month, day, nhours, nmin, nsec)
		return tag

	def create_new_filename(self,tag):
		''' based on tag, generate a new filename '''
		# get rid of full path (if any)
		filein = self.filein.replace('/',' ').split()[-1]
		# get the pieces we want to keep in filename
		filein_wrk = filein.replace('_',' ').split()
		runname = filein_wrk[0]
		filetype = filein_wrk[1]
		# write our new filename
		self.fileout = runname + '_' + filetype + '_' + tag.isoformat() + '.nc'
		return None


	def rename_file(self):
		''' call unix command mv '''
		# remove filein from full path
		wrk = self.filein.replace('/',' ').split()[0:-1]
		# re-create path
		path = ''
		for part in wrk:
			path = path + '/' + part
		# rename file only if different
		if self.filein == path + '/' + self.fileout:
			pass
		else:
			os_utils.execute('mv ' + self.filein + ' ' + path + '/' + self.fileout)
		return None


