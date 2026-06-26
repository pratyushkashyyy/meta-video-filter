from __future__ import annotations

import os
import platform
import sys
import threading
import traceback
from pathlib import Path


def configure_qt_environment() -> None:
    """Prefer the stable X11 Qt backend on Linux Wayland sessions."""
    if platform.system() != "Linux":
        return

    session_type = os.getenv("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.getenv("WAYLAND_DISPLAY")
    if (session_type == "wayland" or wayland_display) and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "Round")


configure_qt_environment()

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .config import DEFAULT_RATIOS, VIDEO_EXTENSIONS
from .distribution import MAX_GROUP_COUNT, MAX_VIDEOS_PER_GROUP, MIN_GROUP_COUNT, MIN_VIDEOS_PER_GROUP
from .pipeline import PipelineError, ProcessingCancelled, run_pipeline
from .scoring import iter_video_files


APP_ICON_PATH = Path(__file__).with_name("assets") / "app_icon.png"


def build_stylesheet(theme: str) -> str:
    if theme == "dark":
        colors = {
            "bg": "#101318",
            "panel": "#171b22",
            "panel_alt": "#1d222b",
            "section": "#141922",
            "border": "#2c3440",
            "border_strong": "#3a4553",
            "text": "#eef2f7",
            "muted": "#9aa4b2",
            "header": "#202732",
            "field": "#11161d",
            "field_disabled": "#1b2028",
            "primary": "#4f8cff",
            "primary_hover": "#6ea2ff",
            "primary_soft": "#13284a",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#f87171",
            "danger_bg": "#27191b",
            "selection": "#21395d",
            "shadow": "#0c0f14",
        }
    else:
        colors = {
            "bg": "#f4f6f8",
            "panel": "#ffffff",
            "panel_alt": "#f8fafc",
            "section": "#ffffff",
            "border": "#d8dee6",
            "border_strong": "#b9c2cf",
            "text": "#17202c",
            "muted": "#647082",
            "header": "#eef2f6",
            "field": "#ffffff",
            "field_disabled": "#eef2f6",
            "primary": "#2563eb",
            "primary_hover": "#1d4ed8",
            "primary_soft": "#eef5ff",
            "success": "#16a34a",
            "warning": "#f59e0b",
            "danger": "#b42318",
            "danger_bg": "#fff5f5",
            "selection": "#dbe7ff",
            "shadow": "#dce2ea",
        }

    return f"""
* {{
    font-family: Inter, Segoe UI, Arial, sans-serif;
    font-size: 13px;
    letter-spacing: 0px;
}}

QMainWindow, QWidget#appRoot {{
    background: {colors["bg"]};
    color: {colors["text"]};
}}

QFrame#topBar {{
    background: {colors["panel"]};
    border: 0;
    border-bottom: 1px solid {colors["border"]};
    border-radius: 0;
}}

QSplitter::handle {{
    background: {colors["bg"]};
}}

QFrame#panel, QFrame#statCard, QFrame#previewCard, QFrame#bottomBar {{
    background: {colors["panel"]};
    border: 1px solid {colors["border"]};
    border-radius: 10px;
}}

QFrame#panel {{
    background: {colors["panel"]};
}}

QFrame#sectionCard, QFrame#runPanel {{
    background: {colors["section"]};
    border: 1px solid {colors["border"]};
    border-radius: 8px;
}}

QFrame#sidebar {{
    background: {colors["panel"]};
    border: 1px solid {colors["border"]};
    border-radius: 10px;
}}

QLabel {{
    color: {colors["text"]};
}}

QLabel#appTitle {{
    color: {colors["text"]};
    font-size: 19px;
    font-weight: 700;
}}

QLabel#appSubtitle,
QLabel#muted,
QLabel#outputPath,
QLabel#statusText,
QLabel#detailLabel,
QLabel#detailValue {{
    color: {colors["muted"]};
}}

QLabel#sectionTitle {{
    color: {colors["text"]};
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}}

QLabel#statNumber {{
    color: {colors["text"]};
    font-size: 22px;
    font-weight: 700;
}}

QLabel#statLabel {{
    color: {colors["muted"]};
    font-size: 12px;
}}

QLabel#statIcon {{
    background: {colors["primary_soft"]};
    border-radius: 12px;
    color: {colors["primary"]};
    font-size: 20px;
    font-weight: 700;
}}

QLabel#sidebarTitle {{
    color: {colors["text"]};
    font-size: 15px;
    font-weight: 700;
}}

QLabel#brandMark {{
    background: {colors["primary"]};
    border-radius: 8px;
    color: #ffffff;
    font-size: 18px;
    font-weight: 800;
}}

QLabel#statusBadge {{
    background: {colors["panel_alt"]};
    border: 1px solid {colors["border"]};
    border-radius: 12px;
    color: {colors["muted"]};
    padding: 5px 10px;
    font-weight: 700;
}}

QLineEdit, QComboBox, QSpinBox {{
    background: {colors["field"]};
    border: 1px solid {colors["border_strong"]};
    border-radius: 7px;
    color: {colors["text"]};
    padding: 8px 9px;
    min-height: 24px;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid {colors["primary"]};
}}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
    background: {colors["field_disabled"]};
    color: {colors["muted"]};
    border-color: {colors["border"]};
}}

QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{
    border: 0;
    width: 22px;
}}

QPushButton {{
    background: {colors["panel"]};
    border: 1px solid {colors["border_strong"]};
    border-radius: 7px;
    color: {colors["text"]};
    font-weight: 700;
    padding: 9px 12px;
}}

QPushButton:hover {{
    background: {colors["panel_alt"]};
    border-color: {colors["primary"]};
}}

QPushButton:disabled {{
    color: {colors["muted"]};
    background: {colors["field_disabled"]};
    border-color: {colors["border"]};
}}

QPushButton#primaryButton {{
    background: {colors["primary"]};
    border: 1px solid {colors["primary"]};
    color: #ffffff;
}}

QPushButton#primaryButton:hover {{
    background: {colors["primary_hover"]};
}}

QPushButton#navButton {{
    background: transparent;
    border: 0;
    border-radius: 0;
    color: {colors["text"]};
    padding: 18px 18px;
}}

QPushButton#activeNavButton {{
    background: {colors["primary_soft"]};
    border: 0;
    border-bottom: 3px solid {colors["primary"]};
    border-radius: 0;
    color: {colors["primary"]};
    padding: 18px 18px;
}}

QPushButton#dangerButton {{
    background: {colors["danger_bg"]};
    border: 1px solid {colors["danger"]};
    color: {colors["danger"]};
}}

QPushButton#dangerButton:disabled {{
    background: {colors["field_disabled"]};
    border-color: {colors["border"]};
    color: {colors["muted"]};
}}

QProgressBar {{
    background: {colors["border"]};
    border: 0;
    border-radius: 5px;
    color: transparent;
    min-height: 10px;
    max-height: 10px;
}}

QProgressBar::chunk {{
    background: {colors["primary"]};
    border-radius: 5px;
}}

QTabWidget::pane {{
    border: 0;
    border-radius: 0;
    background: {colors["panel"]};
    top: -1px;
}}

QTabBar::tab {{
    background: {colors["header"]};
    color: {colors["muted"]};
    border: 1px solid {colors["border"]};
    border-bottom: 0;
    padding: 8px 18px;
    margin-right: 3px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}}

QTabBar::tab:selected {{
    background: {colors["panel"]};
    color: {colors["text"]};
}}

QTableWidget {{
    background: {colors["panel"]};
    alternate-background-color: {colors["panel_alt"]};
    border: 0;
    gridline-color: {colors["border"]};
    color: {colors["text"]};
    selection-background-color: {colors["selection"]};
    selection-color: {colors["text"]};
    outline: 0;
}}

QHeaderView::section {{
    background: {colors["header"]};
    border: 0;
    border-right: 1px solid {colors["border"]};
    color: {colors["muted"]};
    font-weight: 700;
    padding: 8px 10px;
}}

QTableCornerButton::section {{
    background: {colors["header"]};
    border: 0;
}}

QPlainTextEdit {{
    background: {colors["panel"]};
    border: 0;
    color: {colors["text"]};
    font-family: JetBrains Mono, Consolas, monospace;
    font-size: 12px;
    padding: 10px;
}}

QScrollBar:horizontal, QScrollBar:vertical {{
    background: {colors["panel_alt"]};
    border: 0;
    margin: 0;
}}

QScrollBar:horizontal {{
    height: 12px;
}}

QScrollBar:vertical {{
    width: 12px;
}}

QScrollBar::handle:horizontal, QScrollBar::handle:vertical {{
    background: {colors["border_strong"]};
    border-radius: 6px;
    min-width: 32px;
    min-height: 32px;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}

QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}
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
        group_count: int,
        videos_per_group: int,
    ) -> None:
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = str(Path(input_folder) / "Meta_Ad_Output")
        self.ratios = ratios
        self.yolo_device = yolo_device
        self.video_encoder = video_encoder
        self.group_count = group_count
        self.videos_per_group = videos_per_group
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
                group_count=self.group_count,
                videos_per_group=self.videos_per_group,
                log=self.log.emit,
                progress=self.progress.emit,
                result=self.result.emit,
                cancel_event=self.cancel_event,
            )
        except ProcessingCancelled:
            self.log.emit("Cancelled.")
        except PipelineError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.log.emit(traceback.format_exc())
            self.failed.emit("The batch stopped unexpectedly. Check the Run Log for technical details.")
        finally:
            self.finished.emit()

    def cancel(self) -> None:
        self.cancel_event.set()


class MainWindow(QMainWindow):
    columns = [
        "file",
        "group",
        "export_index",
        "export_file",
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
        "error",
    ]
    column_labels = {
        "file": "Original file",
        "group": "Group",
        "export_index": "Export #",
        "export_file": "Export file",
        "final_score": "Score",
        "hook_motion": "Hook motion",
        "motion_avg": "Motion avg",
        "scene_cuts": "Cuts",
        "text_overlay_hits": "Text hits",
        "person_hits": "Person hits",
        "brightness": "Brightness",
        "sharpness": "Sharpness",
        "audio_rms": "Audio RMS",
        "audio_spike": "Audio spike",
        "error": "Error",
    }

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Meta Studio")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1600, 900)
        self.setMinimumSize(1260, 760)
        self.thread: QThread | None = None
        self.worker: PipelineWorker | None = None
        self.result_count = 0
        self.selected_count = 0
        self.top_score_value: float | None = None
        self.score_color = QColor("#2563eb")

        root = QWidget()
        root.setObjectName("appRoot")
        page = QVBoxLayout(root)
        page.setContentsMargins(0, 0, 0, 0)
        page.setSpacing(0)

        page.addWidget(self.build_top_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        work_area = QWidget()
        work_layout = QVBoxLayout(work_area)
        work_layout.setContentsMargins(14, 14, 14, 14)
        work_layout.setSpacing(14)

        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(self.build_setup_panel(), 0)
        content.addWidget(self.build_workspace(), 1)
        content.addWidget(self.build_details_panel(), 0)
        work_layout.addLayout(content, 1)
        work_layout.addWidget(self.build_bottom_bar())

        body.addWidget(work_area, 1)
        page.addLayout(body, 1)

        self.setCentralWidget(root)

    def build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(18)

        brand_mark = QLabel("M")
        brand_mark.setObjectName("brandMark")
        brand_mark.setAlignment(Qt.AlignCenter)
        brand_mark.setFixedSize(34, 34)

        title = QLabel("Meta Studio")
        title.setObjectName("appTitle")

        self.video_filter_tab = QPushButton("Video Filter")
        self.video_filter_tab.setObjectName("activeNavButton")
        self.video_filter_tab.setMinimumHeight(64)
        self.voice_dubbing_tab = QPushButton("Voice Dubbing")
        self.voice_dubbing_tab.setObjectName("navButton")
        self.voice_dubbing_tab.setMinimumHeight(64)
        self.voice_dubbing_tab.setEnabled(False)

        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("statusBadge")
        self.status_label.setAlignment(Qt.AlignCenter)

        theme_label = QLabel("Theme")
        theme_label.setObjectName("muted")
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.currentIndexChanged.connect(self.change_theme)

        layout.addWidget(brand_mark)
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(self.video_filter_tab)
        layout.addWidget(self.voice_dubbing_tab)
        layout.addStretch(1)
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combo)
        layout.addWidget(self.status_label)
        return bar

    def build_section(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        section = QFrame()
        section.setObjectName("sectionCard")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        return section, layout

    def build_setup_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("sidebar")
        panel.setMinimumWidth(310)
        panel.setMaximumWidth(330)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        heading = QLabel("Batch Setup")
        heading.setObjectName("sidebarTitle")
        layout.addWidget(heading)

        source_section, source_layout = self.build_section("Source")
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Choose a folder with videos")
        self.input_edit.setMinimumHeight(42)
        input_button = QPushButton("Choose Folder")
        input_button.setMinimumHeight(42)
        input_button.clicked.connect(self.choose_input)
        self.output_label = QLabel("Output: Meta_Ad_Output")
        self.output_label.setObjectName("outputPath")
        self.output_label.setWordWrap(True)
        source_layout.addWidget(self.input_edit)
        source_layout.addWidget(input_button)
        source_layout.addWidget(self.output_label)
        layout.addWidget(source_section)

        grouping_section, grouping_outer_layout = self.build_section("Grouping")
        grouping_layout = QGridLayout()
        grouping_layout.setHorizontalSpacing(10)
        grouping_layout.setVerticalSpacing(10)
        grouping_layout.addWidget(QLabel("Groups"), 0, 0)
        self.group_count_spin = QSpinBox()
        self.group_count_spin.setRange(MIN_GROUP_COUNT, MAX_GROUP_COUNT)
        self.group_count_spin.setValue(2)
        self.group_count_spin.setMinimumHeight(40)
        grouping_layout.addWidget(self.group_count_spin, 0, 1)
        grouping_layout.addWidget(QLabel("Videos per group"), 1, 0)
        self.videos_per_group_spin = QSpinBox()
        self.videos_per_group_spin.setRange(MIN_VIDEOS_PER_GROUP, MAX_VIDEOS_PER_GROUP)
        self.videos_per_group_spin.setValue(10)
        self.videos_per_group_spin.setMinimumHeight(40)
        grouping_layout.addWidget(self.videos_per_group_spin, 1, 1)
        grouping_outer_layout.addLayout(grouping_layout)
        layout.addWidget(grouping_section)

        hardware_section, hardware_outer_layout = self.build_section("Performance")
        hardware_layout = QGridLayout()
        hardware_layout.setHorizontalSpacing(10)
        hardware_layout.setVerticalSpacing(10)
        hardware_layout.addWidget(QLabel("Person detection"), 0, 0)
        self.yolo_device_combo = QComboBox()
        self.yolo_device_combo.addItem("Auto", "auto")
        self.yolo_device_combo.addItem("Force CPU", "cpu")
        self.yolo_device_combo.addItem("Force NVIDIA GPU", "cuda:0")
        self.yolo_device_combo.setMinimumHeight(40)
        hardware_layout.addWidget(self.yolo_device_combo, 0, 1)
        hardware_layout.addWidget(QLabel("Video export"), 1, 0)
        self.video_encoder_combo = QComboBox()
        self.video_encoder_combo.addItem("Auto", "auto")
        self.video_encoder_combo.addItem("Force CPU", "cpu")
        self.video_encoder_combo.addItem("Force NVIDIA NVENC", "h264_nvenc")
        self.video_encoder_combo.setMinimumHeight(40)
        hardware_layout.addWidget(self.video_encoder_combo, 1, 1)
        hardware_outer_layout.addLayout(hardware_layout)
        layout.addWidget(hardware_section)

        action_box = QFrame()
        action_box.setObjectName("runPanel")
        action_layout = QVBoxLayout(action_box)
        action_layout.setContentsMargins(14, 12, 14, 14)
        action_layout.setSpacing(10)
        run_heading = QLabel("Run")
        run_heading.setObjectName("sectionTitle")
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.start_button = QPushButton("Run Batch")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(42)
        self.cancel_button = QPushButton("Stop")
        self.cancel_button.setObjectName("dangerButton")
        self.cancel_button.setMinimumHeight(42)
        self.cancel_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_processing)
        self.cancel_button.clicked.connect(self.cancel_processing)
        button_row.addWidget(self.start_button, 1)
        button_row.addWidget(self.cancel_button)
        action_layout.addWidget(run_heading)
        action_layout.addLayout(button_row)
        layout.addWidget(action_box)

        layout.addStretch()
        return panel

    def build_workspace(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(560)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.processed_stat = self.build_stat_card("0", "Processed", "P")
        self.group_stat = self.build_stat_card("2", "Groups", "G")
        self.selected_stat = self.build_stat_card("0", "Selected", "S")
        self.score_stat = self.build_stat_card("-", "Top score", "*")
        stats_row.addWidget(self.processed_stat)
        stats_row.addWidget(self.group_stat)
        stats_row.addWidget(self.selected_stat)
        stats_row.addWidget(self.score_stat)
        layout.addLayout(stats_row)

        tabs = QTabWidget()
        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels([self.column_labels[column] for column in self.columns])
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(82)
        self.table.setColumnHidden(self.columns.index("audio_rms"), True)
        self.table.setColumnHidden(self.columns.index("audio_spike"), True)
        self.table.setColumnHidden(self.columns.index("brightness"), True)
        self.table.setColumnHidden(self.columns.index("sharpness"), True)
        self.table.setColumnHidden(self.columns.index("error"), True)
        tabs.addTab(self.table, "Results")

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        tabs.addTab(self.log_view, "Run Log")

        layout.addWidget(tabs, 1)
        return panel

    def build_details_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("previewCard")
        panel.setMinimumWidth(290)
        panel.setMaximumWidth(330)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("VIDEO DETAILS")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.detail_filename = self.build_detail_row(layout, "Filename", "-")
        self.detail_group = self.build_detail_row(layout, "Group", "-")
        self.detail_export = self.build_detail_row(layout, "Export file", "-")
        self.detail_score = self.build_detail_row(layout, "Top score", "-")
        self.detail_motion = self.build_detail_row(layout, "Motion", "-")
        self.detail_text = self.build_detail_row(layout, "Text hits", "-")
        self.detail_person = self.build_detail_row(layout, "Person hits", "-")
        self.detail_output = self.build_detail_row(layout, "Output", "9:16 MP4")
        self.detail_path = self.build_detail_row(layout, "Path", "-")

        layout.addStretch(1)
        return panel

    def build_detail_row(self, parent: QVBoxLayout, label: str, value: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(10)
        label_widget = QLabel(label)
        label_widget.setObjectName("detailLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("detailValue")
        value_widget.setWordWrap(True)
        value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(label_widget)
        row.addWidget(value_widget, 1)
        parent.addLayout(row)
        return value_widget

    def build_bottom_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("bottomBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(18)

        label_col = QVBoxLayout()
        label_col.setSpacing(2)
        heading = QLabel("Batch Progress")
        heading.setObjectName("sectionTitle")
        self.progress_label = QLabel("0 / 0")
        self.progress_label.setObjectName("muted")
        label_col.addWidget(heading)
        label_col.addWidget(self.progress_label)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setValue(0)

        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setObjectName("muted")

        layout.addLayout(label_col)
        layout.addWidget(self.progress, 1)
        layout.addWidget(self.progress_percent_label)
        return bar

    def build_stat_card(self, value: str, label: str, icon: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(96)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        icon_label = QLabel(icon)
        icon_label.setObjectName("statIcon")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(48, 48)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        value_label = QLabel(value)
        value_label.setObjectName("statNumber")
        label_label = QLabel(label)
        label_label.setObjectName("statLabel")
        text_col.addWidget(value_label)
        text_col.addWidget(label_label)
        layout.addWidget(icon_label)
        layout.addLayout(text_col, 1)
        card.value_label = value_label  # type: ignore[attr-defined]
        return card

    @Slot()
    def change_theme(self) -> None:
        theme = str(self.theme_combo.currentData())
        app = QApplication.instance()
        if theme == "dark":
            self.score_color = QColor("#60a5fa")
            if app:
                app.setStyleSheet(build_stylesheet("dark"))
            return

        self.score_color = QColor("#2563eb")
        if app:
            app.setStyleSheet(build_stylesheet("light"))

    def reset_details(self) -> None:
        for label in [
            self.detail_filename,
            self.detail_group,
            self.detail_export,
            self.detail_score,
            self.detail_motion,
            self.detail_text,
            self.detail_person,
            self.detail_path,
        ]:
            label.setText("-")

    @Slot()
    def choose_input(self) -> None:
        options = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select input video folder",
            str(Path.home()),
            options,
        )
        if folder:
            self.input_edit.setText(folder)
            self.input_edit.setCursorPosition(0)
            self.output_label.setText(f"Output: {Path(folder) / 'Meta_Ad_Output'}")

    @Slot()
    def start_processing(self) -> None:
        input_folder = self.input_edit.text().strip()
        ratios = DEFAULT_RATIOS
        yolo_device = str(self.yolo_device_combo.currentData())
        video_encoder = str(self.video_encoder_combo.currentData())
        group_count = int(self.group_count_spin.value())
        videos_per_group = int(self.videos_per_group_spin.value())

        if not input_folder:
            QMessageBox.warning(self, "Missing folder", "Select an input folder.")
            return
        input_path = Path(input_folder).expanduser()
        if not input_path.is_dir():
            QMessageBox.warning(self, "Invalid folder", "Choose an existing folder that contains your source videos.")
            return
        try:
            source_files = iter_video_files(input_path, VIDEO_EXTENSIONS)
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Folder unavailable",
                f"Meta Video Filter cannot read this folder. Choose a different folder or grant macOS access.\n\n{exc}",
            )
            return
        if not source_files:
            supported = ", ".join(extension.upper() for extension in VIDEO_EXTENSIONS)
            QMessageBox.warning(
                self,
                "No videos found",
                f"Choose a folder containing supported video files: {supported}.",
            )
            return
        input_folder = str(input_path)
        self.result_count = 0
        self.selected_count = 0
        self.top_score_value = None
        self.table.setRowCount(0)
        self.log_view.clear()
        self.progress.setValue(0)
        self.progress_label.setText("0 / 0")
        self.progress_percent_label.setText("0%")
        self.reset_details()
        self.processed_stat.value_label.setText("0")  # type: ignore[attr-defined]
        self.group_stat.value_label.setText(str(group_count))  # type: ignore[attr-defined]
        self.selected_stat.value_label.setText("0")  # type: ignore[attr-defined]
        self.score_stat.value_label.setText("-")  # type: ignore[attr-defined]
        self.status_label.setText("Running")
        self.set_running(True)

        self.thread = QThread(self)
        self.worker = PipelineWorker(
            input_folder,
            ratios,
            yolo_device,
            video_encoder,
            group_count,
            videos_per_group,
        )
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
        percent = int(round((done / total) * 100)) if total else 0
        self.progress_percent_label.setText(f"{percent}%")

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
        if row.get("export_file"):
            self.selected_count += 1
        try:
            score = float(row.get("final_score", ""))
        except (TypeError, ValueError):
            score = None
        if score is not None and (self.top_score_value is None or score > self.top_score_value):
            self.top_score_value = score
            self.score_stat.value_label.setText(f"{score:.2f}")  # type: ignore[attr-defined]

        self.processed_stat.value_label.setText(str(self.result_count))  # type: ignore[attr-defined]
        self.selected_stat.value_label.setText(str(self.selected_count))  # type: ignore[attr-defined]
        self.detail_filename.setText(str(row.get("file") or "-"))
        self.detail_group.setText(str(row.get("group") or "-"))
        self.detail_export.setText(str(row.get("export_file") or "-"))
        self.detail_score.setText(str(row.get("final_score") or "-"))
        self.detail_motion.setText(str(row.get("motion_avg") or "-"))
        self.detail_text.setText(str(row.get("text_overlay_hits") or "-"))
        self.detail_person.setText(str(row.get("person_hits") or "-"))
        input_folder = self.input_edit.text().strip()
        self.detail_path.setText(str(Path(input_folder)) if input_folder else "-")

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
            self.group_count_spin,
            self.videos_per_group_spin,
            self.yolo_device_combo,
            self.video_encoder_combo,
            self.theme_combo,
        ]:
            widget.setEnabled(not running)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    app.setStyleSheet(build_stylesheet("light"))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
