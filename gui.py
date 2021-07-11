from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys, argparse, logging

import logging
logger = logging.getLogger(__name__)

from systemtray import SystemTray

def main():

    options, qt_args = create_arg_parser()
    
    app = QApplication(sys.argv[:1] + qt_args)
    app.setApplicationName("Overwatch Omnic Rewards")

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, 'System tray not found', 'Can\'t start app. No system tray found')
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    if options.debug:
        set_local_urls()

    # Create the tray
    tray = SystemTray(quiet_mode=options.quiet, parent=app)
    app.aboutToQuit.connect(tray.prepare_to_exit)
    app.commitDataRequest.connect(tray.prepare_to_exit)

    app.exec_()

def create_arg_parser():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    group.add_argument("-l", "--log", default="warning", help=("Provide logging level. \n Example --log debug', default='warning'"))
    parser.add_argument("-q", "--quiet", help="Quiet mode. No system tray", action="store_true")
    parser.add_argument("-d", "--debug", help="Debug Mode. Switches URL's endpoints to local ones for testing. See docs", action="store_true")
    
    options, qt_args = parser.parse_known_args()

    levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
    }
    if options.verbose:
        level = levels.get('info')
    else:
        level = levels.get(options.log.lower())
    if level is None:
        raise ValueError(
            f"log level given: {options.log}"
            f" -- must be one of: {' | '.join(levels.keys())}")

    logging.basicConfig(stream=sys.stdout, level=level)
    
    return options, qt_args

def set_local_urls():
    logger.info("Using Local endpoints")
    import utils.checker as checker
    from utils.viewer import Viewer
    checker.OWL_URL = "http://127.0.0.1:5000/owlpage"
    checker.OWC_URL = "http://127.0.0.1:5000/owcpage"
    Viewer.TRACKING_OWL = "http://127.0.0.1:5000/owl"
    Viewer.TRACKING_OWC = "http://127.0.0.1:5000/owc"
    

if __name__ == "__main__":
    main()
    
