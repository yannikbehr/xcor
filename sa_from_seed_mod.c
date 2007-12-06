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
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <sqlite.h>
#include <mysac.h>
#include <sac_db.h>
#include <iniparser.h>


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, SAC_DB* sdb)
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

      case 'c':	strncpy(sdb->conf,argv[++i],149);
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
int nint(double f)
{
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
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax)
{
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
  write SAC_DB structure to ascii table 'fname'
  --------------------------------------------------------------------------*/
void sac_db_write_to_asc ( SAC_DB *sdb, char *fname )
{
  int ie, is;
  FILE *fi, *ff;
  static SAC_HD shd;

  ff = fopen(fname,"w");

  for ( ie = 0; ie < sdb->nev; ie++ ) for ( is = 0; is < sdb->nst; is++ )
    {
      fprintf(ff,"%s  %s  ", sdb->ev[ie].name, sdb->st[is].name );

      if ( sdb->rec[ie][is].n <= 0 ) fprintf(ff,"NO DATA\n");

      else 
	{
	  fi = fopen(sdb->rec[ie][is].fname,"rb");
	  fread(&shd, sizeof(SAC_HD), 1, fi );
	  fclose(fi);

	  fprintf(ff,"%s  t0: %d/%d:%d:%d:%g  %g s of record\n", sdb->rec[ie][is].fname, 
		  shd.nzyear, shd.nzjday, shd.nzhour, shd.nzmin, 
		  (shd.nzsec + 0.001*shd.nzmsec), shd.delta*shd.npts );
	}
    } 
      
  fclose(ff);
}


/*--------------------------------------------------------------------------
  converts yyyy/mm/dd into year-day
  --------------------------------------------------------------------------*/
int jday ( int y, int m, int d )
{
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
float av_sig (float *sig, int i, int N, int nwin )
{
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


/*/////////////////////////////////////////////////////////////////////////*/
char str[300];

char fname[300][300];
double t1[300], t2[300], T1, T2;
SAC_HD sd[300], s0;
int nf;

#define NPTSMAX 100000000

float sig0[NPTSMAX], sig1[NPTSMAX];
/*-------------------------------------------------------------------------
  merge several sac files into one-day sac-files interpolating over data
  holes
  sta  = station name
  chan = channel
  t0   = date in s since 1900
  dt   = sample rate in s
  nrec = original number of data points in trace
  -------------------------------------------------------------------------*/
int merge_sac(char *sta, char *chan, double *t0, float *dt, long *nrec)
{
  FILE *fi;
  int i, n, j, N, nfirst, Nholes;

  T1 = 1.e25;
  T2 = -100.;
  

  sprintf(str,"ls *%s*%s*SAC > list_sac\0", sta, chan);
  system(str);

  fi = fopen("list_sac","r");

  if ( !fi )
    {
      fprintf(stderr,"no list_sac\n");

      sprintf(str,"/bin/rm *%s*%s*SAC\0", sta, chan);
      system(str);
      system("/bin/rm list_sac");

      fclose(fi);
      return 0;
    }

  if ( fscanf(fi,"%s", &(fname[0]) ) == EOF )
    {
      fprintf(stderr,"void list_sac\n" );

      sprintf(str,"/bin/rm *%s*%s*SAC\0", sta, chan);
      system(str);
      system("/bin/rm list_sac");

      fclose(fi);
      return 0;
    }

  fclose(fi);


  fi = fopen("list_sac","r");

  for ( i = 0; ; )
    {
      if ( fscanf(fi,"%s", &(fname[i]) ) == EOF ) break;

      if ( !read_sac ( fname[i], sig1, &(sd[i]), NPTSMAX) )
	{
	  fprintf(stderr,"file %s not found\n", fname[i] );
	  continue;
	}

      t1[i] = abs_time (sd[i].nzyear, sd[i].nzjday, sd[i].nzhour, sd[i].nzmin, sd[i].nzsec, sd[i].nzmsec );
      t2[i] = t1[i] + sd[i].npts*sd[i].delta;

      /* finding the longest time series */
      if ( t1[i] < T1 )
	{
	  T1 = t1[i];
	  nfirst = i;
	}

      if ( t2[i] > T2 ) T2 = t2[i];

      i++;
    }

  fclose(fi);


  memcpy(&s0, &(sd[nfirst]), sizeof(SAC_HD) );

  N = nint((T2-T1)/s0.delta);
  if ( N > NPTSMAX ) N = NPTSMAX;

  if ( N > 10000000 ) N = 10000000;

  s0.npts = N;

  *t0 = T1;

  *dt = s0.delta;

  *nrec = s0.npts;


  for ( j = 0; j < N; j++ ) sig0[j] = 1.e30;


  fi = fopen("list_sac","r");

  for ( i = 0; ; )
    {
      int nb;
      double ti;

      if ( fscanf(fi,"%s", &(fname[i]) ) == EOF ) break;

      if ( !read_sac ( fname[i], sig1, &(sd[i]), NPTSMAX-N) )
	{
	  fprintf(stderr,"file %s not found\n", fname[i] );
	  continue;
	}

      if ( fabs(sd[i].delta-s0.delta) > .0001 )
	{
	  fprintf(stderr,"incompatible dt in file file %s\n", fname[i] );
	  continue;
	}

      ti = abs_time (sd[i].nzyear, sd[i].nzjday, sd[i].nzhour, sd[i].nzmin, sd[i].nzsec, sd[i].nzmsec );

      nb = nint((ti-T1)/s0.delta);

      /* finding the all values that are higher than 1e29 */
      for ( j = 0; j < sd[i].npts; j++ )
	{
	  int jj = nb+j;

	  if ( sig0[jj] > 1.e29 ) sig0[jj] = sig1[j];
	}

      i++;
    }

  fclose(fi);


  Nholes = 0;

  for ( j = 0; j < N; j++ ) if ( sig0[j] > 1.e29 ) Nholes++;

  if ( (float)Nholes/(float)N > 0.1 )
    {
      fprintf(stderr,"too many holes\n");

      sprintf(str,"/bin/rm *%s*%s*SAC\0", sta, chan);
      system(str);
      system("/bin/rm list_sac");

      return 0;
    }


  for ( j = 0; j < N; j++ ) if ( sig0[j] > 1.e29 )
    {
      float av;
      int npart = 16;

      for ( ;;) 
	{
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

  write_sac ("merged.sac", sig0, &s0);


  sprintf(str,"/bin/rm *%s*%s*SAC\0", sta, chan);
  system(str);
  system("/bin/rm list_sac");

  return 1;
}


/*------------------------------------------------------------------------
  read one-day seed-files into several sac-files and call merge_sac to 
  merge them into one sac file
  ------------------------------------------------------------------------*/
void mk_one_rec (SAC_DB *sdb,char **buff)
{
  FILE *ff;
  int ns,ne;
  dictionary *d;
  char *rdseedroot;
  char *tmpdir;
  char *bufftmp;
  static char resp_name[150];

  d = iniparser_new(sdb->conf);
  rdseedroot = iniparser_getstr(d, "database:rdseeddir");
  tmpdir = iniparser_getstr(d, "database:tmpdir");
  ne = sdb->cntev;
  for(ns=0;ns<sdb->cntst;ns++){
    if ( sdb->rec[ne][ns].n > 0 ) break;
    /*buffersize should be aquired dynamically*/
    int buffersize=8640000;
    strcpy(bufftmp,tmpdir);
    strcat(bufftmp,"from_seed");
    ff = fopen(bufftmp,"w");
    sprintf(str,"%srdseed <<END\n",rdseedroot);
    fprintf(ff,"%srdseed <<END\n", rdseedroot);
    fprintf(ff,"%s\n", buff[0] );
    fprintf(ff,"\n");                             /* out file */
    fprintf(ff,"\n");                             /* volume */
    fprintf(ff,"d\n");                            /* option */
    fprintf(ff,"\n");                             /* summary file */
    fprintf(ff,"%s\n", sdb->st[ns].name );        /* station list */
    fprintf(ff,"%s\n", buff[1] );                      /* channel list */
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
    fprintf(ff,"END\n");

    
    fclose(ff);

    sprintf(str,"sh %s\0",bufftmp);
    system(str);

    if ( !merge_sac(sdb->st[ns].name, buff[1], &(sdb->rec[ne][ns].t0), &(sdb->rec[ne][ns].dt), &(sdb->rec[ne][ns].n) ) )
      {
	sdb->rec[ne][ns].n = 0;
	continue;
      }

    /*---------- response file -----------*/
    sprintf(str,"ls RESP*%s*%s* > list_resp\0",  sdb->st[ns].name,  buff[1]);
    system(str);
    sprintf(str,"head list_resp\n");
    system(str);
    ff = fopen("list_resp","r");

    if ( fscanf(ff,"%s", resp_name ) == EOF )
      {
	sdb->rec[ne][ns].n = 0;
	continue;
      }

    fclose(ff);
    
    sprintf(sdb->rec[ne][ns].resp_fname,"%s/%s\0", sdb->ev[ne].name, resp_name);
    sprintf(str,"/bin/mv %s %s\0", resp_name, sdb->rec[ne][ns].resp_fname);
    system(str);

    system("/bin/rm list_resp");
    system("/bin/rm RESP*");


    /*------------- moving sac file -------*/
    sprintf(str,"/bin/mv merged.sac %s/%s.%s.SAC\0", sdb->ev[ne].name, sdb->st[ns].name, buff[1]);
    system(str);
  
    sprintf(sdb->rec[ne][ns].fname,"%s/%s.%s.SAC\0", sdb->ev[ne].name, sdb->st[ns].name, buff[1]);
    sprintf(sdb->rec[ne][ns].ft_fname,"%s/ft_%s.%s.SAC\0", sdb->ev[ne].name, sdb->st[ns].name, buff[1]);

    sprintf(sdb->rec[ne][ns].chan,"%s\0", buff[1] );
  }
  sdb->cntev++;
  iniparser_free(d);
  return;
}


/*-------------------------------------------------------------------------
  read in station information into SAC_DB structure
  -------------------------------------------------------------------------*/
void  fill_one_sta (SAC_DB *st1, char **buff)
{
  strcpy(st1->st[st1->cntst].name,buff[0]);
  st1->st[st1->cntst].lon = atof(buff[1]);
  st1->st[st1->cntst].lat = atof(buff[2]);
  st1->cntst++;
  return;
}


/*-------------------------------------------------------------------------
  write date and path of seed-files into SAC_DB structure       
  -------------------------------------------------------------------------*/
void fill_one_event (SAC_DB *ev1, char **buff )
{
  ev1->ev[ev1->cntev].yy = atoi(buff[0]);
  ev1->ev[ev1->cntev].mm = atoi(buff[1]);
  ev1->ev[ev1->cntev].dd = atoi(buff[2]);
  ev1->ev[ev1->cntev].h = atoi(buff[3]);
  ev1->ev[ev1->cntev].m = atoi(buff[4]);
  ev1->ev[ev1->cntev].s = 0;
  ev1->ev[ev1->cntev].ms = 0;
  ev1->ev[ev1->cntev].ms = 10.*ev1->ev[ev1->cntev].ms;

  ev1->ev[ev1->cntev].jday = jday( ev1->ev[ev1->cntev].yy, ev1->ev[ev1->cntev].mm, ev1->ev[ev1->cntev].dd );

  ev1->ev[ev1->cntev].t0 = abs_time (ev1->ev[ev1->cntev].yy, ev1->ev[ev1->cntev].jday, ev1->ev[ev1->cntev].h, ev1->ev[ev1->cntev].m, ev1->ev[ev1->cntev].s, ev1->ev[ev1->cntev].ms );

  sprintf(ev1->ev[ev1->cntev].name,"%d_%d_%d_%d_%d_%d\0",ev1->ev[ev1->cntev].yy, ev1->ev[ev1->cntev].mm, ev1->ev[ev1->cntev].dd, ev1->ev[ev1->cntev].h, ev1->ev[ev1->cntev].m, ev1->ev[ev1->cntev].s );

  sprintf(str,"%s",ev1->ev[ev1->cntev].name);
  strcat(buff[6],"/");
  strcat(buff[6],str);
  sprintf(str,"mkdir %s\0", buff[6] );
  strncpy(ev1->ev[ev1->cntev].name,buff[6],149);
  
  ev1->cntev++;
  printf("Number of events read in is: %d\n",ev1->cntev);
  system(str);
  return;
}



/*========================================================================
  ======== call back functions required by sqlite routine ================*/


static int stat_callback(void *test, int argc, char **argv, char **azColName){
  int i;
  for(i=0; i<argc; i++){
    printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
  }
  fill_one_sta(test, argv);
  printf("\n");
  return 0;
}

static int seed_callback(void *test, int argc, char **argv, char **azColName){
  int i;
  for(i=0; i<argc; i++){
    printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
  }
  fill_one_event(test, argv);
  printf("\n");
  return 0;
}

static int call_mk_one_rec(void *test, int argc, char **argv, char **azColName){
  int i;
  for(i=0; i<argc; i++){
    printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
  }
  mk_one_rec(test, argv);
  //  printf("\n");
  return 0;
}

SAC_DB sdb;
char buff[300];

/*========================== MAIN =================================================*/
int main (int na, char **arg)
{
  sqlite *db;
  char *zErrMsg = 0;
  char *test;
  char *tmpdir;
  int ist, iev;
  FILE *ff;
  int rc;
  dictionary *dd;
  char *database;

  strncpy(sdb.conf,"./config.txt",149);
  get_args(na,arg,&sdb);

  /*opening config file*/
  dd = iniparser_new(sdb.conf);
  database = iniparser_getstr(dd, "database:databasefile");

  /* sql-query commands */
  /*  char command[] = "select station, lon, lat from stations where station='BFZ' or station='BKZ' or station='CRLZ'";*/
  char command[] = "select station, lon, lat from stations";
  char seedcmd[] = "select year,month,day,hour,minute,second,sacdir from seedfiles";
  char seedcmd2[] = "select path,channel from seedfiles";

  /* initialise SAC_DB structure */
  for ( iev = 0; iev < NEVENTS; iev++ ) for ( ist = 0; ist < NSTATION; ist++ ) sdb.rec[iev][ist].n = 0;

  fprintf(stderr,"initializing DB ok\n");

  db = sqlite_open(database, 0, &zErrMsg);
  if( db==0 ){
    fprintf(stderr, "Can't open database: %s\n", zErrMsg);
    return 1;
  }
  sdb.cntst = 0;
  sdb.cntev = 0;
  rc = sqlite_exec(db, command , stat_callback, &sdb, &zErrMsg);
  if( rc!=SQLITE_OK ){
    fprintf(stderr, "SQL error: %s\n", zErrMsg);
  }
  rc = sqlite_exec(db, seedcmd , seed_callback, &sdb, &zErrMsg);
  if( rc!=SQLITE_OK ){
    fprintf(stderr, "SQL error: %s\n", zErrMsg);
  }
  printf("number of events=%d and number of stations=%d\n",sdb.cntev,sdb.cntst);
  sdb.nst = sdb.cntst;
  sdb.nev = sdb.cntev;
  sdb.cntev = 0;
  rc = sqlite_exec(db, seedcmd2 , call_mk_one_rec, &sdb, &zErrMsg);
  if( rc!=SQLITE_OK ){
    fprintf(stderr, "SQL error: %s\n", zErrMsg);
  }
  sqlite_close(db);

  tmpdir = iniparser_getstr(dd, "database:tmpdir");
  sprintf(str,"%ssac_db.out\0", tmpdir);
  printf("name of sac database is: %s\n",str);
  ff = fopen(str,"wb");
  fwrite(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);
  sprintf(str,"%sevent_station.tbl\0", tmpdir);
  printf("name of sac ascii-table is: %s\n",str);
  sac_db_write_to_asc ( &sdb, str );
  iniparser_free(dd);
  return 0;
}
