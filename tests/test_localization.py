import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QRawFont
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QLabel, QApplication

from screenmirror.i18n import (
    font_family_for_language,
    translate,
    translate_message,
    translate_scrcpy_category,
    translate_scrcpy_description,
)
from screenmirror.settings import UiSettings
from screenmirror.ui.main_window import MainWindow


class LocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.project_root = Path(__file__).parents[1]

    def setUp(self):
        self.settings_directory = tempfile.TemporaryDirectory()
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            self.settings_directory.name,
        )
        self.settings_factory = lambda organization, application: QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            organization,
            application,
        )
        self.settings_patch = patch(
            "screenmirror.settings.QSettings", side_effect=self.settings_factory
        )
        self.settings_patch.start()
        self.settings_factory("ScreenMirror", "ScreenMirror").clear()
        self.adb_patch = patch(
            "screenmirror.ui.main_window.AdbManager.check_version"
        )
        self.scrcpy_patch = patch(
            "screenmirror.ui.main_window.ScrcpySession.start_discovery"
        )
        self.adb_patch.start()
        self.scrcpy_patch.start()
        self.window = MainWindow(self.project_root)

    def tearDown(self):
        self.window._shutdown_complete = True
        self.window.close()
        self.app.processEvents()
        self.scrcpy_patch.stop()
        self.adb_patch.stop()
        self.settings_patch.stop()
        self.settings_directory.cleanup()

    def test_ui_switches_between_khmer_and_english_and_persists(self):
        self.window._navigate("Settings")
        previous_combo = self.window.language_combo
        previous_combo.setCurrentIndex(1)
        self.app.processEvents()

        self.assertEqual(self.window.language, "km")
        self.assertEqual(UiSettings.load().language, "km")
        self.assertEqual(self.window.page_title.text(), "ការកំណត់")
        self.assertEqual(self.window.code_edit.placeholderText(), "លេខកូដផ្គូផ្គង")
        self.assertEqual(self.window._nav_buttons["Devices"].text(), "▣    ឧបករណ៍")
        self.assertIn(
            "កែទម្រង់ឆ្លុះអេក្រង់",
            {button.text() for button in self.window.findChildren(type(self.window.settings_button))},
        )
        self.assertEqual(
            self.window.recording_destination_label.text(),
            "មិនទាន់កំណត់ទីតាំងរក្សាទុកការថត",
        )
        self.assertNotEqual(self.window.language_combo, previous_combo)

        restored_window = MainWindow(self.project_root)
        try:
            self.assertEqual(restored_window.language, "km")
        finally:
            restored_window._shutdown_complete = True
            restored_window.close()

        self.window.language_combo.setCurrentIndex(0)
        self.app.processEvents()

        self.assertEqual(self.window.language, "en")
        self.assertEqual(UiSettings.load().language, "en")
        self.assertEqual(self.window.page_title.text(), "Settings")
        self.assertEqual(self.window.code_edit.placeholderText(), "Pairing code")

    def test_khmer_font_supports_unicode_and_long_labels_wrap(self):
        family = font_family_for_language(
            "km", {"Segoe UI", "Khmer UI", "Noto Sans Khmer"}
        )
        self.assertEqual(family, "Khmer UI")
        raw_font = QRawFont.fromFont(QFont(family, 11))
        self.assertTrue(raw_font.isValid())
        self.assertTrue(raw_font.supportsCharacter(ord("ខ")))
        self.assertTrue(raw_font.supportsCharacter(ord("្")))

        self.window.language_combo.setCurrentIndex(1)
        self.window._navigate("Devices")
        self.window.resize(1280, 800)
        self.window.show()
        self.app.processEvents()
        self.assertTrue(self.window.device_empty_label.wordWrap())
        self.assertGreater(self.window.device_empty_label.width(), 0)
        self.assertFalse(self.window.grab().isNull())

    def test_profile_dialog_controls_are_localized(self):
        self.window.language_combo.setCurrentIndex(1)
        dialogs = []

        def reject_dialog(dialog):
            dialogs.append(dialog)
            return QDialog.DialogCode.Rejected

        with patch("screenmirror.ui.main_window.QDialog.exec", reject_dialog):
            self.window.open_settings()

        dialog = dialogs[0]
        self.assertEqual(dialog.windowTitle(), "ទម្រង់ឆ្លុះអេក្រង់")
        self.assertIn(
            "កម្រិតបង្ហាញអតិបរមា",
            {label.text() for label in dialog.findChildren(QLabel)},
        )
        self.assertIn(
            "បញ្ជូនសំឡេងពីឧបករណ៍ បើមានការគាំទ្រ",
            {check.text() for check in dialog.findChildren(QCheckBox)},
        )
        buttons = dialog.findChild(QDialogButtonBox)
        self.assertEqual(
            buttons.button(QDialogButtonBox.StandardButton.Save).text(),
            "រក្សាទុក",
        )
        self.assertEqual(
            buttons.button(QDialogButtonBox.StandardButton.Cancel).text(),
            "បោះបង់",
        )

    def test_dynamic_messages_and_scrcpy_labels_are_localized(self):
        self.assertEqual(translate("Dashboard", "en"), "Dashboard")
        self.assertEqual(translate("Dashboard", "km"), "ផ្ទាំងគ្រប់គ្រង")
        self.assertIn(
            "pair",
            translate_message("ADB command 'pair' timed out after 30 seconds.", "km"),
        )
        self.assertIn(
            "30",
            translate_message("ADB command 'pair' timed out after 30 seconds.", "km"),
        )
        self.assertEqual(translate_scrcpy_category("Audio", "km"), "សំឡេង")
        self.assertEqual(
            translate_scrcpy_description("--fullscreen", "Start in fullscreen", "km"),
            "ចាប់ផ្តើមជារបៀបពេញអេក្រង់",
        )
        self.assertEqual(
            translate_message(
                "The bundled scrcpy does not support h265.", "km"
            ),
            "scrcpy ដែលបានភ្ជាប់មកជាមួយមិនគាំទ្រ h265 ទេ។",
        )
        self.assertEqual(
            translate_message(
                "Could not start scrcpy version discovery: executable missing",
                "km",
            ),
            "មិនអាចចាប់ផ្តើមស្វែងរកកំណែ scrcpy បានទេ៖ executable missing",
        )


if __name__ == "__main__":
    unittest.main()
