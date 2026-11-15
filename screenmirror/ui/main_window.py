from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from screenmirror.adb import AdbDevice, AdbManager
from screenmirror.dynamic_settings import is_display_only_option_allowed
from screenmirror.i18n import (
    LANGUAGE_NAMES,
    font_family_for_language,
    translate,
    translate_message,
    translate_scrcpy_category,
    translate_scrcpy_description,
)
from screenmirror.scrcpy import ScrcpySession, find_scrcpy
from screenmirror.scrcpy_help import ScrcpyOption
from screenmirror.settings import AppSettings, DynamicSettings, UiSettings


THEME = """
QMainWindow, QWidget { background: #111315; color: #e7e9e7; font-family: "__FONT_FAMILY__"; font-size: 10pt; }
QFrame#surface { background: #1a1d1f; border: 1px solid #2c3133; border-radius: 10px; }
QFrame#sidebar { background: #151819; border: 0; border-right: 1px solid #2a2e30; border-radius: 0; }
QLabel#muted { color: #9ba29f; }
QLabel#pageTitle { color: #f2f4f2; font-size: 19pt; font-weight: 650; }
QLabel#sectionTitle { color: #f2f4f2; font-size: 12pt; font-weight: 600; }
QLabel#metric { color: #f3f5f3; font-size: 21pt; font-weight: 650; }
QLabel#statusConnected { color: #b9f36b; background: #26351b; border: 1px solid #435b2a; border-radius: 10px; padding: 4px 9px; font-weight: 600; }
QLabel#statusWarning { color: #f4c66b; background: #392e1a; border: 1px solid #62502a; border-radius: 10px; padding: 4px 9px; font-weight: 600; }
QLabel#statusNeutral { color: #c2c8c5; background: #252a2c; border: 1px solid #3a4042; border-radius: 10px; padding: 4px 9px; font-weight: 600; }
QLabel#statusError { color: #ff8b82; background: #3b2221; border: 1px solid #633633; border-radius: 10px; padding: 4px 9px; font-weight: 600; }
QPushButton { background: #252a2c; border: 1px solid #3a4143; border-radius: 7px; padding: 8px 12px; color: #e7e9e7; }
QPushButton:hover { background: #303638; border-color: #596260; }
QPushButton:pressed { background: #202425; }
QPushButton:disabled { color: #68706d; background: #1c2021; border-color: #2b3031; }
QPushButton#primary { color: #14190f; background: #a5dc55; border-color: #a5dc55; font-weight: 700; }
QPushButton#primary:hover { background: #b7eb69; border-color: #b7eb69; }
QPushButton#danger { color: #ffaaa2; border-color: #633633; background: #322120; }
QPushButton#nav { text-align: left; background: transparent; border: 1px solid transparent; padding: 9px 11px; color: #b8bfbc; }
QPushButton#nav:hover { background: #202526; color: #f1f3f1; }
QPushButton#nav:checked { background: #29321f; color: #c4f47d; border-color: #43562e; font-weight: 600; }
QPushButton#deviceCard { text-align: left; background: #1a1d1f; border: 1px solid #303638; padding: 14px; }
QPushButton#deviceCard:hover { background: #202526; border-color: #65705d; }
QPushButton#deviceCard:checked { border: 1px solid #a5dc55; background: #20271b; }
QPushButton#deviceCard[state="device"] { border-left: 3px solid #83b844; }
QPushButton#deviceCard[state="unauthorized"] { border-left: 3px solid #d5a84f; }
QPushButton#deviceCard[state="offline"] { border-left: 3px solid #6b7471; }
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit { background: #151819; border: 1px solid #373e40; border-radius: 6px; padding: 7px; color: #e7e9e7; selection-background-color: #5d7e32; }
QComboBox QAbstractItemView { background: #1a1d1f; color: #e7e9e7; selection-background-color: #40592b; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { width: 9px; background: #151819; margin: 2px; }
QScrollBar::handle:vertical { background: #3a4241; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


class MainWindow(QMainWindow):
    def __init__(self, project_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.adb = AdbManager(project_root, self)
        self.scrcpy = ScrcpySession(find_scrcpy(project_root), self)
        self.settings = AppSettings.load()
        self.ui_settings = UiSettings.load()
        self.language = self.ui_settings.language
        self.dynamic_settings = DynamicSettings()
        self._selected_device_serial = ""
        self._current_page = "Dashboard"
        self._adb_busy = False
        self._screenshot_busy = False
        self._last_adb_status = "Checking ADB service…"
        self._last_feedback: tuple[str, str] | None = None
        self._adb_version = "Not checked"
        self._recent_screenshots: list[str] = []
        self._device_card_buttons: dict[str, QPushButton] = {}
        self._nav_buttons: dict[str, QPushButton] = {}
        self._page_indices: dict[str, int] = {}
        self._close_requested = False
        self._shutdown_complete = False
        self._shutdown_services_pending: set[str] = set()

        self.setWindowTitle("ScreenMirror")
        self.setWindowIcon(QIcon(str(project_root / "assets" / "screenmirror.png")))
        self._apply_language_font()
        self.setMinimumSize(1040, 640) if self.language == "km" else self.setMinimumSize(960, 600)
        self.resize(1280, 800)
        self._build_shell()
        self._connect_services()
        self._refresh_profile_labels()

        if self.adb.adb_path is None:
            self.on_adb_error("Host-matched ADB executable was not found.")
        else:
            self.host_label.setText(
                self._t("ADB executable: {path}", path=self.adb.adb_path)
            )
            self.adb.check_version()
        QTimer.singleShot(0, self.scrcpy.start_discovery)

    def _build_shell(self) -> None:
        self._nav_buttons = {}
        self._page_indices = {}
        self._device_card_buttons = {}
        root = QWidget(self)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame(root)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220 if self.language == "km" else 196)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 20, 14, 16)
        side_layout.setSpacing(7)

        brand_row = QHBoxLayout()
        mark = QLabel("SM")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(38, 38)
        mark.setStyleSheet("background:#a5dc55;color:#151a11;border-radius:10px;font-weight:800;font-size:12pt;")
        brand_name = QLabel("ScreenMirror")
        brand_name.setStyleSheet("font-size:13pt;font-weight:700;color:#f2f4f2;")
        brand_row.addWidget(mark)
        brand_row.addSpacing(8)
        brand_row.addWidget(brand_name)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)
        side_layout.addSpacing(20)

        nav_items = [
            ("Dashboard", "▦"), ("Devices", "▣"), ("Mirroring", "◉"),
            ("Screenshots", "▧"), ("Recordings", "●"), ("Diagnostics", "⌁"),
        ]
        for title, glyph in nav_items:
            self._add_nav(side_layout, title, glyph)
        side_layout.addSpacing(12)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color:#2a2e30;")
        side_layout.addWidget(divider)
        self._add_nav(side_layout, "Settings", "⚙")
        self._add_nav(side_layout, "About", "ⓘ")
        side_layout.addStretch()
        self.sidebar_footer = QLabel(self._t("Native scrcpy engine\nADB device manager"))
        self.sidebar_footer.setObjectName("muted")
        self.sidebar_footer.setStyleSheet("color:#7e8783;font-size:9pt;")
        side_layout.addWidget(self.sidebar_footer)
        shell.addWidget(sidebar)

        main_area = QWidget(root)
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(24, 18, 24, 18)
        main_layout.setSpacing(16)
        header = QHBoxLayout()
        self.page_title = QLabel(self._t("Dashboard"))
        self.page_title.setObjectName("pageTitle")
        header.addWidget(self.page_title)
        header.addStretch()
        self.adb_badge = QLabel(self._t("ADB · Starting"))
        self.adb_badge.setObjectName("statusNeutral")
        header.addWidget(self.adb_badge)
        self.device_count_badge = QLabel(self._t("{count} devices", count=0))
        self.device_count_badge.setObjectName("statusNeutral")
        header.addWidget(self.device_count_badge)
        self.refresh_button = QPushButton(self._t("↻  Refresh"))
        self.refresh_button.clicked.connect(self.adb_refresh)
        header.addWidget(self.refresh_button)
        main_layout.addLayout(header)

        self.page_stack = QStackedWidget(main_area)
        self._build_pages()
        main_layout.addWidget(self.page_stack, 1)
        self.status_label = QLabel(self._t("Starting…"))
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(22)
        main_layout.addWidget(self.status_label)
        shell.addWidget(main_area, 1)
        self.setCentralWidget(root)
        self._navigate(self._current_page)

    def _t(self, text: str, **values: object) -> str:
        return translate(text, self.language, **values)

    def _message(self, message: str) -> str:
        return translate_message(message, self.language)

    def _apply_language_font(self) -> None:
        family = font_family_for_language(self.language)
        font = QFont(family, 10)
        app = QApplication.instance()
        if app is not None:
            app.setFont(font)
        self.setStyleSheet(THEME.replace("__FONT_FAMILY__", family))

    def _change_language(self, index: int) -> None:
        language = self.language_combo.itemData(index)
        if language not in {"en", "km"} or language == self.language:
            return
        self.language = language
        self.ui_settings.language = language
        self.ui_settings.save()
        self.setMinimumSize(1040, 640) if language == "km" else self.setMinimumSize(960, 600)
        if self.width() < self.minimumWidth() or self.height() < self.minimumHeight():
            self.resize(max(self.width(), self.minimumWidth()), max(self.height(), self.minimumHeight()))
        self._apply_language_font()
        diagnostic_text = self.diagnostics.toPlainText() if hasattr(self, "diagnostics") else ""
        old_central = self.takeCentralWidget()
        if old_central is not None:
            old_central.deleteLater()
        self._build_shell()
        if diagnostic_text:
            self.diagnostics.setPlainText(diagnostic_text)
        self._refresh_profile_labels()
        self._refresh_screenshot_list()
        self.update_devices(self.adb.devices)
        self.set_busy(self._adb_busy)
        self.set_screenshot_busy(self._screenshot_busy)
        self._refresh_mirroring_state()
        self._restore_last_feedback()

    def _restore_last_feedback(self) -> None:
        if self._last_feedback is None:
            return
        kind, message = self._last_feedback
        rendered = self._message(message)
        if kind == "status":
            self.status_label.setText(rendered)
        else:
            self.status_label.setText(f"{self._t('Error')}: {rendered}")
            if kind == "adb_error":
                self.adb_badge.setText(self._t("ADB · Attention"))
                self.adb_badge.setObjectName("statusError")
                self._repolish(self.adb_badge)
                self.dashboard_status.setText(f"{self._t('Error')}: {rendered}")

    def _add_nav(self, layout: QVBoxLayout, title: str, glyph: str) -> None:
        button = QPushButton(f"{glyph}    {self._t(title)}")
        button.setObjectName("nav")
        button.setCheckable(True)
        button.clicked.connect(lambda _checked=False, name=title: self._navigate(name))
        self._nav_buttons[title] = button
        layout.addWidget(button)

    def _build_pages(self) -> None:
        builders = {
            "Dashboard": self._build_dashboard,
            "Devices": self._build_devices_page,
            "Mirroring": self._build_mirroring_page,
            "Screenshots": self._build_screenshots_page,
            "Recordings": self._build_recordings_page,
            "Diagnostics": self._build_diagnostics_page,
            "Settings": self._build_settings_page,
            "About": self._build_about_page,
        }
        for name, builder in builders.items():
            scroll = QScrollArea(self.page_stack)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            page = QWidget()
            page.setObjectName("page")
            content = QVBoxLayout(page)
            content.setContentsMargins(2, 2, 8, 8)
            content.setSpacing(14)
            builder(content)
            content.addStretch(1)
            scroll.setWidget(page)
            self._page_indices[name] = self.page_stack.addWidget(scroll)

    def _card(self, title: str = "") -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("surface")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(9)
        if title:
            label = QLabel(self._t(title))
            label.setObjectName("sectionTitle")
            label.setWordWrap(True)
            layout.addWidget(label)
        return card, layout

    def _muted(self, text: str) -> QLabel:
        label = QLabel(self._t(text))
        label.setObjectName("muted")
        label.setWordWrap(True)
        return label

    def _build_dashboard(self, layout: QVBoxLayout) -> None:
        intro = QLabel(self._t("Your Android workspace"))
        intro.setObjectName("muted")
        layout.addWidget(intro)
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.dashboard_adb_value = QLabel(self._t("Checking…"))
        self.dashboard_device_value = QLabel("0")
        self.dashboard_mirror_value = QLabel(self._t("Stopped"))
        for title, value in (("ADB service", self.dashboard_adb_value), ("Ready devices", self.dashboard_device_value), ("Mirroring", self.dashboard_mirror_value)):
            card, inner = self._card(title)
            value.setObjectName("metric")
            inner.addWidget(value)
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        row = QHBoxLayout()
        row.setSpacing(12)
        selected, selected_layout = self._card("Selected device")
        self.dashboard_selected = QLabel(self._t("No device selected"))
        self.dashboard_selected.setObjectName("sectionTitle")
        self.dashboard_selected.setWordWrap(True)
        selected_layout.addWidget(self.dashboard_selected)
        self.dashboard_selected_detail = self._muted("Connect an Android device and select it in Devices.")
        selected_layout.addWidget(self.dashboard_selected_detail)
        choose = QPushButton(self._t("Manage devices"))
        choose.clicked.connect(lambda: self._navigate("Devices"))
        selected_layout.addWidget(choose, 0, Qt.AlignmentFlag.AlignLeft)
        row.addWidget(selected, 1)

        profile, profile_layout = self._card("Mirror profile")
        self.dashboard_profile = QLabel()
        self.dashboard_profile.setObjectName("sectionTitle")
        self.dashboard_profile.setWordWrap(True)
        profile_layout.addWidget(self.dashboard_profile)
        profile_layout.addWidget(self._muted("Native video decoding and rendering are handled by scrcpy."))
        mirror = QPushButton(self._t("Open mirroring controls"))
        mirror.clicked.connect(lambda: self._navigate("Mirroring"))
        profile_layout.addWidget(mirror, 0, Qt.AlignmentFlag.AlignLeft)
        row.addWidget(profile, 1)
        layout.addLayout(row)

        service_card, service_layout = self._card("Connection status")
        self.dashboard_status = self._muted(self._last_adb_status)
        service_layout.addWidget(self.dashboard_status)
        layout.addWidget(service_card)

    def _build_devices_page(self, layout: QVBoxLayout) -> None:
        intro = QLabel(self._t("USB and wireless Android devices discovered by the host-matched ADB executable."))
        intro.setObjectName("muted")
        layout.addWidget(intro)
        actions = QHBoxLayout()
        self.start_button = QPushButton(self._t("Start ADB server"))
        self.start_button.clicked.connect(self.adb.start_server)
        self.stop_button = QPushButton(self._t("Stop ADB server"))
        self.stop_button.setObjectName("danger")
        self.stop_button.clicked.connect(self.adb.stop_server)
        self.disconnect_button = QPushButton(self._t("Disconnect selected"))
        self.disconnect_button.clicked.connect(self.disconnect_selected)
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addWidget(self.disconnect_button)
        actions.addStretch()
        layout.addLayout(actions)

        devices_card, devices_layout = self._card("Available devices")
        self.device_cards_layout = devices_layout
        self.device_empty_label = self._muted("No Android devices detected. Connect by USB, enable USB debugging, and authorize this computer on the phone.")
        devices_layout.addWidget(self.device_empty_label)
        layout.addWidget(devices_card)

        wireless, wireless_layout = self._card("Wireless ADB")
        form = QFormLayout()
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("192.168.1.20:5555")
        self.code_edit = QLineEdit()
        self.code_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.code_edit.setPlaceholderText(self._t("Pairing code"))
        form.addRow(self._t("Host and port"), self.target_edit)
        form.addRow(self._t("Pairing code"), self.code_edit)
        wireless_layout.addLayout(form)
        wireless_buttons = QHBoxLayout()
        pair_button = QPushButton(self._t("Pair device"))
        pair_button.clicked.connect(self.pair_wireless)
        connect_button = QPushButton(self._t("Connect"))
        connect_button.setObjectName("primary")
        connect_button.clicked.connect(lambda: self.adb.connect_wireless(self.target_edit.text()))
        wireless_buttons.addWidget(pair_button)
        wireless_buttons.addWidget(connect_button)
        wireless_buttons.addStretch()
        wireless_layout.addLayout(wireless_buttons)
        layout.addWidget(wireless)

    def _build_mirroring_page(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._muted("Mirror directly in scrcpy’s native window. OBS can capture that window independently."))
        status, status_layout = self._card("Session")
        session_row = QHBoxLayout()
        self.mirror_status_badge = QLabel(self._t("Stopped"))
        self.mirror_status_badge.setObjectName("statusNeutral")
        session_row.addWidget(self.mirror_status_badge)
        session_row.addStretch()
        self.start_mirroring_button = QPushButton(self._t("Start mirroring"))
        self.start_mirroring_button.setObjectName("primary")
        self.start_mirroring_button.clicked.connect(self.start_mirroring)
        self.stop_mirroring_button = QPushButton(self._t("Stop session"))
        self.stop_mirroring_button.setObjectName("danger")
        self.stop_mirroring_button.setEnabled(False)
        self.stop_mirroring_button.clicked.connect(self.scrcpy.stop)
        session_row.addWidget(self.start_mirroring_button)
        session_row.addWidget(self.stop_mirroring_button)
        status_layout.addLayout(session_row)
        self.mirror_selected_label = self._muted("Selected device: none")
        status_layout.addWidget(self.mirror_selected_label)
        layout.addWidget(status)

        profile, profile_layout = self._card("Current mirror profile")
        self.profile_label = QLabel()
        self.profile_label.setObjectName("sectionTitle")
        profile_layout.addWidget(self.profile_label)
        profile_layout.addWidget(self._muted("Audio is enabled; decoder selection and input methods use scrcpy defaults unless explicitly changed in Advanced Settings."))
        controls = QHBoxLayout()
        self.settings_button = QPushButton(self._t("Edit profile"))
        self.settings_button.clicked.connect(self.open_settings)
        self.advanced_settings_button = QPushButton(self._t("Advanced settings"))
        self.advanced_settings_button.clicked.connect(self.open_dynamic_settings)
        controls.addWidget(self.settings_button)
        controls.addWidget(self.advanced_settings_button)
        controls.addStretch()
        profile_layout.addLayout(controls)
        layout.addWidget(profile)

        capabilities, cap_layout = self._card("scrcpy capability status")
        self.scrcpy_capability_label = self._muted("Capability discovery is starting…")
        cap_layout.addWidget(self.scrcpy_capability_label)
        layout.addWidget(capabilities)

    def _build_screenshots_page(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._muted("Capture a PNG from the selected Android device using asynchronous ADB output."))
        card, inner = self._card("Capture")
        self.screenshot_button = QPushButton(self._t("Save screenshot…"))
        self.screenshot_button.setObjectName("primary")
        self.screenshot_button.clicked.connect(self.capture_screenshot)
        self.screenshot_hint = self._muted("Select an authorized device in Devices first.")
        inner.addWidget(self.screenshot_button, 0, Qt.AlignmentFlag.AlignLeft)
        inner.addWidget(self.screenshot_hint)
        layout.addWidget(card)
        recent, recent_layout = self._card("Recent captures this session")
        self.screenshot_list_layout = recent_layout
        self.screenshot_empty_label = self._muted("Screenshots saved during this session will appear here. No files are scanned or assumed.")
        recent_layout.addWidget(self.screenshot_empty_label)
        layout.addWidget(recent)

    def _build_recordings_page(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._muted("Recording is performed by scrcpy at session launch. ScreenMirror does not capture or convert video frames."))
        card, inner = self._card("Recording destination")
        self.recording_destination_label = QLabel()
        self.recording_destination_label.setObjectName("sectionTitle")
        self.recording_destination_label.setWordWrap(True)
        inner.addWidget(self.recording_destination_label)
        inner.addWidget(self._muted("No recording library exists yet; this page reports only the destination configured for future mirror sessions."))
        edit = QPushButton(self._t("Configure recording and mirror profile"))
        edit.clicked.connect(self.open_settings)
        inner.addWidget(edit, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card)

    def _build_diagnostics_page(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._muted("Live service information and bounded application diagnostics."))
        card, inner = self._card("Environment")
        executable = self.adb.adb_path or self._t("ADB not found")
        self.host_label = self._muted(self._t("ADB executable: {path}", path=executable))
        self.adb_version_label = self._muted(self._t("ADB version: Not checked"))
        self.diagnostic_scrcpy_label = self._muted(self._t("scrcpy version: Discovering…"))
        self.diagnostic_device_label = self._muted("Selected device: none")
        for label in (self.host_label, self.adb_version_label, self.diagnostic_scrcpy_label, self.diagnostic_device_label):
            inner.addWidget(label)
        layout.addWidget(card)
        log_card, log_layout = self._card("Recent messages")
        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        self.diagnostics.setMaximumBlockCount(500)
        self.diagnostics.setMinimumHeight(250)
        log_layout.addWidget(self.diagnostics)
        layout.addWidget(log_card)

    def _build_settings_page(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._muted("Application preferences are saved using the existing ScreenMirror settings store."))
        language_card, language_layout = self._card("Language")
        language_layout.addWidget(self._muted("Choose the language used by ScreenMirror."))
        self.language_combo = QComboBox()
        for language in ("en", "km"):
            self.language_combo.addItem(LANGUAGE_NAMES[language], language)
        language_index = self.language_combo.findData(self.language)
        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)
        self.language_combo.currentIndexChanged.connect(self._change_language)
        language_layout.addWidget(self.language_combo)
        layout.addWidget(language_card)

        card, inner = self._card("Mirror defaults")
        self.settings_summary = self._muted("")
        inner.addWidget(self.settings_summary)
        edit = QPushButton(self._t("Edit mirror profile"))
        edit.setObjectName("primary")
        edit.clicked.connect(self.open_settings)
        advanced = QPushButton(self._t("Configure discovered scrcpy options"))
        advanced.clicked.connect(self.open_dynamic_settings)
        inner.addWidget(edit, 0, Qt.AlignmentFlag.AlignLeft)
        inner.addWidget(advanced, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card)

    def _build_about_page(self, layout: QVBoxLayout) -> None:
        card, inner = self._card("ScreenMirror")
        identity = QLabel(self._t("Android device management and native screen mirroring"))
        identity.setObjectName("sectionTitle")
        inner.addWidget(identity)
        inner.addWidget(self._muted("Python and PySide6 manage the desktop interface and ADB operations. scrcpy remains an independent native process for video decoding, rendering, and input."))
        inner.addWidget(self._muted("OBS Studio can capture the native scrcpy window without a second Python capture pipeline."))
        layout.addWidget(card)

    def _navigate(self, name: str) -> None:
        if name not in self._page_indices:
            return
        self.page_stack.setCurrentIndex(self._page_indices[name])
        self._current_page = name
        self.page_title.setText(self._t(name))
        for title, button in self._nav_buttons.items():
            button.setChecked(title == name)

    def _connect_services(self) -> None:
        self.adb.status_changed.connect(self._on_adb_status)
        self.adb.error_occurred.connect(self.on_adb_error)
        self.adb.version_detected.connect(self._on_adb_version)
        self.adb.version_detected.connect(self.adb.start_server)
        self.adb.devices_changed.connect(self.update_devices)
        self.adb.busy_changed.connect(self.set_busy)
        self.adb.screenshot_busy_changed.connect(self.set_screenshot_busy)
        self.adb.shutdown_finished.connect(lambda: self._on_shutdown_service_finished("adb"))
        self.scrcpy.started.connect(self.on_scrcpy_started)
        self.scrcpy.stopped.connect(self.on_scrcpy_stopped)
        self.scrcpy.error_occurred.connect(self.on_error)
        self.scrcpy.capabilities_ready.connect(self._on_capabilities_ready)
        self.scrcpy.output_received.connect(lambda output: self.log(f"scrcpy: {output}"))
        self.scrcpy.shutdown_finished.connect(lambda: self._on_shutdown_service_finished("scrcpy"))

    def _on_adb_version(self, value: str) -> None:
        self._adb_version = value.replace("\n", " | ")
        self.adb_version_label.setText(self._t("ADB version: {version}", version=self._adb_version))
        self.log(self._t("ADB version: {version}", version=self._adb_version))

    def _on_capabilities_ready(self) -> None:
        capabilities = self.scrcpy.capabilities
        if capabilities is None:
            return
        supported = {option.canonical for option in capabilities.options}
        choices = {option.canonical: option.choices for option in capabilities.options}
        options = {option.canonical: option for option in capabilities.options}
        saved_dynamic = DynamicSettings.load(supported, choices, options)
        if saved_dynamic.needs_cleanup:
            saved_dynamic.save()
        self.dynamic_settings = DynamicSettings(saved_dynamic.values)
        self.scrcpy_capability_label.setText(
            self._t(
                "scrcpy {version} ready · {count} options discovered from bundled help.",
                version=capabilities.version,
                count=len(capabilities.options),
            )
        )
        self.diagnostic_scrcpy_label.setText(
            self._t("scrcpy version: {version}", version=capabilities.version)
        )
        self.on_status(self._t("scrcpy {version} capabilities ready.", version=capabilities.version))

    def set_busy(self, busy: bool) -> None:
        self._adb_busy = busy
        for button in (self.start_button, self.stop_button, self.disconnect_button, self.refresh_button):
            button.setDisabled(busy)
        device = self._selected_device()
        self.start_mirroring_button.setEnabled(
            not busy and self.scrcpy.process is None and device is not None and device.state == "device"
        )
        self.set_screenshot_busy(self._screenshot_busy)

    def set_screenshot_busy(self, busy: bool) -> None:
        self._screenshot_busy = busy
        if hasattr(self, "screenshot_button"):
            self.screenshot_button.setDisabled(busy or self._adb_busy or not self._selected_serial())

    def on_status(self, message: str) -> None:
        self._last_feedback = ("status", message)
        rendered = self._message(message)
        self.status_label.setText(rendered)
        self.log(f"INFO: {rendered}")

    def _on_adb_status(self, message: str) -> None:
        self._last_adb_status = message
        self.on_status(message)
        self.dashboard_status.setText(self._message(message))
        normalized = message.lower()
        if "error" in normalized or "failed" in normalized:
            self.adb_badge.setText(self._t("ADB · Attention"))
            self.adb_badge.setObjectName("statusWarning")
        elif "started" in normalized or "detected" in normalized or "verified" in normalized:
            self.adb_badge.setText(self._t("ADB · Active"))
            self.adb_badge.setObjectName("statusConnected")
        elif "stopped" in normalized:
            self.adb_badge.setText(self._t("ADB · Stopped"))
            self.adb_badge.setObjectName("statusNeutral")
        self._repolish(self.adb_badge)
        status_value = (
            "Active" if "started" in normalized or "verified" in normalized or "detected" in normalized
            else "Ready" if "ready" in normalized
            else "Stopped" if "stopped" in normalized
            else "Checking…"
        )
        self.dashboard_adb_value.setText(self._t(status_value))

    def on_error(self, message: str) -> None:
        self._last_feedback = ("error", message)
        self._render_error(message)

    def on_adb_error(self, message: str) -> None:
        self._last_feedback = ("adb_error", message)
        self._render_error(message)
        self.dashboard_status.setText(f"{self._t('Error')}: {self._message(message)}")
        self.adb_badge.setText(self._t("ADB · Attention"))
        self.adb_badge.setObjectName("statusError")
        self._repolish(self.adb_badge)

    def _render_error(self, message: str) -> None:
        rendered = self._message(message)
        self.status_label.setText(f"{self._t('Error')}: {rendered}")
        self.log(f"ERROR: {rendered}")

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def log(self, message: str) -> None:
        if hasattr(self, "diagnostics"):
            self.diagnostics.appendPlainText(message)

    def adb_refresh(self) -> None:
        self.adb.refresh_devices()

    def update_devices(self, devices: list[AdbDevice]) -> None:
        retained_serial = self._selected_device_serial
        self.adb.devices = devices
        self._clear_device_cards()
        self._device_card_buttons.clear()
        self.device_empty_label.setVisible(not devices)
        for device in devices:
            card_button = QPushButton()
            card_button.setObjectName("deviceCard")
            card_button.setCheckable(True)
            card_button.setChecked(device.serial == retained_serial)
            card_button.setProperty("serial", device.serial)
            card_button.setProperty("state", device.state)
            title = device.model.replace("_", " ") if device.model else self._t("Android device")
            short_serial = device.serial if len(device.serial) < 23 else f"{device.serial[:10]}…{device.serial[-8:]}"
            transport = self._t("Wireless") if ":" in device.serial else self._t("USB / local")
            details = self._t("{serial}   ·   {transport}", serial=short_serial, transport=transport)
            if device.transport_id:
                details += f"   ·   {self._t('transport {value}', value=device.transport_id)}"
            state_text = self._t({
                "device": "Connected",
                "unauthorized": "Unauthorized",
                "offline": "Offline",
            }.get(device.state, device.state.title()))
            card_button.setText(f"{title}\n{details}\n{state_text}")
            card_button.clicked.connect(lambda _checked=False, serial=device.serial: self._select_device(serial))
            self.device_cards_layout.addWidget(card_button)
            self._device_card_buttons[device.serial] = card_button
        if retained_serial and not any(item.serial == retained_serial for item in devices):
            self._selected_device_serial = ""
        if self._selected_device_serial:
            self._select_device(self._selected_device_serial, refresh=False)
        ready_count = sum(item.state == "device" for item in devices)
        self.dashboard_device_value.setText(str(ready_count))
        self.device_count_badge.setText(
            self._t("{ready} ready · {total} found", ready=ready_count, total=len(devices))
        )
        self.device_count_badge.setObjectName("statusConnected" if ready_count else "statusNeutral")
        self._repolish(self.device_count_badge)
        self._refresh_selection_labels()

    def _clear_device_cards(self) -> None:
        while self.device_cards_layout.count() > 1:
            item = self.device_cards_layout.takeAt(1)
            widget = item.widget()
            if widget is not None and widget is not self.device_empty_label:
                widget.deleteLater()

    def _select_device(self, serial: str, refresh: bool = True) -> None:
        self._selected_device_serial = serial
        for candidate, button in self._device_card_buttons.items():
            button.setChecked(candidate == serial)
        self._refresh_selection_labels()
        if refresh:
            self.set_screenshot_busy(self._screenshot_busy)

    def _selected_device(self) -> AdbDevice | None:
        return next((device for device in self.adb.devices if device.serial == self._selected_device_serial), None)

    def _selected_serial(self) -> str:
        return self._selected_device_serial

    def _refresh_selection_labels(self) -> None:
        device = self._selected_device()
        if device is None:
            self.dashboard_selected.setText(self._t("No device selected"))
            self.dashboard_selected_detail.setText(
                self._t("Connect an Android device and select it in Devices.")
            )
            self.mirror_selected_label.setText(self._t("Selected device: none"))
            self.diagnostic_device_label.setText(self._t("Selected device: none"))
            if hasattr(self, "screenshot_hint"):
                self.screenshot_hint.setText(
                    self._t("Select an authorized device in Devices first.")
                )
            self.start_mirroring_button.setEnabled(not self._adb_busy and self.scrcpy.process is None)
            self.disconnect_button.setEnabled(not self._adb_busy)
        else:
            model = device.model.replace("_", " ") if device.model else self._t("Android device")
            readiness = (
                self._t("Authorized and ready")
                if device.state == "device"
                else self._t("Not ready · {state}", state=self._t({
                    "unauthorized": "Unauthorized",
                    "offline": "Offline",
                }.get(device.state, device.state.title())))
            )
            self.dashboard_selected.setText(model)
            self.dashboard_selected_detail.setText(f"{device.serial}\n{readiness}")
            self.mirror_selected_label.setText(
                self._t("Selected device: {model} · {serial}", model=model, serial=device.serial)
            )
            state = self._t({
                "device": "Connected",
                "unauthorized": "Unauthorized",
                "offline": "Offline",
            }.get(device.state, device.state.title()))
            self.diagnostic_device_label.setText(
                self._t(
                    "Selected device: {model} · {serial} · {state}",
                    model=model,
                    serial=device.serial,
                    state=state,
                )
            )
            self.start_mirroring_button.setEnabled(device.state == "device" and not self._adb_busy and self.scrcpy.process is None)
            self.disconnect_button.setEnabled(not self._adb_busy)
            if hasattr(self, "screenshot_hint"):
                self.screenshot_hint.setText(
                    self._t("Selected: {model} · {readiness}", model=model, readiness=readiness)
                )
        self.screenshot_button.setEnabled(device is not None and device.state == "device" and not self._adb_busy and not self._screenshot_busy)

    def disconnect_selected(self) -> None:
        device = self._selected_device()
        if device is None:
            self.on_error(self._t("Select a device before disconnecting."))
            return
        self.adb.disconnect_device(device.serial)

    def pair_wireless(self) -> None:
        pairing_code = self.code_edit.text()
        self.code_edit.clear()
        self.adb.pair_wireless(self.target_edit.text(), pairing_code)

    def capture_screenshot(self) -> None:
        device = self._selected_device()
        if device is None or device.state != "device":
            self.on_error(self._t("Select an authorized, ready device before taking a screenshot."))
            return
        destination, _ = QFileDialog.getSaveFileName(
            self,
            self._t("Save Android screenshot"),
            "screenmirror-screenshot.png",
            self._t("PNG image (*.png)"),
        )
        if not destination:
            return
        self.adb.screenshot(device.serial, Path(destination), self._screenshot_finished)

    def _screenshot_finished(self, success: bool, message: str) -> None:
        if success:
            self._recent_screenshots.insert(0, message)
            del self._recent_screenshots[12:]
            self._refresh_screenshot_list()
            self.on_status(self._t("Screenshot saved: {path}", path=message))
        else:
            self.on_error(message)

    def _refresh_screenshot_list(self) -> None:
        while self.screenshot_list_layout.count() > 1:
            item = self.screenshot_list_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        self.screenshot_empty_label.setVisible(not self._recent_screenshots)
        for path in self._recent_screenshots:
            row = QHBoxLayout()
            label = QLabel(path)
            label.setWordWrap(True)
            row.addWidget(label, 1)
            open_button = QPushButton(self._t("Open file"))
            open_button.clicked.connect(lambda _checked=False, filename=path: self._open_file(filename))
            row.addWidget(open_button)
            self.screenshot_list_layout.addLayout(row)

    @staticmethod
    def _open_file(path: str) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def start_mirroring(self) -> None:
        device = self._selected_device()
        if device is None:
            self.on_error(self._t("Select a device before starting mirroring."))
            return
        if device.state != "device":
            self.on_error(self._t(
                "Device is not authorized or ready: {state}",
                state=self._t({
                    "unauthorized": "Unauthorized",
                    "offline": "Offline",
                }.get(device.state, device.state.title())),
            ))
            return
        self.scrcpy.start(device.serial, self.settings, dynamic_values=self.dynamic_settings.values)
        self.start_mirroring_button.setEnabled(False)
        self.stop_mirroring_button.setEnabled(True)

    def open_settings(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("Mirror profile"))
        dialog.resize(640 if self.language == "km" else 520, 600 if self.language == "km" else 560)
        form = QFormLayout(dialog)
        size = QSpinBox(dialog)
        size.setRange(240, 8192)
        size.setSuffix(" px")
        size.setValue(self.settings.max_size)
        fps = QSpinBox(dialog)
        fps.setRange(1, 240)
        fps.setSuffix(" FPS")
        fps.setValue(self.settings.max_fps)
        bitrate = QComboBox(dialog)
        bitrate.setEditable(True)
        bitrate.addItems(("2M", "4M", "8M", "12M", "16M", "24M"))
        bitrate.setCurrentText(self.settings.video_bit_rate)
        codec = QComboBox(dialog)
        codecs = self.scrcpy.capabilities.video_codecs if self.scrcpy.capabilities else ("h264",)
        codec.addItems(codecs)
        codec.setCurrentText(self.settings.video_codec)
        audio = QCheckBox(self._t("Forward device audio when supported"), dialog)
        audio.setChecked(self.settings.audio_enabled)
        fullscreen = QCheckBox(self._t("Start fullscreen"), dialog)
        fullscreen.setChecked(self.settings.fullscreen)
        awake = QCheckBox(self._t("Keep device awake"), dialog)
        awake.setChecked(self.settings.stay_awake)
        screen_off = QCheckBox(self._t("Turn device screen off while mirroring"), dialog)
        screen_off.setChecked(self.settings.turn_screen_off)
        record = QLineEdit(self.settings.recording_path, dialog)
        record.setPlaceholderText(self._t("Optional .mp4 or .mkv output path"))
        browse = QPushButton(self._t("Browse…"), dialog)
        browse.clicked.connect(lambda: self.choose_recording_path(record))
        record_row = QHBoxLayout()
        record_row.addWidget(record, 1)
        record_row.addWidget(browse)
        form.addRow(self._t("Maximum resolution"), size)
        form.addRow(self._t("Maximum frame rate"), fps)
        form.addRow(self._t("Video bitrate"), bitrate)
        form.addRow(self._t("Video codec"), codec)
        form.addRow(audio)
        form.addRow(fullscreen)
        form.addRow(awake)
        form.addRow(screen_off)
        form.addRow(self._t("Record this session"), record_row)
        form.addRow(self._muted("Settings apply when the next scrcpy session starts. Recording is handled natively by scrcpy."))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self._t("Save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self._t("Cancel"))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated = AppSettings(size.value(), fps.value(), bitrate.currentText().strip(), codec.currentText(), audio.isChecked(), fullscreen.isChecked(), awake.isChecked(), screen_off.isChecked(), record.text().strip())
        try:
            updated.validate()
        except ValueError as error:
            self.on_error(str(error))
            return
        if self.scrcpy.capabilities and updated.video_codec not in self.scrcpy.capabilities.video_codecs:
            self.on_error(self._t("The bundled scrcpy does not support {codec}.", codec=updated.video_codec))
            return
        self.settings = updated
        self.settings.save()
        self._refresh_profile_labels()
        self.on_status(self._t("Mirror settings saved. They apply to the next session."))

    def choose_recording_path(self, edit: QLineEdit) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self,
            self._t("Record mirrored screen"),
            edit.text() or "screenmirror-recording.mp4",
            self._t("MP4 video (*.mp4);;MKV video (*.mkv)"),
        )
        if destination:
            edit.setText(destination)

    def _refresh_profile_labels(self) -> None:
        profile = self._t(
            "{size}p max  ·  {fps} FPS  ·  {bitrate}  ·  {codec}  ·  Audio {audio}",
            size=self.settings.max_size,
            fps=self.settings.max_fps,
            bitrate=self.settings.video_bit_rate,
            codec=self.settings.video_codec.upper(),
            audio=self._t("on" if self.settings.audio_enabled else "off"),
        )
        self.profile_label.setText(profile)
        self.dashboard_profile.setText(profile)
        self.settings_summary.setText(
            profile
            + "\n"
            + self._t(
                "Stay awake: {state} · Fullscreen: {fullscreen}",
                state=self._t("on" if self.settings.stay_awake else "off"),
                fullscreen=self._t("on" if self.settings.fullscreen else "off"),
            )
        )
        self.recording_destination_label.setText(
            self.settings.recording_path
            or self._t("No recording destination configured")
        )

    def open_dynamic_settings(self) -> None:
        """Build advanced controls only from options discovered in scrcpy help."""
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("Advanced scrcpy settings"))
        dialog.resize(940 if self.language == "km" else 850, 700)
        outer = QVBoxLayout(dialog)
        capabilities = self.scrcpy.capabilities
        if capabilities is None:
            outer.addWidget(QLabel(self._message(
                self.scrcpy.initialization_error or self._t("scrcpy capabilities are still loading.")
            )))
            dialog.exec()
            return
        outer.addWidget(QLabel(self._t(
            "scrcpy {version} · {count} supported options",
            version=capabilities.version,
            count=len(capabilities.options),
        )))
        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        controls: dict[str, QWidget] = {}
        forms: dict[str, QFormLayout] = {}
        for option in capabilities.options:
            if (
                option.canonical in {"--help", "--version"}
                or not is_display_only_option_allowed(option.canonical)
            ):
                continue
            if option.category not in forms:
                from PySide6.QtWidgets import QGroupBox
                group = QGroupBox(
                    translate_scrcpy_category(option.category, self.language), content
                )
                forms[option.category] = QFormLayout(group)
                content_layout.addWidget(group)
            widget = self._control_for_option(option, dialog)
            controls[option.canonical] = widget
            if option.canonical in self.dynamic_settings.values:
                self._set_control_value(widget, self.dynamic_settings.values[option.canonical])
            forms[option.category].addRow(self._option_label(option), widget)
        content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        outer.addWidget(QLabel(self._t("Exact command preview")))
        preview = QPlainTextEdit(dialog)
        preview.setReadOnly(True)
        preview.setMaximumHeight(70)
        outer.addWidget(preview)
        buttons = QDialogButtonBox(dialog)
        save = buttons.addButton(self._t("Save"), QDialogButtonBox.ButtonRole.AcceptRole)
        reset = buttons.addButton(
            self._t("Clear advanced overrides"), QDialogButtonBox.ButtonRole.ResetRole
        )
        copy_button = buttons.addButton(
            self._t("Copy command"), QDialogButtonBox.ButtonRole.ActionRole
        )
        cancel = buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        cancel.setText(self._t("Cancel"))
        cancel.clicked.connect(dialog.reject)
        outer.addWidget(buttons)

        def values() -> dict[str, object]:
            result: dict[str, object] = {}
            for option in capabilities.options:
                widget = controls.get(option.canonical)
                if widget is None:
                    continue
                value = self._control_value(widget)
                if value not in (None, "", False):
                    result[option.canonical] = value
            return result

        def update_preview() -> None:
            try:
                preview.setPlainText(capabilities.builder().preview(values(), self._selected_serial()))
            except (RuntimeError, ValueError) as error:
                preview.setPlainText(self._message(f"Invalid settings: {error}"))

        for widget in controls.values():
            if isinstance(widget, QCheckBox):
                widget.toggled.connect(update_preview)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(update_preview)
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(update_preview)
        reset.clicked.connect(lambda: [self._reset_control(widget) for widget in controls.values()])
        reset.clicked.connect(update_preview)
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(preview.toPlainText()))

        def accept_valid_settings() -> None:
            try:
                capabilities.builder().build(values(), self._selected_serial())
            except (RuntimeError, ValueError) as error:
                preview.setPlainText(self._message(f"Invalid settings: {error}"))
                return
            dialog.accept()

        save.clicked.connect(accept_valid_settings)
        update_preview()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.dynamic_settings.values = values()
            self.dynamic_settings.save()
            self.on_status(self._t(
                "Saved {count} advanced settings for scrcpy {version}.",
                count=len(self.dynamic_settings.values),
                version=capabilities.version,
            ))

    def _control_for_option(self, option: ScrcpyOption, parent: QWidget) -> QWidget:
        if option.boolean_flag:
            return QCheckBox(
                translate_scrcpy_description(
                    option.canonical, option.description.split(".")[0], self.language
                ),
                parent,
            )
        if option.choices:
            combo = QComboBox(parent)
            combo.setEditable(True)
            combo.addItems(option.choices)
            combo.setCurrentIndex(-1)
            combo.clearEditText()
            return combo
        edit = QLineEdit(parent)
        edit.setPlaceholderText(
            option.argument_name or self._t("value; validate against scrcpy help")
        )
        return edit

    def _control_value(self, widget: QWidget) -> object:
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QComboBox):
            return widget.currentText().strip()
        return widget.text().strip() if isinstance(widget, QLineEdit) else None

    @staticmethod
    def _set_control_value(widget: QWidget, value: object) -> None:
        if isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))

    def _reset_control(self, widget: QWidget) -> None:
        if isinstance(widget, QComboBox):
            widget.setCurrentIndex(-1)
            widget.clearEditText()
        else:
            self._set_control_value(widget, False if isinstance(widget, QCheckBox) else "")

    @staticmethod
    def _option_label(option: ScrcpyOption) -> str:
        alias = f" ({option.short_option})" if option.short_option else ""
        return f"{option.canonical}{alias}:"

    def on_scrcpy_started(self) -> None:
        self.on_status(self._t("scrcpy mirroring started."))
        self._refresh_mirroring_state()

    def on_scrcpy_stopped(self) -> None:
        self.on_status(self._t("scrcpy mirroring stopped."))
        self._refresh_mirroring_state()

    def _refresh_mirroring_state(self) -> None:
        active = self.scrcpy.process is not None
        self.mirror_status_badge.setText(self._t("Mirroring" if active else "Stopped"))
        self.mirror_status_badge.setObjectName("statusConnected" if active else "statusNeutral")
        self._repolish(self.mirror_status_badge)
        self.dashboard_mirror_value.setText(self._t("Active" if active else "Stopped"))
        device = self._selected_device()
        self.start_mirroring_button.setEnabled(
            not active
            and not self._adb_busy
            and device is not None
            and device.state == "device"
        )
        self.stop_mirroring_button.setEnabled(active)

    def _on_shutdown_service_finished(self, service: str) -> None:
        if not self._close_requested:
            return
        self._shutdown_services_pending.discard(service)
        if not self._shutdown_services_pending:
            self._shutdown_complete = True
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._shutdown_complete:
            event.accept()
            return
        event.ignore()
        if self._close_requested:
            return
        self._close_requested = True
        self._shutdown_services_pending = {"adb", "scrcpy"}
        self.adb.shutdown()
        self.scrcpy.shutdown()
