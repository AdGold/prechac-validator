Prechac Validator
=================

A simple Prechac passing pattern validator

Usage:
```python
p = Prechac('<3p 3 3 | 3p 3 3>')
print(p.valid)
```

Assumptions about Boyce notation:
* The crossingness of a pass is based purely on which hand should be throwing at the time it lands, and 'x' causes it to go to the other hand instead, so a 3.5p from one person will go straight and a 3.5 from the other person will be crossing (assuming a delay of .5 between the jugglers). Additionally, a 4p will go R-L if the one of the jugglers right hand is throwing at the same time as the others left hand, and crossing if both jugglker's right hands are throwing together.
* The delay of jugglers is implicit in patterns where there are decimal passes, so in < 3.5p | 3.5p >, juggler 2 has an implcitic delay of .5, or in general: the delays are < 0 | 1/n | 2/n | ... | (n-1)/n > if there are n jugglers and at least one decimal pass.
* Hurry notation is assumed as the following, a hurry (notated by a '\*' after the throw) will cause that throw to be thrown a beat early, skipping the dwell time, the '\*' is also a shorthand for 'throw with the same hand as the last beat'. So < 3x 3\* > is a RRLL pattern and a pattern such as < R4x\* L4x\* > cannot be written as < 4x\* >
