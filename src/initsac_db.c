/*--------------------------------------------------------------------------
  program to initialise the file 'sac_db.out' which is used by subsequent 
  processing routines; it searches a dir-structure for matching files, 
  extracts the necessary information from the sac-header or the file name
  and writes them into the sac_db-structure
  $Rev$
  $Author$
  $LastChangedDate$
  ---------------------------------------------------------------------------*/

#define MAIN
#define _XOPEN_SOURCE 500
#include <ftw.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <iniparser.h>
#include <mysac.h>
#include <sac_db.h>
#include <glob.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <assert.h>
#include <libgen.h>

#define STRING 300
#define SSTRING 150
#define MODUS 0711

/* function prototypes */
struct sopts{
  int n1, n2, n3;
  char *search_str[50];
  char *skip_dirs[50];
  char *search_dirs[50];
  char *resp_dir;
  char *prefix;
  int flag;
} search_opts;

void extr_sac_hd(char *sacfile, const char *pathname);
int search_stat(char *statname);
void month_day(int year, int yearday, int *pmonth, int *pday);
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms );
void get_args(int argc, char** argv, char *filename);
void sort_sac_db(void);
void print_sac_db(void);
static int glob_this(const char *fpath, const struct stat *sb,
		     int tflag, struct FTW *ftwbuf);
int search_ev(double t);
int day_of_year(int year, int month, int day);

SAC_DB sdb;

int main (int argc, char **argv){

  FILE *ff;
  int N, i;
  int flags = 16;
  char filename[STRING];
  char delimiters[] = " ,;";
  char *search_dirs, *skip_dirs, *search_str, *tmpdir, *buf, *ptr;
  char *sacdbname;
  dictionary *dd;

  strncpy(sdb.conf,"./config.txt",149);
  strncpy(filename,"./dummy.out",STRING-1);
  get_args(argc,argv,filename);

  /*opening config file*/
  dd = iniparser_new(sdb.conf);
  search_dirs          = iniparser_getstr(dd, "init_sacdb:search_directories");
  skip_dirs            = iniparser_getstr(dd, "init_sacdb:skip_directories");
  search_str           = iniparser_getstr(dd, "init_sacdb:search_string");
  search_opts.resp_dir = iniparser_getstr(dd, "init_sacdb:resp_dir");
  search_opts.flag     = iniparser_getint(dd, "init_sacdb:flag", 0);
  search_opts.prefix   = iniparser_getstr(dd, "init_sacdb:prefix");
  sacdbname            = iniparser_getstr(dd, "init_sacdb:dbname");
  buf = strdup(search_dirs);
  ptr  = strtok(buf, delimiters);
  i = 0;
  while(ptr != NULL && i < 50){
    search_opts.search_dirs[i] = strdup(ptr);
    ptr = strtok(NULL,delimiters);
    i++;
  }
  search_opts.n1 = i;
  free(buf);

  buf = strdup(skip_dirs);
  ptr  = strtok(buf, delimiters);
  i = 0;
  while(ptr != NULL && i < 50){
    search_opts.skip_dirs[i] = strdup(ptr);
    ptr = strtok(NULL,delimiters);
    i++;
  }
  search_opts.n2 = i;
  free(buf);

  buf = strdup(search_str);
  ptr  = strtok(buf, delimiters);
  i = 0;
  while(ptr != NULL && i < 50){
    search_opts.search_str[i] = strdup(ptr);
    ptr = strtok(NULL,delimiters);
    i++;
  }
  search_opts.n3 = i;
  free(buf);

  if(!strcmp(filename,"./dummy.out")){
    tmpdir = iniparser_getstr(dd, "init_sacdb:tmpdir");
    assert((strlen(tmpdir)+10)<STRING);
    strncpy(filename,tmpdir,STRING-1);
    if(mkdir(tmpdir, MODUS) == -1)
      fprintf(stdout,"directory %s already exists \n", tmpdir); 
    assert(strlen(filename)+strlen(sacdbname)+1 <STRING);
    strcat(filename,sacdbname);
  }

  /* setting initial values */
  sdb.nev = 0;
  sdb.nst = 0;
  N=sizeof(sdb.st)/sizeof(struct station);
  for(i=0;i<N;i++){
    strncpy(sdb.st[i].name,"init",9);
  }

  /* searching for SAC-files */
  for(i=0;i<search_opts.n1;i++){
    if (nftw(search_opts.search_dirs[i], glob_this, 20, flags) == -1) {
      perror("nftw");
      exit(EXIT_FAILURE);
    }
  }
  sdb.cntev = sdb.nev;
  sdb.cntst = sdb.nst;

  /* sorting SAC-files according to their date */
  sort_sac_db();

#ifdef DEBUG
  print_sac_db();
#endif

  /* writing sac_db structure to file */
  ff = fopen(filename,"wb");
  fwrite(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  iniparser_free(dd);
  return EXIT_SUCCESS;
}


/*------------------------------------------------------------ 
 *  call-back function for nftw()
  ------------------------------------------------------------*/
static int glob_this(const char *fpath, const struct stat *sb,
		     int tflag, struct FTW *ftwbuf){
  //  const char pattern[] = "*BHZ.SAC";
  char localpattern[STRING];
  glob_t match;
  int i, j;

  for(i=0;i<search_opts.n2;i++){
    if(strstr(fpath,search_opts.skip_dirs[i]) != NULL){
      return 0;
    }
  }

  for(i=0;i<search_opts.n3;i++){
    assert((strlen(fpath)+strlen(search_opts.search_str[i]))<STRING-1);
    sprintf(localpattern,"%s/%s",fpath, search_opts.search_str[i]);
    //    printf("%s\n", localpattern);

    if(glob(localpattern, 0, NULL, &match) == 0){
      for(j=0;j<match.gl_pathc;j++){
	//      printf("%s\n",match.gl_pathv[j]);
	extr_sac_hd(match.gl_pathv[j],fpath);
      }
    }
    globfree(&match);
  }
  return 0;
}



/*------------------------------------------------------------ 
 *  function to read sac-header information and write them 
 *  into the corresponding fields of the SAC_DB structure
 *
 *  sacfile = name of sac file
 *  pathname = dirname of sac file 
  ------------------------------------------------------------*/
void extr_sac_hd(char *sacfile, const char *pathname){
  FILE *f;
  int index, ns, ne;
  double t0;
  int year, month, day, yday;
  SAC_HD shd;
  char *ptr;
  char buffer[STRING];
  char respattern[STRING];
  glob_t match;
  struct stat fst;

  //  printf("%s\n",sacfile);
  f = fopen(sacfile,"rb");
  fread(&shd, sizeof(SAC_HD),1,f);
  fclose(f);

  /* shd.kstnm and shd.kcmpnm don't have a proper string ending */
  ptr = strtok(shd.kstnm," ");
  strncpy(shd.kstnm,ptr,7);
  ptr = strtok(shd.kcmpnm," ");
  strncpy(shd.kcmpnm,ptr,7);

    
  index = search_stat(shd.kstnm);
  if(index == -1){
    ns = sdb.nst;
    sdb.st[sdb.nst].lat = shd.stla;
    sdb.st[sdb.nst].lon = shd.stlo;
    strncpy(sdb.st[sdb.nst++].name,shd.kstnm,9);
  }else{
   ns = index;
  }

  /* extract date of day from directory name; this has to be done as the seismogram itself might 
     start a day earlier at for example 23:59:48 */
  assert(strlen(sacfile) < STRING-1);
  strncpy(buffer, sacfile, STRING-1);
  ptr = dirname(buffer);
  ptr = basename(ptr);
  year  = atoi(strtok(ptr, "_"));
  month = atoi(strtok(NULL,"_"));
  day   = atoi(strtok(NULL,"_"));
  yday  = day_of_year(year, month, day);
  t0 = abs_time ( year,yday,0,0,0,0 );
  strncpy(buffer, sacfile, STRING-1);
  index = search_ev(t0);
  if(index == -1){
    ne = sdb.nev;
    ptr = dirname(buffer);
    assert(strlen(ptr) < SSTRING -1);
    strncpy(sdb.ev[sdb.nev++].name, ptr, SSTRING-1);
  }else{
    ne = index;
    ptr = dirname(buffer);
    assert(strlen(ptr) < SSTRING -1);
    strncpy(sdb.ev[ne].name, ptr, SSTRING-1);
  }

  strncpy(sdb.rec[ne][ns].fname,sacfile,SSTRING-1);
  printf("%s\n", sdb.rec[ne][ns].fname);
  sprintf(sdb.rec[ne][ns].ft_fname,"%s/%s_%s.%s.SAC",pathname,search_opts.prefix,shd.kstnm, shd.kcmpnm);
  strncpy(sdb.rec[ne][ns].chan,shd.kcmpnm,6);
  sdb.ev[ne].yy = year;
  sdb.ev[ne].jday = yday;
  month_day(year, yday, &sdb.ev[ne].mm, &sdb.ev[ne].dd);
  sdb.ev[ne].h = 0;
  sdb.ev[ne].m = 0;
  sdb.ev[ne].s = 0;
  sdb.ev[ne].ms = 0;
  sdb.ev[ne].ms = 10.*sdb.ev[ne].ms;
  sdb.ev[ne].t0 = t0;
  sdb.rec[ne][ns].dt = shd.delta;
  sdb.rec[ne][ns].n  = shd.npts;
  sdb.rec[ne][ns].t0 = abs_time(shd.nzyear,shd.nzjday,shd.nzhour,shd.nzmin,shd.nzsec,shd.nzmsec );

  /* find corresponding response file */
  
  if(stat(search_opts.resp_dir,&fst) && S_ISDIR(fst.st_mode)){
    assert((strlen(search_opts.resp_dir)+strlen(shd.kstnm)+strlen(shd.kcmpnm)+7)<STRING-1);
    sprintf(respattern,"%s/RESP*%s*%s",search_opts.resp_dir, shd.kstnm, shd.kcmpnm);
  }else{
    assert((strlen(pathname)+strlen(shd.kstnm)+strlen(shd.kcmpnm)+7)<STRING-1);
    sprintf(respattern,"%s/RESP*%s*%s",pathname, shd.kstnm, shd.kcmpnm);
  }

  if(glob(respattern, 0, NULL, &match) == 0){
    if(match.gl_pathc>1){
      fprintf(stderr,"WARNING: more than 1 response file available for %s\n",sacfile);
      fprintf(stderr,"  --->  taking the first one\n");
      strncpy(sdb.rec[ne][ns].resp_fname,match.gl_pathv[0],SSTRING-1);
    }else if((match.gl_pathc - 1)< 0.0001) {
      //      printf("%s\n",match.gl_pathv[0]);
      strncpy(sdb.rec[ne][ns].resp_fname,match.gl_pathv[0],SSTRING-1);
    }else{
      fprintf(stderr,"ERROR: no response file found for %s\n",sacfile);
    }
  }
  globfree(&match);

  /* find corresponding pole-zero file */
  if((stat(search_opts.resp_dir,&fst)!=-1) && S_ISDIR(fst.st_mode)){
    assert((strlen(search_opts.resp_dir)+strlen(shd.kstnm)+strlen(shd.kcmpnm)+7)<STRING-1);
    sprintf(respattern,"%s/SAC_PZs*%s*%s*",search_opts.resp_dir, shd.kstnm, shd.kcmpnm);
  }else{
    /*printf("%d\n",stat(search_opts.resp_dir,&fst));*/
    assert((strlen(pathname)+strlen(shd.kstnm)+strlen(shd.kcmpnm)+7)<STRING-1);
    sprintf(respattern,"%s/SAC_PZs*%s*%s*",pathname, shd.kstnm, shd.kcmpnm);
  }

  if(glob(respattern, 0, NULL, &match) == 0){
    if(match.gl_pathc>1){
      fprintf(stderr,"WARNING: more than 1 pole-zero file available for %s\n",sacfile);
      fprintf(stderr,"  --->  taking the first one\n");
      strncpy(sdb.rec[ne][ns].pz_fname,match.gl_pathv[0],SSTRING-1);
    }else if((match.gl_pathc - 1)< 0.0001){
      //      printf("%s\n",match.gl_pathv[0]);
      strncpy(sdb.rec[ne][ns].pz_fname,match.gl_pathv[0],SSTRING-1);
    }else{
      fprintf(stderr,"ERROR: no pole-zero file found for %s\n",sacfile);
    }

  }
  globfree(&match);

  /* find ft_* files if flag is set to '1'*/
  if(search_opts.flag == 1){
    assert((strlen(pathname)+strlen(shd.kstnm)+strlen(shd.kcmpnm)+strlen(search_opts.prefix)+5)<STRING-1);
    sprintf(respattern,"%s/%s_*%s*%s.SAC",pathname, search_opts.prefix, shd.kstnm, shd.kcmpnm);

    if(glob(respattern, 0, NULL, &match) == 0){
      if(match.gl_pathc>1){
	fprintf(stderr,"WARNING: more than ft file available for %s\n",sacfile);
	fprintf(stderr,"  --->  taking the first one\n");
	printf("%s\n", match.gl_pathv[0]);
	f = fopen(match.gl_pathv[0],"rb");
	fread(&shd, sizeof(SAC_HD),1,f);
	fclose(f);
	sdb.rec[ne][ns].n  = shd.npts;
	sdb.rec[ne][ns].dt = (double)shd.delta;
      }else if((match.gl_pathc - 1)< 0.0001){
	printf("%s\n", match.gl_pathv[0]);
	f = fopen(match.gl_pathv[0],"rb");
	fread(&shd, sizeof(SAC_HD),1,f);
	fclose(f);
	sdb.rec[ne][ns].n  = shd.npts;
	sdb.rec[ne][ns].dt = (double)shd.delta;
      }else{
	fprintf(stderr,"ERROR: no ft-file found for %s\n",sacfile);
	sdb.rec[ne][ns].n  = 0;
      }

    }else{
	fprintf(stderr,"ERROR: no ft-file found for %s\n",sacfile);
	sdb.rec[ne][ns].n  = 0;
    }
    globfree(&match);
  }
}


/*------------------------------------------------
 *function to check if entry for station name 
 *already exists; if not, writes station name 
 *into SAC_DB structure; returns index of station
 *name
 *
 *statname = name of station
 *sdb      = SAC_DB structure
 --------------------------------------------------*/
int search_stat(char *statname){

  int i,N,cnt=-1;

  N=sizeof(sdb.st)/sizeof(struct station);
  for(i=0;i<N;i++){
    if(strstr(sdb.st[i].name,statname)!=0){
      cnt=i;
      break;
    }
  }
  return cnt;
}


/*------------------------------------------------
 *function to check if entry for event name 
 *already exists; if not, count up number of events
 --------------------------------------------------*/
int search_ev(double t){

  int i,N,cnt=-1;

  N=sizeof(sdb.ev)/sizeof(struct event);
  for(i=0;i<N;i++){
    if(fabs((sdb.ev[i].t0 - t)) < 0.0001){
      cnt=i;
      break;
    }
  }
  return cnt;
}


/*-----------------------------------------------------
 *sort sdb-entries according to the date
 -----------------------------------------------------*/
void sort_sac_db(void){

  int i,j,value,index;  
  static SAC_DB buff;

  for(i=0;i<sdb.nev;i++){
    value=i;
    for(index=i+1;index<=sdb.nev;index++){
      for(j=0;j<sdb.nst;j++){
	if(sdb.rec[index][j].t0<sdb.rec[value][j].t0 && sdb.rec[index][j].t0 !=0){
	  value=index;
	}
      }
    }
    if(value != i){
      for(j=0;j<sdb.nst;j++){
	buff.rec[1][j]=sdb.rec[value][j];
	sdb.rec[value][j]=sdb.rec[i][j];
	sdb.rec[i][j]=buff.rec[1][j];
      }
      buff.ev[1]=sdb.ev[value];
      sdb.ev[value]=sdb.ev[i];
      sdb.ev[i]=buff.ev[1];
    }
  }
}


/*-----------------------------------------------------
 *debug-function to print entries of SAC_DB structure 
 *to stdout
 -----------------------------------------------------*/
void print_sac_db(void){

  int i,j;  

  for(i=0;i<sdb.nst;i++){
    printf("station number %d is %s\n",i,sdb.st[i].name);
  }
  for(i=0;i<sdb.nev;i++){
    for(j=0;j<sdb.nst;j++){
      printf("event number: %d   station number: %d\n", i,j);
      printf("--> station name       :%s\n", sdb.st[j].name);
      printf("--> station latitude   :%f\n", sdb.st[j].lat);
      printf("--> station longitude  :%f\n", sdb.st[j].lon);
      printf("--> eventname          :%s\n", sdb.ev[i].name);
      printf("--> channel name       :%s\n", sdb.rec[i][j].chan);
      printf("--> sample interval    :%f\n", sdb.rec[i][j].dt);
      printf("--> julian day         :%d\n", sdb.ev[i].jday);
      printf("--> month              :%d\n", sdb.ev[i].mm);
      printf("--> month day          :%d\n", sdb.ev[i].dd);
      printf("--> hour               :%d\n", sdb.ev[i].h);
      printf("--> minute             :%d\n", sdb.ev[i].m);
      printf("--> second             :%d\n", sdb.ev[i].s);
      printf("--> millisecond        :%d\n", sdb.ev[i].ms);
      printf("--> absolute time      :%f\n", sdb.rec[i][j].t0);
      printf("--> number of points   :%ld\n", sdb.rec[i][j].n);
      printf("--> record name        :%s\n", sdb.rec[i][j].fname);
      printf("--> record ft-name     :%s\n", sdb.rec[i][j].ft_fname);
      printf("--> response filename  :%s\n", sdb.rec[i][j].resp_fname);
      printf("--> pole-zero filename :%s\n", sdb.rec[i][j].pz_fname);
    }
  }

}


/*---------------------------------------------------------
 * function to convert yearday into monthday
 ---------------------------------------------------------*/
void month_day(int year, int yearday, int *pmonth, int *pday){

  static char daytab[2][13] =  {
    {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31},
    {0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31},
  };

  int i, leap;
  
  leap = (year%4 == 0 && year%100 != 0) || year%400 == 0;
  for (i = 1; yearday > daytab[leap][i]; i++)
    yearday -= daytab[leap][i];
  *pmonth = i;
  *pday = yearday;
}


/*----------------------------------------------------------
 * function to convert calendar date into yearday
 ---------------------------------------------------------*/
int day_of_year(int year, int month, int day)
{
  static char daytab[2][13] =  {
    {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31},
    {0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31},
  };

  int i, leap;
  
  leap = (year%4 == 0 && year%100 != 0) || year%400 == 0;
  for (i = 1; i < month; i++)
    day += daytab[leap][i];
  return day;
}


/*--------------------------------------------------------------------------
 *computes time in s relative to 1900
  --------------------------------------------------------------------------*/
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms ){

  long nyday = 0, i;

  for ( i = 1901; i < yy; i++ )
    {
      if ( 4*(i/4) == i ) nyday += 366;
      else nyday += 365;
    }
  /* as 'jday' discribes the actual date and not the number of whole days that
   have passed since the beginning of the year, we have to decrement it by one;
  luckily that doesn't have an effect on our files, as we were only looking at 
  differences in time*/
  return 24.*3600.*(nyday+jday-1) + 3600.*hh + 60.*mm + ss + 0.001*ms;
}


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char *filename){

  int i;

  if (argc > 3){
    fprintf(stderr,"USAGE: %s [-o output file -c path/to/alt/configfile]\n", argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strncpy(sdb.conf,argv[++i],149);
	break;

      case 'o':	strncpy(filename,argv[++i],STRING-1);
	break;

      case 'h': 
	printf("USAGE: %s [-o output file -c path/to/alt/configfile]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}
