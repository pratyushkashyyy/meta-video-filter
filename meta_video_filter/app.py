from __future__ import annotations

import sys
import threading
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .config import ASPECT_RATIOS, DEFAULT_RATIOS
from .pipeline import ProcessingCancelled, run_pipeline


LIGHT_STYLESHEET = """
* {
    font-family: Inter, Segoe UI, Arial, sans-serif;
    font-size: 13px;
    letter-spacing: 0px;
}

QMainWindow, QWidget#appRoot {
    background: #f6f7fb;
    color: #1f2937;
}

QFrame#topBar {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}

QLabel#appTitle {
    color: #111827;
    font-size: 22px;
    font-weight: 700;
}

QLabel#appSubtitle,
QLabel#muted,
QLabel#outputPath,
QLabel#statusText {
    color: #6b7280;
}

QLabel#sectionTitle {
    color: #111827;
    font-size: 14px;
    font-weight: 700;
}

QLabel#statNumber {
    color: #111827;
    font-size: 21px;
    font-weight: 700;
}

QFrame#panel, QGroupBox {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}

QGroupBox {
    margin-top: 18px;
    padding: 14px 12px 12px 12px;
    font-weight: 700;
    color: #111827;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    color: #111827;
    padding: 9px 10px;
    min-height: 20px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}

QComboBox::drop-down {
    border: 0;
    width: 26px;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    color: #111827;
    font-weight: 700;
    padding: 10px 14px;
}

QPushButton:hover {
    background: #f9fafb;
    border-color: #9ca3af;
}

QPushButton:pressed {
    background: #f3f4f6;
}

QPushButton:disabled {
    color: #9ca3af;
    background: #f3f4f6;
    border-color: #e5e7eb;
}

QPushButton#primaryButton {
    background: #2563eb;
    border: 1px solid #2563eb;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background: #1d4ed8;
}

QPushButton#dangerButton {
    background: #ffffff;
    border: 1px solid #fecaca;
    color: #b91c1c;
}

QPushButton#dangerButton:disabled {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #cbd5e1;
}

QCheckBox {
    spacing: 8px;
    color: #374151;
    min-height: 24px;
}

QProgressBar {
    background: #e5e7eb;
    border: 0;
    border-radius: 8px;
    color: transparent;
    min-height: 14px;
    max-height: 14px;
}

QProgressBar::chunk {
    background: #2563eb;
    border-radius: 8px;
}

QTabWidget::pane {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #ffffff;
}

QTabBar::tab {
    background: #f3f4f6;
    color: #6b7280;
    border: 1px solid #e5e7eb;
    border-bottom: 0;
    padding: 10px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #111827;
    border-color: #e5e7eb;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f9fafb;
    border: 0;
    gridline-color: #edf0f5;
    color: #111827;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}

QHeaderView::section {
    background: #f9fafb;
    border: 0;
    border-right: 1px solid #e5e7eb;
    color: #4b5563;
    font-weight: 700;
    padding: 8px 10px;
}

QPlainTextEdit {
    background: #ffffff;
    border: 0;
    color: #374151;
    font-family: JetBrains Mono, Consolas, monospace;
    font-size: 12px;
    padding: 10px;
}
"""


DARK_STYLESHEET = LIGHT_STYLESHEET.replace("#f6f7fb", "#0f1117").replace(
    "#ffffff", "#171a21"
).replace("#111827", "#f3f4f6").replace("#1f2937", "#e5e7eb").replace(
    "#6b7280", "#9ca3af"
).replace(
    "#e5e7eb", "#2a2f3a"
).replace(
    "#d1d5db", "#3a4250"
).replace(
    "#f9fafb", "#1d222b"
).replace(
    "#f3f4f6", "#202632"
).replace(
    "#374151", "#d1d5db"
).replace(
    "#4b5563", "#cbd5e1"
).replace(
    "#edf0f5", "#242a35"
).replace(
    "#eff6ff", "#13213a"
).replace(
    "#dbeafe", "#1e3a5f"
)

DARK_STYLESHEET += """
QPushButton#primaryButton {
    background: #3b82f6;
    border: 1px solid #3b82f6;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background: #60a5fa;
}

QPushButton#dangerButton {
    background: #25171a;
    border: 1px solid #7f1d1d;
    color: #fca5a5;
}

QProgressBar::chunk {
    background: #3b82f6;
}
"""


class PipelineWorker(QObject):
    log = Signal(str)
    progress = Signal(int, int)
    result = Signal(dict)
    finished = Signal()
    failed = Signal(str)

    def __init__(
        self,
        input_folder: str,
        ratios: tuple[str, ...],
        yolo_device: str,
        video_encoder: str,
    ) -> None:
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = str(Path(input_folder) / "Meta_Ad_Output")
        self.ratios = ratios
        self.yolo_device = yolo_device
        self.video_encoder = video_encoder
        self.cancel_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            run_pipeline(
                self.input_folder,
                self.output_folder,
                self.ratios,
                yolo_device=self.yolo_device,
                video_encoder=self.video_encoder,
                log=self.log.emit,
                progress=self.progress.emit,
                result=self.result.emit,
                cancel_event=self.cancel_event,
            )
        except ProcessingCancelled:
            self.log.emit("Cancelled.")
        except Exception:
            self.failed.emit(traceback.format_exc())
        finally:
            self.finished.emit()

    def cancel(self) -> None:
        self.cancel_event.set()


class MainWindow(QMainWindow):
    columns = [
        "file",
        "final_score",
        "hook_motion",
        "motion_avg",
        "scene_cuts",
        "text_overlay_hits",
        "person_hits",
        "brightness",
        "sharpness",
        "audio_rms",
        "audio_spike",
        "group",
        "error",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Meta Video Filter")
        self.resize(1320, 820)
        self.setMinimumSize(1100, 720)
        self.thread: QThread | None = None
        self.worker: PipelineWorker | None = None
        self.result_count = 0
        self.score_color = QColor("#2563eb")

        root = QWidget()
        root.setObjectName("appRoot")
        page = QVBoxLayout(root)
        page.setContentsMargins(18, 18, 18, 18)
        page.setSpacing(14)

        page.addWidget(self.build_top_bar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.addWidget(self.build_setup_panel())
        splitter.addWidget(self.build_workspace())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 940])
        page.addWidget(splitter, 1)

        self.setCentralWidget(root)

    def build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Meta Video Filter")
        title.setObjectName("appTitle")
        subtitle = QLabel("Batch rank, crop, and export ad-ready verticals.")
        subtitle.setObjectName("appSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("statusText")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        theme_label = QLabel("Theme")
        theme_label.setObjectName("muted")
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.currentIndexChanged.connect(self.change_theme)

        layout.addLayout(title_col, 1)
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combo)
        layout.addWidget(self.status_label)
        return bar

    def build_setup_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(320)
        panel.setMaximumWidth(380)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        heading = QLabel("Setup")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        folder_box = QGroupBox("Source")
        folder_layout = QVBoxLayout(folder_box)
        folder_layout.setSpacing(8)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Choose a folder with videos")
        input_button = QPushButton("Choose Folder")
        input_button.setMinimumHeight(40)
        input_button.clicked.connect(self.choose_input)
        self.output_label = QLabel("Output: Meta_Ad_Output")
        self.output_label.setObjectName("outputPath")
        self.output_label.setWordWrap(True)
        folder_layout.addWidget(self.input_edit)
        folder_layout.addWidget(input_button)
        folder_layout.addWidget(self.output_label)
        layout.addWidget(folder_box)

        ratio_box = QGroupBox("Ratios")
        ratio_layout = QVBoxLayout(ratio_box)
        ratio_layout.setSpacing(8)
        self.ratio_checks: dict[str, QCheckBox] = {}
        for key, preset in ASPECT_RATIOS.items():
            checkbox = QCheckBox(preset.label)
            checkbox.setChecked(key in DEFAULT_RATIOS)
            checkbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.ratio_checks[key] = checkbox
            ratio_layout.addWidget(checkbox)
        layout.addWidget(ratio_box)

        hardware_box = QGroupBox("Performance")
        hardware_layout = QGridLayout(hardware_box)
        hardware_layout.setHorizontalSpacing(10)
        hardware_layout.setVerticalSpacing(10)
        hardware_layout.addWidget(QLabel("Person detection"), 0, 0)
        self.yolo_device_combo = QComboBox()
        self.yolo_device_combo.addItem("Auto", "auto")
        self.yolo_device_combo.addItem("Force CPU", "cpu")
        self.yolo_device_combo.addItem("Force NVIDIA GPU", "cuda:0")
        hardware_layout.addWidget(self.yolo_device_combo, 0, 1)
        hardware_layout.addWidget(QLabel("Video export"), 1, 0)
        self.video_encoder_combo = QComboBox()
        self.video_encoder_combo.addItem("Auto", "auto")
        self.video_encoder_combo.addItem("Force CPU", "cpu")
        self.video_encoder_combo.addItem("Force NVIDIA NVENC", "h264_nvenc")
        hardware_layout.addWidget(self.video_encoder_combo, 1, 1)
        layout.addWidget(hardware_box)

        action_box = QFrame()
        action_box.setObjectName("panel")
        action_layout = QVBoxLayout(action_box)
        action_layout.setContentsMargins(14, 14, 14, 14)
        action_layout.setSpacing(10)
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setValue(0)
        self.progress_label = QLabel("0 / 0")
        self.progress_label.setObjectName("muted")
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.start_button = QPushButton("Run Batch")
        self.start_button.setObjectName("primaryButton")
        self.cancel_button = QPushButton("Stop")
        self.cancel_button.setObjectName("dangerButton")
        self.cancel_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_processing)
        self.cancel_button.clicked.connect(self.cancel_processing)
        button_row.addWidget(self.start_button, 1)
        button_row.addWidget(self.cancel_button)
        action_layout.addWidget(self.progress)
        action_layout.addWidget(self.progress_label)
        action_layout.addLayout(button_row)
        layout.addWidget(action_box)

        layout.addStretch()
        return panel

    def build_workspace(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(560)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.processed_stat = self.build_stat_card("0", "Rows")
        self.group_stat = self.build_stat_card("-", "Latest group")
        self.score_stat = self.build_stat_card("-", "Latest score")
        stats_row.addWidget(self.processed_stat)
        stats_row.addWidget(self.group_stat)
        stats_row.addWidget(self.score_stat)
        layout.addLayout(stats_row)

        tabs = QTabWidget()
        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(self.columns.index("audio_rms"), True)
        self.table.setColumnHidden(self.columns.index("audio_spike"), True)
        self.table.setColumnHidden(self.columns.index("error"), True)
        tabs.addTab(self.table, "Results")

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        tabs.addTab(self.log_view, "Run Log")

        layout.addWidget(tabs, 1)
        return panel

    def build_stat_card(self, value: str, label: str) -> QFrame:
        card = QFrame()
        card.setObjectName("panel")
        card.setMinimumHeight(82)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        value_label = QLabel(value)
        value_label.setObjectName("statNumber")
        label_label = QLabel(label)
        label_label.setObjectName("muted")
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        card.value_label = value_label  # type: ignore[attr-defined]
        return card

    @Slot()
    def change_theme(self) -> None:
        theme = str(self.theme_combo.currentData())
        app = QApplication.instance()
        if theme == "dark":
            self.score_color = QColor("#60a5fa")
            if app:
                app.setStyleSheet(DARK_STYLESHEET)
            return

        self.score_color = QColor("#2563eb")
        if app:
            app.setStyleSheet(LIGHT_STYLESHEET)

    @Slot()
    def choose_input(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select input video folder")
        if folder:
            self.input_edit.setText(folder)
            self.input_edit.setCursorPosition(0)
            self.output_label.setText(f"Output: {Path(folder) / 'Meta_Ad_Output'}")

    @Slot()
    def start_processing(self) -> None:
        input_folder = self.input_edit.text().strip()
        ratios = tuple(key for key, checkbox in self.ratio_checks.items() if checkbox.isChecked())
        yolo_device = str(self.yolo_device_combo.currentData())
        video_encoder = str(self.video_encoder_combo.currentData())

        if not input_folder:
            QMessageBox.warning(self, "Missing folder", "Select an input folder.")
            return
        if not ratios:
            QMessageBox.warning(self, "Missing ratios", "Select at least one export ratio.")
            return

        self.result_count = 0
        self.table.setRowCount(0)
        self.log_view.clear()
        self.progress.setValue(0)
        self.progress_label.setText("0 / 0")
        self.processed_stat.value_label.setText("0")  # type: ignore[attr-defined]
        self.group_stat.value_label.setText("-")  # type: ignore[attr-defined]
        self.score_stat.value_label.setText("-")  # type: ignore[attr-defined]
        self.status_label.setText("Running")
        self.set_running(True)

        self.thread = QThread(self)
        self.worker = PipelineWorker(input_folder, ratios, yolo_device, video_encoder)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_log)
        self.worker.progress.connect(self.update_progress)
        self.worker.result.connect(self.add_result)
        self.worker.failed.connect(self.show_failure)
        self.worker.finished.connect(self.processing_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @Slot()
    def cancel_processing(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.append_log("Cancel requested. Waiting for current step to finish...")
            self.status_label.setText("Stopping")

    @Slot(str)
    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    @Slot(int, int)
    def update_progress(self, done: int, total: int) -> None:
        self.progress.setMaximum(max(1, total))
        self.progress.setValue(done)
        self.progress_label.setText(f"{done} / {total}")

    @Slot(dict)
    def add_result(self, row: dict) -> None:
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        for col_index, column in enumerate(self.columns):
            item = QTableWidgetItem(str(row.get(column, "")))
            if column == "final_score":
                item.setForeground(self.score_color)
                font = QFont()
                font.setBold(True)
                item.setFont(font)
            self.table.setItem(row_index, col_index, item)

        self.result_count += 1
        self.processed_stat.value_label.setText(str(self.result_count))  # type: ignore[attr-defined]
        self.group_stat.value_label.setText(str(row.get("group") or "-"))  # type: ignore[attr-defined]
        self.score_stat.value_label.setText(str(row.get("final_score") or "-"))  # type: ignore[attr-defined]

    @Slot(str)
    def show_failure(self, message: str) -> None:
        self.append_log(message)
        self.status_label.setText("Failed")
        QMessageBox.critical(self, "Processing failed", message)

    @Slot()
    def processing_finished(self) -> None:
        self.set_running(False)
        if self.status_label.text() not in {"Failed", "Stopping"}:
            self.status_label.setText("Complete")
        elif self.status_label.text() == "Stopping":
            self.status_label.setText("Stopped")
        self.thread = None
        self.worker = None

    def set_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        for widget in [
            self.input_edit,
            self.yolo_device_combo,
            self.video_encoder_combo,
            self.theme_combo,
            *self.ratio_checks.values(),
        ]:
            widget.setEnabled(not running)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
