hfiles = iniparser.h\
	 sac_db.h

ofiles = iniparser.o\
	 mysac.o

%.o:%.c
	$(CC) $(CFLAGS) -g -c  $<  

initsacdb: $(ofiles)
	$(CC) $(CFLAGS) -g -I./ initsac_db.c -o initsac_db $(ofiles)

clean:
	-rm *.o *~ initsac_db