include ../makeauto.macro

BIN  = filter4
VPATH = ../modules

fflags_loc = 

cflags_loc = -I $(VPATH)

DBG = -g

LDLIBS = -L/usr/lib -L/usr/local/packages/fftw/lib -lgcc -lfftw3

FFLAGS_all = $(FFLAGS) $(fflags) $(DBG) 

CFLAGS_all = $(CFLAGS) $(cflags_loc) $(DBG) 


COBJS =	driver_c.o\
	swapn.o\
	$(VPATH)/iniparser.o

FOBJS = \
	filter4.o

%.o:%.f 
	$(FC) $(DBG) -c $<

%.o:%.c 
	$(CC) $(DBG) -c $<

$(BIN) : $(FOBJS) $(COBJS) module_obj
	$(FC) $(FFLAGS) $(CFLAGS_all) $(COBJS) $(FOBJS) -o $(BIN) $(LDLIBS) 

module_obj:
	cd $(VPATH); make objects

clean ::
	rm -f $(BIN) core $(COBJS) $(FOBJS) *~ iniparser.o
