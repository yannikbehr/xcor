/*
 * The sample of test driver for FTAN with phase match filter (aftan4i)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <iniparser.h>
#include "aftan.h"

/* os-dependent includes for dir-manipulation */
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>


#define STRING 200

void get_args(int argc, char **argv, char *configfile);
void get_filelist(char *dirname, char **filelist, int cnt);
void count_files(char *dirname, int *cnt);


/*------------------------------------------------------------------------
  function to find all 'COR'-directories and move preliminary correlations
  to final correlations
  needs following headers: sys/types.h, sys/stat.h, dirent.h, string.h, 
  stdio.h, stdlib.h
  ------------------------------------------------------------------------*/
void count_files(char *dirname, int *cnt)
{
  DIR *dir;
  struct dirent *dirpointer;
  struct stat attribut;
  char tmp[STRING];

  /* open directory */
  if((dir=opendir(dirname)) == NULL) {
    fprintf(stderr,"ERROR in opendir ...\n");
    return;
  }
  /* read directory and recursive call of this function to find 
     '*.SAC'-files*/
  while((dirpointer=readdir(dir)) != NULL){
    strncpy(tmp,dirname,STRING-1);
    strcat(tmp,(*dirpointer).d_name);
    if(stat(tmp, &attribut) == -1){
      fprintf(stderr,"ERROR in stat ...\n");
      return;
    }

    /* if filename has ending '.SAC' and is a regular file but does neither 
       contain the string 'COR' nor 'stack' than go on*/
    if(strstr((*dirpointer).d_name,"_s") !=0 && attribut.st_mode & S_IFREG){
      (*cnt)++;
    }
  }
  /* close directory */
  if(closedir(dir) == -1){
    fprintf(stderr,"ERROR while closing %s\n", dirname);
    return;
  }
}


void get_filelist(char *dirname, char **filelist, int cnt)
{
  DIR *dir;
  struct dirent *dirpointer;
  struct stat attribut;
  char tmp[STRING];
  int i=0;

  /* open directory */
  if((dir=opendir(dirname)) == NULL) {
    fprintf(stderr,"ERROR in opendir ...\n");
    return;
  }
  /* read directory and recursive call of this function to find 
     '*.SAC'-files*/
  while((dirpointer=readdir(dir)) != NULL){
    strncpy(tmp,dirname,STRING-1);
    strcat(tmp,(*dirpointer).d_name);
    if(stat(tmp, &attribut) == -1){
      fprintf(stderr,"ERROR in stat ...\n");
      return;
    }

    /* if filename has ending '.SAC' and is a regular file but does neither 
       contain the string 'COR' nor 'stack' than go on*/
    if(strstr((*dirpointer).d_name,"_s") !=0 && attribut.st_mode & S_IFREG){
      strncpy(filelist[i],tmp,STRING-1);
      i++;
    }
  }
  /* close directory */
  if(closedir(dir) == -1){
    fprintf(stderr,"ERROR while closing %s\n", dirname);
    return;
  }
}


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char **argv, char *configfile)
{
  int i;

  if (argc > 3){
    fprintf(stderr,"USAGE: %s [ -c path/to/alt/configfile]\n", argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strncpy(configfile,argv[++i],STRING-1);
	break;

      case 'h': 
	printf("USAGE: %s [-c path/to/alt/configfile]\n", argv[0]);
	printf("-------------------------------\n");
	printf("c-wrapper for FTAN-fortran routines\n");
	
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}


int main (int argc, char **argv)
{
  static int n, npoints, nfin, nfout1, nfout2, ierr;
  static double t0, dt, delta, vmin, vmax, tmin, tmax;
  static double snr, tresh, ffact, perc, taperl;
  static float sei[32768];
  static double arr1[100][7],arr2[100][6];
  static double tamp, ampo[100][32768];// pred[2][300];
  static int nrow, ncol;// npred
  static double pred_1[2][300];
  static int npred_1;
  char configfile[STRING];
  char **filelist, *sacroot;
  char  name[160];//str[160];
  int   i;//nn
  int   sac = 1; // =1 - SAC, =0 - ftat files
  int counter=0;
  double initerror=0;
  dictionary *dd;


  // input command line arguments treatment
  strncpy(configfile,"./config.txt",STRING-1);
  get_args(argc,argv,configfile);

  dd = iniparser_new(configfile);
  vmin = iniparser_getdouble(dd,"FTAN:vmin",initerror);
  vmax = iniparser_getdouble(dd,"FTAN:vmax",initerror);
  tmin = iniparser_getdouble(dd,"FTAN:tmin",initerror);
  tmax = iniparser_getdouble(dd,"FTAN:tmax",initerror);
  tresh = iniparser_getdouble(dd,"FTAN:thresh",initerror);
  ffact = iniparser_getdouble(dd,"FTAN:ffact",initerror);
  taperl = iniparser_getdouble(dd,"FTAN:taperl",initerror);
  snr = iniparser_getdouble(dd,"FTAN:snr",initerror);
  printf("FTAN parameters:\n");
  printf("--> vmin = %lf, vmax = %lf\n",vmin,vmax);
  printf("--> tmin = %lf, tmax = %lf\n",tmin,tmax);
  printf("--> threshhold = %lf\n",tresh);
  printf("--> filter-factor = %lf\n",ffact);
  printf("--> taper length = %lf\n",taperl);
  printf("--> SNR = %lf\n",snr);

  sacroot = iniparser_getstr(dd,"database:sacdirroot");
  strcat(sacroot,"STACK/");
  count_files(sacroot,&counter);
  printf("number of files is: %d\n",counter);

  filelist = (char **)malloc(counter * sizeof(char *));
  if(NULL == filelist) {
    printf("no more virtuel RAM available ... !");
    return EXIT_FAILURE;
  }

  for(i = 0; i < counter; i++) {
    filelist[i] = (char *)malloc(sizeof(char[STRING]));
    if(NULL == filelist[i]) {
      printf("no more storage for line %d\n",i);
      return EXIT_FAILURE;
    }
    
  }

  get_filelist(sacroot,filelist,counter);
  for(i=0;i<counter;i++){
    printf("%s\n",filelist[i]);
  }

  for(i=0;i<counter;i++){
    strncpy(name,filelist[i],159);
    /*
     *   read SAC or ascii data 
     */
    readdata(sac,name,&n,&dt,&delta,&t0,sei);
    t0      = 0.0;
    nfin    = 40;
    npoints = 3;        // only 3 points in jump
    perc    = 50.0;     // 50 % for output segment
    //  taperl  = 2.0;      // factor to the left end tapering
    printf("#filters= %d, Perc= %6.2f %s, npoints= %d, Taper factor= %6.2f\n",
	   nfin,perc,"%",npoints,taperl);
    /* Call aftan4i function, FTAN + prediction         */
    printf("FTAN + prediction curve\n");
    //  ffact =2.0;
    int ii; 
    for(ii=0;ii<=3;ii++)
      {
	if(ii==0)
	  {
	    tmin=5;
	    tmax=14;
	  }
	else if(ii==1)
	  {
	    tmin=10;
	    tmax=25;
	  }
	else if(ii==2)
	  {
	    tmin=15;
	    tmax=35;
	  }
	else
	  {
	    tmin=20;
	    tmax=50;
	  }
   
	/* FTAN with phase match filter. First Iteration. */
      
	printf("FTAN - the first ineration\n");
	//      ffact =1.0;
	aftan4_(&n,sei,&t0,&dt,&delta,&vmin,&vmax,&tmin,&tmax,&tresh,
		&ffact,&perc,&npoints,&taperl,&nfin,&snr,&nfout1,arr1,
		&nfout2,arr2,&tamp,&nrow,&ncol,ampo,&ierr);
	printres(dt,nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,ampo,ierr,name,"_1",delta,ii);
	if(nfout2 == 0) continue;   // break aftan sequence
      
	/* Make prediction based on the first iteration               */
	if(nfout1==nfout2)
	  {
	    npred_1 = nfout2;
	    for(i = 0; i < nfout2; i++) {
	      pred_1[0][i] = arr2[i][1];   // ??central periods
	      pred_1[1][i] = arr2[i][2];   // group velocities
	    }
	  
	    /* FTAN with phase match filter. Second Iteration. */
	  
	    printf("FTAN - the second iteration (phase match filter)\n");
	    //	  ffact = 2.0;
	    aftan4i_(&n,sei,&t0,&dt,&delta,&vmin,&vmax,&tmin,&tmax,&tresh,
		     &ffact,&perc,&npoints,&taperl,&nfin,&snr,&npred_1,pred_1,&nfout1,arr1,
		     &nfout2,arr2,&tamp,&nrow,&ncol,ampo,&ierr);
	    printres(dt,nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,ampo,ierr,name,"_2",delta,ii);
	  }
      }
  }
  iniparser_free(dd);
  return 0;
}






/* ====================================================================
 * Parameters for aftan4 function:
 * Input parameters:
 * n       - number of input samples, (int)
 * sei     - input array length of n, (float)
 * t0      - time shift of SAC file in seconds, (double)
 * dt      - sampling rate in seconds, (double)
 * delta   - distance, km (double)
 * vmin    - minimal group velocity, km/s (double)
 * vmax    - maximal value of the group velocity, km/s (double)
 * tmin    - minimal period, s (double)
 * tmax    - maximal period, s (double)
 * tresh   - treshold, usually = 10, (double)
 * ffact   - factor to automatic filter parameter, (double)
 * perc    - minimal length of of output segment vs freq. range, % (double)
 * npoints - max number points in jump, (int)
 * taperl  - factor for the left end seismogram tapering,
 *           taper = taperl*tmax,    (double)
 * nfin    - starting number of frequencies, nfin <= 100, (int)
 * snr     - phase match filter parameter, spectra ratio to
 *           determine cutting point    (double)
 * npred   - length of prediction table
 * pred    - prediction table: pred[0][] - periods in sec,
 *                             pred[1][] - pedicted velocity, km/s
 * ==========================================================
 * Output parameters are placed in 2-D arrays arr1 and arr2,
 * arr1 contains preliminary results and arr2 - final.
 * ==========================================================
 * nfout1 - output number of frequencies for arr1, (int)
 * arr1   - the first nfout1 raws contain preliminary data,
 *          (double arr1[n][5], n >= nfout1)
 *          arr1[:,0] -  central periods, s (double)
 *          arr1[:,1] -  apparent periods, s (double)
 *          arr1[:,2] -  group velocities, km/s (double)
 *          arr1[:,3] -  amplitudes, Db (double)
 *          arr1[:,4] -  discrimination function, (double)
 *          arr1[:,5] -  signal/noise ratio, Db (double)
 *          arr1[:,6] -  maximum half width, s (double)
 * nfout2 - output number of frequencies for arr2, (int)
 *          If nfout2 == 0, no final result.
 * arr2   - the first nfout2 raws contains final data,
 *          (double arr2[n][5], n >= nfout2)
 *          arr2[:,0] -  central periods, s (double)
 *          arr2[:,1] -  apparent periods, s (double)
 *          arr2[:,2] -  group velocities, km/s (double)
 *          arr2[:,3] -  amplitudes, Db (double)
 *          arr2[:,4] -  signal/noise ratio, Db (double)
 *          arr2[:,5] -  maximum half width, s (double)
 *          tamp      -  time to the beginning of ampo table, s (double)
 *          nrow      -  number of rows in array ampo, (int)
 *          ncol      -  number of columns in array ampo, (int)
 *          ampo      -  Ftan amplitude array, Db, (double [100][32768])
 * ierr   - completion status, =0 - O.K.,           (int)
 *                             =1 - some problems occures
 *                             =2 - no final results
 */

