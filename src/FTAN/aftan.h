#ifndef AFTAN_H

/* Finction prorotypes */

void aftan4i_(int *n,float *sei,double *t0,double *dt,double *delta,
           double *vmin,double *vmax,double *tmin,double *tmax,
           double *tresh,double *ffact,double *perc,int *npoints,
           double *taperl,int *nfin,double *snr,
           int *npred, double pred[2][300],
           int *nfout1,double arr1[100][7],int *nfout2,double arr2[100][6],
           double *tamp, int *nrow,int *ncol, double ampo[100][32768],int *ierr);
void aftan4_(int *n,float *sei,double *t0,double *dt,double *delta,
           double *vmin,double *vmax,double *tmin,double *tmax,
           double *tresh,double *ffact,double *perc,int *npoints,
           double *taperl,int *nfin,double *snr,
           int *nfout1,double arr1[100][7],int *nfout2,double arr2[100][6],
           double *tamp, int *nrow,int *ncol, double ampo[100][32768],int *ierr);
void printres(double dt,int nfout1,double arr1[100][7],int nfout2,
           double arr2[100][6],double tamp, int nrow,int ncol,
           double ampo[100][32768],int ierr, char *name,char *pref,double delta,int ii);
void readdata(int sac,char *name,int *n,double *dt,double *delta,
              double *t0,float sei[]);
void swapn(unsigned char *b, int N, int nn);

#endif /* !AFTAN_H */
