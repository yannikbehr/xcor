#
BIN  = whiten_phamp

VPATH = ../modules

fflags = -O2 -Wall -ffixed-line-length-none
cflags = -O2 -Wall -I $(VPATH)

LDLIBS =   -L/usr/local/packages/fftw/lib -L/usr/lib -lgcc -lfftw3

DBG = -g

FFLAGS = $(DBG) $(fflags)

CFLAGS = $(DBG) $(cflags)

FC = g77

CC = gcc

FOBJS = whiten_phamp.o

COBJS = driver_c.o swapn.o 


#%.o:%.c 
#	$(CC) $(CFLAGS) $<
#%.o:%.f 
#	$(FC) $(FFLAGS) $(LDLIBS) $<
# 

$(BIN) : $(FOBJS) $(COBJS)
	$(FC) $(FFLAGS) $(FOBJS) $(COBJS) $(ofiles) -o $(BIN) $(LDLIBS) 

clean ::
	rm -f $(BIN) core $(FOBJS) $(COBJS)
