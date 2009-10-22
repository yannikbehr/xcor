#!/usr/local/bin/python
"""
wrapper for fortran filter routine
"""

from ctypes import *
from pylab import *
import sys, os, os.path
from obspy.sac import ReadSac


def filter4(f1,f2,f3,f4,npow,dt,npts,trace):
    ft = cdll.LoadLibrary('./filter4.so')
    f1 = c_double(f1)
    f2 = c_double(f2)
    f3 = c_double(f3)
    f4 = c_double(f4)
    npow = c_int(npow)
    dt = c_double(dt)
    n = c_int(npts)
    tr = array(trace,dtype='<f4',order='F')
    seis_out = zeros((n.value),dtype='<f4',order='F')
    e = ft.filter4_(byref(f1),byref(f2),byref(f3),byref(f4),byref(npow),\
                    byref(dt),byref(n),tr.ctypes.data_as(POINTER(c_float)),seis_out.ctypes.data_as(POINTER(c_float)))
    return seis_out


if __name__ == '__main__':
    xtr = ReadSac('/data/sabine/yannik/Results/stack/horizontal/nord/COR_WCZ_TIKO.SAC_RR_s')
    xtr.GetHvalue('delta')
    xtr.GetHvalue('npts')
    t=arange(0,4.01,0.01)
    x=sin(2*pi*t*.5)
    xn=x + sin(2*pi*t*10)*.1
    xn=x+randn(len(t))*0.05
    n = len(xn)
    dt = 0.01
    f1 = 0.4
    f2 = 0.5
    f3 = 0.6
    f4 = 0.7
    npow = 1
    trout = filter4(f1,f2,f3,f4,npow,dt,n,xn)
    plot(t,trout)
    plot(t,xn)
    show()
