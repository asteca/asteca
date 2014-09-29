# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 15:08:39 2014

@author: gabriel
"""

import os
import re
from os.path import join
import numpy as np
from girardi_isochs_format import isoch_format as i_format


def get_metals(iso_path):
    '''
    Read names of all metallicity files stored in isochrones path given and
    store them along with the z values they represent.
    '''

    metal_files = sorted(os.listdir(iso_path))
    met_vals_all, met_files = [], []
    # Iterate in order through all the metallicity files stored for the
    # selected set of isochrones.
    for met_file in metal_files:
        # Extract metallicity value from the name of the file.
        # *THE NAME OF THE FILE IS IMPORTANT*
        met_vals_all.append(float(met_file[:-4]))
        # Store full path to file.
        met_files.append(join(iso_path, met_file))

    return met_vals_all, met_files


def get_ages(met_file, age_format):
    '''
    Read all available ages in metallicity file.
    '''

    # Open the metallicity file.
    with open(met_file, mode="r") as f_iso:
        regex = age_format  # Define regular exoresion.
        ages0 = re.findall(regex, f_iso.read())  # Find all instances.
        ages1 = np.asarray(map(float, ages0))  # Map to floats.
        ages2 = np.log10(ages1)  # Take log10
        isoch_a = np.around(ages2, 2)  # Round to 2 decimals.

    return isoch_a


def get_ranges(par_ranges):
    '''
    Calculate parameter ranges to be used by the selected best fit method.
    '''

    m_rs, a_rs, e_rs, d_rs, mass_rs, bin_rs = par_ranges

    # Store ranges and steps for these parameters.
    z_min, z_max, z_step = m_rs
    age_min, age_max, age_step = a_rs
    e_bv_min, e_bv_max, e_bv_step = e_rs
    dm_min, dm_max, dm_step = d_rs
    mas_min, mas_max, mas_step = mass_rs
    bin_min, bin_max, bin_step = bin_rs

    # UPDATE max values.
    # Add a small value to each max value to ensure that the range is a bit
    # larger than the one between the real min and max values. This simplifies
    # the input of data and ensures that the GA algorithm won't fail when
    # encoding/decoding the floats into their binary representations.
    z_max = z_max + min(z_max / 100., z_step / 2.)
    age_max = age_max + min(age_max / 100., age_step / 2.)
    e_bv_max = e_bv_max + min(e_bv_max / 100., e_bv_step / 2.)
    dm_max = dm_max + min(dm_max / 100., dm_step / 2.)
    mas_max = mas_max + min(mas_max / 100., mas_step / 2.)
    bin_max = bin_max + min(bin_max / 100., bin_step / 2.)

    # Store min, *UPDATED* max values and steps for all parameters.
    param_rs = [[z_min, z_max, z_step], [age_min, age_max, age_step],
        [e_bv_min, e_bv_max, e_bv_step], [dm_min, dm_max, dm_step],
        [mas_min, mas_max, mas_step], [bin_min, bin_max, bin_step]]

    # Store all possible parameter values in array.
    # param = [p_1, p_2, ..., p_n]
    z_range = np.arange(z_min, z_max, z_step)
    a_range = np.arange(age_min, age_max, age_step)
    e_range = np.arange(e_bv_min, e_bv_max, e_bv_step)
    d_range = np.arange(dm_min, dm_max, dm_step)
    mas_range = np.arange(mas_min, mas_max, mas_step)
    bin_range = np.arange(bin_min, bin_max, bin_step)
    param_ranges = [z_range, a_range, e_range, d_range, mas_range, bin_range]

    return param_ranges, param_rs


def match_ranges(met_vals_all, met_files, age_vals_all, z_range, a_range):
    '''
    Matches available matallicity and ages values with those stored in the
    ranges given to these two parameters.
    '''

    # Match metallicity values in ranges with values available.
    met_f_filter, met_values = [], []
    for i, met in enumerate(met_vals_all):
        # Store metallicity file only if it's inside the given range.
        if np.isclose(z_range, met, atol=0.0001).any():
            met_f_filter.append(met_files[i])
            met_values.append(met)

    # Match age values in ranges with values available.
    age_values = []
    for age in age_vals_all:
        # If age value falls inside the given range, store the value.
        if np.isclose(a_range, age, atol=0.01).any():
            age_values.append(round(age, 2))

    return met_f_filter, met_values, age_values


def read_met_file(met_f, age_values, cmd_select, isoch_format):
    '''
    Read a given metallicity file and return the isochrones for the ages
    within the age range.
    '''

    # Read line start format and columns indexes for the selected set of
    # Girardi isochrones.
    line_start, age_format, imass_idx, mag1_idx, mag2_idx = isoch_format

    # Initialize list that will hold all the isochrones for this
    # metallicity value.
    metal_isoch = []

    # Open the metallicity file.
    with open(met_f, mode="r") as f_iso:

        # Define empty lists.
        isoch_col, isoch_mag, isoch_mas = [], [], []

        # Initial value for age to avoid 'not defined' error.
        age = -99.

        # Iterate through each line in the file.
        for line in f_iso:

            # Identify beginning of a defined isochrone.
            if line.startswith(line_start):

                # Save stored values if these exist.
                # Skip first age for which the lists will be empty.
                if isoch_col:
                    # Store color, magnitudes and masses for this
                    # isochrone.
                    metal_isoch.append([isoch_col, isoch_mag,
                        isoch_mas])
                    # Reset lists.
                    isoch_col, isoch_mag, isoch_mas = [], [], []

                # Read age value for this isochrone.
                age0 = re.findall(age_format, line)  # Find age in line.
                age = np.around(np.log10(float(age0[0])), 2)

            # If age value falls inside the given range, store the
            # isochrone's data.
            if age in age_values:

                # Save mag, color and mass values for each isochrone.
                if not line.startswith("#"):
                    reader = line.split()
                    # Color.
                    # Generate colors correctty <-- HARDCODED, FIX
                    if cmd_select in {2, 5}:
                        isoch_col.append(float(reader[mag1_idx]) -
                        float(reader[mag2_idx]))
                    else:
                        isoch_col.append(float(reader[mag2_idx]) -
                        float(reader[mag1_idx]))
                    # Magnitude.
                    isoch_mag.append(float(reader[mag1_idx]))
                    # Mass
                    isoch_mas.append(float(reader[imass_idx]))

        # Save the last isochrone when EOF is reached.
        else:
            # If list is not empty.
            if isoch_col:
                # Store colors, magnitudes and masses for this
                # isochrone.
                metal_isoch.append([isoch_col, isoch_mag, isoch_mas])

    return metal_isoch


def get_isochs(iso_select, cmd_select, met_f_filter, age_values, isoch_format):
    '''
    Stores the available isochrones of different metallicities and
    ages, according to the ranges given to these parameters.
    '''

    # Lists that store the colors, magnitudes and masses of the isochrones.
    # isoch_list = [metal_1, ..., metal_M]
    # metal_i = [isoch_i1, ..., isoch_iN]
    # isoch_ij = [colors, magnitudes, mass]
    # isoch_list[i][j] --> i: metallicity index ; j: age index
    isoch_list = []

    # Iterate in order through all the metallicity files stored for the
    # selected set of isochrones.
    for met_f in met_f_filter:

        metal_isoch = read_met_file(met_f, age_values, cmd_select, isoch_format)

        # Store list holding all the isochrones with the same metallicity
        # in the final isochrone list.
        isoch_list.append(metal_isoch)

    return isoch_list


def ip(ps_params, par_ranges, bf_flag):
    '''
    Read isochrones and parameters if best fit function is set to run.
    '''

    ip_list = []
    # Only read files of best fit method is set to run.
    if bf_flag is True:

        # Unpack.
        iso_path, cmd_select, iso_select = ps_params

        # Read names of all metallicity files stored in isochrones path given.
        # I.e.: store all metallicity values available.
        # Also read full paths to metallicity files.
        met_vals_all, met_files = get_metals(iso_path)

        # Read Girardi metallicity files format.
        isoch_format = i_format(iso_select, cmd_select)

        # Read all ages in the first metallicity file: met_files[0]
        # *WE ASUME ALL METALLICITY FILES HAVE THE SAME NUMBER OF AGE VALUES*
        # I.e: store all age values available.
        age_vals_all = get_ages(met_files[0], isoch_format[1])

        # Get parameters ranges stored in params_input.dat file.
        param_ranges, param_rs = get_ranges(par_ranges)

        # Match values in metallicity and age ranges with those available.
        z_range, a_range = param_ranges[:2]
        met_f_filter, met_values, age_values = match_ranges(met_vals_all,
            met_files, age_vals_all, z_range, a_range)

        # Get isochrones and their parameter values.
        isoch_list = get_isochs(iso_select, cmd_select, met_f_filter,
            age_values, isoch_format)

        # Pack params.
        param_values = [met_values, age_values] + param_ranges[2:]
        ip_list = [isoch_list, param_values, param_rs]

        lens = [len(_) for _ in param_values]
        total = reduce(lambda x, y: x * y, lens, 1)
        print ("Theoretical isochrones read and stored:\n"
        "  {} metallicity values (z),\n"
        "  {} isochrones per z,\n"
        "  {} reddening values,\n"
        "  {} distance values,\n"
        "  {} mass values,\n"
        "  {} binary fraction values.".format(*lens))
        print "  = {:.1e} approx total models.".format(total)

    return ip_list