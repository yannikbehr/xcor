#define MAIN
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <fftw3.h>

#define max(x,y) ((x)<=(y)?(y):(x))

/* filter spectrum using cosine filter between f1,f2 and f3,f4 */
void taper(double f1, double f2, double f3, double f4, double dom, int nk, int npow, fftw_complex *trace ){
  double f, d1, d2, ss;
  int i, j;
  for(i=0;i<nk;i++){
    f = i*dom;
    if(f < f1){
      ss = 0.0;
    }else if(f <= f2){
      d1 = M_PI/(f2-f1);
      ss = 1.0;
      for(j=0;j<npow;j++){
	ss *= (1-cos(d1*(f1-f)))/2.0;
      }
    }else if(f <= f3){
      ss = 1.0;
    }else if(f <= f4){
      d2 = M_PI/(f4-f3);
      ss = 1.0;
      for(j=0;j<npow;j++){
	ss *= (1+cos(d2*(f3-f)))/2.0;
      }
    }else if(f > f4){
      ss = 0.0;
    }
    trace[i][0] *= ss;
    trace[i][1] *= ss;
  }
  return;
}


/* calculate spectrum and call filter function */
void fft_filt(double f1, double f2, double f3, double f4,
	      int npow, double dt, int n, double *seis_in, double *seis_out){
  double *in, dom;
  int ns, i;
  fftw_complex *out;
  fftw_plan pf, pb;

  /* determine power of FFT */
  ns = pow(2,max((int)(log((double)n)/log(2.0))+1,13));
  dom = 1.0/dt/ns;
  in = (double *)calloc(ns,sizeof(double));
  memcpy(in, seis_in,n*sizeof(double));
  out = (fftw_complex*)fftw_malloc(sizeof(fftw_complex)*((ns/2)+1));

  /* make forward FFT for seismogram: in ==> out */
  pf = fftw_plan_dft_r2c_1d(ns,in,out,FFTW_ESTIMATE);
  fftw_execute(pf);
  /* filter using cosine taper */
  taper(f1,f2,f3,f4,dom,(ns/2)+1,npow,out);
  
  /* inverse fft */
  pb = fftw_plan_dft_c2r_1d(ns,out,in,FFTW_ESTIMATE);
  fftw_execute(pb);
  
  for(i=0;i<n;i++){
    seis_out[i] = in[i]/ns;
  }
  fftw_destroy_plan(pf);
  fftw_destroy_plan(pb);
  fftw_free(out);
  free(in);
  return;
}

/* smooth spectrum */
void smooth(double f1,double f2, double f3, double f4, 
	    double dom, int nk, fftw_complex *trace, int winlen){
  
  double *sorig, *sout, f, sum;
  int i, j, k;
  
  sorig = (double*)malloc(nk*sizeof(double));
  sout  = (double*)malloc(nk*sizeof(double));
  for(i=0;i<nk;i++){
    sorig[i] = sqrt(trace[i][0]*trace[i][0]+trace[i][1]*trace[i][1]);
  }
  for(i=0;i<nk;i++){
    f = i*dom;
    if(f >= f1 && f <= f4){
      sum = 0.;
      for(j=-winlen;j<=winlen;j++){
	k = i+j;
	sum += sorig[k];
      }
      sout[i] = sum/(2.*winlen+1);
    }else{
      sout[i] = sorig[i];
    }
  }

  for(i=0;i<nk;i++){
    f = i*dom;
    if(f >= f1 && f <= f4){
      trace[i][0] /= sout[i];
      trace[i][1] /= sout[i];
    }else{
      trace[i][0] = 0.0;
      trace[i][1] = 0.0;
    }
  }
  free(sorig); free(sout);
  return;
}


/* whiten spectrum using a running average and return amplitude and phase separately */
void whiten_1cmp(double f1, double f2, double f3, double f4,
		 int npow, double dt, int n, double *seis_in, 
		 double *seis_out, double *seis_outamp, 
		 double *seis_outph, int winlen){

  double dom;
  int ns, i, nk;
  fftw_complex *out, *in;
  fftw_plan pf, pb;

  /* determine power of FFT */
  ns = pow(2,max((int)(log((double)n)/log(2.0))+1,13));
  nk = (ns/2)+1;
  dom = 1.0/dt/ns;
  out = (fftw_complex*)fftw_malloc(sizeof(fftw_complex)*ns);
  in  = (fftw_complex*)fftw_malloc(sizeof(fftw_complex)*ns);
  for(i=0;i<ns;i++){
    in[i][0] = 0.0;
    in[i][1] = 0.0;
  }
  for(i=0;i<n;i++){
    in[i][0] = seis_in[i];
    in[i][1] = 0.0;
  }
  /* make forward FFT for seismogram: in ==> out */
  pf = fftw_plan_dft_1d(ns,in,out,FFTW_BACKWARD,FFTW_ESTIMATE);
  fftw_execute(pf);

  /* kill half the spectrum */
  for(i=nk;i<ns;i++){
    out[i][0] = 0.0;
    out[i][1] = 0.0;
  }
  out[0][0] /= 2.0;
  out[nk-1][0] = out[n-1][0];
  out[nk-1][1] = 0.0;
  /* smooth amplitude spectrum by dividing each amplitude by the 
   running average*/
  smooth(f1,f2,f3,f4,dom,nk,out,winlen);

  /* filter using cosine taper */
  taper(f1,f2,f3,f4,dom,nk,npow,out);

  for(i=0;i<nk;i++){
    seis_outamp[i] = sqrt(pow(out[i][0],2)+pow(out[i][1],2));
    seis_outph[i]  = atan2(out[i][1],out[i][0]);
    }

  /* inverse fft */
  pb = fftw_plan_dft_1d(ns,out,in,FFTW_FORWARD,FFTW_ESTIMATE);
  fftw_execute(pb);
  
  for(i=0;i<n;i++){
    seis_out[i] = 2.0*in[i][0]/ns;
  }
  fftw_destroy_plan(pf);
  fftw_destroy_plan(pb);
  fftw_free(out);
  free(in);
  return;
}
