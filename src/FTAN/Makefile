
include ../kaikouras.macro

fflags = -O2 -Wall -g -c -ffixed-line-length-none
cflags = -O2 -Wall -g -c -I ../modules


FFLAGS = $(DBG) $(fflags)

CFLAGS = $(DBG) $(cflags) 

DBG =

HFILES = aftan.h\
	 fftw3.h

FOBJS = ftandriver.o\
	swapn.o\
	aftan4.o\
	aftan4i.o\
	ftfilt.o\
	fmax.o\
	taper.o\
	trigger.o\
	lim.o\
	spline.o\
	tapers.o\
	tgauss.o\
	dspline.o\
	pred_cur.o\
	misc.o
%.o:%.c
	$(CC) $(CFLAGS) $<

%.o:%.f
	$(FC) $(FFLAGS) $<


objects: $(FOBJS) $(HFILES)

clean:
	rm -f $(FOBJS)
