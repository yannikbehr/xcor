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


void extr_sac_hd(char *sacfile, SAC_DB *sdb, char *newname);
int walk_dir(char *dirname, SAC_DB *sdb);
int search_stat(char *statname, SAC_DB *sdb);
void month_day(int year, int yearday, int *pmonth, int *pday);

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
  char tmp[200],oldname[200],newname[200];
  char *cutptr;

  strncpy(oldname,"dummy",199);

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

    /* if file name has ending '.SAC' and is a regular file but does neither 
       contain the string 'COR' nor 'stack' than go on*/
    if(strstr((*dirpointer).d_name,".SAC") !=0 &&strstr((*dirpointer).d_name,"ft_") ==0 
       &&strstr((*dirpointer).d_name,"COR") ==0 
       &&strstr((*dirpointer).d_name,"stack") ==0 
       && attribut.st_mode & S_IFREG){
      printf("found sac-file: %s\n",tmp);
      strncpy(newname,tmp,199);
      cutptr = strrchr(newname,'/');
      *cutptr = '\0';
      if (strcmp(oldname,newname) != 0){
	sdb->cntev++;
	sdb->cntst = 0;
	strncpy(oldname,newname,199);
	printf("next event is %s and new eventnumber is %d\n",oldname,sdb->cntev);
      }

      extr_sac_hd(tmp,sdb,newname);
    }
    /* else if dir-entry is directory function calls itself again */
    else if(attribut.st_mode & S_IFDIR && strcmp((*dirpointer).d_name,".") != 0 && strcmp((*dirpointer).d_name,"..") != 0){
      strcat(tmp,"/");
      walk_dir(tmp,sdb);
    }

  }
  /* close directory */
  if(closedir(dir) == -1){
    printf("ERROR while closing %s\n", dirname);
    return EXIT_SUCCESS;
  }
}


void extr_sac_hd(char *sacfile, SAC_DB *sdb, char *newname){
  FILE *f;
  int i, index, ns;
  SAC_HD shd;

  f = fopen(sacfile,"rb");
  fread(&shd, sizeof(SAC_HD),1,f);
  fclose(f);

  shd.kstnm[8]='\0';
  shd.kcmpnm[8]='\0';

  index = search_stat(shd.kstnm,sdb);
  if(index == -1){
    ns = sdb->nst;
    sdb->st[sdb->nst].lat = shd.stla;
    sdb->st[sdb->nst].lon = shd.stlo;
    strncpy(sdb->st[sdb->nst++].name,shd.kstnm,9);
  }else{
   ns = index;
  }

  sprintf(sdb->rec[sdb->cntev][ns].fname,"%s/%s.%s.SAC\0", newname, shd.kstnm, shd.kcmpnm);
  sprintf(sdb->rec[sdb->cntev][ns].ft_fname,"%s/ft_%s.%s.SAC\0", newname, shd.kstnm, shd.kcmpnm);
  sdb->ev[sdb->cntev].yy = shd.nzyear;
  month_day(shd.nzyear, shd.nzjday, &sdb->ev[sdb->cntev].mm, &sdb->ev[sdb->cntev].dd);
  /*    sdb->ev[sdb->cntev].h = atoi(buff[3]);
      sdb->ev[sdb->cntev].m = atoi(buff[4]);
      sdb->ev[sdb->cntev].s = 0;
      sdb->ev[sdb->cntev].ms = 0;
      sdb->ev[sdb->cntev].ms = 10.*sdb->ev[sdb->cntev].ms;*/

  printf("--> event number       :%d\n", sdb->cntev);
  printf("--> station name       :%s\n", shd.kstnm);
  printf("--> station number     :%d\n", ns);
  printf("--> station lat        :%f\n", shd.stla);
  printf("--> station lon        :%d\n", shd.stlo);
  printf("--> channel name       :%s\n", shd.kcmpnm);
  printf("--> number of points   :%d\n", shd.npts);
  printf("--> year               :%d\n", shd.nzyear);
  printf("--> julian day         :%d\n", shd.nzjday);
  printf("--> month              :%d\n", sdb->ev[sdb->cntev].mm);
  printf("--> month day          :%d\n", sdb->ev[sdb->cntev].dd);
  printf("--> hour               :%d\n", shd.nzhour);
  printf("--> minute             :%d\n", shd.nzmin);
  printf("--> second             :%d\n", shd.nzsec);
  printf("--> millisecond        :%d\n", shd.nzmsec);
  printf("--> sample interval    :%g\n", shd.delta);
}


int search_stat(char *statname, SAC_DB *sdb){

  int i,N,cnt=-1;

  N=sizeof(sdb->st)/sizeof(struct station);
  for(i=0;i<N;i++){
    if(strcmp(sdb->st[i].name,statname)==0){
      printf("station %s exists already.\n",statname);
      cnt=i;
      break;
    }
  }
  return cnt;
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


int main (int argc, char **argv){

  int N, i;
  static SAC_DB sdb;

  sdb.nev = 0;
  sdb.nst = 0;
  sdb.cntev = -1;
  sdb.cntst = -1;
  N=sizeof(sdb.st)/sizeof(struct station);
  for(i=0;i<N;i++){
    strncpy(sdb.st[i].name,"init",9);
  }

  walk_dir(argv[1], &sdb);

  for(i=0;i<sdb.nst;i++){
    printf("station number %d is %s\n",i,sdb.st[i].name);
  }


  return EXIT_SUCCESS;
}
