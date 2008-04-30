/*--------------------------------------------------------------------------
  program to pre-process seed files:
  -initialising SAC_DB structure
  -converting seed-files into one-day sac-files
  -putting sac-files into the right directory

  written by Fan Chi ????
  changed by Yannik Behr 15/6/07 for use with sqlite and config-file
  $Log: sa_from_seed_mod.c,v $
  Revision 1.4  2007-07-05 06:51:11  behrya
  '-c' option added for alternative config file

  --------------------------------------------------------------------------*/


#define MAIN
/*#include <stddef.h>*/
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <mysac.h>
#include <sac_db.h>
#include <iniparser.h>
#include <strtok_mod.h>
#include <glob.h>
#include <assert.h>

/* os-dependent includes for dir-manipulation */
#include <sys/types.h>
#include <sys/stat.h>

/* MACROS */
#define LINEL 300
#define RDSEEDBUF 5000000
#define NPTSMAX 5000000
#define SLINE 10

/* GLOBAL VARIABLES */
char str[LINEL];

/* FUNCTION DECLARATIONS */
void get_args(int argc, char** argv, char configfile[LINEL]);
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax);
SAC_HD *read_sac_header(char *fname, SAC_HD *SHD);
void write_sac (char *fname, float *sig, SAC_HD *SHD);
int jday ( int y, int m, int d );
int isign(double f);
int nint(double f);
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms );
float av_sig (float *sig, int i, int N, int nwin );
int merge_sac(char *sta, char *chan, double *t0, float *dt, long *nrec);
int rdseed_cmd(char *rdseedroot, char *filename, char *chan, char *station, int ne, int ns);
int copy(char *in, char *out);
int mv_resp_file(SAC_DB *sdb, char *chan, int ns, int ne);
int mv_sac_files(SAC_DB *sdb, char *chan, int ne, int ns);
void fill_one_sta (SAC_DB *st1, char *inputstring);
void fill_one_event (SAC_DB *ev1, char *inputstring );
void mk_one_rec (SAC_DB *sdb, char *inputstring, char *rdseedroot, char *tmpdir);
int s_len_trim ( char *s );


/*========================== MAIN =================================================*/
int main (int na, char **arg)
{
  char puffer[LINEL];
  int ist, iev;
  FILE *ff, *fi;
  int rc;
  dictionary *dd;
  char *database;
  char *rdseedroot;
  char *tmpdir;
  char configfile[LINEL];
  static SAC_DB sdb;

  /* initialise SAC_DB structure */
  for ( iev = 0; iev < NEVENTS; iev++ ){
    for ( ist = 0; ist < NSTATION; ist++ ){
      sdb.rec[iev][ist].n = 0;
    }
  }
  printf("Initializing SAC_DB ok\n");

  strncpy(configfile,"./config.txt",LINEL-1);
  get_args(na,arg,configfile);

  /*opening config file*/
  dd = iniparser_new(configfile);
  /* reading in config-file parameters */
  database = iniparser_getstr(dd, "database:databasefile");
  rdseedroot = iniparser_getstr(dd, "database:rdseeddir");
  tmpdir = iniparser_getstr(dd, "database:tmpdir");

  if( (fi=fopen(database,"r")) == NULL) {
      fprintf(stderr, "ERROR: cannot open %s\n", database);
      return 1;
  }  

  sdb.cntst = 0;
  sdb.cntev = 0;

  while(fgets(puffer, LINEL, fi)){
    if(strstr(puffer,"[stations]") != 0){
      printf("Reading station information\n");
      while(fgets(puffer, LINEL, fi) > 0 && 
	    strstr(puffer,"[events]") == 0){
	if(s_len_trim(puffer) != 0){
	  fill_one_sta (&sdb, puffer);
	}
      }
      if(strstr(puffer,"[events]") != 0){
	printf("Reading event information and starting rdseed processing\n");
	while(fgets(puffer, LINEL, fi) > 0 && 
	      s_len_trim(puffer) != 0){
	  fill_one_event(&sdb,puffer);
	  printf("%s\n",puffer);
	  mk_one_rec(&sdb,puffer,rdseedroot,tmpdir);
	    }
      }
    }
  }
  fclose(fi);

  printf("\nnumber of events=%d and number of stations=%d\n",sdb.cntev,sdb.cntst);
  sdb.nst = sdb.cntst;
  sdb.nev = sdb.cntev;
  sdb.cntev = 0;

  sprintf(str,"%ssac_db.out\0", tmpdir);
  printf("name of sac database is: %s\n",str);
  ff = fopen(str,"wb");
  fwrite(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);
  iniparser_free(dd);
  return 0;
}
/*===========================================================================*/


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char configfile[LINEL]){
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

      case 'c':	strncpy(configfile,argv[++i],LINEL-1);
	break;

      case 'h':	fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}


/*--------------------------------------------------------------------------
  returns sign of f
  --------------------------------------------------------------------------*/
int isign(double f)
{
  if (f < 0.)     return -1;
  else            return 1;
}


/*--------------------------------------------------------------------------
  compute nearest integer to f
  --------------------------------------------------------------------------*/
int nint(double f){
  int i;
  double df;
  i=(int)f;
  df=f-(double)i;
  if (fabs(df) > .5) i=i+isign(df);

  return i;
}


/*--------------------------------------------------------------------------
  reads sac-files fname with maximum length nmax into signal sig and \
  header SHD
  --------------------------------------------------------------------------*/
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax){
  FILE *fsac;
  fsac = fopen(fname, "rb");
  if ( !fsac )
    {
      fclose (fsac);
      return NULL;
    }

  if ( !SHD ) SHD = &SAC_HEADER;

  fread(SHD,sizeof(SAC_HD),1,fsac);

  if ( SHD->npts > nmax )
    {
      fprintf(stderr,"WARNING: in file %s npts is limited to %d",fname,nmax);

      SHD->npts = nmax;
    }

  fread(sig,sizeof(float),(int)(SHD->npts),fsac);

  fclose (fsac);

  /*-------------  calcule de t0  ----------------*/
  {
    int eh, em ,i;
    float fes;
    char koo[9];

    for ( i = 0; i < 8; i++ ) koo[i] = SHD->ko[i];
    koo[8] = '\0';

    SHD->o = SHD->b + SHD->nzhour*3600. + SHD->nzmin*60 +
      SHD->nzsec + SHD->nzmsec*.001;


    return SHD;
  }
}


/*--------------------------------------------------------------------------
  writes sac file with name fname from signal sig with header SHD
  --------------------------------------------------------------------------*/
void write_sac (char *fname, float *sig, SAC_HD *SHD){
  FILE *fsac;
  int i;
  fsac = fopen(fname, "wb");

  if ( !SHD ) SHD = &SAC_HEADER;


  SHD->iftype = (long)ITIME;
  SHD->leven = (long)TRUE;

  SHD->lovrok = (long)TRUE;
  SHD->internal4 = 6L;

  SHD->depmin = sig[0];
  SHD->depmax = sig[0];
 
  for ( i = 0; i < SHD->npts ; i++ )
    {
      if ( SHD->depmin > sig[i] ) SHD->depmin = sig[i];
      if ( SHD->depmax < sig[i] ) SHD->depmax = sig[i];
    }

  fwrite(SHD,sizeof(SAC_HD),1,fsac);

  fwrite(sig,sizeof(float),(int)(SHD->npts),fsac);


  fclose (fsac);
}


/*--------------------------------------------------------------------------
  converts yyyy/mm/dd into year-day
  --------------------------------------------------------------------------*/
int jday ( int y, int m, int d ){
  int jd = 0;
  int i;
 
  for ( i = 1; i < m; i++ )
    {
      if ( (i==1) || (i==3) || (i==5) || (i==7) || (i==8) || (i==10) ) jd += 31;
      else if (i==2)
	{
	  if ( y == 4*(y/4) ) jd += 29;
	  else jd += 28;
	}
      else jd += 30;
    }
 
  return jd + d;
}


/*--------------------------------------------------------------------------
  computes time in s relative to 1900
  --------------------------------------------------------------------------*/
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms ){

  long nyday = 0, i;

  for ( i = 1901; i < yy; i++ )
    {
      if ( 4*(i/4) == i ) nyday += 366;
      else nyday += 365;
    }

  return 24.*3600.*(nyday+jday) + 3600.*hh + 60.*mm + ss + 0.001*ms;
}


/*------------------------------------------------------------------------
  computes arithmetic average for sig between sig[i-N/2] and sig[i+N/2]
  --------------------------------------------------------------------------*/
float av_sig (float *sig, int i, int N, int nwin ){
  int n1, n2, j, nav = 0;
  float av = 0.;

  if ( nwin > N ) nwin = N;

  n1 = i - nwin/2;

  if ( n1 < 0 ) n1 = 0;

  n2 = n1 + nwin - 1;

  if ( n2 > N-1 ) n2 = N-1;

  n1 = n2 - nwin + 1;

  for ( j = n1; j <= n2; j++ ) if ( sig[j] < 1.e29 )
    {
      av += sig[j];
      nav++;
    }

  if ( nav < 1 ) av = 1.e30;

  else av = av/(float)nav;

  return av;
}


/*-------------------------------------------------------------------------
  merge several sac files into one-day sac-files interpolating over data
  holes
  sta  = station name
  chan = channel
  t0   = date in s since 1900
  dt   = sample rate in s
  nrec = original number of data points in trace
  -------------------------------------------------------------------------*/
float sig0[NPTSMAX];

int merge_sac(SAC_DB *sd, char *chan, int ne, int ns){
  FILE *fi;
  glob_t dircont;
  int i, n, j, N, nfirst, Nholes;
  SAC_HD sh[300], s0;
  double t1[LINEL], t2[LINEL];
  double T1=1.e25, T2=100.;
  float sig1[NPTSMAX];
  int nf;

  assert((strlen(sd->st[ns].name)+strlen(chan)+7)<LINEL);
  sprintf(str,"*%s*%s*SAC",sd->st[ns].name,chan);
  glob(str, GLOB_NOSORT, NULL, &dircont);
  if(dircont.gl_pathc > 0){
  }else{
    fprintf(stderr, "ERROR: no SAC-files found for station %s and channel %s.\n", sta, chan);
    glob("*.SAC", GLOB_NOSORT, NULL, &dircont);
    if(dircont.gl_pathc >0){
      fprintf(stderr,"..... found other SAC-files instead!\n");
      fprintf(stderr,"..... something 's going wrong here\n");
      fprintf(stderr,"..... program is aborted\n");
      exit(1);
    }
    return 0;
  }
  
  for ( i = 0;i<dircont.gl_pathc;i++){
      if ( !read_sac_header( dircont.gl_pathv[i],&(sh[i])))
	{
	  fprintf(stderr,"ERROR: file %s not found\n", dircont.gl_pathv[i] );
	  continue;
	}
      t1[i] = abs_time (sh[i].nzyear, sh[i].nzjday, sh[i].nzhour, sh[i].nzmin, sh[i].nzsec, sh[i].nzmsec );
      t2[i] = t1[i] + sh[i].npts*sh[i].delta;

      /* finding the longest time series and the earliest starting time*/
      if ( t1[i] < T1 )
	{
	  T1 = t1[i];
	  nfirst = i;
	}

      if ( t2[i] > T2 ) T2 = t2[i];
    }

  memcpy(&s0, &(sh[nfirst]), sizeof(SAC_HD) );

  N = nint((T2-T1)/s0.delta);
  if ( N > NPTSMAX ) N = NPTSMAX;

  s0.npts = N;
  *t0 = T1;
  *dt = s0.delta;
  *nrec = s0.npts;

  for ( j = 0; j < N; j++ ) sig0[j] = 1.e30;


  for (i = 0;i<dircont.gl_pathc;i++){
    int nb;
    double ti;
    if ( !read_sac ( dircont.gl_pathv[i], sig1, &(sh[i]), N))
      {
	fprintf(stderr,"ERROR: file %s not found\n", dircont.gl_pathv[i]);
	continue;
      }

    if ( fabs(sh[i].delta-s0.delta) > .0001 )
      {
	fprintf(stderr,"ERROR: incompatible dt in file %s\n", dircont.gl_pathv[i]);
	continue;
      }

    ti = abs_time (sh[i].nzyear, sh[i].nzjday, sh[i].nzhour, sh[i].nzmin, sh[i].nzsec, sh[i].nzmsec );
    nb = nint((ti-T1)/s0.delta);

    /* finding all the values that are higher than 1e29 */
    for ( j = 0; j < sh[i].npts; j++ )
      {
	int jj = nb+j;

	if ( sig0[jj] > 1.e29 ) sig0[jj] = sig1[j];
      }
  }

  Nholes = 0;

  for ( j = 0; j < N; j++ ) if ( sig0[j] > 1.e29 ) Nholes++;

  if ( (float)Nholes/(float)N > 0.1 ){
    fprintf(stderr,"ERROR: too many holes\n");
    for(i=0;i<dircont.gl_pathc;i++){
      if(unlink(dircont.gl_pathv[i])!= 0)
	fprintf(stderr,"ERROR: cannot remove file %s.\n",dircont.gl_pathv[i]);
    }
    return 0;
  }


  for ( j = 0; j < N; j++ ){
    if ( sig0[j] > 1.e29 ){
      float av;
      int npart = 16;
      for( ;;){
	av = av_sig (sig0, j, N, N/npart );
	if ( av < 1.e29 ) break;
	if ( npart = 1 )
	  {
	    av = 0.;
	    break;
	  }
	npart = npart/2;
      }
      sig0[j] = av;
    }
  }
  write_sac ("merged.sac", sig0, &s0);

  for(i=0;i<dircont.gl_pathc;i++){
    if(unlink(dircont.gl_pathv[i])!= 0)
      fprintf(stderr,"ERROR: cannot remove file %s.\n",dircont.gl_pathv[i]);
  }
  return 1;
}

/*-------------------------------------------------------------------
  execute rdseed command 
  -----------------------------------------------------------------*/
int rdseed_cmd(char *rdseedroot, char *filename, char *chan, 
		char *station, int ne, int ns){
  glob_t dircont;
  FILE *ff;
  sprintf(str,"%srdseed 2>/dev/null 1>/dev/null",rdseedroot);
  ff = popen(str,"w");
  if(!ff){
      fprintf (stderr,"ERROR:incorrect parameters or too many files.\n");
      return 0;
    }
  int buffersize = RDSEEDBUF;
  fprintf(ff,"%s\n", filename);
  fprintf(ff,"\n");                             /* out file */
  fprintf(ff,"\n");                             /* volume */
  fprintf(ff,"d\n");                            /* option */
  fprintf(ff,"\n");                             /* summary file */
  fprintf(ff,"%s\n", station );        /* station list */
  fprintf(ff,"%s\n", chan);              /* channel list */
  fprintf(ff,"\n");                             /* network list */
  fprintf(ff,"\n");                             /* Loc Ids */
  fprintf(ff,"1\n");                            /* out format */
  fprintf(ff,"N\n");                            /* Output poles & zeroes */
  fprintf(ff,"0\n");                            /* Check Reversal */
  fprintf(ff,"\n");                             /* Select Data Type */
  fprintf(ff,"\n");                             /* Start Time */
  fprintf(ff,"\n");                             /* End Time */
  fprintf(ff,"%d\n", buffersize);               /* Sample Buffer Length  */
  fprintf(ff,"Y\n");                            /* Extract Responses */
  fprintf(ff,"quit\n");
  if (ferror (ff)){
    fprintf (stderr, "ERROR:Output to stream failed.\n");
    return 0;
  }
  if (pclose (ff) != 0){
    fprintf (stderr,"ERROR:Could not run rdseed or other error.\n");
    return 0;
  }

  assert((strlen("rdseed.err_log*")+1)<LINEL);
  sprintf(str,"rdseed.err_log*");
  glob(str, GLOB_NOSORT, NULL, &dircont);
  if(dircont.gl_pathc == 1){
    if(unlink(dircont.gl_pathv[0])!=0)
      fprintf(stderr,"ERROR: cannot remove rdseed error logfile.\n");
  }else{
    fprintf(stderr, "ERROR: no rdseed error logfile found.\n");
    return 0;
  }
  return 1;
}


/*-------------------------------------------------------
 copy routine for ascii-files
 in = src-file
 out = destination-file
 -------------------------------------------------------*/
int copy(char *in, char *out){
  FILE *fpin = fopen(in, "rb");
  FILE *fpout = fopen(out, "wb");
  int ch;

  assert(fpin && fpout);

  while( (ch = getc(fpin)) != EOF)
    putc(ch, fpout);
  fclose(fpin);
  fclose(fpout);
  return 1;
}


/*---------------------------------------------------------------------------
  copy response file from rdseed output to apropriate directory
  ---------------------------------------------------------------------------*/
int mv_resp_file(SAC_DB *sdb, char *chan, int ns, int ne){

  glob_t dircont;

  assert((strlen(sdb->st[ns].name)+strlen(chan)+6)<LINEL);
  sprintf(str,"RESP*%s*%s*",sdb->st[ns].name,chan);
  glob(str, GLOB_NOSORT, NULL, &dircont);
  if(dircont.gl_pathc == 1){
    assert((strlen(sdb->ev[ne].name)+strlen(dircont.gl_pathv[0])+1)<LINEL);
    sprintf(sdb->rec[ne][ns].resp_fname,"%s/%s\0", sdb->ev[ne].name, dircont.gl_pathv[0]);
  }else{
    fprintf(stderr, "ERROR: no or too many RESP-files found.\n");
    sdb->rec[ne][ns].n = 0;
    return 0;
  }
  if(!copy(dircont.gl_pathv[0],sdb->rec[ne][ns].resp_fname))
    fprintf(stderr,"ERROR: cannot copy RESP-file %s.\n",dircont.gl_pathv[0]);
  if(unlink(dircont.gl_pathv[0])!= 0)
    fprintf(stderr,"ERROR: cannot delete RESP-file %s.\n",dircont.gl_pathv[0]);
  return 1;
}


/*---------------------------------------------------------------------------
 move sac-files from rdseed output to apropriate place
 --------------------------------------------------------------------------*/
int mv_sac_files(SAC_DB *sdb, char *chan, int ne, int ns){
  
  struct stat attribut;

  if(stat("merged.sac", &attribut) == -1){
    fprintf(stderr,"ERROR in stat ...\n");
    return 0;
  }
  if(attribut.st_mode & S_IFREG){
    assert((strlen(sdb->ev[ne].name)+strlen(sdb->st[ns].name)+strlen(chan)+10)<LINEL);
    sprintf(str,"%s/%s.%s.SAC", sdb->ev[ne].name, sdb->st[ns].name, chan);
    if(!copy("merged.sac",str)){
      fprintf(stderr,"ERROR: cannot copy merged.sac.\n");
      return 0;
    }else{
      sprintf(sdb->rec[ne][ns].fname,"%s/%s.%s.SAC\0", sdb->ev[ne].name, sdb->st[ns].name, chan);
      sprintf(sdb->rec[ne][ns].ft_fname,"%s/ft_%s.%s.SAC\0", sdb->ev[ne].name, sdb->st[ns].name, chan);
      assert((strlen(chan)+1)<SLINE);
      sprintf(sdb->rec[ne][ns].chan,"%s", chan);
      if(unlink("merged.sac")!= 0)
	fprintf(stderr,"ERROR: cannot delete 'merged.sac'.\n");
    }
  }else{
    fprintf(stderr,"ERROR: 'merged.sac' not a regular file or doesn't exist.\n");
    return 0;
  }
  return 1;
}


/*------------------------------------------------------------------------
  read one-day seed-files into several sac-files and call merge_sac to 
  merge them into one sac file
  ------------------------------------------------------------------------*/
void mk_one_rec (SAC_DB *sdb, char *inputstring, char *rdseedroot, char *tmpdir){
  int ns, ne, err, i;
  glob_t dircont;
  char chan[SLINE], seedf[LINEL], sacdir[LINEL];
  int year, month, day, hour, min, sec;
  err = sscanf(inputstring,"%d %d %d %d %d %d %s %s %s",&year, &month, &day, &hour,
	       &min, &sec, &chan, &seedf, &sacdir );
  if(err == 9){
    ne = sdb->cntev;
    for(ns=0;ns<sdb->cntst;ns++){
      if ( sdb->rec[ne][ns].n > 0 ) break;
      rdseed_cmd(rdseedroot, seedf, chan, sdb->st[ns].name, ne, ns);
      if ( !merge_sac(sdb, ne, ns, chan) ){
	  sdb->rec[ne][ns].n = 0;
	  glob("RESP*", GLOB_NOSORT, NULL, &dircont);
	  for(i=0;i<dircont.gl_pathc;i++){
	    if(unlink(dircont.gl_pathv[i])!= 0)
	      fprintf(stderr,"ERROR: cannot delete RESP-file %s.\n",dircont.gl_pathv[0]);
	  }
	  continue;
	}
      mv_resp_file(sdb,chan,ns,ne);
      mv_sac_files(sdb,chan,ne,ns);
    }
    fprintf(stderr,".");
    sdb->cntev++;
  }else{
    fprintf(stderr,"ERROR: wrong number of entries in event table!\n");

  }
  return;
}


/*-------------------------------------------------------------------------
  read in station information into SAC_DB structure
  -------------------------------------------------------------------------*/
void  fill_one_sta (SAC_DB *st1, char *inputstring){
  int err;
  char name[SLINE];
  float lat, lon, elev;
  err = sscanf(inputstring,"%s %f %f %f",&name, &lat, &lon, &elev);
  if(err == 4){
    strncpy(st1->st[st1->cntst].name,name,SLINE-1);
    st1->st[st1->cntst].lat = lat;
    st1->st[st1->cntst].lon = lon;
    st1->cntst++;
  }else{
    fprintf(stderr,"ERROR: wrong number of entries in event table!\n");
  }
  return;
}


/*-------------------------------------------------------------------------
  write date and path of seed-files into SAC_DB structure       
  -------------------------------------------------------------------------*/
void fill_one_event (SAC_DB *ev1, char *inputstring ){
  int err;
  char chan[SLINE], seedf[LINEL], sacdir[LINEL];
  int year, month, day, hour, min, sec;
  err = sscanf(inputstring,"%d %d %d %d %d %d %s %s %s",&year, &month, &day, &hour,
	       &min, &sec, &chan, &seedf, &sacdir );
  if(err == 9){
    ev1->ev[ev1->cntev].yy = year;
    ev1->ev[ev1->cntev].mm = month;
    ev1->ev[ev1->cntev].dd = day;
    ev1->ev[ev1->cntev].h = hour;
    ev1->ev[ev1->cntev].m = min;
    ev1->ev[ev1->cntev].s = 0;
    ev1->ev[ev1->cntev].ms = 0;
    ev1->ev[ev1->cntev].ms = 10.*ev1->ev[ev1->cntev].ms;

    ev1->ev[ev1->cntev].jday = jday( ev1->ev[ev1->cntev].yy, ev1->ev[ev1->cntev].mm, ev1->ev[ev1->cntev].dd );
    
    ev1->ev[ev1->cntev].t0 = abs_time (ev1->ev[ev1->cntev].yy, ev1->ev[ev1->cntev].jday, 
				       ev1->ev[ev1->cntev].h, ev1->ev[ev1->cntev].m, 
				       ev1->ev[ev1->cntev].s, ev1->ev[ev1->cntev].ms );

    sprintf(ev1->ev[ev1->cntev].name,"%d_%d_%d_%d_%d_%d\0",ev1->ev[ev1->cntev].yy, ev1->ev[ev1->cntev].mm, 
	    ev1->ev[ev1->cntev].dd, ev1->ev[ev1->cntev].h, ev1->ev[ev1->cntev].m, ev1->ev[ev1->cntev].s );

    sprintf(str,"%s/%s",sacdir, ev1->ev[ev1->cntev].name);
    strncpy(ev1->ev[ev1->cntev].name,str,LINEL-1);
    sprintf(str,"mkdir %s", ev1->ev[ev1->cntev].name);
    system(str);
  }
  else{
    fprintf(stderr,"ERROR: wrong number of entries in event table!\n");
  }
  return;
}


/*-------------------------------------------------------------------------
  returns '0' if given string s is blank  
  -------------------------------------------------------------------------*/
int s_len_trim ( char *s ){
  int n,i=0;
  n = strlen(s);
  while(*(s+i) != '\n')
  {
    if ( *(s+i) == ' ' )
    {
    n--;
    }
    i++;
  }
  /* remove end-of-line character */
  n--;
  return n;
}


SAC_HD *read_sac_header(char *fname, SAC_HD *SHD)
{
 FILE *fsac;
/*..........................................................................*/
        if((fsac = fopen(fname, "rb")) == NULL) {
          printf("could not open sac file to read\n");
          exit(1);
        }

        if ( !fsac )
        {
          /*fprintf(stderr,"file %s not find\n", fname);*/
         return NULL;
        }

        if ( !SHD ) SHD = &SAC_HEADER;

         fread(SHD,sizeof(SAC_HD),1,fsac);

	 fclose (fsac);
   /*-------------  calcule de t0  ----------------*/
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
