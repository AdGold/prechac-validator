import re

LEFT, RIGHT = 0,1
other = lambda h: 1-h
formatThrow = lambda th: '%.1f%s%s'%(th[0], 'p' if th[1]==1 else chr(ord('a')+th[1]-1) if th[1] else '', 'x'*th[2]) if th is not None else ''

class Beat:
    def __init__(self, left, right):
        self.left = self.get_throw(left)
        self.right = self.get_throw(right)
        self.lands = [1 if self.left else 0, 1 if self.right else 0]

    def get_throw(self, throw):
        throwM = re.match(r'(\d+(?:\.\d*)?)(x?)([a-p]?)(x?)$', throw)
        if throwM:
            th, x1, p, x2 = throwM.groups()
            p = 1 if p == 'p' else ord(p)-ord('a')+1 if p else 0
            return (float(th), p, (x1+x2 == 'x') )
        return None

    def __repr__(self):
        return 'Beat(%r,%r)' % (formatThrow(self.left), formatThrow(self.right))

    def __str__(self):
        left, right = formatThrow(self.left), formatThrow(self.right)
        return '(%s,%s)'%(left,right)

class Juggler:
    def __init__(self, throws):
        self.throws = []
        hand = RIGHT
        for throw in throws:
            throwRE = '\d+(?:\.\d*)?x?[a-p]?x?'
            match = re.match(r'\((%s),(%s)\)!?$'%(throwRE,throwRE), throw)
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
        self.validate()
        if not self.valid:
            0#raise ValueError('Prechac not valid')

    def validate(self):
        crossing = lambda ss, x: (int(ss) % 2) ^ x #TODO - this won't work for decimals :(
        self.valid = True
        nJugs = len(self.jugglers)
        period = len(self.jugglers[0].throws)
        for j,juggler in enumerate(self.jugglers):
            for i,throw in enumerate(juggler.throws):
                land = lambda side,th,p,x: (int((th+i)%period), side ^ crossing(th, x), (p+j)%nJugs)

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

    def __repr__(self):
        return 'Prechac(%r)' % str(self)

    def __str__(self):
        return '<%s>' % ' | '.join(str(j) for j in self.jugglers)

test = lambda s: Prechac(s).valid

#test hurries
#p = Prechac('<3p 3* 3 3p 3 3 | 3px 3 3 3px 3* 3>')

#test sync
assert(Prechac('<(4x,4xp)|(4x,4xp)>').valid)
#test hand specifiers
assert(Prechac('<4px 3|L3 4px>').valid)

#jims: <R3p R3 L3 R3p L3 R3 L3p L3 R3 L3p R3 L3 | R3px L3 R3 L3px L3 R3 L3px R3 L3 R3px R3 L3 >
#jims: <3p R3 3 3p 3 3 3p L3 3 3p 3 3 | 3px 3 3 3px L3 3 3px 3 3 3px R3 3 >
print(test('<3p R3 3 3p 3 3 3p L3 3 3p 3 3 | 3px 3 3 3px L3 3 3px 3 3 3px R3 3 >'))
