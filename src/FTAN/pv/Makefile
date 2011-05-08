### overwrite standard CFLAGS as this can mess up the F2PY compiler
CFLAGS = 

ofiles = mspline.o\
	 fmax.o\
	 ftfilt.o\
	 phtovel.o\
	 predcur.o\
	 taper.o\
	 tapers.o\
	 trigger.o\
	 tgauss.o

%.o:%.f
	$(FC) -c $(FFLAGS) $<


aftan4i: $(ofiles)
	$(F2PY) $(F2PYFLAGS) -c ftanpv.pyf ftanpv.f $(ofiles) -lfftw3 


clean:
	rm -f *.o *.so


