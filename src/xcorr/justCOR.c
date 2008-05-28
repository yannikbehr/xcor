/*--------------------------------------------------------------------------
  program to correlate sac-files:
  -reads in sac_db.out file
  -correlation of .am and .ph files in frequ.-domain
  -stacking correlations for one month
  -reads variable 'sacdirroot' from config file

  written by Fan Chi ????
  $Rev$
  $Author$
  $LastChangedDate$
  --------------------------------------------------------------------------*/

#define MAIN

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <iniparser.h>
#include <mysac.h>
#include <sac_db.h>

/* os-dependent includes for dir-manipulation */
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#define MODUS ,0711)

/* Function prorotypes */
void dcommon_(int *len, float *amp,float *phase);
void dmultifft_(int *len,float *amp,float *phase, int *lag,float *seis_out, int *ns);
void swapn(unsigned char *b, int N, int n);
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax);
void write_sac (char *fname, float *sig, SAC_HD *SHD);
int check_info ( SAC_DB *sdb, int ne, int ns1, int ns2 );
int do_cor( SAC_DB *sdb, int lag);
void sac_db_chng ( SAC_DB *sdb, char *pbdir );
int walk_dir(char *dirname);
void get_args(int argc, char** argv, SAC_DB* sdb, char *pbdir, int *lag);


/*----------------------------------------------------------------------------
  reads sac-files fname with maximum length nmax into signal sig and \
  header SHD
  --------------------------------------------------------------------------*/
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax)
{
  FILE *fsac;
  if((fsac=fopen(fname, "rb")) == NULL) return NULL;

  if ( !SHD ) SHD = &SAC_HEADER;

  fread(SHD,sizeof(SAC_HD),1,fsac);

  if ( SHD->npts > nmax ) {
    fprintf(stderr,
	    "ATTENTION !!! in the file %s npts exceeds limit  %ld",fname,nmax);
    SHD->npts = nmax;
  }

  fread(sig,sizeof(float),(int)(SHD->npts),fsac);

  fclose (fsac);

  /*-------------  calculate from t0  ----------------*/
  {
    int eh, em ,i;
    float fes;
    char koo[9];

    for ( i = 0; i < 8; i++ ) koo[i] = SHD->ko[i];
    koo[8] = '\0';

    SHD->o = SHD->b + SHD->nzhour*3600. + SHD->nzmin*60 +
      SHD->nzsec + SHD->nzmsec*.001;

    sscanf(koo,"%d%*[^0123456789]%d%*[^.0123456789]%g",&eh,&em,&fes);

    SHD->o  -= (eh*3600. + em*60. + fes);
    /*-------------------------------------------*/}

  return SHD;
}




/*----------------------------------------------------------------------------
  writes sac file with name fname from signal sig with header SHD
  --------------------------------------------------------------------------*/
void write_sac (char *fname, float *sig, SAC_HD *SHD)
{
  FILE *fsac;
  int i;
  fsac = fopen(fname, "wb");

  if ( !SHD ) SHD = &SAC_HEADER;


  SHD->iftype = (long)ITIME;
  SHD->leven = (long)TRUE;

  SHD->lovrok = (long)TRUE;
  SHD->internal4 = 6L;



  /*+++++++++++++++++++++++++++++++++++++++++*/
  SHD->depmin = sig[0];
  SHD->depmax = sig[0];
 
  for ( i = 0; i < SHD->npts ; i++ ) {
    if ( SHD->depmin > sig[i] ) SHD->depmin = sig[i];
    if ( SHD->depmax < sig[i] ) SHD->depmax = sig[i];
  }

  fwrite(SHD,sizeof(SAC_HD),1,fsac);

  fwrite(sig,sizeof(float),(int)(SHD->npts),fsac);


  fclose (fsac);
}

/*----------------------------------------------------------------------------
  evaluate ne, ns1, ns2 against SAC_DB values
  ne  = number of event
  ns1 = number of first station
  ns2 = number of second station
----------------------------------------------------------------------------*/
int check_info ( SAC_DB *sdb, int ne, int ns1, int ns2 )
{
  if ( ne >= sdb->nev ) {
    fprintf(stderr,"cannot make correlation: too large event number\n");
    return 0;
  }
  if ( (ns1>=sdb->nst) ||(ns2>=sdb->nst)  ) {
    fprintf(stderr,"cannot make correlation: too large station number\n");
    return 0;
  }
  if ( sdb->rec[ne][ns1].n <= 0 ) {
    fprintf(stderr,"no data for station %s and event %s\n", sdb->st[ns1].name, sdb->ev[ne].name );
    return 0;
  }
  if ( sdb->rec[ne][ns2].n <= 0 ) {
    fprintf(stderr,"no data for station %s and event %s\n", sdb->st[ns2].name, sdb->ev[ne].name );
    return 0;
  }
  if ( fabs(sdb->rec[ne][ns1].dt-sdb->rec[ne][ns2].dt) > .0001 ) {
    fprintf(stderr,"incompatible DT\n");
    return 0;
  }
  return 1;
}


/*c/////////////////////////////////////////////////////////////////////////*/
float sig[1000000];
SAC_HD shdamp1, shdph1, shdamp2, shdph2, shd_cor;

/*----------------------------------------------------------------------------
  correlation in frequ.-domain
  lag    = half length of correlation window
  cordir = directory for correl. results
  sdb    = SAC_DB structure with trace information

  calls fortran subroutines:
  -dcommon
  -dmultifft
----------------------------------------------------------------------------*/
int do_cor( SAC_DB *sdb, int lag)
{
  int ine, jsta1, jsta2, k;

  int len,ns,i; 


  char filename[200], amp_sac[200], phase_sac[200], cordir[200];
  char *cutptr;
  float amp[400000], phase[400000], cor[400000];
  float seis_out[400000];

  // outermost loop over day number, then station number

  for( ine = 0; ine < sdb->nev; ine++ ) {
    fprintf(stderr,"sdb->nev %d\n",ine);

    // loop over "base" station number, this will be stored into common memory

    for( jsta1 = 0; jsta1 < sdb->nst; jsta1++ ) {  

      if(sdb->rec[ine][jsta1].n > 0){
        sprintf( amp_sac, "%s.am", sdb->rec[ine][jsta1].ft_fname );
        sprintf( phase_sac, "%s.ph", sdb->rec[ine][jsta1].ft_fname );

	// read amp and phase files and read into common memory
        if ( read_sac(amp_sac, amp, &shdamp1, 1000000 )==NULL ) {
  	  fprintf( stderr,"file %s not found\n", amp_sac );
   	  continue;
        }
        if ( read_sac(phase_sac, phase, &shdph1, 1000000)== NULL ) {
          fprintf( stderr,"file %s not found\n", phase_sac );
          continue;
        }

	len = shdamp1.npts;

        dcommon_( &len, amp, phase ); // reads amp and phase files into common memory

	for( jsta2 = (jsta1+1); jsta2 < sdb->nst; jsta2++ ) {

  	  if(sdb->rec[ine][jsta2].n > 0){

	    // compute correlation
	    sprintf(amp_sac, "%s.am", sdb->rec[ine][jsta2].ft_fname);
            sprintf(phase_sac, "%s.ph", sdb->rec[ine][jsta2].ft_fname);
	    fprintf(stderr,"file %s  %s\n", sdb->rec[ine][jsta1].ft_fname,sdb->rec[ine][jsta2].ft_fname );
            // get array of floats for amp and phase of first signal

            if ( read_sac(amp_sac, amp, &shdamp2, 100000) ==NULL ) {
              fprintf(stderr,"file %s not found\n", amp_sac );
              continue;
            }

            if ( read_sac(phase_sac, phase, &shdph2, 100000)==NULL ) {
              fprintf(stderr,"file %s not found\n", phase_sac );
              continue;
            }
     
	    len = shdamp2.npts;

            if(!check_info(sdb, ine, jsta1, jsta2 )) {
              fprintf(stderr,"files incompatible\n");
              return 0;
            }
            else
	      {
		dmultifft_(&len, amp, phase, &lag, seis_out,&ns);
		cor[lag] = seis_out[0];
		for( i = 1; i< (lag+1); i++)
		  { 
		    cor[lag-i] =  seis_out[i];
		    cor[lag+i] =  seis_out[ns-i];
		  }

		// move and rename cor file accordingly 
		/* extract location for correlations */
		/* and create COR-dir if necessary   */
		strncpy(filename,sdb->rec[ine][jsta1].ft_fname,199);
		cutptr=strrchr(filename,'/');
		if(cutptr != NULL){
		  *(cutptr) = '\0';
		  cutptr=strrchr(filename,'/');
		  if(cutptr != NULL){
		    *(cutptr+1) = '\0';
		    strncpy(cordir,filename,199);
		    strcat(cordir,"COR");
		    if(mkdir(cordir MODUS == -1){
		       printf("directory %s already exists \n", cordir); 
		    }
		  }
		}
		
		sprintf(filename, "%s/COR_%s_%s.SAC.prelim",
			cordir, sdb->st[jsta1].name, sdb->st[jsta2].name);

		if(access(filename, F_OK) == 0) { // if file already present, do this
		  if ( !read_sac (filename, sig, &shd_cor, 1000000 ) ) {
		    fprintf(stderr,"file %s not found\n", filename );
		    return 0;
		  }
		  // add new correlation to previous one
		  for(k = 0; k < (2*lag+1); k++) sig[k] += cor[k];
		  shd_cor.unused1 = shd_cor.unused1+1;
		  write_sac (filename, sig, &shd_cor );
		}
	 
		// if file doesn't already exist, use one of the current headers
		// and change a few values. more may need to be added
		else {
		  shdamp1.delta = sdb->rec[ine][jsta1].dt;
		  shdamp1.evla =  sdb->st[jsta1].lat;
		  shdamp1.evlo =  sdb->st[jsta1].lon;
		  shdamp1.stla =  sdb->st[jsta2].lat;
		  shdamp1.stlo =  sdb->st[jsta2].lon;
		  shdamp1.npts =  2*lag+1;
		  shdamp1.b    = -(lag)*shdamp1.delta;
		  shdamp1.unused1 = 0;
		  write_sac (filename, cor, &shdamp1);
		}
	      }   //loop over check

	  }    //loop over if jsta2
	}   //loop over jsta2
      }  //loop over if jsta1
    }  //loop over jsta1
  }  //loop over events
  return 0;
}


/*--------------------------------------------------------------------------
insert sub-dirname 'pbdir' into sac_db entry 'ft_fname';
previous changes in the overall program structure makes it necessary
--------------------------------------------------------------------------*/
void sac_db_chng ( SAC_DB *sdb, char *pbdir )

{
  int ie, is;
  char *result;
  char filename[20], daydir[20];

  for ( ie = 0; ie < sdb->nev; ie++ ) for ( is = 0; is < sdb->nst; is++ )
    {
      if(sdb->rec[ie][is].ft_fname == NULL){
	printf("ERROR: ft_fname not found\n");
      }else {
	result=strrchr(sdb->rec[ie][is].ft_fname,'/');
	if(result != NULL){
	  strcpy(filename,result);
	  *(result)='\0';
	  result=strrchr(sdb->rec[ie][is].ft_fname,'/');
	  strcpy(daydir,result);
	  *(result+1)='\0';
 	  strcat(sdb->rec[ie][is].ft_fname,pbdir);
 	  strcat(sdb->rec[ie][is].ft_fname,daydir);
	  strcat(sdb->rec[ie][is].ft_fname,filename);
	  printf("dir is: %s\n",sdb->rec[ie][is].ft_fname);
	}else {
	  continue;
	}
      }
    }
  return;
}

/*------------------------------------------------------------------------
function to find all 'COR'-directories and move preliminary correlations
to final correlations
needs following headers: sys/types.h, sys/stat.h, dirent.h, string.h, 
                         stdio.h, stdlib.h
------------------------------------------------------------------------*/
int walk_dir(char *dirname)
{
  DIR *dir, *dir2;
  struct dirent *dirpointer, *dirpointer2;
  struct stat attribut;
  char tmp[200],oldname[200],newname[200];
  char *cutptr;

  /* open directory */
  if((dir=opendir(dirname)) == NULL) {
    fprintf(stderr,"ERROR in opendir ...\n");
    return EXIT_FAILURE;
  }
  /* read directory and recursive call of this function to find 
     'COR'-dirs*/
  while((dirpointer=readdir(dir)) != NULL){
    strncpy(tmp,dirname,199);
    strcat(tmp,(*dirpointer).d_name);
    if(stat(tmp, &attribut) == -1){
      fprintf(stderr,"ERROR in stat ...\n");
      return EXIT_FAILURE;
    }

    /* if directory entry name is 'COR' and is a directory than move
       all preliminery correlations to final ones*/
    if(strcmp((*dirpointer).d_name,"COR")==0 && attribut.st_mode & S_IFDIR){
      printf("working on: %s\n",tmp);
      if((dir2=opendir(tmp)) == NULL) {
	fprintf(stderr,"ERROR in opendir ...\n");
	return EXIT_FAILURE;
      }
      while((dirpointer2=readdir(dir2)) != NULL){
	strncpy(oldname,tmp,199);
	strcat(oldname,"/");
	strcat(oldname,(*dirpointer2).d_name);
	if(stat(oldname, &attribut) == -1){
	  fprintf(stderr,"ERROR in stat ...\n");
	  return EXIT_FAILURE;
	}
	if(attribut.st_mode & S_IFREG && strstr((*dirpointer2).d_name,".prelim") != NULL){
	  strncpy(newname,oldname,199);
	  cutptr = strrchr(newname,'.');
	  *(cutptr) = '\0';
	  printf("--> rename %s to %s\n",oldname, newname);
	  if( (rename(oldname,newname)) < 0) {
	    fprintf(stderr, "---->ERROR while renaming");
	    return EXIT_FAILURE;
	  }
	}
      }
      if(closedir(dir2) == -1)
	printf("ERROR while closing\n");
	
      /* else if dir-entry is directory function calls itself again */
    }else if(attribut.st_mode & S_IFDIR && strcmp((*dirpointer).d_name,".") != 0 && strcmp((*dirpointer).d_name,"..") != 0){
      strcat(tmp,"/");
      walk_dir(tmp);
    }
  }
  /* close directory */
  if(closedir(dir) == -1)
    printf("ERROR while closing %s\n", dirname);
  return EXIT_SUCCESS;
}

/*--------------------------------------------------------------------------
reading and checking commandline arguments
--------------------------------------------------------------------------*/
void get_args(int argc, char** argv, SAC_DB* sdb, char *pbdir, int *lag)
{
  int i;

  if (argc>7){
    fprintf(stderr,"USAGE: %s [-l lag] [-c alt/config.file] [-p passbanddir]\n", argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'l':	*lag=atoi(argv[++i]);
	break;

      case 'c':	strcpy(sdb->conf,argv[++i]);
	break;

      case 'p':	strcpy(pbdir,argv[++i]);
	break;

      case 'h':	fprintf(stderr,"USAGE: %s [-l lag] [-c alt/config.file] [-p passbanddir]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
      }
    }
  }
}


SAC_DB sdb;

/*c/////////////////////////////////////////////////////////////////////////*/
int main (int na, char **arg)
{
  FILE *ff;
  int lag;
  char str[600];
  dictionary *dd;
  char *tmpdir;
  char *sacdirroot;
  char pbdir[20];
  strcpy(sdb.conf,"./config.txt");
  strcpy(pbdir,"5to100");
  lag=3000;

  get_args(na, arg, &sdb, pbdir,&lag);

  /* OPEN SAC DATABASE FILE AND READ IN TO MEMORY */
  dd = iniparser_new(sdb.conf);
  tmpdir = iniparser_getstr(dd, "database:tmpdir");
  sacdirroot = iniparser_getstr(dd, "database:sacdirroot");
  sprintf(str,"%ssac_db.out", tmpdir);

  ff = fopen(str,"rb");
  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  /* change ft_fname value in sdb-struct */
  sac_db_chng(&sdb,pbdir);

  /*do all the work of correlations here  */
  do_cor(&sdb,lag);  
  printf("correlations finished\n");

  /* move COR/COR_STA1_STA2.SAC.prelim to COR/COR_STA1_STA2.SAC */
  walk_dir(sacdirroot);

  iniparser_free(dd);
  return 0;
}
