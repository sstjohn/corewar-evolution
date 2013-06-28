#!/usr/bin/env python

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

PARENTAL_CHOICE_SEQ = [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4]
MUTATION_CHANCE = .25
CHILDREN_PER_GEN = 64
ADAM_FILE = "imp"
EVE_FILE = "imp"
ROUNDS_PER_GEN_PER_CHILD = 1
WIN_TO_TIE_RATIO = 100

superwinners = []

def get_mutator():
	return random.choice([flip_mutator, drop_mutator, dupe_mutator])

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

	#cutpt = random.randint(0, min(a_len, b_len)) * 14

	#return a[:cutpt] + b[cutpt:]

	a_cutpt = random.randint(1, a_len) * 14
	b_cutpt = random.randint(1, b_len) * 14

	return a[:a_cutpt] + b[b_cutpt:]

def flip_mutator(dna):
	strpos = random.randint(0, len(dna) - 1)
	amt = random.randint(0, 10)

	new_dna = dna[0:strpos]
	new_dna += str((int(dna[strpos]) + (amt - 5)) % 10)
	new_dna += dna[strpos + 1:]
	return new_dna

def drop_mutator(dna):
	if len(dna) < 29:
		return flip_mutator(dupe_mutator(dna))
	inst = random.randint(0, (len(dna) / 14) - 1)
	new_dna = dna[:inst * 14]
	new_dna += dna[(inst + 1) * 14:]
	return new_dna

def dupe_mutator(dna):
	if not len(dna) < 1400:
		return flip_mutator(drop_mutator(dna))
	inst = random.randint(0, (len(dna) / 14) - 1)
	new_dna = dna[:inst * 14]
	new_dna += dna[inst * 14:(inst + 1) * 14]
	new_dna += dna[inst * 14:]
	return new_dna

def evolve(a, b):
	child = spawn(a, b)
	while random.random() <= MUTATION_CHANCE:
		child = get_mutator()(child)
	return unparse(child)


def gengen(lastgen, winners):
	parents = []
	sw = 0
        for i in range(4):
		if winners[i][0] == 0:
			winners[i] = superwinners[sw]
			sw += 1
			print "substituting sw %s" % str(winners[i])
		with open(winners[i][1], "r") as f:
			parents.append(warrior_read(f))
	nextgen = str(lastgen + 1)
	os.mkdir(nextgen)
	for i in range(CHILDREN_PER_GEN):
		mother = random.choice(PARENTAL_CHOICE_SEQ)
		father = random.choice([x for x in PARENTAL_CHOICE_SEQ if x != mother])
		#father = random.choice(PARENTAL_CHOICE_SEQ)
		with open(nextgen + "/" + str(i + 1), "w") as f:
			f.write(evolve(parents[mother - 1], parents[father - 1]))


def rungen(gen):
	global superwinners
	parser = Corewar.Parser(coresize=80000,
                                maxprocesses=8000,
                                maxcycles=160000,
                                maxlength=200,
                                mindistance=200,
                                standard=Corewar.STANDARD_88)
	warriors = []
	for i in range(CHILDREN_PER_GEN):
		try:
			warriors.append(parser.parse_file(str(gen) + "/" + str(i + 1)))
			if parser.warnings:
		                for warning in parser.warnings:
                		    print 'Warning: %s' % warning
                		print '\n'
		except Corewar.WarriorParseError, e:
            		print e
            		sys.exit(1)

	mars = Corewar.Benchmarking.MARS_88(coresize=80000,
                                            maxprocesses=8000,
                                            maxcycles=160000,
                                            mindistance=200,
                                            maxlength=200)
	result = mars.mw_run(warriors, max(1, int(ROUNDS_PER_GEN_PER_CHILD * CHILDREN_PER_GEN)))
	scores = zip(range(len(result)), [x[0] * WIN_TO_TIE_RATIO + x[2] for x in result[:-1]])
	scores.sort(key=lambda x: x[1], reverse=True)
	superwinners += map(lambda x: [x[1], str(gen) + "/" + str(x[0] + 1)], scores)
	superwinners.sort(key=lambda x: x[0], reverse=True)
	superwinners = superwinners[:64]
	winners = scores[0:4]
	print "gen %d winners:" % gen
	for x in winners:
		print "\t%s: %s" % (x[0] + 1, x[1])
	print
	
	return map(lambda x: [x[1], str(gen) + "/" + str(x[0] + 1)], winners)

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

if __name__ == "__main__":
	if len(sys.argv) > 1:
		generations_to_run = int(sys.argv[1])
	else:
		generations_to_run = 10
	random.seed()
	initial_setup()
	for i in range(generations_to_run):
		winners = rungen(i)
		gengen(i, winners)
