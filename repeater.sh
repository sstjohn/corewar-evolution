#!/bin/sh

export GIT_MERGE_AUTOEDIT=no

pushed=1
success=0
rm core.*

./evolve.py 100 100
if [ 0 -eq $? ]; then
	pushed=0
	success=1
	git add winners
	git commit -m "adding winners"
	git pull -X ours
	git push
	if [ 0 -ne $? ]; then
		git pull -X ours
		git push
		if [ 0 -eq $? ]; then
			pushed=1
		fi
	else
		pushed=1
	fi
else
	git pull -X ours
fi
rm -rf `seq 0 10000`
if [ $success -eq 1 ]; then
	./eliminate.py
	if [ 0 -eq $? ]; then
		pushed=0
		git add -u winners
		git commit -m "removing losers"
		git pull -X theirs
		git push
		if [ 0 -ne $? ]; then
			git pull -X theirs
			git push
			if [ 0 -eq $? ]; then
				pushed=1
			fi
		else
			pushed=1
		fi
	else
		git pull -X theirs
	fi
fi
if [ ! -x .stopnow ] && [ "$0" != "./run_once.sh" ]; then
	exec $0
fi
if [ $pushed -eq 0 ]; then
	git pull -X theirs
	git push
fi
