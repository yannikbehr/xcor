# every .o file depends on the .cpp file with the same 
# filename; the following line says what to do with 
# the .cpp files; $< means the first dependency


#%.o:%.cpp
#	g++ -g -c $<
############## INSTALLER ########################
BINDIR = ../bin

include makeauto.macro
VPATH = modules

hfiles = \
	$(VPATH)/iniparser.h\
	$(VPATH)/sac_db.h

ofiles = \
	$(VPATH)/iniparser.o\
	$(VPATH)/mysac.o

options = -g -Wall

%.o:%.c
	$(CC) -g -c  $<  

all: cut initsacdb whiteout1cmp whiteout2cmp justcor mergesac ftan 

cut: 	module_obj cut_trans_mod.c
	$(CC) -g -I modules cut_trans_mod.c -o cut_trans_mod $(ofiles) -lm

initsacdb: module_obj initsac_db.c
	$(CC) -g -I$(VPATH) initsac_db.c -o initsac_db $(ofiles)

justcor: 
	cd ./xcorr; make

filter: filter4_driver.c module_obj
	$(CC) -g filter4_driver.c -o filter4 -I $(VPATH) -lfftw3 -lgfortran ./modules/filter4.o ./modules/mysac.o

whiteout1cmp: white_1cmp_driver.c module_obj
	$(CC) -g white_1cmp_driver.c -o white_1cmp -I $(VPATH) -lfftw3 -lgfortran ./modules/white_phamp_1cmp.o ./modules/mysac.o

whiteout2cmp: white_2cmp_driver.c module_obj
	$(CC) -g white_2cmp_driver.c -o white_2cmp -I $(VPATH) -lfftw3 -lgfortran ./modules/white_phamp_2cmp.o ./modules/mysac.o

mergesac: merge_sac.c module_obj $(hfiles)
	$(CC) -Wall -g -I $(VPATH) merge_sac.c -o merge_sac $(ofiles)

ftan:	ftan-module

ftan-module:
	cd ./FTAN/pv; make -f pyMakefile;
	cd ./FTAN/gv; make -f pyMakefile

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
	install merge_sac $(BINDIR)

clean:
	rm initsac_db cut_trans_mod justCOR filter4 white_1cmp\
	white_2cmp merge_sac; \
	cd ./modules; make clean; cd ..; cd ./FTAN; make clean; cd ..

tilde: 
	rm -f $(VPATH)/*~ ; rm -f *~; rm rdseed.err_log.*


tar: 
	tar -czvf ../noise_proc.tar.gz ../src