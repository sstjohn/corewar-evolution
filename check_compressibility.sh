#!/bin/bash

WARRIOR_DIR="winners"


get_comp_ratio () {
	UNCOMP_SIZE=`cat $1 | wc -c`
	COMP_SIZE=`cat $1 | gzip -9 -c | wc -c`
	RATIO=`echo "$COMP_SIZE	/ $UNCOMP_SIZE" | bc -l`
	echo "$UNCOMP_SIZE $COMP_SIZE $RATIO"
}

get_all_comp_ratios () {
	(cd $WARRIOR_DIR
	TOTAL_COMP=0
	TOTAL_UNCOMP=0 
	for i in *; do
		result="`get_comp_ratio $i`"
		TOTAL_UNCOMP=$(($TOTAL_UNCOMP + `echo $result | cut -d\  -f 1`))
		TOTAL_COMP=$(($TOTAL_COMP + `echo $result | cut -d\  -f 2`))
		echo -e "$i\t`echo $result | cut -d\  -f 3`"
	done
	echo "Total compressibility: `echo \"$TOTAL_COMP / $TOTAL_UNCOMP\" | bc -l`")
}

get_all_comp_ratios | sort -k 2 -n | tac

