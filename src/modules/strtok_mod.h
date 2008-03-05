#ifndef _STRTOK_MOD_H_
#define _STRTOK_MOD_H_
#include <stdio.h>              
#include <stdlib.h>                    
#include <string.h>                    

int strtok_mod(char *string, char c, char tokens[][300], int* nwords);

#endif
