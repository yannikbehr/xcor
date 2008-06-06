COMPL = gcc		
FCOMPL = g77

FFLAGS = -I /usr/include

hfiles = \
	iniparser.h\
	strtok_alt.h\
	strtok_mod.h

ofiles = \
	iniparser.o\
	strtok_alt.o\
	strtok_mod.o\
	filter4.o\
	white_phamp_2cmp.o\
	white_phamp_1cmp.o\
	mysac.o



%.o:%.c 
	$(COMPL) -g -c  $<  

%.o:%.f 
	$(FCOMPL) -g -c $(FFLAGS) $<  

objects: $(ofiles) $(hfiles)

clean:
	rm *.o *.pyc
