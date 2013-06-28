#!/usr/bin/python

import bisect
import os
import random
import sys
import Corewar, Corewar.Benchmarking

UNARY_OPS = ["DAT","JMP","SPL"]
INSTRUCTIONS = 		 {"DAT": [["#", "<"], ["#", "<"]],
			  "MOV": [["$", "#", "@", "<"], ["$", "@", "<"]],
			  "ADD": [["$", "#", "@", "<"], ["$", "@", "<"]],
			  "SUB": [["$", "#", "@", "<"], ["$", "@", "<"]],
			  "CMP": [["$", "#", "@", "<"], ["$", "@", "<"]],
			  "SLT": [["$", "#", "@", "<"], ["$", "@", "<"]],
			  "JMP": [["$", "@", "<"], ["$", "#", "@", "<"]],
			  "JMZ": [["$", "@", "<"], ["$", "#", "@", "<"]],
			  "JMN": [["$", "@", "<"], ["$", "#", "@", "<"]],
			  "DJN": [["$", "@", "<"], ["$", "#", "@", "<"]],
			  "SPL": [["$", "@", "<"], ["$", "#", "@", "<"]]}

MUTATION_CHANCE = .10
CHILDREN_PER_GEN = 75
WINNERS_PER_GEN = 50
ADAM_FILE = "imp"
EVE_FILE = "scanner"
ROUNDS_PER_GEN_PER_CHILD = 3
WIN_POINTS = 10
TIE_POINTS = 1
LOSS_POINTS = -3
SCORE_PICKING_EXPONENT = 1.25
SUPERWINNER_SELECTION_PROB = 0.001
SPLICE_MECH_ONE_PROB = .6
DIGIT_MUNGE_PROB = (1.5 / 14.0)

superwinners = []
def print_superwinners():
	print "\nsuperwinners!\n-------------\n"
	for i in range(len(superwinners)):
		print "%d - score: %d, fname %s" % (i, superwinners[i][0], superwinners[i][1])

def get_mutator():
	return random.choice([flip_mutator, swap_mutator])

def line_parse(i):
	parts = i.replace(",", " ").split()
	if len(parts) == 0:
		return ""
	if parts[0][0] == ';':
		return ""
	instruction = -1
	try:
		instruction = INSTRUCTIONS.keys().index(parts[0])
		a_modes, b_modes = INSTRUCTIONS[parts[0]]
	except:
		print "Unknown instruction: %s" % parts[0]
		return ""
	
	if parts[1][0] in a_modes:
		a_mode = a_modes.index(parts[1][0])
		a_val = int(parts[1][1:])
	else:
		a_mode = 0
		a_val = int(parts[1])
	if a_val < 0:
		a_val = -a_val
		a_neg = 1
	else:
		a_neg = 0
		
	if len(parts) < 3 or parts[2][0] == ';':
		b_mode = 0
		b_val = 0
	elif parts[2][0] in b_modes:
		b_mode = b_modes.index(parts[2][0])
		b_val = int(parts[2][1:])
	else:
		b_mode = 0
		b_val = int(parts[2])
	if b_val < 0:
		b_val = -b_val
		b_neg = 1
	else:
		b_neg = 0

	return "%.2d%.1d%.1d%.4d%.1d%.1d%.4d" % (instruction, a_mode, a_neg, a_val, b_mode, b_neg, b_val)

def unparse(dna):
	result = ";redcode\n;assert 1"
	while len(dna) > 0:
		result += "\n\t"
		line = dna[:14]
		dna = dna[14:]
		inst = INSTRUCTIONS.keys()[int(line[0:2]) % len(INSTRUCTIONS)]
		a_modes, b_modes = INSTRUCTIONS[inst]
		result += inst
		result += " "
		mode = a_modes[int(line[2]) % len(a_modes)]
		if not mode == "$":
			result += mode
		if int(line[3]) % 2 == 1:
			result += "-"
		result += str(int(line[4:8]))
		mode = b_modes[int(line[8]) % len(b_modes)]
		val = int(line[10:14])
		if (not inst in UNARY_OPS) or (not mode == "$") or (not val == 0):
			result += ", "
			if not mode == "$":
				result += mode
			if int(line[9]) % 2 == 1:
				result += "-"
			result += str(val)
	return result + "\n"
	
def warrior_read(f):
	dna = ""
	for line in f:
		dna += line_parse(line)

	return dna

def spawn(a, b):
	a_len = len(a) / 14
	b_len = len(b) / 14
	result = ""
	while len(result) == 0:
		if random.random() < SPLICE_MECH_ONE_PROB:
			cutpt = random.randint(0, max(a_len, b_len)) * 14
			result = a[:cutpt] + b[cutpt:]
		else:
			a_cutpt = random.randint(0, a_len) * 14
			b_cutpt = random.randint(0, b_len) * 14
			result = a[:a_cutpt] + b[b_cutpt:]

	while len(result) > (200 * 14):
		result = drop_mutator(result)
	return result

def swap_mutator(dna):
	inst_cnt = len(dna) / 14
	if inst_cnt < 2:
		return flip_mutator(dupe_mutator(dna))
	choices = random.sample(range(inst_cnt), 2)
	if choices[0] > choices[1]:
		choices = [choices[1], choices[0]]

	new_dna = dna[:choices[0] * 14]
	new_dna += dna[choices[1] * 14:(choices[1] + 1) * 14]
	new_dna += dna[(choices[0] + 1) * 14:choices[1] * 14]
	new_dna += dna[choices[0] * 14:(choices[0] + 1) * 14]
	new_dna += dna[(choices[1] + 1) * 14:]
	return new_dna

def flip_mutator(dna):
	strpos = random.randint(0, len(dna) / 14)
	first_part = dna[:(strpos * 14)]
	mutatee = dna[strpos * 14:(strpos + 1) * 14]
	sec_part = dna[(strpos + 1) * 14:]
	
	mutated = ""
	for c in mutatee:
		if random.random() < DIGIT_MUNGE_PROB:
			mutated += str(random.randint(0, 9))
		else:
			mutated += c

	return first_part + mutated + sec_part

def drop_mutator(dna):
	if len(dna) < 29:
		return flip_mutator(dupe_mutator(dna))
	inst = random.randint(0, (len(dna) / 14) - 1)
	new_dna = dna[:inst * 14]
	new_dna += dna[(inst + 1) * 14:]
	return new_dna

def dupe_mutator(dna):
	if not len(dna) < 1000:
		return flip_mutator(drop_mutator(dna))
	inst = random.randint(0, (len(dna) / 14) - 1)
	new_dna = dna[:inst * 14]
	new_dna += dna[inst * 14:(inst + 1) * 14]
	new_dna += dna[inst * 14:]
	return new_dna

def evolve(a, b):
	child = spawn(a, b)
	if random.random() <= MUTATION_CHANCE:
		child = get_mutator()(child)
	return unparse(child)

def report(scores):
	sum = reduce(lambda x, y: x + y, map(lambda x: x[1], scores))
	avg = sum / len(scores)
	print "\t----------"
	print "\tsum: %d" % sum
	print "\tavg: %d" % avg
	print

def score_pick(scores, exclude_ind = None, no_sw = False):
	global superwinners

	if not no_sw and random.random() < SUPERWINNER_SELECTION_PROB:
		scores = superwinners
		exclude_ind = None

	sum = 0.0
	partitions = []
	for i in range(len(scores)):
		if i != exclude_ind:
			sum += (max(0, scores[i][0]) ** SCORE_PICKING_EXPONENT) #* (len(scores) - i))
		partitions.append(sum)

	if sum == 0:
		if not no_sw:
			return score_pick(superwinners, None, True)
		else:
			picked = random.randint(1, len(scores)) - 1
	else:
		score_choice = random.random() * sum

		picked = bisect.bisect(partitions, score_choice)

	with open(scores[picked][1], "r") as f:
		warrior = warrior_read(f)
	return (warrior, picked)

def gengen(lastgen, scores):
	global superwinners

	parents = []
	nextgen = str(lastgen + 1)
	os.mkdir(nextgen)
	for i in range(CHILDREN_PER_GEN):
		mother, exclude = score_pick(scores[0:WINNERS_PER_GEN])
		father, _ = score_pick(scores[0:WINNERS_PER_GEN], exclude)
		with open(nextgen + "/" + str(i + 1), "w") as f:
			f.write(evolve(mother, father))

def rungen(gen):
	global superwinners
	parser = Corewar.Parser(coresize=160000,
                                maxprocesses=8000,
                                maxcycles=160000,
                                maxlength=200,
                                mindistance=200,
                                standard=Corewar.STANDARD_88)
	warriors = []
	for i in range(CHILDREN_PER_GEN):
		try:
			warriors.append(parser.parse_file(str(gen) + "/" + str(i + 1)))
			if len(parser.warnings) > 0:
		                for warning in parser.warnings:
                		    print 'Warning: %s' % warning
                		print '\n'
		except Corewar.WarriorParseError, e:
            		print e
            		sys.exit(1)

	mars = Corewar.Benchmarking.MARS_88(coresize=160000,
                                            maxprocesses=8000,
                                            maxcycles=160000,
                                            mindistance=200,
                                            maxlength=200)
	result = mars.mw_run(warriors, max(1, int(ROUNDS_PER_GEN_PER_CHILD * CHILDREN_PER_GEN)))
	scores = zip(range(len(result)), [x[0] * WIN_POINTS + x[1] * LOSS_POINTS + x[2] * TIE_POINTS for x in result[:-1]])
	scores.sort(key=lambda x: x[1], reverse=True)
	superwinners = map(lambda x: [x[1], str(gen) + "/" + str(x[0] + 1)], scores) + superwinners
	superwinners.sort(key=lambda x: x[0], reverse=True)
	superwinners = superwinners[:CHILDREN_PER_GEN]
	winners = scores[0:4]
	print "gen %d winners:" % gen
	for x in winners:
		print "\t%s: %s" % (x[0] + 1, x[1])
	report(scores)
	print
	
	return map(lambda x: [x[1], str(gen) + "/" + str(x[0] + 1)], scores)

def initial_setup():
	os.mkdir("0")
	adam = None
	with open(ADAM_FILE, "r") as f:
		adam = warrior_read(f)

	eve = None
	with open(EVE_FILE, "r") as f:
		eve = warrior_read(f)

	for i in range(CHILDREN_PER_GEN):
		fname = "0/" + str(i + 1)
		with open(fname, "w") as f:
                        f.write(evolve(adam, eve))
		superwinners.append([0, fname])
def era_gen(g):
	os.mkdir(str(g))
	i = 0
	for s in superwinners:
		i += 1
		with open(str(g) + "/" + str(i), "w") as f:
			with open(s[1], "r") as source:
				f.write(source.read())
	print "======================="
	print "it's the end of an era!"
	print "======================="
	print
	print_superwinners()

if __name__ == "__main__":
	if len(sys.argv) > 1:
		generations_to_run = int(sys.argv[1])
	else:
		generations_to_run = 10
	if len(sys.argv) > 2:
		eras = int(sys.argv[2])
	else:
		eras = 1
	random.seed()
	initial_setup()
	for e in range(eras):
		if e > 0:
			era_gen(e * generations_to_run)
		for i in range(generations_to_run):
			winners = rungen(generations_to_run * e + i)
			if (i + 1) != generations_to_run:
				gengen(generations_to_run * e + i, winners)

	print_superwinners()
