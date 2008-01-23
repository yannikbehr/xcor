COMPL = gcc		

hfiles = \
	iniparser.h\
	strtok_alt.h

ofiles = \
	iniparser.o\
	strtok_alt.o

%.o:%.c 
	$(COMPL) -g -c  $<  

objects: $(ofiles) $(hfiles)

clean:
	rm *.o *.pyc
