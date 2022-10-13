import csv
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


@dataclass
class Record:
    contenders: bool
    min_watched: int
    title: str
    account_id: str


class Stats(QObject):
    changed = pyqtSignal()

    def __init__(self, location: str):
        super().__init__()
        self.file_path = location
        self.records = {}

    def get_records(self):
        return self.records

    def set_record(self, contenders: bool, min_watched: int, title: str, account_id: str):
        self.records[account_id] = Record(contenders, min_watched, title, account_id)
        self.changed.emit()

    def write_record(self, account_id=None):
        if account_id is not None:
            record = self.records.get(account_id)
            if record is not None:
                logger.info("Writing history record: " + account_id)
                self._write(record)
                self.records.pop(account_id)
            else:
                logger.warning("No history record by " + account_id)

            self.changed.emit()

    def write_records(self):
        if len(self.records) > 0:
            logger.info("Writing history records")
            for record in self.records.values():
                self._write(record)

            self.records = {}
            self.changed.emit()

    def _write(self, record):
        file_path = self.file_path.format(record.account_id)
        if os.path.isfile(file_path):
            write_header = False
            write_mode = 'a'
        else:
            write_header = True
            write_mode = 'w'

        contenders = 'owc' if record.contenders else 'owl'
        timestamp = datetime.now().astimezone().isoformat()

        with open(file_path, write_mode) as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['Timestamp', 'Account', 'Type', 'Title', 'Minutes'])
            writer.writerow([
                timestamp,
                record.account_id,
                contenders,
                record.title,
                record.min_watched
            ])


class StatsDialog(QDialog):

    stats: Stats

    def __init__(self, stats: Stats, icon_owl: QIcon, icon_owc: QIcon, accountid=None, parent=None):
        super().__init__(parent)

        self.stats = stats
        self.stats_account = accountid
        stats_owc = [0, 0, 0]
        stats_owl = [0, 0, 0, 0]
        self.setWindowTitle("Stats/History")
        self.setWindowIcon(icon_owl)

        label_owl = QLabel("<h3>Overwatch League</h3>")
        label_owl.setPixmap(icon_owl.pixmap(50, 50))
        label_owc = QLabel("<h3>Overwatch Contenders</h3>")
        label_owc.setPixmap(icon_owc.pixmap(50, 50))

        self.button_layout = QHBoxLayout()
        self.label_account = QLabel()
        self.label_account.setTextFormat(Qt.RichText)
        self.label_account.setText(f"<b> Account: </b> {accountid}" if accountid else '')
        self.button_layout.addWidget(self.label_account)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)
        self.button_layout.addWidget(btn_box)

        self.inner_layout = QGridLayout()

        self.inner_layout.addWidget(label_owl, 0, 0, 3, 1)
        self.inner_layout.addWidget(QLabel("Last 24h"), 0, 1)
        self.inner_layout.addWidget(QLabel("Last 7d"), 1, 1)
        self.inner_layout.addWidget(QLabel("This month"), 2, 1)
        self.inner_layout.addWidget(QLabel("All-time"), 3, 1)
        self.inner_layout.addWidget(QLabel(str(stats_owl[0]) + " min"), 0, 2)
        self.inner_layout.addWidget(QLabel(str(stats_owl[1]) + " min"), 1, 2)
        self.inner_layout.addWidget(QLabel(str(stats_owl[2]) + " min"), 2, 2)
        self.inner_layout.addWidget(QLabel(str(stats_owl[3]) + " min"), 3, 2)
        self.inner_layout.addWidget(QLabel(str(round(stats_owl[0] / 60, 2)) + "h"), 0, 3)
        self.inner_layout.addWidget(QLabel(str(round(stats_owl[1] / 60, 2)) + "h"), 1, 3)
        self.inner_layout.addWidget(QLabel(str(round(stats_owl[2] / 60, 2)) + "h"), 2, 3)
        self.inner_layout.addWidget(QLabel(str(round(stats_owl[3] / 60, 2)) + "h"), 3, 3)
        self.inner_layout.addWidget(QLabel(str(int(stats_owl[0] / 60) * 5) + " tokens"), 0, 4)
        self.inner_layout.addWidget(QLabel(str(int(stats_owl[1] / 60) * 5) + " tokens"), 1, 4)
        self.inner_layout.addWidget(QLabel(str(int(stats_owl[2] / 60) * 5) + " tokens"), 2, 4)
        self.inner_layout.addWidget(QLabel(str(int(stats_owl[3] / 60) * 5) + " tokens"), 3, 4)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setLineWidth(3)
        self.inner_layout.addWidget(line, 4, 0, 2, 5)

        self.inner_layout.addWidget(label_owc, 6, 0, 3, 1)
        self.inner_layout.addWidget(QLabel("Last 24h"), 6, 1)
        self.inner_layout.addWidget(QLabel("Last 7d"), 7, 1)
        self.inner_layout.addWidget(QLabel("This month"), 8, 1)
        self.inner_layout.addWidget(QLabel(str(stats_owc[0]) + " min"), 6, 2)
        self.inner_layout.addWidget(QLabel(str(stats_owc[1]) + " min"), 7, 2)
        self.inner_layout.addWidget(QLabel(str(stats_owc[2]) + " min"), 8, 2)
        self.inner_layout.addWidget(QLabel(str(round(stats_owc[0] / 60, 2)) + "h"), 6, 3)
        self.inner_layout.addWidget(QLabel(str(round(stats_owc[1] / 60, 2)) + "h"), 7, 3)
        self.inner_layout.addWidget(QLabel(str(round(stats_owc[2] / 60, 2)) + "h"), 8, 3)

        outer_layout = QVBoxLayout()
        outer_layout.addLayout(self.inner_layout)
        outer_layout.addLayout(self.button_layout)
        outer_layout.setSpacing(20)

        self.setLayout(outer_layout)

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def show_dialog(self, accountid: str):
        logger.info("Opening stats dialog")
        self.stats_account = accountid
        self._update_values()

        self.show()
        self.raise_()
        self.activateWindow()

        self.stats.changed.connect(self._update_values)
        # This below causes crashes due to finished signal returning an int
        # self.finished.connect(self.stats.changed.disconnect)
        # Use lambda to ignore int returned from finished signal
        self.finished.connect(lambda x: self.stats.changed.disconnect)

    def _update_values(self):
        logger.debug("Updating values on dialog")
        stats_owl, stats_owc = self._get_stats_summary(self.stats_account)
        self._replace_values(stats_owl, stats_owc, self.stats_account)

    def _get_stats_summary(self, account_id: str):
        stats_data = []

        record = self.stats.get_records().get(account_id)
        if record:
            stats_data.append(
                {
                    'Timestamp': datetime.now().astimezone().isoformat(),
                    'Account': record.account_id,
                    'Type': 'owc' if record.contenders else 'owl',
                    'Title': record.title,
                    'Minutes': record.min_watched
                })

        file_path = self.stats.file_path.format(account_id)
        if os.path.isfile(file_path):
            with open(file_path, 'r', newline='') as history_file:
                stats_data.extend(csv.DictReader(history_file))
                logger.debug("Loaded history file")

        stats_owl, stats_owc = self._process_data(stats_data, account_id)

        return stats_owl, stats_owc

    def _process_data(self, history_data: list, accountid: str) -> (list, list):
        range_day = datetime.now().astimezone() - timedelta(hours=24)
        range_week = datetime.now().astimezone() - timedelta(days=7)
        current_month = datetime.now().astimezone().month

        stats_owl = [0, 0, 0, 0]
        stats_owc = [0, 0, 0]

        for row in history_data:
            try:
                if row['Account'] == accountid:
                    stats_owl[3] += int(row['Minutes'])
                    if datetime.fromisoformat(row['Timestamp']) > range_day:
                        if row['Type'] == 'owl':
                            stats_owl[0] += int(row['Minutes'])
                            stats_owl[1] += int(row['Minutes'])
                        elif row['Type'] == 'owc':
                            stats_owc[0] += int(row['Minutes'])
                            stats_owc[1] += int(row['Minutes'])
                    elif datetime.fromisoformat(row['Timestamp']) > range_week:
                        if row['Type'] == 'owl':
                            stats_owl[1] += int(row['Minutes'])
                        elif row['Type'] == 'owc':
                            stats_owc[1] += int(row['Minutes'])
                    if datetime.fromisoformat(row['Timestamp']).month == current_month:
                        if row['Type'] == 'owl':
                            stats_owl[2] += int(row['Minutes'])
                        elif row['Type'] == 'owc':
                            stats_owc[2] += int(row['Minutes'])
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Malformed history file at {row} -  {e}")
                continue

        return stats_owl, stats_owc

    def _replace_values(self, stats_owl: list, stats_owc: list, accountid: str):
        self.label_account.setText(f"<b> Account: </b> {accountid}")
        self.inner_layout.itemAtPosition(0, 2).widget().setText(str(stats_owl[0]) + " min")
        self.inner_layout.itemAtPosition(1, 2).widget().setText(str(stats_owl[1]) + " min")
        self.inner_layout.itemAtPosition(2, 2).widget().setText(str(stats_owl[2]) + " min")
        self.inner_layout.itemAtPosition(3, 2).widget().setText(str(stats_owl[3]) + " min")
        self.inner_layout.itemAtPosition(0, 3).widget().setText(str(round(stats_owl[0] / 60, 2)) + "h")
        self.inner_layout.itemAtPosition(1, 3).widget().setText(str(round(stats_owl[1] / 60, 2)) + "h")
        self.inner_layout.itemAtPosition(2, 3).widget().setText(str(round(stats_owl[2] / 60, 2)) + "h")
        self.inner_layout.itemAtPosition(3, 3).widget().setText(str(round(stats_owl[3] / 60, 2)) + "h")
        self.inner_layout.itemAtPosition(0, 4).widget().setText(str(int(stats_owl[0] / 60) * 5) + " tokens")
        self.inner_layout.itemAtPosition(1, 4).widget().setText(str(int(stats_owl[1] / 60) * 5) + " tokens")
        self.inner_layout.itemAtPosition(2, 4).widget().setText(str(int(stats_owl[2] / 60) * 5) + " tokens")
        self.inner_layout.itemAtPosition(3, 4).widget().setText(str(int(stats_owl[3] / 60) * 5) + " tokens")
        self.inner_layout.itemAtPosition(6, 2).widget().setText(str(stats_owc[0]) + " min")
        self.inner_layout.itemAtPosition(7, 2).widget().setText(str(stats_owc[1]) + " min")
        self.inner_layout.itemAtPosition(8, 2).widget().setText(str(stats_owc[2]) + " min")
        self.inner_layout.itemAtPosition(6, 3).widget().setText(str(round(stats_owc[0] / 60, 2)) + "h")
        self.inner_layout.itemAtPosition(7, 3).widget().setText(str(round(stats_owc[1] / 60, 2)) + "h")
        self.inner_layout.itemAtPosition(8, 3).widget().setText(str(round(stats_owc[2] / 60, 2)) + "h")


def main():
    logging.basicConfig(level=logging.INFO)

    app = QApplication([])

    test_accountid = "123456789"
    stats = Stats('history.123456789.csv')
    stats.set_record(contenders=True, min_watched=24, title="Fake OWL test", account_id=test_accountid)
    stats.write_record(test_accountid)
    stats.set_record(contenders=True, min_watched=24, title="Fake OWL test", account_id=test_accountid)
    stats.write_records()

    app.exec_()


if __name__ == "__main__":
    main()
