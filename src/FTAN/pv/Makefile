include ../../makeauto.macro

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
	gfortran -c -ffixed-line-length-none $<


aftan4i: $(ofiles)
	$(F2PY) -c ftanpv.pyf ftanpv.f $(ofiles) -lfftw3 


clean:
	rm -f *.o *.so


