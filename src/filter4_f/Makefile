include ../makeauto.macro

BIN  = filter4
VPATH = ../modules

fflags_loc = 

cflags_loc = -I $(VPATH)

DBG = -g

LDLIBS = -L/usr/lib -L/usr/local/packages/fftw/lib -lgcc -lfftw3

FFLAGS_all = $(FFLAGS) $(fflags) $(DBG) 

CFLAGS_all = $(CFLAGS) $(cflags) $(DBG) 


COBJS =	driver_c.o\
	swapn.o\
	$(VPATH)/iniparser.o

FOBJS = filter4.o

%.o:%.f 
	$(FC) $(DBG) -c $<

%.o:%.c 
	$(CC) $(DBG) $(cflags) -c $<

$(BIN) : $(COBJS) $(FOBJS) module_obj
	$(FC) $(FFLAGS) $(CFLAGS) $(COBJS) $(FOBJS) -o $(BIN) $(LDLIBS) 

module_obj:
	cd $(VPATH); make objects

clean ::
	rm -f $(BIN) core $(COBJS) $(FOBJS) *~ iniparser.o
