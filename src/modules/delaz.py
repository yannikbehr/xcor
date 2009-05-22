#!/usr/bin/env python

import math as m


def coortr(latin,lonin,flag):
    """geocentric/geographic coordinate transformation
    usage: latout,lonout = coortr(latin,lonin,flag)
    
    purpose: transform between geographic and geocentric coordinates
    geographic degrees to geocentric radians ( if flag=0 )
    or geocentric radians to geographic degrees ( if flag=1 )
    earthquake and station locations are typically
    given in geographic coordinates, whereas most calculations
    such as epicentral distance are given in geocentric coordinates
    latin and lonin can be scalars or vectors, 
    latout and lonout will match the dimensions of latin and lonin
    
    if flag==0,
    latin,  lonin  are latitude and longitude in geographic degrees
    latout, lonout are latitude and longitude in geocentric radians
    if flag==1,
    latin,  lonin  are latitude and longitude in geocentric radians
    latout, lonout are latitude and longitude in geographic degrees
    """

    if flag == 0:
        latout=m.atan(m.tan(latin*m.pi/180.)*0.9933056)
        lonout=lonin*m.pi/180.
    elif flag==1:
        latout=m.atan(m.tan(latin)/0.9933056)*180./m.pi
        lonout=lonin*180./m.pi
        
    return latout, lonout
    
def delaz(eqlat, eqlon, stlat, stlon, flag):
   """compute earthquake/station distance and azimuth
   usage: delta,azeqst,azsteq = delaz(eqlat,eqlon,stlat,stlon,flag);
   
   compute distance and azimuth from earthquake (eq) to station (st)
   delta  = distance between (eq) and (st) in degrees
   azeqst = azimuth from (eq) to (st) clockwise from north in degrees
   azsteq = azimuth from (st) to (eq) clockwise from north in degrees
   
   if input coordinates are geographic degrees   flag=0
   if input coordinates are geocentric radians   flag=1
   
   input latitudes and longitudes can be scalars or vectors
   acceptable combinations are one earthquake with many stations,
   one station and many earthquakes, or the same number of earthquakes
   and stations
   output vectors will have same dimensions as input vectors
   
   calls coortr.m
   
   convert from geographic degrees to geocentric radians if necessary
   convert to spherical polar coordinates in radians (lat -> colatitude)
   """

   if flag==0:   # convert geographic degrees to geocentric radians
       eqlat, eqlon = coortr(eqlat,eqlon,flag)
       stlat, stlon = coortr(stlat,stlon,flag) 

   eqcolat = m.pi/2-eqlat
   stcolat = m.pi/2-stlat

   cos_eq = m.cos(eqcolat)
   sin_eq = m.sin(eqcolat)
   cos_st = m.cos(stcolat)
   sin_st = m.sin(stcolat)
   cos_eqst = m.cos(stlon-eqlon)
   sin_eqst = m.sin(stlon-eqlon)

   cos_delta = cos_eq * cos_st + sin_eq * sin_st * cos_eqst
   sin_delta = m.sqrt(1-cos_delta * cos_delta)
   delta = m.atan2(sin_delta,cos_delta)
   # if sin(delta)=0, set sin(delta)=eps=10**-16
   eps = 3.e-7
   sin_delta = sin_delta + (sin_delta==0)*eps

   # index is zero if expression is false, 1 if true; 
   # if false, leave unchanged, if true azeqst=pi-azeqst
   # this puts azeqst into the correct quadrant
   azeqst = m.asin(sin_st*sin_eqst/sin_delta)
   index = (sin_eq*cos_st - cos_eq*sin_st*cos_eqst < 0)
   azeqst = azeqst + index*(m.pi-2*azeqst)
   azeqst = azeqst + (azeqst<0)*2*m.pi

   azsteq = m.asin(-sin_eq*sin_eqst/sin_delta)
   index = (cos_eq*sin_st - sin_eq*cos_st*cos_eqst < 0)
   azsteq = azsteq + index*(m.pi-2*azsteq)
   azsteq = azsteq + (azsteq<0)*2*m.pi

   # convert to degrees
   delta = delta*180/m.pi
   azeqst = azeqst*180/m.pi
   azsteq = azsteq*180/m.pi

   return delta, azeqst, azsteq


if __name__ == '__main__':
    # clia
    lat1 =-12
    lon1 =-78
    # dota
    lat2 = 52
    lon2 =-10.25
    delta, azeqst, azsteq = delaz(lat1, lon1, lat2, lon2, 0)
    delta = delta * m.pi *6372/180
    print delta, azeqst, azsteq
