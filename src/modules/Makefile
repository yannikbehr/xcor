include ../makeauto.macro

FFLAGS = -I /usr/local/include -I /usr/include

hfiles = \
	iniparser.h

ofiles = \
	iniparser.o\
	filter4.o\
	white_phamp_2cmp.o\
	white_phamp_1cmp.o\
	mysac.o

sofiles = \
	fft_filter.so\
	fft_filter_c.so

%.o:%.c 
	$(CC) -g -c  $<  

%.o:%.f 
	$(FC) -g -c $(FFLAGS) $<  

%.so:%.f90
	$(FC) -g $(FFLAGS) -shared $< -o $@ -lfftw3

%.so:%.c
	$(FC) -g $(FFLAGS) -shared $< -o $@ -lfftw3

objects: $(ofiles) $(hfiles) $(sofiles)


clean:
	rm *.o *.pyc
