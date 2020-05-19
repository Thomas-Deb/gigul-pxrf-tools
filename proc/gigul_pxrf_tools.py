# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 13:44:00 2020

@author: chdup58
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate


def remove_background(n,scale,trace,o,fname,ch):
    step = int(n/2)
    k = 0
    bins = np.arange(0,len(trace),step)
    xsmooth_seed = np.zeros(len(bins)+1)
    ysmooth_seed = np.zeros(len(bins)+1)

    for i in bins:
    
        nstart = i
        nstop = nstart + n

        yobs = trace[nstart:nstop]
        xobs = np.linspace(nstart,nstop,num=len(yobs))
        mu_data = np.median(yobs)
        sigma_data = np.std(yobs)

    
        if mu_data != 0:
            y = yobs[np.where(yobs<mu_data+(scale*sigma_data))]
            x = xobs[np.where(yobs<mu_data+(scale*sigma_data))]
            p=np.polyfit(x,y,o)

            if i == 0:
                xsmooth_seed[k-1]=min(xobs)
                ysmooth_seed[k-1]=np.polyval(p,min(xobs))
            elif i==max(bins):
                xsmooth_seed[k+1]=max(xobs)
                ysmooth_seed[k+1]=np.polyval(p,max(xobs))
            else:         
                xsmooth_seed[k] = min(xobs) + (max(xobs)-min(xobs))/2
                ysmooth_seed[k] = np.polyval(p,xsmooth_seed[k])
        else:
            xsmooth_seed[k]= min(xobs) + (max(xobs)-min(xobs))/2
            ysmooth_seed[k]= 0.0
        k=k+1
    f = interpolate.interp1d(xsmooth_seed, ysmooth_seed,kind='slinear')
    ynoise = f(ch)
    print('Saving denoised trace to file : ' + fname+'.csv')
    np.savetxt(fname+'.csv',trace-ynoise,delimiter=',')
    return ynoise, trace-ynoise


def show_clean_trace (ch,trace,ynoise,trace_clean,fname):
    plt.figure()
    plt.plot(3,1,1)
    plt.semilogy(ch,trace)
    plt.grid()
    plt.subplot(3,1,2)
    plt.plot(ch,trace,ch,ynoise,'k')
    plt.grid()
    plt.subplot(3,1,3)
    plt.plot(ch,trace_clean)
    plt.grid()
    print ('Saving figure : '+'denoised_'+fname+'.png')
    plt.savefig(fname+'.png', format='png')

def show_peaks(data,ch,peaks,peak_est,fname):
    plt.figure()
    plt.plot(peaks[:,0],peaks[:,1],'*',peak_est[:,0],peak_est[:,1],'+')
    plt.title(fname)
    plt.legend(['final-pick','first-estimate'])
    plt.plot(ch,data,ch,smooth(data))
    plt.xlabel('Channels')
    plt.ylabel('CPS')
    plt.grid()
    plt.show()
    print ('Saving figure : '+fname+'.png')
    plt.savefig(fname+'.png', format='png')

def smooth (data):
    n = len(data)
    sdata=np.zeros(n)
    sdata[0]=data[0]
    sdata[n-1]=data[n-1]
    for i in np.arange(1,n-1):
        sdata[i]=(data[i-1]+(2*data[i])+data[i+1])/4.0
    return sdata

def estimate_peaks (data,amp_threshold,slope_threshold):
    ch = np.linspace(1,len(data),num=len(data)) # Assign channel numbers 
    data_smooth =smooth(smooth(smooth(data)))
    d = np.gradient(data_smooth)
    dd = smooth(smooth(smooth(np.gradient(d)))) # Generate a second derivative to evaluate slope at zero crossing
   
    #Plot to troubleshoot settings
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(ch, data, 'g-')
    ax2.plot(ch, dd, 'b-')
    
    ax1.set_xlabel('ch')
    ax1.set_ylabel('data', color='g')
    ax2.set_ylabel('1st deriv', color='b')
    plt.grid()
    plt.show()
    
    peak=np.zeros((len(d),2))

    for i in np.arange(0,len(d)-1):
        if np.sign(d[i])>np.sign(d[i+1]):
            peak[i,0]=ch[i]
            peak[i,1]=data_smooth[i]
    peak_est = peak[np.where((peak[:,1]>amp_threshold)&(dd<slope_threshold))]
    
    return peak_est

def refine_peaks (data,peak_est,peak_half_width,ch,fname):
    peaks = np.zeros((len(peak_est),2))
    for i in np.arange(0,len(peak_est)):
        pk = int(ch[np.where(ch == peak_est[i,0])])
        x = ch[pk-peak_half_width:pk+peak_half_width]
        y =  data[pk-peak_half_width:pk+peak_half_width]
        xnew = np.linspace(ch[pk-peak_half_width],ch[pk+peak_half_width],num=1000)
        p=np.polyfit(x,y,4)
        ynew = np.polyval(p,xnew)
        d = np.gradient(ynew)
        local_peak = np.zeros((1,2))
        for j in np.arange(0,len(d)-1):
            if np.sign(d[j]) > np.sign(d[j+1]):
                local_peak[0,0]=xnew[j]
                local_peak[0,1]=ynew[j]
        peaks[i,0]= local_peak[0,0]
        peaks[i,1]= local_peak[0,1]
    print('Saving refined-picks to file : ' + fname)
    np.savetxt(fname+'.csv',peaks,delimiter=',')
    return peaks


################################################################# 