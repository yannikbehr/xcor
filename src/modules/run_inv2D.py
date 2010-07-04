#!/usr/bin/env mypython
"""
script to run a whole set of 2D maps
"""
from ConfigParser import SafeConfigParser
from inv2D import Inv2D
from pylab import *
from scipy import optimize
import os
from matplotlib import rcParams
rcParams={'backend':'Agg'}

if 0:
    ### run all necessary 2D inversions
    dir_root = '/data/wanakaII/yannik/cnipse/inversion/'
    runlist = [(dir_root+'disp_tables_all_tt/','2lambda_5_min',dir_root+'phase_maps_min/tt/','range(3,13)'),
               (dir_root+'disp_tables_all_tt/','2lambda_5_max',dir_root+'phase_maps_max/tt/','range(3,13)'),
               (dir_root+'disp_tables_all_tt/','2lambda_5_gv_min',dir_root+'group_maps_min/tt/','range(3,13)'),
               (dir_root+'disp_tables_all_tt/','2lambda_5_gv_max',dir_root+'group_maps_max/tt/','range(3,13)')]

    cnf = SafeConfigParser()
    cnf.add_section('2Dmap')
    cnf.set('2Dmap','tomoray','/home/data/dev/barmin_tomo/pc/tomo_sp_cu_s')
    cnf.set('2Dmap','tomobin','/home/data/dev/2Dmaps_svn//INVERSION_CODE/itomo_ra_sp_cu_shn_l')
    cnf.set('2Dmap','datadir','/data/wanakaII/yannik/cnipse/inversion/disp_tables_all_tt/')
    cnf.set('2Dmap','raytracing','off')
    cnf.set('2Dmap','ctrfile','/data/wanakaII/yannik/cnipse/inversion/contour.ctr')
    cnf.set('2Dmap','gridlat','.25')
    cnf.set('2Dmap','gridlon','.25')
    cnf.set('2Dmap','integration_step','0.1')
    cnf.set('2Dmap','cell_size','.25')
    cnf.set('2Dmap','beta','1')
    cnf.set('2Dmap','alpha','200')
    cnf.set('2Dmap','sigma','200')
    cnf.set('2Dmap','period','range(3,13)')
    cnf.set('2Dmap','name','2lambda_5')
    cnf.set('2Dmap','result','/data/wanakaII/yannik/cnipse/inversion/phase_maps/tt/')

    for _rs in runlist:
        cnf.set('2Dmap','datadir',_rs[0])
        cnf.set('2Dmap','name',_rs[1])
        cnf.set('2Dmap','result',_rs[2])
        cnf.set('2Dmap','period',_rs[3])
        print cnf.get('2Dmap','result'), cnf.get('2Dmap','alpha'),cnf.get('2Dmap','sigma')
        run = Inv2D(cnf)
        run()



if 1:
    def gauss(x,y):
        fitfunc = lambda p,x: (1/sqrt(2*pi*p[0]**2))*exp(-(x-p[1])**2/(2*p[0]**2))
        #errfunc = lambda p,x,y: fitfunc(p,x)-y
        def errfunc(p,x,y):
            return fitfunc(p,x)-y
        gaussian = lambda m,s,x: (1/sqrt(2*pi*s**2))*exp(-(x-m)**2/(2*s**2))
        p0 = [0.1,0.]
        p1, success = optimize.leastsq(errfunc,p0[:],args=(x,y))
        sigm,mean = p1
        return sigm,mean,gaussian(mean,sigm,x)

    ### get L-curve
    cnf = SafeConfigParser()
    cnf.add_section('2Dmap')
    cnf.set('2Dmap','tomoray','/home/data/dev/barmin_tomo/pc/tomo_sp_cu_s')
    cnf.set('2Dmap','tomobin','/home/data/dev/2Dmaps_svn//INVERSION_CODE/itomo_ra_sp_cu_shn_l')
    cnf.set('2Dmap','datadir','/data/wanakaII/yannik/cnipse/inversion/disp_tables_all/')
    cnf.set('2Dmap','raytracing','off')
    cnf.set('2Dmap','ctrfile','/data/wanakaII/yannik/cnipse/inversion/contour.ctr')
    cnf.set('2Dmap','gridlat','.25')
    cnf.set('2Dmap','gridlon','.25')
    cnf.set('2Dmap','integration_step','0.1')
    cnf.set('2Dmap','cell_size','.25')
    cnf.set('2Dmap','beta','1')
    cnf.set('2Dmap','alpha','400')
    cnf.set('2Dmap','sigma','400')
    cnf.set('2Dmap','period','range(12,13)')
    cnf.set('2Dmap','name','2lambda_7')
    cnf.set('2Dmap','result','/data/wanakaII/yannik/cnipse/inversion/L-curve/alpha/')
    alphalist = range(10,430,20)
    sigmalist = range(10,430,20)
    #alphalist = [200]
    #sigmalist = [400]
    mapdir = cnf.get('2Dmap','result')
    if 0:
        periods = eval(cnf.get('2Dmap','period'))
        f = open(os.path.join(mapdir,'misfit_stats_%d.txt'%periods[0]),'w')
        for _a in alphalist:
            for _s in sigmalist:
                print _a, _s
                cnf.set('2Dmap','alpha',str(_a))
                cnf.set('2Dmap','sigma',str(_s))
                run = Inv2D(cnf)
                run()
                beta = cnf.get('2Dmap','beta')
                prefix = cnf.get('2Dmap','name')
                for _p in periods:
                    residf = os.path.join(mapdir,str(_p),'%s_%s_%s'%(_a,_s,beta),'%s_%d.resid'%(prefix,_p))
                    resid = loadtxt(residf,usecols=[7],unpack=True)
                    hist, bin_edges = histogram(resid,bins=100,normed=True)
                    x = bin_edges[0:-1]+diff(bin_edges)
                    y = hist
                    sigm,mean,y_g = gauss(x,y)
                    print >>f,_a,_s,mean,sigm
                    if 0:
                        plot(x,y)
                        plot(x,y_g,'r')
        f.close()
    if 1:
        a,s,m,sd = loadtxt(os.path.join(mapdir,'misfit_stats_12.txt'),unpack=True)
        sd = abs(sd)
        #sz = len(alphalist)
        #aa = a.reshape(sz,sz)
        #ss = s.reshape(sz,sz)
        #mm = m.reshape(sz,sz)
        #sds = sd.reshape(sz,sz)
        #figure()
        #contourf(ss,aa,mm,20)
        #xlabel('Sigma')
        #ylabel('Alpha')
        #ax = gca()
        #ax.autoscale_view(tight=True)
        #colorbar()
        #figure()
        #contourf(ss,aa,sds,20)
        #xlabel('Sigma')
        #ylabel('Alpha')
        #colorbar()
        fig = figure()
        rect_top = [0.08, 0.25, 0.9, 0.7]
        rect_bot = [0.06, 0.1, 0.9, 0.05]

        a1 = axes(rect_top)
        nsd = where(sd > 1.5,1.5,sd)
        nnsd = where(nsd < .59,.1,nsd)
        nm = where(abs(m) > .79,1.5,m)
        handles = []
        idx = nsd.argmin()
        handles.append(a1.scatter(s[idx],a[idx],c='white',s=exp(sd[idx]*2)))
        idx1 = nsd.argmax()
        handles.append(a1.scatter(s[idx1],a[idx1],c='white',s=exp(sd[idx1]*2)))
        cset = a1.scatter(s,a,c=nm,s=exp(nnsd*2))
        cb = fig.colorbar(cset,ax=a1)
        cb.set_label('Mean')
        a1.set_xlabel('Sigma')
        a1.set_ylabel('Alpha')
        a1.autoscale_view(tight=True)
        a2 = figlegend(handles,labels=[str(round(nsd.min(),2)),str(round(nsd.max(),2))],loc=[0.6,0.05],scatterpoints=1,ncol=2,title='Standard deviation')
        a2.draw_frame(False)
        savefig('misfit_stats_12s.pdf')
