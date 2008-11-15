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
#include <assert.h>

#define STRING 300
#define SSTRING 150

/* FUNCTION PROTOTYPES */
int one_rec_trans(int ne, int ns, char *sacdir, char *tmpdir, int respflag);
int one_rec_cut(int ne, int ns, float t1, float n, char *tmpdir);
void get_args(int argc, char** argv, char* conffile);

char str[STRING];

SAC_DB sdb;

/*////////////////////////////////////////////////////////////////////////*/
int main (int argc, char **argv)
{
  FILE *ff;
  int ne, ns;
  float t1, npts;
  char conffile[SSTRING];
  dictionary *dd;
  char *tmpdir;
  char *sacdir;
  int respflag ;
  /* CHECK INPUT ARGUMENTS */
  strncpy(conffile,"./config.txt",SSTRING-1);
  get_args(argc,argv,conffile);

  fprintf(stderr,"The program assumes the results are within the 1-5 s period band.\n");

  /* OPEN SAC DATABASE FILE AND READ IN TO MEMORY */
  dd       = iniparser_new(conffile);
  tmpdir   = iniparser_getstr(dd, "rm_resp:tmpdir");
  sacdir   = iniparser_getstr(dd, "rm_resp:sacdir");
  t1       = iniparser_getint(dd, "rm_resp:start_t", 1000);
  npts     = iniparser_getint(dd, "rm_resp:npts", 84000);
  respflag = iniparser_getint(dd, "rm_resp:rm_opt", 1);

  assert(strlen(conffile) < SSTRING);
  strncpy(sdb.conf,conffile,SSTRING-1);
  assert((strlen(tmpdir)+11) < STRING);
  sprintf(str,"%ssac_db.out", tmpdir);

  if((ff = fopen(str, "rb"))==NULL) {
    fprintf(stderr,"sac_db.out file not found\n");
    exit(1);
  }
  fread(&sdb, sizeof(SAC_DB), 1, ff);
  fclose(ff);

  /* REMOVE INSTRUMENT RESPONSE AND CUT TO DESIRED LENGTH */
  for ( ns = 0; ns < sdb.nst; ns++ ){
    for ( ne = 0; ne < sdb.nev; ne++ ) {
      if(!one_rec_trans(ne, ns, sacdir, tmpdir, respflag)){
	fprintf(stderr,"ERROR: removing instrument response failed.\n");
	continue;
      }
      if(!one_rec_cut(ne, ns, t1, npts, tmpdir)){
	fprintf(stderr,"ERROR: cutting trace failed.\n");
	continue;
      }
    }
  }
  sprintf(str,"%ssac_db.out", tmpdir);
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

  if (argc>3){
    fprintf(stderr,"USAGE: %s [-c alt/config.file]\n",argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strncpy(conffile,argv[++i],SSTRING-1);
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
int one_rec_cut(int ne, int ns, float t1, float n, char *tmpdir)
{
  float sig1[200000]; 
  double t1b, t1e, t2;
  long n1;
  char ft_name[SSTRING];
  SAC_HD shd1;

  t2 = t1 + (n-1)*sdb.rec[ne][ns].dt;

  /* ATTENTION: THE FOLLOWING TEST IS HARD-WIRED TO 1s!!!! */
  t1b = sdb.rec[ne][ns].t0 - sdb.ev[ne].t0;
  t1e = t1b + (sdb.rec[ne][ns].n-1)*sdb.rec[ne][ns].dt;

  fprintf(stderr,"t1 %lg  t2 %lg   t1b %lg  t1e %lg\n", t1, t2, t1b, t1e);

  if ( (t1b>t1) || (t1e<t2) ) {
    fprintf(stderr,"incompatible time limits for station %s and event %s\n", sdb.st[ns].name, sdb.ev[ne].name );
    assert((strlen(tmpdir)+14) < STRING);
    sprintf(str,"/bin/rm %ss1.sac",tmpdir );
    system(str);
    return 0;
  }

  sprintf(str,"%ss1.sac",tmpdir );
  if ( !read_sac (str, sig1, &shd1, 1000000 ) ) return 0;

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
  assert((strlen(tmpdir)+14) < STRING);
  sprintf(str,"/bin/rm %ss1.sac",tmpdir );
  system(str);
  return 1;
}


/*--------------------------------------------------------------------------
  remove mean, trend and instrument response 
  ne = number of event
  ns = number of station
  sd = SAC_DB structure written by sa_from_seed_mod
  sacdir = pointer to dir of sac-binaries
  ---------------------------------------------------------------------------*/
int one_rec_trans(int ne, int ns, char *sacdir, char *tmpdir, int respflag)
{
  FILE *ff;
  float fl1, fl2, fl3, fl4, factor=1;
  int freq;

  /* ASSUME THAT THE DATA ARE WITHIN THE FOLLOWING FILTER BAND */
  fl1=1.0/170.0;		/* currently set for 5-150 s period band */
  fl2=1.0/160.0;
  fl3=1.0/4.0;
  fl4=1.0/3.0;
  if ( (fl1<=0.)||(fl2<=0.)||(fl3<=0.)||(fl4<=0.)||(fl1>=fl2)||(fl2>=fl3)||(fl3>=fl4) ) {
    fprintf(stderr,"ERROR incompatible frequency limits.\n");
    exit(1);
  }
  else {
    fprintf(stdout,"Frequency limits: %f %f %f %f\n", fl1, fl2, fl3, fl4);
  }

  if ( ne >= sdb.nev ) return 0;
  if ( ns >= sdb.nst  ) return 0;
  if ( sdb.rec[ne][ns].n <= 0 ) return 0;

  /* open pipe to sac-process */
  assert((strlen(sacdir)+3) < STRING);
  sprintf(str,"%ssac",sacdir);
  ff = popen(str, "w");
  if (NULL == ff){
      fprintf (stderr,"ERROR: cannot open pipe to SAC subprocess.\n");
      return 0;
  }

  fprintf(ff,"r %s\n",sdb.rec[ne][ns].fname);
  fprintf(ff,"rmean\n");
  fprintf(ff,"rtrend\n");
  if(respflag == 1){
    fprintf(ff,"transfer from evalresp fname %s to vel freqlimits %f %f %f %f\n",
	    sdb.rec[ne][ns].resp_fname, fl1, fl2, fl3, fl4 );
  }else if(respflag == 0){
    fprintf(ff,"transfer from polezero subtype %s to vel freqlimits %f %f %f %f\n",
	    sdb.rec[ne][ns].pz_fname, fl1, fl2, fl3, fl4 );
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
  if(pclose (ff) != 0){
    fprintf (stderr,"ERROR: when closing pipe.\n");
    return 0;
  }
  
  return 1;
}

