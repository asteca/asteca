
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from os.path import join
import warnings
import add_version_plot
import mp_best_fit2
import prep_plots


def plot_observed_cluster(
    fig, gs, gs_y1, gs_y2, cld, x_ax, y_ax, cl_max_mag, x_min_cmd, x_max_cmd,
    y_min_cmd, y_max_cmd, err_lst, v_min_mp, v_max_mp, plot_colorbar,
        obs_x, obs_y, obs_MPs, hess_xedges, hess_yedges, x_isoch, y_isoch,
        plt_xlabel):
    """
    This function is called separately since we need to retrieve some
    information from it to plot that #$%&! colorbar.
    """
    err_bar = prep_plots.error_bars(cl_max_mag, x_min_cmd, err_lst)

    try:
        # pl_mps_phot_diag
        sca, trans = mp_best_fit2.pl_mps_phot_diag(
            gs, gs_y1, gs_y2, fig, x_min_cmd, x_max_cmd, y_min_cmd, y_max_cmd,
            x_ax, y_ax, v_min_mp, v_max_mp, obs_x, obs_y, obs_MPs,
            err_bar, hess_xedges, hess_yedges, x_isoch, y_isoch, plt_xlabel)
    except Exception:
        # import traceback
        # print traceback.format_exc()
        print("  WARNING: error when plotting MPs on cluster's "
              "photometric diagram.")

    # Ignore warning issued by colorbar plotted in photometric diagram with
    # membership probabilities.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig.tight_layout()

    # Plot colorbar down here so tight_layout won't move it around.
    try:
        if plot_colorbar is True:
            import matplotlib.transforms as mts
            # Position and dimensions relative to the axes.
            x0, y0, width, height = [0.74, 0.93, 0.2, 0.04]
            # Transform them to get the ABSOLUTE POSITION AND DIMENSIONS
            Bbox = mts.Bbox.from_bounds(x0, y0, width, height)
            l, b, w, h = mts.TransformedBbox(Bbox, trans).bounds
            # Create the axes and the colorbar.
            cbaxes = fig.add_axes([l, b, w, h])
            cbar = plt.colorbar(
                sca, cax=cbaxes, ticks=[v_min_mp, v_max_mp],
                orientation='horizontal')
            cbar.ax.tick_params(labelsize=9)
    except Exception:
        # import traceback
        # print traceback.format_exc()
        print("  WARNING: error when plotting colorbar on cluster's "
              "photometric diagram.")


def main(npd, cld, pd, synth_clst, shift_isoch, fit_params_r, fit_errors_r,
         cl_max_mag, err_lst, **kwargs):
    '''
    Make D2 block plots.
    '''
    if 'D2' in pd['flag_make_plot'] and pd['bf_flag']:
        fig = plt.figure(figsize=(30, 25))
        gs = gridspec.GridSpec(10, 12)
        add_version_plot.main()

        cl_histo, syn_histo, bin_edges = prep_plots.get_histos(
            synth_clst, pd['lkl_method'], pd['lkl_binning'], cl_max_mag)

        # Magnitude and colors defined
        first_mag = list(zip(*zip(*cl_max_mag)[3])[0])
        first_col = list(zip(*zip(*cl_max_mag)[5])[0])
        hr_diags = [
            [first_col, first_mag, pd['colors'][0], pd['filters'][0], 'mag',
             bin_edges[1], bin_edges[0], synth_clst[0][0][1],
             synth_clst[0][0][0], shift_isoch[1], shift_isoch[0],
             0, 0, 0, 1, 0, 2]]
        # If more than one color was defined.
        if len(pd['colors']) > 1:
            plt_xlabel = False
            secnd_col = list(zip(*zip(*cl_max_mag)[5])[1])
            hr_diags.append(
                [secnd_col, first_mag, pd['colors'][1], pd['filters'][0],
                 'mag', bin_edges[2], bin_edges[0], synth_clst[0][0][2],
                 synth_clst[0][0][0], shift_isoch[2], shift_isoch[0],
                 1, 0, 0, 2, 2, 4])
            hr_diags.append(
                [first_col, secnd_col, pd['colors'][0], pd['colors'][1],
                 'col', bin_edges[1], bin_edges[2], synth_clst[0][0][1],
                 synth_clst[0][0][2], shift_isoch[1], shift_isoch[2],
                 0, 1, 2, 1, 4, 6])
        else:
            plt_xlabel = True

        for diag in hr_diags:
            phot_x, phot_y, x_name, y_name, yaxis, hess_xedges, hess_yedges,\
                x_synth, y_synth, x_isoch, y_isoch,\
                i_obs_x, i_obs_y, i, j, gs_y1, gs_y2 = diag

            hess_x, hess_y, HD = prep_plots.get_hess(
                cl_histo, syn_histo, hess_xedges, hess_yedges, i, j)

            # DELETE
            import numpy as np
            print(np.shape(HD), np.shape(synth_clst[0][0]),
                  np.shape(shift_isoch))

            x_ax, y_ax = prep_plots.ax_names(x_name, y_name, yaxis)
            x_max_cmd, x_min_cmd, y_min_cmd, y_max_cmd =\
                prep_plots.diag_limits(yaxis, phot_x, phot_y)
            print(yaxis, x_max_cmd, x_min_cmd, y_min_cmd, y_max_cmd)

            arglist = [
                # pl_hess_diag: Hess diagram 'observed - synthetic'
                [gs, gs_y1, gs_y2, x_min_cmd, x_max_cmd, y_min_cmd, y_max_cmd,
                 x_ax, y_ax, pd['lkl_method'], hess_xedges, hess_yedges,
                 hess_x, hess_y, HD, plt_xlabel],
                # pl_bf_synth_cl: Best fit synthetic cluster obtained.
                [gs, gs_y1, gs_y2, x_min_cmd, x_max_cmd, y_min_cmd, y_max_cmd,
                 x_ax, y_ax, hess_xedges, hess_yedges, x_synth, y_synth,
                 pd['IMF_name'], pd['R_V'], fit_params_r, fit_errors_r,
                 x_isoch, y_isoch, pd['lkl_method'], pd['lkl_binning'],
                 pd['cmd_evol_tracks'], pd['evol_track'], plt_xlabel]
            ]
            for n, args in enumerate(arglist):
                mp_best_fit2.plot(n, *args)

            # tight_layout is called here
            v_min_mp, v_max_mp = prep_plots.da_colorbar_range(cl_max_mag, [])
            plot_colorbar, diag_fit_inv, dummy = prep_plots.da_phot_diag(
                cl_max_mag, [], v_min_mp, v_max_mp)
            # Force to not plot colorbar after the first row.
            plot_colorbar = False if gs_y1 != 0 else plot_colorbar
            # Main photometric diagram of observed cluster.
            i_y = 0 if yaxis == 'mag' else 1
            obs_x, obs_y, obs_MPs = diag_fit_inv[1][i_obs_x],\
                diag_fit_inv[i_y][i_obs_y], diag_fit_inv[2]
            plot_observed_cluster(
                fig, gs, gs_y1, gs_y2, cld, x_ax, y_ax, cl_max_mag, x_min_cmd,
                x_max_cmd, y_min_cmd, y_max_cmd, err_lst, v_min_mp, v_max_mp,
                plot_colorbar, obs_x, obs_y, obs_MPs, hess_xedges, hess_yedges,
                x_isoch, y_isoch, plt_xlabel)

        # Generate output file.
        plt.savefig(
            join(npd['output_subdir'], str(npd['clust_name']) +
                 '_D2.' + pd['plot_frmt']), dpi=pd['plot_dpi'],
            bbox_inches='tight')
        # Close to release memory.
        plt.clf()
        plt.close()

        print("<<Plots for D2 block created>>")
    else:
        print("<<Skip D2 block plot>>")
