#!/usr/local/bin/python

"""
use ctypes to read and write sac_db structure
"""

from ctypes import *
import numpy as np

NSTATION = 100
NEVENTS = 750
HLINE = 150
SLINE = 10

class Event(Structure):
    _fields_ = [
        ('lat', c_float),
        ('lon', c_float),
        ('yy', c_int),
        ('mm', c_int),
        ('dd', c_int),
        ('h', c_int),
        ('m', c_int),
        ('s', c_int),
        ('ms', c_int),
        ('jday', c_int),
        ('t0', c_double),
        ('name', c_char*HLINE)
        ]

class Station(Structure):
    _fields_ = [
        ('lat', c_float),
        ('lon', c_float),
        ('name', c_char*SLINE)
        ]
class Record(Structure):
    _fields_ = [
        ('fname',c_char*HLINE),
        ('ft_fname', c_char*HLINE),
        ('resp_fname', c_char*HLINE),
        ('pz_fname', c_char*HLINE),
        ('chan', c_char*7),
        ('t0', c_double),
        ('dt', c_float),
        ('n', c_long)
        ]

class SacDb(Structure):
    _fields_ = [
        ('ev', Event*NEVENTS),
        ('st', Station*NSTATION),
        ('rec', Record*NSTATION*NEVENTS),
        ('conf', c_char*HLINE),
        ('nev',c_int),
        ('nst',c_int),
        ('cntst',c_int),
        ('cntev',c_int)
        ]


def read_db(fname):
    f = open(fname,'rb')
    a = SacDb()
    f.readinto(a)
    f.close()
    return a

def write_db(sdb, fname):
    f = open(fname,'wb')
    f.write(sdb)
    f.close()
