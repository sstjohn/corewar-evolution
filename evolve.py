#!/usr/bin/python -u

import bisect
import os
import random
import sys

import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import Corewar, Corewar.Benchmarking

from math import ceil

from Warrior import Warrior

ROUNDS_PER_GAME=5
ERA_COMP_ROUNDS = 4
MUTATION_CHANCE = .1
CHILDREN_PER_GEN = 32
ADAM_FILE = "dat"
EVE_FILE = "dat"
SPLICE_MECH_ONE_PROB = .4
DIGIT_MUNGE_PROB = (2.0 / 14.0)
INTERERA_SW_AGE_PENALTY = 0
RADIATION_THRESH = 4
MIN_REPRODUCTIVE_STDDEV = -.5
MAX_RADIATION_MUTATION_PROB = .4
MAX_MUTATION_ROUNDS = 5
EXTINCTION_LEVEL_RADIATION_THRESHOLD = 1
EXTINCTION_LEVEL_RADIATION_ROUNDS = 10
PROGENITOR_DIR = "winners"
DUPEDROP_MUTATOR_PROB = 0.25
SCORING_EXP = 2
MUNGE_ROUNDS_MAX = 85
PROGENITORS_TO_SAVE = 16
CROSSOVER_CHANCE = .25

elites = None
def era_score_function(w):
    return (((float(w.lap_scores.wins) + 0.5 * float(w.lap_scores.ties))) + ((float(w.all_scores.ties) * 0.5 + float(w.all_scores.wins)))) / (float(w.all_scores.losses) + float(w.lap_scores.losses))

def gen_score_function(w):
    return  ((((float(w.lap_scores.ties) * 0.5 + float(w.lap_scores.wins)) / (float(w.lap_scores.wins) + float(w.lap_scores.ties) + float(w.lap_scores.losses)))) *
           float(w.lap_scores.lines))

def print_elites():
    avg = 0
    print "\nelites!\n-------------\n"
    for i in range(len(elites)):
        print "%d - score: %f, fname %s (%s, %s, %s) [w: %d, l: %d, t: %d, loc: %d]" % (i, era_score_function(elites[i]), elites[i].name, elites[i].parent_a_name, elites[i].parent_b_name, elites[i].mut_marks, elites[i].all_scores.wins, elites[i].all_scores.losses, elites[i].all_scores.ties, elites[i].all_scores.lines)
        avg += era_score_function(elites[i])

    avg /= float(len(elites))
    std_dev = (float(reduce(lambda x, y: x + y, map(lambda x: (era_score_function(x) - avg) ** 2, elites))) / float(len(elites) - 1)) ** 0.5

    print
    print "era average: %4.02f" % avg
    print "era std dev: %4.02f" % std_dev
    if 0 != std_dev:
        print "era dev del: %4.02f" % (((era_score_function(elites[0]) - avg) / std_dev) - ((era_score_function(elites[-1]) - avg) / std_dev))

    print

def get_mutator():
    return random.choice([flip_mutator, swap_mutator, dupedrop_mutator, irev_mutator, dupe_mutator, drop_mutator, segrev_mutator, munge_mutator, segdupe_mutator])

def munge_mutator(w):
    i = 0
    #haha, this is lazy
    while i < (random.random() * MUNGE_ROUNDS_MAX):
        m = get_mutator()
        if m != munge_mutator:
            w = m(w)
            i += 1
    return w

def warrior_load(fname, id=None, gen=None):
    with open(fname, "r") as f:
        return warrior_read(f, id=id, gen=gen)
    
def warrior_read(f, id=None, gen=None):
    return Warrior(code=f.read(), id=id, generation=gen)


def spawn(warrior_a, warrior_b, gen = None, id = None):
    a = warrior_a.dna
    if len(a) / 14 < 50:
        a += a

    b = warrior_b.dna
    if len(b) / 14 < 50:
        b += b
    result_l = ''
    result_r = ''

    cut_pt = random.randint(1, min(len(a) / 14, len(b) / 14))

    cur_parent = a
    i = 0
    while i < (len(cur_parent) / 14):
        result_l += cur_parent[i * 14:(i + 1) * 14]
        if i == cut_pt or random.random() < CROSSOVER_CHANCE:
            if cur_parent == a:
                cur_parent = b
            else:
                cur_parent = a
        i += 1

    cur_parent = b
    i = 0
    while i < (len(cur_parent) / 14):
        result_r += cur_parent[i * 14:(i + 1) * 14]
        if i == cut_pt or random.random() < CROSSOVER_CHANCE:
            if cur_parent == b:
                cur_parent = a
            else:
                cur_parent = b
        i += 1
    
    if id != None:
        r_id = id + 1
    else:
        r_id = None
    return (Warrior(dna=result_l, parent_a=warrior_a, parent_b=warrior_b, generation=gen, id=id), 
        Warrior(dna=result_r, parent_a=warrior_a, parent_b=warrior_b, generation=gen, id=r_id))

def swap_mutator(w):
    dna = w.dna
    inst_cnt = len(dna) / 14
    if inst_cnt < 2:
        return flip_mutator(dupe_mutator(w))
    w.add_mut_mark("sw")
    choices = random.sample(range(inst_cnt), 2)
    if choices[0] > choices[1]:
        choices = [choices[1], choices[0]]

    new_dna = dna[:choices[0] * 14]
    new_dna += dna[choices[1] * 14:(choices[1] + 1) * 14]
    new_dna += dna[(choices[0] + 1) * 14:choices[1] * 14]
    new_dna += dna[choices[0] * 14:(choices[0] + 1) * 14]
    new_dna += dna[(choices[1] + 1) * 14:]
    w.dna = new_dna
    return w

def segrev_mutator(w):
    dna = w.dna
    inst_cnt = len(dna) / 14
    if inst_cnt < 5:
        return swap_mutator(irev_mutator(w))
    
    w.add_mut_mark("sr")
    seg_len = (inst_cnt / 3)
    seg_offset = random.randint(0, inst_cnt - seg_len)

    new_dna = dna[:(seg_offset * 14)]
    new_dna += dna[(seg_offset + seg_len) * 14:seg_offset * 14:-1]
    new_dna += dna[(seg_offset + seg_len) * 14:]
    w.dna = new_dna
    return w

def flip_mutator(w):
    w.add_mut_mark("fl")

    dna = w.dna
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

    w.dna = first_part + mutated + sec_part
    return w

def irev_mutator(w):
    w.add_mut_mark("ir")
    dna = w.dna
    strpos = random.randint(0, (len(dna) / 14) - 1)
    first_part = dna[:(strpos * 14)]
    mutatee = dna[strpos * 14:(strpos + 1) * 14]
    sec_part = dna[(strpos + 1) * 14:]

    w.dna = first_part + mutatee[::-1] + sec_part
    return w

def dupedrop_mutator(w):
    w.add_mut_mark("dd")
    dna = w.dna
    new_dna = ""
    for i in range(len(dna) / 14):
        if (i + 1) * 14 < len(dna) and dna[i * 14:(i + 1)*14] == dna[(i + 1) * 14:(i + 2) * 14] and random.random() < DUPEDROP_MUTATOR_PROB:
            pass
        else:
            new_dna += dna[i * 14:(i + 1) * 14]
    w.dna = new_dna
    return w

def drop_mutator(w):
    dna = w.dna
    if len(dna) < 29:
        return flip_mutator(dupe_mutator(w))

    w.add_mut_mark("dr")
    inst = random.randint(0, (len(dna) / 14) - 1)
    new_dna = dna[:inst * 14]
    new_dna += dna[(inst + 1) * 14:]
    w.dna = new_dna
    return w

def dupe_mutator(w):
    dna = w.dna
    if not len(dna) < 1400:
        return flip_mutator(drop_mutator(w))
    w.add_mut_mark("du")
    inst = random.randint(0, (len(dna) / 14) - 1)
    new_dna = dna[:inst * 14]
    new_dna += dna[inst * 14:(inst + 1) * 14]
    new_dna += dna[inst * 14:]
    w.dna = new_dna
    return w

def segdupe_mutator(w):
    dna = w.dna
    w.add_mut_mark("sd")
    first_pos = random.randint(0, len(dna) / 14 - 1)
    sec_pos = random.randint(1, len(dna) / 14)
    if sec_pos > first_pos:
        tmp = first_pos
        first_pos = sec_pos
        sec_pos = tmp
    new_dna = dna[:sec_pos * 14]
    new_dna += dna[first_pos * 14:sec_pos * 14]
    new_dna += dna[sec_pos * 14:]
    w.dna = new_dna
    return w

def evolve(a, b, radiation = 0, gen = None, id = None):
    child_l, child_r = spawn(a, b, gen, id)
    while random.random() <= (MUTATION_CHANCE + (radiation  * MAX_RADIATION_MUTATION_PROB)):
        for i in range(random.randint(1, MAX_MUTATION_ROUNDS)):
            child_l = get_mutator()(child_l)
    while random.random() <= (MUTATION_CHANCE + (radiation  * MAX_RADIATION_MUTATION_PROB)):
        for i in range(random.randint(1, MAX_MUTATION_ROUNDS)):
            child_r = get_mutator()(child_r)
    return (child_l, child_r)

def report(scores):
    sum = reduce(lambda x, y: x + y, map(lambda x: x[1], scores))
    avg = sum / len(scores)
    print "\t----------"
    print "\tsum: %d" % sum
    print "\tavg: %d" % avg
    print

def score_pick(scores, exclude_ind = None, score_function=gen_score_function):
    avg = float(reduce(lambda x, y: x + y, map(score_function, scores))) / float(len(scores))
    std_dev = (float(reduce(lambda x, y: x + y, map(lambda x: (score_function(x) - avg) ** 2, scores))) / float(len(scores) - 1)) ** 0.5
    
    if std_dev != 0:
        rel_scores = map(lambda x: float(max(0.0, ((score_function(x) - avg) / std_dev) - MIN_REPRODUCTIVE_STDDEV) ** SCORING_EXP if exclude_ind == None or scores[exclude_ind] != x else 0.0), scores)

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

def gengen(lastgen, scores, score_function=gen_score_function):
    parents = []
    nextgen = str(lastgen + 1)
    os.mkdir(nextgen)

    avg = float(reduce(lambda x, y: x + y, map(score_function, scores))) / float(len(scores))
    std_dev = (float(reduce(lambda x, y: x + y, map(lambda x: (score_function(x) - avg) ** 2, scores))) / float(len(scores) - 1)) ** 0.5

    if std_dev != 0:
        win_loss_dev = float(score_function(scores[0]) - score_function(scores[-1])) / std_dev
    else:
        win_loss_dev = 0.0

    print "deviation spread is %2.04f" % win_loss_dev

    if win_loss_dev < RADIATION_THRESH:
        radiation = float((RADIATION_THRESH - win_loss_dev) / RADIATION_THRESH)
        print "radiation now at %f" % radiation
    else:
        radiation = 0

    newgen = []

    for i in range(0, CHILDREN_PER_GEN, 2):
        mother = score_pick(scores, None, score_function)
        father = score_pick(scores, mother, score_function)
        l, r = evolve(scores[mother], scores[father], radiation, gen = lastgen + 1, id = (i + 1))
        with open(nextgen + "/" + str(i + 1), "w") as f:
            f.write(l.code)
            newgen.append(l)
        with open(nextgen + "/" + str(i + 2), "w") as f:
            f.write(r.code)
            newgen.append(r)
    return (radiation, newgen)



def rungen(gen, warriors = None):
    global elites
    
    if None == warriors or len(warriors) == 0:
        warriors = [warrior_load(str(gen) + "/" + str(x + 1), gen=gen, id=(x + 1))
                for x in range(CHILDREN_PER_GEN)]

    if elites == None:
        elites = warriors
    else:
        for e in elites:
            e.lap()


    for i in range(CHILDREN_PER_GEN - 1):
        for j in range(CHILDREN_PER_GEN):
            run_games(warriors[j], elites[j])
            
        warriors.append(warriors.pop(0))

    pairings = range(1, CHILDREN_PER_GEN)
    for i in range((CHILDREN_PER_GEN - 1)):
            top = [0] + pairings[:(CHILDREN_PER_GEN / 2) - 1]
            bottom = pairings[len(top) - 1:][::-1]
            for j in range(CHILDREN_PER_GEN / 2):
                run_games(warriors[top[j]], warriors[bottom[j]])
                run_games(elites[top[j]], elites[bottom[j]])
            pairings.append(pairings.pop(0))

    elites.sort(key=gen_score_function, reverse=True)
    warriors.sort(key=gen_score_function, reverse=True)

    print "gen %d:" % gen
    print "\twarriors\t\telite"
    print "\t=======\t\t\t====="
    for (x, sw) in zip(warriors, elites):
        print "\t%s:\t%09.02f\t%s:\t%09.02f" % (x.name, gen_score_function(x), sw.name, gen_score_function(sw))
    print

    if int(gen) > 0:    
        elites = warriors + elites
    elites.sort(key=gen_score_function, reverse=True)
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
def run_games(l, r):
        l_results = [0, 0]
        r_results = [0, 0]
        for i in range(ROUNDS_PER_GAME):
            tmp = mars.run((l.player, r.player), rounds = 1, seed = int(ceil(((2 ** 31) - 101) * random.random() + 100)))
            if tmp[0][0] > 0:
                l.lap_scores.inc_wins()
                l.lap_scores.add_lines(tmp[2])
            if tmp[0][1] > 0:
                l.lap_scores.inc_losses()
            if tmp[0][2] > 0:
                l.lap_scores.inc_ties()
            if tmp[1][0] > 0:
                r.lap_scores.inc_wins()
                r.lap_scores.add_lines(tmp[2])
            if tmp[1][1] > 0:
                r.lap_scores.inc_losses()
            if tmp[1][2] > 0:
                r.lap_scores.inc_ties()

            tmp = mars.run((r.player, l.player), rounds = 1, seed = int(ceil(((2 ** 31) - 101) * random.random() + 100)))
            if tmp[1][0] > 0:
                l.lap_scores.inc_wins()
                l.lap_scores.add_lines(tmp[2])
            if tmp[1][1] > 0:
                l.lap_scores.inc_losses()
            if tmp[1][2] > 0:
                l.lap_scores.inc_ties()
            if tmp[0][0] > 0:
                r.lap_scores.inc_wins()
                r.lap_scores.add_lines(tmp[2])
            if tmp[0][1] > 0:
                r.lap_scores.inc_losses()
            if tmp[0][2] > 0:
                r.lap_scores.inc_ties()

def save_progenitors():
    global elites
    os.system("git pull --no-edit -X theirs")
    if PROGENITOR_DIR != None:
        for w in elites[:PROGENITORS_TO_SAVE]:
            sname = w.name
            tmp_dname = PROGENITOR_DIR + "/" + sname.replace("/","")
            dname = tmp_dname
            ext="a"
            while os.path.exists(dname):
                dname = tmp_dname + ext
                if ext[-1] == "z":
                    add_letters = 1
                    ext = ext[:-1]
                    while len(ext) > 0 and ext[-1] == "z":
                        add_letters = add_letters + 1
                        ext = ext[:-1]
                    if len(ext) == 0:
                        ext = "a"
                    else:
                        ext = ext[:-1] + str(chr(ord(ext[-1]) + 1))
                    ext = ext + ("a" * add_letters)
                else:
                    ext = ext[:-1] + str(chr(ord(ext[-1]) + 1))
            with open(sname, "r") as s:
                with open(dname, "w") as d:
                    d.write(s.read())

def initial_setup():
    try:
        os.mkdir("0")
    except:
        print "Initial setup already completed. Moving on..."
        return
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
        child_l, child_r = evolve(adam, eve, gen=0, id=(i + 1))
        with open(fname_l, "w") as f:
            f.write(child_l.code)
        with open(fname_r, "w") as f:
            f.write(child_r.code)

def era_comp(winners):
    print "beginning end-of-era selection...",

    pairings = range(1, len(elites))
    for i in range(len(elites) - 1):
        top = [0] + pairings[:(len(elites) / 2) - 1]
        bottom = pairings[len(top) - 1:][::-1]
        for j in range(len(elites) / 2):
            for _ in range(ERA_COMP_ROUNDS):
                run_games(elites[top[j]], elites[bottom[j]])
        pairings.append(pairings.pop(0))
    elites.sort(key=era_score_function, reverse=True)

def era_gen(g, prev_gen):
    global elites
    i = 0

    era_comp(prev_gen)
    radiation, newgen = gengen(g - 1, prev_gen + elites, era_score_function)

    print "======================="
    print "it's the end of an era!"
    print "======================="
    print
    print_elites()
    return newgen

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
    next_gen = []
    for e in range(eras):
        radioactive_rounds = 0
        if e > 0:
            next_gen = era_gen(e * generations_to_run, prev_gen_winners)
            prev_gen_winners = []
        for i in range(generations_to_run):
            if os.path.exists(str(generations_to_run * e + i + 1)):
                print "Future generation %d already exists. Moving on..." % (generations_to_run * e + i + 1)
                continue
            winners = rungen(generations_to_run * e + i, next_gen)
            prev_gen_winners = winners
            if (i + 1) != generations_to_run:
                cur_rad, next_gen = gengen(generations_to_run * e + i, winners)
                if cur_rad > EXTINCTION_LEVEL_RADIATION_THRESHOLD:
                    radioactive_rounds += 1
                elif radioactive_rounds > 0 and cur_rad < (EXTINCTION_LEVEL_RADIATION_THRESHOLD / 2.0):
                        radioactive_rounds -= 1
                if radioactive_rounds == EXTINCTION_LEVEL_RADIATION_ROUNDS:
                    print "Extinction level event! Begining next era!"
                    break

    elites.sort(key=era_score_function, reverse=True)
    save_progenitors()
    print_elites()
