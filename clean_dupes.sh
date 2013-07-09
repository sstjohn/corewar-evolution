#!/bin/bash

true
while [ $? -eq 0 ]; do
	sha1sum winners/* | sort | sed -e 's/^\([^ ]*\)  \(.*\)$/\2 \1/' | uniq -f 1 -d | cut -f 1 -d\  | xargs rm
done

