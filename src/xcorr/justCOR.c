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
#define MODUS 0711
#define STRING 300
#define SSTRING 150

/* Function prorotypes */
void dcommon_(int *len, float *amp,float *phase);
void dmultifft_(int *len,float *amp,float *phase, int *lag,float *seis_out, int *ns);
void swapn(unsigned char *b, int N, int n);
int check_info (int ne, int ns1, int ns2 );
int do_cor(int lag, char *cordir);
void sac_db_chng (char *pbdir);
static int glob_this(const char *fpath, const struct stat *sb,
		     int tflag, struct FTW *ftwbuf);
void get_args(int argc, char** argv);


SAC_DB sdb;

/*c/////////////////////////////////////////////////////////////////////////*/
int main (int na, char **arg)
{
  FILE *ff;
  int lag;
  int flags = 1;
  char str[600];
  dictionary *dd;
  char *tmpdir, *sacdirroot, *cordir, *pbdir;
  strcpy(sdb.conf,"./config.txt");

  get_args(na, arg);

  /* OPEN SAC DATABASE FILE AND READ IN TO MEMORY */
  dd         = iniparser_new(sdb.conf);
  tmpdir     = iniparser_getstr(dd, "xcor:tmpdir");
  sacdirroot = iniparser_getstr(dd, "xcor:sacfiles");
  cordir     = iniparser_getstr(dd, "xcor:cordir");
  lag        = iniparser_getint(dd, "xcor:lag", 3000);
  pbdir      = iniparser_getstr(dd, "xcor:pbdir");

  sprintf(str,"%ssac_db.out", tmpdir);
  ff = fopen(str,"rb");
  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  /* change ft_fname value in sdb-struct */
  sac_db_chng(pbdir);

  /*do all the work of correlations here  */
  do_cor(lag,cordir);  
  printf("correlations finished\n");

  /* move COR/COR_STA1_STA2.SAC.prelim to COR/COR_STA1_STA2.SAC */
  if (nftw(cordir, glob_this, 20, flags) == -1) {
      perror("nftw");
      exit(EXIT_FAILURE);
  }

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
int do_cor(int lag, char *cordir)
{
  int ine, jsta1, jsta2, k;

  int len,ns,i; 


  char filename[STRING], amp_sac[STRING], phase_sac[STRING], yeardir[STRING], mondir[STRING];
  char *buf, *month, *year;
  float amp[400000], phase[400000], cor[400000];
  float seis_out[400000];

  // outermost loop over day number, then station number

  for( ine = 0; ine < sdb.nev; ine++ ) {
    fprintf(stderr,"sdb.nev %d\n",ine);

    // loop over "base" station number, this will be stored into common memory

    for( jsta1 = 0; jsta1 < sdb.nst; jsta1++ ) {  

      if(sdb.rec[ine][jsta1].n > 0){
        sprintf( amp_sac, "%s.am", sdb.rec[ine][jsta1].ft_fname );
        sprintf( phase_sac, "%s.ph", sdb.rec[ine][jsta1].ft_fname );

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

	for( jsta2 = (jsta1+1); jsta2 < sdb.nst; jsta2++ ) {

  	  if(sdb.rec[ine][jsta2].n > 0){

	    // compute correlation
	    sprintf(amp_sac, "%s.am", sdb.rec[ine][jsta2].ft_fname);
            sprintf(phase_sac, "%s.ph", sdb.rec[ine][jsta2].ft_fname);
	    fprintf(stderr,"file %s  %s\n", sdb.rec[ine][jsta1].ft_fname,sdb.rec[ine][jsta2].ft_fname );
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

		// move and rename cor file accordingly 
		/* extract location for correlations */
		/* and create COR-dir if necessary   */
		buf = strdup(sdb.ev[ine].name);
		month = strdup(basename(dirname(buf)));
		year = strdup(basename(dirname(buf)));
		assert(strlen(cordir)+strlen(year)+strlen(month)+3<STRING);
		sprintf(yeardir,"%s/%s",cordir,year);
		if(mkdir(yeardir, MODUS) == -1){
		  printf("directory %s already exists \n", yeardir); 
		}
		sprintf(mondir,"%s/%s/%s/",cordir,year,month);
		if(mkdir(mondir, MODUS) == -1){
		  printf("directory %s already exists \n", mondir); 
		}
		
		
		sprintf(filename, "%s/COR_%s_%s.SAC.prelim",
			mondir, sdb.st[jsta1].name, sdb.st[jsta2].name);

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
		  shdamp1.delta = sdb.rec[ine][jsta1].dt;
		  shdamp1.evla =  sdb.st[jsta1].lat;
		  shdamp1.evlo =  sdb.st[jsta1].lon;
		  shdamp1.stla =  sdb.st[jsta2].lat;
		  shdamp1.stlo =  sdb.st[jsta2].lon;
		  shdamp1.npts =  2*lag+1;
		  shdamp1.b    = -(lag)*shdamp1.delta;
		  shdamp1.unused1 = 0;
		  write_sac (filename, cor, &shdamp1);
		}
		free(buf);
		free(month);
		free(year);
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


/*------------------------------------------------------------ 
 *  call-back function for nftw()
  ------------------------------------------------------------*/
static int glob_this(const char *fpath, const struct stat *sb,
		     int tflag, struct FTW *ftwbuf){
  const char pattern[] = "*.prelim";
  char localpattern[STRING];
  char *newname, *ptr;
  glob_t match;
  int j;

  assert((strlen(fpath)+strlen(pattern))<STRING-1);
  sprintf(localpattern,"%s/%s",fpath, pattern);

  if(glob(localpattern, 0, NULL, &match) == 0){
      for(j=0;j<match.gl_pathc;j++){
	newname = strdup(match.gl_pathv[j]);
	ptr = strrchr(newname,'.');
	*(ptr) = '\0';
	printf("--> rename %s to %s\n", match.gl_pathv[j], newname);
	if( (rename(match.gl_pathv[j],newname)) < 0) {
	  fprintf(stderr, "---->ERROR while renaming");
	  return EXIT_FAILURE;
	}
	free(newname);
      }
  }
  globfree(&match);
  return 0;
}


/*--------------------------------------------------------------------------
reading and checking commandline arguments
--------------------------------------------------------------------------*/
void get_args(int argc, char** argv)
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

      case 'c':	strcpy(sdb.conf,argv[++i]);
	break;

      case 'h':	fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
      }
    }
  }
}

