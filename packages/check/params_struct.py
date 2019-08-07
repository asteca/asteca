
import sys


def check(center_bw, radius_method, fdens_method, **kwargs):
    """
    Check that the parameters are properly written.
    """

    if center_bw < 0.:
        sys.exit("ERROR: KDE bandwidth ('{}') must be greater\n"
                 "than (or equal to) zero.".format(center_bw))

    # Radius finding function.
    if radius_method not in ('low', 'mid', 'high'):
        sys.exit("ERROR: mode selected ('{}') for radius finding"
                 " function is not valid.".format(radius_method))

    # Radius finding function.
    try:
        fd = float(fdens_method)
        if fd < 0.:
            sys.exit("ERROR: field density ('{}') must be"
                     " greater than zero.".format(fd))
    except ValueError:
        if fdens_method != 'auto':
            sys.exit("ERROR: field density mode ('{}') is not"
                     " recognized.".format(fdens_method))
