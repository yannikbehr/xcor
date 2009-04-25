c cut group velocity by low and upper limits
      subroutine lim(nf,per,gr,gr1)
      implicit none
      integer*4 nf,i,ierr
      real*8    per(100),gr(100),gr1(100)
      real*4    c_per(23),c_low(23),c_up(23),sm(30),sm1(30),xl,xu,sd,sdd,p
      data c_per/4.0,  8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 25.0,
     *          30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 70.0, 80.0, 90.0,
     *         100.0,125.0,150.0,175.0,200.0/
      data c_low/1.00,1.25,1.50,1.60,1.70,1.80,1.90,2.00,2.00,2.30,2.40,
     *           2.50,2.60,2.70,2.70,2.70,2.70,2.70,2.70,2.70,2.70,2.70,2.70/
      data c_up /3.50,3.65,3.80,3.80,3.80,3.90,3.90,3.90,4.00,4.10,4.20,
     *           4.30,4.40,4.50,4.70,4.70,4.70,4.70,4.70,4.70,4.70,4.70,4.70/

      call spline(23,c_per,c_low,sm,2,0.0,2,0.0)
      call spline(23,c_per,c_up,sm1,2,0.0,2,0.0)
      do i =1,nf
        gr1(i) = gr(i)
        p = per(i)
        call splder(1,23,c_per,c_low,sm,p,xl,sd,sdd,ierr)
        if(ierr.eq.1) goto 999
        call splder(1,23,c_per,c_up,sm1,p,xu,sd,sdd,ierr)
        if(ierr.eq.1) goto 999
        if(gr(i).ge.xu) gr1(i) = xu
        if(gr(i).le.xl) gr1(i) =xl
  999   continue
      enddo
      return
      end
c test
c      real*8 per(10),gr(10),gr1(10)
c      data per/10.0d0,20.0d0,30.0d0,40.0d0,50.0d0,60.0d0,70.0d0,80.0d0,90.0d0,100.0d0/
c      data gr/1.0d0,2.0d0,3.0d0,4.0d0,5.0d0,6.0d0,7.0d0,8.0d0,9.0d0,10.0d0/
c      call lim(10,per,gr,gr1)
c      do i =1,10
c       write(*,*),i,per(i),gr(i),gr1(i)
c      enddo
c      end
