#!/usr/bin/env mypython

"""create a cpt file that divides the zrange below and
above the average velocity value into 4 equidistant
slices and assigns a color to each slice
"""
import sys, os, os.path

def _get_color_tuple_():
    return ((0,0,0),(255,0,0),(255,85,0),(237,255,0),(255,255,255),
            (150,255,50),(0,85,255),(0,0,255),(85,0,255))

def _get_slices_(zmin,zmax,mean):
    lmean = (mean-0.001*mean)
    umean = (mean+0.001*mean)
    lslice = (lmean-zmin)/4.0
    uslice = (zmax-umean)/4.0
    ### make first and last slice sligthly bigger
    sl1    = lslice+lslice*0.8
    sl2    = uslice+uslice*0.8
    lslice = lslice-lslice*0.8/3.0
    uslice = uslice-uslice*0.8/3.0
    lslices = [sl1,lslice,lslice,lslice]
    uslices = [uslice,uslice,uslice,sl2]
    return lslices,uslices,lmean,umean

def make_cpt((zmin,zmax,mean),filen):
    lslices,uslices,lmean,umean = _get_slices_(zmin,zmax,mean)
    colors = _get_color_tuple_()
    f = open(filen,'w')
    print >>f,"# cpt-file created by script ",sys.argv[0]
    zold = zmin
    for _i in range(4):
        znew = zold + lslices[_i]
        print >>f,"%f\t%d\t%d\t%d\t%f\t%d\t%d\t%d"\
              %(zold,colors[_i][0],colors[_i][1],colors[_i][2],\
                znew,colors[_i+1][0],colors[_i+1][1],colors[_i+1][2])
        zold = znew
    print >>f,"%f\t%d\t%d\t%d\t%f\t%d\t%d\t%d"\
          %(lmean,colors[4][0],colors[4][1],colors[4][2],\
            umean,colors[4][0],colors[4][1],colors[4][2])

    zold = umean
    for _i in range(4):
        znew = zold + uslices[_i]
        print >>f,"%f\t%d\t%d\t%d\t%f\t%d\t%d\t%d"\
              %(zold,colors[_i+4][0],colors[_i+4][1],colors[_i+4][2],\
                znew,colors[_i+5][0],colors[_i+5][1],colors[_i+5][2])
        zold = znew

    print >>f,"B\t%d\t%d\t%d"%(colors[0][0],colors[0][1],colors[0][2])
    print >>f,"F\t%d\t%d\t%d"%(colors[-1][0],colors[-1][1],colors[-1][2])


if __name__ == '__main__':
    try:
        mean = float(sys.argv[1])
        zmin = float(sys.argv[2])
        zmax = float(sys.argv[3])
    except:
        print "usage: %s mean zmin zmax"%sys.argv[0]
        sys.exit(0)

