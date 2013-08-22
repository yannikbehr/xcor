#!/usr/bin/env mypython
"""
wrapper for fortran filter routine
"""

from ctypes import *
from pylab import *
import sys, os, os.path

def filter4_f(trace,f1,f2,f3,f4,dt,npow=1):
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


def filter4_c(trace,f1,f2,f3,f4,dt,npow=1):
    npts=len(trace)
    ft = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__),'fft_filter_c.so'))
    f1 = c_double(f1)
    f2 = c_double(f2)
    f3 = c_double(f3)
    f4 = c_double(f4)
    npow = c_int(npow)
    dt = c_double(dt)
    n = c_int(npts)
    tr = array(trace,dtype='<f8')
    seis_out = zeros((n.value),dtype='<f8')
    ft.fft_filt(f1,f2,f3,f4,npow,dt,n,tr.ctypes.data_as(POINTER(c_double)),seis_out.ctypes.data_as(POINTER(c_double)))
    return seis_out


def smooth_spec(trace,f1,f2,f3,f4,dt,npow=1,winlen=20):
    npts = len(trace)
    ssp  = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__),'fft_filter_c.so'))
    f1 = c_double(f1)
    f2 = c_double(f2)
    f3 = c_double(f3)
    f4 = c_double(f4)
    npow = c_int(npow)
    dt = c_double(dt)
    n = c_int(npts)
    tr = array(trace,dtype='<f8')
    seis_out = zeros((n.value),dtype='<f8')
    ns = 2**max(int(log(float(npts))/log(2.0))+1,13);
    nk = (ns/2)+1
    seis_outamp = zeros((nk),dtype='<f8')
    seis_outph  = zeros((nk),dtype='<f8')
    wl = c_int(winlen)
    ssp.whiten_1cmp(f1,f2,f3,f4,npow,dt,n,tr.ctypes.data_as(POINTER(c_double)),
                    seis_out.ctypes.data_as(POINTER(c_double)),
                    seis_outamp.ctypes.data_as(POINTER(c_double)),
                    seis_outph.ctypes.data_as(POINTER(c_double)),wl)
    return seis_out, seis_outamp, seis_outph
                    

                    
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
    trout3 = filter4_f(xn.copy(),f1,f2,f3,f4,dt)
    trout = filter4_c(xn.copy(),f1,f2,f3,f4,dt)
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
    #plot(t,trout2,'c')
    #plot(t,xtr2.seis,'k--')
    plot(t,trout,'g')
    plot(t,trout3,'k--')
    plot(t,xn,'r')
    #plot(t,x,'k--')
    os.remove('tmp.sac')
    os.remove('tmp.sac.filter')

    s, samp, sph = smooth_spec(xn.copy(),f1,f2,f3,f4,dt,npow=1,winlen=20)
    figure()
    plot(samp)
    figure()
    plot(t,s)
    show()
    
