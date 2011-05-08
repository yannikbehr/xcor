### overwrite standard CFLAGS as this can mess up the F2PY compiler
CFLAGS = 

ofiles = dspline.o\
	 fmax.o\
	 ftfilt.o\
	 spline.o\
	 taper.o\
	 tapers.o\
	 trigger.o\
	 tgauss.o\
	 lim.o

%.o:%.f
	$(FC) -c $(FFLAGS) $<


aftan4i: $(ofiles)
	$(F2PY) $(F2PYFLAGS)  -c ftan.pyf ftan.f $(ofiles) -lfftw3

clean:
	rm -f *.o *.so
