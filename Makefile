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
COMPL = gcc
VPATH = modules
hfiles = \
	$(VPATH)/iniparser.h\
	$(VPATH)/sac_db.h

ofiles = \
	$(VPATH)/iniparser.o

%.o:%.c
	$(COMPL) -g -c  $<  

all: sacseed cut justcor filter4 whiteout

sacseed: module_obj sa_from_seed_mod.c $(hfiles)
	$(COMPL)  -g -I modules  sa_from_seed_mod.c -o sa_from_seed_mod $(ofiles)  -lsqlite

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

sqlite: sqlite-test.c
	$(COMPL) -g sqlite-test.c -o sqlite-test -lsqlite


testini: testini.c
	$(COMPL) -g -I modules testini.c -o testini $(ofiles)
clean:
	rm -r ./sacroot/

run:
	./sa_from_seed_mod

runcut:
	./cut_trans_mod 1000 84000
tilde: 
	rm -f $(VPATH)/*~ ; rm -f *~; rm rdseed.err_log.*

ofiles: 
	rm -f $(VPATH)/*.o


