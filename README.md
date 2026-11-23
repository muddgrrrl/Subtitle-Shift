# Subtitle Shift

Fix captions that are early or late, or turn an existing subtitle file into captions for a short clip.

```sh
python3 subtitle_shift.py captions.srt --offset=-1.250 -o synced.srt
python3 subtitle_shift.py captions.srt --from 34.5 --to 52 -o clip.srt
```

Requires Python 3.8+. Time arguments are seconds, precise to milliseconds. The offset applies first, then cues are clipped to the chosen range and rebased to zero. The script renumbers cues and preserves multiline caption text and optional position settings. It reads UTF-8 SubRip files, including files with a UTF-8 BOM. Without `-o`, it writes to standard output. With `-o`, it creates a new file and refuses to overwrite an existing one.

[MIT license](LICENSE)
