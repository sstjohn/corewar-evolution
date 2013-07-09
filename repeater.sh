#!/bin/bash

export GIT_MERGE_AUTOEDIT=no
export PYTHONPATH=`pwd`/pycorewar/lib64/python2.6/site-packages/

pushed=1
success=0
rm -f core.*

./evolve.py 30 10
if [ 0 -eq $? ]; then
	pushed=0
	success=1
	git add winners
	git commit -m "adding winners"
	git pull -X ours 2>&1
	git push 2>&1
	if [ 0 -ne $? ]; then
		git pull -X ours 2>&1
		git push 2>&1
		if [ 0 -eq $? ]; then
			pushed=1
		fi
	else
		pushed=1
	fi
else
	git clean -f winners 2>&1
	git pull -X theirs 2>&1
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
		./clean_dupes.sh 2>&1
		git add -u winners
		git commit -m "removing dupes" 2>&1
		git pull -X theirs 2>&1
		git push 2>&1
		if [ 0 -ne $? ]; then
			git pull -X theirs 2>&1
			git push 2>&1
			if [ 0 -eq $? ]; then
				pushed=1
			fi
		else
			pushed=1
		fi
	else
		git clean -f winners 2>&1
		git checkout winners 2>&1
		git pull -X theirs 2>&1
	fi
fi
if [ ! -f .stopnow ] && [ "$0" == "./repeater.sh" ]; then
	exec $0
fi
if [ $pushed -eq 0 ]; then
	result=1
	tries=0
	while [ $result -ne 0 ] && [ $tries -ne 10 ]; do
		git pull -X theirs 2>&1
		git push 2>&1
		result=$?
		tries=$(($tries + 1))
	done
	if [ $result -ne 0 ]; then
		echo "failed to commit results! giving it one last go!" >&2
		git pull -X theirs >&2
		git push >&2
		result=$?
	fi
	exit $result
fi
