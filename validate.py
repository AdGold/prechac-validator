import re

LEFT, RIGHT = 0,1
other = lambda h: 1-h
formatSS = lambda ss: ('%.3f'%ss).rstrip('0').rstrip('.')
def formatThrow(throw):
    if throw is None: return ''
    passMod = throw[1]
    if passMod == 'r' and throw[2] == 1:
        passMod = 'p'
    elif passMod:
        passMod += str(throw[2] or '')
    return formatSS(throw[0]) + passMod + 'x'*throw[3]

class Beat:
    def __init__(self, left, right):
        self.left = self.get_throw(left)
        self.right = self.get_throw(right)
        self.lands = [1 if self.left else 0, 1 if self.right else 0]

    def get_throw(self, throw):
        throwM = re.match(r'(\d+(?:\.\d*)?)(x?)(?:([rp])(\d)?)?(x?)$', throw)
        if throwM:
            th, x1, passType, passTo, x2 = throwM.groups()
            if passType == 'p' and passTo is None:
                passType, passTo = 'r', 1
            return (float(th), passType or '', int(passTo or 0), (x1+x2 == 'x') )
        return None

    def __repr__(self):
        return 'Beat(%r,%r)' % (formatThrow(self.left), formatThrow(self.right))

    def __str__(self):
        left, right = formatThrow(self.left), formatThrow(self.right)
        return '(%s,%s)'%(left,right)

    def has_decimal(self):
        left = self.left or (0.,)
        right = self.right or (0.,)
        return not (left[0].is_integer() and right[0].is_integer())

class Juggler:
    def __init__(self, throws):
        self.throws = []
        hand = RIGHT
        for throw in throws:
            throwRE = '\d+(?:\.\d*)?x?(?:[rp]\d?)?x?'
            match = re.match(r'\((%s),(%s)\)!?$'%(throwRE,throwRE), throw)
            #TODO fix handling of hurries here
            if match:
                left, right = match.groups()
                self.throws.append(Beat(left, right))
                if throw[-1] != '!':
                    self.throws.append(Beat('',''))
                    hand = other(hand)
            else:
                if throw[0] in 'RL':
                    hand = (throw[0] == 'R')
                if throw[-1] == '*':
                    hand = other(hand)
                throw = throw.strip('*').strip('R').strip('L')
                if hand == LEFT:
                    self.throws.append(Beat(throw, ''))
                else:
                    self.throws.append(Beat('', throw))
            hand = other(hand)

    def __repr__(self):
        return 'Juggler(%r)' % str(self)

    def __str__(self):
        return ' '.join(str(th) for th in self.throws);

    def has_decimal(self):
        return any(th.has_decimal() for th in self.throws)

class Prechac:
    def __init__(self, pattern):
        if pattern[0] != '<' or pattern[-1] != '>':
            raise ValueError('Invalid prechac format')
        pattern = pattern[1:-1]
        jugglers = pattern.split('|')
        try:
            self.jugglers = [Juggler(j.split() * 2) for j in jugglers]
        except:
            raise ValueError('Invalid prechac format')
        self.num_jugs = len(self.jugglers)
        self.period = len(self.jugglers[0].throws)
        if any(juggler.has_decimal() for juggler in self.jugglers): #check for auto shifting
            self.decimals = True
            for j,juggler in enumerate(self.jugglers):
                juggler.delay = j/self.num_jugs
        else:
            self.decimals = False
            for juggler in self.jugglers:
                juggler.delay = 0

        self.validate()
        if not self.valid:
            0#raise ValueError('Prechac not valid')

    def validate(self):
        crossing = lambda ss, x: (int(ss) % 2) ^ x #TODO - this won't work for decimals :(
        self.valid = True
        for j,juggler in enumerate(self.jugglers):
            for i,throw in enumerate(juggler.throws):
                self.check_throw(throw.left, LEFT, j, i)
                self.check_throw(throw.right, RIGHT, j, i)
                continue
                land = lambda side,th,pt,pto,x: (int((th+i)%period), side ^ crossing(th, x), (pto+j)%nJugs)

                if throw.left:
                    time, side, jug = land(LEFT, *throw.left)
                    if not self.jugglers[jug].throws[time].lands[side]:
                        self.valid = False
                        print('at juggler %d:'%j, juggler, 'throw %d:'%i, throw, 'land (time,side,jug):', time, side, jug)
                        #return
                    else:
                        self.jugglers[jug].throws[time].lands[side] -= 1

                if throw.right:
                    time, side, jug = land(RIGHT, *throw.right)
                    if not self.jugglers[jug].throws[time].lands[side]:
                        self.valid = False
                        print('at juggler %d:'%j, juggler, 'throw %d:'%i, throw, 'land (time,side,jug):', time, side, jug)
                        #return
                    else:
                        self.jugglers[jug].throws[time].lands[side] -= 1

    def check_throw(self, throw, side, juggler, beat):
        if throw is None: return
        ss, ptype, pto, x = throw
        if ptype == 'r':
            juggler_to = (juggler + pto) % self.num_jugs
        elif ptype == 'p':
            juggler_to = pto - 1 # convert absolute passes to 0-based index
        else:
            juggler_to = juggler
        new_ss = ss + self.jugglers[juggler].delay - self.jugglers[juggler_to].delay
        if not new_ss.is_integer():
            self.error = 'seems like a bad throw value in %f' % ss
            return False
        new_ss = int(new_ss)
        beat_to = (beat + new_ss) % self.period
        #if the same hand is throwing with the other juggler it will be of type 1, otherwise of type 2
        #type 1: Both right hands throwing at same time, hence crossing as expected (3p goes from R-L)
        #type 2: Right hand throwing at same time as LH, hence crossing inverse to expected (3p goes from R-R)
        if side == LEFT:
            diff_hand = self.jugglers[juggler_to].throws[beat].left is None
        if side == RIGHT:
            diff_hand = self.jugglers[juggler_to].throws[beat].right is None
        #print('ss,new_ss,x,side,diff_hand:',ss,new_ss,x,side,diff_hand)
        side_to = diff_hand ^ side ^ x ^ (new_ss % 2)
        #print('land (time,side,jug):', beat_to, side_to, juggler_to)
        #TODO add hurry stuff
        if not self.jugglers[juggler_to].throws[beat_to].lands[side_to]:
            #print('at juggler %d:'%juggler, self.jugglers[juggler], 'throw %d:'%beat, 'land (time,side,jug):', beat_to, side_to, juggler_to)
            self.valid = False
        else:
            self.jugglers[juggler_to].throws[beat_to].lands[side_to] -= 1

    def __repr__(self):
        return 'Prechac(%r)' % str(self)

    def __str__(self):
        return '<%s>' % ' | '.join(str(j) for j in self.jugglers)

test = lambda s: Prechac(s).valid

#test hurries
#p = Prechac('<3p 3* 3 3p 3 3 | 3px 3 3 3px 3* 3>')


#print('test sync')
assert(Prechac('<(4x,4xp)|(4x,4xp)>').valid)
#print('test hand specifiers')
assert(Prechac('<4p 3|L3 4p>').valid)
#print('test decimal')
assert(Prechac('<3.5p|3.5p>').valid)

#jims: <R3p R3 L3 R3p L3 R3 L3p L3 R3 L3p R3 L3 | R3px L3 R3 L3px L3 R3 L3px R3 L3 R3px R3 L3 >
#jims: <3p R3 3 3p 3 3 3p L3 3 3p 3 3 | 3px 3 3 3px L3 3 3px 3 3 3px R3 3 >
#print(test('<3p R3 3 3p 3 3 3p L3 3 3p 3 3 | 3px 3 3 3px L3 3 3px 3 3 3px R3 3 >'))
#print(test('<3p 3* 3 3px 3 3|3px 3 3 3p 3* 3>'))

#martin's 3: <(2 , 4xp) (4xp , 2x) (4x , 2) (2 , 4xp) (4xp , 2) (2 , 4x) * (4xp , 2) (2x , 4xp) (2 , 4x) (4xp , 2) (2 , 4xp) (4x , 2) | (2 , 4p) (4p , 2) (2 , 4x) (4p , 2) (2x , 4p) (2 , 4x) * (4p , 2) (2 , 4p) (4x , 2) (2 , 4p) (4p , 2x) (4x , 2) >
