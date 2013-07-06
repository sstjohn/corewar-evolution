import Corewar

UNARY_OPS = ["DAT","JMP","SPL"]
INSTRUCTIONS =           {"DAT": [["#", "<"], ["#", "<"]],
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


parser = Corewar.Parser(coresize=8000,
                        maxprocesses=8000,
                        maxcycles=80000,
                        maxlength=100,
                        mindistance=100,
                        standard=Corewar.STANDARD_88)
def dna_decompile(dna):
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

def dna_compile(code):
	dna = ''
	ln_cnt = 0
	for i in code.split("\n"):
		parts = i.replace(",", " ").split()
		if len(parts) == 0:
			continue
		if parts[0][0] == ';':
			continue
		instruction = -1
		try:
			instruction = INSTRUCTIONS.keys().index(parts[0])
			a_modes, b_modes = INSTRUCTIONS[parts[0]]
		except:
			print "Unknown instruction: %s" % parts[0]
			continue
		ln_cnt += 1
		if ln_cnt > 100:
			continue
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

		dna += ("%.2d%.1d%.1d%.4d%.1d%.1d%.4d" % (instruction, a_mode, a_neg, a_val, b_mode, b_neg, b_val))
	return dna

class CascadingScore:
	def add_lines(self, val):
		self.lines += val
		if self._parent != None:	
			self._parent.add_lines(val)
	def inc_wins(self):
		self.wins += 1
		if self._parent != None:	
			self._parent.inc_wins()
	def inc_losses(self):
		self.losses += 1
		if self._parent != None:
			self._parent.inc_losses()

	def inc_ties(self):
		self.ties += 1
		if self._parent != None:	
			self._parent.inc_ties()

	def __init__(self, parent = None):
		self._parent = parent
		self.lines = 0
		self.wins = 0
		self.losses = 0
		self.ties = 0
		
class Warrior:
	def _get_code(self):
		return self._code

	def _set_code(self, code):
		code_lines = code.split("\n")

		ln_cnt = 0
		i = -1
		while i < len(code_lines) - 1:
			i += 1
			if code_lines[i].strip() == "":
				continue
			if code_lines[i].strip()[0] == ';':
				continue
			ln_cnt += 1
			if ln_cnt == 100:
				break

		self._code = "\n".join(code_lines[:(i + 1)])
		if not self._dna_code_mutex:
			self._dna_code_mutex = True
			self.dna = dna_compile(self._code)
			self.player = parser.parse(self._code)
			self._dna_code_mutex = False

	code = property(_get_code, _set_code)

	def _get_dna(self):
		return self._dna

	def _set_dna(self, dna):
		self._dna = dna
		if not self._dna_code_mutex:
			self._dna_code_mutex = True
			self._set_code(dna_decompile(dna))
			self.player = parser.parse(self.code)
			self._dna_code_mutex = False

	dna = property(_get_dna, _set_dna)

	def _get_name(self):
		return "%s/%s" % (str(self.generation), str(self.id))

	name = property(_get_name, None)

	def lap(self):
		self.lap_scores = CascadingScore(self.all_scores)

	def __init__(self, code = None, dna = None, generation = None, id = None):
		self._code = None
		self._dna = None
		self._dna_code_mutex = False
		self.generation = generation
		self.id = id
		self.all_scores = CascadingScore()
		self.lap_scores = CascadingScore(self.all_scores)

		if code != None:
			self._set_code(code)
		elif dna != None:
			self._set_dna(dna)
