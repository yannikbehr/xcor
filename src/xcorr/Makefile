# Makefile for justCOR subroutine
#$Log$
#Revision 1.4  2007/07/19 22:31:35  behrya
#sa_from_seed_holes_NZ.c
#
#Revision 1.3  2007-07-10 04:51:39  behrya
#*** empty log message ***
#

BIN  = justCOR

VPATH = ../modules

fflags = -c
#fflags = -fast -Mextend -Msave
#fflags =  -O -e

# if you don't use shared libraries comment the next line
#shlib = -R/opt/SUNWspro/lib

DBG = -g

FFLAGS = $(DBG)  $(fflags) $(shlib)

CFLAGS = $(DBG) -I $(VPATH)

LDLIBS = -L/usr/lib -L/usr/local/packages/fftw/lib -L/Volumes/Server\ HD/usr/lib/ -lfftw3 -lgcc

FC = g77

CC = gcc


FOBJS = dcommon.o dmultifft.o 

#COBJS = justCOR.o 

ofiles = $(VPATH)/iniparser.o

#%.o:%.c 
#	$(CC) $(CFLAGS) $<

%.o:%.f 
	$(FC) $(FFLAGS) $<

$(BIN) : $(FOBJS) $(COBJS) module_obj
	$(CC) justCOR.c $(ofiles) $(FOBJS) -o $(BIN) $(LDLIBS) $(CFLAGS)

module_obj:
	cd $(VPATH); make objects

clean ::
	rm -f $(BIN) core $(FOBJS) $(COBJS)

install:
	cp $(BIN) ../
tilde :
	rm ./*~

test: changesacdb.c
	gcc -g -o changesacdb changesacdb.c -I $(VPATH)

testtest:
	./changesacdb