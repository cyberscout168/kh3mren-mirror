import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from screenmirror.adb import AdbManager


class FakeSignal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in list(self._slots):
            slot(*args)

    def clear(self):
        self._slots.clear()

    def disconnect(self):
        self.clear()


class FakeProcess:
    class ProcessChannelMode:
        SeparateChannels = object()

    class ProcessError:
        FailedToStart = 1

    class ProcessState:
        NotRunning = 0
        Starting = 1
        Running = 2

    def __init__(self, parent=None):
        self.readyReadStandardOutput = FakeSignal()
        self.readyReadStandardError = FakeSignal()
        self.errorOccurred = FakeSignal()
        self.finished = FakeSignal()
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.program = None
        self.arguments = []
        self.terminated = False
        self.killed = False
        self.deleted = False
        self.blocked = False
        self.process_state = self.ProcessState.NotRunning
        self.terminate_count = 0
        self.wait_count = 0

    def setProgram(self, value):
        self.program = value

    def setArguments(self, value):
        self.arguments = value

    def setProcessChannelMode(self, _value):
        pass

    def readAllStandardOutput(self):
        value = bytes(self.stdout)
        self.stdout.clear()
        return value

    def readAllStandardError(self):
        value = bytes(self.stderr)
        self.stderr.clear()
        return value

    def errorString(self):
        return "fake process error"

    def start(self):
        self.process_state = self.ProcessState.Running

    def terminate(self):
        self.terminate_count += 1
        self.terminated = True

    def waitForFinished(self, _timeout):
        self.wait_count += 1
        return True

    def kill(self):
        self.killed = True

    def state(self):
        return self.process_state

    def blockSignals(self, value):
        self.blocked = value

    def disconnect(self):
        for signal in (self.readyReadStandardOutput, self.readyReadStandardError,
                       self.errorOccurred, self.finished):
            signal.clear()

    def deleteLater(self):
        self.deleted = True


class FakeQProcess(FakeProcess):
    instances = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.instances.append(self)


class AdbLifecycleTests(unittest.TestCase):
    def setUp(self):
        FakeQProcess.instances.clear()
        self.patch = patch("screenmirror.adb.QProcess", FakeQProcess)
        self.patch.start()
        self.manager = AdbManager()
        self.manager.adb_path = Path("adb")

    def tearDown(self):
        self.manager.shutdown()
        self.patch.stop()

    def test_shutdown_invalidates_callbacks_and_terminates_process(self):
        callbacks = []
        shutdown = []
        self.manager.shutdown_finished.connect(lambda: shutdown.append(True))
        self.manager.run(["devices"], lambda *args: callbacks.append(args))
        process = FakeQProcess.instances[-1]

        self.manager.shutdown()
        self.assertEqual(process.wait_count, 0)
        self.assertEqual(shutdown, [])
        process.finished.emit(0, None)

        self.assertTrue(process.terminated)
        self.assertFalse(process.killed)
        self.assertTrue(process.deleted)
        self.assertEqual(callbacks, [])
        self.assertEqual(shutdown, [True])
        self.assertFalse(self.manager.screenshot("ABC", Path("unused.png")))

    def test_shutdown_waits_for_adb_and_screenshot_processes_without_blocking(self):
        shutdown = []
        self.manager.shutdown_finished.connect(lambda: shutdown.append(True))
        self.manager.run(["devices"], lambda *_args: None)
        adb_process = FakeQProcess.instances[-1]
        self.manager.screenshot("ABC", Path("unused.png"))
        screenshot_process = FakeQProcess.instances[-1]

        self.manager.shutdown()

        self.assertTrue(adb_process.terminated)
        self.assertTrue(screenshot_process.terminated)
        self.assertEqual((adb_process.wait_count, screenshot_process.wait_count), (0, 0))
        adb_process.finished.emit(0, None)
        self.assertEqual(shutdown, [])
        screenshot_process.finished.emit(1, None)

        self.assertEqual(shutdown, [True])
        self.assertIsNone(self.manager._process)
        self.assertIsNone(self.manager._screenshot_process)

    def test_refresh_requests_coalesce_while_another_command_runs(self):
        self.manager.run(["start-server"], lambda *_args: None)
        first = FakeQProcess.instances[-1]
        self.manager.refresh_devices()
        self.manager.refresh_devices()
        self.assertEqual(len(FakeQProcess.instances), 1)

        first.finished.emit(0, None)

        self.assertEqual(len(FakeQProcess.instances), 2)
        self.assertEqual(FakeQProcess.instances[-1].arguments, ["devices", "-l"])

    def test_screenshot_success_writes_png_asynchronously(self):
        results = []
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "capture.png"
            self.assertTrue(self.manager.screenshot("ABC", destination, lambda *args: results.append(args)))
            process = FakeQProcess.instances[-1]
            process.stdout.extend(b"\x89PNG\r\n\x1a\nimage")
            process.readyReadStandardOutput.emit()
            process.finished.emit(0, None)

            self.assertEqual(destination.read_bytes(), b"\x89PNG\r\n\x1a\nimage")
            self.assertEqual(results, [(True, str(destination))])
            self.assertTrue(process.deleted)

    def test_screenshot_failure_reports_stderr_and_cleans_up(self):
        results = []
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "capture.png"
            self.assertTrue(self.manager.screenshot("ABC", destination, lambda *args: results.append(args)))
            process = FakeQProcess.instances[-1]
            process.stderr.extend(b"device offline")
            process.readyReadStandardError.emit()
            process.finished.emit(1, None)

            self.assertFalse(destination.exists())
            self.assertEqual(results, [(False, "device offline")])
            self.assertTrue(process.deleted)

    def test_duplicate_screenshot_is_rejected(self):
        self.assertTrue(self.manager.screenshot("ABC", Path("first.png")))
        self.assertFalse(self.manager.screenshot("ABC", Path("second.png")))
        self.assertEqual(len(FakeQProcess.instances), 1)

    def test_adb_failed_to_start_cleans_up_and_allows_another_operation(self):
        errors = []
        busy = []
        self.manager.error_occurred.connect(errors.append)
        self.manager.busy_changed.connect(busy.append)

        self.manager.run(["devices", "-l"], lambda *_args: None)
        first = FakeQProcess.instances[-1]
        first.errorOccurred.emit(FakeProcess.ProcessError.FailedToStart)

        self.assertIsNone(self.manager._process)
        self.assertEqual(busy, [True, False])
        self.assertTrue(any("could not start" in message.lower() for message in errors))

        self.manager.run(["version"], lambda *_args: None)
        self.assertIs(self.manager._process, FakeQProcess.instances[-1])
        self.assertEqual(len(FakeQProcess.instances), 2)

    def test_adb_timeout_terminates_process_and_reports_after_cleanup(self):
        results = []
        busy = []
        self.manager.busy_changed.connect(busy.append)
        self.manager.run(["devices", "-l"], lambda *args: results.append(args))
        process = FakeQProcess.instances[-1]

        self.assertEqual(self.manager._process_timer.interval(), 15000)
        self.manager._process_timer.timeout.emit()

        self.assertTrue(process.terminated)
        self.assertEqual(busy, [True])
        self.manager._kill_timers[process].timeout.emit()
        self.assertTrue(process.killed)
        process.finished.emit(1, None)

        self.assertIsNone(self.manager._process)
        self.assertEqual(busy, [True, False])
        self.assertIn("timed out after 15 seconds", results[0][1])
        self.manager.run(["version"], lambda *_args: None)
        next_process = FakeQProcess.instances[-1]
        self.assertIs(self.manager._process, next_process)
        next_process.finished.emit(0, None)

    def test_pairing_code_is_redacted_from_adb_output(self):
        messages = []
        self.manager.error_occurred.connect(messages.append)
        self.manager.pair_wireless("192.0.2.1:1234", "123456")
        process = FakeQProcess.instances[-1]
        process.stderr.extend(b"pairing code 123456 was rejected")
        process.finished.emit(1, None)

        self.assertTrue(messages)
        self.assertNotIn("123456", messages[-1])
        self.assertIn("[redacted]", messages[-1])

    def test_screenshot_failed_to_start_cleans_up_and_reports_callback(self):
        results = []
        busy = []
        self.manager.screenshot_busy_changed.connect(busy.append)
        self.assertTrue(
            self.manager.screenshot("ABC", Path("unused.png"), lambda *args: results.append(args))
        )
        process = FakeQProcess.instances[-1]
        process.errorOccurred.emit(FakeProcess.ProcessError.FailedToStart)

        self.assertIsNone(self.manager._screenshot_process)
        self.assertEqual(busy, [True, False])
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])
        self.assertIn("could not start", results[0][1].lower())

        self.assertTrue(self.manager.screenshot("ABC", Path("next.png")))
        self.assertEqual(len(FakeQProcess.instances), 2)

    def test_screenshot_timeout_terminates_and_reports_failure(self):
        results = []
        self.assertTrue(
            self.manager.screenshot("ABC", Path("unused.png"), lambda *args: results.append(args))
        )
        process = FakeQProcess.instances[-1]

        self.assertEqual(self.manager._screenshot_timer.interval(), 60000)
        self.manager._screenshot_timer.timeout.emit()
        self.assertTrue(process.terminated)
        self.manager._kill_timers[process].timeout.emit()
        self.assertTrue(process.killed)
        process.finished.emit(1, None)

        self.assertFalse(results[0][0])
        self.assertIn("timed out after 60 seconds", results[0][1])
        self.assertIsNone(self.manager._screenshot_process)


if __name__ == "__main__":
    unittest.main()
