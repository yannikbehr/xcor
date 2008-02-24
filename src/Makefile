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

############## COMPILER #########################
COMPL = gcc
CPPOMPL = g++
FC = g77

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
	$(VPATH)/sac_db.h\
	$(VPATH)/strtok_alt.h

ofiles = \
	$(VPATH)/iniparser.o\
	$(VPATH)/strtok_alt.o


options = -pg -D DEBUG

%.o:%.c
	$(COMPL) -g -c  $<  

all: cut justcor filter4 whiteout ftan stack lag initsacdb sacseed

sacseed: module_obj sa_from_seed_new.c $(hfiles)
	$(COMPL)  -g -I $(VPATH) sa_from_seed_new.c -o sa_from_seed_new $(ofiles)

cut: 	module_obj cut_trans_mod.c
	$(COMPL) -g -I modules cut_trans_mod.c -o cut_trans_mod $(ofiles)

initsacdb: initsac_db.c
	$(COMPL) -g  -I $(VPATH) initsac_db.c -o initsac_db $(ofiles)

justcor: ./xcorr/justCOR.c
	cd ./xcorr; make

filter4: ./filter4_f/driver_c.c
	cd filter4_f; make

whiteout: ./white_outphamp/driver_c.c
	cd ./white_outphamp; make

stack:  newstack.c module_obj $(hfiles)
	$(CPPOMPL) -g -D DEBUG -I modules newstack.c -o newstack $(ofiles)

lag:    new_ch_lag.c module_obj $(hfiles)
	$(COMPL) -g -D DEBUG -I $(VPATH) new_ch_lag.c -o new_ch_lag $(ofiles)

ftan:	ftan-module
	$(FC) -o ftandriver $(ofilesftan) $(FTANLIBS) $(ofiles)

ftan-module:
	cd $(FTANPATH); make objects

module_obj:
	cd $(VPATH); make objects

install:
	install sa_from_seed_new $(BINDIR);\
	install	cut_trans_mod $(BINDIR);\
	install initsac_db $(BINDIR);\
	install	./xcorr/justCOR $(BINDIR);\
	install	./filter4_f/filter4 $(BINDIR);\
	install	./white_outphamp/whiten_phamp $(BINDIR);\
	install	newstack $(BINDIR);\
	install	new_ch_lag $(BINDIR);\
	install	ftandriver $(BINDIR);

clean:
	rm sa_from_seed_mod read_sac_db initsac_db new_ch_lag newstack \
	ftandriver cut_trans_mod justCOR; cd ./white_outphamp; make clean; \
	cd ..; cd ./filter4_f; make clean; cd ..; cd ./xcorr; make clean; \
	cd ..; cd ./modules; make clean; cd ..; cd ./FTAN; make clean; cd ..

tilde: 
	rm -f $(VPATH)/*~ ; rm -f *~; rm rdseed.err_log.*
