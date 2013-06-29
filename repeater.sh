#!/bin/sh

export GIT_MERGE_AUTOEDIT=no

while true; do
	./evolve.py 100 100
	if [ 0 -eq $? ]; then
		git pull -X theirs
		git add winners
		git commit -m "adding winners"
		git push
	fi
	rm -rf `seq 0 10000`
done
