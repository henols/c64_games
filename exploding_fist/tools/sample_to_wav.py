#!/usr/bin/env python3
"""Render a 1-bit sample of The Way of the Exploding Fist as a WAV file.

Both sample players of the game (M.MYTINY in the loading stage, and the sample IRQ of the
game) work the same way. CIA1 timer A underflows every TICK_CYCLES cycles. Timer B counts
these underflows. At each timer B IRQ the player flips the SID volume between 0 and 15 and
loads timer B with the count for the next sample byte: count = lo[byte] + 256 * hi[byte].
So each sample byte is the length of one half-wave of a square wave.

The script reads a memory file: a 64 KB image (image.bin of a capture: address = offset), or
a plain build with --start, the address of its first byte. It takes the sample bytes from
SAMPLE_START to SAMPLE_END (SAMPLE_END not included) and the two count tables LO and HI, and
writes a 16-bit mono WAV at 44100 Hz.

Usage (from the group folder):
  python3 tools/sample_to_wav.py IMAGE SAMPLE_START SAMPLE_END LO HI OUT.wav
      [--start ADDRESS] [--tick CYCLES]
Example, the speech sample of the loading stage:
  python3 tools/sample_to_wav.py v1/original/releases/2010_loading/image.bin \\
      0x2000 0x35d6 0x9800 0x9900 v1/docs/assets/loading_sample.wav
"""
import argparse
import struct
import wave

PAL_CLOCK = 985248  # cycles per second of a PAL C64
RATE = 44100


def render(image: bytes, start: int, end: int, lo: int, hi: int, tick: int) -> bytes:
    out = bytearray()
    level = 1
    t = 0.0
    produced = 0
    for address in range(start, end):
        value = image[address]
        count = image[lo + value] + 256 * image[hi + value]
        t += (count + 1) * tick / PAL_CLOCK
        target = int(t * RATE)
        amplitude = 12000 if level else -12000
        out += struct.pack('<h', amplitude) * (target - produced)
        produced = target
        level ^= 1
    return bytes(out)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('image')
    p.add_argument('sample_start', metavar='SAMPLE_START', type=lambda s: int(s, 0))
    p.add_argument('sample_end', metavar='SAMPLE_END', type=lambda s: int(s, 0))
    p.add_argument('lo', type=lambda s: int(s, 0))
    p.add_argument('hi', type=lambda s: int(s, 0))
    p.add_argument('out')
    p.add_argument('--tick', type=int, default=9, help='cycles per timer A underflow (default 9)')
    p.add_argument('--start', type=lambda s: int(s, 0), metavar='ADDRESS',
                   help='address of the first byte of IMAGE (default 0, for a 64 KB image)')
    a = p.parse_args()
    data = open(a.image, 'rb').read()
    if a.start is None:
        if len(data) != 65536:
            raise SystemExit(f'{a.image}: not a 64 KB memory image; give --start for a plain build')
        a.start = 0
    first, last = a.start, a.start + len(data)  # last not included
    if last > 65536:
        raise SystemExit(f'{a.image}: {len(data)} bytes from ${first:04X} go past $FFFF')
    for name, lo, hi in (('sample', a.sample_start, a.sample_end),
                         ('LO table', a.lo, a.lo + 256), ('HI table', a.hi, a.hi + 256)):
        if lo < first or hi > last:
            raise SystemExit(f'{a.image}: the {name} ${lo:04X}-${hi - 1:04X} is not in '
                             f'${first:04X}-${last - 1:04X} of the file')
    image = bytes(first) + data + bytes(65536 - last)
    frames = render(image, a.sample_start, a.sample_end, a.lo, a.hi, a.tick)
    with wave.open(a.out, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames)
    print(f'{a.out}: {len(frames) // 2 / RATE:.2f} s')


if __name__ == '__main__':
    main()
