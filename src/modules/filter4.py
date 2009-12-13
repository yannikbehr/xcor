#!/usr/local/bin/python
"""
wrapper for fortran filter routine
"""

from ctypes import *
from pylab import *
import sys, os, os.path

def filter4(trace,f1,f2,f3,f4,dt,npow=1):
    npts=len(trace)
    ft = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__),'fft_filter.so'))
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
    from subprocess import *
    import obspy.signal.filter
    from obspy.sac import ReadSac
    t=arange(0,4.01,0.01)
    x=sin(2*pi*t*.5)
    xtr = ReadSac()
    xn=x + sin(2*pi*t*10)*.1
    xn=x+randn(len(t))*0.05
    xtr.fromarray(xn,delta=0.01)
    xtr.WriteSacBinary('tmp.sac')
    n = len(xn)
    dt = 0.01
    f1 = 0.3
    f2 = 0.35
    f3 = 0.65
    f4 = 0.7
    npow = 1
    trout = filter4(xn.copy(),f1,f2,f3,f4,dt)
    #trout2 = filter4(f1,f2,f3,f4,npow,dt,n,-1.*trout[::-1].copy())
    trout2 = obspy.signal.filter.bandpassZPHSH(xn,f1,f4,df=1/0.01)
    p = Popen('sac',stdin=PIPE)
    f = p.stdin
    print >>f,'r tmp.sac'
    print >>f,'bandpass npoles 2 passes 2 corner %f %f'%(f1,f4)
    print >>f,'w tmp.sac.filter'
    print >>f,'quit'
    f.close()
    p.wait()
    xtr2 = ReadSac('tmp.sac.filter')
    plot(t,trout2,'c')
    plot(t,xtr2.seis,'k--')
    plot(t,trout,'g')
    plot(t,xn,'r')
    plot(t,x,'k--')
    os.remove('tmp.sac')
    os.remove('tmp.sac.filter')
    show()
    
