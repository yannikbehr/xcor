hfiles = $(COMMONDIR)/iniparser.h\
	$(COMMONDIR)/mysac.h


ofiles = $(COMMONDIR)/mysac.o\
	$(COMMONDIR)/iniparser.o\
	white_phamp_1cmp.o\
	white_phamp_2cmp.o\
	filter4.o\

sofiles = \
	fft_filter_c.so\
	#fft_filter.so\

%.o:%.c 
	$(CC) -g -c $(CFLAGS) $<  

%.o:%.f 
	$(FC) -g -c $(FFLAGS) $(INCLUDES)  $<  

%.so:%.f90
	$(FC) -g $(FFLAGS) $(CFLAGS) -shared $< -o $@ -lfftw3 -fPIC

%.so:%.c
	$(CC) -g $(INCLUDES) -shared $< -o $@ -lfftw3 -fPIC

all: objects filter whiteout1cmp whiteout2cmp

objects: $(ofiles) $(hfiles) $(sofiles)

filter: filter4_driver.c
	$(CC) $(CFLAGS) $(options) filter4_driver.c -o filter4 -I$(COMMONDIR) filter4.o $(COMMONDIR)/mysac.o -lfftw3 -lgfortran $(CLIBS)

whiteout1cmp: white_1cmp_driver.c
	$(CC) $(CFLAGS) $(options) white_1cmp_driver.c -o white_1cmp -I$(COMMONDIR) $(LIBS) white_phamp_1cmp.o $(COMMONDIR)/mysac.o -lfftw3 -lgfortran $(CLIBS)

whiteout2cmp: white_2cmp_driver.c
	$(CC) $(CFLAGS) $(options) white_2cmp_driver.c -o white_2cmp -I$(COMMONDIR) white_phamp_2cmp.o $(COMMONDIR)/mysac.o -lfftw3 -lgfortran $(CLIBS)

clean:
	-rm *.o *.pyc *.so *~ white_2cmp white_1cmp filter4 
