/*--------------------------------------------------------------------------
  program to merge several sac files of the same date to one file
  --------------------------------------------------------------------------*/

#define MAIN
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <mysac.h>
#include <sac_db.h>
#include <assert.h>


/* MACROS */
#define LINEL 300
#define NPTSMAX 5000000
#define SLINE 10
#define NFILES 30


/* FUNCTION DECLARATIONS */
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax);
SAC_HD *read_sac_header(char *fname, SAC_HD *SHD);
void write_sac (char *fname, float *sig, SAC_HD *SHD);
int isign(double f);
int nint(double f);
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms );
float av_sig (float *sig, int i, int N, int nwin );

/* some systems can't cope with very big, locally defined arrays; in this case 
 the array has to be defined globally*/
float sig1[NPTSMAX];
float sig0[NPTSMAX];

/*========================== MAIN =================================================*/
int main (int argc, char** argv)
{
/*-------------------------------------------------------------------------
  merge several sac files into one-day sac-files interpolating over data
  holes
  -------------------------------------------------------------------------*/
  int i=0, n, j, nfirst, Nholes;
  long N;
  SAC_HD sh[NFILES], s0;
  double t1[NFILES], t2[NFILES];
  double T1=1.e25, T2=100.;
  char str[NFILES][LINEL];
  int nf, nn;


  while((nn = fscanf(stdin,"%s",str[i])) != EOF){
      if ( !read_sac_header( str[i],&(sh[i])))
	{
	  fprintf(stderr,"ERROR: file %s not found\n", str[i]);
	  continue;
	}
      t1[i] = abs_time (sh[i].nzyear, sh[i].nzjday, sh[i].nzhour, 
			sh[i].nzmin, sh[i].nzsec, sh[i].nzmsec );
      t2[i] = t1[i] + sh[i].npts*sh[i].delta;

      /* finding the longest time series and the earliest starting time*/
      if ( t1[i] < T1 )
	{
	  T1 = t1[i];
	  nfirst = i;
	}

      if ( t2[i] > T2 ) T2 = t2[i];
      i++;
    }
  nf = i;
  memcpy(&s0, &(sh[nfirst]), sizeof(SAC_HD) );

  N = nint((T2-T1)/s0.delta);
  if ( N > NPTSMAX ) N = NPTSMAX;

  s0.npts = N;

  for ( j = 0; j < N; j++ ) sig0[j] = 1.e30;


  for (i = 0;i<nf;i++){
    int nb;
    double ti;
    if ( !read_sac ( str[i], sig1, &(sh[i]), N))
      {
	fprintf(stderr,"ERROR: file %s not found\n", str[i]);
	continue;
      }

    if ( fabs(sh[i].delta-s0.delta) > .0001 )
      {
	fprintf(stderr,"ERROR: incompatible dt in file %s\n", str[i]);
	continue;
      }

    ti = abs_time (sh[i].nzyear, sh[i].nzjday, sh[i].nzhour, sh[i].nzmin, 
		   sh[i].nzsec, sh[i].nzmsec );
    nb = nint((ti-T1)/s0.delta);

    /* finding all the values that are higher than 1e29 */
    for ( j = 0; j < sh[i].npts; j++ )
      {
	int jj = nb+j;

	if ( sig0[jj] > 1.e29 ) sig0[jj] = sig1[j];
      }
  }

  Nholes = 0;

  for ( j = 0; j < N; j++ ) if ( sig0[j] > 1.e29 ) Nholes++;

  if ( (float)Nholes/(float)N > 0.1 ){
    fprintf(stderr,"ERROR: too many holes\n");
    return 1;
  }


  for ( j = 0; j < N; j++ ){
    if ( sig0[j] > 1.e29 ){
      float av;
      int npart = 16;
      for( ;;){
	av = av_sig (sig0, j, N, N/npart );
	if ( av < 1.e29 ) break;
	if ( npart = 1 )
	  {
	    av = 0.;
	    break;
	  }
	npart = npart/2;
      }
      sig0[j] = av;
    }
  }
  write_sac (argv[1], sig0, &s0);
  return 0;
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


/*--------------------------------------------------------------------------
  reads sac-files fname with maximum length nmax into signal sig and \
  header SHD
  --------------------------------------------------------------------------*/
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax){
  FILE *fsac;
  fsac = fopen(fname, "rb");
  if ( !fsac )
    {
      fclose (fsac);
      return NULL;
    }

  if ( !SHD ) SHD = &SAC_HEADER;

  fread(SHD,sizeof(SAC_HD),1,fsac);

  if ( SHD->npts > nmax )
    {
      fprintf(stderr,"WARNING: in file %s npts is limited to %d",fname,nmax);

      SHD->npts = nmax;
    }

  fread(sig,sizeof(float),(int)(SHD->npts),fsac);

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


    return SHD;
  }
}


/*--------------------------------------------------------------------------
  writes sac file with name fname from signal sig with header SHD
  --------------------------------------------------------------------------*/
void write_sac (char *fname, float *sig, SAC_HD *SHD){
  FILE *fsac;
  int i;
  fsac = fopen(fname, "wb");

  if ( !SHD ) SHD = &SAC_HEADER;


  SHD->iftype = (long)ITIME;
  SHD->leven = (long)TRUE;

  SHD->lovrok = (long)TRUE;
  SHD->internal4 = 6L;

  SHD->depmin = sig[0];
  SHD->depmax = sig[0];
 
  for ( i = 0; i < SHD->npts ; i++ )
    {
      if ( SHD->depmin > sig[i] ) SHD->depmin = sig[i];
      if ( SHD->depmax < sig[i] ) SHD->depmax = sig[i];
    }

  fwrite(SHD,sizeof(SAC_HD),1,fsac);

  fwrite(sig,sizeof(float),(int)(SHD->npts),fsac);


  fclose (fsac);
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




SAC_HD *read_sac_header(char *fname, SAC_HD *SHD)
{
 FILE *fsac;
/*..........................................................................*/
        if((fsac = fopen(fname, "rb")) == NULL) {
          printf("could not open sac file to read\n");
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
