C#######################################################################
      subroutine dspline (ip,n,x,y,ind1,d1,ind2,d2)
      implicit none
      save
      real*8 q(1001),m(1001)
      real*8 x(2),y(2)
      integer*4 i,j,ibit,iabs,n,n1,ind1,ind2,ip
      real*8    ac0,ack,r,r1,d0,d1,d2,dk,p,hj,hj1,a,c
c ---
      integer*4 nn(10),ndim(10)
      real*8    xx(1001,5),yy(1001,5),mm(1001,5)
      common /spdat/nn,ndim,xx,yy,mm
c ---
      ibit(i)=iabs((i-1)*(i-2))

      if(ibit(ind1)+ibit(ind2).eq.0) go to 60
      print 2 ,ind1,ind2
    2 format(/' !!!!!***stop-spline:ind1=',i5,' ind2=',i5)
      go to 999
   60 if(n.le.1001) go to 1
      print    62,n
   62 format(/' !!!!!***stop-spline: length of array=',i4,'>1001')
  999 stop
    1 ac0 = mod(ind1,2)
      ack = mod(ind2,2)
      hj = x(2)-x(1)
      r = (y(2)-y(1))/hj
      d0 = 2.0d0*d1
      if(ind1.eq.1) d0 = 6.0d0*(r-d1)/hj
      dk = 2.0d0*d2
      if(ind2.eq.1)dk=6.0d0*(d2-(y(n)-y(n-1))/(x(n)-x(n-1)))/(x(n)-x(n-1))
      q(1) = -ac0*0.5d0
      m(1) = d0*0.5d0
      n1 = n-1
      if(n1.le.1) goto 5
      do 3 i=2,n1
      hj1 = x(i+1)-x(i)
      r1 = (y(i+1)-y(i))/hj1
      c = hj1/(hj+hj1)
      a = 1.0d0-c
      p = 1.0d0/(a*q(i-1)+2.0d0)
      q(i) = -c*p
      m(i) = (6.0d0*(r1-r)/(hj+hj1)-a*m(i-1))*p
      hj = hj1
      r = r1
    3 continue
    5 m(n) = (dk-ack*m(n1))/(ack*q(n1)+2.0d0)
      do 4 i=1,n1
      j = n-i
    4 m(j) = q(j)*m(j+1)+m(j)
      nn(ip) = n
      do i = 1,n
         xx(i,ip) = x(i)
         yy(i,ip) = y(i)
         mm(i,ip) = m(i)
      enddo
      return
      end
c-----------------------------------------------------------------------
c     subroutine splint (i0,ik,x,y,m,sa,sb,sint,ierr)
      subroutine dsplint (ip,sa,sb,sint,ierr)
c-----------------------------------------------------------------------
      implicit none
      save
      real*8    x(1001),y(1001),m(1001)
      real*8    sa,sb,sint
      integer*4 i,i0,ip,ik,j,j1,j2,n1,n,n2,ierr
      real*8    sll,sul,sig,fsig,x1,x2,r,h,h2,xr,xr2,xl,xl2,s,sd,sdd
c ---
      integer*4 nn(10),ndim(10)
      real*8    xx(1001,5),yy(1001,5),mm(1001,5)
      common /spdat/nn,ndim,xx,yy,mm
c ---
      fsig(x1,x2,r)=(x1-r)*(x2-r)

      ierr = 0
      j1 = 1
      j2 = 1
      sint=0.0d0
      n = nn(ip)
      x(1) = 0.0d0
      do i = 1,n
          x(i+1) = xx(i,ip)
          y(i+1) = yy(i,ip)
          m(i+1) = mm(i,ip)
      enddo
      x(n+2) = 0.0d0
      i0 = 2
      ik = n+1
c check sa position
      if(fsig(x(i0),x(ik),sa).gt.(0.0d0)) then
          call dsplder (ip,sa,s,sd,sdd,ierr)
          if(sa.gt.x(ik)) then
              ik = ik+1
              x(ik) = sa
              y(ik) = s
              m(ik) = sdd
          else
              i0 = i0-1
              x(i0) = sa
              y(i0) = s
              m(i0) = sdd
          endif
      endif
      if(fsig(x(i0),x(ik),sb).gt.(0.0d0)) then
          call dsplder (ip,sb,s,sd,sdd,ierr)
          if(sb.gt.x(ik)) then
              if(ik.eq.n+1)ik = ik+1
              x(ik) = sb
              y(ik) = s
              m(ik) = sdd
          else
              if(i0.eq.2) i0 = i0-1
              x(i0) = sb
              y(i0) = s
              m(i0) = sdd
          endif
      endif
c     write(*,*)(x(l),l=i0,ik)
c     write(*,*)(y(l),l=i0,ik)
c     write(*,*)(m(l),l=i0,ik)
c     if(fsig(x(i0),x(ik),sa).gt.(0.).or.fsig(x(i0),x(ik),sb).gt.0.) then
c         ierr = 1
c         return
c     endif
      n1=ik-1
      do 20 j=i0,n1
      if(fsig(x(j),x(j+1),sa).gt.0.0d0) go to 20
      j1=j
      go to 30
   20 continue
   30 do 40 j=i0,n1
      if(fsig(x(j),x(j+1),sb).gt.0.0d0) go to 40
      j2=j
      go to 50
   40 continue
   50 n1=j1
      n2=j2-1
      sll=sa
      sul=sb
      if((x(ik)-x(1))*(sb-sa).ge.0.0d0) goto 23
   24 n1=j2
      n2=j1-1
      sll=sb
      sul=sa
   23 if(j1.eq.j2) goto 22
      do 21 j=n1,n2
      h=(x(j+1)-x(j))*0.5
   21 sint=sint+(y(j+1)+y(j)-(m(j)+m(j+1))*h*h/3.0d0)*h
   22 sig=1.0d0
      do 26 j=1,2
      h=x(n1+1)-x(n1)
      h2=h*h/6.0d0
      xr=(x(n1+1)-sll)/h
      xr2=xr*xr
      xl=(sll-x(n1))/h
      xl2=xl*xl
      sint=sint-(((1.0d0-xr2*xr2)*m(n1)+xl2*xl2*m(n1+1))*h*h2*0.250d0
     *  +((1.0d0-xr2)*(y(n1)-m(n1)*h2)+xl2*(y(n1+1)-m(n1+1)*h2))
     1  *h/2.0d0)*sig
      n1=n2+1
      sll=sul
   26 sig=-1.0d0
      if((sb-sa)*(x(ik)-x(1)).lt.0.0d0) sint=-sint
      return
      end
C#######################################################################
c     subroutine splder (i0,ik,x,y,m,xt,s,sd,sdd,ierr)
      subroutine dsplder (ip,xt,s,sd,sdd,ierr)
      implicit none
      save
      real*8    x(1001),y(1001),m(1001)
      integer*4 i,j,ik,ip,i0,ierr,n1
      real*8    s,sd,sdd,xr,xr2,xl,xl2,h,xt,fsig,r,x1,x2
c ---
      integer*4 nn(10),ndim(10)
      real*8    xx(1001,5),yy(1001,5),mm(1001,5)
      common /spdat/nn,ndim,xx,yy,mm
c ---
      fsig(x1,x2,r)=(x1-r)*(x2-r)

      ierr = 0
      ik = nn(ip)
      do i = 1,ik
         x(i) = xx(i,ip)
         y(i) = yy(i,ip)
         m(i) = mm(i,ip)
      enddo
      s = 0.0d0
      sd =0.0d0
      sdd = 0.0d0
      i0 = 1
      n1 = ik-1
c       if(fsig(x(i0),x(ik),xt).gt.0.) then
c         ierr = 1
c         return
c     endif
      do 10 j=i0,n1
      if(fsig(x(j),x(j+1),xt).le.0.0d0) go to 11
   10 continue
      j = n1
      if(xt.le.x(1)) j = 1
   11 h = x(j+1)-x(j)
      xr = (x(j+1)-xt)/h
      xr2 = xr*xr
      xl = (xt-x(j))/h
      xl2=xl*xl
      s = (m(j)*xr*(xr2-1.0d0)+m(j+1)*xl*(xl2-1.0d0))*h*h/6.0d0
     *  +y(j)*xr+y(j+1)*xl
      sd = (m(j+1)*xl2-m(j)*xr2+(m(j)-m(j+1))/3.0d0)*h*0.5d0
     *  +(y(j+1)-y(j))/h
      sdd = m(j)*xr+m(j+1)*xl
      return
      end
