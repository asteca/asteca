
from subprocess import Popen, PIPE


def R_inst_packages():
    '''
    Check installed packages inside R.
    '''
    from rpy2.rinterface import RRuntimeError
    from rpy2.robjects.packages import importr
    utils = importr('utils')
    try:
        pack_lst = utils.installed_packages()
        rpack = list(pack_lst.rx(True, 1))
    except RRuntimeError:
        rpack = []
    return rpack


def R_check(inst_packgs_lst):
    """
    Check if R, the ks r package, and rpy2 are installed.
    """
    rpy2_inst, R_inst = True, True
    # Check if rpy2 package is installed.
    if 'rpy2' not in inst_packgs_lst:
        rpy2_inst = False
    # Now check for R.
    proc = Popen(["which", "R"], stdout=PIPE, stderr=PIPE)
    stdoutdata = proc.communicate()[0]
    if stdoutdata == '':
        R_inst = False

    R_in_place = False
    # If both R and rpy2 packages are installed.
    if R_inst and rpy2_inst:
        # Check if needed packages within R are installed.
        needed_packg = ['ks']
        rpack = R_inst_packages()
        missing_pckg = []
        for pck in needed_packg:
            if pck not in rpack:
                missing_pckg.append(pck)

        if not missing_pckg:
            # R, rpy2 and all packages are installed, function is good to go.
            R_in_place = True
        else:
            # A package is missing in R.
            print("  WARNING: the following packages are missing in R:\n")
            for p in missing_pckg:
                print(" - {}".format(p))
            print("\n  The 'KDE p-value test' function will be skipped.\n")
    else:
        if R_inst and not rpy2_inst:
            R_pack = "'rpy2' is"
        if rpy2_inst and not R_inst:
            R_pack = "'R' is"
        if not R_inst and not rpy2_inst:
            R_pack = "'R' and 'rpy2' are"
        # Something is not installed and function was told to run.
        print("  WARNING: {} not installed and the\n  'KDE p-value test'"
              "  was set to run.\n  The function will be skipped.\n".format(
                  R_pack))

    return R_in_place


def check(pd):
    """
    Check that the R statistical software and the rpy2 package are installed,
    if necessary.
    R_in_place = True indicates that R and rpy2 are installed.
    """
    # Check KDE p-value cluster probability function.
    if pd['pvalue_runs'] > 0:
        # Check if R and rpy2 are installed.
        R_in_place = R_check(pd['inst_packgs_lst'])
    else:
        # Function was told not to run so we don't care if R and/or rpy2 are
        # installed since it will be skipped anyway.
        R_in_place = True

    # Add to parameters dictionary.
    pd['R_in_place'] = R_in_place
    return pd
