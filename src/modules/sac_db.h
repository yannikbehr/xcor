/*
$Log$
Revision 1.4  2007/08/06 03:47:31  behrya
extended 'NEVENTS' to 366 in order to avoid buffer overflow

Revision 1.3  2007-07-05 06:51:28  behrya
sac_db.h

Revision 1.2  2007-07-05 06:10:59  behrya
conf element for config filename added

*/
#define NSTATION 220
#define NEVENTS 788
#define LINEL 300
#define SLINE 10


typedef struct event
{
  float lat, lon;
  int yy, mm, dd, h, m, s, ms, jday;
  double t0;
  char name[150];
}
EVENT;

typedef struct station
{
  float lat, lon;
  char name[10];
}
STATION;

typedef struct record
{
  char fname[150];
  char ft_fname[150];
  char resp_fname[150];
  char chan[7];
  double t0;
  float dt;
  long n;
}
RECORD;

typedef struct sac_dbase
{
  EVENT ev[NEVENTS];
  STATION st[NSTATION];
  RECORD rec[NEVENTS][NSTATION];
  char conf[150];
  int nev, nst;
  int cntst;
  int cntev;
}
SAC_DB;

typedef struct sac_dbase3
{
  EVENT ev[NEVENTS];
  STATION st[NSTATION];
  RECORD rz[NEVENTS][NSTATION];
  RECORD rn[NEVENTS][NSTATION];
  RECORD re[NEVENTS][NSTATION];
  int nev, nst;
}
SAC_DB3;
