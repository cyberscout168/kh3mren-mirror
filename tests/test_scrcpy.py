import unittest
import tempfile
import time
import subprocess
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QWidget

from screenmirror.scrcpy import ScrcpyCapabilityManager, ScrcpySession
from screenmirror.scrcpy import ScrcpyCapabilities
from screenmirror.scrcpy_help import ScrcpyHelpParser, ScrcpyOption
from screenmirror.settings import AppSettings
from screenmirror.ui.main_window import MainWindow


class FakeSignal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in list(self._slots):
            slot(*args)

    def disconnect(self):
        self._slots.clear()


class FakeProcess:
    class ProcessChannelMode:
        SeparateChannels = object()

    class ProcessError:
        FailedToStart = 1

    class ProcessState:
        NotRunning = 0
        Running = 2

    instances = []

    def __init__(self, _parent=None):
        self.readyReadStandardOutput = FakeSignal()
        self.readyReadStandardError = FakeSignal()
        self.errorOccurred = FakeSignal()
        self.finished = FakeSignal()
        self.started = FakeSignal()
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.process_state = self.ProcessState.NotRunning
        self.terminate_count = 0
        self.wait_count = 0
        self.killed = False
        self.deleted = False
        self.program = ""
        self.arguments = []
        self.__class__.instances.append(self)

    def setProgram(self, value):
        self.program = value

    def setArguments(self, value):
        self.arguments = value

    def setWorkingDirectory(self, _value):
        pass

    def setProcessChannelMode(self, _value):
        pass

    def start(self):
        self.process_state = self.ProcessState.Running

    def state(self):
        return self.process_state

    def errorString(self):
        return "fake process error"

    def readAllStandardOutput(self):
        value = bytes(self.stdout)
        self.stdout.clear()
        return value

    def readAllStandardError(self):
        value = bytes(self.stderr)
        self.stderr.clear()
        return value

    def terminate(self):
        self.terminate_count += 1

    def kill(self):
        self.killed = True

    def waitForFinished(self, _timeout):
        self.wait_count += 1
        return True

    def deleteLater(self):
        self.deleted = True

    def blockSignals(self, _blocked):
        pass


class ScrcpyCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capabilities = object.__new__(ScrcpyCapabilities)
        self.capabilities.executable = Path("scrcpy.exe")
        self.capabilities.help_text = (
            "--serial --max-size --max-fps --video-bit-rate --video-codec "
            "--no-audio --fullscreen --stay-awake --turn-screen-off "
            "--record=file --record-format --render-fit=mode "
            "--camera-facing=mode --camera-size=size --video-source=source "
            "--new-display --no-vd-destroy-content --display-id=id"
            "\nSelect a video codec (h264, h265)"
        )
        self.capabilities.video_codecs = ("h264", "h265")
        self.capabilities.record_formats = ("mp4", "mkv")

    def test_command_is_argument_vector_and_keeps_serial_as_one_value(self) -> None:
        args = self.capabilities.build_command("device with spaces", AppSettings())
        self.assertIn("--serial=device with spaces", args)
        self.assertIn("--max-size=720", args)
        self.assertIn("--max-fps=30", args)
        self.assertIn("--video-bit-rate=4M", args)
        self.assertIn("--video-codec=h264", args)
        self.assertIn("--stay-awake", args)
        self.assertNotIn("--no-audio", args)
        self.assertNotIn("--keyboard=disabled", args)
        self.assertNotIn("--mouse=disabled", args)
        self.assertFalse(any(
            "camera" in flag or flag.startswith(("--new-display", "--vd-", "--no-vd-"))
            for flag in args
        ))
        self.assertNotIn("--video-source=display", args)
        self.assertNotIn("--display-id=", args)

    def test_advanced_override_is_added_and_empty_values_do_not_emit_flags(self) -> None:
        args = self.capabilities.build_command(
            "ABC123",
            AppSettings(),
            {
                "--render-fit": "stretched",
                "--camera-facing": "front",
                "--camera-size": "1280x720",
                "--video-source": "camera",
                "--new-display": "1920x1080",
                "--no-vd-destroy-content": True,
            },
        )
        self.assertIn("--render-fit=stretched", args)
        self.assertFalse(any(
            "camera" in flag or flag.startswith(("--video-source", "--new-display", "--vd-", "--no-vd-"))
            for flag in args
        ))

        cleared_args = self.capabilities.build_command("ABC123", AppSettings(), {})
        self.assertNotIn("--render-fit=stretched", cleared_args)
        self.assertFalse(any(
            "camera" in flag or flag.startswith(("--video-source", "--new-display", "--vd-", "--no-vd-"))
            for flag in cleared_args
        ))

    def test_explicit_physical_display_selection_remains_supported(self) -> None:
        args = self.capabilities.build_command("ABC123", AppSettings(), {"--display-id": "2"})
        self.assertIn("--display-id=2", args)

    def test_empty_advanced_dropdown_contributes_no_option(self) -> None:
        app = QApplication.instance() or QApplication([])
        parent = QWidget()
        option = ScrcpyOption(
            name="render-fit",
            long_option="--render-fit",
            argument_name="mode",
            accepts_value=True,
            choices=("letterbox", "stretched", "unscaled"),
        )
        combo = MainWindow._control_for_option(None, option, parent)
        self.assertIsInstance(combo, QComboBox)
        self.assertEqual(MainWindow._control_value(None, combo), "")
        args = self.capabilities.build_command(
            "ABC123", AppSettings(), {"--render-fit": MainWindow._control_value(None, combo)}
        )
        self.assertFalse(any(arg.startswith("--render-fit") for arg in args))
        parent.deleteLater()
        app.processEvents()

    def test_bundled_scrcpy_501_accepts_default_profile_options(self):
        executable = Path(__file__).parents[1] / "third_party" / "scrcpy" / "scrcpy-win64-v5.0.1" / "scrcpy.exe"
        if not executable.is_file():
            self.skipTest("bundled Windows scrcpy executable is unavailable")
        version = subprocess.run([str(executable), "--version"], capture_output=True, text=True, timeout=10)
        help_result = subprocess.run([str(executable), "--help"], capture_output=True, text=True, timeout=10)
        self.assertEqual(version.returncode, 0)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("5.0.1", version.stdout + version.stderr)

        from screenmirror.scrcpy_help import ScrcpyHelpParser
        from screenmirror.dynamic_settings import ScrcpyCommandBuilder

        options = ScrcpyHelpParser().parse(help_result.stdout + help_result.stderr, "5.0.1")
        hardware_decoder = next(option for option in options if option.canonical == "--hwdec")
        audio_codec = next(option for option in options if option.canonical == "--audio-codec")
        self.assertIn("auto", hardware_decoder.choices)
        self.assertIn('Default is "auto"', hardware_decoder.description)
        self.assertIn("opus, aac, flac or raw", audio_codec.description)
        self.assertIn("Default is opus", audio_codec.description)
        builder = ScrcpyCommandBuilder(executable, options)
        args = builder.build(
            {
                "--max-size": 720,
                "--max-fps": 30,
                "--video-bit-rate": "4M",
                "--video-codec": "h264",
                "--stay-awake": True,
            },
            "SERIAL WITH SPACE",
        )
        self.assertEqual(args[1], "--serial=SERIAL WITH SPACE")
        self.assertIn("--max-size=720", args)
        self.assertIn("--max-fps=30", args)
        self.assertIn("--video-bit-rate=4M", args)
        self.assertIn("--video-codec=h264", args)
        self.assertIn("--stay-awake", args)
        self.assertNotIn("--video-source=display", args)
        self.assertFalse(any(
            "camera" in flag or flag.startswith(("--new-display", "--vd-", "--no-vd-"))
            for flag in args
        ))
        self.assertNotIn("--no-audio", args)
        self.assertNotIn("--keyboard=disabled", args)
        self.assertNotIn("--mouse=disabled", args)

    def test_recording_path_is_passed_as_one_argument(self) -> None:
        settings = AppSettings(recording_path="C:/My Videos/session capture.mp4")
        args = self.capabilities.build_command("ABC123", settings)
        self.assertIn("--record=C:/My Videos/session capture.mp4", args)

    def test_rejects_codec_missing_from_detected_scrcpy_help(self) -> None:
        with self.assertRaisesRegex(ValueError, "not supported"):
            self.capabilities.build_command("ABC123", AppSettings(video_codec="av1"))

    def test_rejects_empty_serial(self) -> None:
        with self.assertRaisesRegex(ValueError, "serial is required"):
            self.capabilities.build_command(" ", AppSettings())

    def test_rejects_invalid_settings(self) -> None:
        with self.assertRaisesRegex(ValueError, "Maximum FPS"):
            self.capabilities.build_command("ABC123", AppSettings(max_fps=0))


class ScrcpyLifecycleTests(unittest.TestCase):
    def _use_fake_process(self):
        FakeProcess.instances.clear()
        process_patch = patch("screenmirror.scrcpy.QProcess", FakeProcess)
        process_patch.start()
        self.addCleanup(process_patch.stop)

    def test_capability_cache_changes_when_executable_changes(self):
        help_text = "  --serial=serial\n      Select device.\n"
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "scrcpy.exe"
            executable.write_bytes(b"version-one")
            manager = ScrcpyCapabilityManager(executable, Path(directory) / "cache")
            self.assertTrue(manager.apply_outputs("scrcpy 5.0.1", help_text))
            first_cache = list((Path(directory) / "cache").glob("capabilities-*.json"))

            executable.write_bytes(b"version-two-with-a-different-size")
            self.assertTrue(manager.apply_outputs("scrcpy 5.0.1", help_text))
            second_cache = list((Path(directory) / "cache").glob("capabilities-*.json"))

            self.assertEqual(len(first_cache), 1)
            self.assertEqual(len(second_cache), 2)

    def test_capability_cache_is_invalidated_when_help_parser_changes(self):
        help_text = "  --serial=serial\n      Select device.\n"
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "scrcpy.exe"
            executable.write_bytes(b"same executable")
            cache_dir = Path(directory) / "cache"
            manager = ScrcpyCapabilityManager(executable, cache_dir)
            self.assertTrue(manager.apply_outputs("scrcpy 5.0.1", help_text))
            with patch.object(ScrcpyHelpParser, "CACHE_VERSION", ScrcpyHelpParser.CACHE_VERSION + 1):
                self.assertTrue(manager.apply_outputs("scrcpy 5.0.1", help_text))
            self.assertEqual(len(list(cache_dir.glob("capabilities-*.json"))), 2)

    def test_discovery_is_deferred_until_started_and_completes_asynchronously(self):
        executable = Path(__file__).parents[1] / "third_party" / "scrcpy" / "scrcpy-win64-v5.0.1" / "scrcpy.exe"
        if not executable.is_file():
            self.skipTest("bundled scrcpy executable is unavailable")
        app = QApplication.instance() or QApplication([])
        session = ScrcpySession(executable)
        self.assertIsNone(session.capabilities)
        session.start_discovery()
        deadline = time.monotonic() + 5
        while session.capabilities is None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        try:
            self.assertIsNotNone(session.capabilities)
            self.assertGreater(len(session.capabilities.options), 0)
        finally:
            session.shutdown()

    def test_scrcpy_failed_to_start_cleans_up_and_allows_restart(self):
        self._use_fake_process()
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "scrcpy.exe"
            executable.write_bytes(b"test")
            session = ScrcpySession(executable)
            session.capabilities = unittest.mock.Mock()
            session.capabilities.build_command.return_value = [str(executable), "--serial=ABC"]
            errors = []
            stopped = []
            session.error_occurred.connect(errors.append)
            session.stopped.connect(lambda: stopped.append(True))

            session.start("ABC")
            first = FakeProcess.instances[-1]
            first.errorOccurred.emit(FakeProcess.ProcessError.FailedToStart)

            self.assertIsNone(session.process)
            self.assertTrue(any("could not start" in message.lower() for message in errors))
            self.assertEqual(stopped, [True])

            session.start("ABC")
            self.assertIs(session.process, FakeProcess.instances[-1])
            self.assertEqual(len(FakeProcess.instances), 2)
            session.shutdown()
            FakeProcess.instances[-1].finished.emit(0, None)

    def test_scrcpy_discovery_failed_to_start_cleans_up_and_allows_retry(self):
        self._use_fake_process()
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "scrcpy.exe"
            executable.write_bytes(b"test")
            session = ScrcpySession(executable)
            errors = []
            session.error_occurred.connect(errors.append)

            session.start_discovery()
            first = FakeProcess.instances[-1]
            first.errorOccurred.emit(FakeProcess.ProcessError.FailedToStart)

            self.assertIsNone(session._discovery_process)
            self.assertIn("fake process error", session.initialization_error)
            self.assertEqual(errors, [session.initialization_error])

            session.start_discovery()
            self.assertIs(session._discovery_process, FakeProcess.instances[-1])
            self.assertEqual(len(FakeProcess.instances), 2)
            session.shutdown()
            FakeProcess.instances[-1].finished.emit(0, None)

    def test_stop_is_async_and_duplicate_stop_is_ignored(self):
        self._use_fake_process()
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "scrcpy.exe"
            executable.write_bytes(b"test")
            session = ScrcpySession(executable)
            session.capabilities = unittest.mock.Mock()
            session.capabilities.build_command.return_value = [str(executable), "--serial=ABC"]
            session.start("ABC")
            process = FakeProcess.instances[-1]

            session.stop()
            session.stop()

            self.assertEqual(process.terminate_count, 1)
            self.assertEqual(process.wait_count, 0)
            session._kill_timers[process].timeout.emit()
            self.assertTrue(process.killed)
            process.finished.emit(0, None)
            self.assertIsNone(session.process)
            session.shutdown()

    def test_shutdown_waits_asynchronously_for_active_processes(self):
        self._use_fake_process()
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "scrcpy.exe"
            executable.write_bytes(b"test")
            session = ScrcpySession(executable)
            session.capabilities = unittest.mock.Mock()
            session.capabilities.build_command.return_value = [str(executable), "--serial=ABC"]
            session.start("ABC")
            process = FakeProcess.instances[-1]
            shutdown = []
            session.shutdown_finished.connect(lambda: shutdown.append(True))

            session.shutdown()

            self.assertEqual(process.terminate_count, 1)
            self.assertEqual(process.wait_count, 0)
            self.assertEqual(shutdown, [])
            process.finished.emit(0, None)
            self.assertEqual(shutdown, [True])
            self.assertIsNone(session.process)

    def test_pairing_ui_clears_code_before_submitting(self):
        calls = []

        class Edit:
            def __init__(self, value):
                self.value = value

            def text(self):
                return self.value

            def clear(self):
                self.value = ""
                calls.append("cleared")

        class Adb:
            def pair_wireless(self, host, code):
                calls.append(("pair", host, code))

        window = SimpleNamespace(
            code_edit=Edit("123456"),
            target_edit=Edit("192.0.2.1:1234"),
            adb=Adb(),
        )

        MainWindow.pair_wireless(window)

        self.assertEqual(window.code_edit.value, "")
        self.assertEqual(calls, ["cleared", ("pair", "192.0.2.1:1234", "123456")])

    def test_window_close_waits_for_both_services_to_finish(self):
        class Service:
            def __init__(self):
                self.shutdown_finished = FakeSignal()
                self.shutdown_calls = 0

            def shutdown(self):
                self.shutdown_calls += 1

        class Event:
            def __init__(self):
                self.ignored = False
                self.accepted = False

            def ignore(self):
                self.ignored = True

            def accept(self):
                self.accepted = True

        adb = Service()
        scrcpy = Service()
        closed = []
        window = SimpleNamespace(
            _shutdown_complete=False,
            _close_requested=False,
            _shutdown_services_pending=set(),
            adb=adb,
            scrcpy=scrcpy,
            close=lambda: closed.append(True),
        )
        adb.shutdown_finished.connect(lambda: MainWindow._on_shutdown_service_finished(window, "adb"))
        scrcpy.shutdown_finished.connect(
            lambda: MainWindow._on_shutdown_service_finished(window, "scrcpy")
        )
        first_event = Event()

        with patch(
            "screenmirror.ui.main_window.QTimer.singleShot",
            side_effect=lambda _delay, callback: callback(),
        ):
            MainWindow.closeEvent(window, first_event)

            self.assertTrue(first_event.ignored)
            self.assertEqual((adb.shutdown_calls, scrcpy.shutdown_calls), (1, 1))
            adb.shutdown_finished.emit()
            self.assertEqual(window._shutdown_services_pending, {"scrcpy"})
            scrcpy.shutdown_finished.emit()

        self.assertTrue(window._shutdown_complete)
        self.assertEqual(closed, [True])
        final_event = Event()
        MainWindow.closeEvent(window, final_event)
        self.assertTrue(final_event.accepted)


if __name__ == "__main__":
    unittest.main()
