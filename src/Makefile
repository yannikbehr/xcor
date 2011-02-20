# every .o file depends on the .cpp file with the same 
# filename; the following line says what to do with 
# the .cpp files; $< means the first dependency


#%.o:%.cpp
#	g++ -g -c $<
############## INSTALLER ########################
#BINDIR = /Users/home/carrizad/xcorr/bin

BINDIR = ../bin

include makeauto.macro
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

all: initsacdb whiteout1cmp whiteout2cmp xcor mergesac ftan filter

cut: 	module_obj cut_trans_mod.c
	$(CC) $(CFLAGS) -g -I modules cut_trans_mod.c -o cut_trans_mod $(ofiles) -lm -limf

initsacdb: module_obj initsac_db.c
	$(CC) $(CFLAGS) -g -I$(VPATH) initsac_db.c -o initsac_db $(ofiles)

xcor: 
	cd ./xcorr; make

filter: filter4_driver.c module_obj
	$(CC) $(CFLAGS) $(options) filter4_driver.c -o filter4 -I $(VPATH) $(MODULES)/filter4.o $(MODULES)/mysac.o -lfftw3 -lgfortran 

whiteout1cmp: white_1cmp_driver.c module_obj
	$(CC) $(CFLAGS) $(options) white_1cmp_driver.c -o white_1cmp -I $(VPATH) $(MODULES)/white_phamp_1cmp.o $(MODULES)/mysac.o -lfftw3 -lgfortran 

whiteout2cmp: white_2cmp_driver.c module_obj
	$(CC) $(CFLAGS) $(options) white_2cmp_driver.c -o white_2cmp -I $(VPATH) $(MODULES)/white_phamp_2cmp.o $(MODULES)/mysac.o -lfftw3 -lgfortran 

mergesac: merge_sac.c module_obj $(hfiles)
	$(CC) -Wall $(CFLAGS) -g -I $(VPATH) merge_sac.c -o merge_sac $(ofiles)

ftan:	ftan-module

ftan-module:
	cd ./FTAN/pv; make;
	cd ./FTAN/gv; make

module_obj:
	cd $(VPATH); make objects

install:
	install	cut_trans_mod $(BINDIR);\
	install initsac_db $(BINDIR);\
	install	./xcorr/justCOR $(BINDIR);\
	install	./xcorr/justCOR_EE_EN $(BINDIR);\
	install	./xcorr/xcor_h $(BINDIR);\
	install filter4 $(BINDIR);\
	install white_1cmp $(BINDIR);\
	install white_2cmp $(BINDIR);\
	install merge_sac $(BINDIR);\
	install ./xcorr/autoCOR $(BINDIR);
clean:
	rm initsac_db cut_trans_mod justCOR filter4 white_1cmp\
	white_2cmp merge_sac; \
	cd ./modules; make clean; cd ..;\
	rm ../bin/*;\
	cd ./FTAN/pv; make clean; cd -;\
	cd ./FTAN/gv; make clean;\


tilde: 
	-rm -f $(VPATH)/*~ 
	-rm -f *~
	-rm rdseed.err_log.*

tar: 
	tar -czvf ../noise_proc.tar.gz ../src
