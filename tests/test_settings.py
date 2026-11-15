import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QSettings

from screenmirror.scrcpy_help import ScrcpyOption
from screenmirror.settings import AppSettings, DynamicSettings, UiSettings


class SettingsPersistenceTests(unittest.TestCase):
    def _use_temporary_settings(self, directory):
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory)
        factory = lambda organization, application: QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            organization,
            application,
        )
        settings_patch = patch("screenmirror.settings.QSettings", side_effect=factory)
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        store = factory("ScreenMirror", "ScreenMirror")
        store.clear()
        return store

    def test_fresh_settings_use_lightweight_default_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            self._use_temporary_settings(directory)
            settings = AppSettings.load()
            self.assertEqual(settings.max_size, 720)
            self.assertEqual(settings.max_fps, 30)
            self.assertEqual(settings.video_bit_rate, "4M")
            self.assertEqual(settings.video_codec, "h264")
            self.assertTrue(settings.audio_enabled)
            self.assertTrue(settings.stay_awake)

    def test_existing_standard_preferences_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self._use_temporary_settings(directory)
            store.setValue("mirror/max_size", 1080)
            store.setValue("mirror/max_fps", 45)
            store.setValue("mirror/video_bit_rate", "8M")
            store.setValue("mirror/audio_enabled", False)
            store.sync()

            settings = AppSettings.load()
            self.assertEqual(settings.max_size, 1080)
            self.assertEqual(settings.max_fps, 45)
            self.assertEqual(settings.video_bit_rate, "8M")
            self.assertFalse(settings.audio_enabled)

    def test_app_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            self._use_temporary_settings(directory)

            expected = AppSettings(max_size=720, max_fps=30, video_bit_rate="4M", fullscreen=True)
            expected.save()
            actual = AppSettings.load()

            self.assertEqual(actual.max_size, 720)
            self.assertEqual(actual.max_fps, 30)
            self.assertEqual(actual.video_bit_rate, "4M")
            self.assertTrue(actual.fullscreen)

    def test_ui_language_defaults_to_english_and_persists_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self._use_temporary_settings(directory)
            settings = UiSettings.load()
            self.assertEqual(settings.language, "en")

            settings.language = "km"
            settings.save()

            self.assertEqual(UiSettings.load().language, "km")
            self.assertIsNone(store.value("mirror/language"))

    def test_unsupported_persisted_ui_language_falls_back_to_english(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self._use_temporary_settings(directory)
            store.setValue("ui/language", "fr")
            store.sync()

            self.assertEqual(UiSettings.load().language, "en")

    def test_ui_settings_reject_unsupported_language_on_save(self):
        with self.assertRaisesRegex(ValueError, "Unsupported interface language"):
            UiSettings("fr").save()

    def test_dynamic_settings_persist_only_explicit_values(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self._use_temporary_settings(directory)
            store.beginGroup("dynamic")
            store.setValue("--max-fps", "30")
            store.setValue("--camera-facing", "front")
            store.endGroup()

            settings = DynamicSettings.load({"--max-fps", "--camera-facing"})
            settings.save()
            settings.values.clear()
            settings.save()
            loaded = DynamicSettings.load({"--max-fps", "--camera-facing", "--video-bit-rate"})

            self.assertEqual(loaded.values, {})
            self.assertIsNone(store.value("dynamic/--max-fps"))
            self.assertIsNone(store.value("dynamic/--camera-facing"))

    def test_incompatible_dynamic_options_are_removed_but_display_options_remain(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self._use_temporary_settings(directory)
            store.beginGroup("dynamic")
            store.setValue("--camera-size", "1280x720")
            store.setValue("--video-source", "camera")
            store.setValue("--new-display", "1920x1080")
            store.setValue("--display-id", "2")
            store.endGroup()
            options = {
                "--display-id": ScrcpyOption(
                    name="display-id", long_option="--display-id", argument_name="id", accepts_value=True
                )
            }

            settings = DynamicSettings.load(
                {"--camera-size", "--video-source", "--new-display", "--display-id"},
                options=options,
            )
            self.assertEqual(settings.values, {"--display-id": "2"})
            self.assertTrue(settings.needs_cleanup)
            settings.save()

            self.assertIsNone(store.value("dynamic/--camera-size"))
            self.assertIsNone(store.value("dynamic/--video-source"))
            self.assertIsNone(store.value("dynamic/--new-display"))
            self.assertEqual(store.value("dynamic/--display-id"), "2")

    def test_saving_dynamic_settings_preserves_unrecognized_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self._use_temporary_settings(directory)
            store.beginGroup("dynamic")
            store.setValue("--future-option", "keep-me")
            store.setValue("--max-fps", "60")
            store.endGroup()

            loaded = DynamicSettings.load({"--max-fps"})
            loaded.values["--max-fps"] = "30"
            loaded.save()

            self.assertEqual(store.value("dynamic/--future-option"), "keep-me")
            self.assertEqual(store.value("dynamic/--max-fps"), "30")

    def test_invalid_persisted_port_is_dropped_and_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self._use_temporary_settings(directory)
            store.setValue("dynamic/--port", "true")
            store.setValue("dynamic/--audio-codec", "opus")
            store.setValue("dynamic/--future-option", "preserve")
            store.sync()
            supported = {"--port", "--audio-codec"}
            options = {
                "--port": ScrcpyOption(
                    name="port", long_option="--port", argument_name="port[:port]", accepts_value=True
                ),
                "--audio-codec": ScrcpyOption(
                    name="audio-codec", long_option="--audio-codec", argument_name="name",
                    accepts_value=True, choices=("opus", "aac", "raw")
                ),
            }

            settings = DynamicSettings.load(supported, options=options)
            self.assertEqual(settings.values, {"--audio-codec": "opus"})
            settings.save()

            self.assertIsNone(store.value("dynamic/--port"))
            self.assertEqual(store.value("dynamic/--audio-codec"), "opus")
            self.assertEqual(store.value("dynamic/--future-option"), "preserve")


if __name__ == "__main__":
    unittest.main()
