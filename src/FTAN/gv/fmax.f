c
c parabolic interpolation of signal amplitude and phase,
c finding phase derivative
c
      subroutine fmax(am1,am2,am3,ph1,ph2,ph3,t,dph,tm,ph)
      real*8 t, dph, tm, pi,pi2,ph1,ph2,ph3,ph
      real*8 am1,am2,am3
      real*8 a1,a2,a3,dd
      pi = datan(1.0d0)*4.0d0
      pi2 = pi*2.0d0
      tresh=1.5d0*pi
      dd=am1+am3-2*am2
      t=0.0d0
      if(dd .ne. 0.0d0) then
          t=(am1-am3)/dd/2.0d0
      endif
c  phase derivative
      a1 = ph1
      a2 = ph2
      a3 = ph3
c  check for 2*pi phase jump
      if(a2-a1 .gt. tresh) then
          a2 = a2 - pi2
      endif
      if(a2-a1 .lt. 0.0d0 - tresh) then
          a2 = a2 + pi2
      endif
      if(a3-a2 .gt. tresh) then
          a3 = a3 - pi2
      endif
      if(a3-a2 .lt. 0.0d0 - tresh) then
          a3 = a3 + pi2
      endif
      dph=t*(a1+a3-2.0d0*a2)+(a3-a1)/2.0d0
      tm=t*t*(am1+am3-2.0d0*am2)/2.0d0+t*(am3-am1)/2.0d0+am2
      ph=t*t*(a1+a3-2.0d0*a2)/2.0d0+t*(a3-a1)/2.0d0+a2
      return
      end
