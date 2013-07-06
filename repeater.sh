#!/bin/sh

export GIT_MERGE_AUTOEDIT=no
export PYTHONPATH=`pwd`/pycorewar/lib64/python2.6/site-packages/

pushed=1
success=0
rm core.*

./evolve.py 30 10
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
		if (./check_compressibility.sh | tee compress); then
			git add compress
		else
			git checkout compress
		fi
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
if [ ! -f .stopnow ] && [ "$0" == "./repeater.sh" ]; then
	exec $0
fi
if [ $pushed -eq 0 ]; then
	result=1
	while [ $result -ne 0 ]; do
		git pull -X theirs
		git push
		result=$?
	done
fi
