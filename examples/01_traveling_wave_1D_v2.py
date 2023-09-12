#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Fri Nov 30 09:11:12 2018

@author: philipp krah, jiahan wang
"""

###############################################################################
# IMPORTED MODULES
###############################################################################
import sys
sys.path.append('../lib')
import numpy as np
from numpy import exp, mod,meshgrid, cos, sin, exp, pi
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sPOD_tools import shifted_rPCA, shifted_POD, give_interpolation_error
from transforms import transforms
from plot_utils import save_fig
###############################################################################
pic_dir = "../images/"

def generate_data(Nx,Nt,case, noise_percent=0.2):
    Tmax = 0.5  # total time
    L = 1  # total domain size
    sigma = 0.015  # standard diviation of the puls
    x = np.arange(0, Nx) / Nx * L
    t = np.arange(0, Nt) / Nt * Tmax
    dx = x[1] - x[0]
    dt = t[1] - t[0]
    c = 1
    [X, T] = meshgrid(x, t)
    X = X.T
    T = T.T

    if case == "crossing_waves":
        nmodes = 1
        fun = lambda x, t: exp(-(mod((x - c * t), L) - 0.1) ** 2 / sigma ** 2) + \
                           exp(-(mod((x + c * t), L) - 0.9) ** 2 / sigma ** 2)

        # Define your field as a list of fields:
        # For example the first element in the list can be the density of
        # a flow quantity and the second element could be the velocity in 1D
        density = fun(X, T)
        velocity = fun(X, T)
        shifts1 = np.asarray(-c * t)
        shifts2 = np.asarray(c * t)
        Q = density  # , velocity]
        shift_list = [shifts1, shifts2]
    elif case == "sine_waves":
        delta = 0.0125
        # first frame
        q1 = np.zeros_like(X)
        shifts1 = -0.25 * cos(7 * pi * t)
        for r in np.arange(1, 5):
            x1 = 0.25 + 0.1 * r - shifts1
            q1 = q1 + sin(2 * pi * r * T / Tmax) * exp(-(X - x1) ** 2 / delta ** 2)
        # second frame
        c2 = dx / dt
        shifts2 = -c2 * t
        q2 = np.zeros_like(X)

        x2 = 0.2 - shifts2
        q2 = exp(-(X - x2) ** 2 / delta ** 2)

        Q = q1 + q2
        nmodes = [4, 1]
        shift_list = [shifts1, shifts2]

    elif case == "sine_waves_noise":
        delta = 0.0125
        # first frame
        q1 = np.zeros_like(X)
        shifts1 = -0.25 * cos(7 * pi * t)
        for r in np.arange(1, 5):
            x1 = 0.25 + 0.1 * r - shifts1
            q1 = q1 + sin(2 * pi * r * T / Tmax) * exp(-(X - x1) ** 2 / delta ** 2)
        # second frame
        c2 = dx / dt
        shifts2 = -c2 * t

        x2 = 0.2 - shifts2
        q2 = exp(-(X - x2) ** 2 / delta ** 2)
        #E = 0.1*np.random.random(np.shape(q2))
        Q = q1 + q2 #+ E
        indices = np.random.choice(np.arange(Q.size), replace=False,
                                   size=int(Q.size * noise_percent))
        Q=Q.flatten()
        Q[indices] = 1
        Q = np.reshape(Q,np.shape(q1))
        nmodes = [4, 1]
        shift_list = [shifts1, shifts2]

    elif case == "multiple_ranks":
        delta = 0.0125
        # first frame
        q1 = np.zeros_like(X)
        c2 = dx / dt
        shifts1 = c2 * t
        for r in np.arange(1, 5):
            # x1 = 0.25 + 0.1 * r - shifts1
            x1 = 0.5 + 0.1 * r - shifts1
            q1 = q1 + sin(2 * pi * r * T / Tmax) * exp(-(X - x1) ** 2 / delta ** 2)
        # second frame
        c2 = dx / dt
        shifts2 = -c2 * t
        q2 = np.zeros_like(X)
        for r in np.arange(1, 3):
            x2 = 0.2 + 0.1 * r - shifts2
            q2 = q2 + cos(2 * pi * r * T / Tmax) * exp(-(X - x2) ** 2 / delta ** 2)

        Q = q1 + q2
        nmodes = [4, 2]
        shift_list = [shifts1, shifts2]

    return Q, shift_list, nmodes, L, dx

##########################################
#%% Define parameters:
##########################################
plt.close("all")
method = "shifted_POD"
#method = "shifted_rPCA"
#case = "crossing_waves"
case = "sine_waves"
Nx = 500 # number of grid points in x
Nt = Nx//2  # numer of time intervalls
Niter = 500 # number of sPOD iterations

fields, shift_list, nmodes, L, dx = generate_data(Nx,Nt,case)
#######################################
# %% CALL THE SPOD algorithm
######################################
data_shape = [Nx,1,1,Nt]
trafos = [transforms(data_shape ,[L], shifts = shift_list[0], dx = [dx], interp_order=5 ),
            transforms(data_shape ,[L], shifts = shift_list[1], dx = [dx], interp_order=5)]

interp_err = np.max([give_interpolation_error(fields,trafo) for trafo in trafos])
print("interpolation error: %1.2e "%interp_err)
# %%
qmat = np.reshape(fields,[Nx,Nt])
if method == "shifted_rPCA":
    mu = Nx * Nt / (4 * np.sum(np.abs(qmat)))*0.01
    lambd0 = 1 / np.sqrt(np.maximum(Nx, Nt)) * 1
    ret = shifted_rPCA(qmat, trafos, nmodes_max = np.max(nmodes)+10, eps=1e-16, Niter=Niter, use_rSVD=True, lambd=lambd0, mu = mu)
else:
    ret = shifted_POD(qmat, trafos, nmodes, eps=1e-16, Niter=Niter, total_variation_iterations = 40)
sPOD_frames, qtilde, rel_err = ret.frames, ret.data_approx, ret.rel_err_hist
qf = [np.squeeze(np.reshape(trafo.apply(frame.build_field()),data_shape)) for trafo,frame in zip(trafos,ret.frames)]
###########################################
# %% 1. visualize your results: sPOD frames
##########################################
# first we plot the resulting field
gridspec = {'width_ratios': [1, 1, 1, 1]}
fig, ax = plt.subplots(1, 4, figsize=(12, 4), gridspec_kw=gridspec,num=101)
mycmap = "viridis"
vmin = np.min(qtilde)*0.6
vmax = np.max(qtilde)*0.6

ax[0].pcolormesh(qmat,vmin=vmin,vmax=vmax,cmap=mycmap)
ax[0].set_title(r"$\mathbf{Q}$")
#ax[0].axis("image")
ax[0].axis("off")

ax[1].pcolormesh(qtilde,vmin=vmin,vmax=vmax,cmap=mycmap)
ax[1].set_title(r"$\tilde{\mathbf{Q}}$")
#ax[0].axis("image")
ax[1].axis("off")
# the result is a list of the decomposed field.
# each element of the list contains a frame of the decomposition.
# If you want to plot the k-th frame use:
# 1. frame
plot_shifted = True
k_frame = 0
if plot_shifted:
    ax[2].pcolormesh(qf[k_frame],vmin=vmin,vmax=vmax,cmap=mycmap)
    ax[2].set_title(r"$T^" + str(k_frame + 1) + "\mathbf{Q}^" + str(k_frame + 1) + "$")
else:
    ax[2].pcolormesh(sPOD_frames[k_frame].build_field())
    ax[2].set_title(r"$\mathbf{Q}^" + str(k_frame + 1) + "$")
ax[2].axis("off")
#ax[1].axis("image")
# 2. frame
k_frame = 1
if plot_shifted:
    im2 = ax[3].pcolormesh(qf[k_frame],vmin=vmin,vmax=vmax,cmap=mycmap)
    ax[3].set_title(r"$T^" + str(k_frame + 1) + "\mathbf{Q}^" + str(k_frame + 1) + "$")
else:
    im2 = ax[3].pcolormesh(sPOD_frames[k_frame].build_field())
    ax[3].set_title(r"$\mathbf{Q}^" + str(k_frame + 1) + "$")
ax[3].axis("off")
#ax[2].axis("image")

for axes in ax[:4]:
    axes.set_aspect(0.6)

plt.colorbar(im2)
plt.tight_layout()

#save_fig(pic_dir + "01_traveling_wave_1D_Frames.png",fig)
plt.show()
###########################################
# %% 2. visualize your results: relative error
##########################################
plt.close(5)
fig,ax = plt.subplots(num=5)
Niter = 1000
case = "crossing_waves"
case = "sine_waves"
linestyles=["--","-.",":","-","-."]
plot_list = []
for ip, Nx in enumerate([40,80,120,160,200]):#,400, 800]):#,800,1000]:
    Nt = Nx // 3  # numer of time intervalls
    fields, shift_list, nmodes, L, dx = generate_data(Nx, Nt, case)
    data_shape = [Nx,1,1,Nt]
    trafos = [transforms(data_shape ,[L], shifts = shift_list[0], dx = [dx], interp_order=5 ),
            transforms(data_shape ,[L], shifts = shift_list[1], dx = [dx], interp_order=5 )]

    interp_err = np.max([give_interpolation_error(fields,trafo) for trafo in trafos])

    qmat = np.reshape(fields, [Nx, Nt])
    # mu = Nx * Nt / (4 * np.sum(np.abs(qmat))) * 0.01
    # lambd0 = 1 / np.sqrt(np.maximum(Nx, Nt)) * 100
    # ret = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 10, eps=1e-16, Niter=Niter, use_rSVD=True,
    #                    lambd=lambd0, mu=mu)
    ret = shifted_POD(qmat, trafos, nmodes=nmodes, eps=1e-16, Niter=Niter)
    sPOD_frames, qtilde, rel_err = ret.frames, ret.data_approx, ret.rel_err_hist

    h = ax.semilogy(np.arange(0,np.size(rel_err)),rel_err,linestyles[ip], label="$h=%1.3f$"%dx)
    ax.hlines(interp_err,-5,Niter+5, colors = h[0].get_color(), linestyles=h[0].get_linestyle(), linewidth=3 )
    ax.hlines(interp_err, -5, Niter + 5, "k",linewidth=5,alpha = 0.3)
    plt.text(10,interp_err,"$\mathcal{E}_*$",transform=ax.transData ,  va='bottom', ha="left")
    plot_list.append(h)
#
plt.legend(loc=1)
ax.set_xlim(-5,Niter+5)
#plt.title("relative error")
plt.ylabel(r"relative error")
plt.xlabel(r"iteration")
plt.show()
#save_fig(pic_dir + "/convergence_interp.png",fig)


# %% comapring the convergence of the J2 algorithm for different transformation opperators
plt.close(6)
fig,ax = plt.subplots(num=6)
Niter = 1000
case = "crossing_waves"
case = "sine_waves"
linestyles=["--","-.",":","-","-."]
plot_list = []
for ip, Nx in enumerate([200]):#,400, 800]):#,800,1000]:
    Nt = Nx // 3  # numer of time intervalls
    fields, shift_list, nmodes, L, dx = generate_data(Nx, Nt, case)
    data_shape = [Nx,1,1,Nt]

    # transformations with interpolation order T^k of Ord(h^5) and T^{-k} of Ord(h^5)
    trafos = [transforms(data_shape, [L], shifts=shift_list[0], dx=[dx], interp_order=[5, 5]),
               transforms(data_shape, [L], shifts=shift_list[1], dx=[dx], interp_order=[5, 5])]
    interp_err = np.max([give_interpolation_error(fields,trafo) for trafo in trafos])
    qmat = np.reshape(fields, [Nx, Nt])
    # transformations with interpolation order T^k of Ord(h^1) and T^{-k} of Ord(h^5)
    trafos1 = [transforms(data_shape ,[L], shifts = shift_list[0], dx = [dx], interp_order=[1,5] ),
            transforms(data_shape ,[L], shifts = shift_list[1], dx = [dx], interp_order=[1,5] )]
    ret1 = shifted_POD(qmat, trafos1, nmodes=nmodes, eps=1e-16, Niter=Niter)
    # transformations with interpolation order T^k of Ord(h^5) and T^{-k} of Ord(h^1)
    trafos2 = [transforms(data_shape, [L], shifts=shift_list[0], dx=[dx], interp_order=[5, 1]),
               transforms(data_shape, [L], shifts=shift_list[1], dx=[dx], interp_order=[5, 1])]
    ret2 = shifted_POD(qmat, trafos2, nmodes=nmodes, eps=1e-16, Niter=Niter)
    # transformations with interpolation order T^k of Ord(h^1) and T^{-k} of Ord(h^1)
    trafos3 = [transforms(data_shape, [L], shifts=shift_list[0], dx=[dx], interp_order=[1, 1]),
               transforms(data_shape, [L], shifts=shift_list[1], dx=[dx], interp_order=[1, 1])]
    ret3 = shifted_POD(qmat, trafos3, nmodes=nmodes, eps=1e-16, Niter=Niter)

    h1 = ax.semilogy(np.arange(0,np.size(ret1.rel_err_hist)),ret1.rel_err_hist,linestyles[ip], label=" $T^k$/$T^{-k}$ int. ord. $h^1/h^5$", color = h[0].get_color(), linestyle="-" )
    h2 = ax.semilogy(np.arange(0, np.size(ret2.rel_err_hist)), ret2.rel_err_hist, linestyles[ip], label="$T^k$/$T^{-k}$ int. ord. $h^5/h^1$" % dx, color = h[0].get_color(), linestyle=h[0].get_linestyle())
    h3 = ax.semilogy(np.arange(0, np.size(ret3.rel_err_hist)), ret3.rel_err_hist, linestyles[ip],
                     label="$T^k$/$T^{-k}$ int. ord. $h^1/h^1$" % dx, color='k',
                     linestyle=":",linewidth=2)
    ax.hlines(interp_err,-5,Niter+5, colors = h[0].get_color(), linestyles=h[0].get_linestyle(), linewidth=3 )
    ax.hlines(interp_err, -5, Niter + 5, "k",linewidth=5,alpha = 0.3)
    plt.text(10,interp_err,"$\mathcal{E}_*$",transform=ax.transData ,  va='bottom', ha="left")
    #plot_list.append(h)
# %
plt.legend(loc=1)
ax.set_xlim(-5,Niter+5)
plt.ylabel(r"relative error")
plt.xlabel(r"iteration")
plt.show()
#save_fig(pic_dir + "/convergence_interp_order.png",fig)


# %%  convergence co-moving ranks
Nx = 400
Nt = Nx // 2  # numer of time intervalls
Niter = 100
case ="multiple_ranks"
fields, shift_list, nmodes, L, dx = generate_data(Nx, Nt, case)
qmat = np.reshape(fields, [Nx, Nt])
data_shape = [Nx, 1, 1, Nt]

trafos = [transforms(data_shape, [L], shifts=shift_list[0], dx=[dx], interp_order=3),
          transforms(data_shape, [L], shifts=shift_list[1], dx=[dx], interp_order=3)]
mu = Nx * Nt / (4 * np.sum(np.abs(qmat)))
lambd0 = 1 / np.sqrt(np.maximum(Nx, Nt))*1000
ret = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 50, eps=1e-16, Niter=Niter, use_rSVD=False,
                   lambd=lambd0, mu=mu)


xlims = [-1,Niter]
plt.close(11)
fig,ax = plt.subplots(num=11)
plt.plot(ret.ranks_hist[0],'+', label="$\mathrm{rank}(\mathbf{Q}^1)$")
plt.plot(ret.ranks_hist[1],'x', label="$\mathrm{rank}(\mathbf{Q}^2)$")
plt.plot(xlims,[nmodes[0],nmodes[0]],'k--', label="exact rank $r_1=%d$"%nmodes[0])
plt.plot(xlims,[nmodes[1],nmodes[1]],'k-', label="exact rank $r_2=%d$"%nmodes[1])
plt.xlim(xlims)
plt.xlabel("iterations")
plt.ylabel("rank $r_k$")
plt.legend()

left, bottom, width, height = [0.5, 0.45, 0.3, 0.35]
ax2 = fig.add_axes([left, bottom, width, height])
ax2.pcolormesh(qmat)
ax2.axis("off")
ax2.set_title(r"$\mathbf{Q}$")


#save_fig(pic_dir + "/convergence_ranks_shifted_rPCA.png",fig)

###########################################
#%%  visualize your results: sPOD frames
##########################################
# first we plot the resulting field
sPOD_frames, qtilde, rel_err = ret.frames, ret.data_approx, ret.rel_err_hist
qf = [np.squeeze(np.reshape(trafo.apply(frame.build_field()),data_shape)) for trafo,frame in zip(trafos,ret.frames)]

gridspec = {'width_ratios': [1, 1, 1, 1]}
fig, ax = plt.subplots(1, 4, figsize=(12, 4), gridspec_kw=gridspec,num=105)
mycmap = "viridis"
vmin = np.min(qtilde)*0.6
vmax = np.max(qtilde)*0.6

ax[0].pcolormesh(qmat,vmin=vmin,vmax=vmax,cmap=mycmap)
ax[0].set_title(r"$\mathbf{Q}$")
#ax[0].axis("image")
ax[0].axis("off")

ax[1].pcolormesh(qtilde,vmin=vmin,vmax=vmax,cmap=mycmap)
ax[1].set_title(r"$\tilde{\mathbf{Q}}$")
#ax[0].axis("image")
ax[1].axis("off")
# the result is a list of the decomposed field.
# each element of the list contains a frame of the decomposition.
# If you want to plot the k-th frame use:
# 1. frame
plot_shifted = True
k_frame = 0
if plot_shifted:
    ax[2].pcolormesh(qf[k_frame],vmin=vmin,vmax=vmax,cmap=mycmap)
    ax[2].set_title(r"$T^" + str(k_frame + 1) + "\mathbf{Q}^" + str(k_frame + 1) + "$")
else:
    ax[2].pcolormesh(sPOD_frames[k_frame].build_field())
    ax[2].set_title(r"$\mathbf{Q}^" + str(k_frame + 1) + "$")
ax[2].axis("off")
#ax[1].axis("image")
# 2. frame
k_frame = 1
if plot_shifted:
    im2 = ax[3].pcolormesh(qf[k_frame],vmin=vmin,vmax=vmax,cmap=mycmap)
    ax[3].set_title(r"$T^" + str(k_frame + 1) + "\mathbf{Q}^" + str(k_frame + 1) + "$")
else:
    im2 = ax[3].pcolormesh(sPOD_frames[k_frame].build_field())
    ax[3].set_title(r"$\mathbf{Q}^" + str(k_frame + 1) + "$")
ax[3].axis("off")
#ax[2].axis("image")

for axes in ax[:4]:
    axes.set_aspect(0.6)

plt.colorbar(im2)
plt.tight_layout()

#save_fig(pic_dir + "multiple_traveling_wave_1D_Frames.png",fig)
plt.show()

# %% compare shifted rPCA and shifted POD
Niter = 500
Nx = 400
Nt = Nx // 2
case ="multiple_ranks"
fields, shift_list, nmodes, L, dx = generate_data(Nx, Nt, case)
qmat = np.reshape(fields, [Nx, Nt])
data_shape = [Nx,1,1,Nt]

linestyles=["--","-.",":","-","-."]
plot_list = []
mu0 = Nx * Nt / (4 * np.sum(np.abs(qmat)))
lambd0 = 1 / np.sqrt(np.maximum(Nx, Nt))*1000
ret_list = []
plt.close(87)
fig,ax = plt.subplots(num=87)
for ip, fac in enumerate([0.0001,0.1,1,10,1000]):#,400, 800]):#,800,1000]:

    mu = mu0 * fac
    # transformations with interpolation order T^k of Ord(h^5) and T^{-k} of Ord(h^5)
    trafos = [transforms(data_shape, [L], shifts=shift_list[0], dx=[dx], interp_order=[5, 5]),
               transforms(data_shape, [L], shifts=shift_list[1], dx=[dx], interp_order=[5, 5])]

    ret = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 10, eps=1e-16, Niter=Niter, use_rSVD=True,
                       lambd=lambd0, mu=mu)
    ret_list.append(ret)
    h = ax.semilogy(np.arange(0,np.size(ret.rel_err_hist)),ret.rel_err_hist,linestyles[ip], label="sPOD-$\mathcal{J}_1$ $\mu=10^{%d}\mu_0$"%int(np.log10(fac)) )
    plt.text(Niter, ret.rel_err_hist[-1], "$(r_1,r_2)=(%d,%d)$"%(ret.ranks[0],ret.ranks[1]), transform=ax.transData, va='bottom', ha="right")
    #plot_list.append(h)
# sPOD results
ret = shifted_POD(qmat, trafos, nmodes=nmodes, eps=1e-16, Niter=Niter)
# %
h = ax.semilogy(np.arange(0, np.size(ret.rel_err_hist)), ret.rel_err_hist, "k-",
                label="sPOD-$\mathcal{J}_2$ $(r_1,r_2)=(%d,%d)$"%(nmodes[0],nmodes[1]))
#plt.text(Niter, ret.rel_err_hist[-1], "$(r_1,r_2)=(%d,%d)$" % (nmodes[0], nmodes[1]), transform=ax.transData,
#         va='bottom', ha="right")
#interp_err = np.max([give_interpolation_error(fields, trafo) for trafo in trafos])
#ax.hlines(interp_err, -5, Niter + 5, "k",linewidth=5,alpha = 0.3)
#plt.text(10,interp_err,"$\mathcal{E}_*$",transform=ax.transData ,  va='bottom', ha="left")
plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower right")
ax.set_xlim(-5,ax.get_xlim()[-1])
plt.ylabel(r"relative error")
plt.xlabel(r"iteration")
#save_fig(pic_dir + "/convergence_J1_vs_J2.png",fig)
plt.show()

####################################################################
# shifted RPC: DATA with noise!!!!
####################################################################
# %%  convergence co-moving ranks
Nx = 400
Nt = Nx // 2  # numer of time intervalls
Niter = 10
case ="sine_waves_noise"
fields, shift_list, nmodes, L, dx = generate_data(Nx, Nt, case)
qmat = np.reshape(fields, [Nx, Nt])
data_shape = [Nx, 1, 1, Nt]

trafos = [transforms(data_shape, [L], shifts=shift_list[0], dx=[dx], interp_order=5),
          transforms(data_shape, [L], shifts=shift_list[1], dx=[dx], interp_order=5)]
mu = Nx * Nt / (4 * np.sum(np.abs(qmat)))*0.1
lambd0 = 1 / np.sqrt(np.maximum(Nx, Nt))
ret_E = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 50, eps=1e-16, Niter=Niter, use_rSVD=False,
                   lambd=lambd0, mu=mu)
ret = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 50, eps=1e-16, Niter=Niter, use_rSVD=False,
                   lambd=lambd0*1000, mu=mu)


xlims = [-1,Niter]
plt.close(14)
fig,ax = plt.subplots(num=14)
handl_list =[]
h=plt.plot(ret.ranks_hist[0],'o:',fillstyle='none', label="$\mathrm{rank}(\mathbf{Q}^1)$")

h=plt.plot(ret.ranks_hist[1],'+:',fillstyle='none', label="$\mathrm{rank}(\mathbf{Q}^2)$")
h=plt.plot(ret_E.ranks_hist[0],'<:', label="$\mathrm{rank}(\mathbf{Q}^1)$ robust")
h=plt.plot(ret_E.ranks_hist[1],'x:', label="$\mathrm{rank}(\mathbf{Q}^2)$ robust")
h=plt.plot(xlims,[nmodes[0],nmodes[0]],'k--', label="exact rank $r_1=%d$"%nmodes[0])
h=plt.plot(xlims,[nmodes[1],nmodes[1]],'k-', label="exact rank $r_2=%d$"%nmodes[1])
plt.xlim(xlims)
plt.xlabel("iterations")
plt.ylabel("rank $r_k$")

plt.legend()
#
# legend1 = plt.legend(handles=handl_list[:2], title="not noise robust",
#                     loc='upper left', bbox_to_anchor=(0.65, 0.9), fontsize='small', frameon=False)
# legend2 = plt.legend(handles=handl_list[2:4], title="noise robust",
#                     loc='upper left', bbox_to_anchor=(0.65, 0.7), fontsize='small', frameon=False)
# legend = plt.legend(handles=handl_list[4:],
#                     loc='upper left', bbox_to_anchor=(0.65, 0.5), fontsize='small', frameon=False)
# ax.add_artist(legend1)
# ax.add_artist(legend2)
#
# left, bottom, width, height = [0.5, 0.45, 0.3, 0.35]
# ax2 = fig.add_axes([left, bottom, width, height])
# ax2.pcolormesh(qmat)
# ax2.axis("off")
# ax2.set_title(r"$\mathbf{Q}$")


#save_fig(pic_dir + "/convergence_ranks_shifted_rPCA_noise.png",fig)

###########################################
#%%  visualize your results: sPOD frames
##########################################
#facecolors='none' first we plot the resulting field
Niter = 500
ret_E = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 50, eps=1e-16, Niter=Niter, use_rSVD=False,
                   lambd=lambd0, mu=mu)
sPOD_frames, qtilde, rel_err = ret_E.frames, ret_E.data_approx, ret.rel_err_hist
qf = [np.squeeze(np.reshape(trafo.apply(frame.build_field()),data_shape)) for trafo,frame in zip(trafos,ret_E.frames)]

gridspec = {'width_ratios': [1, 1, 1, 1, 1]}
fig, ax = plt.subplots(1, 5, figsize=(12, 4), gridspec_kw=gridspec,num=105)
mycmap = "viridis"
vmin = np.min(qtilde)*0.6
vmax = np.max(qtilde)*0.6

ax[0].pcolormesh(qmat,vmin=vmin,vmax=vmax,cmap=mycmap)
ax[0].set_title(r"$\mathbf{Q}$")
#ax[0].axis("image")
ax[0].axis("off")

ax[1].pcolormesh(qtilde,vmin=vmin,vmax=vmax,cmap=mycmap)
ax[1].set_title(r"$\tilde{\mathbf{Q}}$")
#ax[0].axis("image")
ax[1].axis("off")
# the result is a list of the decomposed field.
# each element of the list contains a frame of the decomposition.
# If you want to plot the k-th frame use:
# 1. frame
plot_shifted = True
k_frame = 0
if plot_shifted:
    ax[2].pcolormesh(qf[k_frame],vmin=vmin,vmax=vmax,cmap=mycmap)
    ax[2].set_title(r"$T^" + str(k_frame + 1) + "\mathbf{Q}^" + str(k_frame + 1) + "$")
else:
    ax[2].pcolormesh(sPOD_frames[k_frame].build_field())
    ax[2].set_title(r"$\mathbf{Q}^" + str(k_frame + 1) + "$")
ax[2].axis("off")
#ax[1].axis("image")
# 2. frame
k_frame = 1
if plot_shifted:
    im2 = ax[3].pcolormesh(qf[k_frame],vmin=vmin,vmax=vmax,cmap=mycmap)
    ax[3].set_title(r"$T^" + str(k_frame + 1) + "\mathbf{Q}^" + str(k_frame + 1) + "$")
else:
    im2 = ax[3].pcolormesh(sPOD_frames[k_frame].build_field())
    ax[3].set_title(r"$\mathbf{Q}^" + str(k_frame + 1) + "$")
ax[3].axis("off")
#ax[2].axis("image")

# 3. noise
im2 = ax[4].pcolormesh(ret_E.error_matrix,vmin=vmin,vmax=vmax,cmap=mycmap)
ax[4].set_title(r"$\mathbf{E}$")
ax[4].axis("off")

for axes in ax[:5]:
    axes.set_aspect(0.6)

plt.colorbar(im2)
plt.tight_layout()

#save_fig(pic_dir + "traveling_waves_noise_1D_Frames.png",fig)
plt.show()

# %% compare shifted rPCA and shifted POD
Niter = 500
Nx = 400
Nt = Nx // 2
case ="sine_waves_noise"
fields, shift_list, nmodes, L, dx = generate_data(Nx, Nt, case, noise_percent=0.125)
qmat = np.reshape(fields, [Nx, Nt])
data_shape = [Nx,1,1,Nt]

linestyles=["--","-.",":","-","-."]
plot_list = []
mu0 = Nx * Nt / (4 * np.sum(np.abs(qmat)))
lambd0 = 1 / np.sqrt(np.maximum(Nx, Nt))
ret_list = []
plt.close(87)
fig,ax = plt.subplots(num=87)
for ip, fac in enumerate([0.0001,0.1,1,10,1000]):#,400, 800]):#,800,1000]:

    mu = mu0 * fac
    # transformations with interpolation order T^k of Ord(h^5) and T^{-k} of Ord(h^5)
    trafos = [transforms(data_shape, [L], shifts=shift_list[0], dx=[dx], interp_order=[5, 5]),
               transforms(data_shape, [L], shifts=shift_list[1], dx=[dx], interp_order=[5, 5])]

    ret = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 10, eps=1e-16, Niter=Niter, use_rSVD=True,
                       lambd=lambd0, mu=mu)
    ret_list.append(ret)
    h = ax.semilogy(np.arange(0,np.size(ret.rel_err_hist)),ret.rel_err_hist,linestyles[ip], label="sPOD-$\mathcal{J}_1$ $\mu=10^{%d}\mu_0$"%int(np.log10(fac)) )
    plt.text(Niter, ret.rel_err_hist[-1], "$(r_1,r_2)=(%d,%d)$"%(ret.ranks[0],ret.ranks[1]), transform=ax.transData, va='bottom', ha="right")
    #plot_list.append(h)
# sPOD results           Xgrid - 0.1 * L) / w)

ret = shifted_POD(qmat, trafos, nmodes=nmodes, eps=1e-16, Niter=Niter)
# %
h = ax.semilogy(np.arange(0, np.size(ret.rel_err_hist)), ret.rel_err_hist, "k-",
                label="sPOD-$\mathcal{J}_2$ $(r_1,r_2)=(%d,%d)$"%(nmodes[0],nmodes[1]))
#plt.text(Niter, ret.rel_err_hist[-1], "$(r_1,r_2)=(%d,%d)$" % (nmodes[0], nmodes[1]), transform=ax.transData,
#         va='bottom', ha="right")
#interp_err = np.max([give_interpolation_error(fields, trafo) for trafo in trafos])
#ax.hlines(interp_err, -5, Niter + 5, "k",linewidth=5,alpha = 0.3)
#plt.text(10,interp_err,"$\mathcal{E}_*$",transform=ax.transData ,  va='bottom', ha="left")
plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower right")
ax.set_xlim(-5,ax.get_xlim()[-1])
plt.ylabel(r"relative error")
plt.xlabel(r"iteration")
#save_fig(pic_dir + "/convergence_J1_vs_J2_noise.png",fig)
plt.show()


###########################################
# %%  compare TV sPOD with sPOD
###########################################
plt.close(91)
fig,ax = plt.subplots(num=91)
Niter = 1000
case = "crossing_waves"
case = "sine_waves"
linestyles=["--","-.",":","-","-."]
plot_list = []
Nx = 800
Nt = Nx // 2  # numer of time intervalls
fields, shift_list, nmodes, L, dx = generate_data(Nx, Nt, case)
data_shape = [Nx,1,1,Nt]
trafos = [transforms(data_shape ,[L], shifts = shift_list[0], dx = [dx], interp_order=3 ),
          transforms(data_shape ,[L], shifts = shift_list[1], dx = [dx], interp_order=3 )]
qmat = np.reshape(fields, [Nx, Nt])

ret_list = []
for ip, niter_TV in enumerate([0,20,40,60,80]):#,80,120,160,200]):#,400, 800]):#,800,1000]:

    # mu = Nx * Nt / (4 * np.sum(np.abs(qmat))) * 0.01
    # lambd0 = 1 / np.sqrt(np.maximum(Nx, Nt)) * 100
    # ret = shifted_rPCA(qmat, trafos, nmodes_max=np.max(nmodes) + 10, eps=1e-16, Niter=Niter, use_rSVD=True,
    #                    lambd=lambd0, mu=mu)
    ret = shifted_POD(qmat, trafos, nmodes=nmodes, eps=1e-16, Niter=Niter, total_variation_iterations=niter_TV)
    sPOD_frames, qtilde, rel_err = ret.frames, ret.data_approx, ret.rel_err_hist
    ret_list.append(ret)
    h = ax.semilogy(np.arange(0,np.size(rel_err)),rel_err,linestyles[ip], label="$N_\mathrm{TV-iter} =%d$"%niter_TV)
    plot_list.append(h)
#

plt.legend(loc=1)
ax.set_xlim(-5,Niter+5)
#plt.title("relative error")
plt.ylabel(r"relative error")
plt.xlabel(r"iteration")
plt.show()
#save_fig(pic_dir + "/convergence_sPOD-TV.png",fig)

# %%
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

plt.close(92)
fig,ax = plt.subplots(2,2,sharex=True,num=92)

qf_TV = [np.squeeze(np.reshape(trafo.apply(frame.build_field()),data_shape)) for trafo,frame in zip(trafos,ret.frames)]
ax[0,0].pcolormesh(qf_TV[0],vmin=-0.5,vmax=0.5)
#ax[0,0].axis("off")
frames_tv = ret_list[-1].frames
ax[1,0].plot(frames_tv[0].modal_system["VT"].T)

qf = [np.squeeze(np.reshape(trafo.apply(frame.build_field()),data_shape)) for trafo,frame in zip(trafos,ret_list[0].frames)]
ax[0,1].pcolormesh(qf[0],vmin=-0.5,vmax=0.5)
ax[0,0].set_title("$N_\mathrm{TV}=80$")
ax[0,1].set_title("$N_\mathrm{TV}=0$")
#ax[0,0].set_xticks([])
ax[0,0].set_yticks([0,Nx//2,Nx])
ax[0,0].set_yticklabels([0.0,0.5,1.0])
ax[0,1].set_yticks([0,Nx//2,Nx])
ax[0,1].set_yticklabels([0.0,0.5,1.0])
#ax[0,0].set_xlabel("time $t$")
ax[0,0].set_ylabel("space $x$")
frames = ret_list[0].frames
ax[1,1].plot(frames[0].modal_system["VT"].T)
ax[1,1].set_xlabel("time $t$")
ax[1,0].set_xlabel("time $t$")
ax[1,1].set_yticklabels([])
ax[1,1].set_xticks([0,np.shape(qf)[-1]])
ax[1,1].set_xticklabels([0,"$T$"])
ax[0,1].set_xticks([0,np.shape(qf)[-1]])
ax[0,1].set_xticklabels([0,"$T$"])
ax[0,0].set_xticks([0,np.shape(qf)[-1]])
ax[0,0].set_xticklabels([0,"$T$"])
ax[1,0].set_ylabel("amplitude $a^1_k(t)$")
#ax[1,1].legend(["$k=%1d$"%(k+1) for k in range(nmodes[0])],loc=1)

axins = zoomed_inset_axes(ax[0,1], 6, loc=1) # zoom = 6
for axis in ['top','bottom','left','right']:
    axins.spines[axis].set_linewidth(3)
    axins.spines[axis].set_color('r')
axins.pcolormesh(qf[0],vmin=-0.5,vmax=0.5)
x1, x2, y1, y2 = 160, 170, 300, 350
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)
plt.xticks(visible=False)
plt.yticks(visible=False)
# draw a bbox of the region of the inset axes in the parent axes and
# connecting lines between the bbox and the inset axes area
mark_inset(ax[0,1], axins, loc1=2, loc2=4, fc="none",lw=2, ec="r")


axins = zoomed_inset_axes(ax[0,0], 6, loc=1) # zoom = 6
axins.pcolormesh(qf_TV[0],vmin=-0.5,vmax=0.5)
x1, x2, y1, y2 = 160, 170, 300, 350
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)
plt.xticks(visible=False)
plt.yticks(visible=False)
# draw a bbox of the region of the inset axes in the parent axes and
# connecting lines between the bbox and the inset axes area
mark_inset(ax[0,0], axins, loc1=2, loc2=4, fc="none",lw=2, ec="r")
for axis in ['top','bottom','left','right']:
    axins.spines[axis].set_linewidth(3)
    axins.spines[axis].set_color('r')

#save_fig(pic_dir + "/sine_waves_sPOD-TV.png",fig)
