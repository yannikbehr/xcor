include ../makeauto.macro

BIN  = filter4
VPATH = ../modules

fflags_loc = 

cflags_loc = -I $(VPATH)

DBG = -g

LDLIBS = -L/usr/lib -L/usr/local/packages/fftw/lib -lgcc -lfftw3

FFLAGS_all = $(FFLAGS) $(fflags) $(DBG) 

CFLAGS_all = $(CFLAGS) $(cflags) $(DBG) 


OBJS = 	driver_c.o\
	filter4.o\
	swapn.o\
	$(VPATH)/iniparser.o

%.o:%.f 
	$(FC) $(DBG) -c $<

%.o:%.c 
	$(CC) $(DBG) $(cflags) -c $<

$(BIN) : $(OBJS) module_obj
	$(FC) $(FFLAGS) $(CFLAGS) $(OBJS) -o $(BIN) $(LDLIBS) 

module_obj:
	cd $(VPATH); make objects

clean ::
	rm -f $(BIN) core $(OBJS) *~
