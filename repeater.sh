#!/bin/sh

while true; do
	git pull
	./evolve.py 100 60
	if [ 0 -eq $? ]; then
		git add winners
		git commit -m "adding winners"
		git push
	fi
	rm -rf `seq 0 60001`
done
