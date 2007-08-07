#include <stdio.h>
#include <sqlite.h>

static int callback(void *NotUsed, int argc, char **argv, char **azColName){
  int i;
  for(i=0; i<argc; i++){
    printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
  }
  return 0;
}

int main(){
  sqlite *db;
  char *zErrMsg = 0;
  int rc;
  /*  char command[] = "select station, lon, lat from stations where station='BFZ' or station='BKZ' or station='CRLZ'";*/
  char command[] = "select year,month,day,hour,minute,second,sacdir,path,channel from seedfiles ";
  char database[] = "nord-data.db";

  db = sqlite_open(database, 0, &zErrMsg);
  if( db==0 ){
    fprintf(stderr, "Can't open database: %s\n", zErrMsg);
    return 1;
  }
  rc = sqlite_exec(db, command , callback, 0, &zErrMsg);
  if( rc!=SQLITE_OK ){
    fprintf(stderr, "SQL error: %s\n", zErrMsg);
  }
  sqlite_close(db);
  return 0;
}

// compile it with g++ -o executablefile thisfile.c -lsqlite
