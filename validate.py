import re

LEFT, RIGHT = 0,1
other = lambda h: 1-h

class ParseException(Exception): pass

class Hand:
    def __init__(self, throw):
        throwM = re.match(r'(\d+(?:\.\d*)?)(x?)(?:([rp])(\d)?)?(x?)(\*?)$', throw)
        self.neg1x = False
        if throwM:
            th, x1, passType, passTo, x2, hurry = throwM.groups()
            if passType == 'p' and passTo is None:
                passType, passTo = 'r', 1
            self.ss = float(th)
            self.passType = passType or ''
            self.passTo = int(passTo or 0)
            self.x = (x1+x2 == 'x')
            self.hurry = hurry == '*'
            self.throw = True
        else:
            self.throw = False

    def __str__(self):
        if not self.throw: return ''
        passMod = self.passType
        if passMod == 'r' and self.passTo == 1: #r1 is the same as p so simplify
            passMod = 'p'
        elif passMod:
            passMod += str(self.passTo or '')
        ss = ('%.3f'%self.ss).rstrip('0').rstrip('.')
        return ss + passMod + 'x'*self.x

    def __repr__(self):
        return 'Hand(%r)' % str(self)

    def has_decimal(self):
        return self.throw and not self.ss.is_integer()

class Beat:
    def __init__(self, left, right):
        self.hands = [Hand(left), Hand(right)]
        self.lands = [int(hand.throw) for hand in self.hands]

    def __repr__(self):
        return 'Beat(%r,%r)' % (str(self.hands[LEFT]), str(self.hands(RIGHT)))

    def __str__(self):
        return '(%s,%s)' % (self.hands[LEFT], self.hands[RIGHT])

    def has_decimal(self):
        return self.hands[LEFT].has_decimal() or self.hands[RIGHT].has_decimal()

class Juggler:
    def __init__(self, throws):
        self.throws = []
        hand = RIGHT
        for throw in throws:
            throwRE = '\d+(?:\.\d*)?x?(?:[rp]\d?)?x?\*?'
            sync = re.match(r'\((%s),(%s)\)!?$' % (throwRE,throwRE), throw)
            async = re.match(r'[LR]?%s$' % throwRE, throw)
            if sync:
                left, right = sync.groups()
                self.throws.append(Beat(left, right))
                if throw[-1] != '!':
                    self.throws.append(Beat('',''))
                    hand = other(hand)
            elif async:
                if throw[-1] == '*':
                    hand = other(hand)
                if throw[0] in 'RL':
                    hand = (throw[0] == 'R')
                throw = throw.lstrip('R').lstrip('L')
                if hand == LEFT:
                    self.throws.append(Beat(throw, ''))
                else:
                    self.throws.append(Beat('', throw))
            else:
                raise ParseException('Bad throw format')
            hand = other(hand)

    def __repr__(self):
        return 'Juggler(%r)' % str(self)

    def __str__(self):
        return ' '.join(str(th) for th in self.throws)

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

    def validate(self):
        self.valid = True
        #For hurries, add a -1x on the next beat (same hand)
        # - lands[i+1] += 1
        # - lands[i] -= 1
        for j,juggler in enumerate(self.jugglers):
            for i,throw in enumerate(juggler.throws):
                ni = (i + 1) % len(juggler.throws)
                for HAND in (LEFT, RIGHT):
                    if throw.hands[HAND].throw and throw.hands[HAND].hurry:
                        throw.lands[HAND] -= 1
                        juggler.throws[ni].lands[HAND] += 1
                        juggler.throws[ni].hands[HAND].neg1x = True
        #Check each throw has a landing spot
        for j,juggler in enumerate(self.jugglers):
            for i,throw in enumerate(juggler.throws):
                self.check_throw(throw.hands[LEFT], LEFT, j, i)
                self.check_throw(throw.hands[RIGHT], RIGHT, j, i)

    def check_throw(self, throw, side, juggler, beat):
        if not throw.throw: return
        if throw.passType == 'r':
            juggler_to = (juggler + throw.passTo) % self.num_jugs
        elif throw.passType == 'p':
            juggler_to = throw.passTo - 1 # convert absolute passes to 0-based index
        else:
            juggler_to = juggler
        new_ss = throw.ss + self.jugglers[juggler].delay - self.jugglers[juggler_to].delay
        if not new_ss.is_integer():
            self.error = 'Seems like a bad throw value of %f' % throw.ss
            self.valid = False
            return False
        new_ss = int(new_ss)
        beat_to = (beat + new_ss) % self.period
        #if the same hand is throwing with the other juggler it will be of type 1, otherwise of type 2
        #type 1: Both right hands throwing at same time, hence crossing as expected (3p goes from R-L)
        #type 2: Right hand throwing at same time as LH, hence crossing inverse to expected (3p goes from R-R)
        diff_hand = not self.jugglers[juggler_to].throws[beat].hands[side].throw

        #print('ss,new_ss,x,side,diff_hand:',throw.ss,new_ss,throw.x,side,diff_hand)
        side_to = diff_hand ^ side ^ throw.x ^ (new_ss % 2)
        #print('land (time,side,jug):', beat_to, side_to, juggler_to)
        #Hurry validation:
        # - add -1x on the beat after a hurry (above)
        # - if a ball is landing on a beat where the other hand is doing a hurry then skip to the next beat
        # - - unless this beat/hand also has a -1x on it
        # - not sure if this method is completely correct...
        check = lambda hands, sidet: hands[other(sidet)].throw and hands[other(sidet)].hurry and not hands[sidet].neg1x
        max_left = self.period
        throws = self.jugglers[juggler_to].throws
        while max_left and check(throws[beat_to].hands, side_to):
            beat_to = (beat_to + 1) % self.period
            max_left -= 1
        if not self.jugglers[juggler_to].throws[beat_to].lands[side_to]:
            #print('at juggler %d:'%juggler, self.jugglers[juggler], 'throw %d:'%beat, 'land (time,side,jug):', beat_to, side_to, juggler_to)
            self.valid = False
        else:
            self.jugglers[juggler_to].throws[beat_to].lands[side_to] -= 1

    def __repr__(self):
        return 'Prechac(%r)' % str(self)

    def __str__(self):
        return '<%s>' % ' | '.join(str(j) for j in self.jugglers)

def tests():
    #test basic pattern
    assert(Prechac('<3p 3 3|3p 3 3>').valid)
    #test brolly 552 from 1 count
    assert(Prechac('<3p 3p 3p 4p 4p 2 3p 3p|3p 3p 3p 3p 2 3p 3p 3p>').valid)
    #test sync
    assert(Prechac('<(4x,4xp)|(4x,4xp)>').valid)
    #test hand specifiers
    assert(Prechac('<4p 3|L3 4p>').valid)
    #test decimal
    assert(Prechac('<3.5p|3.5p>').valid)
    #test hurry
    assert(Prechac('<3x 3*>').valid)
    #test hurry in passing
    assert(Prechac('<3p 3* 3 3px 3 3|3px 3 3 3p 3* 3>').valid)
    #large sync test - martins 3 count in sync
    assert(Prechac('<(2,4xp) (4xp,2x) (4x,2) (2,4xp) (4xp,2) (2,4x) (4xp,2) (2x,4xp) (2,4x) (4xp,2) (2,4xp) (4x,2) | (2,4p) (4p,2) (2,4x) (4p,2) (2x,4p) (2,4x) (4p,2) (2,4p) (4x,2) (2,4p) (4p,2x) (4x,2) >').valid)
    #more complex hurry test
    assert(Prechac('<(3x*,3x*)! R3* (3x*,3x*)! L3*>').valid)
    #more complex hurry test, another way of writing it
    assert(Prechac('<(3x*,3x*)! (3*,0)! (3x*,3x*)! (0,3*)!>').valid)
    #edge case hurry pattern
    # <4x*> is invalid here because it assumes all throws would be from the same hand so it must be written:
    assert(Prechac('<R4x* L4x*>').valid)
    print('tests done')

tests()