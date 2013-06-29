#!/bin/sh

export GIT_MERGE_AUTOEDIT=no

./evolve.py 100 100
if [ 0 -eq $? ]; then
	git add winners
	git commit -m "adding winners"
	git pull -X ours
	git push
else
	git pull -X ours
fi
rm -rf `seq 0 10000`
./eliminate.py
if [ 0 -eq $? ]; then
	git add -u winners
	git commit -m "removing losers"
	git pull -X theirs
	git push
else
	git pull -X theirs
fi
. ./repeater.sh
