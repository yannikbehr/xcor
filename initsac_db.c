/* program to initialise the file 'sac_db.out' which is used by subsequent 
   processing routines; it searches a dir-structure for matching files, 
   extracts the necessary information from the sac-header and writes them 
   into the sac_db-structure*/


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


#define STRING 200

void extr_sac_hd(char *sacfile, SAC_DB *sdb, char *newname);
int walk_dir(char *dirname, SAC_DB *sdb);
int search_stat(char *statname, SAC_DB *sdb);
void month_day(int year, int yearday, int *pmonth, int *pday);
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms );
void get_args(int argc, char** argv, SAC_DB *sdb, char *filename);
void read_resp(char *resppath, SAC_DB *sdb, char *newname, char *respfile);
void count_ev(char *newname, char *tmp, char *oldname, SAC_DB *sdb);
void print_sac_db(SAC_DB *sdb);


/*------------------------------------------------------------------------
  function to find all 'COR'-directories and move preliminary correlations
  to final correlations
  needs following headers: sys/types.h, sys/stat.h, dirent.h, string.h, 
  stdio.h, stdlib.h
  ------------------------------------------------------------------------*/
int walk_dir(char *dirname, SAC_DB *sdb){

  DIR *dir, *dir2;
  struct dirent *dirpointer, *dirpointer2;
  struct stat attribut;
  char tmp[STRING],oldname[STRING],newname[STRING];
  char *cutptr;

  strncpy(oldname,"dummy",STRING-1);

  /* open directory */
  if((dir=opendir(dirname)) == NULL) {
    fprintf(stderr,"ERROR in opendir ...\n");
    return EXIT_FAILURE;
  }
  /* read directory and recursive call of this function to find 
     '*.SAC'-files*/
  while((dirpointer=readdir(dir)) != NULL){
    strncpy(tmp,dirname,STRING-1);
    strcat(tmp,(*dirpointer).d_name);
    if(stat(tmp, &attribut) == -1){
      fprintf(stderr,"ERROR in stat ...\n");
      return EXIT_FAILURE;
    }

    /* if filename has ending '.SAC' and is a regular file but does neither 
       contain the string 'COR' nor 'stack' than go on*/
    if(strstr((*dirpointer).d_name,".SAC") !=0 &&strstr((*dirpointer).d_name,"ft_") ==0 
       &&strstr((*dirpointer).d_name,"COR") ==0 
       &&strstr((*dirpointer).d_name,"stack") ==0 
       && attribut.st_mode & S_IFREG){
      count_ev(newname, tmp, oldname, sdb);
      extr_sac_hd(tmp,sdb,newname);

    }
    /* if filename has contains 'RESP' string and is regular file */
    else if(strstr((*dirpointer).d_name,"RESP") !=0 && attribut.st_mode & S_IFREG){
      count_ev(newname, tmp, oldname, sdb);
      read_resp(tmp,sdb,newname,dirpointer->d_name);

    }
    /* else if dir-entry is directory function calls itself again */
    else if(attribut.st_mode & S_IFDIR && strcmp((*dirpointer).d_name,".") != 0 && strcmp((*dirpointer).d_name,"..") != 0){
      strcat(tmp,"/");
      walk_dir(tmp,sdb);
    }

  }
  /* close directory */
  if(closedir(dir) == -1){
    fprintf(stderr,"ERROR while closing %s\n", dirname);
    return EXIT_SUCCESS;
  }
}


void extr_sac_hd(char *sacfile, SAC_DB *sdb, char *newname){
  FILE *f;
  int i, index, ns;
  SAC_HD shd;
  char dummy[8];
  char *ptr;

  f = fopen(sacfile,"rb");
  fread(&shd, sizeof(SAC_HD),1,f);
  fclose(f);

  /* shd.kstnm and shd.kcmpnm don't have a proper string ending */
  ptr = strtok(shd.kstnm," ");
  strncpy(shd.kstnm,ptr,7);
  ptr = strtok(shd.kcmpnm," ");
  strncpy(shd.kcmpnm,ptr,7);

  index = search_stat(shd.kstnm,sdb);
  if(index == -1){
    ns = sdb->nst;
    strncpy(sdb->st[sdb->nst++].name,shd.kstnm,9);
  }else{
   ns = index;
  }

  strncpy(sdb->rec[sdb->cntev][ns].fname,sacfile,149);
  sprintf(sdb->rec[sdb->cntev][ns].ft_fname,"%s/ft_%s.%s.SAC\0", newname, shd.kstnm, shd.kcmpnm);
  strncpy(sdb->rec[sdb->cntev][ns].chan,shd.kcmpnm,6);
  sdb->ev[sdb->cntev].yy = shd.nzyear;
  sdb->ev[sdb->cntev].jday = shd.nzjday;
  month_day(shd.nzyear, shd.nzjday, &sdb->ev[sdb->cntev].mm, &sdb->ev[sdb->cntev].dd);
  sdb->ev[sdb->cntev].h = shd.nzhour;
  sdb->ev[sdb->cntev].m = shd.nzmin;
  sdb->ev[sdb->cntev].s = 0;
  sdb->ev[sdb->cntev].ms = 0;
  sdb->ev[sdb->cntev].ms = 10.*sdb->ev[sdb->cntev].ms;
  sdb->rec[sdb->cntev][ns].dt = (double)shd.delta;
  sdb->rec[sdb->cntev][ns].n  = shd.npts;
  sdb->rec[sdb->cntev][ns].t0 = abs_time ( shd.nzyear,shd.nzjday,shd.nzhour,shd.nzmin,shd.nzsec,shd.nzmsec );
 
}

void read_resp(char *resppath, SAC_DB *sdb, char *newname, char *respfile){

  int  i, ns, index, m=0;
  char *ptr;
  char name[6][8];

  ptr = strtok(respfile, ".");
  while(ptr != NULL) {
    strncpy(name[m],ptr,7);
    ptr = strtok(NULL, ".");
    m++;
  }

  index = search_stat(name[2],sdb);
  if(index == -1){
    ns = sdb->nst;
    strncpy(sdb->st[sdb->nst++].name,name[2],9);
  }else{
   ns = index;
  }

  strncpy(sdb->rec[sdb->cntev][ns].resp_fname,resppath,149);

}


void count_ev(char *newname, char *tmp, char *oldname, SAC_DB *sdb){

  char *cutptr;
  strncpy(newname,tmp,STRING-1);
  cutptr = strrchr(newname,'/');
  *cutptr = '\0';
  if (strcmp(oldname,newname) != 0){
    sdb->cntev++;
    strncpy(oldname,newname,STRING-1);
    strncpy(sdb->ev[sdb->cntev].name,newname,150);
  }
}


int search_stat(char *statname, SAC_DB *sdb){

  int i,N,cnt=-1;

  N=sizeof(sdb->st)/sizeof(struct station);
  for(i=0;i<N;i++){
    if(strstr(sdb->st[i].name,statname)!=0){
      cnt=i;
      break;
    }
  }
  return cnt;
}


void print_sac_db(SAC_DB *sdb){

  int i,j;  

  for(i=0;i<sdb->nst;i++){
    printf("station number %d is %s\n",i,sdb->st[i].name);
  }
  for(i=0;i<=sdb->cntev;i++){
    for(j=0;j<sdb->nst;j++){
      printf("event number: %d   station number: %d\n", i,j);
      printf("--> station name       :%s\n", sdb->st[j].name);
      printf("--> eventname          :%s\n", sdb->ev[i].name);
      printf("--> channel name       :%s\n", sdb->rec[i][j].chan);
      printf("--> sample interval    :%f\n", sdb->rec[i][j].dt);
      printf("--> julian day         :%d\n", sdb->ev[i].jday);
      printf("--> month              :%d\n", sdb->ev[i].mm);
      printf("--> month day          :%d\n", sdb->ev[i].dd);
      printf("--> hour               :%d\n", sdb->ev[i].h);
      printf("--> minute             :%d\n", sdb->ev[i].m);
      printf("--> second             :%d\n", sdb->ev[i].s);
      printf("--> millisecond        :%d\n", sdb->ev[i].ms);
      printf("--> absolute time      :%f\n", sdb->rec[i][j].t0);
      printf("--> number of points   :%d\n", sdb->rec[i][j].n);
      printf("--> record name        :%s\n", sdb->rec[i][j].fname);
      printf("--> record ft-name     :%s\n", sdb->rec[i][j].ft_fname);
      printf("--> response filename  :%s\n", sdb->rec[i][j].resp_fname);
    }
  }

}

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


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, SAC_DB *sdb, char *filename){

  int i;

  if (argc > 5){
    fprintf(stderr,"USAGE: %s [-o output file -c path/to/alt/configfile]\n", argv[0]);
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

      case 'o':	strncpy(filename,argv[++i],STRING-1);
	break;

      case 'h': 
	printf("USAGE: %s [-o output file -c path/to/alt/configfile]\n", argv[0]);
	printf("-------------------------------\n");
	printf("program to initialize sac_db.out\n");
	printf("file by scanning directory structure\n");
	printf("under path/to/directory/ for existing\n");
	printf("*.SAC files and writing their header\n");
	printf("properties into the sac_db structure.\n");
	
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}


int main (int argc, char **argv){

  FILE *ff;
  int N, i, j;
  char filename[STRING];
  char *dirname;
  static SAC_DB sdb;
  dictionary *dd;

  strncpy(sdb.conf,"./config.txt",149);
  strncpy(filename,"./sac_db.out",STRING-1);
  get_args(argc,argv,&sdb,filename);

  /*opening config file*/
  dd = iniparser_new(sdb.conf);
  dirname = iniparser_getstr(dd, "database:sacdirroot");


  sdb.nev = 0;
  sdb.nst = 0;
  sdb.cntev = -1;
  sdb.cntst = -1;
  N=sizeof(sdb.st)/sizeof(struct station);
  for(i=0;i<N;i++){
    strncpy(sdb.st[i].name,"init",9);
  }


  walk_dir(dirname, &sdb);
  sdb.nev = sdb.cntev+1;
#ifdef DEBUG
  print_sac_db(&sdb);
#endif

  ff = fopen(filename,"wb");
  fwrite(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  iniparser_free(dd);
  return EXIT_SUCCESS;
}