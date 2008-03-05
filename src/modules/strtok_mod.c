#include <stdio.h>              
#include <stdlib.h>                    
#include <string.h>                    
#define LINEL 300

int strtok_mod(char *string, char c, char tokens[][LINEL], int* nwords);

/*                                               
*int main(){
*  
*  int  i=0;
*  int  nwords = 10;
*  char tokens[nwords][LINEL];                              
*  strtok_mod("2003 02 05 00 00 00 LHZ ../testing/testdata/seed/S-20030205-000000-00000.seed ./geonet/2003/Feb", ' ', tokens, &nwords);
*  
*  if(nwords != 0){
*    while(i<= nwords)
*      {                                            
*	printf("%s\n",tokens[i]);                
*	i++;
*      }                                    
*  }
*  return(0);
*}
*/

                                      
int strtok_mod(char *string, char c, char tokens[][LINEL], int* nwords)
{                                      
  int i, j=0, k=0;        
  char tmp_string[LINEL];
  
  if (string == NULL)return (0);    
                                       
  for (i = 0; i < strlen(string); i++)
    {                      
      if (string[i] == c) j++;
    }
	
  if(j++ > *nwords){
    printf("WARNING: possible buffer overflow in strtok_mod\n");
    *nwords = 0;
    return (0);
  }

  j = 0;
  memset(tmp_string, 0, LINEL);
  for (i = 0; i < strlen(string); i++)
    {                      
      if (string[i] != c && string[i] != '\n'){
	if(k < LINEL){
	  tmp_string[k] = string[i];
	  k++;
	}else{
	  printf("WARNING: possible buffer overflow in strtok_mod\n");
	  return(0);
	}
      }else{
	if(strlen(tmp_string) != 0){
	  strncpy(tokens[j], tmp_string, strlen(tmp_string)+1);
	  j++;
	  k=0;
	  memset(tmp_string, 0, LINEL);
	}
      }
    }
  if(strlen(tmp_string) != 0)
    strncpy(tokens[j], tmp_string, strlen(tmp_string)+1);

  *nwords = j;
  return(1);
}


