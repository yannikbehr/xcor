PRE-PROCESSING
=================================================================

The general concept is to bring the available raw-data in 
the following directory-structure:
The python-script 'seed_db.py' , called by the python-wrapper 
'proc-driver.py', stores the paths of seed files found in 
one directory plus some information from these seed files 
in a sqlite-database file. This database file is used by the 
C-program 'sa_from_seed_mod' to convert the seed files into 
SAC files and write them into the structure mentioned above. 

If the raw-data is distributed among different directories 
it might be necessary to repeat this step several times. 

The next step is to check if the response-files are correct 
i.e. if they exist and if they have the right date. If not, 
this has to be corrected manually. To check the response 
files the python-script 'check-resp.py' can be executed.

If the raw-data structure above is a patchwork from several 
different sources a new sac_db.out file has to be created. 
This file is crucial for the rest of the processing as it 
contains the paths of the SAC files and several other 
information on the data and the processing that is needed 
for subsequent steps. 

'sac_db.out' can be created by the C-program 'initsacdb'. It 
scans the directory-structure above for SAC-files and 
constructs the new 'sac_db.out' file from the information 
found. The resulting binary file can be written to stdout 
with the C-program 'read_sac_db'.  

These last two steps are not part of the proc-driver script 
yet. 



The C-program 'cut_trans_mod' removes the instrument-response 
and cuts the trace, at the moment, between -3000 and + 3000 
seconds.

The python-script 'do_whiten.py' calls the fortran-programs 
'filter4' and 'whiten_phamp' which apply a time-normalisation 
as well as a spectral whitening. 

