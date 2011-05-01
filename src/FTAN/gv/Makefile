include ../../makeauto.macro

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
	gfortran -c -ffixed-line-length-none -fPIC $<


aftan4i: $(ofiles)
	$(F2PY) $(F2PYFLAGS)  -c ftan.pyf ftan.f $(ofiles) -lfftw3

clean:
	rm -f *.o *.so
