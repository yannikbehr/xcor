hfiles=$(COMMONDIR)/mysac.h\
       $(COMMONDIR)/sac_db.h

ofiles=$(COMMONDIR)/mysac.o


mergesac: merge_sac.c
	$(CC) $(CFLAGS) -I$(COMMONDIR) merge_sac.c -o merge_sac $(ofiles)

clean:
	-rm *.pyc *~ merge_sac

