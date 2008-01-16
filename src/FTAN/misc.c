/*
 * Read SAC header and seismogram and make output
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "aftan.h"

void readdata(int sac,char *name,int *n,double *dt,double *delta,
              double *t0,float *sei)
{
int   i,nn, iswap, *ih, *nsam;
float hed[158];       // the SAC header
float dumm,dum[2];
FILE  *fd;

      for(i=0; i < 6000; i++) sei[i]=0.0f;
      iswap = 0;
      if((fd = fopen(name,"r")) == NULL) {
          printf("Can not find file %s.\n",name);
          exit(1);
      }
   if(sac) {
//       The header
      fread(hed,sizeof(float),158,fd);
      ih = (int *)(&hed[76]);
      if(*ih > 100 || *ih < -100) iswap = 1;
      if(iswap) swapn((unsigned char *)hed,(int)(sizeof(float)),158);
      *dt = hed[0];
      *delta = hed[50];
      nsam = (int *)(&hed[79]);
      *t0 = 0.0;
//       The body
      fread(sei,sizeof(float),*nsam,fd);
      if(iswap) swapn((unsigned char *)sei,(int)(sizeof(float)),*nsam);
      *n = *nsam;
   } else {
/*
 * Read test data from ascii file
 */
      i = 0;
      while((nn = fscanf(fd,"%f %f",&dumm,&sei[i])) == 2) {
          if(i < 2) dum[i] = dumm; i++;
      }
// extract delta from file name
      sscanf(&name[strlen("proba_10_0_")],"%lf",delta);
      *dt = dum[1]-dum[0];
      *n = i;
   }
      fclose(fd);

// seismogram is ready

      printf("Delta= %lf, Dt= %lf, Nsamples= %d\n",*delta,*dt,*n);
}
/*
 * print completion result
 */
void printres(double dt,int nfout1,double arr1[100][7],int nfout2,
              double arr2[100][6],double tamp, int nrow,int ncol,
              double ampo[100][32768],int ierr, char *name,char *pref,double delta,int ii)
{
  int i,j;
  FILE *out;
  char name2[160];
  if(ierr  ==  0 ) {
    printf("REESULT: O.K.\n");
  } else if(ierr == 1) {
    printf("RESULT: SOME PROBLEMS\n");
  } else {
    printf("RESULT: NO FINAL RESULT\n");
  }
  //  write results to hard drive
  // file ...DISP.0 contains preliminary result
  strcpy(name2,name);
  strcat(name2,pref);
  strcat(name2,"_DISP.0");
  if(ii==0)
    {
      if((out = fopen(name2,"w")) == NULL) {
	printf("Can not open file %s.\n",name2);
	exit(1);
      }
    }
  else out = fopen(name2,"a");
  for(i = 0; i < nfout1; i++) {
    fprintf(out,"%4d %10.4lf %10.4lf %12.4lf %12.4lf %12.4lf %8.3lf\n",
	    i,arr1[i][0],arr1[i][1],arr1[i][2],arr1[i][3],
	    arr1[i][4],arr1[i][5]);
  }
  fclose(out);
  // file ...DISP.1 includes final results
  if(nfout2 != 0) {
    strcpy(name2,name);
    strcat(name2,pref);
    strcat(name2,"_DISP.1_v1");
    if(ii==0)
      {
	if((out = fopen(name2,"w")) == NULL) {
	  printf("Can not open file %s.\n",name2);
	  exit(1);
	}
      }
    else out=fopen(name2,"a");
    for(i = 0; i < nfout2; i++) {
      if(ii==0 && arr2[i][1]<12)
	fprintf(out,"%4d %10.4lf %10.4lf %12.4lf %12.4lf %8.3lf\n",
		i,arr2[i][0],arr2[i][1],arr2[i][2],arr2[i][3],
		arr2[i][4]);
      if(ii==1 && arr2[i][1]<20 && arr2[i][1] > 11)
	fprintf(out,"%4d %10.4lf %10.4lf %12.4lf %12.4lf %8.3lf\n",
		i,arr2[i][0],arr2[i][1],arr2[i][2],arr2[i][3],
		arr2[i][4]);
      if(ii==2 && arr2[i][1]<27 && arr2[i][1] > 19 )
	fprintf(out,"%4d %10.4lf %10.4lf %12.4lf %12.4lf %8.3lf\n",
		i,arr2[i][0],arr2[i][1],arr2[i][2],arr2[i][3],
		arr2[i][4]);
      if(ii==3 && arr2[i][1] > 27)
	fprintf(out,"%4d %10.4lf %10.4lf %12.4lf %12.4lf %8.3lf\n",
		i,arr2[i][0],arr2[i][1],arr2[i][2],arr2[i][3],
		arr2[i][4]);
    }
    fclose(out);
  }
  // Output amplitude array into file on hard drive
  strcpy(name2,name);
  strcat(name2,pref);
  strcat(name2,"_AMP");
 

  if(ii==0)
    {
      if((out = fopen(name2,"w")) == NULL) {
	printf("Can not open file %s.\n",name2);
	exit(1);
      }
    }
  else out = fopen(name2,"a");
  for(i = 0; i < nrow; ++i)
    for(j = 0; j < ncol; ++j)
      fprintf(out,"%8.3lf %8.3lf %15.6e\n", arr2[i][0],(delta/(tamp+j*dt)),ampo[i][j]);

  // fprintf(out,"%8.3lf %8.3lf %15.6e\n", (double)(i+1),tamp+j*dt,ampo[i][j]);

  fclose(out);
  
}
