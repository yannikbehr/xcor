# every .o file depends on the .cpp file with the same 
# filename; the following line says what to do with 
# the .cpp files; $< means the first dependency
#$Rev$
#$Author$
#$LastChangedDate$

#%.o:%.cpp
#	g++ -g -c $<
############## INSTALLER ########################
BINDIR = ../bin

include makeauto.macro
############## ftan options ######################
FTANPATH = FTAN

ofilesftan = $(FTANPATH)/ftandriver.o\
	     $(FTANPATH)/swapn.o\
	     $(FTANPATH)/aftan4.o\
	     $(FTANPATH)/aftan4i.o\
	     $(FTANPATH)/ftfilt.o\
	     $(FTANPATH)/fmax.o\
	     $(FTANPATH)/taper.o\
	     $(FTANPATH)/trigger.o\
	     $(FTANPATH)/lim.o\
	     $(FTANPATH)/spline.o\
	     $(FTANPATH)/tapers.o\
	     $(FTANPATH)/tgauss.o\
	     $(FTANPATH)/dspline.o\
	     $(FTANPATH)/pred_cur.o\
	     $(FTANPATH)/misc.o

FTANLIBS =   -L/usr/lib -L/usr/local/packages/fftw/lib -lgcc -lfftw3

##################################################

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

#all: cut justcor filter4 whiteout ftan stack lag initsacdb sacseed
all: cut filter4 whiteout stack lag initsacdb whiteout1cmp newfilter4 whiteout2cmp justcor mergesac ftan 

sacseed: module_obj sa_from_seed_new.c $(hfiles)
	$(CC)  -g -I $(VPATH) sa_from_seed_new.c -o sa_from_seed_new $(ofiles)

cut: 	module_obj cut_trans_mod.c
	$(CC) -g -I modules cut_trans_mod.c -o cut_trans_mod $(ofiles) -lm

initsacdb: module_obj initsac_db.c
	$(CC) -g -I$(VPATH) initsac_db.c -o initsac_db $(ofiles)

justcor: 
	cd ./xcorr; make

filter4: ./filter4_f/driver_c.c
	cd filter4_f; make

newfilter4: filter4_driver.c module_obj
	$(CC) -g filter4_driver.c -o filter4 -I $(VPATH) -lfftw3 ./modules/filter4.o ./modules/mysac.o

whiteout: ./white_outphamp/driver_c.c
	cd ./white_outphamp; make

whiteout1cmp: white_1cmp_driver.c module_obj
	$(CC) -g white_1cmp_driver.c -o white_1cmp -I $(VPATH) -lfftw3 ./modules/white_phamp_1cmp.o ./modules/mysac.o

whiteout2cmp: white_2cmp_driver.c module_obj
	$(CC) -g white_2cmp_driver.c -o white_2cmp -I $(VPATH) -lfftw3 ./modules/white_phamp_2cmp.o ./modules/mysac.o

stack:  newstack.c module_obj $(hfiles)
	$(CPP) -g -D DEBUG -I modules newstack.c -o newstack $(ofiles)

lag:    new_ch_lag.c module_obj $(hfiles)
	$(CC) -g -D DEBUG -I $(VPATH) new_ch_lag.c -o new_ch_lag $(ofiles)

mergesac: merge_sac.c module_obj $(hfiles)
	$(CC) -Wall -g -I $(VPATH) merge_sac.c -o merge_sac $(ofiles)

ftan:	ftan-module
	$(FC) -o ftandriver $(ofilesftan) $(FTANLIBS) $(ofiles)

testing: module_obj test_sa_from_seed.c test_cut_trans_mod.c $(hfiles)
	$(CC)  -g -I $(VPATH) test_sa_from_seed.c -o test_sa_from_seed $(ofiles);
	$(CC) -g -I modules test_cut_trans_mod.c -o test_cut_trans_mod $(ofiles)

ftan-module:
	cd $(FTANPATH); make objects

module_obj:
	cd $(VPATH); make objects

install:
	install	cut_trans_mod $(BINDIR);\
	install initsac_db $(BINDIR);\
	install	./xcorr/justCOR $(BINDIR);\
	install	./xcorr/justCOR_EE_EN $(BINDIR);\
	install	./filter4_f/filter4 $(BINDIR);\
	install	./white_outphamp/whiten_phamp $(BINDIR);\
	install	newstack $(BINDIR);\
	install	new_ch_lag $(BINDIR);\
	install	ftandriver $(BINDIR);\
	install filter4 $(BINDIR);\
	install white_1cmp $(BINDIR);\
	install white_2cmp $(BINDIR);\
	install merge_sac $(BINDIR)

clean:
	rm sa_from_seed_mod read_sac_db initsac_db new_ch_lag newstack \
	ftandriver cut_trans_mod justCOR filter4 white_1cmp white_2cmp; \
	cd ./white_outphamp; make clean; \
	cd ..; cd ./filter4_f; make clean; cd ..; cd ./xcorr; make clean; \
	cd ..; cd ./modules; make clean; cd ..; cd ./FTAN; make clean; cd ..

tilde: 
	rm -f $(VPATH)/*~ ; rm -f *~; rm rdseed.err_log.*
