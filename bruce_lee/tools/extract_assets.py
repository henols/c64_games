#!/usr/bin/env python3
"""Bruce Lee (C64) asset extractor.

Reads the 64 KiB RAM image at the game entry (unpacked/image.bin) and writes
graphics, maps, tables, texts, sound data and the demo input into assets/.

Python 3 standard library only.  Run from the project folder:

    python3 -I tools/extract_assets.py            # extract everything
    python3 -I tools/extract_assets.py --check    # also compare the room renders
                                                  # with runs/rooms/roomNN*.png

Formats: .c64-re-tools/local/formats.md and formats_sound.md (condensed in
assets/README.md).  Names come from the knowledge export
.c64-re-tools/local/kexport.json when it is present; the tool falls back to
built-in names (the same knowledge names) when it is not.
"""

import json
import os
import re
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE = os.path.join(ROOT, "unpacked", "image.bin")
KEXPORT = os.path.join(ROOT, ".c64-re-tools", "local", "kexport.json")
OUT = os.path.join(ROOT, "assets")
SHOTS = os.path.join(ROOT, "runs", "rooms")

IMG = b""


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def rmtree(path):
    """shutil.rmtree without shutil (not present in every minimal Python)."""
    if not os.path.isdir(path):
        return
    for d, dirs, files in os.walk(path, topdown=False):
        for f in files:
            os.remove(os.path.join(d, f))
        for x in dirs:
            os.rmdir(os.path.join(d, x))
    os.rmdir(path)


def rd(a):
    return IMG[a & 0xFFFF]


def w16(a):
    return IMG[a] | IMG[a + 1] << 8


def hx(a):
    return "$%04X" % a


def hb(b):
    return "$%02X" % b


def hexbytes(bs):
    return " ".join("%02x" % b for b in bs)


def out_path(*parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def to_json(obj, indent=0):
    """JSON with one item per line, but lists of plain values on one line."""
    pad = " " * indent
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = ["%s %s: %s" % (pad, json.dumps(k), to_json(v, indent + 1)) for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(obj, list):
        flat = json.dumps(obj, ensure_ascii=False)
        if all(not isinstance(v, (dict, list)) for v in obj) and (
                len(flat) <= 160 or all(not isinstance(v, str) for v in obj)):
            return flat
        items = ["%s %s" % (pad, to_json(v, indent + 1)) for v in obj]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    return json.dumps(obj, ensure_ascii=False)


def write_json(rel, obj):
    with open(out_path(*rel.split("/")), "w", newline="\n", encoding="utf-8") as f:
        f.write(to_json(obj))
        f.write("\n")


def write_bin(rel, data):
    with open(out_path(*rel.split("/")), "wb") as f:
        f.write(bytes(data))


def write_text(rel, text):
    with open(out_path(*rel.split("/")), "w", newline="\n", encoding="utf-8") as f:
        f.write(text)


# ----------------------------------------------------------------------------
# knowledge names
# ----------------------------------------------------------------------------

class Knowledge:
    def __init__(self, path):
        self.symbols = {}
        self.regions = []
        self.comments = {}
        self.loaded = False
        if not os.path.exists(path):
            return
        with open(path) as f:
            d = json.load(f)
        for s in d.get("symbols", []):
            self.symbols[int(s["address"][1:], 16)] = s["name"]
        for r in d.get("regions", []):
            r = dict(r)
            r["s"] = int(r["start"][1:], 16)
            r["e"] = int(r["end"][1:], 16)
            self.regions.append(r)
        self.regions.sort(key=lambda r: (r["s"], r["e"]))
        for c in d.get("comments", []):
            a = int(c["address"][1:], 16)
            self.comments.setdefault(a, {})[c["placement"]] = c["text"]
        self.loaded = True
        self._sorted = sorted(self.symbols)

    def name(self, a, default=None):
        if a in self.symbols:
            return self.symbols[a]
        return default

    def label(self, a):
        """Exact name, else nearest lower symbol + offset (within 256 bytes)."""
        if a in self.symbols:
            return self.symbols[a]
        lo, hi = 0, len(self._sorted) if self.loaded else 0
        best = None
        while lo < hi:
            m = (lo + hi) // 2
            if self._sorted[m] <= a:
                best = self._sorted[m]
                lo = m + 1
            else:
                hi = m
        if best is not None and 0 < a - best < 0x100:
            return "%s+%d" % (self.symbols[best], a - best)
        return None

    def comment(self, a):
        c = self.comments.get(a, {})
        return c.get("line") or c.get("side")

    def region_at(self, a):
        for r in self.regions:
            if r["s"] <= a <= r["e"]:
                return r
        return None


K = None


def nm(a, default):
    """Knowledge name of address a, or the built-in default."""
    return K.name(a, default) if K else default


# ----------------------------------------------------------------------------
# PNG
# ----------------------------------------------------------------------------

# Pepto's C64 palette (VICE default), indexed by C64 colour number.
PALETTE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x68, 0x37, 0x2B), (0x70, 0xA4, 0xB2),
    (0x6F, 0x3D, 0x86), (0x58, 0x8D, 0x43), (0x35, 0x28, 0x79), (0xB8, 0xC7, 0x6F),
    (0x6F, 0x4F, 0x25), (0x43, 0x39, 0x00), (0x9A, 0x67, 0x59), (0x44, 0x44, 0x44),
    (0x6C, 0x6C, 0x6C), (0x9A, 0xD2, 0x84), (0x6C, 0x5E, 0xB5), (0x95, 0x95, 0x95),
]
COLOUR_NAMES = ["black", "white", "red", "cyan", "purple", "green", "blue", "yellow",
                "orange", "brown", "light red", "dark grey", "grey", "light green",
                "light blue", "light grey"]
SHEET_BG = (0x8C, 0xA0, 0xB4)  # sheet background, not a C64 colour (index 16)


def png_chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)


def write_png(rel, w, h, pix, palette=None, trns=None):
    """Indexed 8-bit PNG.  pix = flat list of palette indices."""
    palette = palette or PALETTE
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(pix[y * w:(y + 1) * w])
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
    data += png_chunk(b"PLTE", b"".join(bytes(c) for c in palette))
    if trns is not None:
        data += png_chunk(b"tRNS", bytes(trns))
    data += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += png_chunk(b"IEND", b"")
    with open(out_path(*rel.split("/")), "wb") as f:
        f.write(data)


def read_png(path):
    """Minimal PNG decoder (8-bit, non-interlaced, colour types 0/2/3/6).
    Returns (w, h, rows, palette); rows hold palette indices for type 3,
    else RGB tuples."""
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: " + path)
    p = 8
    idat = b""
    plte = None
    while p < len(d):
        n, = struct.unpack(">I", d[p:p + 4])
        t = d[p + 4:p + 8]
        body = d[p + 8:p + 8 + n]
        if t == b"IHDR":
            w, h, bd, ct, _, _, il = struct.unpack(">IIBBBBB", body)
        elif t == b"PLTE":
            plte = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif t == b"IDAT":
            idat += body
        p += 12 + n
    if bd != 8 or il != 0:
        raise ValueError("unsupported PNG layout")
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows = []
    prev = bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        prev = line
        if ct == 3:
            rows.append(list(line))
        elif ct == 0:
            rows.append([(v, v, v) for v in line])
        else:
            rows.append([tuple(line[x * bpp:x * bpp + 3]) for x in range(w)])
    return w, h, rows, plte


def screenshot_indices(path):
    """Screenshot as C64 colour numbers.  The emulator writes a 16-entry
    palette in C64 colour order; otherwise use the nearest Pepto colour."""
    w, h, rows, plte = read_png(path)
    if plte is not None and len(plte) == 16 and plte[0] == (0, 0, 0) and plte[1] == (255, 255, 255):
        return w, h, rows
    if plte is not None:
        rows = [[plte[v] for v in r] for r in rows]

    def near(c):
        return min(range(16), key=lambda k: sum((c[j] - PALETTE[k][j]) ** 2 for j in range(3)))
    cache = {}
    out = []
    for r in rows:
        o = []
        for c in r:
            if c not in cache:
                cache[c] = near(c)
            o.append(cache[c])
        out.append(o)
    return w, h, out


# ----------------------------------------------------------------------------
# addresses (formats.md)
# ----------------------------------------------------------------------------

NROOMS = 20
CHARSET_SRC = [0x9000, 0x9400, 0x9800, 0x9C00]
CHARSET_EXP = [0xA000, 0xA800, 0xB000, 0xB800]
CHARSET_D018 = [0x38, 0x3A, 0x3C, 0x3E]

ROOM_CHAR_COLOURS = 0x47A0
ROOM_SPLIT_COLOUR_PTRS = 0x480B
ROOM_RASTER_LINE_PTRS = 0x4833
ROOM_ATARI_COLOUR_PTRS = 0x4AA8
ROOM_MAP_LO, ROOM_MAP_HI = 0x4B34, 0x4B49
EXIT_TABLES = {  # code: (dest room, x, y)
    2: (0x4B5E, 0x4BFE, 0x4C12),
    3: (0x4B72, 0x4C26, 0x4C3A),
    4: (0x4B86, 0x4C4E, 0x4C62),
    5: (0x4B9A, 0x4C76, 0x4C8A),
}
ROOM_SPAWN_X, ROOM_SPAWN_Y = 0x4BAE, 0x4BC2
ROOM_ALT_SPAWN_X, ROOM_ALT_SPAWN_Y = 0x4BD6, 0x4BEA
ROOM_NO_COMBAT = 0x4C9E
ROOM_LANTERN_COUNTS = 0x4CCE
LANTERN_LIST_PTRS = 0x4CE2
ROOM_SETUP_HANDLERS = 0x4E9C
ROOM_FRAME_HANDLERS = 0x4EC4
ENEMY_DELAY_TABLES = [0x130B, 0x131F, 0x1333, 0x1347, 0x135B, 0x136F]
FRAME_SRC_LO, FRAME_SRC_HI = 0x59BD, 0x5A8F
FRAME_HEIGHT, FRAME_COLOUR, FRAME_WIDE = 0x5B61, 0x5C33, 0x5CBF
FRAME_MASK_LO, FRAME_MASK_HI = 0x1167, 0x1239
ACTOR_TYPE_BASE, ACTOR_SPRITE_A, ACTOR_SPRITE_B = 0x59A5, 0x59A8, 0x59AB
MESSAGE_POINTERS = 0x43BE
NMESSAGES = 101
TITLE_FONT = 0x8400
TM_SPRITE_ROWS = 0x0E40
DEMO_INPUT = 0xF300

BUILTIN_NAMES = {
    0x47A0: "room_char_colours", 0x47C8: "room_band_colours", 0x47F9: "room_raster_split_lists",
    0x480B: "room_split_colour_ptrs", 0x4833: "room_raster_line_ptrs",
    0x4AA8: "room_atari_colour_ptrs", 0x4B34: "room_map_ptrs_lo", 0x4B49: "room_map_ptrs_hi",
    0x4B5E: "exit2_room", 0x4B72: "exit3_room", 0x4B86: "exit4_room", 0x4B9A: "exit5_room",
    0x4BFE: "exit2_x", 0x4C12: "exit2_y", 0x4C26: "exit3_x", 0x4C3A: "exit3_y",
    0x4C4E: "exit4_x", 0x4C62: "exit4_y", 0x4C76: "exit5_x", 0x4C8A: "exit5_y",
    0x4BAE: "room_spawn_x", 0x4BC2: "room_spawn_y", 0x4BD6: "room_alt_spawn_x",
    0x4BEA: "room_alt_spawn_y", 0x4C9E: "room_no_combat_flags", 0x4CCE: "room_lantern_counts",
    0x4CE2: "lantern_list_ptrs", 0x4E9C: "room_setup_handlers", 0x4EC4: "room_frame_handlers",
    0x130B: "ninja_first_spawn_delay", 0x131F: "ninja_respawn_delay",
    0x1333: "ninja_entry_preference", 0x1347: "yamo_first_spawn_delay",
    0x135B: "yamo_respawn_delay", 0x136F: "yamo_entry_preference",
    0x1167: "actor_frame_addr_lo", 0x1239: "actor_frame_addr_hi",
    0x59BD: "frame_src_lo", 0x5A8F: "frame_src_hi", 0x5B61: "frame_height",
    0x5C33: "frame_colour", 0x5CBF: "frame_wide_flag", 0x5D91: "frame_graphics",
    0x43BE: "message_pointers", 0x8400: "title_font", 0x0E40: "tm_sprite_rows",
    0x9000: "charset_src_0", 0x9400: "charset_src_1", 0x9800: "charset_src_2",
    0x9C00: "charset_src_3", 0xF300: "demo_input", 0x4707: "version_text",
    0x5900: "leftover_source_text", 0xEBE5: "sfx_table", 0xE8C0: "music_tune_table",
}


def tname(a):
    return nm(a, BUILTIN_NAMES.get(a, "tbl_%04x" % a))


def table20(a):
    return [IMG[a + r] for r in range(NROOMS)]


# ----------------------------------------------------------------------------
# tiny 6502 interpreter (documented opcodes) to run the room setup code
# ----------------------------------------------------------------------------

class CPU6502:
    """Just enough 6502 to run short game routines on a RAM copy.  I/O at
    $D000-$DFFF is plain memory (colour RAM included); no interrupts."""

    MODES = {}

    def __init__(self, mem):
        self.m = mem
        self.a = self.x = self.y = 0
        self.sp = 0xFF
        self.c = self.z = self.i = self.d = self.v = self.n = 0

    def push(self, v):
        self.m[0x100 + self.sp] = v & 0xFF
        self.sp = (self.sp - 1) & 0xFF

    def pull(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.m[0x100 + self.sp]

    def nz(self, v):
        v &= 0xFF
        self.z = int(v == 0)
        self.n = v >> 7
        return v

    def flags(self):
        return (self.n << 7 | self.v << 6 | 0x20 | 0x10 | self.d << 3 | self.i << 2 | self.z << 1 | self.c)

    def setflags(self, p):
        self.n, self.v, self.d, self.i, self.z, self.c = p >> 7 & 1, p >> 6 & 1, p >> 3 & 1, p >> 2 & 1, p >> 1 & 1, p & 1

    def call(self, addr, limit=200000):
        """JSR addr and run until it returns.  Returns the number of steps."""
        m = self.m
        self.push(0xFF)
        self.push(0xFE)          # return to $FFFF: sentinel
        pc = addr
        for step in range(limit):
            if pc == 0xFFFF:
                return step
            op = m[pc]
            pc = self.execute(op, pc)
        raise RuntimeError("step limit at %04X" % pc)

    def execute(self, op, pc):
        m = self.m
        lo = m[(pc + 1) & 0xFFFF]
        hi = m[(pc + 2) & 0xFFFF]
        w = lo | hi << 8
        g = op & 3
        mode = (op >> 2) & 7
        aaa = op >> 5

        def zpw(a):
            return m[a & 0xFF] | m[(a + 1) & 0xFF] << 8

        # --- single-byte and special instructions -----------------------------
        if op == 0x00:
            raise RuntimeError("BRK at %04X" % pc)
        if op == 0x20:
            ret = pc + 2
            self.push(ret >> 8)
            self.push(ret)
            return w
        if op == 0x60:
            lo2 = self.pull()
            return ((self.pull() << 8 | lo2) + 1) & 0xFFFF
        if op == 0x40:
            self.setflags(self.pull())
            lo2 = self.pull()
            return self.pull() << 8 | lo2
        if op == 0x4C:
            return w
        if op == 0x6C:
            return m[w] | m[(w & 0xFF00) | ((w + 1) & 0xFF)] << 8
        if op & 0x1F == 0x10:      # branches
            cond = [self.n, self.v, self.c, self.z][op >> 6]
            if cond == (op >> 5) & 1:
                return (pc + 2 + (lo - 256 if lo > 127 else lo)) & 0xFFFF
            return pc + 2
        simple = {
            0x08: lambda: self.push(self.flags()),
            0x28: lambda: self.setflags(self.pull()),
            0x48: lambda: self.push(self.a),
            0x68: lambda: setattr(self, "a", self.nz(self.pull())),
            0x18: lambda: setattr(self, "c", 0), 0x38: lambda: setattr(self, "c", 1),
            0x58: lambda: setattr(self, "i", 0), 0x78: lambda: setattr(self, "i", 1),
            0xB8: lambda: setattr(self, "v", 0), 0xD8: lambda: setattr(self, "d", 0),
            0xF8: lambda: setattr(self, "d", 1),
            0x88: lambda: setattr(self, "y", self.nz(self.y - 1)),
            0xC8: lambda: setattr(self, "y", self.nz(self.y + 1)),
            0xCA: lambda: setattr(self, "x", self.nz(self.x - 1)),
            0xE8: lambda: setattr(self, "x", self.nz(self.x + 1)),
            0x8A: lambda: setattr(self, "a", self.nz(self.x)),
            0x98: lambda: setattr(self, "a", self.nz(self.y)),
            0xA8: lambda: setattr(self, "y", self.nz(self.a)),
            0xAA: lambda: setattr(self, "x", self.nz(self.a)),
            0x9A: lambda: setattr(self, "sp", self.x),
            0xBA: lambda: setattr(self, "x", self.nz(self.sp)),
            0xEA: lambda: None,
        }
        if op in simple:
            simple[op]()
            return pc + 1

        # --- operand address --------------------------------------------------
        size = 2
        if g == 1:
            if mode == 0:
                ea = zpw(lo + self.x)
            elif mode == 1:
                ea = lo
            elif mode == 2:
                ea = None
            elif mode == 3:
                ea, size = w, 3
            elif mode == 4:
                ea = (zpw(lo) + self.y) & 0xFFFF
            elif mode == 5:
                ea = (lo + self.x) & 0xFF
            elif mode == 6:
                ea, size = (w + self.y) & 0xFFFF, 3
            else:
                ea, size = (w + self.x) & 0xFFFF, 3
            val = lo if ea is None else None
            rd = (lambda: val) if ea is None else (lambda: m[ea])
            if aaa == 0:
                self.a = self.nz(self.a | rd())
            elif aaa == 1:
                self.a = self.nz(self.a & rd())
            elif aaa == 2:
                self.a = self.nz(self.a ^ rd())
            elif aaa == 3:
                self.adc(rd())
            elif aaa == 4:
                m[ea] = self.a
            elif aaa == 5:
                self.a = self.nz(rd())
            elif aaa == 6:
                self.cmp(self.a, rd())
            else:
                self.adc(rd() ^ 0xFF)
            return pc + size
        if g in (0, 2):
            idx = self.y if (g == 2 and aaa in (4, 5)) else self.x
            if mode == 0:
                ea = None
            elif mode == 1:
                ea = lo
            elif mode == 2:
                ea = "acc"
                size = 1
            elif mode == 3:
                ea, size = w, 3
            elif mode == 5:
                ea = (lo + idx) & 0xFF
            elif mode == 7:
                ea, size = (w + idx) & 0xFFFF, 3
            else:
                raise RuntimeError("opcode %02X at %04X" % (op, pc))
            if g == 2 and aaa < 4:          # ASL ROL LSR ROR
                v = self.a if ea == "acc" else m[ea]
                if aaa == 0:
                    self.c, v = v >> 7, v << 1
                elif aaa == 1:
                    self.c, v = v >> 7, v << 1 | self.c
                elif aaa == 2:
                    self.c, v = v & 1, v >> 1
                else:
                    self.c, v = v & 1, v >> 1 | self.c << 7
                v = self.nz(v)
                if ea == "acc":
                    self.a = v
                else:
                    m[ea] = v
                return pc + size
            if g == 2 and aaa in (6, 7) and ea != "acc":   # DEC INC
                m[ea] = self.nz(m[ea] + (1 if aaa == 7 else -1))
                return pc + size
            v = lo if ea is None else (m[ea] if ea != "acc" else None)
            if g == 2 and aaa == 4:
                m[ea] = self.x
            elif g == 2 and aaa == 5:
                self.x = self.nz(v)
            elif g == 0 and aaa == 1:            # BIT
                self.z = int(self.a & v == 0)
                self.n, self.v = v >> 7, v >> 6 & 1
            elif g == 0 and aaa == 4:
                m[ea] = self.y
            elif g == 0 and aaa == 5:
                self.y = self.nz(v)
            elif g == 0 and aaa == 6:
                self.cmp(self.y, v)
            elif g == 0 and aaa == 7:
                self.cmp(self.x, v)
            else:
                raise RuntimeError("opcode %02X at %04X" % (op, pc))
            return pc + size
        raise RuntimeError("opcode %02X at %04X" % (op, pc))

    def cmp(self, r, v):
        t = r - v
        self.c = int(t >= 0)
        self.nz(t)

    def adc(self, v):
        if self.d:
            raise RuntimeError("decimal mode not supported")
        t = self.a + v + self.c
        self.v = int((~(self.a ^ v) & (self.a ^ t) & 0x80) != 0)
        self.c = int(t > 0xFF)
        self.a = self.nz(t)


# ----------------------------------------------------------------------------
# rooms
# ----------------------------------------------------------------------------

def room_map_ptr(r):
    return IMG[ROOM_MAP_LO + r] | IMG[ROOM_MAP_HI + r] << 8


def decode_map(addr):
    """RLE map stream (decoder $0AD5): $80 end, $81-$FF literal run of b&$7F
    cells, $01-$7F repeat the next byte b times.  Returns (cells, end)."""
    p = addr
    cells = []
    while True:
        b = IMG[p]
        if b == 0x80:
            return cells, p
        if b & 0x80:
            n = b & 0x7F
            cells += list(IMG[p + 1:p + 1 + n])
            p += 1 + n
        else:
            cells += [IMG[p + 1]] * (b if b else 256)
            p += 2


def room_charset(r):
    """$0A9B: rooms 0-9 $D018=$38 (set 0), room 18 $3C (set 2), others $3A (set 1)."""
    if r < 10:
        return 0
    if r == 18:
        return 2
    return 1


def room_triplets(r):
    p = w16(ROOM_SPLIT_COLOUR_PTRS + 2 * r)
    raw = [IMG[p + i] for i in range(12)]
    return p, raw, [[raw[3 * k] & 15, raw[3 * k + 1] & 15, raw[3 * k + 2] & 15] for k in range(4)]


def room_raster_lines(r):
    p = w16(ROOM_RASTER_LINE_PTRS + 2 * r)
    lines = []
    while IMG[p + len(lines)] != 0xFD and len(lines) < 4:
        lines.append(IMG[p + len(lines)])
    return p, lines


# The colour split IRQ $4982 waits for raster line L+2 and then writes
# $D021-$D023; the new colours show from raster line L+3 on (checked against
# the screenshots).  Screen pixel row y is raster line y+51 ($33).
SPLIT_DELAY = 3
RASTER_Y0 = 0x33
MAP_Y0 = 24          # map rows start at screen row 3
MAP_ROWS, MAP_COLS = 11, 40


def band_index(lines, y_screen):
    return sum(1 for L in lines if y_screen + RASTER_Y0 >= L + SPLIT_DELAY)


SCREEN = 0x8C00
COLOUR_RAM = 0xD800
REDRAW_TAKEN_LANTERNS = 0x336E   # ends with the RTS dispatch to the room setup handler


def room_state(r):
    """Screen and colour RAM of room r as draw_room ($09BC) leaves them:
    colour RAM filled with the room colour, map decoded from screen row 3,
    then redraw_taken_lanterns + the room setup handler run on a 6502
    interpreter.  Returns (screen[1000], colour[1000], changes, error)."""
    mem = bytearray(IMG)
    for a in range(COLOUR_RAM, COLOUR_RAM + 0x400):
        mem[a] = 0
    for a in range(COLOUR_RAM + 0x78, COLOUR_RAM + 0x400):
        mem[a] = IMG[ROOM_CHAR_COLOURS + r]
    cells, _ = decode_map(room_map_ptr(r))
    for i, v in enumerate(cells):
        R, C = divmod(i, MAP_COLS)
        top = SCREEN + 120 + 80 * R + C
        for a, ch in ((top, v & 0x7F), (top + 40, (v & 0x7F) | 0x80)):
            if a < SCREEN + 1000:           # the 2 extra cells of some rooms land off screen
                mem[a] = ch
                if v & 0x80:
                    mem[a - SCREEN + COLOUR_RAM] = 0xF8
    before_s = bytes(mem[SCREEN:SCREEN + 1000])
    before_c = bytes(mem[COLOUR_RAM:COLOUR_RAM + 1000])
    mem[0x29] = r          # current_room
    mem[0x02] = 0x32       # protection_marker as the running game has it (room 5 init checks it)
    mem[0x03] = 0          # current_player
    err = None
    try:
        CPU6502(mem).call(REDRAW_TAKEN_LANTERNS)
    except RuntimeError as e:
        err = str(e)
        mem[SCREEN:SCREEN + 1000] = before_s
        mem[COLOUR_RAM:COLOUR_RAM + 1000] = before_c
    screen = bytes(mem[SCREEN:SCREEN + 1000])
    colour = bytes(b & 0x0F for b in mem[COLOUR_RAM:COLOUR_RAM + 1000])
    changes = []
    for i in range(120, 1000):
        if screen[i] != before_s[i] or colour[i] != before_c[i] & 15:
            changes.append({"screen_row": i // 40, "column": i % 40,
                            "map_row": (i // 40 - 3) // 2,
                            "char": [hb(before_s[i]), hb(screen[i])],
                            "colour_ram": [before_c[i] & 15, colour[i]]})
    return screen, colour, changes, err


def render_room(r, state=None):
    """320x176 pixels (screen rows 3-24) as C64 colour numbers."""
    screen, colour, _, _ = state or room_state(r)
    src = CHARSET_SRC[room_charset(r)]
    _, _, trip = room_triplets(r)
    _, lines = room_raster_lines(r)
    W, H = 320, MAP_ROWS * 16
    pix = [0] * (W * H)
    for row in range(3, 25):
        for C in range(40):
            ch = screen[40 * row + C]
            cr = colour[40 * row + C]
            base = src + 8 * (ch & 0x7F) + (4 if ch & 0x80 else 0)
            for cy in range(8):
                y = 8 * (row - 3) + cy
                bg, m1, m2 = trip[band_index(lines, y + MAP_Y0)]
                b = IMG[base + cy // 2]
                o = y * W + 8 * C
                if cr & 8:        # multicolour
                    cols = (bg, m1, m2, cr & 7)
                    for p in range(4):
                        k = cols[(b >> (6 - 2 * p)) & 3]
                        pix[o + 2 * p] = pix[o + 2 * p + 1] = k
                else:             # hi-res
                    for p in range(8):
                        pix[o + p] = cr if b >> (7 - p) & 1 else bg
    return W, H, pix


def lantern_list(r):
    """Lantern records.  The row is a text row of print_message's tables
    ($0869 with base $8BD8): screen row 2*row-1, i.e. map row row-2."""
    p = w16(LANTERN_LIST_PTRS + 2 * r)
    cells, _ = decode_map(room_map_ptr(r))
    recs = []
    a = p
    while IMG[a] & 0x80 == 0:
        st, cell, col, row = IMG[a:a + 4]
        rec = {"address": hx(a), "state": st, "present": st != 0,
               "collected_cell": cell, "collected_tile": cell & 0x7F,
               "column": col, "text_row": row, "screen_row": 2 * row - 1, "map_row": row - 2}
        if cell == 0 and col == 0 and row == 0:
            rec["note"] = "placeholder record (room has no lanterns)"
            del rec["screen_row"], rec["map_row"]
        elif 0 <= row - 2 < MAP_ROWS:
            rec["map_cell"] = cells[(row - 2) * MAP_COLS + col]
        recs.append(rec)
        a += 4
    return p, a, recs


def extract_rooms():
    rooms_meta = []
    renders = {}
    states = {}
    for r in range(NROOMS):
        mp = room_map_ptr(r)
        cells, end = decode_map(mp)
        cs = room_charset(r)
        tp, traw, trip = room_triplets(r)
        lp, lines = room_raster_lines(r)
        cr = IMG[ROOM_CHAR_COLOURS + r]
        state = room_state(r)
        states[r] = state
        W, H, pix = render_room(r, state)
        renders[r] = (W, H, pix)
        write_png("rooms/room%02d.png" % r, W, H, pix)

        grid = [cells[R * 40:(R + 1) * 40] for R in range(MAP_ROWS)]
        extra = cells[MAP_ROWS * MAP_COLS:]
        bands = []
        for k in range(len(lines) + 1):
            ys = [y for y in range(H) if band_index(lines, y + MAP_Y0) == k]
            if ys:
                bands.append({"triplet": k, "colours": trip[k], "y_first": ys[0], "y_last": ys[-1]})

        exits = {}
        for code, (td, tx, ty) in sorted(EXIT_TABLES.items()):
            g = code
            while g < 5 and IMG[EXIT_TABLES[g][1] + r] == 0:
                g += 1
            gd, gx, gy = EXIT_TABLES[g]
            trig = [[i // 40, i % 40] for i, v in enumerate(cells[:440]) if v & 0x7F == code]
            exits[str(code)] = {
                "table": {"dest_room": IMG[td + r], "x": IMG[tx + r], "y": IMG[ty + r],
                          "names": [tname(td), tname(tx), tname(ty)]},
                "defined": IMG[tx + r] != 0,
                "effective_group": g,
                "dest_room": IMG[gd + r], "entry_x": IMG[gx + r], "entry_y": IMG[gy + r],
                "trigger_cells": trig,
            }
        llp, lle, lrecs = lantern_list(r)
        meta = {
            "room": r,
            "map": {"name": nm(mp, "room%02d_map" % r), "address": hx(mp),
                    "end_marker": hx(end), "bytes": end + 1 - mp,
                    "cells_encoded": len(cells),
                    "note": "cells beyond 440 are written past the visible screen (bug of the original)" if extra else None},
            "cells_hex": [" ".join("%02x" % v for v in row) for row in grid],
            "cells": grid,
            "cells_beyond_map": extra,
            "cell_format": "bits 0-6 tile (top char = tile, bottom char = tile|$80), bit 7 = colour RAM $F8 (colour-3 pixels black)",
            "charset": {"set": cs, "source": hx(CHARSET_SRC[cs]), "expanded": hx(CHARSET_EXP[cs]),
                        "d018": hb(CHARSET_D018[cs])},
            "colours": {
                "colour_ram": hb(cr), "colour3": cr & 7, "colour3_name": COLOUR_NAMES[cr & 7],
                "split_colours_ptr": hx(tp), "triplets_raw": [hb(b) for b in traw],
                "triplets": [{"d021": t[0], "d022": t[1], "d023": t[2]} for t in trip],
                "raster_lines_ptr": hx(lp), "raster_lines": [hb(L) for L in lines],
                "bands_in_png": bands,
            },
            "exits": exits,
            "spawn": {"x": IMG[ROOM_SPAWN_X + r], "y": IMG[ROOM_SPAWN_Y + r],
                      "alt_enemy_x": IMG[ROOM_ALT_SPAWN_X + r], "alt_enemy_y": IMG[ROOM_ALT_SPAWN_Y + r],
                      "coordinates": "x in multicolour pixels (sprite X = 2*x), y = raster line - $1D"},
            "no_combat_flag": IMG[ROOM_NO_COMBAT + r],
            "enemy_spawn": {tname(a): IMG[a + r] for a in ENEMY_DELAY_TABLES},
            "lanterns": {"count": IMG[ROOM_LANTERN_COUNTS + r], "list": hx(llp), "list_end": hx(lle),
                         "records": lrecs},
            "handlers": {"setup": hx(w16(ROOM_SETUP_HANDLERS + 2 * r) + 1),
                         "frame": hx(w16(ROOM_FRAME_HANDLERS + 2 * r) + 1)},
            "setup_changes": {
                "note": "screen/colour RAM cells that redraw_taken_lanterns and the room setup handler "
                        "change after the map is drawn (run on a 6502 interpreter); included in roomNN.png",
                "error": state[3],
                "cells": state[2]},
        }
        if state[3] is None:
            del meta["setup_changes"]["error"]
        if meta["map"]["note"] is None:
            del meta["map"]["note"]
        write_json("rooms/room%02d.json" % r, meta)
        rooms_meta.append(meta)
    return renders, states


# ----------------------------------------------------------------------------
# charsets
# ----------------------------------------------------------------------------

# Sheets use palette index = bit pair (0-3), so a sheet can be re-imported.
TILE_PALETTE = [PALETTE[0], PALETTE[15], PALETTE[12], PALETTE[7]]


def mc_tile(addr, rows_per_src=2, nrows=8):
    """Multicolour char rows -> list of rows of 8 bit-pair values (double width)."""
    out = []
    for r in range(nrows * rows_per_src):
        b = IMG[addr + r // rows_per_src]
        row = []
        for p in range(4):
            v = (b >> (6 - 2 * p)) & 3
            row += [v, v]
        out.append(row)
    return out


def extract_charsets():
    for s, src in enumerate(CHARSET_SRC):
        W, H = 16 * 8, 8 * 16
        pix = [0] * (W * H)
        for c in range(128):
            ox, oy = (c % 16) * 8, (c // 16) * 16
            for y, row in enumerate(mc_tile(src + 8 * c)):
                for x, v in enumerate(row):
                    pix[(oy + y) * W + ox + x] = v
        write_png("charsets/charset_%d.png" % s, W, H, pix, TILE_PALETTE)
        write_bin("charsets/charset_%d.bin" % s, IMG[src:src + 0x400])


def extract_title_font():
    # 128 chars $80-$FF of the title charset at $8000, 4x8 multicolour.
    W, H = 16 * 8, 8 * 8
    pix = [0] * (W * H)
    for c in range(128):
        ox, oy = (c % 16) * 8, (c // 16) * 8
        for y, row in enumerate(mc_tile(TITLE_FONT + 8 * c, 1, 8)):
            for x, v in enumerate(row):
                pix[(oy + y) * W + ox + x] = v
    write_png("fonts/title_font.png", W, H, pix, TILE_PALETTE)
    write_bin("fonts/title_font.bin", IMG[TITLE_FONT:TITLE_FONT + 0x400])

    # Title text rows as the title screen shows them ($0584): screen filled with
    # $DC, rows 2/5/6/9 from the row tables ORed with $80, BGCOL0 6, BGCOL1/2 15,
    # colour RAM $FF (multicolour, colour 7).
    rows = {2: 0x4A0D, 5: 0x49BD, 6: 0x49E5, 9: 0x4A35}
    screen = [[0xDC] * 40 for _ in range(11)]
    for row, a in rows.items():
        screen[row] = [IMG[a + i] | 0x80 for i in range(40)]
    cols = (6, 15, 15, 7)
    W, H = 320, 11 * 8
    pix = [6] * (W * H)
    for row in range(11):
        for col in range(40):
            ch = screen[row][col]
            for y, line in enumerate(mc_tile(0x8000 + 8 * ch, 1, 8)):
                for x, v in enumerate(line):
                    pix[(row * 8 + y) * W + col * 8 + x] = cols[v]
    # TM sprite: sprite 0 at X=$10A, Y=$56, X-expanded, colour 15.
    tm = tm_sprite_block()
    sx, sy = 0x10A - 24, 0x56 - 50
    for y in range(21):
        for x in range(24):
            if tm[3 * y + x // 8] >> (7 - x % 8) & 1:
                for dx in (0, 1):
                    px, py = sx + 2 * x + dx, sy + y
                    if 0 <= px < W and 0 <= py < H:
                        pix[py * W + px] = 15
    write_png("fonts/title_layout.png", W, H, pix)
    banner = {
        "player_banner_top": {"address": hx(0x4A5D), "codes": list(IMG[0x4A5D:0x4A6D])},
        "player_banner_bottom": {"address": hx(0x4A6D), "codes": list(IMG[0x4A6D:0x4A7D])},
        "player_digit_top": {"address": hx(0x4A7D), "codes": list(IMG[0x4A7D:0x4A81]),
                             "note": "2 bytes per player, patched into $4A6B"},
        "player_digit_bottom": {"address": hx(0x4A81), "codes": list(IMG[0x4A81:0x4A85]),
                                "note": "2 bytes per player, patched into $4A7B"},
    }
    write_json("fonts/title_layout.json", {
        "charset": "title_font $8400-$87FF = chars $80-$FF of the VIC charset at $8000 ($D018=$30), multicolour",
        "glyph_rule": "single-height letter = chars n, n+1 side by side; double-height letter = n (top left), n+2 (top right), n+1 (bottom left), n+3 (bottom right)",
        "fill_code": hb(0xDC),
        "colours": {"d021": 6, "d022": 15, "d023": 15, "colour_ram": hb(0xFF)},
        "rows": [{"screen_row": row, "name": nm(a, "title_row_%04x" % a), "address": hx(a),
                  "codes": [IMG[a + i] for i in range(40)],
                  "screen_codes": [IMG[a + i] | 0x80 for i in range(40)]}
                 for row, a in sorted(rows.items())],
        "player_banner": banner,
        "tm_sprite": "sprite 0, block $83C0, X=$10A, Y=$56, X-expanded, colour 15 (see sprites/tm_sprite.png)",
    })


# ----------------------------------------------------------------------------
# sprites
# ----------------------------------------------------------------------------

ACTORS = [("bruce", "Bruce Lee", 0), ("yamo", "Yamo", 70), ("ninja", "Ninja", 140)]
OVERLAY_SHIFT_REL = (0x05, 0x19, 0x3F, 0x43)   # $2636: overlay moves 16 px left


def frame_rows(f):
    src = IMG[FRAME_SRC_LO + f] | IMG[FRAME_SRC_HI + f] << 8
    h = IMG[FRAME_HEIGHT + f]
    if src == 0:
        return []
    if IMG[FRAME_WIDE + f] == 0:
        return [[IMG[src + r]] for r in range(h + 1)]
    return [[IMG[src + 2 * r], IMG[src + 2 * r + 1]] for r in range(h)]


def frame_colour(f):
    if f >= 140:
        return 0   # actor slot 2 (Ninja) forced to $F0 at $2734
    return IMG[FRAME_COLOUR + f] & 15


def frame_pixels(f):
    """Set of (x, y) hi-res pixels, X-expanded (2 screen px per bit)."""
    s = set()
    for y, row in enumerate(frame_rows(f)):
        for bi, b in enumerate(row):
            for bit in range(8):
                if b >> (7 - bit) & 1:
                    x = 2 * (8 * bi + bit)
                    s.add((x, y))
                    s.add((x + 1, y))
    return s


def compose(base, rel):
    """Pair (rel, rel+1) of one actor as $2584/$25F5/$2636 show it.
    Returns (layers, facing): layers = [(frame, dx, colour, pixels)] back to front."""
    fa, fb = base + rel, base + rel + 1
    a_wide = IMG[FRAME_WIDE + fa] != 0
    b_used = base != 140 and (IMG[FRAME_SRC_LO + fb] | IMG[FRAME_SRC_HI + fb] << 8) != 0
    b_shift = -16 if (rel + 1) in OVERLAY_SHIFT_REL else 0
    pa = frame_pixels(fa)
    pb = frame_pixels(fb) if b_used else set()
    facing = None
    a_shift = 0
    if a_wide and pb:
        # The body moves 16 px left when facing != 1, and the facing is not
        # stored with the frame.  Take the placement where the overlay pixels
        # touch the body best (the two layers are drawn to fit together; on
        # every wide pair this gives "left" exactly when the overlay is one of
        # the shifted frames).
        def score(sh):
            body = {(x + sh, y) for x, y in pa}
            return sum(1 for x, y in pb if any((x + b_shift + dx, y + dy) in body
                                               for dx in (-2, 0, 2) for dy in (-1, 0, 1)))
        if score(-16) > score(0):
            facing, a_shift = "left", -16
        else:
            facing = "right"
    elif a_wide:
        facing = "unknown (no overlay; drawn unshifted)"
    layers = []
    if b_used:
        layers.append((fb, b_shift, frame_colour(fb), pb))
    layers.append((fa, a_shift, frame_colour(fa), pa))   # lower sprite number = in front
    return layers, facing


def tm_sprite_block():
    blk = [0] * 63
    for i in range(12):
        blk[12 + i] = IMG[TM_SPRITE_ROWS + i]
    return blk


def extract_sprites():
    frames = []
    for f in range(210):
        actor = ACTORS[f // 70]
        src = IMG[FRAME_SRC_LO + f] | IMG[FRAME_SRC_HI + f] << 8
        h = IMG[FRAME_HEIGHT + f]
        wide = IMG[FRAME_WIDE + f]
        rows = frame_rows(f)
        mask = IMG[FRAME_MASK_LO + f] | IMG[FRAME_MASK_HI + f] << 8
        frames.append({
            "frame": f, "actor": actor[0], "relative_frame": f % 70,
            "layer": "A (body)" if f % 2 == 0 else "B (overlay)",
            "source": hx(src) if src else None,
            "source_end": hx(src + len(rows) * len(rows[0]) - 1) if rows else None,
            "height_value": h, "rows": len(rows),
            "wide_flag": wide, "wide": wide != 0, "width_px": 16 if wide else 8,
            "colour_byte": hb(IMG[FRAME_COLOUR + f]) if f < 140 else None,
            "colour": frame_colour(f) if rows else None,
            "colour_note": "Ninja frames are drawn in $F0 (black) by $2734; the table read runs into frame_wide_flag" if f >= 140 else None,
            "mask_address": hx(mask) if mask >> 8 else None,
            "data_hex": [hexbytes(r) for r in rows],
        })
        for k in ("colour_byte", "colour_note"):
            if frames[-1][k] is None:
                del frames[-1][k]

    for key, title, base in ACTORS:
        # section 1: 35 composed pairs, 7 columns x 5 rows, cells 52x25
        CW, CH, NC = 52, 25, 7
        # section 2: 70 single frames, 10 columns x 7 rows, cells 36x25
        SW, SH, SC = 36, 25, 10
        W = max(NC * CW, SC * SW) + 4
        top = 5 * CH + 6
        H = top + 7 * SH + 2
        pix = [16] * (W * H)

        def put(x, y, c):
            if 0 <= x < W and 0 <= y < H:
                pix[y * W + x] = c
        # separator line between the sections
        for x in range(W):
            put(x, top - 3, 11)
        for n, rel in enumerate(range(0, 70, 2)):
            ox = 2 + (n % NC) * CW + 16
            oy = 2 + (n // NC) * CH
            layers, facing = compose(base, rel)
            for f, dx, colour, pxs in layers:
                for x, y in pxs:
                    put(ox + dx + x, oy + y, colour)
            entry = frames[base + rel]
            entry["sheet_pair_cell"] = {"x": ox - 16, "y": oy, "w": 48, "h": 21, "origin_x": ox}
            entry["pair_facing_assumed"] = facing
            entry["pair_offsets"] = {"A": layers[-1][1], "B": layers[0][1] if len(layers) > 1 else None}
        for rel in range(70):
            f = base + rel
            ox = 2 + (rel % SC) * SW
            oy = top + (rel // SC) * SH
            colour = frame_colour(f)
            for x, y in frame_pixels(f):
                put(ox + x, oy + y, colour)
            frames[f]["sheet_frame_cell"] = {"x": ox, "y": oy, "w": 32, "h": 21}
        write_png("sprites/%s.png" % key, W, H, pix, PALETTE + [SHEET_BG])

    write_json("sprites/frames.json", {
        "tables": {k: hx(a) for k, a in (
            (tname(FRAME_SRC_LO), FRAME_SRC_LO), (tname(FRAME_SRC_HI), FRAME_SRC_HI),
            (tname(FRAME_HEIGHT), FRAME_HEIGHT), (tname(FRAME_COLOUR), FRAME_COLOUR),
            (tname(FRAME_WIDE), FRAME_WIDE), (tname(FRAME_MASK_LO), FRAME_MASK_LO),
            (tname(FRAME_MASK_HI), FRAME_MASK_HI))},
        "graphics": "$5D91-$68F8 (frames overlap; $63C1-$63EA unreferenced)",
        "layout": "narrow: height_value+1 rows of 1 byte; wide: height_value rows of 2 bytes (left, right). "
                  "Bit 7 = leftmost pixel, set = sprite colour. Hi-res sprites, X-expanded (2 screen px per bit), "
                  "rows start at sprite row 0.",
        "actors": [{"actor": k, "name": t, "frames": "%d-%d" % (b, b + 69),
                    "type_base_table": hx(ACTOR_TYPE_BASE),
                    "vic_sprite_a": IMG[ACTOR_SPRITE_A + i], "vic_sprite_b": None if i == 1 else IMG[ACTOR_SPRITE_B + i]}
                   for i, (k, t, b) in enumerate([("bruce", "Bruce Lee", 0), ("ninja", "Ninja", 140), ("yamo", "Yamo", 70)])],
        "sheet": "sprites/<actor>.png: top = 35 displayed pairs (A even frame + B overlay frame), "
                 "7 per row, 52x25 cells, pair origin 16 px in from the cell's left edge; "
                 "bottom = the 70 single frames, 10 per row, 36x25 cells. Palette index 16 = sheet background.",
        "frames": frames,
    })

    # TM sprite (title): 63-byte block as built at $83C0 by $05D1
    tm = tm_sprite_block()
    write_bin("sprites/tm_sprite.bin", tm)
    W, H = 48, 21
    pix = [16] * (W * H)
    for y in range(21):
        for x in range(24):
            if tm[3 * y + x // 8] >> (7 - x % 8) & 1:
                pix[y * W + 2 * x] = pix[y * W + 2 * x + 1] = 15
    write_png("sprites/tm_sprite.png", W, H, pix, PALETTE + [SHEET_BG])


# ----------------------------------------------------------------------------
# texts
# ----------------------------------------------------------------------------

def read_until(a, end=0xA0, limit=256):
    out = []
    while IMG[a + len(out)] != end and len(out) < limit:
        out.append(IMG[a + len(out)])
    return out


def is_text_region(a, data):
    if K and K.loaded:
        r = K.region_at(a)
        if r is not None:
            return r["type"] == "petscii"
    return all(0x20 <= b < 0x60 for b in data)


# Text charset at $8800 (built at $044C): chars 0-31 = ROM $20-$3F, 32-63 =
# ROM $00-$1F (so char c shows ASCII c+$20), 64-127 = the same inverted.
# Patched at $0471: char $20 solid block, $42 right bar, $56 left bar.
TEXT_PATCHED = {0x20: "\u2588", 0x42: "\u2590", 0x56: "\u258c"}


def screen_text(codes):
    """Codes of the text charset -> (text, inverse mask or None)."""
    out, inv = [], []
    for c in codes:
        c &= 0x7F
        out.append(TEXT_PATCHED.get(c, chr((c & 63) + 0x20)))
        inv.append("#" if c >= 64 and c not in TEXT_PATCHED else ".")
    inv = "".join(inv)
    return "".join(out), (inv if "#" in inv else None)


def message_text(data):
    return screen_text([(b - 0x20) & 0x7F for b in data])


def extract_texts():
    msgs = []
    for i in range(NMESSAGES):
        a = w16(MESSAGE_POINTERS + 2 * i)
        data = read_until(a)
        e = {"index": i, "address": hx(a), "label": K.label(a) if K else None,
             "length": len(data)}
        if is_text_region(a, data):
            e["kind"] = "text"
            e["text"], inv = message_text(data)
            if inv:
                e["inverse"] = inv
        else:
            e["kind"] = "tiles"
            e["raw"] = [hb(b) for b in data]
            e["chars_top"] = [hb((b - 0x20) & 0x7F) for b in data]
            e["chars_bottom"] = [hb(((b - 0x20) & 0x7F) | 0x80) for b in data]
        if e["label"] is None:
            del e["label"]
        msgs.append(e)

    def strings(a, n):
        out = []
        for _ in range(n):
            d = read_until(a)
            out.append({"address": hx(a), "text": message_text(d)[0]})
            a += len(d) + 1
        return out

    version = [IMG[0x4707 + i] for i in range(40)]
    left = []
    a, end = 0x5900, 0x59A4
    for b in IMG[a:end + 1]:
        left.append(b & 0x7F)
    leftover_text = "".join("\n" if b == 0x0D else (chr(b) if 0x20 <= b < 0x7F else "\\x%02x" % b) for b in left)

    write_json("text/messages.json", {
        "message_pointers": {"name": tname(MESSAGE_POINTERS), "address": hx(MESSAGE_POINTERS),
                             "entries": NMESSAGES},
        "printer": "print_message $17E2: bytes until $A0; each byte b is drawn as screen code (b-$20)&$7F "
                   "(top) and that |$80 (bottom) at text row X = screen rows 2X-1/2X. Text messages use the text "
                   "charset $8800 (ASCII $20-$5F, +$40 = inverse; \u2588 \u2590 \u258c are the patched block/bar "
                   "chars); tile messages are room tile codes +$20.",
        "messages": msgs,
        "version_text": {"name": nm(0x4707, "version_text"), "address": "$4707-$472E",
                         "codes": [hb(b) for b in version],
                         "text": screen_text(version)[0],
                         "note": "40 codes = ASCII-$20, copied to the screen by the V key ($1B71)"},
        "unreferenced": [
            {"name": nm(0x4563, "credits_text_unused"), "address": "$4563-$457D",
             "strings": strings(0x4563, 3), "note": "no message pointer, no code reads it"},
            {"name": nm(0x4598, "game_over_text_unused"), "address": "$4598-$45A9",
             "strings": strings(0x4598, 2), "note": "no message pointer, no code reads it"},
            {"name": nm(0x4770, "msg_diabolo_presents"), "address": "$4770-$4781",
             "strings": strings(0x4770, 1), "note": "message 98; no code prints it"},
        ],
        "leftovers": [
            {"name": nm(0x5900, "leftover_source_text"), "address": "$5900-$59A4",
             "leftover": True, "encoding": "ASCII with bit 7 set, $8D = new line",
             "text": leftover_text,
             "note": "Apple II Merlin assembler source text, not game data"},
        ],
    })


# ----------------------------------------------------------------------------
# tables
# ----------------------------------------------------------------------------

def find_irq_chain():
    """Every LDA #<h / STA $0408 / LDA #>h / STA $0409 in the image."""
    setters = []
    for a in range(0x0400, 0xFFF0):
        if (IMG[a] == 0xA9 and IMG[a + 2:a + 5] == b"\x8d\x08\x04" and IMG[a + 5] == 0xA9
                and IMG[a + 7:a + 10] == b"\x8d\x09\x04"):
            target = IMG[a + 1] | IMG[a + 6] << 8
            raster = None
            for b in range(a + 10, a + 40):
                if IMG[b] == 0xA9 and IMG[b + 2:b + 5] == b"\x8d\x12\xd0":
                    raster = IMG[b + 1]
                    break
                if IMG[b] in (0x60, 0x4C, 0x40):
                    break
            setters.append((a, target, raster))
    handlers = sorted({t for _, t, _ in setters})
    return setters, handlers


def decode_region(r):
    s, e, t = r["s"], r["e"], r["type"]
    entries = []
    if t in ("addresses", "rts-addresses", "words"):
        for i in range((e - s + 1) // 2):
            v = w16(s + 2 * i)
            tgt = v + 1 if t == "rts-addresses" else v
            ent = {"index": i, "at": hx(s + 2 * i), "value": hx(v), "target": hx(tgt)}
            lab = K.label(tgt)
            if lab:
                ent["target_name"] = lab
            entries.append(ent)
    elif t == "addresses-split":
        n = (e - s + 1) // 2
        for i in range(n):
            v = IMG[s + i] | IMG[s + n + i] << 8
            ent = {"index": i, "value": hx(v)}
            lab = K.label(v)
            if lab:
                ent["target_name"] = lab
            entries.append(ent)
    elif t == "jumps":
        a = s
        i = 0
        while a <= e:
            op = IMG[a]
            if op in (0x4C, 0x6C, 0x20):
                v = w16(a + 1)
                ent = {"index": i, "at": hx(a), "op": {0x4C: "JMP", 0x6C: "JMP ()", 0x20: "JSR"}[op],
                       "target": hx(v)}
                lab = K.label(v)
                if lab:
                    ent["target_name"] = lab
                entries.append(ent)
                a += 3
            else:
                entries.append({"index": i, "at": hx(a), "raw": hb(op)})
                a += 1
            i += 1
    out = {"name": K.name(s), "start": hx(s), "end": hx(e), "type": t, "entries": entries}
    if t == "addresses-split":
        out["lo"] = hx(s)
        out["hi"] = hx(s + (e - s + 1) // 2)
    c = K.comment(s)
    if c:
        out["comment"] = c
    return out


def room_table(a, label=None, fmt=None):
    vals = table20(a)
    return {"name": tname(a), "address": hx(a), "end": hx(a + NROOMS - 1),
            "values": vals if fmt is None else [fmt(v) for v in vals]}


def extract_tables():
    # --- jump and dispatch tables --------------------------------------------
    def handler_table(a):
        ents = []
        for r in range(NROOMS):
            v = w16(a + 2 * r)
            ents.append({"room": r, "value": hx(v), "target": hx(v + 1),
                         "target_name": (K.label(v + 1) if K else None)})
        return {"name": tname(a), "address": hx(a), "kind": "rts-addresses (value = target-1)",
                "entries": ents}

    setters, handlers = find_irq_chain()
    irq = {
        "vector": {"address": "$FFFE", "target": hx(w16(0xFFFE)), "target_name": K.label(w16(0xFFFE)) if K else None,
                   "note": "irq_handler jumps through irq_chain_vector ($0408/$0409)"},
        "chain_vector": "$0408",
        "handlers": [{"address": hx(h), "name": K.label(h) if K else None,
                      "comment": K.comment(h) if K else None} for h in handlers],
        "settings": [],
        "game_chain": "irq_frame_top $48C1 (raster $FD) -> irq_playfield_top $491E (raster $40) -> "
                      "irq_colour_split $4982 once per raster_lines entry -> irq_frame_top",
    }
    for a, t, rl in setters:
        e = {"at": hx(a), "in": K.label(a) if K else None, "next_handler": hx(t),
             "next_name": K.label(t) if K else None,
             "raster_line": hb(rl) if rl is not None else "from the room's raster list ($47F5)"}
        reg = K.region_at(a) if K and K.loaded else None
        if reg is not None and reg["type"] != "code":
            e["note"] = "inside a %s region: not executed (leftover copy of $482C-$492A)" % reg["type"] \
                if 0x4FE8 <= a <= 0x50E6 else "inside a %s region" % reg["type"]
        irq["settings"].append(e)
    write_json("tables/room_handlers.json", {
        "setup": handler_table(ROOM_SETUP_HANDLERS),
        "frame": handler_table(ROOM_FRAME_HANDLERS),
    })
    write_json("tables/irq_chain.json", irq)
    generic = []
    if K and K.loaded:
        for r in K.regions:
            if r["type"] in ("addresses", "rts-addresses", "jumps", "addresses-split", "words"):
                generic.append(decode_region(r))
    write_json("tables/jump_tables.json", {
        "source": "every region of type addresses, rts-addresses, jumps, addresses-split and words in the knowledge export",
        "regions": generic,
    })

    # --- room tables ----------------------------------------------------------
    pool_lo, pool_hi = 0x47C8, 0x47F4
    split_ptrs = []
    for r in range(NROOMS):
        p, raw, trip = room_triplets(r)
        lp, lines = room_raster_lines(r)
        split_ptrs.append({"room": r, "colours_ptr": hx(p), "triplets": trip,
                           "raster_lines_ptr": hx(lp), "raster_lines": [hb(L) for L in lines]})
    atari = []
    for r in range(NROOMS):
        p = w16(ROOM_ATARI_COLOUR_PTRS + 2 * r)
        atari.append({"room": r, "ptr": hx(p), "bytes": hexbytes(IMG[p:p + 20])})
    exits = {}
    for code, (td, tx, ty) in sorted(EXIT_TABLES.items()):
        exits["exit%d" % code] = {"dest_room": room_table(td), "x": room_table(tx), "y": room_table(ty)}
    write_json("tables/room_tables.json", {
        "char_colours": room_table(ROOM_CHAR_COLOURS, fmt=hb),
        "band_colours": {"name": tname(0x47C8), "address": "$47C8-$47F4",
                         "bytes": hexbytes(IMG[pool_lo:pool_hi + 1]),
                         "note": "pool of $D021/$D022/$D023 triplets; rooms point into it (shared, overlapping)"},
        "raster_split_lists": {"name": tname(0x47F9), "address": "$47F9-$480A",
                               "bytes": hexbytes(IMG[0x47F9:0x480B]), "terminator": "$FD"},
        "split_colour_ptrs": {"name": tname(ROOM_SPLIT_COLOUR_PTRS), "address": hx(ROOM_SPLIT_COLOUR_PTRS)},
        "raster_line_ptrs": {"name": tname(ROOM_RASTER_LINE_PTRS), "address": hx(ROOM_RASTER_LINE_PTRS)},
        "per_room_splits": split_ptrs,
        "map_ptrs": {"lo": tname(ROOM_MAP_LO), "hi": tname(ROOM_MAP_HI),
                     "address": "$4B34/$4B49 (21 entries; 20 duplicates 19)",
                     "values": [hx(room_map_ptr(r)) for r in range(21)]},
        "exits": exits,
        "exit_rule": "touching tile 2/3/4/5 uses that exit group; x = 0 falls through to the next group",
        "spawn": {"x": room_table(ROOM_SPAWN_X), "y": room_table(ROOM_SPAWN_Y),
                  "alt_enemy_x": room_table(ROOM_ALT_SPAWN_X), "alt_enemy_y": room_table(ROOM_ALT_SPAWN_Y)},
        "no_combat_flags": room_table(ROOM_NO_COMBAT),
        "lantern_counts": room_table(ROOM_LANTERN_COUNTS),
        "lantern_list_ptrs": {"name": tname(LANTERN_LIST_PTRS), "address": hx(LANTERN_LIST_PTRS),
                              "values": [hx(w16(LANTERN_LIST_PTRS + 2 * r)) for r in range(21)]},
        "enemy_spawn_delays": [room_table(a) for a in ENEMY_DELAY_TABLES],
        "atari_colour_records": {"name": tname(ROOM_ATARI_COLOUR_PTRS), "address": hx(ROOM_ATARI_COLOUR_PTRS),
                                 "leftover": True,
                                 "note": "copied to $0153-$0166 at $0A87, overwritten by the IRQ every frame; Atari 8-bit colour values",
                                 "rooms": atari},
    })

    # --- actor frame mask address tables -------------------------------------
    ents = []
    for f in range(210):
        v = IMG[FRAME_MASK_LO + f] | IMG[FRAME_MASK_HI + f] << 8
        ents.append({"frame": f, "address": hx(v), "none": (v >> 8) == 0})
    write_json("tables/actor_frame_addr.json", {
        "lo": {"name": tname(FRAME_MASK_LO), "address": "$1167-$1238"},
        "hi": {"name": tname(FRAME_MASK_HI), "address": "$1239-$130A"},
        "comment": (K.comment(FRAME_MASK_LO) if K else None) or
                   "96-byte collision masks built at init by $512F; odd entries name the overlay frame",
        "entries": ents,
    })


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
LEN_TABLE = 0xE6F9


def note_name(n):
    if n == 0:
        return "rest"
    if n > 82:
        return "beyond table"
    return "%s%d" % (NOTE_NAMES[(n - 1) % 12], (n - 1) // 12 + 1)


def leading_table_sel(ptrs):
    """$E38C reads the commands before the first note of every voice at tune
    start; the length-table select ($E2E7) they set is global."""
    sel = 0
    for a in ptrs:
        while IMG[a] >= 0x80 and IMG[a] != 0xFF:
            b = IMG[a]
            if 0xAC <= b <= 0xAF:
                sel = b & 1
            a += {0xC: 3, 0xD: 2, 0xE: 2}.get(b >> 4, 1)
    return sel


def decode_voice(a, table_sel=0):
    events = []
    length = 0
    tempo = None
    t = 0
    while True:
        b = IMG[a]
        ev = {"address": hx(a)}
        size = 1
        if b < 0x80:
            ticks = IMG[LEN_TABLE + length + 16 * table_sel]
            ev.update({"type": "rest" if b == 0 else "note", "note": b, "name": note_name(b),
                       "length_index": length, "ticks": ticks, "tick_start": t})
            t += ticks
        elif b == 0xFF:
            ev.update({"type": "end"})
            ev["bytes"] = hexbytes([b])
            events.append(ev)
            return events, a, t
        else:
            hi, lo = b >> 4, b & 15
            if hi == 0x8 or hi == 0xF:
                length = lo
                ev.update({"type": "length", "index": lo})
            elif hi == 0x9:
                ev.update({"type": "volume", "value": lo})
            elif hi == 0xA:
                names = {0: "waveform triangle", 1: "waveform saw", 2: "waveform pulse", 3: "waveform noise",
                         4: "articulation 0 (gate 7/8)", 5: "articulation 1 (gate 1/2)",
                         6: "articulation 2 (gate length-1)", 7: "tie on", 8: "tie off",
                         9: "ring modulation on", 10: "ring modulation off", 11: "waveform pulse+triangle",
                         12: "short length table", 13: "long length table", 14: "short length table",
                         15: "long length table"}
                if lo >= 12:
                    table_sel = lo & 1
                ev.update({"type": "control", "what": names[lo]})
            elif hi == 0xB:
                ev.update({"type": "instrument", "value": lo, "adsr_source": hx(0xE80A + 8 * lo)})
            elif hi == 0xC:
                pw = IMG[a + 1] | IMG[a + 2] << 8
                ev.update({"type": "pulse_width", "value": pw})
                size = 3
            elif hi == 0xD:
                ev.update({"type": "filter", "preset": lo, "resonance_or": IMG[a + 1]})
                size = 2
            elif hi == 0xE:
                tempo = IMG[a + 1]
                ev.update({"type": "tempo", "frames_per_tick": tempo})
                size = 2
        ev["bytes"] = hexbytes(IMG[a:a + size])
        events.append(ev)
        a += size


SFX_SIZES = {0: 1, 1: 3, 2: 4, 3: 5, 4: 6, 5: 5, 6: 5, 7: 2}
SFX_TABLE = 0xEBE5
SFX_ADSR = 0xEC11
SFX_PULSE = 0xEC1B
SFX_CALLERS_FALLBACK = {0: ["$1FCB"], 1: ["$225F", "$3656", "$36DF"], 2: ["$10BC"], 3: [],
                        4: ["$205A", "$209F"], 5: ["$227C", "$22D2"], 6: ["$2E30"], 7: ["$2A93"],
                        8: [], 9: ["$407A"], 10: ["$4256"], 11: ["$3E0D"], 12: ["$3059"],
                        13: ["$32D3"], 14: ["$2FEC"]}


def control_desc(c):
    w = [n for bit, n in ((0x10, "triangle"), (0x20, "saw"), (0x40, "pulse"), (0x80, "noise")) if c & bit]
    f = [n for bit, n in ((1, "gate"), (2, "sync"), (4, "ring"), (8, "test")) if c & bit]
    return "+".join(w + f) or "off"


def decode_sfx(a):
    recs = []
    while True:
        op = IMG[a]
        if op > 7:
            recs.append({"address": hx(a), "error": "unknown opcode", "bytes": hexbytes([op])})
            return recs, a
        n = SFX_SIZES[op]
        b = IMG[a:a + n]
        r = {"address": hx(a), "op": op, "bytes": hexbytes(b)}
        if op == 0:
            r["what"] = "end"
        elif op == 7:
            r.update({"control": hb(b[1]), "control_desc": control_desc(b[1])})
        else:
            r.update({"wait": b[1], "note": b[2], "note_name": note_name(b[2])})
            if b[2] > 82:
                r["note_note"] = "index past the frequency table: near-zero frequency"
            if op == 2:
                r["control"] = b[3]
            elif op == 3:
                r.update({"adsr_offset": b[3], "control": b[4]})
            elif op == 4:
                r.update({"adsr_offset": b[3], "pulse_offset": b[4], "control": b[5]})
            elif op in (5, 6):
                r.update({"pulse_offset": b[3], "control": b[4]})
            if "adsr_offset" in r:
                o = r["adsr_offset"]
                r["ad"], r["sr"] = hb(IMG[SFX_ADSR + o]), hb(IMG[SFX_ADSR + o + 1])
            if "pulse_offset" in r:
                o = r["pulse_offset"]
                r["pulse_width"] = (IMG[SFX_PULSE + o] | IMG[SFX_PULSE + o + 1] << 8) & 0xFFF
            if "control" in r:
                c = r["control"]
                r["control"] = hb(c)
                r["control_desc"] = control_desc(c)
        recs.append(r)
        if op == 0:
            return recs, a
        a += n


def sfx_callers(i, addr):
    if K and K.loaded:
        c = K.comment(addr) or ""
        if "no code requests" in c:
            return []
        m = re.search(r"requested at ([^;.]*)", c)
        if m:
            return re.findall(r"\$[0-9A-Fa-f]{4}", m.group(1))
    return SFX_CALLERS_FALLBACK[i]


def extract_sound():
    tt = 0xE8C0
    voices = []
    sel = leading_table_sel([w16(tt + 2 * v) for v in range(3)])
    for v in range(3):
        p = w16(tt + 2 * v)
        ev, end, ticks = decode_voice(p, sel)
        voices.append({"voice": v + 1, "name": nm(p, "tune0_voice%d" % (v + 1)), "start": hx(p),
                       "end": hx(end), "total_ticks": ticks, "events": ev})
    write_json("sound/title_tune.json", {
        "player": "MICROPEARL MUSIC PLAYER (C) 1983 John A. Fitzpatrick, $E000-$E86F; API $E000 stop, $E003 play song list, $E006 update per frame",
        "tune_table": {"name": tname(tt), "address": hx(tt), "tune0": [hx(w16(tt + 2 * k)) for k in range(4)],
                       "tune1_stale": [hx(w16(tt + 8 + 2 * k)) for k in range(4)]},
        "length_table": {"address": hx(LEN_TABLE), "short": list(IMG[LEN_TABLE:LEN_TABLE + 16]),
                         "long": list(IMG[LEN_TABLE + 16:LEN_TABLE + 32])},
        "instruments": {"address": "$E80A", "entries": [hexbytes(IMG[0xE80A + 8 * k:0xE812 + 8 * k]) for k in range(8)],
                        "format": "AD/SR pairs for articulation 0, 1, 2 + 2 unused bytes"},
        "note_numbering": "1 = C1 ... 82 = A7 (NTSC frequency table $E200/$E254), transpose $E100 added",
        "length_table_at_start": "long" if sel else "short",
        "ticks": "note lengths in ticks of the global length table (set by the leading $AC/$AD commands); "
                 "frames = ticks * tempo ($E0 command)",
        "voices": voices,
    })
    eff = []
    for i in range(15):
        a = w16(SFX_TABLE + 2 * i)
        recs, end = decode_sfx(a)
        eff.append({"id": i, "request_y": hb(0x80 + i), "name": nm(a, "sfx_%d" % i), "start": hx(a),
                    "end": hx(end), "callers": sfx_callers(i, a), "records": recs})
    write_json("sound/sfx.json", {
        "table": {"name": tname(SFX_TABLE), "address": hx(SFX_TABLE), "entries": 15},
        "request": "game routine $2509 with Y = $80 + id; players $EB03/$EF73/$F073 (SID voices 1-3) run once per frame",
        "opcodes": {"0": "00 end", "1": "01 wait note", "2": "02 wait note control",
                    "3": "03 wait note adsr_offset control", "4": "04 wait note adsr_offset pulse_offset control",
                    "5": "05 wait note pulse_offset control", "6": "06 wait note pulse_offset control",
                    "7": "07 control (not used)"},
        "adsr_table": hx(SFX_ADSR), "pulse_table": hx(SFX_PULSE),
        "effects": eff,
    })
    write_bin("sound/music_player_e000-eaff.bin", IMG[0xE000:0xEB00])
    write_bin("sound/title_tune_e8c0-eaac.bin", IMG[0xE8C0:0xEAAD])
    write_bin("sound/sfx_data_ebe5-ee82.bin", IMG[0xEBE5:0xEE83])


# ----------------------------------------------------------------------------
# demo input
# ----------------------------------------------------------------------------

DIRS = {0xF: "none", 0xE: "up", 0xD: "down", 0xB: "left", 0x7: "right",
        0xA: "up+left", 0x6: "up+right", 0x9: "down+left", 0x5: "down+right"}


def extract_demo():
    end = 0xF538
    if K and K.loaded:
        r = K.region_at(DEMO_INPUT)
        if r is not None and r["s"] == DEMO_INPUT:
            end = r["e"]
    data = IMG[DEMO_INPUT:end + 1]
    steps = []
    for i, b in enumerate(data):
        d = b & 15
        pressed = [n for bit, n in ((1, "up"), (2, "down"), (4, "left"), (8, "right")) if not d & bit]
        steps.append({"step": i, "address": hx(DEMO_INPUT + i), "byte": hb(b),
                      "direction": DIRS.get(d, "+".join(pressed)), "dir_nibble": d,
                      "standard": d in DIRS, "fire": (b >> 4) == 0, "fire_nibble": b >> 4})
    write_bin("demo_input.bin", data)
    write_json("demo_input.json", {
        "name": nm(DEMO_INPUT, "demo_input"), "address": "%s-%s" % (hx(DEMO_INPUT), hx(end)),
        "reader": "$179E reads one byte per main-loop pass through ($1D): low nibble -> actor_joy_dir ($98, "
                  "joystick bits, 0 = pressed: bit0 up, bit1 down, bit2 left, bit3 right), "
                  "high nibble -> actor_joy_fire ($9B, 0 = pressed). The stream has no end marker; the "
                  "recorded demo runs read up to $F538 (end of the knowledge region).",
        "note": "the bytes look like (note, length) pairs of another music format: reused leftover data, "
                "so many steps hold non-standard direction combinations",
        "steps": steps,
    })


# ----------------------------------------------------------------------------
# README
# ----------------------------------------------------------------------------

README = """# Bruce Lee (C64) - extracted assets

Generated by `python3 -I tools/extract_assets.py` from `unpacked/image.bin`
(the 64 KiB RAM at the game entry `$0400`). Do not edit; run the tool again.
`--check` also compares the room renders with the screenshots in `runs/rooms/`.
Names come from the project knowledge (`.c64-re-tools/local/kexport.json`).
Addresses below are C64 RAM addresses in that image. Colours are C64 colour
numbers 0-15; PNGs are indexed and use Pepto's palette, so the PNG pixel index
is the C64 colour number unless stated otherwise.

## rooms/ - the 20 screens

| file | content |
|---|---|
| `roomNN.png` | 320x176 render of screen rows 3-24 (the map area; the status line rows 0-2 are not room data) |
| `roomNN.json` | decoded 40x11 cell map, charset, colours, raster bands, exits, spawn points, enemy delays, lantern list, room handlers, setup changes |

The render shows the room as `draw_room` (`$09BC`) leaves it: map decoded, colour RAM filled, then
`redraw_taken_lanterns` (`$336E`) and the room's setup handler (`$4E9C` table) run on a small 6502
interpreter inside the tool, so their colour RAM patches (rooms 5, 9, 16, 17, 18) are included
(`setup_changes` in the JSON). Run-time animation is not: lamp flicker, the scrolling texture tiles
`$61-$63` (shown at phase 0), moving hazards and sliders, room 17's colour flip and room 19's random colours.

Map streams `$68F9-$817F`, pointers `$4B34` (lo) / `$4B49` (hi). RLE: `$80` end,
`$81-$FF` = the next `b&$7F` bytes are cells, `$01-$7F` = the next byte repeated `b` times.
40 cells per row, 11 rows. A cell is an 8x16 tile: tile `v&$7F` in the top char row, `(v&$7F)|$80` below.
Bit 7 of a cell sets colour RAM `$F8` (colour-3 pixels black). Rooms 4, 7, 10, 13, 17, 18 encode 442 cells
(the extra two land outside the screen: a bug of the original).
Exit tiles: `&$7F` = 2/3/4/5 use the exit tables (dest `$4B5E/$4B72/$4B86/$4B9A`, X `$4BFE/$4C26/$4C4E/$4C76`,
Y `$4C12/$4C3A/$4C62/$4C8A`); X = 0 falls through to the next group.

Pixel colours: `%00` = `$D021`, `%01` = `$D022`, `%10` = `$D023` from the room's colour triplets
(`$480B` pointers into `$47C8`), `%11` = room colour `$47A0+room` & 7 (or black for bit-7 cells).
Colour bands: `$4833` points to up to 3 raster lines (ended by `$FD`); triplet k applies from raster line L+3
of the k-th listed line (screen pixel row y = raster - 51). Charset: rooms 0-9 set 0, room 18 set 2, others set 1.

Lanterns: `$4CE2` -> per room 4-byte records (state, cell drawn when collected, column, text row), ended by `$FF`.
The row is a text row of the message printer (screen row 2*row-1), so the lantern is in map row `row-2`.
Rooms 13 and 19 hold one placeholder record (count 0).

## charsets/

| file | content |
|---|---|
| `charset_N.bin` | raw 1 KiB source of set N (`$9000`, `$9400`, `$9800`, `$9C00`) |
| `charset_N.png` | 128 tiles, 16 per row, each 8x16 pixels |

Source char c = 8 bytes at `src+8c`, one byte per row of 4 multicolour pixels (bits 7-6 leftmost).
The game expands it at init (`$4892`) to a 2 KiB VIC charset: rows 0-3 doubled -> char c (top half),
rows 4-7 doubled -> char c+128 (bottom half), so each source row is 2 pixel rows tall.
The PNG pixel index is the bit pair (0 = `$D021`, 1 = `$D022`, 2 = `$D023`, 3 = colour RAM),
shown in black, light grey, grey and yellow. Set 3 is used only by the room 18 flash effect.
Note: the game overwrites `$9000-$9FBF` with collision masks after expansion; these files are taken from the image before that.

## sprites/

| file | content |
|---|---|
| `bruce.png`, `yamo.png`, `ninja.png` | top: the 35 displayed frame pairs; bottom: all 70 single frames |
| `frames.json` | per frame: source address, height, wide flag, colour, actor, mask address, raw bytes, sheet position |
| `tm_sprite.png`, `tm_sprite.bin` | the title's TM sign (63-byte sprite block, rows 4-7 from `$0E40`) |

Frame tables (210 frames, Bruce 0-69, Yamo 70-139, Ninja 140-209): source `$59BD`/`$5A8F`, height `$5B61`,
colour `$5C33`, wide flag `$5CBF`; graphics `$5D91-$68F8`. Narrow frame = h+1 rows of 1 byte, wide = h rows of
2 bytes. Hi-res, X-expanded sprites (every bit 2 screen pixels wide), bit set = sprite colour.
A displayed pose is the pair (even frame A, odd frame B) at the same position; A is the lower VIC sprite
number (4 for Bruce, 6 for Yamo) and so is in front of B. A wide A frame moves 16 px left when the actor
faces left; B moves 16 px left for relative frames 5, $19, $3F, $43. The facing is not stored with the
frame; the sheet uses the placement where the layers overlap best (`pair_facing_assumed` in frames.json).
The Ninja has no overlay and is always black. Sheet palette index 16 is the background.

## fonts/

| file | content |
|---|---|
| `title_font.png`, `title_font.bin` | the big title font `$8400-$87FF` (chars `$80-$FF` of the charset at `$8000`), multicolour, index = bit pair as in charsets/ |
| `title_layout.png` | screen rows 0-10 of the title as the game shows them (title colours, with the TM sprite) |
| `title_layout.json` | title row codes (`$4A0D`, `$49BD`, `$49E5`, `$4A35`), letter layout, PLAYER n banner codes |

## text/messages.json

`$43BE`: 101 message pointers used by `print_message` (`$17E2`). A message ends with `$A0`; byte b is drawn
as screen code `(b-$20)&$7F` (top half) and `|$80` (bottom half). Text messages are ASCII; tile messages
(room tile strings drawn by room scripts) list the raw bytes and the resulting chars. Also the version line
`$4707`, the unreferenced texts and the Apple II source text leftover at `$5900` (not game data).

## tables/

| file | content |
|---|---|
| `room_handlers.json` | room setup (`$4E9C`) and per-frame (`$4EC4`) RTS tables: target and name per room |
| `irq_chain.json` | raster IRQ handlers and every place that sets the next handler (`$0408`) and its raster line |
| `jump_tables.json` | every addresses / rts-addresses / jumps / split-address / words region of the knowledge, decoded |
| `room_tables.json` | room colours, band colours, raster lists, map pointers, exits, spawns, lanterns, enemy delays, Atari leftovers |
| `actor_frame_addr.json` | collision mask address per frame (`$1167`/`$1239`) |

## sound/

| file | content |
|---|---|
| `title_tune.json` | the 3 voice streams of tune 0 decoded to commands and notes |
| `sfx.json` | the 15 sound effect streams decoded, with request id and callers |
| `music_player_e000-eaff.bin` | the complete music player with its data (load at `$E000`) |
| `title_tune_e8c0-eaac.bin` | tune table + the 3 voice streams |
| `sfx_data_ebe5-ee82.bin` | effect table, opcode offsets, ADSR and pulse tables, effect streams |

Music voice stream: `$00` rest, `$01-$7F` note (1 = C1), `$8n`/`$Fn` length index n (ticks from `$E6F9`),
`$9n` volume, `$A0-$A3` waveform, `$A4-$A6` articulation, `$A7/$A8` tie, `$A9/$AA` ring mod, `$AB` pulse+tri,
`$AC/$AD` short/long length table, `$Bn` instrument (`$E80A+8n`), `$C0 lo hi` pulse width, `$Dn xx` filter,
`$E0 nn` tempo (frames per tick), `$FF` end.
Effect stream records: `00` end, `01 w n`, `02 w n ctrl`, `03 w n adsr ctrl`, `04 w n adsr pulse ctrl`,
`05/06 w n pulse ctrl`, `07 ctrl`; w = frames to wait, n = note, adsr/pulse = byte offsets into `$EC11`/`$EC1B`.

## demo_input.json / demo_input.bin

`$F300-$F538`: one byte per main-loop pass in demo mode. Low nibble = joystick direction bits
(0 = pressed: bit 0 up, 1 down, 2 left, 3 right), high nibble = fire (0 = pressed). The data is reused
leftover data, so many bytes hold unusual direction combinations.
"""


# ----------------------------------------------------------------------------
# check against screenshots
# ----------------------------------------------------------------------------

# Expanded-charset bytes the lamp flicker code $40D0-$412F rewrites (formats.md 1.2)
FLICKER_BYTES = (0xA432, 0xA49A, 0xA4A2, 0xA58A, 0xAC9A, 0xACA2, 0xAD8A, 0xA73A)
SCROLL_TILES = (0x61, 0x62, 0x63)   # animate_scrolling_chars $2C70 (rooms using sets 0 and 1)


def static_tags(r, R, C, state):
    """What the image alone says about a map cell that may differ in a
    screenshot: lanterns, lamp flicker tiles, scrolling texture tiles."""
    tags = []
    screen = state[0]
    _, _, recs = lantern_list(r)
    if any(rec.get("map_row") == R and rec["column"] == C for rec in recs):
        tags.append("lantern")
    cs = room_charset(r)
    for half in (0, 1):
        ch = screen[40 * (3 + 2 * R + half) + C]
        start = CHARSET_EXP[cs] + (0x400 if ch & 0x80 else 0) + 8 * (ch & 0x7F)
        if any(start <= a + k < start + 8 for a in FLICKER_BYTES for k in (0, 1)):
            tags.append("lamp flicker")
            break
    if cs in (0, 1) and screen[40 * (3 + 2 * R) + C] & 0x7F in SCROLL_TILES:
        tags.append("scrolling tile")
    return tags


def check_rooms(renders, states):
    """Compare the room renders with runs/rooms/roomNN.png and roomNN_b.png
    (border cropped: 32 px left/right, 35 px top; map area only)."""
    results = []
    for r in range(NROOMS):
        W, H, pix = renders[r]
        shots = []
        for suffix in ("", "_b"):
            path = os.path.join(SHOTS, "room%02d%s.png" % (r, suffix))
            if not os.path.exists(path):
                continue
            sw, sh, rows = screenshot_indices(path)
            same = 0
            diff_cells = {}
            for y in range(H):
                srow = rows[35 + MAP_Y0 + y]
                for x in range(W):
                    if srow[32 + x] == pix[y * W + x]:
                        same += 1
                    else:
                        diff_cells[(y // 16, x // 8)] = diff_cells.get((y // 16, x // 8), 0) + 1
            cells = []
            for (R, C), n in sorted(diff_cells.items()):
                cells.append({"cell": [R, C], "pixels": n, "tags": static_tags(r, R, C, states[r])})
            shots.append({"room": r, "file": os.path.basename(path), "rate": same / (W * H), "cells": cells})
        results.append(shots)
    return results


# ----------------------------------------------------------------------------
def read_program():
    """The program from the knowledge (D83): 64 KiB, 0 outside its segments."""
    memory = bytearray(0x10000)
    with open(os.path.join(ROOT, ".c64-re-tools", "knowledge", "memory.jsonl")) as rows:
        for line in rows:
            row = json.loads(line)
            if row["closed"] is None and row["space"] == "c64":
                at = int(row["at"][1:], 16)
                data = bytes.fromhex(row["bytes"])
                memory[at:at + len(data)] = data
    return bytes(memory)

def main():
    global IMG, K
    IMG = read_program()
    if len(IMG) != 0x10000:
        sys.exit("image.bin must be 64 KiB")
    K = Knowledge(KEXPORT)
    if not K.loaded:
        print("note: %s not found; using built-in names" % KEXPORT)
    for sub in ("rooms", "charsets", "sprites", "fonts", "text", "tables", "sound"):
        rmtree(os.path.join(OUT, sub))
    for f in ("demo_input.json", "demo_input.bin", "README.md"):
        p = os.path.join(OUT, f)
        if os.path.exists(p):
            os.remove(p)
    os.makedirs(OUT, exist_ok=True)

    renders, states = extract_rooms()
    extract_charsets()
    extract_sprites()
    extract_title_font()
    extract_texts()
    extract_tables()
    extract_sound()
    extract_demo()
    write_text("README.md", README)

    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print("wrote %d files to %s" % (n, os.path.relpath(OUT, os.getcwd())))

    if "--check" in sys.argv[1:]:
        if not os.path.isdir(SHOTS):
            print("no screenshots in %s" % SHOTS)
            return
        for shots in check_rooms(renders, states):
            for res in shots:
                cells = res["cells"]
                untagged = [c for c in cells if not c["tags"]]
                tags = {}
                for c in cells:
                    for t in c["tags"]:
                        tags[t] = tags.get(t, 0) + 1
                print("room %02d  %-13s %7.3f%%  %3d cells differ  %s" % (
                    res["room"], res["file"], 100 * res["rate"], len(cells),
                    " ".join("%s:%d" % kv for kv in sorted(tags.items()))))
                if untagged:
                    print("          other cells (row,col:pixels): " + " ".join(
                        "%d,%d:%d" % (c["cell"][0], c["cell"][1], c["pixels"]) for c in untagged[:24])
                        + (" ... (%d more)" % (len(untagged) - 24) if len(untagged) > 24 else ""))


if __name__ == "__main__":
    main()
