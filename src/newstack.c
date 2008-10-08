/*--------------------------------------------------------------------------
  Program to stack monthly cross-correlations

  $Rev$
  $Author$
  $LastChangedDate$
  --------------------------------------------------------------------------*/

#define MAIN

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>
#include <iniparser.h>
#include <mysac.h>
#include <sac_db.h>

/* os-dependent includes for dir-manipulation */
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>


struct corfile {
  char path[200];
  char stationpair[200];
} COR_FILE;


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


void fill_matrix(char *filename, char *filepath, struct corfile **matrix, int row, int col);

/*--------------------------------------------------------------------------
reading and checking commandline arguments
--------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char *configfile, char *altrootdir)
{
  int i;

  if (argc>5){
    fprintf(stderr,"USAGE: %s [-c alt/config.file -r alt/root/dir]\n", argv[0]);
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

      case 'r':	strncpy(altrootdir,argv[++i],199);
	break;

      case 'h':	printf("USAGE: %s [-c alt/config.file -r alt/root/dir]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
      }
    }
  }
}


/*-------------------------------------------------------
 copy routine
 in = src-file
 out = destination-file
 -------------------------------------------------------*/
void copy(char *in, char *out)
{
  FILE *fpin = fopen(in, "rb");
  FILE *fpout = fopen(out, "wb");
  int ch;

  assert(fpin && fpout);

  printf("copy %s --> %s\n",in,out);

  while( (ch = getc(fpin)) != EOF)
    putc(ch, fpout);
  fclose(fpin);
  fclose(fpout);
}

/*------------------------------------------------------------------------
function to find all 'COR'-directories and move preliminary correlations
to final correlations
needs following headers: sys/types.h, sys/stat.h, dirent.h, string.h, 
                         stdio.h, stdlib.h
dirname = root dir to start searching
matrix  = 2-D array to store the correlation-file paths
row     = number of station pairs
col     = number of correlations for each station pair
------------------------------------------------------------------------*/
int find_correl(char *dirname, struct corfile **matrix, int row, int col)
{
  DIR *dir, *dir2;
  struct dirent *dirpointer, *dirpointer2;
  struct stat attribut;
  char tmp[200],oldname[200],newname[200];
  char *cutptr;

  /* open directory */
  if((dir=opendir(dirname)) == NULL) {
    fprintf(stderr,"ERROR in opendir ...\n");
    return EXIT_FAILURE;
  }
  /* read directory and recursive call of this function to find 
     'COR'-dirs*/
  while((dirpointer=readdir(dir)) != NULL){
    strncpy(tmp,dirname,199);
    strcat(tmp,(*dirpointer).d_name);
    if(stat(tmp, &attribut) == -1){
      fprintf(stderr,"ERROR in stat ...\n");
      return EXIT_FAILURE;
    }

    /* if directory entry name is 'COR' and is a directory than move
       all preliminery correlations to final ones*/
    if(strcmp((*dirpointer).d_name,"COR")==0 && attribut.st_mode & S_IFDIR){
      if((dir2=opendir(tmp)) == NULL) {
	fprintf(stderr,"ERROR in opendir ...\n");
	return EXIT_FAILURE;
      }
      while((dirpointer2=readdir(dir2)) != NULL){
	strncpy(oldname,tmp,199);
	strcat(oldname,"/");
	strcat(oldname,(*dirpointer2).d_name);
	if(stat(oldname, &attribut) == -1){
	  fprintf(stderr,"ERROR in stat ...\n");
	  return EXIT_FAILURE;
	}
	if(attribut.st_mode & S_IFREG && strstr((*dirpointer2).d_name,"COR_") != NULL){
	  fill_matrix(dirpointer2->d_name, oldname, matrix, row, col);
	}
      }

      if(closedir(dir2) == -1)
	printf("ERROR while closing\n");
	
      /* else if dir-entry is directory, function calls itself again */
    }else if(attribut.st_mode & S_IFDIR && strcmp((*dirpointer).d_name,".") != 0 && strcmp((*dirpointer).d_name,"..") != 0){
      strcat(tmp,"/");
      find_correl(tmp,matrix,row,col);
    }
  }
  /* close directory */
  if(closedir(dir) == -1)
    printf("ERROR while closing %s\n", dirname);
  return EXIT_SUCCESS;
}



/*------------------------------------------------------------------------
function to fill the 2-D array that holds the correlation-file paths
filename = the file's basename
filepath = the full path of the file
matrix   = 2-D array to store the correlation-file paths
row      = number of station pairs
col      = number of correlations for each station pair
------------------------------------------------------------------------*/
void fill_matrix(char *filename, char *filepath, struct corfile **matrix, int row, int col)
{
  int i, j;

  for(i=0;i<row;i++){
    if(strcmp(matrix[i][0].stationpair,filename)==0){
      for(j=0;j<col;j++){
	if(strcmp(matrix[i][j].path,filepath)==0){
	  break;
	}else if(strcmp(matrix[i][j].path,"dummy")==0){
	  strncpy(matrix[i][j].stationpair,filename,199);
	  strncpy(matrix[i][j].path,filepath,199);
	  break;
	}
      }
    }else if(strcmp(matrix[i][0].stationpair,"dummy")==0){
      strncpy(matrix[i][0].stationpair,filename,199);
      strncpy(matrix[i][0].path,filepath,199);
      break;
    }
   }
}


/*--------------------------------------------------------------------
stacking of the found correlation-files
rootdir = dir that holds the 'STACK' directory
sacdir  = path to sac executables
matrix   = 2-D array that stores the correlation-file paths
row      = number of station pairs
col      = number of correlations for each station pair
---------------------------------------------------------------------*/
void stack(char *rootdir, char *sacdir, struct corfile **matrix, int row, int col)
{
  FILE *f3, *f2;
  float stackcnt;
  int i, ii, j;
  char newdir[200], newfile[200], command[200], str[200], buf[3];
  char **stack;
  static SAC_HD shd;

  strncpy(newdir,rootdir,199);
  strcat(newdir,"STACK");
  if(mkdir(newdir ,0711) == -1)
    fprintf(stderr,"cannot create directory %s\n", newdir); 

  for(i=0;i<row;i++){
    j=0;
    while(strcmp(matrix[i][j].path,"dummy")!=0){
      strncpy(newfile,newdir,199);
      strcat(newfile,"/");
      strcat(newfile,matrix[i][j].stationpair);
      strcat(newfile,"_stack");
      sprintf(buf,"%d",j);
      strcat(newfile,buf);
      copy(matrix[i][j].path,newfile);
      j++;
    }

  stack = (char **)malloc(j * sizeof(char *));
  if(NULL == stack) {
    printf("no more virtuel RAM available ... !");
    return;
  }

  for(ii = 0; ii < j; ii++) {
    stack[ii] = (char *)malloc(sizeof(char[200]));
    if(NULL == stack[ii]) {
      printf("no more storage for line %d\n",i);
      return;
    }
  }
  sprintf(command,"ls  %s/*_stack* > %s/temp_stack\n", newdir, newdir);
  system(command);
  
  sprintf(str,"%s/temp_stack",newdir);
  f3=fopen(str,"r");
  for(ii=0;ii<j;ii++)
    if(fscanf(f3,"%s",stack[ii])==EOF) break;
  fclose(f3);
  printf("number of months %d\n",ii);
  
  f2=fopen("do_stacking.csh","w");
  fprintf(f2,"%ssac << END >/dev/null\n",sacdir);
  fprintf(f2,"r %s\n",stack[0]);
  if( read_sac_header(stack[0],&shd)==NULL){
    fprintf(stderr,"file %s not found\n", stack[0]);
    return;
  }
  stackcnt = shd.unused1;
  for(ii=1;ii<j;ii++){
    fprintf(f2,"addf %s\n",stack[ii]);
    if( read_sac_header(stack[ii],&shd)==NULL){
      fprintf(stderr,"file %s not found\n", stack[0]);
      return;
    }
    stackcnt = stackcnt+shd.unused1;
  }
  fprintf(f2,"ch mag %f\n",stackcnt);
  fprintf(f2,"ch o 0\n");
  fprintf(f2,"w %s/%s\n",newdir, matrix[i][0].stationpair);
  fprintf(f2,"END\n");
  fprintf(f2,"rm %s/*_stack*\n",newdir);
  fclose(f2);
  system("csh do_stacking.csh");
  system("rm do_stacking.csh");
  
  for(ii=0;ii<j;ii++)
    free(stack[ii]);
  free(stack);
  
  }

}



int main(int argc, char **argv)
{
  FILE *ff;
  int row, col, i, j;
  char configfile[200], str[200], newdir[200];
  char *sacdir, *tmpdir, *rootdir;
  char altrootdir[200];
  struct corfile **matrix;
  dictionary *dd;
  static SAC_DB sdb;

  strncpy(configfile,"./config.txt",199);
  strncpy(altrootdir,"dummy",199);
  get_args(argc,argv,configfile,altrootdir);
  dd = iniparser_new(configfile);
  tmpdir = iniparser_getstr(dd, "stack:tmpdir");
  sacdir = iniparser_getstr(dd, "stack:sacdir");
  if(strcmp(altrootdir,"dummy")==0){
    rootdir = iniparser_getstr(dd, "stack:cordir");
  }else{
    rootdir=&altrootdir[0];
  }
  sprintf(str,"%ssac_db.out\0", tmpdir);

  ff = fopen(str,"rb");
  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  if(sdb.nst <=2){
    row = 1;
  }else{
    row = sdb.nst*(sdb.nst-1)/2;
  }
  col = 25;  /* Attention: hard-wired to not more than 2 years of data  */

  matrix = (struct corfile **)malloc(row * sizeof(struct corfile *));
   if(NULL == matrix) {
      printf("no more virtuel RAM available ... !");
      return EXIT_FAILURE;
   }

   for(i = 0; i < row; i++) {
      matrix[i] = (struct corfile *)malloc(col * sizeof(struct corfile));
         if(NULL == matrix[i]) {
            printf("no more storage for line %d\n",i);
            return EXIT_FAILURE;
         }
	 
   }

   for(i=0;i<row;i++){
     for(j=0;j<col;j++){
       strncpy(matrix[i][j].path,"dummy",199);
       strncpy(matrix[i][j].stationpair,"dummy",199);
     }
   }


  find_correl(rootdir,matrix, row, col);
  stack(rootdir,sacdir,matrix,row,col);
  iniparser_free(dd);

#ifdef DEBUG
  for(i=0;i<row;i++){
    for(j=0;j<col;j++){
      printf("entry in row %d and column %d is:\n",i,j);
      printf("-->path: %s, station pair: %s\n",matrix[i][j].path,matrix[i][j].stationpair );
    }
  }
  printf("Number of stations is: %d\n",sdb.nst);
#endif

  for(i = 0; i < row; i++)
    free(matrix[i]);
  free(matrix);
  return EXIT_SUCCESS;  
}

