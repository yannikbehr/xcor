/*--------------------------------------------------------------------------
  driver program to call fortran filter routines; do spectral whitening and
  time normalization

  written by Fan Chi ????
  $Rev: 454 $
  $Author$
  $LastChangedDate: 2008-01-16 13:02:26 +1300 (Wed, 16 Jan 2008) $
  --------------------------------------------------------------------------*/
#define MAIN

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mysac.h>


#define ANPTSMAX 4320000
#define SLENGTH  300

/* Function prorotypes */

void filter4_(double *f1,double *f2,double *f3,double *f4,int *npow,
		double *dt,int *n, float seis_in[],float seis_out[],
		float seis_outamp[],float seis_outph[],int *ns,double *dom);

float sig[ANPTSMAX];
SAC_HD shd1;

int main (int argc, char **argv)
{
	static int n, ns,npow;
	static double f1, f2, f3, f4, dt,dom;
	static float seis_in[ANPTSMAX],seis_out[ANPTSMAX];
	static float seis_outamp[ANPTSMAX],seis_outph[ANPTSMAX];
	double t1,t2,t3,t4;
	char  name[SLENGTH], name1[SLENGTH];
	char  nameamp[SLENGTH], nameph[SLENGTH];
	int   i, nn;

	while((nn = fscanf(stdin,"%lf %lf %lf %lf %d %s",&t1,&t2,&t3,&t4,
			&npow,name)) != EOF) { // start main loop
		if(nn == 0 || nn != 6){
			fprintf(stderr,"ERROR: wrong number of input parameters for white_1cmp\n");
			break;
		}
		printf("Corners periods. Low: %f - %f, High: %f - %f\n",t1, t2, t3, t4);
		if ( !read_sac(name, sig, &shd1, ANPTSMAX ) )
		{
			fprintf(stderr,"file %s did not found\n", name1 );
			return 0;
		}

		n  = shd1.npts;
		dt = shd1.delta;

		for( i =0; i< n; i++)
		{
			seis_in[i] = sig[i];
		}
		f1 = 1.0/t1; f2 = 1.0/t2; f3 = 1.0/t3; f4 = 1.0/t4;
		filter4_(&f1,&f2,&f3,&f4,&npow,&dt,&n,seis_in,seis_out,seis_outamp,seis_outph,&ns,&dom);

		write_sac(name,seis_out, &shd1);

		strcpy(nameamp,name);
		strcpy(nameph,name);
		strcat(nameamp,".am");
		strcat(nameph, ".ph");
		shd1.npts = ns/2 + 1;
		shd1.delta = dom;
		shd1.b = 0;
		shd1.iftype = IXY;
		write_sac(nameamp,seis_outamp, &shd1 );
		write_sac(nameph, seis_outph,  &shd1 );
	}
	return 0;
}
