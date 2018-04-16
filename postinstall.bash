#!/bin/bash

# to find out where RMANAGER was installed, we need to move out of here
here=$( pwd ) ; cd $HOME
RMANAGERPATH=$( python -c 'import RMANAGER ; print RMANAGER.__path__[0]' )
cd $here

# copy templates into install directory
cp -r ./RMANAGER/templates $RMANAGERPATH/.
