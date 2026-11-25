import argparse
import unittest

from subtitle_shift import adjust, parse, render, seconds


class SubtitleShiftTests(unittest.TestCase):
    def test_extreme_decimal_returns_an_argument_error(self):
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "fractional digits"):
            seconds("1e9999999")

    def test_millisecond_precision(self):
        self.assertEqual(seconds("-1.125"), -1125)
        with self.assertRaises(argparse.ArgumentTypeError):
            seconds("0.0001")

    def test_clipping_rebases_time_and_preserves_cue_text(self):
        cues = parse("1\n00:00:00,500 --> 00:00:02,500 X1:15\nLine one\nLine two\n")
        result = render(adjust(cues, 250, 1000, 1500))
        self.assertEqual(
            result, "1\n00:00:00,000 --> 00:00:00,500 X1:15\nLine one\nLine two\n\n"
        )
