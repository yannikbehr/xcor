/*--------------------------------------------------------------------------
  program to pre-process sac files:
  -program takes sac files from sa_from_seed_holes
  -removes the instrument response 
  -cuts the file based on the user input parameters [t1] and [npts]

  program is hard-wired a broadband signal in the period band 5-150 s
  this can be changed in the one_rec_trans function

  written by Fan Chi ????
  $Rev$
  $Author$
  $LastChangedDate$
  --------------------------------------------------------------------------*/


#define MAIN
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <iniparser.h>
#include <mysac.h>
#include <sac_db.h>


/* FUNCTION PROTOTYPES */
void one_rec_trans(int ne, int ns, char *sacdir, int respflag);
void one_rec_cut(int ne, int ns, float t1, float n);
void get_args(int argc, char** argv, char* conffile);

char str[300];

SAC_DB sdb;

/*////////////////////////////////////////////////////////////////////////*/
int main (int argc, char **argv)
{
  FILE *ff;
  int ne, ns;
  float t1, npts;
  char conffile[150];
  dictionary *dd;
  char *tmpdir;
  char *sacdir;
  int respflag = 1;
  /* CHECK INPUT ARGUMENTS */
  strncpy(conffile,"./config.txt",149);
  get_args(argc,argv,conffile);
  sscanf(argv[1],"%f",&t1);
  sscanf(argv[2],"%f",&npts);

  fprintf(stderr,"t1-%f. npts-%f.\n", t1, npts);
  fprintf(stderr,"The program assumes the results are within the 1-5 s period band.\n");

  /* OPEN SAC DATABASE FILE AND READ IN TO MEMORY */
  dd = iniparser_new(conffile);
  tmpdir = iniparser_getstr(dd, "database:tmpdir");
  sprintf(str,"%ssac_db.out\0", tmpdir);

  if((ff = fopen(str, "rb"))==NULL) {
    fprintf(stderr,"sac_db.out file not found\n");
    exit(1);
  }

  fread(&sdb, sizeof(SAC_DB), 1, ff);
  fclose(ff);
  sacdir = iniparser_getstr(dd, "database:sacdir");
  strncpy(sdb.conf,conffile,149);

  /* REMOVE INSTRUMENT RESPONSE AND CUT TO DESIRED LENGTH */
  for ( ns = 0; ns < sdb.nst; ns++ ){
    for ( ne = 0; ne < sdb.nev; ne++ ) {
    one_rec_trans(ne, ns, sacdir, respflag);
    fprintf(stderr,"back to main prog\n");
    one_rec_cut(ne, ns, t1, npts);
    }
  }
  sprintf(str,"%ssac_db.out\0", tmpdir);
  ff = fopen(str,"wb");
  fwrite(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  iniparser_free(dd);
  return 0;
}


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char* conffile)
{
  int i;

  if (argc>5){
    fprintf(stderr,"USAGE: %s t1 npts [-c alt/config.file]\n",argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strncpy(conffile,argv[++i],149);
	break;

      case 'h':	    fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}


/*--------------------------------------------------------------------------
  cuts signal "s1.sac" from one_rec_trans between borders given
  by commandline arguments
  ne = number of event
  ns = number of station
  sd = SAC_DB structure written by sa_from_seed_mod
  t1 = lower boundary [s]
  n  = number of samples between lower and upper boundary
  --------------------------------------------------------------------------*/
void one_rec_cut(int ne, int ns, float t1, float n)
{
  float sig1[200000]; 
  double t1b, t1e, t2b, t2e, t2;
  long n1, n2;
  char ft_name[100];
  char *tmpdir;
  SAC_HD shd1;
  dictionary *d;

  d = iniparser_new(sdb.conf);
  tmpdir = iniparser_getstr(d, "database:tmpdir");

  t2 = t1 + (n-1)*sdb.rec[ne][ns].dt;

  /* ATTENTION: THE FOLLOWING TEST IS HARD-WIRED TO 1s!!!! */
  t1b = sdb.rec[ne][ns].t0 - sdb.ev[ne].t0;
  t1e = t1b + (sdb.rec[ne][ns].n-1)*sdb.rec[ne][ns].dt;

  fprintf(stderr,"t1 %lg  t2 %lg   t1b %lg  t1e %lg\n", t1, t2, t1b, t1e);

  if ( (t1b>t1) || (t1e<t2) ) {
    fprintf(stderr,"incompatible time limits for station %s and event %s\n", sdb.st[ns].name, sdb.ev[ne].name );
    return;
  }

  sprintf(str,"%ss1.sac\0",tmpdir );
  if ( !read_sac (str, sig1, &shd1, 1000000 ) ) {
    fprintf(stderr,"file %s not found\n", sdb.rec[ne][ns].fname );
    return;
  }

  n1 = (long)((t1-t1b)/sdb.rec[ne][ns].dt);

  shd1.npts = n;
  shd1.nzyear = 2000;
  shd1.nzjday = 1;
  shd1.nzhour = 0;
  shd1.nzmin = 0;
  shd1.nzsec = 0;
  shd1.nzmsec = 0;
  shd1.b = 0.;

  strcpy(ft_name, sdb.rec[ne][ns].ft_fname);
  write_sac (ft_name, &(sig1[n1]), &shd1 );
  sprintf(str,"/bin/rm %ss1.sac",tmpdir );
  system(str);
  iniparser_free(d);
}


/*--------------------------------------------------------------------------
  remove mean, trend and instrument response 
  ne = number of event
  ns = number of station
  sd = SAC_DB structure written by sa_from_seed_mod
  sacdir = pointer to dir of sac-binaries
  ---------------------------------------------------------------------------*/
void one_rec_trans(int ne, int ns, char *sacdir, int respflag)
{
  FILE *ff;
  float fl1, fl2, fl3, fl4, freq1, factor=1;
  int freq, i;
  long n1, n2;
  char *tmpdir;
  dictionary *d;
  d = iniparser_new(sdb.conf);
  tmpdir = iniparser_getstr(d, "database:tmpdir");

  /* ASSUME THAT THE DATA ARE WITHIN THE FOLLOWING FILTER BAND */
  fl1=1.0/170.0;		/* currently set for 5-150 s period band */
  fl2=1.0/160.0;
  fl3=1.0/4.0;
  fl4=1.0/3.0;
  if ( (fl1<=0.)||(fl2<=0.)||(fl3<=0.)||(fl4<=0.)||(fl1>=fl2)||(fl2>=fl3)||(fl3>=fl4) ) {
    fprintf(stderr,"Error with frequency limits for transfer from evalresp.\n");
    exit(1);
  }
  else {
    fprintf(stderr,"Frequency limits: %f %f %f %f\n", fl1, fl2, fl3, fl4);
  }

  if ( ne >= sdb.nev ) return;
  if ( ns >= sdb.nst  ) return;
  if ( sdb.rec[ne][ns].n <= 0 ) return;

  sprintf(str,"/bin/cp %s %ss1.sac\0", sdb.rec[ne][ns].fname,tmpdir ); 
  system(str);

  /* GENERATE TEMPORARY FILES */
  if(respflag == 1){
    sprintf(str,"/bin/cp %s %sresp1\0", sdb.rec[ne][ns].resp_fname,tmpdir );
    system(str);
  }else if(respflag == 0){
    sprintf(str,"/bin/cp %s %sresp1\0", sdb.rec[ne][ns].pz_fname,tmpdir );
    system(str);
  }
   
  sprintf(str,"%ssac_bp_respcor\0",tmpdir);
  ff = fopen(str,"w");
  fprintf(ff,"%ssac << END\n",sacdir);
  fprintf(ff,"r %ss1.sac\n",tmpdir);
  fprintf(ff,"rmean\n");
  fprintf(ff,"rtrend\n");
  if(respflag == 1){
    fprintf(ff,"transfer from evalresp fname %sresp1 to vel freqlimits %f %f %f %f\n",
	    tmpdir, fl1, fl2, fl3, fl4 );
  }else if(respflag == 0){
    fprintf(ff,"transfer from polezero subtype %sresp1 to vel freqlimits %f %f %f %f\n",
	    tmpdir, fl1, fl2, fl3, fl4 );
  }

  if(sdb.rec[ne][ns].dt < 1.0){
    /*****************************************************************/
    /* The following part was edited by Z. Rawlinson in order to     */
    /* automatically downsample traces with sample frequencies       */
    /* higher than 1 Hz                                              */
    /* the sac-manual says that only numbers between 2 and 7 can be  */
    /* used with the command 'decimate'; factor 4 and 6 can be       */
    /* substituted by 2 and 3                                        */
    /* 01/08                                                         */

    /* in order to prevent rounding errors i.e. int(1./0.0250041) be-*/
    /* coming 39 instead of 40 we'll disregard any decimal numbers   */
    /* smaller than 0.0001 */
    /* Y.Behr 08/08 */
    freq  = 100000/(int)floor(sdb.rec[ne][ns].dt*100000.);
    printf("sampling rate is %d.\n",freq);
    while (freq % 7 == 0 && freq > 1){
      freq=freq/7;
      factor = factor * 7;
      fprintf(ff,"decimate 7 filter on\n");
    }
    while (freq % 5 == 0 && freq > 1){
      freq=freq/5;
      factor = factor * 5;
      fprintf(ff,"decimate 5 filter on\n");
    }
    while (freq % 3 == 0 && freq > 1){
      freq=freq/3;
      factor = factor * 3;
      fprintf(ff,"decimate 3 filter on\n");
    }
    while (freq % 2 == 0 && freq > 1){
      freq=freq/2;
      factor = factor * 2;
      fprintf(ff,"decimate 2 filter on\n");
    }
    
    sdb.rec[ne][ns].dt = 1.0;
    sdb.rec[ne][ns].n  = (int)(sdb.rec[ne][ns].n/factor);
  }
  /*******************************************************************/

  fprintf(ff,"w %ss1.sac\n",tmpdir);
  fprintf(ff,"quit\n");
  fprintf(ff,"END\n");
  fclose(ff);

  sprintf(str,"sh %ssac_bp_respcor\0",tmpdir );
  system(str);
  sprintf(str,"/bin/rm %sresp1\0",tmpdir );
  system(str);
  iniparser_free(d);
}

