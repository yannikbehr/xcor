#!/usr/bin/env mypython
"""
run a checkerboard test
"""


from gmtpy import GMT
from pylab import *
from ConfigParser import SafeConfigParser
from inv2D import *

def create_mdl(fn):
    """create checkerboard model"""
    mean = 3
    inc = 1
    lon = arange(0,360,1.0)
    lat = arange(-89,90,1.0)
    f = open(fn,'w')
    for lt in range(0,len(lat),1):
        oldval = inc
        for ln in range(0,len(lon),1):
            inc = inc*(-1)
            val = mean + inc
            print >>f,'%f    %f    %f'%(lon[ln],lat[lt],val)
            #print >>f,'%f    %f    %f'%(lon[ln+1],lat[lt],val)
        if oldval == inc:
            inc = inc*(-1)
    f.close()


def syn_disp(infn,outfn):
    """from first inversion run calculate new input-dataset"""
    print 'syn_disp: converting ', infn,' to ',outfn
    a = loadtxt(infn)
    f = open(outfn,'w')
    for l in a:
        delta = l[9]*pi*6372/180
        t1    = delta/l[5]
        t2    = t1 + l[8]
        vnew  = delta/t2
        newline = '%d\t%f\t%f\t%f\t%f\t%f\t%d\t%d'\
                  %(l[0],l[1],l[2],l[3],l[4],l[8],int(l[6]),int(l[6]))
        print >>f,newline
    f.close()


def plot_mdl(fnmodel,fout):
    """plot checkerboard model"""
    print 'plotting: ', fnmodel
    rng='174.5/178/-40/-37.5'
    rng='164.5/180.5/-49.5/-32.5'
    sca='M9c'
    gmt = GMT(config={'BASEMAP_TYPE':'fancy'} )
    cptfile=gmt.tempfilename('res.cpt')
    grdmodel=gmt.tempfilename('chkbd.grd')
    #gmt.surface(fnmodel,G=grdmodel,I=0.01,R=rng,out_discard=True)
    gmt.xyz2grd(fnmodel,G=grdmodel,I='1.0/1.0',R='0/359/-89/89',out_discard=True)
    gmt.makecpt(I=True, C="polar",T='0/5/.2',Z=True, out_filename=cptfile)
    gmt.grdimage(grdmodel,J=sca,R=rng,C=cptfile)
    gmt.pscoast( R=True,J=True,B='a5f5/a5f5',D='i',W='thinnest' )
    gmt.save(fout)
    os.system('gv %s&'%fout)


if __name__ == '__main__':
    model = '/data/wanakaII/yannik/cnipse/inversion/model_map.ctr'
    os.chdir('/data/wanakaII/yannik/cnipse/inversion/')
    fout = '/data/wanakaII/yannik/cnipse/inversion/checkerboard.pdf'
    create_mdl(model)
    #plot_mdl(model,fout)
    cnf = SafeConfigParser()
    cnf.add_section('2Dmap')
    cnf.set('2Dmap','datadir','/data/wanakaII/yannik/cnipse/inversion/disp_tables_c_g/')
    cnf.set('2Dmap','ctrfile','/data/wanakaII/yannik/cnipse/inversion/contour.ctr')
    cnf.set('2Dmap','gridlat','.25')
    cnf.set('2Dmap','gridlon','.25')
    cnf.set('2Dmap','integration_step','0.1')
    cnf.set('2Dmap','cell_size','.25')
    cnf.set('2Dmap','beta','1')
    cnf.set('2Dmap','alpha','600')
    cnf.set('2Dmap','sigma','600')
    cnf.set('2Dmap','period','range(3,21)')
    cnf.set('2Dmap','name','2lambda_7')
    cnf.set('2Dmap','result','/data/wanakaII/yannik/cnipse/inversion/phase_maps/')
    cnf.set('2Dmap','tomoray','/home/data/dev/barmin_tomo/pc/tomo_sp_cu_s')
    cnf.set('2Dmap','tomobin','/home/data/dev/2Dmaps_svn//INVERSION_CODE/itomo_ra_sp_cu_shn_l')
    cnf.set('2Dmap','raytracing','on')
    cnf.set('2Dmap','model',model)
    fin = './fort.35'
    fout = './raytrace_input.txt'
    t = Inv2D(cnf)
    t.run_inv2D(10,ray=True)
    #syn_disp(fin,fout)
    #t.run_inv2D(10,datafile='raytrace_input.txt')
    #plot_mdl('2lambda_7_10.1','test')
