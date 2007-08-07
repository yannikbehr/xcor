#
INST_DIR = $(HOME)/bin
BIN  = filter4
VPATH = ../modules

fflags = -O2 -Wall -ffixed-line-length-none
cflags = -O2 -Wall -I $(VPATH)

LDLIBS = -L/usr/lib -L/usr/local/packages/fftw/lib -lgcc -lfftw3

FFLAGS = $(DBG) $(fflags)

CFLAGS = $(DBG) $(cflags)

FC = g77

CC = gcc

DBG = -g

FOBJS = \
	driver_c.o \
	filter4.o \
	swapn.o \
	$(VPATH)/iniparser.o

%.o:%.f 
	$(FC) $(DBG) -c $<

%.o:%.c 
	$(CC) $(DBG) $(cflags) -c $<

$(BIN) : $(FOBJS) module_obj
	$(FC) $(FFLAGS) $(CFLAGS) $(FOBJS) -o $(BIN) $(LDLIBS) 

module_obj:
	cd $(VPATH); make objects

install :: $(BIN)
	install -s $(BIN) $(INST_DIR)

clean ::
	rm -f $(BIN) core $(FOBJS)
