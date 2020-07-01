from openwfom.imaging import andor, spinnaker, arduino, gui
from openwfom import file, solis
import time, argparse, sys, os

def _get_args():

    """
    This function simply checks for arguments when the script is called
    and stores them in their corresponding variable.

    Example:

    wfom 0

    """

    parser = argparse.ArgumentParser(description="Command line tool for the OpenWFOM library.")

    msg = "The index of the camera you would like to connect to."
    parser.add_argument('cam_num', type=int, nargs='?',default=0, help=msg)

    msg = "Run a diagnostic test of your OpenWFOM installation."
    parser.add_argument('-t', '--test', dest='test', action='store_true', default=False, help=msg)

    msg = "Print additional text while running OpenWFOM."
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help=msg)

    msg = "Option to run OpenWFOM with Solis' built-in User Interface."
    parser.add_argument('-s', '--solis', dest='solis', action='store_true', default=False, help=msg)

    args = vars(parser.parse_args())

    return args

def wfom_solis():

    andor = solis.Solis()

    COMMANDS = {
        "info":andor._info,
        "camera":andor._camera,
        "strobe_order":arduino._strobe,
        "stim":arduino._stim,
        "run":arduino._stim,
        "preview":andor._preview
    }
    # Loop until you've completed the settings.json file
    while True:
        # See which settings are missing from settings.json
        st = set(andor.JSON_SETTINGS.keys())
        TO_BE_COMPLETED = [ele for ele in COMMANDS.keys() if ele not in st]
        # See if there are any missing settings
        if len(TO_BE_COMPLETED) == 0:
            # Exit loop if no
            break
        else:
            # Run command if yes
            COMMANDS[TO_BE_COMPLETED[0]]()
            andor._read_json_settings()

    arduino._turn_on_strobing(andor.JSON_SETTINGS["strobe_order"])
    # Begin Acquisition
    andor._acquire()
    arduino._turn_off_strobing()
    print("Files were saved to:\n"+andor.PATH_TO_FILES)

def wfom_headless():
    pass

if __name__ == '__main__':
    args = _get_args()
    if args['solis']:
        wfom_solis()
    else:
        wfom_headless()
