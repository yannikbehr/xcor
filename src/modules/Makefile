hfiles = \
	iniparser.h\
	mysac.h


ofiles = \
	mysac.o\
	white_phamp_1cmp.o\
	white_phamp_2cmp.o\
	filter4.o\
	iniparser.o\



#sofiles = \
	fft_filter.so\
	fft_filter_c.so

%.o:%.c 
	$(CC) -g  -c $(CFLAGS) $<  

%.o:%.f 
	$(FC) -g -c $(INCLUDES)  $<  

#%.so:%.f90
#	$(FC) -g $(FFLAGS) $(CFLAGS) -shared $< -o $@ -lfftw3 -fPIC

%.so:%.c
	$(FC) -g $(INCLUDES) $(CFLAGS) -shared $< -o $@ -lfftw3 -fPIC

objects: $(ofiles) $(hfiles) $(sofiles)


clean:
	rm *.o *.pyc

