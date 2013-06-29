#!/bin/sh

sudo apt-get --yes --force-yes install mercurial python-dev
hg clone http://hg.code.sf.net/p/pycorewar/code /tmp/pycorewar-code
(cd /tmp/pycorewar-code/; python setup.py install --user)

WORKING_DIR=`mktemp -d`
git clone git@github.com:sstjohn/corewar-evolution.git $WORKING_DIR

cd $WORKING_DIR
./repeater.sh
