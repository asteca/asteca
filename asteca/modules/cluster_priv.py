import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
import astropy.coordinates as coord
from scipy.optimize import curve_fit
from scipy.spatial import KDTree
from astropy.stats import knuth_bin_width, bayesian_blocks
from fast_histogram import histogram2d


def load(self):
    """ """
    print("Reading and processing cluster data")

    cl_ids = np.array(self.cluster_df[self.source_id])
    
    mag = np.array(self.cluster_df[self.magnitude])
    e_mag = np.array(self.cluster_df[self.e_mag])
    
    colors = [np.array(self.cluster_df[self.color])]
    if self.color2 is not None:
        colors.append(np.array(self.cluster_df[self.color2]))
    e_colors = [np.array(self.cluster_df[self.e_color])]
    if self.e_color2 is not None:
        e_colors.append(np.array(self.cluster_df[self.e_color2]))

    # Obtain bin edges for each dimension, defining a grid.
    bin_edges, ranges, Nbins = bin_edges_f(self.bin_method, mag, colors)

    # Obtain histogram for observed cluster.
    hess_diag = []
    for i, col in enumerate(colors):
        # Fast 2D histogram
        hess_diag = histogram2d(
            mag,
            col,
            range=[[ranges[0][0], ranges[0][1]], [ranges[i + 1][0], ranges[i + 1][1]]],
            bins=[Nbins[0], Nbins[i + 1]],
        )

    # Flatten array
    cl_histo_f = []
    for i, diag in enumerate(hess_diag):
        cl_histo_f += list(np.array(diag).ravel())
    cl_histo_f = np.array(cl_histo_f)

    # Index of bins where stars were observed
    cl_z_idx = cl_histo_f != 0

    # Remove all bins where n_i=0 (no observed stars)
    cl_histo_f_z = cl_histo_f[cl_z_idx]

    # Used by the synthetic cluster module
    max_mag_syn = max(mag)
    N_obs_stars = len(mag)
    m_ini_idx = len(colors) + 1
    err_lst = error_distribution(self, mag, e_mag, e_colors)

    cluster_dict = {
        "cl_ids": cl_ids,
        "mag": mag,
        "colors": colors,
        "bin_edges": bin_edges,
        "ranges": ranges,
        "Nbins": Nbins,
        "cl_z_idx": cl_z_idx,
        "cl_histo_f_z": cl_histo_f_z,
        #
        "max_mag_syn": max_mag_syn,
        "N_obs_stars": N_obs_stars,
        "m_ini_idx": m_ini_idx,
        "err_lst": err_lst,
    }

    return cluster_dict


def bin_edges_f(bin_method, mag, colors):
    """ """

    bin_edges = []

    if bin_method == "knuth":
        bin_edges.append(
            knuth_bin_width(mag[~np.isnan(mag)], return_bins=True, quiet=True)[1]
        )
        for col in colors:
            bin_edges.append(
                knuth_bin_width(col[~np.isnan(col)], return_bins=True, quiet=True)[1]
            )

    elif bin_method == "fixed":
        # Magnitude
        mag_min, mag_max = np.nanmin(mag), np.nanmax(mag)
        bin_edges.append(np.linspace(mag_min, mag_max, self.N_mag))
        # Colors
        for col in colors:
            col_min, col_max = np.nanmin(col), np.nanmax(col)
            bin_edges.append(np.linspace(col_min, col_max, self.N_col))

    elif bin_method == "bayes_blocks":
        bin_edges.append(bayesian_blocks(mag[~np.isnan(mag)]))
        for col in colors:
            bin_edges.append(bayesian_blocks(col[~np.isnan(col)]))

    # Extract ranges and number of bins, used by histogram2d
    ranges, Nbins = [], []
    for be in bin_edges:
        ranges.append([be[0], be[-1]])
        Nbins.append(len(be))

    return bin_edges, ranges, Nbins


def error_distribution(self, mag, e_mag, e_colors):
    """
    Fit an exponential function to the errors in each photometric dimension,
    using the main magnitude as the x coordinate.
    This data is used to display the error bars, and more importantly, to
    generate the synthetic clusters in the best match module.
    """
    def exp_3p(x, a, b, c):
        """
        Three-parameters exponential function.

        This function is tied to the 'synth_cluster.add_errors' function.
        """
        return a * np.exp(b * x) + c

    # Mask of not nan values across arrays
    nan_msk = np.isnan(mag) | np.isnan(e_mag)
    for e_col in e_colors:
        nan_msk = nan_msk | np.isnan(e_col)
    not_nan_msk = ~nan_msk
    # Remove nan values
    mag, e_mag = mag[not_nan_msk], e_mag[not_nan_msk]
    e_col_non_nan = []
    for e_col in e_colors:
        e_col_non_nan.append(e_col[not_nan_msk])
    e_colors = e_col_non_nan

    # Left end of magnitude range
    be_m = max(min(mag) + 1.0, np.percentile(mag, 0.5))
    # Width of the intervals in magnitude.
    interv_mag = 0.5
    # Number of intervals.
    delta_mag = mag.max() - be_m
    n_interv = int(round(delta_mag / interv_mag))
    #
    steps_x = np.linspace(be_m - 0.5 * interv_mag, mag.max(), n_interv - 1)

    # Median values for each error array in each magnitude range
    mag_y = []
    for i, e_mc in enumerate([e_mag] + [list(_) for _ in e_colors]):
        x1 = steps_x[0]
        e_mc_medians = []
        for x2 in steps_x[1:]:
            msk = (mag >= x1) & (mag < x2)
            strs_in_range = np.array(e_mc)[msk]
            if len(strs_in_range) > 1:
                e_mc_medians.append(np.median(strs_in_range))
            else:
                # If no stars in interval, use fixed value
                e_mc_medians.append(0.0001)
            x1 = x2
        mag_y.append(e_mc_medians)

    # Make sure that median error values increase with increasing magnitude. This
    # ensures that the 3P exponential fit does not fail
    mag_y_new = []
    for e_arr in mag_y:
        e_arr_new, v_old = [], np.inf
        for i in range(-1, -len(e_arr) - 1, -1):
            if e_arr[i] > v_old:
                e_arr_new.append(v_old)
            else:
                e_arr_new.append(e_arr[i])
            v_old = e_arr[i]
        e_arr_new.reverse()
        mag_y_new.append(e_arr_new)
    mag_y = mag_y_new

    # Mid points in magnitude range
    mag_x = 0.5 * (steps_x[:-1] + steps_x[1:])

    # Fit 3-parameter exponential
    err_lst = []
    for y in mag_y:
        popt_mc, _ = curve_fit(exp_3p, mag_x, y)
        err_lst.append(popt_mc)

    return err_lst


def ranModels(N_models, model_fit, model_std):
    """
    Generate the requested models via sampling a Gaussian centered on the
    selected solution, with standard deviation given by the attached
    uncertainty.

    N_models: number of models to generate (HARDCODED)
    """
    models_ran = {}
    for k, f_val in model_fit.items():
        std = model_std[k]
        models_ran[k] = np.random.normal(f_val, std, N_models)
    # Transpose dict of arrays into list of dicts
    ran_models = [dict(zip(models_ran, t)) for t in zip(*models_ran.values())]

    return ran_models


def xxx(Nm, st_mass_mean, st_mass_var, Nm_binar, obs_phot, m_ini_idx,
    st_mass_mean_binar, st_mass_var_binar, prob_binar, binar_vals, alpha, isoch):
    """
    Estimate the mean and variance for each star via recurrence.
    """
    # Masses, binary mask
    mass_primary = isoch[m_ini_idx]
    mass_secondary = isoch[-1]
    # shape: (N_stars, Ndim)
    photom = isoch[:m_ini_idx].T

    if alpha is not None:
        # Binaries have M2>0
        binar_idxs = isoch[-1] > 0.0
        binar_frac = binar_idxs.sum() / isoch.shape[-1]
    else:
        # No binaries were defined
        binar_idxs = np.full(isoch.shape[1], False)
        binar_frac = 0.
    binar_vals.append(binar_frac)

    # For non-binary systems
    photom_single = photom[~binar_idxs]
    if photom_single.any():
        Nm += 1
        obs_mass, lkl_p = photomMatch(
            obs_phot, photom_single, mass_primary[~binar_idxs]
        )
        # Estimate mean and variance
        st_mass_mean, st_mass_var = recurrentStats(
            Nm, st_mass_mean, st_mass_var, obs_mass)

        # For binary systems
        if binar_idxs.sum() > 0:
            photom_binar = photom[binar_idxs]
            # If there are no binary systems, skip
            if photom_binar.any():
                Nm_binar += 1
                obs_mass, lkl_b = photomMatch(
                    obs_phot, photom_binar, mass_secondary[binar_idxs]
                )
                st_mass_mean_binar, st_mass_var_binar = recurrentStats(
                    Nm, st_mass_mean_binar, st_mass_var_binar, obs_mass
                )

                # Bayesian probability
                new_prob_binar = 1.0 / (1.0 + (lkl_p / lkl_b))
                prob_binar = recurrentStats(Nm, prob_binar, None, new_prob_binar)

    return Nm, Nm_binar, st_mass_mean, st_mass_var, st_mass_mean_binar, \
           st_mass_var_binar, binar_vals, prob_binar


def photomMatch(obs_phot, photom, mass_ini):
    """
    For each observed star in 'obs_phot', find the closest synthetic star in
    the (synthetic) photometric space 'photom', and assign the mass of that
    synthetic star to the observed star
    """
    tree = KDTree(photom)
    dd, ii = tree.query(obs_phot, k=1)

    # Assign masses to each observed star
    obs_mass = mass_ini[ii]

    # Likelihood is defined as the inverse of the distance
    lkl = 1.0 / dd

    return obs_mass, lkl


def recurrentStats(Nm, mean, var, newValue):
    """
    Source: en.wikipedia.org/wiki/
            Algorithms_for_calculating_variance#Welford's_online_algorithm
    """
    count = Nm + 1
    delta = newValue - mean
    mean += delta / count
    if var is None:
        return mean
    var += delta * (newValue - mean)
    return mean, var


def get_masses(masses_dict, ra, dec, m_ini_idx, st_dist_mass, isoch, loga, dm):
    """ """
    # N_obs = cl_dict["N_obs_stars"]
    mass_ini = isoch[m_ini_idx]
    M_obs = mass_ini.sum()
    mass_min, mass_max = mass_ini.min(), mass_ini.max()

    # Select a random IMF sampling array
    Nmets, Nages = len(st_dist_mass), len(st_dist_mass[0])
    i = np.random.randint(Nmets)
    j = np.random.randint(Nages)
    mass_samples = st_dist_mass[i][j]

    # def sampled_inv_cdf(N):
    #     mr = np.random.rand(N)
    #     return inv_cdf(mr)
    # mass_samples = sampled_inv_cdf(500000)

    mass_tot = np.cumsum(mass_samples)

    gamma = 0.62
    t = 10**loga
    qev_t = stellar_evol_mass_loss(loga)
    term1 = (1-qev_t)**gamma
    t0 = minit_LGB05(ra, dec, dm)

    def func_optm(N_max, flag_mass=False):
        M_init_sample = mass_samples[:int(N_max)]
        M_init = mass_tot[int(N_max)]

        # Masks for the min-max mass range
        msk_max = M_init_sample > mass_max
        M_ev = M_init_sample[msk_max].sum()
        M_actual_dyn = M_init - M_ev
        msk_min = M_init_sample < mass_min
        # This is the percentage of mass below the photometric minimum mass limit
        M_ratio = M_init_sample[msk_min].sum() / M_actual_dyn

        term2 = (gamma/(M_init**gamma))*(t/t0)
        M_actual, M_actual_range = 0, 0
        if term1 > term2:
            M_actual = M_init * (term1 - term2)**(1/gamma)
            M_actual_range = M_actual - M_actual*M_ratio

        if flag_mass:
            return M_actual, M_init, abs(M_actual_range - M_obs)
        return abs(M_actual_range - M_obs)

    # Perform grid search
    optimal_param = grid_search_optimal_parameter(func_optm, 100, len(mass_samples))
    M_actual, M_init, mass_diff = func_optm(optimal_param, True)

    # print(round(loga, 2), int(M_actual), int(M_init), int(mass_diff))

    masses_dict['M_actual'].append(M_actual)
    masses_dict['M_init'].append(M_init)

    return masses_dict


def grid_search_optimal_parameter(
    func, lower_bound, upper_bound, tolerance=500, max_iterations=5
) -> float:
    """
    Perform a grid search to find the optimal parameter within a given range.

    Parameters:
    - func: The objective function to optimize.
    - lower_bound: The lower bound of the parameter range.
    - upper_bound: The upper bound of the parameter range.
    - tolerance: The tolerance level to determine convergence.
    - max_iterations: Maximum number of iterations.

    Returns:
    - optimal_parameter: The optimal parameter within the specified range.
    """

    iteration = 0
    while iteration < max_iterations and (upper_bound - lower_bound) > tolerance:
        mid_point = (lower_bound + upper_bound) / 2
        par_range = upper_bound - lower_bound
        left_point = mid_point - par_range / 4
        right_point = mid_point + par_range / 4

        func_mid = func(mid_point)
        if func(left_point) < func_mid:
            upper_bound = mid_point
        elif func(right_point) < func_mid:
            lower_bound = mid_point
        else:
            lower_bound = left_point
            upper_bound = right_point

        iteration += 1

    optimal_parameter = (lower_bound + upper_bound) / 2

    return optimal_parameter


def stellar_evol_mass_loss(loga) -> float:
    """ Fraction of the initial cluster mass (Mini) lost by stellar evolution"""
    a, b, c = 7, 0.26, -1.8
    q_ev = 10**((max(7.1, loga) - a)**b + c)
    return q_ev


def minit_LGB05(ra, dec, dm, epsilon=0.08):
    """
    Laplacian in spherical coordinates:

    https://planetmath.org/derivationofthelaplacianfromrectangulartosphericalcoordinates
    https://www.math.cmu.edu/~rcristof/pdf/Teaching/Spring2017/The%20Laplacian%20in%20polar%20and%20spherical%20coordinates(1).pdf

    I need polar coordinates in r so I just disregard the derivatives in the two
    angles.
    """
    # Constants for all clusters
    gamma = 0.62
    C_env0 = 810e6

    # Constants for MW potentials
    M_B = 2.5e10
    r_B = 0.5e3
    M_D = 7.5e10
    a = 5.4e3
    b = 0.3e3
    r_s = 15.19e3
    M_s = 1.87e11

    # Extract z value
    c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)
    lon, lat = c.galactic.l, c.galactic.b
    dist_pc = 10**(.2*(dm+5))
    c = SkyCoord(l=lon, b=lat, distance=dist_pc*u.pc, frame='galactic')
    c.representation_type = 'cylindrical'
    z = c.z.value
    # Estimate R_GC
    gc = c.transform_to(coord.Galactocentric(galcen_distance=8*u.kpc, z_sun=0*u.pc))
    r = np.sqrt(gc.x.value**2+gc.y.value**2)

    # Hernquist potential (bulge)
    # https://galaxiesbook.org/chapters/I-01.-Potential-Theory-and-Spherical-Mass-Distributions.html; Eq 3.58
    # This source above gives a density that does not match the two below formulas:
    # r_B/(r*(1+r/R_B)**3) <-- ?
    # https://docs.galpy.org/en/latest/reference/potentialhernquist.html
    # "note that amp is 2 x [total mass] for the chosen definition of the Two Power Spherical potential"
    # Phi_B_Laplacian = 2*M_B/r_B**3 * 1/((r/r_B)*(1+r/r_B)**3)
    # The above is equivalent to this one by
    # https://academic.oup.com/mnras/article/428/4/2805/992063; Eq 1
    Phi_B_Laplacian = 2*M_B*r_B/(r*(r+r_B)**3)

    # Miyamoto & Nagai potential (disk)
    # https://galaxiesbook.org/chapters/II-01.-Flattened-Mass-Distributions.html#Thickened-disk:-the-Miyamoto-Nagai-model
    # https://articles.adsabs.harvard.edu/pdf/1975PASJ...27..533M
    # https://www.astro.utu.fi/~cflynn/galdyn/lecture4.html
    numerator = M_D * b**2 * (
        a*r**2 + (a + 3*np.sqrt(z**2 + b**2)) * (a + np.sqrt(z**2 + b**2))**2)
    denominator = (b**2 + z**2)**(3/2) * (r**2 + (a + np.sqrt(b**2 + z**2))**2)**(5/2)
    Phi_D_laplacian = numerator / denominator

    # Sanderson potential (dark matter halo)
    A = -M_s / (np.log(2) - 0.5)
    Phi_H_Laplacian = -A/(r*(r+r_s)**2)

    # Ambient density
    rho_amb = (1/(4*np.pi)) * (Phi_B_Laplacian + Phi_D_laplacian + Phi_H_Laplacian)
    t0 = C_env0*(1-epsilon)*10**(-4*gamma)*rho_amb**(-.5)

    return t0
    # Minit = (M_actual**gamma + gamma*(t/t0))**(1/gamma)/(1-q_ev)
