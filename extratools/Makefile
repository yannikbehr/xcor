############## INSTALLER ########################
BINDIR = ../bin

############## COMPILER #########################
COMPL = gcc
CPPOMPL = g++
FC = g77
CFLAGS = -m32

VPATH = ../src/modules

readsacdb: read_sac_db.c
	$(COMPL) $(CFLAGS) -g  -I $(VPATH) read_sac_db.c -o read_sac_db

sqlite: sqlite-test.c
	$(COMPL) $(CFLAGS) -g sqlite-test.c -o sqlite-test -lsqlite

install:
	install read_sac_db $(BINDIR)
