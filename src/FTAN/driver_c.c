/*
 * The sample of test driver for FTAN with phase match filter (aftan4i)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "aftan.h"


int main (int argc, char *argv[])
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
 char  name[160],name1[160],name2[160];//str[160];
 FILE  *in; //*fd;
 int   i, j;//nn
int   sac = 1; // =1 - SAC, =0 - ftat files

// input command line arguments treatment
  if(argc != 2) {
      printf("Usage: aftan4_c_test parameter_file\n");
      exit(-1);
  }
// open and read contents of parameter file
  if((in = fopen(argv[1],"r")) == NULL) {
      printf("Can not find file %s.\n",argv[1]);
      exit(1);
  }
  while((n = fscanf(in,"%lf %lf %lf %lf %lf %lf %lf %lf %s",&vmin,&vmax,&tmin,
            &tmax,&tresh,&ffact,&taperl,&snr,name)) != EOF) { // start main loop
      if(n == 0 || n != 9) break;
      printf("vmin= %lf, vmax= %lf, tmin= %lf, tmax= %lf\n",vmin,vmax,tmin,tmax);
// remove quotes from name
      j = 0;
      for(i = 0; i < strlen(name); i++) {
          if(name[i] == '\'' || name[i] == '\"') continue;
          name[j] = name[i]; j++;
      }
      name[j] = '\0';
      printf("Tresh= %lf, Filter factor= %lf, fmatch= %lf\nData file name=%s\n",
             tresh,ffact,snr,name);

      //      strcpy(name1,name);
      // *(strstr(name1,"SAC")) = 0;
/*
 *   read SAC or ascii data 
 */
      readdata(sac,name,&n,&dt,&delta,&t0,sei);
/*
 * Read prediction file
 */

      for(i = 0; i < (strlen(name)-1);i++){
        name1[i] = name[i];
      }
      name1[i] = '\0';
      printf(" name1 %s", name1);
      strcpy(name2,"/Volumes/data/indrajit/Newzealand/2005/PRED_DISP/");
      strcat(name2,name1);
      strcat(name2,"PRED");
      //printf("Prediction curve: %s\n",name2);

      //      if((fd = fopen(name2,"r")) == NULL) {
      //  printf("Can not find file %s\n",name2);
      //  exit(1);
      //}
      //i = 0;
      //fgets(str,100,fd);
      //while((nn = fscanf(fd,"%lf %lf",&pred[0][i],&pred[1][i])) == 2) i++;
      //npred = i;
      //fclose(fd);

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
      //      aftan4i_(&n,sei,&t0,&dt,&delta,&vmin,&vmax,&tmin,&tmax,&tresh,
      //       &ffact,&perc,&npoints,&taperl,&nfin,&snr,&npred,pred,&nfout1,arr1,
      //       &nfout2,arr2,&tamp,&nrow,&ncol,ampo,&ierr);
      //printres(dt,nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,ampo,ierr,name,"_P",delta,ii);
      //if(nfout2 == 0) continue;   // break aftan sequence
      
      
      /* FTAN with phase with phase match filter. First Iteration. */
      
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
	  
	  /* FTAN with phase with phase match filter. Second Iteration. */
	  
	  printf("FTAN - the second iteration (phase match filter)\n");
	  //	  ffact = 2.0;
	  aftan4i_(&n,sei,&t0,&dt,&delta,&vmin,&vmax,&tmin,&tmax,&tresh,
		   &ffact,&perc,&npoints,&taperl,&nfin,&snr,&npred_1,pred_1,&nfout1,arr1,
		   &nfout2,arr2,&tamp,&nrow,&ncol,ampo,&ierr);
	  printres(dt,nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,ampo,ierr,name,"_2",delta,ii);
	}
    }
  }
  fclose(in);
  return 0;
}
