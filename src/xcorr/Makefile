BIN1  = justCOR
BIN2  = justCOR_EE_EN
BIN3 = autoCOR

LPATH = /usr/local/lib 

FOBJS = dcommon.o dmultifft.o 

binofiles = justCOR.o\
	    justCOR_EE_EN.o\
            autoCOR.o

ofiles = $(COMMONDIR)/iniparser.o\
	 $(COMMONDIR)/mysac.o

%.o:%.c 
	$(CC) $(CFLAGS) -c $<

%.o:%.f 
	$(FC) $(FFLAGS) -c $<

all: $(BIN1) $(BIN2) $(BIN3)

$(BIN1) : $(FOBJS) $(COBJS) $(binofiles)
	$(CC) $(CFLAGS) justCOR.o $(ofiles) $(FOBJS) -o $(BIN1) $(CLIBS) -L $(LPATH)

$(BIN2) : $(FOBJS) $(COBJS) $(binofiles)
	$(CC) justCOR_EE_EN.o $(CFLAGS) $(ofiles) $(FOBJS) -o $(BIN2) $(CLIBS) -L $(LPATH)

$(BIN3) : $(FOBJS) $(COBJS) $(binofiles)
	$(CC) autoCOR.o $(CFLAGS) $(ofiles) $(FOBJS) -o $(BIN3) $(CLIBS) -L $(LPATH)

clean:
	-rm $(BIN1) $(BIN2) $(BIN3) *.o *~

