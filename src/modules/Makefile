COMPL = gcc		

hfiles = \
	iniparser.h

ofiles = \
	iniparser.o

%.o:%.c 
	$(COMPL) -g -c  $<  

objects: $(ofiles) $(hfiles)

clean:
	rm *.o *.pyc
