import unittest

from screenmirror.adb import parse_devices


class AdbParserTests(unittest.TestCase):
    def test_parse_devices_with_metadata(self) -> None:
        devices = parse_devices(
            "List of devices attached\n"
            "ABC123\tdevice product:demo model:Pixel_8 transport_id:1\n"
            "XYZ999\tunauthorized\n"
        )
        self.assertEqual(devices[0].serial, "ABC123")
        self.assertEqual(devices[0].state, "device")
        self.assertEqual(devices[0].model, "Pixel_8")
        self.assertEqual(devices[1].state, "unauthorized")


if __name__ == "__main__":
    unittest.main()
