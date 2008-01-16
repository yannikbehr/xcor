#include <string.h>
#include <stdio.h>
#include <mysac.h>
#include <sac_db.h>


void sac_db_chng ( SAC_DB *sdb, char *fname,char *pbdir )
/*--------------------------------------------------------------------------
insert sub-dirname 'pbdir' into sac_db entry 'ft_fname'
--------------------------------------------------------------------------*/

{
  int ie, is, k, j;
  char *result;
  char filename[20], daydir[20];

  for ( ie = 0; ie < sdb->nev; ie++ ) for ( is = 0; is < sdb->nst; is++ )
    {
      if(sdb->rec[ie][is].ft_fname == NULL){
	printf("ERROR: ft_fname not found\n");
      }else {
	result=strrchr(sdb->rec[ie][is].ft_fname,'/');
	if(result != NULL){
	  strcpy(filename,result);
	  *(result)='\0';
	  result=strrchr(sdb->rec[ie][is].ft_fname,'/');
	  strcpy(daydir,result);
	  *(result+1)='\0';
 	  strcat(sdb->rec[ie][is].ft_fname,pbdir);
 	  strcat(sdb->rec[ie][is].ft_fname,daydir);
	  strcat(sdb->rec[ie][is].ft_fname,filename);
	  printf("dir is: %s\n",sdb->rec[ie][is].ft_fname);
	}else {
	  continue;
	}
      }
    }
  return;
}
      


int main(){

  FILE *ff, *fi;
  char str[] = "./sac_db_test.out";
  SAC_DB sdb;
  char pbdir[] = "5to100";



  ff = fopen(str,"rb");
  fread(&sdb, sizeof(SAC_DB), 1, ff );
  fclose(ff);

  sac_db_chng ( &sdb, str , pbdir);
  /*  fi = fopen(str,"wb");
  fwrite(&sdb, sizeof(SAC_DB), 1, fi );
  fclose(fi);*/

  return 0;
}
