! ==========================================================
! Function filter4. Broadband filreting.
! ==========================================================
! Parameters for filter4 function:
! Input parameters:
! f1,f2   - low corner frequences, f2 > f1, Hz, (double)
! f3,f4   - high corner frequences, f4 > f3, Hz, (double)
! npow    - power of cosine tapering,  (int)
! dt      - sampling rate of seismogram in seconds, (double)
! n       - number of input samples, (int)
! seis_in - input array length of n, (float)
! Output parameters:
! seis_out - output array length of n, (float)
! ==========================================================

      subroutine filter4(f1,f2,f3,f4,npow,dt,n,seis_in,seis_out)
      implicit none
      include 'fftw3.f'
      integer npow,n
      real(8) f1,f2,f3,f4,dt
      real, dimension(n), intent(in):: seis_in
      real, dimension(n), intent(inout):: seis_out
      integer k,ns,nk
      real(8)   plan1,plan2
      real(8)    dom
      complex(8), dimension(:), allocatable:: s,sf
      complex(8) czero
! ---
     czero = (0.0d0,0.0d0)

! determine the power of FFT
      ns = 2**max0(int(dlog(dble(n))/dlog(2.0d0))+1,13)
      dom = 1.0d0/dt/ns
      allocate(s(1:ns),sf(1:ns))
      do k = 1,ns
        s(k) = czero
      enddo
      do k = 1,n
        s(k) = seis_in(k)
      enddo

! make backward FFT for seismogram: s ==> sf
      call dfftw_plan_dft_1d(plan1,ns,s,sf,FFTW_BACKWARD, FFTW_ESTIMATE)
      call dfftw_execute(plan1)
      call dfftw_destroy_plan(plan1)
! kill half spectra and correct ends
      nk = ns/2+1
      do k = nk+1,ns
        sf(k) = czero
      enddo
      sf(1) = sf(1)/2.0d0
      sf(nk) = dcmplx(dble(sf(nk)),0.0d0)
!===============================================================
!   make tapering
      call flt4(f1,f2,f3,f4,dom,nk,npow,sf)
!===============================================================
! make forward FFT for seismogram: sf ==> s
      call dfftw_plan_dft_1d(plan2,ns,sf,s,FFTW_FORWARD, FFTW_ESTIMATE)
      call dfftw_execute(plan2)
      call dfftw_destroy_plan(plan2)
! forming final result
      do k = 1,n
        seis_out(k) = 2.0*real(dble(s(k)))/ns
      enddo
      return
      end
!===============================================================
! Tapering subroutine itself
!===============================================================
      subroutine flt4(f1,f2,f3,f4,dom,nk,npow,sf)
      real*8    f1,f2,f3,f4,dom
      integer*4 nk,npow
      complex(8) sf(400000)
      real*8    d1,d2,f,dpi,ss,s(400000)
      integer*4 i,j
! ---
      dpi = datan(1.0d0)*4.0d0
      do i = 1,nk
         s(i) = 0.0d0
      enddo
      do i = 1,nk
        f = (i-1)*dom
        if(f.le.f1) then
          goto 1
        else if(f.le.f2) then
          d1 = dpi/(f2-f1)
          ss = 1.0d0
          do j = 1,npow
            ss = ss*(1-dcos(d1*(f1-f)))/2.0d0
          enddo
          s(i) = ss
        else if(f.le.f3) then
           s(i) = 1.0d0
        else if(f.le.f4) then
          d2 = dpi/(f4-f3)
          ss = 1.0d0
          do j = 1,npow
            ss = ss*(1+dcos(d2*(f3-f)))/2.0d0
          enddo
          s(i) = ss
        endif
  1     continue
      enddo
      do i = 1,nk
        sf(i) = sf(i)*s(i)
      enddo
      return
      end