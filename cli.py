from PyQt5.QtCore import *

import logging
import sys

from settings import SettingsManager
from stats import Stats
from checkviewer import CheckViewer

logger = logging.getLogger(__name__)


class CLIApp(QObject):
    def __init__(self, settings: SettingsManager, stats: Stats, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.stats = stats

        account_ids = self.settings.get("account")
        if not account_ids:
            logger.error("No account set. Please setup and account on config.json or through the GUI")
            sys.exit(1)

        if type(account_ids) != list:
            account_ids = list(account_ids)

        self.check_viewers = list()
        for account in account_ids:
            check_viewer = CheckViewer(
                account,
                owl_flag=self.settings.get("owl"),
                owc_flag=self.settings.get("owc"),
                min_check=self.settings.get("min_check")
            )

            check_viewer.check_progress.connect(self.update_check_progress)
            check_viewer.watching_owl.connect(self.update_watching_owl)
            check_viewer.watching_owc.connect(self.update_watching_owc)
            check_viewer.error.connect(self.update_error)

            check_viewer.run()
            self.check_viewers.append(check_viewer)

    @pyqtSlot(int, str)
    def update_check_progress(self, min_remaining=None, account_id=""):
        if min_remaining:
            logger.debug(f"id: {account_id}: Not Live - {min_remaining}min until next check")

    @pyqtSlot(str, int, str, bool)
    def update_watching_owl(self, account_id, min_watching, title, end):
        self.stats.set_record(False, min_watching, title, account_id)
        if not end:
            logger.info(f"{account_id}: Watching OWL for {min_watching}min")
        else:
            self.stats.write_record(account_id)
            logger.info(f"{account_id}: Watched {min_watching}mins of OWL - {title}")

    @pyqtSlot(str, int, str, bool)
    def update_watching_owc(self, account_id, min_watching, title, end):
        self.stats.set_record(True, min_watching, title, account_id)
        if not end:
            logger.info(f"{account_id}: Watching OWC for {min_watching}min")
        else:
            self.stats.write_record(account_id)
            logger.info(f"{account_id}: Watched {min_watching}mins of OWC - {title}")

    # noinspection PyUnusedLocal
    @pyqtSlot(str, bool)
    def update_error(self, error_msg, notification):
        self.stats.write_records()
        if notification:
            QTimer.singleShot(60000, self.unfreeze_checkviewer)

    def unfreeze_checkviewer(self):
        for check_viewer in self.check_viewers:
            if not check_viewer.check_timer.isActive() and not check_viewer.watcher_timer.isActive():
                check_viewer.start_check_timer()

    @pyqtSlot()
    def prepare_to_exit(self):
        logger.info("Preparing to exit")
        self.stats.write_records()
        for check_viewer in self.check_viewers:
            check_viewer.prepare_to_exit(exit_signal=False)
