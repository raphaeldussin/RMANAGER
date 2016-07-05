# RMANAGER = run manager for ROMS ocean model

# Introduction

This is a public version of the run manager (RMANAGER) I wrote for the Earth System Modeling Group at Rutgers University. The idea is not new and largely inspired by Jean-Marc Molines' Drakkar Config Manager for NEMO configurations. This tool aims at helping the ocean modeler at : 

* running a long simulation, divided in N jobs, by auto-filling the namelist from a template and creating the scripts for the batch scheduler.
* keeping tracks of input files (modified source code, namelist, forcing files,...) used for his/her simulation
* storing output files in an organized way  

It is mostly written in python, except for batch scripts. The pre-req are python 2.X with netCDF4 and numpy installed and of course a fortran compiler to compile ROMS.

# Installation

The install is not very pythonic and does not use a setup.py script. Simply clone the repository and run the install script with `./install`

It will add several environment variables to your .bashrc or .cshrc to point to the python libraries,... You may want to change the value of SCRATCH (by default set to $HOME) to make it point to the scratch of your system. It will also add your login under RMANAGER/user, this is your user space to put namelists (ocean.in), code (config.h,sourcecode.F90),... for your simulations.

## testing the install

Open ipython and try:

`import libmanager`

if you don't see any errors, congrats you're done!

# Usage, example from upwelling test case

Let's walk through the usage of the RMANAGER using ROMS simple upwelling test case. First you need a copy
of ROMS on your computer. RMANAGER does NOT provide a copy of ROMS and is designed to work with [Rutgers ROMS](http://myroms.org) and its close relatives, such as [Kate Hedstrom's branch](https://github.com/kshedstrom/roms).

## Setting up a simulation

We're gonna set up a first upwelling simulation. At the end of the setup process, you should obtain something very similar from what is in the user/raphael directory.

### running the setup_simulation

In ipython, there is 3 commands to run : 

`import libmanager as lm`

`setup = lm.setup_simulation()`

`setup()`

you'll be asked a few questions. At creating the setup object, you will be
asked to choose on which supercomputer you are running. RMANAGER is designed
to be working on different systems. If you are running on your laptop/desktop
or anything not listed, pick **workstation**. You can change this later.

During the setup itself, you'll be ask for the domain name. Type **UPWELLING**
for this example (or in the general case the domain you want to run). Next you'll
be asked to use or not the naming assistant. We'll skip here and put **n** and pick
the name ourselves (let call it **UPWELLING-TESTINSTALL**). Last you'll be asked for the
full path of the ROMS source code (for example /Users/raphael/MODELS/ROMS-Rutgers).

This setup will create a custom set of directories in your RMANAGER user space, scratch and
write a build.bash script for the current simulation.

### Compiling the code

1. Copy the upwelling.h from RMANAGER/user/template/UPWELLING-TESTCASE/src to your
RMANAGER/user/yourlogin/UPWELLING-TESTINSTALL/src directory.

2. Go to RMANAGER/user/yourlogin/UPWELLING-TESTINSTALL and run the build.bash script.

The src directory under your experiment name is the suitable place to put your ROMS headers,...
netcdf path use nf-config. You may have to customize the build.bash script to fit your install.

Your executable will be written in $SCRATCH/tmpdir_UPWELLING-TESTINSTALL

### Preparing input files

1. Copy the varinfo.dat from RMANAGER/user/template/UPWELLING-TESTCASE to your
RMANAGER/user/yourlogin/UPWELLING-TESTINSTALL directory.

2. Copy the ocean_upwelling.in from RMANAGER/user/template/ to RMANAGER/user/yourlogin/ocean_UPWELLING-TESTINSTALL.template

3. Check you're pointing to the right namelist in the runs.archive

The runs.archive is a file that is designed to keep track of information on input files used for your experiments, computer used,... The upwelling test case does not need data input files so you don't have to
worry about it yet.

### Running ROMS with RMANAGER

1. Set NtileI and NtileJ in the runs.archive to 1 and 1 (serial) or other

The UPWELLING-TESTINSTALL_ctl.py is the launching script. You can provide information for the queuing system
if needed, what are the input files you want to copy to the tmpdir (nam_files), how many jobs you want to run
(with lastjob) and jobs duration ( jobduration )

Here we are going to run 2 jobs of 2 days (set lastjob=1 and jobduration='2d'). We use C indexing, first job is job 0.

2. Start the script : 
 
`./UPWELLING-TESTINSTALL_ctl.py 0`
 
### What happens next

Go to your $SCRATCH/tmpdir_UPWELLING-TESTINSTALL. When the runs finishes, outputs and restarts will be stored in their subdirectories. The tar.gz files contains the script, namelist and logs.

If you want to continue for a third job, go back to RMANAGER/user/yourlogin, change the value of lastjob to 2 and run : 

`./UPWELLING-TESTINSTALL_ctl.py 2`
