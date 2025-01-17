from PyQt5.QtCore import *

import requests

import utils.checker as checker
from utils.viewer import Viewer, ViewerStatusCodeError

import logging

logger = logging.getLogger(__name__)


class CheckViewer(QObject):
    check_progress = pyqtSignal(int, str)
    checking = pyqtSignal()
    watching_owl = pyqtSignal(str, int, str, bool)
    watching_owc = pyqtSignal(str, int, str, bool)
    error = pyqtSignal(str, bool)
    false_tracking = pyqtSignal(bool)
    exit_signal = pyqtSignal()

    viewer = None
    viewer_title = None
    contenders = None

    def __init__(self, userid=None, owl_flag=True, owc_flag=True, min_check=10, force_rewards=False):
        super().__init__()
        logger.info(f"{userid}: Starting checkviewer")

        self.check_counter = 0
        self.min_check = min_check
        self.userid = userid
        self.owl_flag = owl_flag
        self.owc_flag = owc_flag
        self.force_rewards = force_rewards
        self.watcher_timer = QTimer()
        self.check_timer = QTimer()

    def run(self):
        # Create QTimers
        self.watcher_timer.setInterval(60000)
        self.watcher_timer.timeout.connect(self.watch)
        self.check_timer.setInterval(60000)
        self.check_timer.timeout.connect(self.timeout_check_timer)
        if self.userid:
            self.start_check_timer()

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def set_owl_flag(self, checked):
        if checked:
            self.owl_flag = True
            if not self.watcher_timer.isActive():
                self.start_check_timer()
        else:
            self.owl_flag = False
            if self.watcher_timer.isActive() and not self.contenders:
                self.watching_owl.emit(self.userid, self.viewer.time_watched, self.viewer_title, True)
                self.start_check_timer(check=False)

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def set_owc_flag(self, checked):
        if checked:
            self.owc_flag = True
            if not self.watcher_timer.isActive():
                self.start_check_timer()
        else:
            self.owc_flag = False
            if self.watcher_timer.isActive() and self.contenders:
                self.watching_owc.emit(self.userid, self.viewer.time_watched, self.viewer_title, True)
                self.start_check_timer(check=False)

    @pyqtSlot(str)
    def set_userid(self, userid):
        logger.info(f"Setting userid - {userid}")
        self.userid = userid
        self.start_check_timer()

    @pyqtSlot(int)
    def set_min_check(self, min_check):
        self.min_check = min_check

    @pyqtSlot(int)
    @pyqtSlot(bool)
    def set_force_rewards(self, checked):
        self.force_rewards = True if checked else False
        if self.check_timer.isActive():
            self.start_check_timer()

    @pyqtSlot()
    def start_check_timer(self, check=True):
        logger.debug("Starting checker timer")
        self.watcher_timer.stop()
        self.check_timer.start()
        if check:
            self.check_if_live()

    @pyqtSlot()
    def timeout_check_timer(self):
        if self.check_counter >= self.min_check:
            self.check_counter = 0
            self.check_if_live()
        else:
            self.check_counter += 1
            self.check_progress.emit(self.min_check - self.check_counter, self.userid)

    def check_if_live(self):
        logger.info(f"{self.userid}: Checking if live")
        self.checking.emit()
        try:
            if self.owl_flag and (
                    video_player_owl := checker.check_page_islive(contenders=False, ignore_rewards=self.force_rewards)):
                logger.info(f"{self.userid}: OWL is Live")
                self.start_watching(video_player_owl, False)
            elif self.owc_flag and (
                    video_player_owc := checker.check_page_islive(contenders=True, ignore_rewards=self.force_rewards)):
                logger.info(f"{self.userid}: OWC is live")
                self.start_watching(video_player_owc, True)
            else:
                self.check_progress.emit(self.min_check, self.userid)
        except requests.exceptions.Timeout:
            logger.error(f"{self.userid}: Checker Timeout error")
            self.error.emit(f"{self.userid}: Checker timeout'ed", False)
        except requests.exceptions.HTTPError as errh:
            logger.error(f"{self.userid}: Checker HTTP error - {errh.response.status_code}")
            self.error.emit(f"{self.userid}: Checker HTTP error - {errh.response.status_code}", True)
        except requests.exceptions.ConnectionError:
            logger.error(f"{self.userid}: Checker ConnectionError")
            self.error.emit(f"{self.userid}: Couldn't connect - Check internet", False)
        except requests.exceptions.RequestException as err:
            logger.error(f"{self.userid}: Checker Requests error - {err}")
            self.error.emit(f"{self.userid}: Unknown error (requests). Check Logs", True)
        except Exception as e:
            logger.error(f"{self.userid}: Checker Exception - {e}")
            self.error.emit(f"{self.userid}: OWL/OWC Page incorrectly formatted/error", True)

    def start_watching(self, video_player, contenders=False):
        logger.info(f"{self.userid}: Start Watching")
        # Stop checker QTimer
        self.check_timer.stop()

        self.viewer = Viewer(self.userid, video_player['video']['id'], video_player['uid'], contenders)
        self.viewer_title = video_player['video']['metadata']['title']

        # Create viewer QTimer
        self.watcher_timer.start()

        self.contenders = contenders
        self.watch()

    @pyqtSlot()
    def watch(self):
        logger.info(f"{self.userid}: Sending sentinel packets")
        try:
            tracking_status = self.viewer.send_sentinel_packets()
        except requests.exceptions.Timeout:
            logger.error(f"{self.userid}: Watcher Timeout error")
            self.error.emit(f"{self.userid}: Watcher timeout'ed", False)
            self.viewer.restart_session()
            self.viewer.time_watched = 0
        except requests.exceptions.HTTPError as errh:
            logger.error(f"{self.userid}: Watcher HTTP error - {errh.response.status_code}")
            self.error.emit(f"{self.userid}: Watcher HTTP error - {errh.response.status_code}", True)
            self.watcher_timer.stop()
            self.start_check_timer(check=False)
        except requests.exceptions.ConnectionError:
            logger.error(f"{self.userid}: Watcher ConnectionError")
            self.error.emit(f"{self.userid}: Couldn't connect - Check internet", False)
            self.watcher_timer.stop()
            self.start_check_timer(check=True)
        except requests.exceptions.RequestException as err:
            logger.error(f"{self.userid}: Watcher Requests error - {err}")
            self.error.emit(f"{self.userid}: Unknown error (requests). Check Logs", True)
            self.watcher_timer.stop()
            self.start_check_timer(check=False)
        except ViewerStatusCodeError as e:
            logger.error(f"{self.userid}: Watcher Bad API Response - {e.response}")
            self.error.emit(f"{self.userid}: Bad response from API. Check Logs", True)
            self.watcher_timer.stop()
            self.start_check_timer(check=False)
        except Exception as e:
            logger.error(f"{self.userid}: Watcher Exception - {e}")
            self.error.emit(f"{self.userid}: Unknown error (watcher). Check Logs", True)
            self.watcher_timer.stop()
            self.start_check_timer(check=False)
        else:
            if tracking_status:
                if self.contenders:
                    self.watching_owc.emit(self.userid, self.viewer.time_watched, self.viewer_title, False)
                else:
                    self.watching_owl.emit(self.userid, self.viewer.time_watched, self.viewer_title, False)
                self.viewer.time_watched += 1
            elif self.viewer.time_watched:
                self.watcher_timer.stop()
                if self.contenders:
                    self.watching_owc.emit(self.userid, self.viewer.time_watched, self.viewer_title, True)
                else:
                    self.watching_owl.emit(self.userid, self.viewer.time_watched, self.viewer_title, True)
                self.start_check_timer(check=False)
            else:
                logger.warning(f"{self.userid}: Watched for 0 minutes. Stream has probably ended")
                self.false_tracking.emit(self.contenders)
                self.start_check_timer(check=False)
                pass

    @pyqtSlot(bool)
    def prepare_to_exit(self, exit_signal):
        logger.info(f"{self.userid}: Preparing to exit")
        self.check_timer.stop()
        self.watcher_timer.stop()
        if exit_signal:
            self.exit_signal.emit()
