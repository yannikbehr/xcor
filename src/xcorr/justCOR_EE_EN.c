/*--------------------------------------------------------------------------
  program to correlate sac-files:
  -reads in sac_db.out file
  -correlation of .am and .ph files in frequ.-domain
  -stacking correlations for one month
  -reads variable 'sacdirroot' from config file

  written by Fan Chi ????
  $Rev: 454 $
  $Author$
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
#include <errno.h>

#define MODUS 0711
#define LINEL 300

/* Function prorotypes */
void dcommon_(int *len, float *amp,float *phase);
void dmultifft_(int *len,float *amp,float *phase, int *lag,float *seis_out, int *ns);
int check_info (int ne, int ns1, int ns2 );
int do_cor(int lag, char *cordir,char *pbdir, char *prefix);
void sac_db_chng (char *pbdir);
void get_args(int argc, char** argv);
//int find_n_comp(char *nameE, char *nameN);
int find_n_comp(char *nameE, char *nameN, char *pbdir,char *prefix, int ne,int ns);
int check_exist(char *nameE, char *nameN);
void make_dir(int ie, char *cordir, char *pbdir, char *daydir);
  //static int glob_this(const char *fpath, const struct stat *sb,
  //		     int tflag, struct FTW *ftwbuf);

SAC_DB sdb;
float amp[900000], phase[900000], cor[900000];
float seis_out[2000000];

/*c/////////////////////////////////////////////////////////////////////////*/
int main (int na, char **arg)
{
  FILE *ff;
  int lag;
  //int flags = 1;
  char str[LINEL];
  dictionary *dd;
  char *tmpdir, *pbdir, *cordir, *sacdbname, *prefix;
  strcpy(sdb.conf,"./config.txt");

  get_args(na, arg);

  /* OPEN SAC DATABASE FILE AND READ IN TO MEMORY */
  dd         = iniparser_new(sdb.conf);
  tmpdir     = iniparser_getstr(dd, "xcor:tmpdir");
  cordir     = iniparser_getstr(dd, "xcor:cordir");
  lag        = iniparser_getint(dd, "xcor:lag", 3000);
  pbdir      = iniparser_getstr(dd, "xcor:pbdir");
  sacdbname  = iniparser_getstr(dd, "xcor:dbname");
  prefix     = iniparser_getstr(dd, "xcor:prefix");

  assert((strlen(tmpdir)+strlen(sacdbname)+1) < LINEL);
  sprintf(str,"%s/%s", tmpdir,sacdbname);
  ff = fopen(str,"rb");
  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  /* change ft_fname value in sdb-struct */
  sac_db_chng(pbdir);

  /*do all the work of correlations here  */
  do_cor(lag,cordir,pbdir,prefix);  
  printf("correlations finished\n");
  iniparser_free(dd);
  return 0;

  /* move COR/COR_STA1_STA2.SAC_EE.prelim to COR/COR_STA1_STA2.SAC_EE etc. */
  /*if (nftw(cordir, glob_this, 20, flags) == -1) {
      perror("nftw");
      exit(EXIT_FAILURE);
      }*/

}


///*------------------------------------------------------------ 
// *  call-back function for nftw()
//  ------------------------------------------------------------*/
//static int glob_this(const char *fpath, const struct stat *sb,
//		     int tflag, struct FTW *ftwbuf){
//  const char pattern[] = "*.prelim";
//  char localpattern[LINEL];
//  char *newname, *ptr;
//  glob_t match;
//  int j;
//
//  assert((strlen(fpath)+strlen(pattern))<LINEL-1);
//  sprintf(localpattern,"%s/%s",fpath, pattern);
//
//  if(glob(localpattern, 0, NULL, &match) == 0){
//      for(j=0;j<match.gl_pathc;j++){
//	newname = strdup(match.gl_pathv[j]);
//	ptr = strrchr(newname,'.');
//	*(ptr) = '\0';
//	printf("--> rename %s to %s\n", match.gl_pathv[j], newname);
//	if( (rename(match.gl_pathv[j],newname)) < 0) {
//	  fprintf(stderr, "---->ERROR while renaming");
//	  return EXIT_FAILURE;
//	}
//	free(newname);
//      }
//  }
//  globfree(&match);
//  return 0;
//}


/*----------------------------------------------------------------------------
  evaluate ne, ns1, ns2 against SAC_DB values
  ne  = number of event
  ns1 = number of first station
  ns2 = number of second station
  ----------------------------------------------------------------------------*/
int check_info (int ne, int ns1, int ns2 )
{
  if ( ne >= sdb.nev ) {
    fprintf(stderr,"cannot make correlation: too large event number\n");
    return 0;
  }
  if ( (ns1>=sdb.nst) ||(ns2>=sdb.nst)  ) {
    fprintf(stderr,"cannot make correlation: too large station number\n");
    return 0;
  }
  if ( sdb.rec[ne][ns1].n <= 0 ) {
    fprintf(stdout,"no data for station %s and event %s\n", sdb.st[ns1].name, sdb.ev[ne].name );
    return 0;
  }
  if ( sdb.rec[ne][ns2].n <= 0 ) {
    fprintf(stdout,"no data for station %s and event %s\n", sdb.st[ns2].name, sdb.ev[ne].name );
    return 0;
  }
  if ( fabs(sdb.rec[ne][ns1].dt-sdb.rec[ne][ns2].dt) > .0001 ) {
    fprintf(stderr,"incompatible DT\n");
    return 0;
  }
  return 1;
}

/*c/////////////////////////////////////////////////////////////////////////*/
float sig[1000000];
SAC_HD shdamp1, shdph1, shdamp2, shdph2, shd_cor;

/*----------------------------------------------------------------------------
  correlation in frequ.-domain
  lag    = half length of correlation window
  cordir = directory for correl. results
  sdb    = SAC_DB structure with trace information

  calls fortran subroutines:
  -dcommon
  -dmultifft
  ----------------------------------------------------------------------------*/
int do_cor(int lag , char *cordir, char *pbdir, char *prefix)
{
  int ine, jsta1, jsta2;

  int len,ns,i, comp; 


  char filename[LINEL];
  char amp_sac[LINEL], phase_sac[LINEL];
  char amp_sac1E[LINEL], phase_sac1E[LINEL];

  char amp_sac1N[LINEL], phase_sac1N[LINEL];
  char amp_sac2E[LINEL], phase_sac2E[LINEL];
  char amp_sac2N[LINEL], phase_sac2N[LINEL];
  char name1_N[LINEL],name1_E[LINEL];
  char name2_N[LINEL],name2_E[LINEL]; 
  //char *buf, *month, *year;
  //char yeardir[LINEL];
  char mondir[LINEL];
  /*  float amp[400000], phase[400000], cor[400000];
      float seis_out[400000];*/

  /*outermost loop over day number, then station number*/
  for( ine = 0; ine < sdb.nev; ine++ ) {
    fprintf(stdout,"event number %d\n",ine);
    make_dir(ine,cordir,pbdir,mondir);

    /* move and rename cor file accordingly 
       extract location for correlations
       and create COR-dir if necessary   */
    /*loop over "base" station number, this will be stored into common memory*/
    for( jsta1 = 0; jsta1 < sdb.nst; jsta1++ ) {  
      if(!(sdb.rec[ine][jsta1].n > 0)) continue;
      strcpy(name1_E,sdb.rec[ine][jsta1].ft_fname);
      if(!find_n_comp(name1_E,name1_N,pbdir,prefix,ine,jsta1)) continue;
      sprintf( amp_sac1E, "%s.am", name1_E );
      sprintf( phase_sac1E, "%s.ph", name1_E );
      sprintf( amp_sac1N, "%s.am", name1_N );
      sprintf( phase_sac1N, "%s.ph", name1_N );

      /* loop over second station */
      for( jsta2 = (jsta1+1); jsta2 < sdb.nst; jsta2++ ){
	if(!check_info(ine, jsta1, jsta2 )) continue;
	if(!(sdb.rec[ine][jsta2].n > 0)) continue;
	strcpy(name2_E,sdb.rec[ine][jsta2].ft_fname);
	if(!find_n_comp(name2_E,name2_N,pbdir,prefix,ine,jsta2)) continue;

	sprintf( amp_sac2E, "%s.am", name2_E );
	sprintf( phase_sac2E, "%s.ph", name2_E );
	sprintf( amp_sac2N, "%s.am", name2_N );
	sprintf( phase_sac2N, "%s.ph", name2_N );
	//fprintf(stdout,"xcor: %s %s %s %s\n", name1_E,name1_N,name2_E,name2_N);

	/* compute correlation */
	for(comp=0;comp<4;comp++){   
	  if(comp==0||comp==1){
	    sprintf( amp_sac, "%s.am", name1_E );
	    sprintf( phase_sac, "%s.ph", name1_E );
	  }else{
	    sprintf( amp_sac, "%s.am", name1_N );
	    sprintf( phase_sac, "%s.ph", name1_N );
	  }
	  // read amp and phase files and read into common memory
	  if ( read_sac(amp_sac, amp, &shdamp1, 9000000 )==NULL ){
	    fprintf(stderr,"ERROR: cannot read  %s\n", amp_sac );
	    return 0;
	  }
	  if ( read_sac(phase_sac, phase, &shdph1, 9000000)== NULL ){
	    fprintf(stderr,"ERROR: cannot read  %s\n", phase_sac );
	    return 0;
	  }
	  len = shdamp1.npts;
	  dcommon_( &len, amp, phase ); // reads amp and phase files into common memory
	  
	  if(comp==0||comp==2){
	    sprintf(amp_sac, "%s.am", name2_E);
	    sprintf(phase_sac, "%s.ph", name2_E);
	  }else{
	    sprintf(amp_sac, "%s.am", name2_N);
	    sprintf(phase_sac, "%s.ph", name2_N);
	  }
	  // get array of floats for amp and phase of first signal
	  if ( read_sac(amp_sac, amp, &shdamp2, 9000000) ==NULL ){
	    fprintf(stderr,"ERROR: cannot read  %s\n", amp_sac );
	    return 0;
	  }
	  if ( read_sac(phase_sac, phase, &shdph2, 9000000)==NULL ){
	    fprintf(stderr,"ERROR: cannot read  %s\n", phase_sac );
	    return 0;
	  }

	  len = shdamp2.npts;
	  dmultifft_(&len, amp, phase, &lag, seis_out,&ns);
	  cor[lag] = seis_out[0];
	  for( i = 1; i< (lag+1); i++){ 
	    cor[lag-i] =  seis_out[i];
	    cor[lag+i] =  seis_out[ns-i];
	  }
	  
	  /*move and rename cor file accordingly */
	  if(comp==0){
	    sprintf(filename, "%s/COR_%s_%s.SAC_EE",
		    mondir, sdb.st[jsta1].name, sdb.st[jsta2].name);
	  }else if(comp==1){
	    sprintf(filename, "%s/COR_%s_%s.SAC_EN",
		    mondir, sdb.st[jsta1].name, sdb.st[jsta2].name);
	  }else if(comp==2){
	    sprintf(filename, "%s/COR_%s_%s.SAC_NE",
		    mondir, sdb.st[jsta1].name, sdb.st[jsta2].name);
	  }else{
	    sprintf(filename, "%s/COR_%s_%s.SAC_NN",
		    mondir, sdb.st[jsta1].name, sdb.st[jsta2].name);
	  }

	 
	  shdamp1.delta = sdb.rec[ine][jsta1].dt;
	  shdamp1.evla =  sdb.st[jsta1].lat;
	  shdamp1.evlo =  sdb.st[jsta1].lon;
	  shdamp1.stla =  sdb.st[jsta2].lat;
	  shdamp1.stlo =  sdb.st[jsta2].lon;
	  shdamp1.npts =  2*lag+1;
	  shdamp1.b    = -(lag)*shdamp1.delta;
	  shdamp1.user9=  shdamp2.cmpaz;
	  shdamp1.unused1 = 1;
	  strncpy(shdamp1.kevnm,sdb.st[jsta1].name,7);
	  strncpy(shdamp1.kstnm,sdb.st[jsta2].name,7);
	  fprintf(stderr,"%s %d %s\n",filename,ine,sdb.ev[ine].name);
	  write_sac (filename, cor, &shdamp1);
	}    //loop over comp
      }   //loop over jsta2
    }  //loop over jsta1
  //    free(buf);free(month);free(year);
  }  //loop over events
  return 1;
}


/*--------------------------------------------------------------------------
insert sub-dirname 'pbdir' into sac_db entry 'ft_fname';
previous changes in the overall program structure makes it necessary
--------------------------------------------------------------------------*/
void sac_db_chng (char *pbdir )

{
  int ie, is;
  char *filename, *day,*month,*year,*cp,*ptr;


  for ( ie = 0; ie < sdb.nev; ie++ ) for ( is = 0; is < sdb.nst; is++ )
    {
      if(sdb.rec[ie][is].ft_fname == NULL){
	continue;
      }else if(!strncmp(sdb.rec[ie][is].ft_fname,"\0",1)){
	continue;
      }else {
	/*cut off the last for parts of the path*/
	cp = strdup(sdb.rec[ie][is].ft_fname);
	ptr=strrchr(cp,'/');
	if(ptr != NULL){
	    filename = strdup(ptr);
	    *(ptr)='\0';
	    ptr=strrchr(cp,'/');
	    day = strdup(ptr);
	    *(ptr)='\0';
	    ptr = strrchr(cp,'/');
	    month = strdup(ptr);
	    *(ptr)='\0';
	    ptr = strrchr(cp,'/');
	    year = strdup(ptr);
	    *(ptr)='\0';
	    ptr = strrchr(cp,'/');
	    *(ptr)='\0';
	}
	/* put path together and put in pass-band dir */
	sprintf(sdb.rec[ie][is].ft_fname,"%s/%s%s%s%s%s",
		cp,pbdir,year,month,day,filename);
	printf("%s\n",sdb.rec[ie][is].ft_fname);
	free(filename);
	free(day);
	free(month);
	free(year);
	free(cp);
      }
    }
  return;
}

/*--------------------------------------------------------------------------
  insert sub-dirname 'pbdir' into sac_db entry 'ft_fname';
  previous changes in the overall program structure makes it necessary
  --------------------------------------------------------------------------*/
//void sac_db_chng (char *pbdir )
//
//{
//  int ie, is;
//  char *result, *filename, *daydir;
//
//  for ( ie = 0; ie < sdb.nev; ie++ ) for ( is = 0; is < sdb.nst; is++ )
//    {
//      if(sdb.rec[ie][is].ft_fname == NULL){
//	printf("ERROR: ft_fname not found\n");
//      }else {
//	result=strrchr(sdb.rec[ie][is].ft_fname,'/');
//	if(result != NULL){
//	  filename = strdup(result);
//	  *(result)='\0';
//	  result=strrchr(sdb.rec[ie][is].ft_fname,'/');
//	  daydir = strdup(result);
//	  *(result+1)='\0';
//	  strcat(sdb.rec[ie][is].ft_fname,pbdir);
//	  strcat(sdb.rec[ie][is].ft_fname,daydir);
//	  strcat(sdb.rec[ie][is].ft_fname,filename);
//	  printf("dir is: %s\n",sdb.rec[ie][is].ft_fname);
//	}else {
//	  continue;
//	}
//	free(filename);
//	free(daydir);
//      }
//    }
//  return;
//}

/*--------------------------------------------------------------------------
  function to find East-, North- and Z-component files for given date-dir
   ------------------------------------------------------------------------*/
int find_n_comp(char *nameE, char *nameN, char *pbdir,char *prefix, int ne,int ns){
  char *dircp, *dirn, *base, *basecp;
  char pattern[LINEL], newdir[LINEL];
  glob_t match;
  dircp = strdup(sdb.rec[ne][ns].ft_fname);
  basecp = strdup(sdb.rec[ne][ns].ft_fname);
  dirn = dirname(dircp);
  base = basename(basecp);
  //assert((strlen(dirn)+strlen(pbdir)+strlen(base)+2)<LINEL-1);
  //sprintf(newdir,"%s/%s/%s",dirn,pbdir,base);
  
  /* find N-component file*/
  //assert((strlen(newdir)+strlen(prefix)+strlen(sdb.st[ns].name)+11)<LINEL-1);
  sprintf(pattern,"%s/%s_%s.*HN.SAC",dirn,prefix,sdb.st[ns].name);
  if(glob(pattern, 0, NULL, &match) == 0){
    if(match.gl_pathc>1){
      fprintf(stderr,"WARNING: found more than 1 matching file for %s\n",pattern);
      return 0;
    }else{
      strncpy(nameN,match.gl_pathv[0],LINEL-1);
    }
  }else{
    fprintf(stderr,"ERROR: no matching file found for %s\n",pattern);
    return 0;
  }
  
  printf("%s %s %s %d\n",nameE,nameN,pattern,glob(pattern, 0, NULL, &match));

  globfree(&match);
  free(dircp);
  free(basecp);
  return 1;
}



//
///*--------------------------------------------------------------------------
//  function to construct North-component filename 
//  from given East-component filename 
//   ------------------------------------------------------------------------*/
//int find_n_comp(char *nameE, char *nameN){
//  char pattern[]="(.*/ft_.{1,4}[.])(.{1,3})([.]SAC.*)";
//  regmatch_t submatch[4];
//  regex_t *regexpr;
//  char *filename, *cmp, *start, *end;
//  char ncmp[4];
//  int err, i;
//  filename = strdup(nameE);
//  regexpr = (regex_t *)malloc(sizeof(regex_t));
//  memset(regexpr, 0, sizeof(regex_t));
//  /* Compile the regex */
//  err = regcomp(regexpr,pattern, REG_EXTENDED);
//  if(err!=0){
//    fprintf(stderr,"ERROR: in regular expression %s!\n", pattern);
//    regfree(regexpr);
//    return 0; 
//  }
//  /* extract all the matches */
//  if(regexec( regexpr,filename,regexpr->re_nsub+1, submatch, 0)== 0){
//    start = strdup(filename);
//    memcpy(start,filename,submatch[1].rm_eo);
//    *(start+submatch[1].rm_eo) = '\0';
//
//    cmp = strdup(filename+submatch[2].rm_so);
//    memcpy(cmp,filename+submatch[2].rm_so,submatch[2].rm_eo-submatch[2].rm_so);
//    *(cmp+(submatch[2].rm_eo-submatch[2].rm_so)) = '\0';
//
//    end = strdup(filename+submatch[3].rm_so);
//    memcpy(end,filename+submatch[3].rm_so,submatch[3].rm_eo-submatch[3].rm_so);
//    *(end+(submatch[3].rm_eo-submatch[3].rm_so)) = '\0';
//
//    for(i=0;i<3;i++){
//      if(cmp[i]=='E'){
//	ncmp[i]='N';
//      }else{
//	ncmp[i]=cmp[i];
//      }
//    }
//    ncmp[3] = '\0';
//    assert((strlen(start)+strlen(ncmp)+strlen(end))<100);
//    sprintf(nameN,"%s%s%s",start,ncmp,end);
//    printf("%s\n",nameN); 
//    free(start);free(cmp);free(end);
//  }else{
//    fprintf(stderr,"ERROR: no match for regular expression %s\n",pattern);
//    return 0;
//  }
//  regfree(regexpr);
//  free(filename);
//  if(!check_exist(nameE,nameN)) return 0;
//  return 1;
// 
//} 


/*--------------------------------------------------------------------------
  check for existence of filenames constructed by 'find_n_comp'
  ------------------------------------------------------------------------*/
int check_exist(char *nameE, char *nameN){
  char buffer[LINEL];
  if(access(nameN, F_OK) != 0){
    fprintf(stderr,"WARNING: cannot find %s\n",nameN);
    return 0;
  }
  if(access(nameE, F_OK) != 0){
    fprintf(stderr,"WARNING: cannot find %s\n",nameE);
    return 0;
  }
  sprintf( buffer, "%s.am", nameE );
  if(access(buffer, F_OK) != 0){
    fprintf(stderr,"WARNING: cannot find %s\n",buffer);
    return 0;
  }
  sprintf( buffer, "%s.ph", nameE );
  if(access(buffer, F_OK) != 0){
    fprintf(stderr,"WARNING: cannot find %s\n",buffer);
    return 0;
  }
  sprintf( buffer, "%s.am", nameN );
  if(access(buffer, F_OK) != 0){
    fprintf(stderr,"WARNING: cannot find %s\n",buffer);
    return 0;
  }
  sprintf( buffer, "%s.ph", nameN );
  if(access(buffer, F_OK) != 0){
    fprintf(stderr,"WARNING: cannot find %s\n",buffer);
    return 0;
  }
  return 1;
}


/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv)
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

      case 'c':	strcpy(sdb.conf,argv[++i]);
	break;

      case 'h':	fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
      }
    }
  }
}



/* ------------------------------------------------------------------------
   create sub-directory for correlations under correlation root directory
   according to given information in sdb-structure
   --------------------------------------------------------------------- */
void make_dir(int ie, char *cordir, char *pbdir, char *daydir){
  int month, year, day;
  char months[12][4] = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
  year = sdb.ev[ie].yy;
  month = sdb.ev[ie].mm;
  day   = sdb.ev[ie].dd;
  char yeardir[LINEL],mondir[LINEL],bnddir[LINEL];
  assert((strlen(cordir)+40)<LINEL);
  sprintf(bnddir,"%s/%s",cordir,pbdir);
  sprintf(yeardir,"%s/%d",bnddir,year);
  sprintf(mondir,"%s/%s",yeardir,months[month-1]);
  sprintf(daydir,"%s/%d_%d_%d_0_0_0",mondir,year,month,day);
  errno = 0;
  if(mkdir(cordir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",cordir, strerror (errno));
    }
  }
  if(mkdir(bnddir, MODUS) == -1){
    if(errno != EEXIST){
      fprintf(stderr, "Couldn't create directory %s; %s\n",bnddir, strerror (errno));
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

