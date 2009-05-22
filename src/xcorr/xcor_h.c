/*--------------------------------------------------------------------------
  program to correlate sac-files:
  -reads in sac_db.out file
  -correlation of .am and .ph files in frequ.-domain
  -stacking correlations for one month
  -reads variable 'sacdirroot' from config file

  written by Fan Chi ????
  $Rev: 454 $
  $Author: $
  $LastChangedDate: 2008-01-16 13:02:26 +1300 (Wed, 16 Jan 2008) $
  --------------------------------------------------------------------------*/

#define MAIN
#define _XOPEN_SOURCE 500
#include <ftw.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <regex.h>
#include <glob.h>
#include <libgen.h>
#include <assert.h>
#include <iniparser.h>
#include <mysac.h>
#include <sac_db.h>

/* os-dependent includes for dir-manipulation */
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>

#include <gsl/gsl_errno.h>
#include <gsl/gsl_fft_real.h>
#include <gsl/gsl_fft_halfcomplex.h>

#define MODUS 0711
#define LINEL 300

struct array{
  float delta;
  float az;
  float baz;
};


/* Function prorotypes */
int check_info (SAC_HD *sh1, SAC_HD *sh2);
int do_cor(int lag,char *cordir,char *pbdir);  
void get_args(int argc, char** argv,char *confile);
int find_comp(char *name1_Z, char *name1_N, char *name1_E,char *pbdir,int ne,int ns);
void rotate(int ndat, float* n, float* e,float* r,float* t,float baz);
struct array delaz(float eqlat, float eqlon, float stlat, float stlon, int flag);
void coortr(float *lat, float *lon, int flag);
float *myxcor(float *sig1, float *sig2, int len, int lag);
int write_xcor(float *sig1, float *sig2, int len, int lag, 
	       char *mondir, int ine, int jsta1, int jsta2, char *app);
void make_dir(int ie, char *cordir, char *mondir);


SAC_DB sdb;

#ifndef TEST
/* ---------------------------MAIN-------------------------------------- */
int main (int na, char **arg)
{
  FILE *ff;
  int lag;
  char str[LINEL];
  dictionary *dd;
  char *tmpdir, *pbdir, *cordir, *sacdbname;
  char confile[LINEL];
  strncpy(confile,"./config.txt",LINEL-1);

  get_args(na, arg,confile);

  /* OPEN SAC DATABASE FILE AND READ IN TO MEMORY */
  dd         = iniparser_new(confile);
  tmpdir     = iniparser_getstr(dd, "xcor:tmpdir");
  cordir     = iniparser_getstr(dd, "xcor:cordir");
  lag        = iniparser_getint(dd, "xcor:lag", 3000);
  pbdir      = iniparser_getstr(dd, "xcor:pbdir");
  sacdbname  = iniparser_getstr(dd, "xcor:dbname");

  assert((strlen(tmpdir)+strlen(sacdbname)+1) < LINEL);
  sprintf(str,"%s/%s", tmpdir,sacdbname);

  if((ff = fopen(str, "rb"))==NULL) {
    fprintf(stderr,"%s/%s file not found\n",tmpdir,sacdbname);
    exit(1);
  }

  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  /*do all the work of correlations here  */
  if(!do_cor(lag,cordir,pbdir)){
    fprintf(stderr,"ERROR: in function 'do_cor'!\n");  
    return 1;
  }
  printf("correlations finished\n");

  iniparser_free(dd);
  return 0;
}

/* ------------------------------END MAIN----------------------------------- */
#endif


/*----------------------------------------------------------------------------
  evaluate sac_header
  ----------------------------------------------------------------------------*/
int check_info (SAC_HD *sh1, SAC_HD *sh2){
  if(sh1->npts <= 0){
    fprintf(stderr,"no data for station %s \n", sh1->kstnm);
    return 0;
  }
  if(sh2->npts <=0){
    fprintf(stderr,"no data for station %s \n", sh2->kstnm);
    return 0;
  }
  if(abs((sh1->npts - sh2->npts))>0.0001){
    fprintf(stderr,"ERROR: traces have not the same length!\n");
    return 0;
  }
  if ( fabs(sh1->delta - sh2->delta) > .0001 ) {
    fprintf(stderr,"ERROR: incompatible sampling frequ. for %s and %s \n",sh1->kstnm, sh2->kstnm);
    return 0;
  }
  return 1;
}


SAC_HD sh1, sh2, shd_cor;

/*----------------------------------------------------------------------------
  correlation in frequ.-domain
  lag    = half length of correlation window
  cordir = directory for correl. results
  ----------------------------------------------------------------------------*/
int do_cor(int lag , char *cordir, char* pbdir)
{
  int ine, jsta1, jsta2;
  int len, ndat, retval1, retval2; 
  char  mondir[LINEL];
  char name1_N[LINEL], name1_E[LINEL], name1_Z[LINEL];
  char name2_N[LINEL], name2_E[LINEL], name2_Z[LINEL]; 
  float *t1, *t2, *r1, *r2, *z1, *z2;
  float *sigE, *sigN;
  struct array loc;
  
  t1=t2=r1=r2=z1=z2=sigE=sigN=NULL;
  /*outermost loop over day number, then station number*/
  for( ine = 0; ine < sdb.nev; ine++ ) {
    fprintf(stdout,"event number %d\n",ine);
    make_dir(ine,cordir,mondir);

    /*loop over "base" station number, this will be stored into common memory*/
    for( jsta1 = 0; jsta1 < sdb.nst; jsta1++ ) {  
      retval1 = find_comp(name1_Z, name1_N, name1_E,pbdir,ine,jsta1);
      if(retval1 < 1)continue;
      //      if(retval1 == 1 || retval1 == 3 || retval1 == 5 || retval1 == 7){
      if(((retval1+2)%2)>0){
	z1 = read_sac_dyn(name1_Z, &sh1);
      }

      /* loop over second station */
      for( jsta2 = (jsta1+1); jsta2 < sdb.nst; jsta2++ ) {
	retval2 = find_comp(name2_Z, name2_N, name2_E,pbdir,ine,jsta2);
	if(retval2 < 1)continue;
	if(((retval1+2)%2)>0 && ((retval2+2)%2)>0){
		z2 = read_sac_dyn(name2_Z, &sh2);
		if(!check_info(&sh1,&sh2))continue;
		len=sh1.npts;
		fprintf(stdout,"xcor ZZ: %s %s\n", sdb.st[jsta1].name, sdb.st[jsta2].name);
		write_xcor(z1,z2,len,lag,mondir,ine,jsta1,jsta2,"_zz");
		free(z2);
	}
	if(retval2 >= 6 && retval1 >= 6){
	  /* if east and north comp present do rotation */
	  /* rotation 1st station */
	  fprintf(stdout,"rotation of: %s %s\n",name1_E,name1_N);
	  loc = delaz(sdb.st[jsta1].lat,sdb.st[jsta1].lon,sdb.st[jsta2].lat,sdb.st[jsta2].lon,0);
	  sigE = read_sac_dyn(name1_E, &sh1);
	  sigN = read_sac_dyn(name1_N, &sh2);
	  if(!check_info(&sh1,&sh2))continue;
	  ndat = sh1.npts;
	  t1 = (float *)malloc(ndat*sizeof(float));
	  r1 = (float *)malloc(ndat*sizeof(float));
	  rotate(ndat,sigN,sigE,r1,t1,loc.baz*M_PI/180.);
	  free(sigE);free(sigN);
	  /* rotation 2nd station */
	  fprintf(stdout,"rotation of: %s %s\n",name2_E,name2_N);
	  sigE = read_sac_dyn(name2_E, &sh1);
	  sigN = read_sac_dyn(name2_N, &sh2);
	  if(!check_info(&sh1,&sh2))continue;
	  t2 = (float *)malloc(ndat*sizeof(float));
	  r2 = (float *)malloc(ndat*sizeof(float));
	  rotate(ndat,sigN,sigE,r2,t2,loc.baz*M_PI/180.);
	  free(sigE);free(sigN);
	  /* XCORR */
	  len=sh1.npts;
	  fprintf(stdout,"xcor TT: %s %s\n", sdb.st[jsta1].name, sdb.st[jsta2].name);
	  write_xcor(t1,t2,len,lag,mondir,ine,jsta1,jsta2,"_tt");
	  fprintf(stdout,"xcor RR: %s %s\n", sdb.st[jsta1].name, sdb.st[jsta2].name);
	  write_xcor(r1,r2,len,lag,mondir,ine,jsta1,jsta2,"_rr");
	  free(t1);free(t2);free(r1);free(r2);
	}
      }	/* loop over jsta2 */
      if(((retval1+2)%2)>0)free(z1);
    } /* loop over jsta1 */
  }  /* loop over events */
  return 1;
}



int write_xcor(float *sig1, float *sig2, int len, int lag, 
	       char *mondir, int ine, int jsta1, int jsta2, char *app){
  /* construct xcor filename */
  char filename[LINEL];
  float *cor=NULL;
  assert((strlen(mondir)+strlen(sdb.st[jsta1].name)+
	  strlen(sdb.st[jsta2].name)+16)<LINEL);
  sprintf(filename, "%s/COR_%s_%s.SAC%s",
	  mondir, sdb.st[jsta1].name, sdb.st[jsta2].name,app);
  cor = myxcor(sig1,sig2,len,lag);
  if(NULL == cor){
    fprintf(stderr,"ERROR: xcor failed!\n");
    return 0;
  }else{
    if(lag<len){
      shd_cor.npts =  2*lag+1;
    }else{
      shd_cor.npts =  2*len-1;
    }
    shd_cor.delta = sdb.rec[ine][jsta1].dt;
    shd_cor.evla =  sdb.st[jsta1].lat;
    shd_cor.evlo =  sdb.st[jsta1].lon;
    shd_cor.stla =  sdb.st[jsta2].lat;
    shd_cor.stlo =  sdb.st[jsta2].lon;
    shd_cor.b    = -(lag)*shd_cor.delta;
    shd_cor.unused1 = 1;
    strncpy(shd_cor.kevnm,sdb.st[jsta1].name,7);
    strncpy(shd_cor.kstnm,sdb.st[jsta2].name,7);
    if(!write_sac(filename, cor, &shd_cor)){
      fprintf(stderr,"ERROR: cannot write sac-file for %s and %s!\n",
	      sdb.st[jsta1].name,sdb.st[jsta2].name);
      free(cor);
      return 0;
    }
    free(cor);
  }
  return 1;
}
/*--------------------------------------------------------------------------
  function to find East-, North- and Z-component files for given date-dir
   ------------------------------------------------------------------------*/
int find_comp(char *nameZ, char *nameN, char *nameE, char *pbdir,int ne,int ns){
  char *dircp, *dirn, *base, *basecp;
  char pattern[LINEL], newdir[LINEL];
  glob_t match;
  int retval=0;
  
  dircp = strdup(sdb.ev[ne].name);
  basecp = strdup(sdb.ev[ne].name);
  dirn = dirname(dircp);
  base = basename(basecp);
  assert((strlen(dirn)+strlen(pbdir)+strlen(base)+2)<LINEL-1);
  sprintf(newdir,"%s/%s/%s",dirn,pbdir,base);
  
  /* find Z-component file*/
  assert((strlen(newdir)+strlen(sdb.st[ns].name)+11)<LINEL-1);
  sprintf(pattern,"%s/ft_%s.*HZ.SAC",newdir,sdb.st[ns].name);
  if(glob(pattern, 0, NULL, &match) == 0){
    if(match.gl_pathc>1){
      fprintf(stderr,"WARNING: found more than 1 matching file for %s\n",pattern);
    }else if(abs(match.gl_pathc - 1)< 0.0001) {
      strncpy(nameZ,match.gl_pathv[0],LINEL-1);
      retval = retval + 1;
    }else{
      fprintf(stderr,"ERROR: no matching file found for %s\n",pattern);
    }
  }
  globfree(&match);

  /* find E-component file */
  assert((strlen(newdir)+strlen(sdb.st[ns].name)+11)<LINEL-1);
  sprintf(pattern,"%s/ft_%s.*HE.SAC",newdir,sdb.st[ns].name);
  if(glob(pattern, 0, NULL, &match) == 0){
    if(match.gl_pathc>1){
      fprintf(stderr,"WARNING: found more than 1 matching file for %s\n",pattern);
    }else if(abs(match.gl_pathc - 1)< 0.0001) {
      strncpy(nameE,match.gl_pathv[0],LINEL-1);
      retval=retval+2;
    }else{
      fprintf(stderr,"ERROR: no matching file found for %s\n",pattern);
    }
  }
  globfree(&match);

  /* find N-component file*/
  assert((strlen(newdir)+strlen(sdb.st[ns].name)+11)<LINEL-1);
  sprintf(pattern,"%s/ft_%s.*HN.SAC",newdir,sdb.st[ns].name);
  if(glob(pattern, 0, NULL, &match) == 0){
    if(match.gl_pathc>1){
      fprintf(stderr,"WARNING: found more than 1 matching file for %s\n",pattern);
    }else if(abs(match.gl_pathc - 1)< 0.0001) {
      strncpy(nameN,match.gl_pathv[0],LINEL-1);
      retval=retval+4;
    }else{
      fprintf(stderr,"ERROR: no matching file found for %s\n",pattern);
    }
  }

  globfree(&match);
  free(dircp);
  free(basecp);
  return retval;
}



/*------------------------------------------------------------------------------
  cross-correlation function using the gsl-library
  ----------------------------------------------------------------------------*/
float *myxcor(float *sig1, float *sig2, int len, int lag){
  double *x, *y, *c;
  float *sigout;
  int n=2, i, cl;
  if(lag<len){
    cl = lag;
  }else{
    cl = len-1;
  }
  n = (int)pow(2.,(int)(log10(2*len)/log10(2))+1);
  x = (double *)malloc(sizeof(double)*n);
  memset(x,0,sizeof(double)*n);
  y = (double *)malloc(sizeof(double)*n);
  memset(y,0,sizeof(double)*n);
  c = (double *)malloc(sizeof(double)*n);
  memset(c,0,sizeof(double)*n);
  sigout = (float *)malloc(sizeof(float)*(2*cl+1));
  memset(sigout,0,sizeof(float)*(2*cl+1));
  for(i=0;i<len;i++){
    x[i]=(double)sig1[i];
    y[i]=(double)sig2[i];
  }
  gsl_fft_real_radix2_transform(&x[0], 1, n);
  gsl_fft_real_radix2_transform(&y[0], 1, n);
  c[0] = x[0]*y[0];
  c[n/2] = x[n/2]*y[n/2];
  for(i=1;i<n/2; ++i){
    c[i] = x[i]*y[i]+x[n-i]*y[n-i];
    c[n-i] = x[n-i]*y[i] - x[i]*y[n-i];
  }
  gsl_fft_halfcomplex_radix2_inverse(&c[0], 1, n);
  for(i=0;i<cl;i++){
    sigout[i]=(float)c[n-cl+i];
    sigout[cl+1+i]=(float)c[i+1];
  }
  sigout[cl]=(float)c[0];
  free(x);free(y);free(c);
  return sigout;
}


/* ----------------------------------------------------------------------
   rotate n-e into r-t using given backazimuth
   ----------------------------------------------------------------------*/
void rotate(int ndat, float* n, float* e,float* r,float* t,float baz){
  int i;
  for(i=0;i<ndat;i++){
    r[i] = -cos(baz)*n[i]-sin(baz)*e[i];
    t[i] = sin(baz)*n[i]-cos(baz)*e[i];
  }
}


/* ----------------------------------------------------------------------
   calculate distance, azimuth and backazimuth for given coordinates
   ----------------------------------------------------------------------*/
struct array delaz(float eqlat, float eqlon, float stlat, float stlon, int flag){

  float eqcolat,stcolat,cos_eq,sin_eq;
  float cos_st, sin_st, cos_eqst, sin_eqst;
  float cos_delta, sin_delta,delta;
  float az, baz,index, eps;
  struct array ret;

  if(flag==0){
    coortr(&eqlat,&eqlon,flag);
    coortr(&stlat,&stlon,flag);
  }
  eqcolat = M_PI/2.-eqlat;
  stcolat = M_PI/2.-stlat;

  cos_eq = cos(eqcolat);
  sin_eq = sin(eqcolat);
  cos_st = cos(stcolat);
  sin_st = sin(stcolat);
  cos_eqst = cos(stlon-eqlon);
  sin_eqst = sin(stlon-eqlon);

  cos_delta = cos_eq * cos_st + sin_eq * sin_st * cos_eqst;
  sin_delta = sqrt(1-cos_delta * cos_delta);
  delta = atan2(sin_delta,cos_delta);
  eps = 3.e-7;
  sin_delta = sin_delta + (sin_delta==0)*eps;

  az = asin(sin_st*sin_eqst/sin_delta);
  index = (sin_eq*cos_st - cos_eq*sin_st*cos_eqst < 0);
  az = az + index*(M_PI-2*az);
  az = az + (az<0)*2*M_PI;

  baz = asin(-sin_eq*sin_eqst/sin_delta);
  index = (cos_eq*sin_st - sin_eq*cos_st*cos_eqst < 0);
  baz = baz + index*(M_PI-2*baz);
  baz = baz + (baz<0)*2*M_PI;

  delta = delta*180/M_PI;
  az = az*180/M_PI;
  baz = baz*180/M_PI;
  ret.delta = delta;
  ret.az = az;
  ret.baz = baz;
  return ret;
  
}


/* ----------------------------------------------------------------------
   geocentric/geographic coordinate transformation
   flag == 0: input lat,lon in geographic degrees
   flag == 1: input lat,lon in geocentric radians
   ----------------------------------------------------------------------*/
void coortr(float *lat, float *lon, int flag){
  if(flag == 0){
    *lat = atan(tan(*(lat)*M_PI/180.)*0.9933056);
    *lon = *(lon)*M_PI/180.;
  }else if(flag == 1){
    *lat = atan(tan(*(lat))/0.9933056)*180./M_PI;
    *lon = *(lon)*180./M_PI;
  }
  return;
}


/* ------------------------------------------------------------------------
   create sub-directory for correlations under correlation root directory
   according to given information in sdb-structure
   --------------------------------------------------------------------- */
void make_dir(int ie, char *cordir, char *daydir){
  int month, year, day;
  year = sdb.ev[ie].yy;
  month = sdb.ev[ie].mm;
  day   = sdb.ev[ie].dd;
  char yeardir[LINEL],mondir[LINEL];
  assert((strlen(cordir)+30)<LINEL);
  sprintf(yeardir,"%s/%d",cordir,year);
  sprintf(mondir,"%s/%d",cordir,month);
  sprintf(daydir,"%s/%d_%d_%d_0_0_0",mondir,year,month,day);
  errno = 0;
  if(mkdir(cordir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",yeardir, strerror (errno));
    }
  }
  if(mkdir(yeardir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",yeardir, strerror (errno));
    }
  }
  errno = 0;
  if(mkdir(mondir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",mondir, strerror (errno));
    }
  }
  errno = 0;
  if(mkdir(daydir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",daydir, strerror (errno));
    }
  }
  return;
}


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv,char *confile)
{
  int i;

  if (argc>3){
    fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strncpy(confile,argv[++i],LINEL-1);
	break;

      case 'h':	fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
      }
    }
  }
}
