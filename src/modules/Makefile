include ../makeauto.macro

FFLAGS = -I /usr/local/include -I /usr/include

hfiles = \
	iniparser.h

ofiles = \
	iniparser.o\
	filter4.o\
	white_phamp_2cmp.o\
	white_phamp_1cmp.o\
	mysac.o



%.o:%.c 
	$(CC) -g -c  $<  

%.o:%.f 
	$(FC) -g -c $(FFLAGS) $<  

objects: $(ofiles) $(hfiles)

clean:
	rm *.o *.pyc
