COMPL = gcc		

hfiles = \
	iniparser.h\
	strtok_alt.h\
	strtok_mod.h

ofiles = \
	iniparser.o\
	strtok_alt.o\
	strtok_mod.o

%.o:%.c 
	$(COMPL) -g -c  $<  

objects: $(ofiles) $(hfiles)

clean:
	rm *.o *.pyc
