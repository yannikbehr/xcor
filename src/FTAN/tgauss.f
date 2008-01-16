c taper phase matched signal
c function [ss] = tgauss(fsnr,gt0,dw,dt,n,seis);
      subroutine tgauss(fsnr,gt0,dw,dt,n,seis,
     *                  ss)
      implicit none
      integer*4 n, i,ism,nn,nnn
      double complex czero,seis(n),ss(n)
      real*8    smax(32768)
      real*8    pi, dt, gt0, dw, fsnr,sm,smw
      integer*4 nc,ii,nnl,nnnl,nnr,nnnr,nleft,nright,left(100),right(100)
      integer*4 nnrj, nnnrj
      real*8    freq,dzer,dl,dr,vleft(100),vright(100)

cxx   write(*,*)(i,seis(i),i=1,n)
      ism = 1
      dzer = 0.0d0
      czero = (0.0d0,0.0d0)
      pi = datan(1.0d0)*4.0d0
      nc = nint(gt0/dt)+1
c find global max, sm, and index ism
      sm = 0.0d0
      do i = 1,n
         smw = cdabs(seis(i))
         if(smw.ge.sm) then
             sm = smw
             ism = i
         endif
         smax(i) = smw
         ss(i) = seis(i)
      enddo
      write(*,*) 'Distance between maximas=',gt0-(ism-1)*dt,' in sec,',
     * ' Spectra point= ',ism
c find some local minima,# < 100 from left and right side of central max ism
c left side 
      nleft = 0
      do i = ism-1,2,-1     
          dl = smax(i)-smax(i-1)
          dr = smax(i+1)-smax(i)
          if((dl.lt.dzer.and.dr.ge.dzer).or.(dl.le.dzer.and.dr.gt.dzer)) then
              nleft = nleft+1
              left(nleft) = i
              vleft(nleft) = smax(i)
cxx    write(*,*) 'X',nleft,(i-1)*dt,left(nleft),vleft(nleft)
          endif
          if(nleft.ge.100) goto 10
      enddo
   10 continue
c right side
      nright = 0
      do i = ism+1,n-1      
          dl = smax(i)-smax(i-1)
          dr = smax(i+1)-smax(i)
          if((dl.lt.dzer.and.dr.ge.dzer).or.(dl.le.dzer.and.dr.gt.dzer)) then
              nright = nright+1
              right(nright) = i
              vright(nright) = smax(i)
cxx    write(*,*) 'Y',nright,(i-1)*dt,right(nright),vright(nright)
          endif
          if(nright.ge.100) goto 20
      enddo
   20 continue
c left side, apply cutting
      ii = 0
      nnl = 0 
      nnnl = 0
      if(nleft.eq.0) goto 21
       do i = 1,nleft
cxx        write(*,*) vleft(i)
           if(abs(ism-left(i))*dt.gt.5.0d0) then
                if(vleft(i) .lt. fsnr*sm) then
                    nnnl = left(i)
                    ii = i
cxx        write(*,*) 'L',i,nnnl
                    goto 21
                endif
           endif
       enddo
   21 continue
       if(nnnl.ne.0) then
           if(ii.ne.nleft) then
               nnl = left(ii+1)
           else
               nnl = 1
           endif
       endif
cxx    write(*,*) 'LLL',nnl,nnnl,sm,ism,fsnr
c right side, apply cutting
      ii = 0
      nnr = 0 
       nnnr = 0
      if(nright.eq.0) goto 31
       do i = 1,nright
           if(abs(ism-right(i))*dt.gt.5.0d0) then
                if(vright(i) .lt. fsnr*sm) then
                    nnr = right(i)
                    ii = i
cxx        write(*,*) 'R',i,nnr
                    goto 31
                endif
           endif
       enddo
   31  continue
       if(nnr.ne.0) then
           if(ii.ne.nright) then
               nnnr = right(ii+1)
           else
               nnnr = n
           endif
       endif
cxx    write(*,*) 'RRR',nnr,nnnr,sm,ism,fsnr
c ---
       if(nnnr.ne.0.and.nnnl.ne.0) then
       nn = (abs(ism-nnnl)+abs(ism-nnr))/2
       nnn = min0(abs(nnnl-nnl),abs(nnnr-nnr))
       nnrj = nn/2+1
       nnnrj = nnn/2+1
       nnnl = ism -nnrj
       nnl = nnnl-nnnrj
       nnr = ism +nnrj
       nnnr = nnr+nnnrj
cxx    write(*,*) 'WWW',nnl,nnnl,nnr,nnnr,sm,ism,fsnr
       endif
       if(nnl.eq.0.or.nnnl.eq.0) goto 30
           freq =(nnnl-nnl)
       do i = 1,nnnl
           ss(i) = ss(i)*dexp(-(i-nnnl)/freq*(i-nnnl)/freq/2.0d0)
       enddo
   30  continue
       if(nnr.eq.0.or.nnnr.eq.0) goto 40
           freq =(nnnr-nnr)
       do i = nnr,n
           ss(i) = ss(i)*dexp(-(i-nnr)/freq*(i-nnr)/freq/2.0d0)
       enddo
   40 continue
      return
      end
