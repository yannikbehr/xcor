#define MAIN

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "mysac.h"

#define ANPTSMAX 4320000
#define SLENGTH  300

/* Function prorotypes */
void filter4_(double *f1,double *f2,double *f3,double *f4,int *npow,
              double *dt,int *n, float seis_in_E[],float seis_in_N[],float seis_out_E[],float seis_out_N[],
              float seis_outamp_E[],float seis_outamp_N[],
              float seis_outph_E[],float seis_outph_N[],int *ns,double *dom);


/*c/////////////////////////////////////////////////////////////////////////*/
float sig[ANPTSMAX];
SAC_HD shd1;
SAC_HD shd2; 


/*c/////////////////////////////////////////////////////////////////////////*/

int main (int argc, char *argv[])
{
  static int n, ns,npow;
  static double f1, f2, f3, f4, dt,dom;
  static float seis_in_E[ANPTSMAX],seis_out_E[ANPTSMAX];
  static float seis_in_N[ANPTSMAX],seis_out_N[ANPTSMAX];
  static float seis_outamp_E[ANPTSMAX],seis_outph_E[ANPTSMAX];
  static float seis_outamp_N[ANPTSMAX],seis_outph_N[ANPTSMAX];

  double t1,t2,t3,t4;
  char  name_E[SLENGTH],name_N[SLENGTH];
  char  name_amp_E[SLENGTH],name_ph_E[SLENGTH];
  char  name_amp_N[SLENGTH],name_ph_N[SLENGTH];
  int   i, nn;

  while((nn = fscanf(stdin,"%lf %lf %lf %lf %d %s %s",&t1,&t2,&t3,&t4,
		     &npow,name_E, name_N)) != EOF) 
    { // start main loop
      if(nn == 0 || nn != 7) break;
      printf("Corners periods. Low: %f - %f, High: %f - %f\n",t1, t2, t3, t4);

      if ( !read_sac(name_E, sig, &shd1, ANPTSMAX) )
	{
	  fprintf(stderr,"ERROR: file %s not found\n",name_E );
	  continue;
	}
      n  = shd1.npts;
      dt = shd1.delta;
      
      for( i =0; i< n; i++)
	{  
	  seis_in_E[i] = sig[i];  
	}
      if ( !read_sac(name_N, sig, &shd2, ANPTSMAX) )
	{
	  fprintf(stderr,"file %s not found\n", name_N );
	  continue;
	}
      for( i =0; i< n; i++)
	{  
	  seis_in_N[i] = sig[i];  
	  //     printf(" seis_in1  %d %f\n", i,sig[i]);
	}
      printf(" Dt1= %f, Nsamples1= %d\n",dt, n);
      
      f1 = 1.0/t1; f2 = 1.0/t2; f3 = 1.0/t3; f4 = 1.0/t4;
      filter4_(&f1,&f2,&f3,&f4,&npow,&dt,&n,seis_in_E,seis_in_N,seis_out_E,seis_out_N,seis_outamp_E,seis_outamp_N,seis_outph_E,seis_outph_N,&ns,&dom);
            
      write_sac(name_E,seis_out_E, &shd1);
      write_sac(name_N,seis_out_N, &shd2);
      
      strcpy(name_amp_E,name_E);
      strcpy(name_ph_E,name_E);
      strcat(name_amp_E,".am");
      strcat(name_ph_E, ".ph");
      strcpy(name_amp_N,name_N);
      strcpy(name_ph_N,name_N);
      strcat(name_amp_N,".am");
      strcat(name_ph_N, ".ph");
      shd1.npts = ns/2 + 1;
      shd1.delta = dom;
      shd1.b = 0;
      shd1.iftype = IXY;
      shd2.npts = ns/2 + 1;
      shd2.delta = dom;
      shd2.b = 0;
      shd2.iftype = IXY;
      write_sac(name_amp_E,seis_outamp_E, &shd1 );
      write_sac(name_ph_E, seis_outph_E,  &shd1 );
      
      write_sac(name_amp_N,seis_outamp_N, &shd2 );
      write_sac(name_ph_N, seis_outph_N,  &shd2 );
      
    }
  
  return 0;
}
