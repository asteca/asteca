
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from os.path import join
from . import add_version_plot
from . import cornerPlot
from . import prep_plots
from . prep_plots import figsize_x, figsize_y, grid_x, grid_y


def main(npd, pd, clp, td):
    """
    Make D2 block plots (corner plot).
    """
    fig = plt.figure(figsize=(figsize_x, figsize_y))
    gs = gridspec.GridSpec(grid_y, grid_x)

    fit_pars = clp['isoch_fit_params']

    # Title and version for the plot.
    m_bf, s_bf = divmod(fit_pars['bf_elapsed'], 60)
    h_bf, m_bf = divmod(m_bf, 60)

    xf, yf = .02, .999
    add_version_plot.main(x_fix=xf, y_fix=yf)

    # r'$M\,(M_{{\odot}})$'
    labels = [r'$z$', r'$log(age)$', r'$E_{(B-V)}$', r'$DR$', r'$(m-M)_o$',
              r'$\beta$']

    # pl_2_param_dens: Param vs param density map.
    for p2 in [
            'metal-age', 'metal-ext', 'metal-dr', 'metal-dist', 'metal-beta',
            'age-ext', 'age-dist', 'age-dr', 'age-beta',
            'ext-dr', 'ext-dist', 'ext-beta',
            'dr-dist', 'dr-beta', 'dist-beta']:

        # Limits for the 2-dens plots.
        min_max_p = prep_plots.param_ranges(
            td['fundam_params'], clp['varIdxs'], fit_pars['pars_chains'])
        min_max_p2 = prep_plots.p2_ranges(p2, min_max_p)

        trace = fit_pars['mcmc_trace']
        args = [p2, gs, labels, min_max_p2, clp['varIdxs'], trace]
        cornerPlot.plot(0, *args)

    par_list = ['metal', 'age', 'ext', 'dr', 'dist', 'beta']

    # pl_param_pf: Parameters probability functions.
    for p in par_list:
        args = [
            p, gs, labels, min_max_p, clp['varIdxs'],
            fit_pars['mean_sol'], fit_pars['map_sol'],
            fit_pars['median_sol'], fit_pars['mode_sol'],
            fit_pars['pardist_kde'], trace]
        cornerPlot.plot(1, *args)

    # Generate output file.
    fig.tight_layout()
    plt.savefig(join(
        npd['output_subdir'], str(npd['clust_name']) + '_D2_'
        + pd['best_fit_algor'] + npd['ext']))

    plt.clf()
    plt.close("all")
