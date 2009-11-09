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
#define _XOPEN_SOURCE 500
#include <ftw.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <glob.h>
#include <iniparser.h>
#include <mysac.h>
#include <sac_db.h>

/* os-dependent includes for dir-manipulation */
#include <libgen.h>
#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <errno.h>
#define MODUS 0711
#define STRING 300
#define SSTRING 150

/* Function prorotypes */
void dcommon_(int *len, float *amp,float *phase);
void dmultifft_(int *len,float *amp,float *phase, int *lag,float *seis_out, int *ns);
int check_info (int ne, int ns1, int ns2 );
int do_cor(int lag, char *cordir,char *pbdir);
void sac_db_chng (char *pbdir);
void get_args(int argc, char** argv,char *fconf);
void make_dir(int ie, char *cordir, char *pbdir, char *daydir);


SAC_DB sdb;
SAC_HD shdamp1, shdph1, shdamp2, shdph2, shd_cor;

/* as there are sometimes problems with very large arrays that are defined 
within functions, we define them here*/
float amp[900000], phase[900000], cor[900000];
float seis_out[2000000];

/*c/////////////////////////////////////////////////////////////////////////*/
int main (int na, char **arg)
{
  FILE *ff;
  int lag;
  int flags = 1;
  char str[600],fconf[STRING];
  dictionary *dd;
  char *tmpdir, *cordir, *pbdir, *sacdbname, *prefix;
  strncpy(fconf,"./config.txt",STRING-1);
  get_args(na, arg,fconf);

  /* read in parameters from config file*/
  dd         = iniparser_new(fconf);
  tmpdir     = iniparser_getstr(dd, "xcor:tmpdir");
  cordir     = iniparser_getstr(dd, "xcor:cordir");
  lag        = iniparser_getint(dd, "xcor:lag", 3000);
  pbdir      = iniparser_getstr(dd, "xcor:pbdir");
  sacdbname  = iniparser_getstr(dd, "xcor:dbname");
  prefix     = iniparser_getstr(dd, "xcor:prefix");

  /* open sac-database file and read into memory*/
  assert((strlen(tmpdir)+strlen(sacdbname)+1) < STRING);
  sprintf(str,"%s/%s", tmpdir,sacdbname);
  ff = fopen(str,"rb");
  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);
  /* change ft_fname value in sdb-struct */
  sac_db_chng(pbdir);

  /*do all the work of correlations here  */
  do_cor(lag,cordir,pbdir);  
  printf("correlations finished\n");
  iniparser_free(dd);
  return 0;
}


/*----------------------------------------------------------------------------
  evaluate ne, ns1, ns2 against SAC_DB values
  ne  = number of event
  ns1 = number of first station
  ns2 = number of second station
----------------------------------------------------------------------------*/
int check_info (int ne, int ns1, int ns2 )
{
  if ( ne >= sdb.nev ) {
    fprintf(stderr,"cannot make correlation: too large event number\n");
    return 0;
  }
  if ( (ns1>=sdb.nst) ||(ns2>=sdb.nst)  ) {
    fprintf(stderr,"cannot make correlation: too large station number\n");
    return 0;
  }
  if ( sdb.rec[ne][ns1].n <= 0 ) {
    fprintf(stderr,"no data for station %s and event %s\n", sdb.st[ns1].name, sdb.ev[ne].name );
    return 0;
  }
  if ( sdb.rec[ne][ns2].n <= 0 ) {
    fprintf(stderr,"no data for station %s and event %s\n", sdb.st[ns2].name, sdb.ev[ne].name );
    return 0;
  }
  if ( fabs(sdb.rec[ne][ns1].dt-sdb.rec[ne][ns2].dt) > .0001 ) {
    fprintf(stderr,"incompatible DT\n");
    return 0;
  }
  return 1;
}


/*c/////////////////////////////////////////////////////////////////////////*/
/*----------------------------------------------------------------------------
  correlation in frequ.-domain
  lag    = half length of correlation window
  cordir = directory for correl. results
  sdb    = SAC_DB structure with trace information

  calls fortran subroutines:
  -dcommon
  -dmultifft
----------------------------------------------------------------------------*/
int do_cor(int lag, char *cordir, char *pbdir)
{
  int ine, jsta1, jsta2;
  int len,ns,i; 
  char filename[STRING], amp_sac[STRING], phase_sac[STRING];
  char mondir[STRING];

  /*outermost loop over day number, then station number*/
  for( ine = 0; ine < sdb.nev; ine++ ) {
    fprintf(stderr,"sdb.nev %d\n",ine);
    make_dir(ine,cordir,pbdir,mondir);
    /*loop over "base" station number, this will be stored into common memory*/
    for( jsta1 = 0; jsta1 < sdb.nst; jsta1++ ) {  
      if(sdb.rec[ine][jsta1].n > 0){
	if(sdb.rec[ine][jsta1].n > 840000){
	  fprintf(stderr,"ERROR: trace longer than 840000 pts; %s\n",sdb.rec[ine][jsta1].ft_fname);
	  continue;
	}
        sprintf( amp_sac, "%s.am", sdb.rec[ine][jsta1].ft_fname );
        sprintf( phase_sac, "%s.ph", sdb.rec[ine][jsta1].ft_fname );
	// read amp and phase files and read into common memory
        if ( read_sac(amp_sac, amp, &shdamp1, 900000 )==NULL ) {
  	  fprintf( stderr,"file %s not found\n", amp_sac );
   	  continue;
        }
        if ( read_sac(phase_sac, phase, &shdph1, 900000)== NULL ) {
          fprintf( stderr,"file %s not found\n", phase_sac );
          continue;
	  }
	len = shdamp1.npts;
        dcommon_( &len, amp, phase ); // reads amp and phase files into common memory
	for( jsta2 = (jsta1+1); jsta2 < sdb.nst; jsta2++ ) {
  	  if(sdb.rec[ine][jsta2].n > 0){
	    if(sdb.rec[ine][jsta2].n > 840000){
	      fprintf(stderr,"ERROR: trace longer than 84000 pts; %s\n",sdb.rec[ine][jsta2].ft_fname);
	      continue;
	    }
	    // compute correlation
	    sprintf(amp_sac, "%s.am", sdb.rec[ine][jsta2].ft_fname);
            sprintf(phase_sac, "%s.ph", sdb.rec[ine][jsta2].ft_fname);
	    fprintf(stderr,"file %s  %s\n", sdb.rec[ine][jsta1].ft_fname,sdb.rec[ine][jsta2].ft_fname );
            // get array of floats for amp and phase of first signal
            if ( read_sac(amp_sac, amp, &shdamp2, 900000) ==NULL ) {
              fprintf(stderr,"file %s not found\n", amp_sac );
              continue;
            }
            if ( read_sac(phase_sac, phase, &shdph2, 900000)==NULL ) {
              fprintf(stderr,"file %s not found\n", phase_sac );
              continue;
	      }
	    len = shdamp2.npts;
            if(!check_info(ine, jsta1, jsta2 )) {
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
		sprintf(filename, "%s/COR_%s_%s.SAC",
			mondir, sdb.st[jsta1].name, sdb.st[jsta2].name);
		shdamp1.delta = sdb.rec[ine][jsta1].dt;
		shdamp1.evla =  sdb.st[jsta1].lat;
		shdamp1.evlo =  sdb.st[jsta1].lon;
		shdamp1.stla =  sdb.st[jsta2].lat;
		shdamp1.stlo =  sdb.st[jsta2].lon;
		shdamp1.npts =  2*lag+1;
		shdamp1.b    = -(lag)*shdamp1.delta;
		shdamp1.unused1 = 1;
		strncpy(shd_cor.kevnm,sdb.st[jsta1].name,7);
		strncpy(shd_cor.kstnm,sdb.st[jsta2].name,7);
		write_sac (filename, cor, &shdamp1);
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
void sac_db_chng (char *pbdir )

{
  int ie, is;
  char *result, *filename, *daydir;

  for ( ie = 0; ie < sdb.nev; ie++ ) for ( is = 0; is < sdb.nst; is++ )
    {
      if(sdb.rec[ie][is].ft_fname == NULL){
	printf("ERROR: ft_fname not found\n");
      }else {
	result=strrchr(sdb.rec[ie][is].ft_fname,'/');
	if(result != NULL){
	  filename = strdup(result);
	  *(result)='\0';
	  result=strrchr(sdb.rec[ie][is].ft_fname,'/');
	  daydir = strdup(result);
	  *(result+1)='\0';
 	  strcat(sdb.rec[ie][is].ft_fname,pbdir);
 	  strcat(sdb.rec[ie][is].ft_fname,daydir);
	  strcat(sdb.rec[ie][is].ft_fname,filename);
	  printf("dir is: %s\n",sdb.rec[ie][is].ft_fname);
	}else {
	  continue;
	}
	free(filename);
	free(daydir);
      }
    }
  return;
}


/*--------------------------------------------------------------------------
reading and checking commandline arguments
--------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char *fconf)
{
  int i;

  if (argc>3){
    fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strcpy(fconf,argv[++i]);
	break;

      case 'h':	fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
      }
    }
  }
}


/* ------------------------------------------------------------------------
   create sub-directory for correlations under correlation root directory
   according to given information in sdb-structure
   --------------------------------------------------------------------- */
void make_dir(int ie, char *cordir, char *pbdir, char *daydir){
  int month, year, day;
  char months[12][4] = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
  year = sdb.ev[ie].yy;
  month = sdb.ev[ie].mm;
  day   = sdb.ev[ie].dd;
  char yeardir[LINEL],mondir[LINEL],bnddir[LINEL];
  assert((strlen(cordir)+40)<LINEL);
  sprintf(bnddir,"%s/%s",cordir,pbdir);
  sprintf(yeardir,"%s/%d",bnddir,year);
  sprintf(mondir,"%s/%s",yeardir,months[month-1]);
  sprintf(daydir,"%s/%d_%d_%d_0_0_0",mondir,year,month,day);
  errno = 0;
  if(mkdir(cordir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",cordir, strerror (errno));
    }
  }
  if(mkdir(bnddir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",bnddir, strerror (errno));
    }
  }
  if(mkdir(yeardir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",yeardir, strerror (errno));
    }
  }
  errno = 0;
  if(mkdir(mondir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",mondir, strerror (errno));
    }
  }
  errno = 0;
  if(mkdir(daydir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",daydir, strerror (errno));
    }
  }
  return;
}


