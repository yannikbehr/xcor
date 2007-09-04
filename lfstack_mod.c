#include <iostream>
#include <iniparser.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#define MODUS ,0711)

using namespace std;



/*c/////////////////////////////////////////////////////////////////////////*/
void get_args(int argc, char** argv, char *cnffile)
/*--------------------------------------------------------------------------
reading and checking commandline arguments
--------------------------------------------------------------------------*/
{
  int i;

  if (argc>3){
    fprintf(stderr,"USAGE: %s [-c alt/config.file]\n",argv[0]);
    exit(1);
  }
  /* Start at i = 1 to skip the command name. */

  for (i = 1; i < argc; i++) {

    /* Check for a switch (leading "-"). */

    if (argv[i][0] == '-') {

      /* Use the next character to decide what to do. */

      switch (argv[i][1]) {

      case 'c':	strncpy(cnffile,argv[++i],149);
	break;

      case 'h':	    fprintf(stderr,"USAGE: %s [-c alt/config.file]\n", argv[0]);
	exit(0);
	break;

      default:	fprintf(stderr,"Unknown switch %s\n", argv[i]);
	exit(1);
      }
    }
  }
}

int main(int na, char **arg)
{
  FILE *f1,*f2,*f3;
  int N=100;
  int err[N];
  char configfile[150];
  char *stations;
  char *tmpdir;
  char *rootdir;
  char *year;
  char *sacdir;
  char str[200];
  char newdir[200];
  char yearsubdir[200];
  char name[N][6];
  char stack[12][20];
  dictionary *dd;
  int i,j,k,ii,jj,m,mm;

  strncpy(configfile,"./config.txt",149);
  get_args(na,arg,&configfile[0]);
  dd = iniparser_new(configfile);
  stations = iniparser_getstr(dd, "data:stations");
  tmpdir = iniparser_getstr(dd, "database:tmpdir");
  rootdir = iniparser_getstr(dd, "database:sacdirroot");
  year = iniparser_getstr(dd, "rawdata:year");
  sacdir = iniparser_getstr(dd, "database:sacdir");
  strncpy(newdir,rootdir,199);
  strcat(newdir,year);
  strncpy(yearsubdir,newdir,199);
  strcat(newdir,"/STACK");
  if(mkdir(newdir MODUS == -1)
     printf("cannot create directory %s\n", newdir); 
  m=0;
  char *ptr;
  ptr = strtok(stations, " ");
  while(ptr != NULL) {
    strncpy(name[m],ptr,5);
    ptr = strtok(NULL, "\n\t ");
    m++;
  }
  for(i=0;i<m;i++){
    printf("%s\n",name[i]);
  }
     for(j=0;j<m-1;j++)
    {
      for(k=j+1;k<m;k++)
	{
	  f2=fopen("./do_stacking_1.csh","w");
	  fprintf(f2,"foreach var1 (Jan Feb Mar)\n");
	  fprintf(f2,"cp %s/$var1/5to100/COR/COR_%s_%s.SAC %s/$var1\"_\"stack.SAC\n",yearsubdir,name[j],name[k],newdir);
	  fprintf(f2,"end\n");
	  fprintf(f2,"ls %s/*stack.SAC > %s/temp_stack\n",newdir,newdir);
	  fclose(f2);
	  system("csh ./do_stacking_1.csh");
	  
	  sprintf(str,"%s/temp_stack",newdir);
	  f3=fopen(str,"r");
	  for(ii=0;ii<12;ii++)
	    if(fscanf(f3,"%s",stack[ii])==EOF) break;
	  fclose(f3);
	  cout<<"number of month "<<ii<<endl;
	  
	  f2=fopen("do_stacking_2.csh","w");
	  fprintf(f2,"%ssac << END\n",sacdir);
	  fprintf(f2,"r %s\n",stack[0]);
	  for(jj=1;jj<ii;jj++)
	    fprintf(f2,"addf %s\n",stack[jj]);
	  //	  fprintf(f2,"ch b %f\n",-3000+15.930462*(err[j]-err[k]));
	  fprintf(f2,"ch o 0\n");
	  fprintf(f2,"w %s/COR_%s_%s.SAC\n",newdir,name[j],name[k]);
	  fprintf(f2,"END\n");
	  fprintf(f2,"rm %s/*_stack.SAC\n",newdir);
	  fclose(f2);
	  //	  system("csh do_stacking_2.csh");
	}
    }

  cout<<name[0]<<"*"<<name[1]<<endl;
  iniparser_free(dd);
 
}
