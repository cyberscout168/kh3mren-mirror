"""Tolerant parsing of scrcpy's human-readable help output."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class ScrcpyOption:
    name: str
    short_option: str | None = None
    long_option: str | None = None
    argument_name: str | None = None
    description: str = ""
    category: str = "Advanced"
    accepts_value: bool = False
    boolean_flag: bool = False
    supported: bool = True
    version: str | None = None
    choices: tuple[str, ...] = field(default_factory=tuple)

    @property
    def canonical(self) -> str:
        return self.long_option or self.short_option or self.name


_HEADER = re.compile(
    r"^\s{2,}(?:(?P<short>-[A-Za-z0-9]),\s*)?(?P<long>--[A-Za-z0-9][\w-]*)"
    r"(?:[= ](?P<arg>[^\s]+)|\[=(?P<optional_arg>[^\]\s]+)\])?\s*$"
)
_CATEGORY_RULES = (
    ("Audio", ("audio",)),
    ("Video", ("video", "codec", "bit-rate", "fps", "max-size", "crop", "orientation", "angle")),
    ("Camera", ("camera",)),
    ("Recording", ("record", "time-limit", "raw-stream")),
    ("Connection", ("tcpip", "tunnel", "port", "serial", "select-usb", "verbosity")),
    ("Window", ("window", "fullscreen", "always-on-top", "borderless", "position", "display", "stay-awake")),
    ("Input and Control", ("input", "control", "keyboard", "mouse", "gamepad", "touch", "clipboard", "power-off-on-close")),
    ("Device", ("device", "screen-off", "turn-screen-off", "list-", "forward", "push-target")),
)


def _category(option: str, description: str) -> str:
    text = f"{option} {description}".lower()
    for category, words in _CATEGORY_RULES:
        if any(word in text for word in words):
            return category
    return "Advanced"


def _choices(description: str) -> tuple[str, ...]:
    # scrcpy has used both "Possible values are ..." and short parenthetical lists.
    match = re.search(r"possible values are\s*:?\s*(.*?)(?:\.|\n|$)", description, re.I | re.S)
    candidate = match.group(1) if match else ""
    if not candidate:
        return ()
    quoted = re.findall(r"[\"']([^\"']+)[\"']", description)
    if len(quoted) >= 2:
        return tuple(dict.fromkeys(quoted))
    values = re.findall(r"[\"']([^\"']+)[\"']|(?<![\w-])([A-Za-z][\w-]*)(?![\w-])", candidate)
    result = tuple(a or b for a, b in values)
    return tuple(value for value in result if value not in {"and", "or"})


class ScrcpyHelpParser:
    """Parse options without relying on one exact scrcpy version's layout."""

    CACHE_VERSION = 2

    def parse(self, help_text: str, version: str | None = None) -> list[ScrcpyOption]:
        lines = help_text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
        found: list[ScrcpyOption] = []
        current: dict[str, object] | None = None

        def finish() -> None:
            nonlocal current
            if not current:
                return
            description = " ".join(str(x).strip() for x in current["description"] if str(x).strip())
            long_option = str(current["long"])
            arg = current["arg"] or current["optional_arg"]
            found.append(ScrcpyOption(
                name=long_option.lstrip("-") if long_option else str(current["short"] or "").lstrip("-"),
                short_option=current["short"], long_option=long_option,
                argument_name=str(arg) if arg else None, description=description,
                category=_category(long_option, description), accepts_value=bool(arg),
                boolean_flag=not bool(arg), version=version, choices=_choices(description),
            ))
            current = None

        for line in lines:
            match = _HEADER.match(line)
            if match:
                finish()
                current = {"short": match.group("short"), "long": match.group("long"),
                           "arg": match.group("arg"), "optional_arg": match.group("optional_arg"),
                           "description": []}
            elif current is not None:
                stripped = line.strip()
                if stripped:
                    current["description"].append(stripped)
        finish()

        unique: dict[str, ScrcpyOption] = {}
        for option in found:
            unique[option.canonical] = option
        return list(unique.values())

