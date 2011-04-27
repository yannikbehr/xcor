############## INSTALLER ########################
BINDIR = ../../bin

############## COMPILER #########################
include ../makeauto.macro

VPATH = ../modules

readsacdb: read_sac_db.c
	$(CC) $(CFLAGS) -g  -I $(VPATH) read_sac_db.c -o read_sac_db

install:
	install read_sac_db $(BINDIR)

clean:
	rm read_sac_db
