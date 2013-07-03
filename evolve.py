#!/usr/bin/python -u

import bisect
import os
import random
import sys
import Corewar, Corewar.Benchmarking

from math import ceil

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

ROUNDS_PER_GAME=3
ERA_COMP_ROUNDS = 4
MUTATION_CHANCE = .1
CHILDREN_PER_GEN = 16
ADAM_FILE = "dat"
EVE_FILE = "dat"
SPLICE_MECH_ONE_PROB = .4
DIGIT_MUNGE_PROB = (1.5 / 14.0)
INTERERA_SW_AGE_PENALTY = 0
RADIATION_THRESH = 3.75
MIN_REPRODUCTIVE_STDDEV = -.5
MAX_RADIATION_MUTATION_PROB = .85
EXTINCTION_LEVEL_RADIATION_THRESHOLD = 1
EXTINCTION_LEVEL_RADIATION_ROUNDS = 10
PROGENITOR_DIR = "winners"
DUPEDROP_MUTATOR_PROB = 0.6
SCORING_EXP = 2
SINGLE_GEN_INCEST_CHANCE = .05
CLONE_CHANCE = .05
MUNGE_ROUNDS_MAX = 85

elites = None
def print_elites():
	avg = 0
	print "\nelites!\n-------------\n"
	for i in range(len(elites)):
		print "%d - score: %f, fname %s" % (i, elites[i][2], elites[i][0])
		avg += elites[i][2]

	avg /= float(len(elites))
	std_dev = (float(reduce(lambda x, y: x + y, map(lambda x: (float(x[2]) - avg) ** 2, elites))) / float(len(elites) - 1)) ** 0.5

	print
	print "era average: %4.02f" % avg
	print "era std dev: %4.02f" % std_dev
	if 0 != std_dev:
		print "era dev del: %4.02f" % (((elites[0][2] - avg) / std_dev) - ((elites[-1][2] - avg) / std_dev))

	print

def get_mutator():
	return random.choice([flip_mutator, swap_mutator, dupedrop_mutator, irev_mutator, dupe_mutator, drop_mutator, segrev_mutator, munge_mutator])

def munge_mutator(dna):
	new_dna = dna
	i = 0

	#haha, this is lazy
	while i < (random.random() * MUNGE_ROUNDS_MAX):
		m = get_mutator()
		if m != munge_mutator:
			new_dna = m(new_dna)
			i += 1
	return new_dna

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
		result += str(int(line[5:8]))
		mode = b_modes[int(line[8]) % len(b_modes)]
		val = int(line[11:14])
		if (not inst in UNARY_OPS) or (not mode == "$") or (not val == 0):
			result += ", "
			if not mode == "$":
				result += mode
			if int(line[9]) % 2 == 1:
				result += "-"
			result += str(val)
	return result + "\n"

def warrior_load(fname):
	with open(fname, "r") as f:
		return warrior_read(f)
	
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

def segrev_mutator(dna):
	inst_cnt = len(dna) / 14
	if inst_cnt < 5:
		return swap_mutator(irev_mutator(dna))
	
	seg_len = (inst_cnt / 3)
	seg_offset = random.randint(0, inst_cnt - seg_len)

	new_dna = dna[:(seg_offset * 14)]
	new_dna += dna[(seg_offset + seg_len) * 14:seg_offset * 14:-1]
	new_dna += dna[(seg_offset + seg_len) * 14:]

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
	strpos = random.randint(0, (len(dna) / 14) - 1)
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
	if random.random() > CLONE_CHANCE:
		child_l, child_r = spawn(a, b)
	else:
		child_l = a
		child_r = b
	if random.random() <= (MUTATION_CHANCE + (radiation  * MAX_RADIATION_MUTATION_PROB)):
		child_l = get_mutator()(child_l)
	if random.random() <= (MUTATION_CHANCE + (radiation  * MAX_RADIATION_MUTATION_PROB)):
		child_r = get_mutator()(child_r)
	if random.random() <= SINGLE_GEN_INCEST_CHANCE:
		return evolve(child_l, child_r, radiation)
	return (unparse(child_l), unparse(child_r))

def report(scores):
	sum = reduce(lambda x, y: x + y, map(lambda x: x[1], scores))
	avg = sum / len(scores)
	print "\t----------"
	print "\tsum: %d" % sum
	print "\tavg: %d" % avg
	print

def score_pick(scores, exclude_ind = None):
	avg = float(reduce(lambda x, y: x + y, map(lambda x: x[2], scores))) / float(len(scores))
	std_dev = (float(reduce(lambda x, y: x + y, map(lambda x: (float(x[2]) - avg) ** 2, scores))) / float(len(scores) - 1)) ** 0.5
	
	if std_dev != 0:
		rel_scores = map(lambda x: float(max(0.0, ((float(x[2]) - avg) / std_dev) - MIN_REPRODUCTIVE_STDDEV) ** SCORING_EXP if exclude_ind == None or scores[exclude_ind] != x else 0.0), scores)

		partitions = []
		sum = reduce(lambda x, y: x + y, map(lambda x: x if x > 0 else 0, rel_scores))
		running_total = 0.0
		for i in range(len(rel_scores)):
			running_total += rel_scores[i]
			partitions.append(running_total)
		picked = bisect.bisect(partitions, random.random() * running_total)
	else:
		picked = random.randint(1, len(scores)) - 1

	return picked

def gengen(lastgen, scores):
	parents = []
	nextgen = str(lastgen + 1)
	os.mkdir(nextgen)

	avg = float(reduce(lambda x, y: x + y, map(lambda x: x[2], scores))) / float(len(scores))
	std_dev = (float(reduce(lambda x, y: x + y, map(lambda x: (float(x[2]) - avg) ** 2, scores))) / float(len(scores) - 1)) ** 0.5

	if std_dev != 0:
		win_loss_dev = float(scores[0][2] - scores[-1][2]) / std_dev
	else:
		win_loss_dev = 0.0

	print "deviation spread is %2.04f" % win_loss_dev

	if win_loss_dev < RADIATION_THRESH:
		radiation = float((RADIATION_THRESH - win_loss_dev) / RADIATION_THRESH)
		print "radiation now at %f" % radiation
	else:
		radiation = 0

	for i in range(0, CHILDREN_PER_GEN, 2):
		mother = score_pick(scores)
		father = score_pick(scores, mother)
		l, r = evolve(scores[mother][1], scores[father][1], radiation)
		with open(nextgen + "/" + str(i + 1), "w") as f:
			f.write(l)
		with open(nextgen + "/" + str(i + 2), "w") as f:
			f.write(r)
	return radiation



def rungen(gen):
	global elites
	
	warriors = [[str(gen) + "/" + str(x + 1), warrior_load(str(gen) + "/" + str(x + 1)), 0, 0]
			for x in range(CHILDREN_PER_GEN)]

	if elites == None:
		elites = warriors
	else:
		elites = [[x[0], x[1], 0, 0] for x in elites]


	for i in range(CHILDREN_PER_GEN - 1):
		for j in range(CHILDREN_PER_GEN):
			child_res, e_res = run_games(warriors[j][1], elites[j][1])
			warriors[j][2] += child_res[0]
			warriors[j][3] += child_res[1] + child_res[0] + child_res[2]
			elites[j][2] += e_res[0]
			elites[j][3] += e_res[1] + e_res[0] + e_res[2]
			
		warriors.append(warriors.pop(0))

	pairings = range(1, CHILDREN_PER_GEN)
        for i in range((CHILDREN_PER_GEN - 1)):
                top = [0] + pairings[:(CHILDREN_PER_GEN / 2) - 1]
                bottom = pairings[len(top) - 1:][::-1]
                for j in range(CHILDREN_PER_GEN / 2):
                        top_res, bottom_res = run_games(warriors[top[j]][1], warriors[bottom[j]][1])
                        warriors[top[j]][2] += top_res[0]
			warriors[top[j]][3] += top_res[0] + top_res[1] + top_res[2]
                        warriors[bottom[j]][2] += bottom_res[0]
			warriors[bottom[j]][3] += bottom_res[1] + bottom_res[1] + bottom_res[2]
			top_res, botton_res = run_games(elites[top[j]][1], elites[bottom[j]][1])
			elites[top[j]][2] += top_res[0]
			elites[top[j]][3] += top_res[1] + top_res[0] + top_res[2]
			elites[bottom[j]][2] += bottom_res[0]
			elites[bottom[j]][3] += bottom_res[1] + bottom_res[0] + bottom_res[2]
                pairings.append(pairings.pop(0))

	elites = [[x[0], x[1], float(x[2]) / float(x[3])] for x in elites]
	warriors = [[x[0], x[1], float(x[2]) / float(x[3])] for x in warriors]

	elites.sort(key=lambda x: x[2], reverse=True)
	warriors.sort(key=lambda x: x[2], reverse=True)

	print "gen %d:" % gen
	print "\twarriors\t\telite"
	print "\t=======\t\t\t====="
	for (x, sw) in zip(warriors, elites):
		print "\t%s:\t%3.02f\t\t%s:\t%3.02f" % (x[0], x[2], sw[0], sw[2])
	print
	
	elites = warriors + elites
	elites.sort(key=lambda x: x[2], reverse=True)
	elites = elites[:CHILDREN_PER_GEN]

	return warriors

parser = Corewar.Parser(coresize=8000,
			maxprocesses=8000,
			maxcycles=80000,
			maxlength=100,
			mindistance=100,
			standard=Corewar.STANDARD_88)

mars = Corewar.Benchmarking.MARS_88(coresize=8000,
					maxprocesses=8000,
					maxcycles=80000,
					mindistance=100,
					maxlength=100)
def run_games(left, right):
		l = parser.parse(unparse(left))
		r = parser.parse(unparse(right))
		tmp = mars.run((l, r), rounds = ROUNDS_PER_GAME, seed = int(ceil(((2 ** 31) - 101) * random.random() + 100)))
		l_results_1 = tmp[0]
		r_results_1 = tmp[1]
		tmp = mars.run((r, l), rounds = ROUNDS_PER_GAME, seed = int(ceil(((2 ** 31) - 101) * random.random() + 100)))
		l_results_2 = tmp[0]
		r_results_2 = tmp[1]

		return (map(lambda (x, y): x + y, zip(l_results_1, l_results_2)),
			map(lambda (x, y): x + y, zip(r_results_1, r_results_2)))


def save_progenitors():
	global elites
	os.system("git pull --no-edit -X theirs")
	if PROGENITOR_DIR != None:
		for w in elites:
			sname = w[0]
			tmp_dname = PROGENITOR_DIR + "/" + sname.replace("/","")
			dname = tmp_dname
			ext="a"
			while os.path.exists(dname):
				dname = tmp_dname + ext
				if ext[-1] == "z":
					add_letters = 1
					ext = ext[:-1]
					while ext[-1] == "z":
						add_letters = add_letters + 1
						ext = ext[:-1]
					if len(ext) == 0:
						ext = "a"
					else:
						ext = ext[:-1] + str(chr(ord(ext[-1])))
					ext = ext + ("a" * add_letters)
				else:
					ext = ext[:-1] + str(chr(ord(ext[-1]) + 1))
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
def era_comp(winners):
	global supperwinners
	warriors = [[x[0], x[1], 0] for x in (winners + elites)]
	parser = Corewar.Parser(coresize=8000,
								maxprocesses=8000,
								maxcycles=80000,
								maxlength=100,
								mindistance=100,
								standard=Corewar.STANDARD_88)
	print "beginning end-of-era selection...",

	pairings = range(1, len(warriors))
	for i in range(len(warriors) - 1):
		top = [0] + pairings[:(len(warriors) / 2) - 1]
		bottom = pairings[len(top) - 1:][::-1]
		for j in range(len(warriors) / 2):
			for _ in range(ERA_COMP_ROUNDS):
				top_score_delta, bottom_score_delta = run_games(warriors[top[j]][1], warriors[bottom[j]][1])
				warriors[top[j]][2] += top_score_delta
				warriors[bottom[j]][2] += bottom_score_delta
		pairings.append(pairings.pop(0))

	warriors = [[x[0], x[1], float(x[2]) / (2 * float(ERA_COMP_ROUNDS))] for x in warriors]

	print
	print
	print "selection results!"
	print "--------------------"
	print

	warriors.sort(key=lambda x: x[2], reverse=True)
	for w in warriors:
			print "%s: %4d" % (w[0], w[2])

	print

	return warriors

def era_gen(g, prev_gen):
	global elites
	i = 0

	potential_parents = era_comp(prev_gen)
	gengen(g - 1, potential_parents)
	elites = potential_parents[:CHILDREN_PER_GEN]

	print "======================="
	print "it's the end of an era!"
	print "======================="
	print
	print_elites()

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

	print_elites()
