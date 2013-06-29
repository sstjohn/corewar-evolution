#!/usr/bin/python -u

import bisect
import os
import random
import sys
import Corewar, Corewar.Benchmarking

COMPETITORS_PER_TOURN = 20
GAMES_PER_PAIR = 4
ROUNDS_PER_GAME = 10
COMPETITORS_DIR = "winners"
ELIMINATION_SOFT_CUTOFF = 1.5
ELIMINATION_HARD_CUTOFF = 3
MIN_USEFUL_STD_DEV = 150
MAX_TRIES = 100

if len(os.listdir(COMPETITORS_DIR)) > 1500:
	COMPETITORS_TO_ELIMINATE = 15
else:
	COMPETITORS_TO_ELIMINATE = 10

competitors_destroyed = 0

def destroy_competitor(warrior):
	print "destroying %s (with score %d)" % (warrior[0], warrior[1])
	os.remove(warrior[0])

def eliminate_failures(results):
	global competitors_destroyed
	avg = float(reduce(lambda x, y: x + y, map(lambda x: x[1], results))) / float(len(results))
	std_dev = (float(reduce(lambda x, y: x + y, map(lambda x: (float(x[1]) - avg) ** 2, results))) / float(len(results) - 1)) ** 0.5
	print "average score is %4.03d" % avg
	print "standard deviation is %4.03d" % std_dev 
	if std_dev < MIN_USEFUL_STD_DEV:
		print "insufficient deviation in results. results voided."
		return 0

	while(results[-1][1] < (avg - (float(ELIMINATION_SOFT_CUTOFF) * std_dev))) and competitors_destroyed < COMPETITORS_TO_ELIMINATE:
		if False and results[-1][1] < (avg - (float(ELIMINATION_HARD_CUTOFF) * std_dev)):
			destroy_competitor(results.pop())
			competitors_destroyed += 1
		else:
			destruction_num = (((avg - float(results[-1][1])) / std_dev) - float(ELIMINATION_SOFT_CUTOFF))
			destruction_denom = float(ELIMINATION_HARD_CUTOFF) - float(ELIMINATION_SOFT_CUTOFF)
			print "destruction probibility for %s is %4.02f / %04.02f" % (results[-1][0], destruction_num, destruction_denom)
			if random.random() < (destruction_num / destruction_denom):
				destroy_competitor(results.pop())
				competitors_destroyed += 1
			else:
				break

def run_comp():
	parser = Corewar.Parser(coresize=8000,
								maxprocesses=8000,
								maxcycles=80000,
								maxlength=100,
								mindistance=100,
								standard=Corewar.STANDARD_88)
	try:
		warriors = [[COMPETITORS_DIR + "/" + x, parser.parse_file(COMPETITORS_DIR + "/" + x), 0] 
				for x in random.sample(os.listdir(COMPETITORS_DIR), COMPETITORS_PER_TOURN)]
	except Corewar.WarriorParseError, e:
		print e
		sys.exit(1)

	pairings = range(1, COMPETITORS_PER_TOURN)
	for i in range((COMPETITORS_PER_TOURN - 1)):
		top = [0] + pairings[:(COMPETITORS_PER_TOURN / 2) - 1]
		bottom = pairings[len(top) - 1:][::-1]
		for j in range(COMPETITORS_PER_TOURN / 2):
			top_score_delta, bottom_score_delta = run_games(warriors[top[j]][1], warriors[bottom[j]][1])
			warriors[top[j]][2] += top_score_delta
			warriors[bottom[j]][2] += bottom_score_delta
		pairings.append(pairings.pop(0))

	print
	print "elimination results!"
	print "--------------------"
	print
	
	warriors.sort(key=lambda x: x[2], reverse=True)
	for w in warriors:
		print "%s: %4d" % (w[0], w[2])

	print

	return eliminate_failures([[x[0], x[2]] for x in warriors])

def run_games(left, right):
	mars = Corewar.Benchmarking.MARS_88(coresize=8000,
						maxprocesses=8000,
						maxcycles=80000,
						mindistance=100,
						maxlength=100)
	left_score = 0
	right_score = 0
	for i in range(GAMES_PER_PAIR):
		if i % 2 == 0:
			warriors = (left, right)
		else:
			warriors = (right, left)
		results = mars.run(warriors, rounds = ROUNDS_PER_GAME)
		if i % 2 == 0:
			left_score += (5 * results[0][0] + results[0][2])
			right_score += (5 * results[1][0] + results[1][2])
		else:
			left_score += (5 * results[1][0] + results[1][2])
			right_score += (5 * results[0][0] + results[0][2])
	
	return left_score, right_score

if __name__ == "__main__":
	random.seed()
	comp_tries = 0
	while competitors_destroyed < COMPETITORS_TO_ELIMINATE:
		run_comp()
		if competitors_destroyed < COMPETITORS_TO_ELIMINATE:
			comp_tries += 1
			if comp_tries % 10 == 0:
				os.system("git pull --no-edit -X theirs")
				if comp_tries > MAX_TRIES:
					sys.exit(0)
