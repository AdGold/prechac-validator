prechac-validator
=================

A simple Prechac passing pattern validator

Usage:
```python
p = Prechac('<3p 3 3 | 3p 3 3>')
print(p.valid)
#or
print(test('<3p 3 3 | 3p 3 3>'))
```
Limitations:
* No support for decimal passes
* No support for hurries
