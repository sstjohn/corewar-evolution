#!/usr/bin/python -u

import bisect
import os
import random
import sys
import Corewar, Corewar.Benchmarking

UNARY_OPS = ["DAT","JMP","SPL"]
INSTRUCTIONS =		 {"DAT": [["#", "<"], ["#", "<"]],
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

MUTATION_CHANCE = .05
CHILDREN_PER_GEN = 10
WINNERS_PER_GEN = 10
ADAM_FILE = "jmp"
EVE_FILE = "dat"
ROUNDS_PER_GEN = 5
SPLICE_MECH_ONE_PROB = .4
DIGIT_MUNGE_PROB = (1.5 / 14.0)
INTERERA_SW_AGE_PENALTY = 0.01
RADIATION_THRESH = 1.75
MAX_RADIATION_MUTATION_PROB = .9
TIE_PENALTY = 1.9
REPRODUCTION_SCORE_MIN = 0
EXTINCTION_LEVEL_RADIATION_THRESHOLD = 0.7
EXTINCTION_LEVEL_RADIATION_ROUNDS = 25
PROGENITOR_DIR = "winners"
DUPEDROP_MUTATOR_PROB = 0.75

superwinners = []
def print_superwinners():
	print "\nsuperwinners!\n-------------\n"
	for i in range(len(superwinners)):
		print "%d - score: %f, fname %s" % (i, superwinners[i][0], superwinners[i][1])

def get_mutator():
	return random.choice([flip_mutator, swap_mutator, dupedrop_mutator, irev_mutator])

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
	result_l = ""
	result_r = ""
	while len(result_l) == 0 or len(result_r) == 0:
		if random.random() < SPLICE_MECH_ONE_PROB:
			cutpt = random.randint(0, max(a_len, b_len)) * 14
			result_l = a[:cutpt] + b[cutpt:]
			result_r = b[:cutpt] + a[cutpt:]
		else:
			a_cutpt = random.randint(0, a_len) * 14
			b_cutpt = random.randint(0, b_len) * 14
			result_l = a[:a_cutpt] + b[b_cutpt:]
			result_r = b[:b_cutpt] + a[a_cutpt:]

	while len(result_l) > (100 * 14):
		result_l = drop_mutator(result_l)
	while len(result_r) > (100 * 14):
		result_r = drop_mutator(result_r)
	return (result_l, result_r)

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
	strpos = random.randint(0, (len(dna) / 14) - 1)
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

def irev_mutator(dna):
	inst_no = random.randint(0, (len(dna) / 14) - 1)
	first_part = dna[:(strpos * 14)]
	mutatee = dna[strpos * 14:(strpos + 1) * 14]
	sec_part = dna[(strpos + 1) * 14:]

	return first_part + mutatee[::-1] + sec_part

def dupedrop_mutator(dna):
	new_dna = ""
	for i in range(len(dna) / 14):
		if (i + 1) * 14 < len(dna) and dna[i * 14:(i + 1)*14] == dna[(i + 1) * 14:(i + 2) * 14] and random.random() < DUPEDROP_MUTATOR_PROB:
			pass
		else:
			new_dna += dna[i * 14:(i + 1) * 14]
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

def evolve(a, b, radiation = 0):
	child_l, child_r = spawn(a, b)
	while random.random() <= (MUTATION_CHANCE + (((radiation / (RADIATION_THRESH - 1)) * MAX_RADIATION_MUTATION_PROB))):
		child_l = get_mutator()(child_l)
	while random.random() <= (MUTATION_CHANCE + (((radiation / (RADIATION_THRESH - 1)) * MAX_RADIATION_MUTATION_PROB))):
		child_r = get_mutator()(child_r)
	return (unparse(child_l), unparse(child_r))

def report(scores):
	sum = reduce(lambda x, y: x + y, map(lambda x: x[1], scores))
	avg = sum / len(scores)
	print "\t----------"
	print "\tsum: %d" % sum
	print "\tavg: %d" % avg
	print

def score_pick(scores, exclude_ind = None, no_sw = False):
	global superwinners

	partitions = []
	sum = reduce(lambda x, y: x + y, map(lambda x: float(max(0.0, x[0])) if exclude_ind == None or scores[exclude_ind] != x else 0.0, scores))
	if sum == 0:
		if not no_sw:
			return score_pick(superwinners, None, True)
		else:
			picked = random.randint(1, len(scores)) - 1
	else:
		running_total = 0.0
		for i in range(len(scores)):
			if i != exclude_ind:
				running_total += ((max(0.0, float(scores[i][0]))) / sum)
			partitions.append(running_total)
		picked = bisect.bisect(partitions, random.random() * running_total)

	with open(scores[picked][1], "r") as f:
		warrior = warrior_read(f)
	return (warrior, picked)					

def gengen(lastgen, scores):
	global superwinners
	
	parents = []
	nextgen = str(lastgen + 1)
	os.mkdir(nextgen)
	if scores[0][0] < RADIATION_THRESH:
		radiation = RADIATION_THRESH - scores[0][0]
		print "radiation now at %f" % radiation
	else:
		radiation = 0
	for i in range(0, CHILDREN_PER_GEN, 2):
		mother, exclude = score_pick(scores[0:WINNERS_PER_GEN])
		father, _ = score_pick(scores[0:WINNERS_PER_GEN], exclude)
		l, r = evolve(mother, father, radiation)
		with open(nextgen + "/" + str(i + 1), "w") as f:
			f.write(l)
		with open(nextgen + "/" + str(i + 2), "w") as f:
			f.write(r)
	return radiation

def rungen(gen):
	global superwinners
	parser = Corewar.Parser(coresize=8000,
								maxprocesses=8000,
								maxcycles=80000,
								maxlength=100,
								mindistance=100,
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

	mars = Corewar.Benchmarking.MARS_88(coresize=8000,
											maxprocesses=8000,
											maxcycles=80000,
											mindistance=100,
											maxlength=100)
	results = mars.mw_run(warriors, max(1, int(ROUNDS_PER_GEN * CHILDREN_PER_GEN)))
	scores = []
	score_tot = 0.0
	for result in results[:-1]:
		score = 0.0
		for winners_cnt in range(len(result) - 1):
			score += float(result[winners_cnt]) * float(len(results) - (1 + winners_cnt))
		scores.append(score)
		score_tot += score
	avg = float(score_tot) / float(len(result) - 1)
	scores = zip(range(len(scores)), [x / max(avg, 1.0) for x in scores])
	scores.sort(key=lambda x: x[1], reverse=True)
	totes = reduce(lambda x, y: x + y, map(lambda x: x[1], scores))
	superwinners = map(lambda x: [x[1] * max(avg, 1.0), str(gen) + "/" + str(x[0] + 1)], scores) + superwinners
	superwinners.sort(key=lambda x: x[0], reverse=True)
	superwinners = superwinners[:CHILDREN_PER_GEN]
	winners = scores[0:4]
	print "gen %d winners:" % gen
	for x in winners:
		print "\t%02d: %4.2f " % (x[0] + 1, x[1])
	print
	
	return map(lambda x: [x[1], str(gen) + "/" + str(x[0] + 1)], filter(lambda x: x[1] >= REPRODUCTION_SCORE_MIN, scores))

def save_progenitors():
	global superwinners
	if PROGENITOR_DIR != None:
		for w in superwinners:
			sname = w[1]
			dname = PROGENITOR_DIR + "/" + sname.replace("/","")
			with open(sname, "r") as s:
				with open(dname, "w") as d:
					d.write(s.read())

def initial_setup():
	os.mkdir("0")
	adam = None
	progenitor_options = None
	if PROGENITOR_DIR != None:
		try:
			progenitor_options = os.listdir(PROGENITOR_DIR)
			adam = None
			eve = None
		except:
			pass

	if progenitor_options == None:
		with open(ADAM_FILE, "r") as f:
			adam = warrior_read(f)

		with open(EVE_FILE, "r") as f:
			eve = warrior_read(f)

	for i in range(0, CHILDREN_PER_GEN, 2):
		fname_l = "0/" + str(i + 1)
		fname_r = "0/" + str(i + 2)
		if progenitor_options != None:
			adam_file, eve_file = random.sample(progenitor_options, 2)
			with open(PROGENITOR_DIR + "/" + adam_file, "r") as f:
				adam = warrior_read(f)
			with open(PROGENITOR_DIR + "/" + eve_file, "r") as f:
				eve = warrior_read(f)
		child_l, child_r = evolve(adam, eve)
		with open(fname_l, "w") as f:
			f.write(child_l)
		with open(fname_r, "w") as f:
			f.write(child_r)
		superwinners.append([0, fname_l])
		superwinners.append([0, fname_r])

def era_gen(g, prev_gen):
	global superwinners
	os.mkdir(str(g))
	i = 0
	for s in random.sample(superwinners + prev_gen, CHILDREN_PER_GEN):
		i += 1
		with open(str(g) + "/" + str(i), "w") as f:
			with open(s[1], "r") as source:
				f.write(source.read())
	print "======================="
	print "it's the end of an era!"
	print "======================="
	print
	print_superwinners()
	superwinners = map(lambda x: [x[0] * (1.0 - INTERERA_SW_AGE_PENALTY), x[1]], superwinners)

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
	prev_gen_winners = []
	for e in range(eras):
		radioactive_rounds = 0
		if e > 0:
			era_gen(e * generations_to_run, prev_gen_winners)
			prev_gen_winners = []
		for i in range(generations_to_run):
			winners = rungen(generations_to_run * e + i)
			prev_gen_winners = winners
			if (i + 1) != generations_to_run:
				cur_rad = gengen(generations_to_run * e + i, winners)
				if cur_rad > EXTINCTION_LEVEL_RADIATION_THRESHOLD:
					radioactive_rounds += 1
				elif radioactive_rounds > 0 and cur_rad < (EXTINCTION_LEVEL_RADIATION_THRESHOLD / 2.0):
						radioactive_rounds -= 1
			if radioactive_rounds == EXTINCTION_LEVEL_RADIATION_ROUNDS:
				print "Extinction level event! Begining next era!"
				break

	save_progenitors()

	print_superwinners()
