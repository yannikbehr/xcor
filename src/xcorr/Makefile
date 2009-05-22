# Makefile for justCOR subroutine
#$Log$
#Revision 1.4  2007/07/19 22:31:35  behrya
#sa_from_seed_holes_NZ.c
#
#Revision 1.3  2007-07-10 04:51:39  behrya
#*** empty log message ***
#

############## COMPILER #########################
CC = gcc
CPP = g++
FC = g77

BIN1  = justCOR
BIN2  = justCOR_EE_EN
BIN3  = xcor_h

VPATH = ../modules

fflags = -O2 -Wall -c -ffixed-line-length-none

cflags = -O2 -Wall -c -I $(VPATH)

DBG = -g

FFLAGS = $(DBG)  $(fflags)

CFLAGS = $(DBG) $(cflags)

LDLIBS = -lfftw3 -lgcc -lm -lgsl -lgslcblas

FOBJS = dcommon.o dmultifft.o 

binofiles = justCOR.o\
	    justCOR_EE_EN.o\
	    xcor_h.o

ofiles = $(VPATH)/iniparser.o\
	 $(VPATH)/mysac.o

%.o:%.c 
	$(CC) $(CFLAGS) $<

%.o:%.f 
	$(FC) $(FFLAGS) $<

all: $(BIN1) $(BIN2) $(BIN3)

$(BIN1) : $(FOBJS) $(COBJS) $(binofiles) module_obj 
	$(CC) justCOR.o $(ofiles) $(FOBJS) -o $(BIN1) $(LDLIBS)

$(BIN2) : $(FOBJS) $(COBJS) $(binofiles) module_obj
	$(CC) justCOR_EE_EN.o $(ofiles) $(FOBJS) -o $(BIN2) $(LDLIBS)

$(BIN3) :   module_obj
	$(CC) -g -Wall -I $(VPATH) xcor_h.c $(ofiles) -o $(BIN3) $(LDLIBS)

test: test_xcor_h.c xcor_h.c
	$(CC) -D TEST -I $(VPATH) -g -c xcor_h.c;
	$(CC) -D TEST -I $(VPATH) -g test_xcor_h.c -o test xcor_h.o $(ofiles) -lm -lgsl -lgslcblas

module_obj:
	cd $(VPATH); make objects

clean ::
	rm -f $(BIN1) $(BIN2) core *.o

tilde :
	rm ./*~

