#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mysac.h>
#include <sac_db.h>

#define STRING 200

void get_args(int argc, char** argv, char *filename);
void print_sac_db(SAC_DB *sdb);

/*--------------------------------------------------------------------------
  reading and checking commandline arguments
  --------------------------------------------------------------------------*/
void get_args(int argc, char** argv, char *filename){

  int i;

  if (argc != 3 ){
    fprintf(stderr,"USAGE: %s -f input sac_db file\n", argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'f':	strncpy(filename,argv[++i],STRING-1);
	break;

      case 'h': 
	printf("USAGE: %s -f input sac_db file\n", argv[0]);
	printf("-------------------------------\n");
	printf("program to read sac_db file:\n");
	printf("-->output on stdout\n");
	
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}

void print_sac_db(SAC_DB *sdb){

  int i,j;  

  for(i=0;i<sdb->nst;i++){
    printf("station number %d is %s\n",i,sdb->st[i].name);
  }
  for(i=0;i<=sdb->cntev;i++){
    for(j=0;j<sdb->nst;j++){
      printf("event number: %d   station number: %d\n", i,j);
      printf("--> station name       :%s\n", sdb->st[j].name);
      printf("--> eventname          :%s\n", sdb->ev[i].name);
      printf("--> channel name       :%s\n", sdb->rec[i][j].chan);
      printf("--> sample interval    :%f\n", sdb->rec[i][j].dt);
      printf("--> julian day         :%d\n", sdb->ev[i].jday);
      printf("--> month              :%d\n", sdb->ev[i].mm);
      printf("--> month day          :%d\n", sdb->ev[i].dd);
      printf("--> hour               :%d\n", sdb->ev[i].h);
      printf("--> minute             :%d\n", sdb->ev[i].m);
      printf("--> second             :%d\n", sdb->ev[i].s);
      printf("--> millisecond        :%d\n", sdb->ev[i].ms);
      printf("--> absolute time      :%f\n", sdb->rec[i][j].t0);
      printf("--> number of points   :%d\n", sdb->rec[i][j].n);
      printf("--> record name        :%s\n", sdb->rec[i][j].fname);
      printf("--> record ft-name     :%s\n", sdb->rec[i][j].ft_fname);
      printf("--> response filename  :%s\n", sdb->rec[i][j].resp_fname);
    }
  }

}

int main(int argc, char **argv){

  FILE *ff;
  char filename[STRING];
  static SAC_DB sdb;
  int i;

  strncpy(filename,"./sac_db.out",STRING-1);
  get_args(argc,argv,filename);

  if((ff = fopen(filename, "rb"))==NULL) {
    fprintf(stderr,"sac_db  file not found\n");
    exit(1);
  }


  fread(&sdb, sizeof(SAC_DB), 1, ff);
  fclose(ff);

  print_sac_db(&sdb);

  return EXIT_SUCCESS;
}
