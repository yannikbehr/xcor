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
	g77 -c -ffixed-line-length-none $<


aftan4i: $(ofiles)
	/usr/bin/f2py -c ftan.pyf ftan.f $(ofiles) -lfftw3