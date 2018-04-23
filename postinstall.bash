#!/bin/bash

# to find out where RMANAGER was installed, we need to move out of here
here=$( pwd ) ; cd $HOME
RMANAGERPATH=$( python -c 'import RMANAGER ; print RMANAGER.__path__[0]' )
cd $here

# copy templates into install directory
cp -r ./RMANAGER/templates $RMANAGERPATH/.

if [ $SHELL == /bin/bash ] ; then

   echo your shell is bash 
   echo RMANAGER will append environment variables to your .bashrc
   echo '#------------ RMANAGER -----------------------#' >> $HOME/.bashrc
   echo "export RMANAGERPATH=$RMANAGERPATH " >> $HOME/.bashrc
   echo "export RMANAGER_SCRATCH=${HOME}/SCRATCH" >> $HOME/.bashrc
   echo 'RAMANAGER_SCRATCH (= where the model will run )' set to $HOME/SCRATCH by default, you may want to change this
   . $HOME/.bashrc

elif [ $SHELL == /bin/csh ] ; then

   echo your shell is csh
   echo RMANAGER will append environment variables to your .cshrc
   echo '#------------ RMANAGER -----------------------#' >> $HOME/.cshrc
   echo "setenv RMANAGERPATH $RMANAGERPATH " >> $HOME/.cshrc
   echo "setenv RMANAGER_SCRATCH ${HOME}/SCRATCH" >> $HOME/.cshrc
   echo 'RAMANAGER_SCRATCH (= where the model will run )' set to $HOME/SCRATCH by default, you may want to change this
   source $HOME/.cshrc

else

   echo only bash and csh are currently supported
   
fi
