/*
$Log$
Revision 1.4  2007/08/06 03:47:31  behrya
extended 'NEVENTS' to 366 in order to avoid buffer overflow

Revision 1.3  2007-07-05 06:51:28  behrya
sac_db.h

Revision 1.2  2007-07-05 06:10:59  behrya
conf element for config filename added

*/
#define NSTATION 100
#define NEVENTS 750
#define LINEL 300
#define HLINE 150
#define SLINE 10


typedef struct event
{
  float lat, lon;
  long yy, mm, dd, h, m, s, ms, jday;
  double t0;
  char name[HLINE];
}
EVENT;

typedef struct station
{
  float lat, lon;
  char name[SLINE];
}
STATION;

typedef struct record
{
  char fname[HLINE];
  char ft_fname[HLINE];
  char resp_fname[HLINE];
  char pz_fname[HLINE];
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
  char conf[HLINE];
  long nev, nst;
  long cntst;
  long cntev;
}
SAC_DB;

typedef struct sac_dbase3
{
  EVENT ev[NEVENTS];
  STATION st[NSTATION];
  RECORD rz[NEVENTS][NSTATION];
  RECORD rn[NEVENTS][NSTATION];
  RECORD re[NEVENTS][NSTATION];
  long nev, nst;
}
SAC_DB3;
