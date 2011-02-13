#! /usr/bin/env mypthon

import os, os.path, sys
from obspy.core import *
import numpy as np


fin = sys.argv[1]
#fin = '/Users/home/carrizad/GRID/array/sac/2009/Dec/2009_12_1_0_0_0/S019.ELZ.SAC'
st = read(fin)

fft_test = np.fft.fft(st[0].data)

fft_test = np.abs(fft_test)

autocorr_fft = fft_test * fft_test

autocorr = np.fft.ifft(autocorr_fft)

st[0].data = autocorr

st.write('autocorr.SAC',format="SAC")



