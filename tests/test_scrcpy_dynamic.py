import unittest
from pathlib import Path

from screenmirror.dynamic_settings import ScrcpyCommandBuilder
from screenmirror.scrcpy_help import ScrcpyHelpParser


HELP = """Options:
    --serial=serial
        Select device.
    -b, --video-bit-rate=value
        Encode video at a given rate.
    --fullscreen
        Start fullscreen.
    --audio-codec=name
        Select audio codec. Possible values are \"opus\", \"aac\" or \"raw\".
    --unknown-format <value>
        A future option.
"""


class DynamicScrcpyTests(unittest.TestCase):
    def setUp(self):
        self.options = ScrcpyHelpParser().parse(HELP, "5.0.1")

    def test_parser_extracts_aliases_values_flags_choices_and_version(self):
        bitrate = next(option for option in self.options if option.long_option == "--video-bit-rate")
        self.assertEqual(bitrate.short_option, "-b")
        self.assertTrue(bitrate.accepts_value)
        self.assertEqual(bitrate.version, "5.0.1")
        self.assertTrue(next(option for option in self.options if option.long_option == "--fullscreen").boolean_flag)
        self.assertEqual(next(option for option in self.options if option.long_option == "--audio-codec").choices, ("opus", "aac", "raw"))

    def test_builder_only_emits_discovered_options(self):
        builder = ScrcpyCommandBuilder(Path("scrcpy"), self.options)
        args = builder.build({"--fullscreen": True, "--video-bit-rate": "8M", "--not-supported": "x"}, "ABC")
        self.assertEqual(args[1:], ["--serial=ABC", "--fullscreen", "--video-bit-rate=8M"])

    def test_builder_rejects_unknown_choice(self):
        builder = ScrcpyCommandBuilder(Path("scrcpy"), self.options)
        with self.assertRaisesRegex(ValueError, "must be one of"):
            builder.build({"--audio-codec": "bad"}, "ABC")

    def test_optional_argument_help_header_does_not_pollute_previous_option(self):
        options = ScrcpyHelpParser().parse(
            """Options:
    -p, --port=port[:port]
        Set the TCP port range used by the client to listen.
        Default is 27183:27199.
    --pause-on-exit[=mode]
        Possible values are \"true\", \"false\" and \"if-error\".
        Passing the option without argument is equivalent to passing \"true\".
""",
            "5.0.1",
        )
        port = next(option for option in options if option.canonical == "--port")
        pause = next(option for option in options if option.canonical == "--pause-on-exit")
        self.assertEqual(port.choices, ())
        self.assertEqual(port.argument_name, "port[:port]")
        self.assertEqual(pause.argument_name, "mode")
        self.assertEqual(pause.choices, ("true", "false", "if-error"))

    def test_port_value_rejects_old_boolean_preference_and_accepts_numeric_range(self):
        options = ScrcpyHelpParser().parse(
            """Options:
    --serial=serial
        Select the device.
    --port=port[:port]
        Set the TCP port range used by the client to listen.
""",
            "5.0.1",
        )
        builder = ScrcpyCommandBuilder(Path("scrcpy"), options)
        with self.assertRaisesRegex(ValueError, "numeric port"):
            builder.build({"--port": "true"}, "ABC")
        self.assertEqual(
            builder.build({"--port": "27183:27199"}, "ABC")[2],
            "--port=27183:27199",
        )
        for invalid in ("0", "65536", "30000:20000", "27183:abc"):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                builder.build({"--port": invalid}, "ABC")


if __name__ == "__main__":
    unittest.main()
