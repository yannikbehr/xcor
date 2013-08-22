include makeauto.macro

BINDIR = ../bin

VPATH = modules

hfiles = \
	$(VPATH)/iniparser.h\
	$(VPATH)/sac_db.h

ofiles = \
	$(VPATH)/iniparser.o\
	$(VPATH)/mysac.o

options = -g -Wall -I/usr/local/include -L/usr/local/lib

%.o:%.c
	$(CC) $(CFLAGS) -g -c  $<  

all: initsacdb whiteout1cmp whiteout2cmp xcor mergesac filter extra 
#ftan  

initsacdb: module_obj initsac_db.c
	$(CC) $(CFLAGS) -g -I$(VPATH) initsac_db.c -o initsac_db $(ofiles)

xcor: 
	$(MAKE) -C xcorr

filter: filter4_driver.c module_obj
	$(CC) $(CFLAGS) $(options) filter4_driver.c -o filter4 -I $(VPATH) $(MODULES)/filter4.o $(MODULES)/mysac.o -lfftw3 -lgfortran 

whiteout1cmp: white_1cmp_driver.c module_obj
	$(CC) $(CFLAGS) $(options) white_1cmp_driver.c -o white_1cmp -I$(VPATH) $(LIBS) $(MODULES)/white_phamp_1cmp.o $(MODULES)/mysac.o -lfftw3 -lgfortran 

whiteout2cmp: white_2cmp_driver.c module_obj
	$(CC) $(CFLAGS) $(options) white_2cmp_driver.c -o white_2cmp -I$(VPATH) $(MODULES)/white_phamp_2cmp.o $(MODULES)/mysac.o -lfftw3 -lgfortran 

mergesac: merge_sac.c module_obj $(hfiles)
	$(CC) -Wall $(CFLAGS) -g -I $(VPATH) merge_sac.c -o merge_sac $(ofiles)

ftan:	ftan-module

ftan-module:
	$(MAKE) -C FTAN/pv
	$(MAKE) -C FTAN/gv

module_obj:
	$(MAKE) -C $(VPATH) objects

extra:
	$(MAKE) -C extratools

install:
	install initsac_db $(BINDIR);\
	install	./xcorr/justCOR $(BINDIR);\
	install	./xcorr/justCOR_EE_EN $(BINDIR);\
	install filter4 $(BINDIR);\
	install white_1cmp $(BINDIR);\
	install white_2cmp $(BINDIR);\
	install merge_sac $(BINDIR);\
	install ./xcorr/autoCOR $(BINDIR);\
	install ./extratools/read_sac_db $(BINDIR);

clean:
	rm initsac_db filter4 white_1cmp \
	white_2cmp merge_sac; \
	$(MAKE) -C $(VPATH) clean;\
	rm ../bin/*;\
	$(MAKE) -C FTAN/pv clean;\
	$(MAKE) -C FTAN/gv clean;\
	$(MAKE) -C extratools clean;

tilde: 
	-rm -f $(VPATH)/*~ 
	-rm -f *~
	-rm rdseed.err_log.*

tar: 
	tar -czvf ../noise_proc.tar.gz ../src
