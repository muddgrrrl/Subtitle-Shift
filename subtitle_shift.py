#!/usr/bin/env python3
"""Shift SubRip subtitle timing and optionally clip it to a new timeline."""

import argparse
from dataclasses import dataclass
from decimal import Decimal, DecimalException
from pathlib import Path
import re
import sys

TIMECODE = r"(\d{2,}:[0-5]\d:[0-5]\d,\d{3})"
TIMING = re.compile(rf"^{TIMECODE}[ \t]+-->[ \t]+{TIMECODE}([ \t]+.*)?$")


@dataclass(frozen=True)
class Cue:
    start: int
    end: int
    text: str
    settings: str = ""


def milliseconds(value):
    hours, minutes, seconds, fraction = map(int, re.split("[:,]", value))
    return (((hours * 60 + minutes) * 60) + seconds) * 1000 + fraction


def timecode(value):
    seconds, fraction = divmod(value, 1000)
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    return f"{hours:02}:{minute:02}:{sec:02},{fraction:03}"


def seconds(value):
    try:
        scaled = Decimal(value) * 1000
        if scaled.is_finite() and abs(scaled) <= 10**12 and scaled == scaled.to_integral_value():
            return int(scaled)
    except DecimalException:
        pass
    raise argparse.ArgumentTypeError("use seconds with at most three fractional digits")


def parse(text):
    cues = []
    for number, block in enumerate(re.split(r"\n[ \t]*\n+", text.strip("\n")), 1):
        if not block.strip():
            continue
        lines = block.splitlines()
        if lines[0].strip().isdigit():
            lines = lines[1:]
        match = TIMING.fullmatch(lines[0].strip()) if lines else None
        if not match or len(lines) < 2:
            raise ValueError(f"cue {number}: expected a timing line and subtitle text")
        start, end = map(milliseconds, match.group(1, 2))
        if end <= start:
            raise ValueError(f"cue {number}: end must follow start")
        cues.append(Cue(start, end, "\n".join(lines[1:]), match.group(3) or ""))
    return cues


def adjust(cues, offset, trim_start, trim_end):
    shifted = []
    for cue in cues:
        start = max(cue.start + offset, trim_start)
        end = cue.end + offset
        if trim_end is not None:
            end = min(end, trim_end)
        if start < end:
            shifted.append(Cue(start - trim_start, end - trim_start, cue.text, cue.settings))
    return shifted


def render(cues):
    return "".join(
        f"{index}\n{timecode(cue.start)} --> {timecode(cue.end)}{cue.settings}\n{cue.text}\n\n"
        for index, cue in enumerate(cues, 1)
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 .srt file")
    parser.add_argument("--offset", type=seconds, default=0, help="seconds to shift, including negative values")
    parser.add_argument("--from", dest="trim_start", type=seconds, default=0,
                        help="trim from this shifted time and rebase it to zero")
    parser.add_argument("--to", dest="trim_end", type=seconds, help="trim to this shifted time")
    parser.add_argument("-o", "--output", type=Path, help="write a new file instead of standard output")
    args = parser.parse_args(argv)
    if args.trim_start < 0 or (args.trim_end is not None and args.trim_end <= args.trim_start):
        parser.error("choose a nonnegative start and an end after that start")
    try:
        cues = parse(args.input.read_text(encoding="utf-8-sig"))
        result = render(adjust(cues, args.offset, args.trim_start, args.trim_end))
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as output:
                output.write(result)
        else:
            sys.stdout.write(result)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Subtitle Shift: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
