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

VPATH = ../modules

fflags = -O2 -Wall -c -ffixed-line-length-none

cflags = -O2 -Wall -c -I $(VPATH)

DBG = -g

FFLAGS = $(DBG)  $(fflags)

CFLAGS = $(DBG) $(cflags)

LDLIBS = -lfftw3 -lgcc

FOBJS = dcommon.o dmultifft.o 

binofiles = justCOR.o\
	    justCOR_EE_EN.o

ofiles = $(VPATH)/iniparser.o\
	 $(VPATH)/mysac.o

%.o:%.c 
	$(CC) $(CFLAGS) $<

%.o:%.f 
	$(FC) $(FFLAGS) $<

all: $(BIN1) $(BIN2)

$(BIN1) : $(FOBJS) $(COBJS) $(binofiles) module_obj 
	$(CC) justCOR.o $(ofiles) $(FOBJS) -o $(BIN1) $(LDLIBS)

$(BIN2) : justCOR_EE_EN.c $(FOBJS) $(COBJS) $(binofiles) module_obj
	$(CC) justCOR_EE_EN.o $(ofiles) $(FOBJS) -o $(BIN2) $(LDLIBS)

module_obj:
	cd $(VPATH); make objects

clean ::
	rm -f $(BIN1) $(BIN2) core *.o

tilde :
	rm ./*~

