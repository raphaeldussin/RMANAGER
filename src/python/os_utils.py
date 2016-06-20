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
#   wrapper functions to deal with subprocess, os and commands under different python flavors             #
#   Author : Raphael Dussin 2014-                                                                         #
#                                                                                                         #
###########################################################################################################

try:
	import subprocess as sp
except:
	import commands as cm
	import os

def execute(cmd):
	''' cmd is the string we want to execute in the shell
	out is the error status'''
	try:   
		# first use subprocess
		out = sp.call(cmd,shell=True)
	except:
		# else os (python 2.6 or older)
		out = os.system(cmd)
	return out

def get_output(cmd):
	''' cmd is the string we want to execute in the shell
	and have the output'''
	try:   
		# first use subprocess
		out = sp.check_output(cmd,shell=True).replace('\n',' ').split()
	except:
		# else os (python 2.6 or older)
		out = cm.getoutput(cmd).replace('\n',' ').split()
	return out

def get_envvar(environ_var):
	''' get environment variable '''
	try:   
		# first use subprocess
		out = sp.check_output('echo $' + environ_var,shell=True).replace('\n','')
	except:
		# else os (python 2.6 or older)
		out = os.environ.get(environ_var)
	return out

