#!/usr/bin/env python3
"""Pack the Datasoft title picture for src/boot.asm.

Reads src/title_picture.kla (Koala Painter: load address $6000, 8000 bytes bitmap,
1000 bytes screen, 1000 bytes colour RAM, 1 byte background) and writes
src/title_picture.rle: the bitmap, the screen and the colour RAM, each as one RLE
stream. A stream is literal bytes and runs. A run is ESC, count (1-255), value.
ESC, 0 ends a stream. The first byte of the file is ESC; the second is the background.

Usage (from the project folder): python3 tools/pack_title_picture.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
KLA = ROOT / "src" / "title_picture.kla"
OUT = ROOT / "src" / "title_picture.rle"


def pack(data: bytes, esc: int) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        j = i
        while j < len(data) and data[j] == data[i] and j - i < 255:
            j += 1
        if j - i >= 4 or data[i] == esc:
            out += bytes([esc, j - i, data[i]])
            i = j
        else:
            out.append(data[i])
            i += 1
    return bytes(out + bytes([esc, 0]))


def main() -> None:
    kla = KLA.read_bytes()
    if len(kla) != 10003 or kla[:2] != b"\x00\x60":
        raise SystemExit(f"{KLA}: not a Koala file of 10003 bytes with load address $6000")
    body = kla[2:]
    bitmap, screen, colour, background = body[:8000], body[8000:9000], body[9000:10000], body[10000]
    used = set(bitmap) | set(screen) | set(colour)
    esc = next((b for b in range(256) if b not in used), 0xFE)
    out = bytes([esc, background]) + pack(bitmap, esc) + pack(screen, esc) + pack(colour, esc)
    OUT.write_bytes(out)
    print(f"{OUT.relative_to(ROOT)}: {len(out)} bytes, escape ${esc:02X}")


if __name__ == "__main__":
    main()
