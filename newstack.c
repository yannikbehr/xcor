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

void fill_matrix(char *filename, char *filepath, struct corfile **matrix, int row, int col);

/*--------------------------------------------------------------------------
reading and checking commandline arguments
--------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char *configfile)
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

      case 'c':	strncpy(configfile,argv[++i],199);
	break;

      case 'h':	printf("USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
      }
    }
  }
}


/*------------------------------------------------------------------------
function to find all 'COR'-directories and move preliminary correlations
to final correlations
needs following headers: sys/types.h, sys/stat.h, dirent.h, string.h, 
                         stdio.h, stdlib.h
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
      printf("working on: %s\n",tmp);
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



void fill_matrix(char *filename, char *filepath, struct corfile **matrix, int row, int col)
{
  int i;

  printf("-->found correl-file: %s\n",filepath);

  for(i=0;i<row;i++){
    if(strcmp(matrix[i][0].stationpair,filename)==0)
      printf("-->number of row is: %d\n",i);
    break;
   }
}
int main(int argc, char **argv)
{
  FILE *ff;
  int row, col, i, j;
  char configfile[200], str[200];
  char *sacdirroot;
  char *tmpdir;
  struct corfile **matrix;
  dictionary *dd;
  static SAC_DB sdb;

  strncpy(configfile,"./config.txt",199);
  get_args(argc,argv,configfile);
  dd = iniparser_new(configfile);
  tmpdir = iniparser_getstr(dd, "database:tmpdir");
  sprintf(str,"%ssac_db.out\0", tmpdir);

  ff = fopen(str,"rb");
  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  row = (sdb.nst+1)*(sdb.nst)/2;
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

   /*   for(i=0;i<row;i++){
     for(j=0;j<col;j++){
       printf("Eintrag in Zeile %d und Spalte %d ist:\n",i,j);
       printf("-->Path: %s, Station Pair: %s\n",matrix[i][j].path,matrix[i][j].stationpair );
	 }
   }
   */
  sacdirroot = iniparser_getstr(dd, "database:sacdirroot");

  find_correl(sacdirroot,matrix, row, col);
  iniparser_free(dd);
  for(i = 0; i < row; i++)
    free(matrix[i]);
  free(matrix);
  return EXIT_SUCCESS;  
}

