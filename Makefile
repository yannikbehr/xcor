# every .o file depends on the .cpp file with the same 
# filename; the following line says what to do with 
# the .cpp files; $< means the first dependency
#$Log$
#Revision 1.4  2007/07/20 03:15:23  behrya
#added 'all' entry and some minor changes
#
#Revision 1.3  2007-07-05 06:54:24  behrya
#sac_db.h added to hfiles
#
#%.o:%.cpp
#	g++ -g -c $<

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
	$(VPATH)/sac_db.h

ofiles = \
	$(VPATH)/iniparser.o


options = -pg -D DEBUG

%.o:%.c
	$(COMPL) -g -c  $<  

all: sacseed cut justcor filter4 whiteout

sacseed: module_obj sa_from_seed_mod.c $(hfiles)
	$(COMPL)  -g -I $(VAPTH) sa_from_seed_mod.c -o sa_from_seed_mod $(ofiles)  -lsqlite

ftan:	ftan-module
	$(FC) -o ftandriver $(ofilesftan) $(FTANLIBS) $(ofiles)

ftan-module:
	cd $(FTANPATH); make objects

cut: 	module_obj cut_trans_mod.c
	$(COMPL) -g -I modules cut_trans_mod.c -o cut_trans_mod $(ofiles)

justcor: ./xcorr/justCOR.c
	cd ./xcorr; make; make install

module_obj:
	cd $(VPATH); make objects

filter4: ./filter4_f/driver_c.c
	cd filter4_f; make

whiteout: ./white_outphamp/driver_c.c
	cd ./white_outphamp; make

stack:  newstack.c module_obj $(hfiles)
	$(CPPOMPL) -g -D DEBUG -I modules newstack.c -o newstack $(ofiles)

lag:    new_ch_lag.c module_obj $(hfiles)
	$(COMPL) -g -D DEBUG -I $(VPATH) new_ch_lag.c -o new_ch_lag $(ofiles)

initsacdb: initsac_db.c
	$(COMPL) -g  -I $(VPATH) initsac_db.c -o initsac_db $(ofiles)

readsacdb: read_sac_db.c
	$(COMPL) -g -I $(VPATH) read_sac_db.c -o read_sac_db


sqlite: sqlite-test.c
	$(COMPL) -g sqlite-test.c -o sqlite-test -lsqlite

clean:
	rm -r ./sacroot/

run:
	./sa_from_seed_mod

tilde: 
	rm -f $(VPATH)/*~ ; rm -f *~; rm rdseed.err_log.*

ofiles: 
	rm -f $(VPATH)/*.o


cowsay:
	./cowsay-3.03/bin/bin/cowsay this is the modified version of Fan Chi\'s correlation software