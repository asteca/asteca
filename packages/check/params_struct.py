
import sys
from os.path import join, isfile


def check(mypath, mode, coords, flag_make_plot, plot_frmt, histo_struct_method,
          radius_method, **kwargs):
    """
    Check that the parameters are properly written.
    """

    # Check mode.
    if mode not in ('auto', 'semi', 'manual'):
        sys.exit("ERROR: 'mode' value selected ('{}') is not valid.".format(
            mode))

    if mode == 'semi':
        # Check if semi_input.dat file exists.
        semi_file = 'semi_input.dat'
        if not isfile(join(mypath, semi_file)):
            # File semi_input.dat does not exist.
            sys.exit("ERROR: 'semi' mode is set but 'semi_input.dat' file does"
                     " not exist.")

    # Check px/deg.
    if coords not in ('px', 'deg'):
        sys.exit("ERROR: coordinate units '{}' given in the input parameters\n"
                 "file are incorrect.".format(coords))

    # Output figure.
    if flag_make_plot:
        if plot_frmt not in ('png', 'pdf', 'PNG', 'PDF'):
            sys.exit("ERROR: figure output format selected ('{}') is"
                     " not valid.".format(plot_frmt))

    # 2D positional histogram.
    if histo_struct_method not in ('auto', 'manual'):
        sys.exit("ERROR: mode selected ('{}') for 2D histogram"
                 " is not valid.".format(histo_struct_method))

    # Radius finding function.
    if radius_method not in ('low', 'mid', 'high'):
        sys.exit("ERROR: mode selected ('{}') for radius finding"
                 " function is not valid.".format(radius_method))
