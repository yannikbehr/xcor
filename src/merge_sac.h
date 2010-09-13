#ifndef __MERGESAC__
#define __MERGESAC__
/* MACROS */
#include <mysac.h>
#include <sac_db.h>
#define LINEL 300
#define THRESH 36000
#define SLINE 10
#define NFILES 500
/* FUNCTION DECLARATIONS */
int merge_sac(char str[NFILES][LINEL], int i, char *fileout);
int isign(double f);
int nint(double f);
double abs_time ( int yy, long jday, long hh, long mm, long ss, long ms );
float av_sig (float *sig, int i, int N, int nwin );
int ndaysinyear (int yy);
#endif
