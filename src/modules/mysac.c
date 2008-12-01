#include <stdlib.h>
#include <stdio.h>
#include "mysac.h"

/*--------------------------------------------------------------------------
  reads sac-files fname with maximum length nmax into signal sig and \
  header SHD
  --------------------------------------------------------------------------*/
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax){
  FILE *fsac;
  fsac = fopen(fname, "rb");
  if ( !fsac )
    {
      fprintf(stderr,"file %s not found\n",fname);
      return NULL;
    }

  if ( !SHD ) SHD = &SAC_HEADER;

  fread(SHD,sizeof(SAC_HD),1,fsac);

  if ( SHD->npts > nmax )
    {
      fprintf(stderr,"WARNING: in file %s npts is limited to %d",fname,nmax);
      fclose (fsac);
      return NULL;
      //SHD->npts = nmax;
    }

  fread(sig,sizeof(float),(int)(SHD->npts),fsac);


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


/*--------------------------------------------------------------------------
  writes sac file with name fname from signal sig with header SHD
  --------------------------------------------------------------------------*/
int write_sac (char *fname, float *sig, SAC_HD *SHD){
  FILE *fsac;
  int i, ret;
  fsac = fopen(fname, "wb");
  if( NULL == fsac ) {
    fprintf(stderr,"could not open sac file to read\n");
    return 0;
   }
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

  ret = fwrite(SHD,sizeof(SAC_HD),1,fsac);

  ret = fwrite(sig,sizeof(float),(int)(SHD->npts),fsac);


  fclose (fsac);
  return 1;
}


/*--------------------------------------------------------------------------
  reads sac-file fname and allocates memory for trace dynamically according 
  to sac-header information
  --------------------------------------------------------------------------*/
float *read_sac_dyn (char *fname, SAC_HD *SHD){

  FILE *fsac;
  float *sig;
  fsac = fopen(fname, "rb");
  if ( !fsac )
    {
      fprintf( stderr,"file %s not found\n",fname);
      return NULL;
    }
  if ( !SHD ) SHD = &SAC_HEADER;
  fread(SHD,sizeof(SAC_HD),1,fsac);
  sig = (float *)malloc(SHD->npts*sizeof(float));
  if(sig != NULL){
    fread(sig,sizeof(float),(int)(SHD->npts),fsac);
  }else{
    printf("ERROR: nomore virtual RAM available!\n");
    return NULL;
  } 
  fclose (fsac);

  /*-------------  calcule de t0  ----------------*/
  {
    int i;
    char koo[9];

    for ( i = 0; i < 8; i++ ) koo[i] = SHD->ko[i];
    koo[8] = '\0';

    SHD->o = SHD->b + SHD->nzhour*3600. + SHD->nzmin*60 +
      SHD->nzsec + SHD->nzmsec*.001;


    return sig;
  }
}


