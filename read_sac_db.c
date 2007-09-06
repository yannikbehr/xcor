#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mysac.h>
#include <sac_db.h>

SAC_DB sdb;

int main(int argc, char **argv){

  FILE *ff;
  char str[200];
  sprintf(str,"%ssac_db.out\0", argv[1]);
  int i;

  if((ff = fopen(str, "rb"))==NULL) {
    fprintf(stderr,"sac_db.out file not found\n");
    exit(1);
  }

  fread(&sdb, sizeof(SAC_DB), 1, ff);
  printf("%d\n",NSTATION);
  for(i=0;i<sdb.nst;i++){
    printf("%s\n",sdb.rec[0][i].resp_fname);
  }
  fclose(ff);

  return EXIT_SUCCESS;
}
