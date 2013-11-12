#define MAIN

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mysac.h>

#define ANPTSMAX 4320000
#define SLENGTH 300

/* Function prototypes */

void filter4_(double *f1,double *f2,double *f3,double *f4,int *npow,
              double *dt,int *n, float seis_in[], float seis_out[]);

int main (int argc, char *argv[])
{
  static int n, npow;
  static double f1, f2, f3, f4, dt;
  static float seis_in[ANPTSMAX],seis_out[ANPTSMAX];
  static SAC_HD shd;
  
  double t1,t2,t3,t4;
  char  name_in[SLENGTH], name_out[SLENGTH];
  int   nn;
      
  while((nn = fscanf(stdin,"%lf %lf %lf %lf %d %s %s",
      &t1,&t2,&t3,&t4,&npow,name_in, name_out)) != EOF){
      if(nn == 0 || nn   != 7){
	fprintf(stderr,"ERROR: wrong number of input parameters to filter4\n");
	break;
      }
      
      /* Read SAC header and seismogram */
      if ( !read_sac(name_in, seis_in, &shd, ANPTSMAX))
	{
	  fprintf(stderr,"ERROR: file %s not found\n", name_in);
	  continue;
	}
      n  = shd.npts;
      dt = shd.delta;
      fprintf(stdout,"%d %f\n",n,dt);
      /* ==========================================================
       * Parameters for filter4 function:
       * Input parameters:
       * f1,f2   - low corner frequences, f2 > f1, Hz, (double)
       * f3,f4   - high corner frequences, f4 > f3, Hz, (double)
       * npow    - power of cosine tapering,  (int)
       * dt      - sampling rate of seismogram in seconds, (double)
       * n       - number of input samples, (int)
       * seis_in - input array length of n, (float)
       * Output parameters:
       * seis_out - output array length of n, (float)
       * ==========================================================
       */
      f1 = 1.0/t1; f2 = 1.0/t2; f3 = 1.0/t3; f4 = 1.0/t4;
      fprintf(stdout,"Parameters for filter 4 are:\n");
      fprintf(stdout,"--> f1: %f\n", f1);
      fprintf(stdout,"--> f2: %f\n", f2);
      fprintf(stdout,"--> f3: %f\n", f3);
      fprintf(stdout,"--> f4: %f\n", f4);
      fprintf(stdout,"--> filein: %s\n", name_in);
      fprintf(stdout,"--> fileout: %s\n", name_out);
      filter4_(&f1,&f2,&f3,&f4,&npow,&dt,&n,seis_in,seis_out);

      /*write results to SAC file*/
      write_sac(name_out,seis_out, &shd);
   }

   return 0;
}
