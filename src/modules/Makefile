include ../makeauto.macro

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
	$(CC) -g -c  $<  

%.o:%.f 
	$(FC) -g -c $(FFLAGS) $<  

objects: $(ofiles) $(hfiles) stack

stack: c_stack.c
	gcc -O3 -g -I $(PYTHON) -I $(NUMPY) -c c_stack.c;\
	gcc -shared -o c_stack.so c_stack.o	

clean:
	rm *.o *.pyc
