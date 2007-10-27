/*--------------------------------------------------------------------------
  Program to divide stacks of cross-correlations into positive, negative and
  symmetric part

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

/* os-dependent includes for dir-manipulation */
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>


SAC_HD *read_sac_header(char *fname, SAC_HD *SHD)
{
 FILE *fsac;
/*..........................................................................*/
        if((fsac = fopen(fname, "rb")) == NULL) {
          printf("could not open sac file to write\n");
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

/*-----------------------------------------------------------
 *one_pair is the main routine to run the other subroutines.  
 ------------------------------------------------------------*/
int one_pair(char *name1, char *staname1, char *staname2, char *sacdir)
{
  float b, dist, dt, tmax, Umin = 1.;
  float Evla, Evlo, Stla, Stlo;
  char fname[300],Statname[9], Evname[9];
  char ch1;
  FILE *fp1;

  strncpy(fname, name1, 299);

  printf("fname is %s\n\n", fname);

  /*---------------- reading sac file  -------------------*/
  if ( read_sac_header (fname, &SAC_HEADER) == NULL )
    {
      fprintf(stderr,"file %s not found\n", fname);
      return 0;
    }

  b = SAC_HEADER.b;
  dt = SAC_HEADER.delta;
  dist = SAC_HEADER.dist;
  Evla = SAC_HEADER.evla;
  Evlo = SAC_HEADER.evlo;
  Stla = SAC_HEADER.stla;
  Stlo = SAC_HEADER.stlo;

  if((fp1 = fopen("change.csh", "w"))==NULL) {
    printf("cannot open change.csh.\n");
    exit(1);
  }
  sprintf(Statname, staname2);
  strcpy(SAC_HEADER.kstnm, Statname);

  printf("sta1 %s sta2 %s\n", staname1, staname2);
  printf("sta1len %d sta2len %d\n", strlen(staname1), strlen(staname2));

  fprintf(fp1,"%ssac << END >/dev/null\n",sacdir);
  fprintf(fp1, "r %s\n", fname);
  fprintf(fp1, "ch kevnm %s\n", staname1);
  fprintf(fp1, "ch kstnm %s\n", staname2);
  fprintf(fp1, "w %s\n", fname);
  fprintf(fp1, "cut 0 2900\n");
  fprintf(fp1, "r %s\n", fname);
  fprintf(fp1, "ch o 0\n");
  fprintf(fp1, "ch kevnm %s\n", staname1);
  fprintf(fp1, "w %s_p\n", fname);

  fprintf(fp1, "cut -2900 0\n");
  fprintf(fp1, "r %s\n", fname);
  fprintf(fp1, "reverse\n");
  fprintf(fp1, "ch b 0\n");
  fprintf(fp1, "ch e 2900\n");
  fprintf(fp1, "ch o 0\n");
  fprintf(fp1, "w %s_n\n", fname);

  fprintf(fp1, "cut off\n");
  fprintf(fp1, "addf %s_p\n", fname);
  fprintf(fp1, "ch o 0\n");
  fprintf(fp1, "div 2\nw %s_s\n", fname);
  fprintf(fp1, "END\n");

  fclose(fp1);
  system("csh change.csh");
  system("rm change.csh");

  return 1;
}


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, SAC_DB *sdb, char *altrootdir){

  int i;

  if (argc > 5){
    fprintf(stderr,"USAGE: %s [ -c path/to/alt/configfile -r alt/root/dir]\n", argv[0]);
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

      case 'r':	strncpy(altrootdir,argv[++i],199);
	break;

      case 'h': 
	printf("USAGE: %s [-c path/to/alt/configfile -r alt/root/dir]\n", argv[0]);
	printf("-------------------------------\n");
	printf("program to devide correlations\n");
	printf("in positiv, negativ and symmetric part\n");
	
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}


void chlag(char *rootdir,char *sacdir)
{
  DIR *dir;
  struct dirent *dirpointer;
  struct stat attribut;
  char tmp[200];
  char *ptr;
  char name[3][8];
  int m;

  /* open directory */
  if((dir=opendir(rootdir)) == NULL) {
    fprintf(stderr,"ERROR in opendir ...\n");
    return;
  }
  /* read directory and recursive call of this function to find 
     '*.SAC'-files*/
  while((dirpointer=readdir(dir)) != NULL){
    strncpy(tmp,rootdir,199);
    strcat(tmp,"/");
    strcat(tmp,(*dirpointer).d_name);
    if(stat(tmp, &attribut) == -1){
      fprintf(stderr,"ERROR in stat ...\n");
      return;
    }
    if(strstr((*dirpointer).d_name,".SAC") !=0 &&strstr((*dirpointer).d_name,"COR") !=0 
       && strstr((*dirpointer).d_name,".SAC_") ==0 && attribut.st_mode & S_IFREG ){
      printf("working on file %s\n",tmp);
      ptr = strrchr(dirpointer->d_name,'.');
      *ptr = '\0';
      ptr = NULL;
      ptr = strtok(dirpointer->d_name,"_");
      m=0;
      while(ptr != NULL){
	strncpy(name[m],ptr,7);
	ptr = strtok(NULL,"_");
	m++;
      }
      if ( !one_pair(tmp,name[1],name[2],sacdir) ) continue;
      
    }
  }
}


/*c/////////////////////////////////////////////////////////////*/
char fname[300], str[300];
SAC_DB sdb;
/*--------------------------------------------------------------*/
int main (int argc, char **argv)
/*--------------------------------------------------------------*/
{
  float stla, stlo, evla, evlo, dist;
  FILE *ff;
  int N, j, cnt;
  int ns1 = 0, ns2 = 4, n = 0, len = 0, i;
  char filename[29], fname[29], shortname[26];
  char staname1[8], staname2[8], dump[500], altrootdir[200];
  char ch, ch1;
  char *rootdir, *sacdir;
  dictionary *dd;

  strncpy(sdb.conf,"./config.txt",149);
  strncpy(altrootdir,"dummy",199);
  get_args(argc,argv,&sdb,altrootdir);

  dd = iniparser_new(sdb.conf);
  sacdir = iniparser_getstr(dd, "database:sacdir");
  if(strcmp(altrootdir,"dummy")==0){
    rootdir = iniparser_getstr(dd, "database:sacdirroot");
  }else{
    rootdir = &altrootdir[0];
  }
  strcat(rootdir,"STACK");

  chlag(rootdir,sacdir);
  iniparser_free(dd);

  return 0;
}
