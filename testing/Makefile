all: testsafromseed testcuttransmod testdowhiten

testsafromseed:
		python test_modules.py -c ./sa_from_seed_new_test.cfg

testcuttransmod:
		python test_modules.py -c ./cut_trans_mod_test.cfg	

testdowhiten:
		python test_modules.py -c ./do_whiten_test.cfg	

testdowhitenew:
		python test_modules.py -c ./do_whiten_new_test.cfg	


horizontal: safromseed 

safromseed: 
	python test_h_comp.py -c ./h-comp.cfg



clean:
	rm -r ./testdata/test_h ./testdata/test ./testdata/tmp/*