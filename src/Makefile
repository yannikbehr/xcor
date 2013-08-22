include makeauto.macro
#include makeauto.macro_gns

all: core conv prep xcor extra 

core: 
	$(MAKE) -C common initsacdb

conv:
	$(MAKE) -C conversion

prep:
	$(MAKE) -C preproc

xcor: 
	$(MAKE) -C xcorr 

extra:
	$(MAKE) -C extratools

install:
	install ./common/initsac_db $(BINDIR);\
	install	./xcorr/justCOR $(BINDIR);\
	install	./xcorr/justCOR_EE_EN $(BINDIR);\
	install ./xcorr/autoCOR $(BINDIR);\
	install ./preproc/filter4 $(BINDIR);\
	install ./preproc/white_1cmp $(BINDIR);\
	install ./preproc/white_2cmp $(BINDIR);\
	install ./conversion/merge_sac $(BINDIR);\
	install ./extratools/read_sac_db $(BINDIR);

clean:
	-rm $(BINDIR)/*;\
	$(MAKE) -C common clean;\
	$(MAKE) -C conversion clean;\
	$(MAKE) -C preproc clean;\
	$(MAKE) -C xcorr clean;\
	$(MAKE) -C extratools clean;\

tilde: 
	-rm -f *~
	-rm rdseed.err_log.*

tar: 
	tar -czvf ../noise_proc.tar.gz ../src
