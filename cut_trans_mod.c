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
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax);
void write_sac (char *fname, float *sig, SAC_HD *SHD);
void one_rec_trans( SAC_DB *sd, int ne, int ns, char *sacdir);
void one_rec_cut(SAC_DB *sd, int ne, int ns, float t1, float n);
void get_args(int argc, char** argv, SAC_DB* sdb);

char str[300];

/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, SAC_DB* sdb)
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

      case 'c':	strncpy(sdb->conf,argv[++i],149);
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
  reads sac-files fname with maximum length nmax into signal sig and \
  header SHD
  --------------------------------------------------------------------------*/
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax)
{
  FILE *fsac;

  if((fsac = fopen(fname, "rb")) == NULL) {
    printf("could not open sac file to read%s \n", fname);
    exit(1);
  }

  if ( !fsac ) {
    /*fprintf(stderr,"file %s not found\n", fname);*/
    return NULL;
  }

  if ( !SHD ) SHD = &SAC_HEADER;

  fread(SHD,sizeof(SAC_HD),1,fsac);

  if ( SHD->npts > nmax ) {
    fprintf(stderr,"ATTENTION !!! dans le fichier %s npts est limite a %d",fname,nmax);
    SHD->npts = nmax;
  }

  fread(sig,sizeof(float),(int)(SHD->npts),fsac);
  fclose (fsac);

  /*-------------  calcule de t0  ----------------*/
  {
    int eh, em ,i;
    float fes;
    char koo[9];

    for ( i = 0; i < 8; i++ ) {
      koo[i] = SHD->ko[i];
    }
    koo[8] = '\0';

    SHD->o = SHD->b + SHD->nzhour*3600. + SHD->nzmin*60 +
      SHD->nzsec + SHD->nzmsec*.001;

    //sscanf(koo,"%d%*[^0123456789]%d%*[^.0123456789]%g",&eh,&em,&fes);

    //SHD->o  -= (eh*3600. + em*60. + fes);
    /*-------------------------------------------*/}

  return SHD;
}


/*--------------------------------------------------------------------------
  writes sac file with name fname from signal sig with header SHD 
  --------------------------------------------------------------------------*/
void write_sac (char *fname, float *sig, SAC_HD *SHD)
{
  FILE *fsac;
  int i;
  if((fsac = fopen(fname, "wb"))==NULL) {
    printf("could not open sac file to write\n");
    exit(1);
  }

  if ( !SHD ) {
    SHD = &SAC_HEADER;
  }

  SHD->iftype = (long)ITIME;
  SHD->leven = (long)TRUE;
  SHD->lovrok = (long)TRUE;
  SHD->internal4 = 6L;
  SHD->depmin = sig[0];
  SHD->depmax = sig[0];

  for ( i = 0; i < SHD->npts ; i++ ) {
    if ( SHD->depmin > sig[i] ) {
      SHD->depmin = sig[i];
    }
    if ( SHD->depmax < sig[i] ) {
      SHD->depmax = sig[i];
    }
  }

  fwrite(SHD,sizeof(SAC_HD),1,fsac);
  fwrite(sig,sizeof(float),(int)(SHD->npts),fsac);

  fclose (fsac);
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
void one_rec_cut(SAC_DB *sd, int ne, int ns, float t1, float n)
{
  float sig1[200000]; 
  double t1b, t1e, t2b, t2e, t2;
  long n1, n2;
  char ft_name[100];
  char *tmpdir;
  SAC_HD shd1;
  dictionary *d;

  d = iniparser_new(sd->conf);
  tmpdir = iniparser_getstr(d, "database:tmpdir");

  t2 = t1 + (n-1)*sd->rec[ne][ns].dt;

  /* ATTENTION: THE FOLLOWING TEST IS HARD-WIRED TO 1s!!!! */
  t1b = sd->rec[ne][ns].t0 - sd->ev[ne].t0;
  t1e = t1b + (sd->rec[ne][ns].n-1)*sd->rec[ne][ns].dt;

  fprintf(stderr,"t1 %lg  t2 %lg   t1b %lg  t1e %lg\n", t1, t2, t1b, t1e);

  if ( (t1b>t1) || (t1e<t2) ) {
    fprintf(stderr,"incompatible time limits for station %s and event %s\n", sd->st[ns].name, sd->ev[ne].name );
    return;
  }

  sprintf(str,"%ss1.sac\0",tmpdir );
  if ( !read_sac (str, sig1, &shd1, 1000000 ) ) {
    fprintf(stderr,"file %s not found\n", sd->rec[ne][ns].fname );
    return;
  }

  n1 = (long)((t1-t1b)/sd->rec[ne][ns].dt);

  shd1.npts = n;
  shd1.nzyear = 2000;
  shd1.nzjday = 1;
  shd1.nzhour = 0;
  shd1.nzmin = 0;
  shd1.nzsec = 0;
  shd1.nzmsec = 0;
  shd1.b = 0.;

  strcpy(ft_name, sd->rec[ne][ns].ft_fname);
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
void one_rec_trans( SAC_DB *sd, int ne, int ns, char *sacdir)
{
  FILE *ff;
  float fl1, fl2, fl3, fl4;
  long n1, n2;
  char *tmpdir;
  dictionary *d;
  d = iniparser_new(sd->conf);
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

  if ( ne >= sd->nev ) return;
  if ( ns >= sd->nst  ) return;
  if ( sd->rec[ne][ns].n <= 0 ) return;

  sprintf(str,"/bin/cp %s %ss1.sac\0", sd->rec[ne][ns].fname,tmpdir ); 
  system(str);

  /* GENERATE TEMPORARY FILES */
  sprintf(str,"/bin/cp %s %sresp1\0", sd->rec[ne][ns].resp_fname,tmpdir );
  system(str);
   
  sprintf(str,"%ssac_bp_respcor\0",tmpdir);
  ff = fopen(str,"w");
  fprintf(ff,"%ssac << END\n",sacdir);
  fprintf(ff,"r %ss1.sac\n",tmpdir);
  fprintf(ff,"rmean\n");
  fprintf(ff,"rtrend\n");
  fprintf(ff,"transfer from evalresp fname %sresp1 to vel freqlimits %f %f %f %f\n",tmpdir, fl1, fl2, fl3, fl4 );
  if(sd->rec[ne][ns].dt!=1.0){
    printf("sampling rate is %f.\n",sd->rec[ne][ns].dt);
    fprintf(ff,"decimate 5 filter on\n");
    fprintf(ff,"decimate 5 filter on\n");
    fprintf(ff,"decimate 2 filter on\n");
    sd->rec[ne][ns].dt = 1.0;
  }
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

SAC_DB sdb;


/*////////////////////////////////////////////////////////////////////////*/
int main (int argc, char **argv)
{
  FILE *ff;
  int ne, ns;
  float t1, npts;
  dictionary *dd;
  char *tmpdir;
  char *sacdir;
  
  /* CHECK INPUT ARGUMENTS */
  strncpy(sdb.conf,"./config.txt",149);
  get_args(argc,argv,&sdb);
  sscanf(argv[1],"%f",&t1);
  sscanf(argv[2],"%f",&npts);

  fprintf(stderr,"t1-%f. npts-%f.\n", t1, npts);
  fprintf(stderr,"The program assumes the results are within the 1-5 s period band.\n");

  /* OPEN SAC DATABASE FILE AND READ IN TO MEMORY */
  dd = iniparser_new(sdb.conf);
  tmpdir = iniparser_getstr(dd, "database:tmpdir");
  sprintf(str,"%ssac_db.out\0", tmpdir);

  if((ff = fopen(str, "rb"))==NULL) {
    fprintf(stderr,"sac_db.out file not found\n");
    exit(1);
  }
  fread(&sdb, sizeof(SAC_DB), 1, ff);
  fclose(ff);
  sacdir = iniparser_getstr(dd, "database:sacdir");

  /* REMOVE INSTRUMENT RESPONSE AND CUT TO DESIRED LENGTH */
  for ( ns = 0; ns < sdb.nst; ns++ ) for ( ne = 0; ne < sdb.nev; ne++ ) {
    one_rec_trans( &sdb, ne, ns, sacdir);
    fprintf(stderr,"back to main prog\n");
    one_rec_cut( &sdb, ne, ns, t1, npts);
  }
  sprintf(str,"%ssac_db.out\0", tmpdir);
  ff = fopen(str,"wb");
  fwrite(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  iniparser_free(dd);
  return 0;
}
