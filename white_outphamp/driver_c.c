/*--------------------------------------------------------------------------
  driver program to call fortran filter routines; do spectral whitening and
  time normalization

  written by Fan Chi ????
  $Rev:$
  $Author:$
  $LastChangedDate:$
  --------------------------------------------------------------------------*/
#define MAIN

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mysac.h>
#include <iniparser.h>


/* Function prorotypes */

void filter4_(double *f1,double *f2,double *f3,double *f4,int *npow,
              double *dt,int *n, float seis_in[],float seis_out[],
              float seis_outamp[],
              float seis_outph[],int *ns,double *dom);

void swapn(unsigned char *b, int N, int n);
void get_args(int argc, char** argv, char *configfile);
SAC_HD *read_sac (char *fname, float *sig, SAC_HD *SHD, long nmax);
void write_sac (char *fname, float *sig, SAC_HD *SHD);

/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char *configfile){

  int i;

  if (argc>4){
    fprintf(stderr,"USAGE: %s parameter file [-c alt/config.file]\n",argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strncpy(configfile,argv[++i],199);
	break;

      case 'h':	printf("USAGE: %s parameter file [-c alt/config.file]\n",argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
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
      fprintf(stderr,
	      "ATTENTION !!! dans le fichier %s npts est limite a %ld",fname,nmax);

      SHD->npts = nmax;
    }

  fread(sig,sizeof(float),(int)(SHD->npts),fsac);

  fclose (fsac);

  /*-------------  calcul de t0  ----------------*/
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
void write_sac (char *fname, float *sig, SAC_HD *SHD){

  FILE *fsac;
  int i;

  fsac = fopen(fname, "wb");

  if ( !SHD ) SHD = &SAC_HEADER;


  SHD->iftype = (long)ITIME;
  SHD->leven = (long)TRUE;

  SHD->lovrok = (long)TRUE;
  SHD->internal4 = 6L;



  /*+++++++++++++++++++++++++++++++++++++++++*/
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



/*c/////////////////////////////////////////////////////////////////////////*/
float sig[1000000];
SAC_HD shd1;

/*c/////////////////////////////////////////////////////////////////////////*/

int main (int argc, char **argv)
{
  static int n, ns,npow;
  static double f1, f2, f3, f4, dt,dom;
  static float seis_in[400000],seis_out[400000];
  static float seis_outamp[400000],seis_outph[400000];
  double t1,t2,t3,t4;
  char  name[160], name1[160], name_test[160];
  char  nameamp[160], nameph[160], configfile[200];
  char *sacdir;
  dictionary *dd;
  FILE  *in, *ff;
  int   i, j, nn;

  strncpy(configfile,"./config.txt",199);
  get_args(argc,argv,configfile);

  // open and read parameter file param.dat
  if((in = fopen(argv[1],"r")) == NULL) {
    printf("Can not find file %s.\n",argv[1]);
    exit(1);
  }

  while((nn = fscanf(in,"%lf %lf %lf %lf %lf %d %s %s",&t1,&t2,&t3,&t4,
		     &dt,&npow,name,name_test)) != EOF) { // start main loop
    if(nn == 0 || nn != 8) break;
    printf("TEST: filename: %s\n",name);
    printf("Corners periods. Low: %f - %f, High: %f - %f\n",t1, t2, t3, t4);
    printf("Step: %f, Cosine power: %d\n",dt, npow);

    // remove quotes from name
    j = 0;
    for(i = 0; i < strlen(name); i++) {
      if(name[i] == '\'' || name[i] == '\"') continue;
      name[j] = name[i]; j++;
    }
    name[j] = '\0';

    // do running average before whitening
    dd = iniparser_new(configfile);
    sacdir = iniparser_getstr(dd, "database:sacdir");


    ff = fopen("sac_one_cor","w");
    fprintf(ff,"%ssac << END >/dev/null\n",sacdir);
    fprintf(ff,"r %s\n",name_test);
    // ./test2/%s ./test3/%s\n", name,name,name);
    fprintf(ff,"abs\n");
    fprintf(ff,"smooth mean h 128\n");
    fprintf(ff,"w a1.avg\n");
    // a2.avg a3.avg\n");
    //fprintf(ff,"r a1.avg\n");
    //fprintf(ff,"mulf a2.avg\n");
    //fprintf(ff,"mulf a3.avg\n");
    //fprintf(ff,"smooth h 128\n");
    //fprintf(ff,"w a4.avg\n");
    fprintf(ff,"r %s\n",name);
    fprintf(ff,"divf a1.avg\n");
    fprintf(ff,"w smooth.sac\n");
    fprintf(ff,"quit\n");
    fprintf(ff,"END\n");
    fclose(ff);
    system("sh sac_one_cor");
    system("rm sac_one_cor a1.avg");

    // end of running average


    if ( !read_sac("smooth.sac", sig, &shd1, 1000000 ) )
      {
	fprintf(stderr,"file %s did not found\n", name1 );
	return 0;
      }

    n  = shd1.npts;
    dt = shd1.delta;
   
    for( i =0; i< n; i++)
      {  
	seis_in[i] = sig[i];  
	//     printf(" seis_in1  %d %f\n", i,sig[i]);
      }

    printf(" Dt1= %f, Nsamples1= %d\n",dt, n);


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
    system("rm smooth.sac");
    


  }

  iniparser_free(dd);
  return 0;
}
