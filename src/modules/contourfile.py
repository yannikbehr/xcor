#!/usr/bin/env mypython

""" plot polygon defined in contour.ctr which
is used for 2D inversion"""

import os, sys
import numpy as np
import socket
if socket.gethostname() == 'sgees010.geo.vuw.ac.nz':
        os.environ['GMTHOME'] = '/usr/local/gmt/'
from gmtpy import GMT

### standard contour file
#lons = [165,167,170,180,171]
#lats = [-46,-48,-47,-37.5,-33]
#lons = [173,173,175,175]
#lats = [-38.5,-40,-40,-38.5]
lons = []
lats = []

def construct_file(lats,lons):
    output = []
    output.append('0.7 0.7\n')
    output.append('%d\n'%(len(lats)))
    for _lon,_lat in zip(lons,lats):
        output.append('%f %f\n'%(_lon,_lat))
    output.append('%d\n'%(len(lats)))
    cnt = 1
    while cnt <= len(lats):
        output.append('%d %d\n'%(cnt,cnt+1))
        cnt += 1
    output.append('%d %d\n'%(cnt,1))
    return output


def get_lat_lon():
    while True:
        try:
            x = raw_input('latitude,longitude>>')
            lat,lon = x.split(',')
            lats.append(float(lat))
            lons.append(float(lon))
        except EOFError:
            print 
            break
        except ValueError:
            print "separate latitudes and longitude with ','"
    try:
        fn = raw_input('filename>')
    except EOFError:
        print "no output-filename given"
    else:
        output = construct_file(lats,lons)
        f = open(fn,'w').writelines(output)
        return fn
    
def plotctr(filename, outfile):
    gmt = GMT(config={'BASEMAP_TYPE':'fancy'} )
    ### read contour file
    f = open(filename,'r')
    line = f.readline()
    line = f.readline()
    no   = int(line.split()[0])
    coord = []
    for ii in range(no):
        line = map(float,f.readline().split())
        coord.append(line)
    f.close()
    coord = np.array(coord)
    rng='%f/%f/%f/%f'%(min(coord[:,0])-1,max(coord[:,0])+1,\
                       min(coord[:,1])-1,max(coord[:,1])+1)
    sca='M9c'
    gmt.pscoast(R=rng,J=sca,B='a5f5/a5f5',D='i',W='thinnest' )
    gmt.psxy(R=True,J=True,B=True,L=True,W='1p,red',in_rows=coord )
    gmt.save(outfile) 
    os.system('gv '+outfile+'&')


if __name__ == '__main__':
    try:
        fn = sys.argv[1]
    except:
        fn = get_lat_lon()
        
    outfile = './contour_plot.ps'
    plotctr(fn,outfile)
