#include <iostream>
#include <iniparser.h>

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

int main(int na, char **arg[])
{
  FILE *f1,*f2,*f3;
  int N=100;
  int err[N];
  char configfile[150];
  char name[N][6];
  char stack[12][20];
  dictionary *dd;
  int i,j,k,ii,jj;

  strncpy(configfile,"./config.txt",149);
  get_args(na,arg,&configfile[0]);

//  for(i=0;i<N;i++)
//    {
//      if(fscanf(f1,"%s %d",name[i],&err[i])==EOF) break;
//      cout<<name[i]<<" "<<err[i]<<endl;
//    }
//  fclose(f1);
//  cout<<"number of stations read "<<i<<endl;
//  for(j=0;j<i-1;j++)
//    {
//      for(k=j+1;k<i;k++)
//	{
//	  f2=fopen("do_stacking_1.csh","w");
//	  fprintf(f2,"foreach var1 (Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec )\n");
//	  fprintf(f2,"cp ../$var1/5to100/COR/COR_%s_%s.SAC $var1\"_\"stack.SAC\n",name[j],name[k]);
//	  fprintf(f2,"end\n");
//	  fprintf(f2,"ls *stack.SAC > temp_stack\n");
//	  fclose(f2);
//	  //	  system("csh do_stacking_1.csh");
//	  
//	  f3=fopen("temp_stack","r");
//	  for(ii=0;ii<12;ii++)
//	    if(fscanf(f3,"%s",stack[ii])==EOF) break;
//	  fclose(f3);
//	  cout<<"number of month "<<ii<<endl;
//	  
//	  f2=fopen("do_stacking_2.csh","w");
//	  fprintf(f2,"sac << END\n");
//	  fprintf(f2,"r %s\n",stack[0]);
//	  for(jj=1;jj<ii;jj++)
//	    fprintf(f2,"addf %s\n",stack[jj]);
//	  //	  fprintf(f2,"ch b %f\n",-3000+15.930462*(err[j]-err[k]));
//	  fprintf(f2,"ch o 0\n");
//	  fprintf(f2,"w COR_%s_%s.SAC\n",name[j],name[k]);
//	  fprintf(f2,"END\n");
//	  fprintf(f2,"rm *_stack.SAC\n");
//	  fclose(f2);
//	  //	  system("csh do_stacking_2.csh");
//	}
//    }
//
//  cout<<name[0]<<"*"<<name[1]<<endl;
 
}
