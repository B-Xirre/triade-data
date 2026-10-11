"""Exact fixed-point implementation with a checked signed 128-bit intermediate."""
from fractions import Fraction
from decimal import Decimal, InvalidOperation
SCALE=12000
I64_MIN=-(1<<63);I64_MAX=(1<<63)-1
def checked(value,bits=64):
    if type(value) is not int or not -(1<<(bits-1))<=value<(1<<(bits-1)):raise ValueError('integer_overflow')
    return value
def round_ratio(n,d):
    if d<=0:raise ValueError('positive_denominator_required')
    sign=-1 if n<0 else 1;n=abs(n)
    return sign*((2*n+d)//(2*d))
def q(value):
    if isinstance(value,bool) or isinstance(value,float):raise ValueError('binary_float_forbidden')
    if isinstance(value,Fraction):fraction=value
    else:
        try:fraction=Fraction(str(value))
        except (ValueError,ZeroDivisionError):raise ValueError('invalid_decimal_or_fraction')
    return checked(round_ratio(checked(fraction.numerator*SCALE,128),fraction.denominator))
def mul(a,b):return checked(round_ratio(checked(checked(a)*checked(b),128),SCALE))
def div(a,b):return checked(round_ratio(checked(checked(a)*SCALE,128),checked(b)))
def allocate(total,weights):
    checked(total)
    if total<0 or not weights or any(w<0 for w in weights) or sum(weights)<=0:raise ValueError('invalid_allocation')
    den=sum(weights);values=[checked(total*w,128)//den for w in weights]
    order=sorted(range(len(weights)),key=lambda i:(-(total*weights[i]%den),i))
    for i in order[:total-sum(values)]:values[i]+=1
    return values
def wire(value):
    if type(value) is int:return str(value)
    if isinstance(value,list):return [wire(v) for v in value]
    if isinstance(value,dict):return {k:wire(v) for k,v in value.items()}
    return value
