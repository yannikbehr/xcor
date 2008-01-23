 /*              
 * The Ultimate Network Tool.
 * Copyright (C) 2004 Virtual Pointer
 *
 * The Ultimate Network Tool is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *              
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *              
 * You should have received a copy of the GNU General Public
 * License along with this program; if not, write to the Free
 * Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 * 02111-1307 USA.      
 */                            
                               
#include <stdio.h>              
#include <stdlib.h>                    
#include <string.h>                    
                                               
/* sample:                                      
 *                                              
 *int main(){
 *
 *  char **tokens;                              
 *  int i;
 *  ex_tokens("bla bla string", ' ', &tokens);
 *  
 *  for(i=0;i<3;i++)
 *    {                                            
 *      printf("%s\n",tokens[i]);                
 *    }                                    
 *  
 *  free(tokens);              
 *  return(0);
 *}
 */                            
                                       
int ex_tokens(char *string, char c, char ***tokens)
{                                      
        int i, toks = 0;        
        char **tmp_tokens;
        char *tmp_string;
                       
                       
        if (string == NULL)    
                return (0);    
                                       
        for (i = 0; i < strlen(string); i++)
        {                      
                if (string[i] == c)
                        toks++;
        }

        if (toks)
        {
                toks++;

                if ( (tmp_string = (char *)malloc(strlen(string)+1)) == NULL)
                        return (0);

                memset(tmp_string, 0, strlen(string)+1);

                if ( (tmp_tokens = (char **)calloc(toks, sizeof(char *))))
                {
                        toks = 0;
                        for (i = 0; i < strlen(string); i++)
                        {
                                /* cia toks patikrinimas tam jei stringas prasideda skirtuku */
                                if (string[i] == c && strlen(tmp_string))
                                {
                                        if ( (tmp_tokens[toks] = (char *)malloc(strlen(tmp_string)+1)))
                                        {
                                                memset(tmp_tokens[toks], 0, strlen(tmp_string));
                                                strncpy(tmp_tokens[toks], tmp_string, strlen(tmp_string));
                                                memset(tmp_string, 0, strlen(tmp_string)+1);
                                                toks++;
                                        }
                                        else
                                        {
                                                free(tmp_string);
                                                free(tmp_tokens);
                                                return (0);
                                        }
                                }
                                else
                                {
                                        if (string[i] == c)
                                                continue;
                                        strncat(tmp_string, (char*)&string[i], 1);
                                }
                        }

                        if (strlen(tmp_string))
                        {
                                if ( (tmp_tokens[toks] = (char *)malloc(strlen(tmp_string)+1)))
                                {
                                        memset(tmp_tokens[toks], 0, strlen(tmp_string));
                                        strncpy(tmp_tokens[toks], tmp_string, strlen(tmp_string));
                                }
                                else
                                {
                                        free(tmp_string);
                                        free(tmp_tokens);
                                        return (0);
                                }
                        }

                        free(tmp_string);
                        *tokens = tmp_tokens;
                        return (1);
                }
                else
                        return (0);
        }

        return(0);
}


