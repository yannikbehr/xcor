/*--------------------------------------------------------------------------
  program to merge several sac files of the same date to one file
  --------------------------------------------------------------------------*/

#define MAIN
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <assert.h>
#include "merge_sac.h"


/*========================== MAIN =================================================*/
int main (int argc, char** argv)
{
  int i=0, nn, ret;
  char str[NFILES][LINEL];
  while((nn = fscanf(stdin,"%s",str[i])) != EOF) i++;
  ret = merge_sac(str, i, argv[1]);
  if(ret == 0){
    return 1;
  }else{
    return 0;
  }
}

/*-------------------------------------------------------------------------
  merge several sac files into one-day sac-files interpolating over data
  holes
  -------------------------------------------------------------------------*/
int merge_sac(char str[NFILES][LINEL], int i, char *fileout){
  int k, j, nfirst, Nholes;
  long N;
  SAC_HD sh[NFILES], s0;
  double t1[NFILES], t2[NFILES];
  double T1=1.e25, T2=100.;
  float *sig0, *sig1;
  int nf;


  for(j=0; j<i; j++){
    if ( !read_sac_header( str[j],&(sh[j])))
      {
	fprintf(stderr,"ERROR: file %s not found\n", str[i]);
	continue;
      }
    t1[j] = abs_time (sh[j].nzyear, sh[j].nzjday, sh[j].nzhour, 
		      sh[j].nzmin, sh[j].nzsec, sh[j].nzmsec );
    t2[j] = t1[j] + sh[j].npts*sh[j].delta;
    
    /* finding the longest time series and the earliest starting time*/
    if ( t1[j] < T1 )
      {
	T1 = t1[j];
	nfirst = j;
	}

      if ( t2[j] > T2 ) T2 = t2[j];
    }
  nf = j;
  memcpy(&s0, &(sh[nfirst]), sizeof(SAC_HD) );
  s0.user0 = T1;
  s0.user1 = T2;

  N = nint((T2-T1)/s0.delta);
  //  if(N < THRESH){
  //    fprintf(stdout, "WARNING: trace smaller than %d pts", THRESH);
  //    return 1;
  //  }
  s0.npts = N;
  sig0 = (float *)malloc(N*sizeof(float));
  for (j=0;j<N;j++ ) sig0[j] = 1.e30;


  for (j = 0;j<nf;j++){
    int nb;
    double ti;
    //    if ( !read_sac( str[i], sig1, &(sh[i]), N))
    sig1 = read_sac_dyn( str[j], &(sh[j]));
    if ( !sig1 )
      {
	fprintf(stderr,"ERROR: file %s not found\n", str[j]);
	continue;
      }

    if ( fabs(sh[j].delta-s0.delta) > .0001 )
      {
	fprintf(stderr,"ERROR: incompatible dt in file %s\n", str[j]);
	continue;
      }

    ti = abs_time (sh[j].nzyear, sh[j].nzjday, sh[j].nzhour, sh[j].nzmin, 
		   sh[j].nzsec, sh[j].nzmsec );
    nb = nint((ti-T1)/s0.delta);

    /* finding all the values that are higher than 1e29 */
    for ( k = 0; k < sh[j].npts; k++ )
      {
	int jj = nb+k;

	if ( sig0[jj] > 1.e29 ) sig0[jj] = sig1[k];
      }
    free(sig1);
  }

  Nholes = 0;

  for ( j = 0; j < N; j++ ) if ( sig0[j] > 1.e29 ) Nholes++;

  if ( (float)Nholes/(float)N > 0.1 ){
    fprintf(stderr,"ERROR: too many holes\n");
    return 0;
  }


  for ( j = 0; j < N; j++ ){
    if ( sig0[j] > 1.e29 ){
      float av;
      int npart = 16;
      for( ;;){
	av = av_sig (sig0, j, N, N/npart );
	if ( av < 1.e29 ) break;
	if ( npart == 1 )
	  {
	    av = 0.;
	    break;
	  }
	npart = npart/2;
      }
      sig0[j] = av;
    }
  }
  write_sac (fileout, sig0, &s0);
  free(sig0);
  return 1;
}


/*--------------------------------------------------------------------------
  returns sign of f
  --------------------------------------------------------------------------*/
int isign(double f)
{
  if (f < 0.)     return -1;
  else            return 1;
}


/*--------------------------------------------------------------------------
  compute nearest integer to f
  --------------------------------------------------------------------------*/
int nint(double f){
  int i;
  double df;
  i=(int)f;
  df=f-(double)i;
  if (fabs(df) > .5) i=i+isign(df);

  return i;
}


/*------------------------------------------------------------------------
  computes arithmetic average for sig between sig[i-N/2] and sig[i+N/2]
  --------------------------------------------------------------------------*/
float av_sig (float *sig, int i, int N, int nwin ){
  int n1, n2, j, nav = 0;
  float av = 0.;

  if ( nwin > N ) nwin = N;

  n1 = i - nwin/2;

  if ( n1 < 0 ) n1 = 0;

  n2 = n1 + nwin - 1;

  if ( n2 > N-1 ) n2 = N-1;

  n1 = n2 - nwin + 1;

  for ( j = n1; j <= n2; j++ ) if ( sig[j] < 1.e29 )
    {
      av += sig[j];
      nav++;
    }

  if ( nav < 1 ) av = 1.e30;

  else av = av/(float)nav;

  return av;
}


/*--------------------------------------------------------------------------
  computes time in s relative to 1970
  --------------------------------------------------------------------------*/
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms ){

  long nyday = 0, i;

  for ( i = 1970; i < yy; i++ )
    {
      nyday += ndaysinyear(i);
    }

  return 24.*3600.*(nyday+jday) + 3600.*hh + 60.*mm + ss + 0.001*ms;
}


/*--------------------------------------------------------------------------
  decide whether year is a leap year or not and return number of days 
  accordingly
  --------------------------------------------------------------------------*/
int ndaysinyear (int yy){
  int i0, i1, i2;
  i0 = yy % 4;
  i1 = yy % 100;
  i2 = yy % 400;
  if((i0 == 0 && i1 != 0) || i2 == 0){
    return 366;
  }else{
    return 365;
  }
}




