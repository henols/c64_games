# The releases

This page tells about the four cracked releases of "The Way of the Exploding Fist" in the project. Two releases have version I of the game, and two releases have version II. The page gives the files of each disk and the traces that each crack left in the program. It also tells how the project captured and compared the releases. Version I is on [../v1/README.md](../v1/README.md), version II is on [../v2/README.md](../v2/README.md), and the copy protection is on [protection.md](protection.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge, with the label `v1:` or `v2:` of their project.
- A *release* is one disk image of a crack. The *game bytes* are the bytes of the program at its entry, without the loader of the crack.
- The *entry* is the first instruction of the game: `$1158` in version I and `$115A` in version II.
- **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The four releases

Each release is a crack. No release has the original protected loader of Melbourne House, because each crack replaces it with a loader of its own (**Conclusion**). The project uses R2010 as the base release of version I and SCC as the base release of version II.

| Label | Version | Disk file | SHA-256 of the disk | Entry |
|---|---|---|---|---|
| R2010 | I | `v1/original/2010.d64` | `2646d419a57fa29c76d914dbe9b9dfe23f5e6e13d232ed1d30386b9ce31f7494` | `$1158` |
| SHADOW | I | `v1/original/Exploding_Fist.d64` | `de5ddbc564fe70f4d0b9e4d2809d2aa72707e812f58cc1d559db7b6970283299` | `$1158` |
| SCC | II | `v2/original/scc.d64` | `6a789804806c01c090c87ce32a31bd68be4e09b3865092f2592ebf3c1f48712c` | `$115A` |
| MRZ | II | `v2/original/mr_z.d64` | `8495eff9f00ebb4748916bd1ba8a60082853a9039368a7c549dbdeedd5756137` | `$115A` |

**Observed** (sha256sum of each disk file).

The knowledge holds each release as a capture of the game at its entry: `v1/original/releases/2010`, `v1/original/releases/shadow`, `v2/original/releases/scc` and `v2/original/releases/mrz`. Each folder has the image, the entry state and one PRG for each segment. The files `v1/original/fist_v1_2010.prg` and `v2/original/fist_v2_scc.prg` are loaders that the project generated for the two base releases. They put the original game bytes into memory, set the original entry state and start the game. The tests and the recordings run on them (**Observed**).

The differences in the game bytes are small:

- R2010 and SHADOW differ in 307 bytes (**Observed**). 304 bytes are values that a running game left in memory, and 3 bytes are a change of the crack (**Conclusion**).
- SCC and MRZ have the same game bytes (**Observed**).
- The two versions have different code and data layouts. The list of the differences is on [versions.md](versions.md).

## The disk layout

### The 2010 disk (R2010)

The disk name is "VAN DER WAALS SG" and the id is " 7". The disk holds eleven files (**Observed**).

| File | Blocks | Load range | Content |
|---|---|---|---|
| EXPLODING FIST | 1 | `$0801-$08FC` | BASIC line `2010 SYS2080`, the start of the crack, with its screen text |
| (2010) | 5 | `$C000-$C3FF` | The KERNAL loader of the crack |
| M.PROG | 125 | `$0400-$7FFF` | The game program |
| M.SHAPES | 84 | `$1000-$62FF` | The fighter shapes and other graphics, for `$8000-$BFFF`, `$C900` and `$D000` |
| M.CHSET | 7 | `$6300-$68FF` | The charset, for `$E000` |
| M.PRERUN | 1 | `$C400-$C435` | An RTS and a short routine that nothing calls |
| M.PICTURE | 40 | `$6000-$870F` | The Melbourne House title picture |
| M.XSPRITES | 11 | `$1000-$1AAF` | More sprite data, for `$F540` |
| M.MYTINY | 2 | `$9000-$910F` | The sample player of the loading stage |
| M.SPCHTBL | 4 | `$9800-$9AFF` | The count table of the sample player |
| M.TSOUND | 23 | `$2000-$35FF` | The speech sample of the loading stage |

The `M.` files have the names of the files on the original disk of Melbourne House. The crackers kept the original file set and replaced only the protected loader (**Conclusion**). The loading stage with the picture, the sample and M.PRERUN is on [loading_stage.md](loading_stage.md).

The loader (2010) loads and moves the files in this order (**Observed** in the disassembly and a run):

1. It loads M.PRERUN and M.PICTURE, copies the picture into VIC bank 3 and shows it.
2. It loads M.MYTINY, M.SPCHTBL and M.TSOUND, then calls `$9000`. The sample plays one time and the call returns at its end.
3. It loads M.SHAPES at `$1000` and copies it to `$8000-$BFFF`, `$C900` and `$D000`. The copy to `$D000` goes into the RAM under the I/O area.
4. It loads M.PROG at `$0400`, M.CHSET to `$E000` and M.XSPRITES to `$F540`.
5. It calls M.PRERUN at `$C400`, which is only an RTS. Then it jumps to the entry `$1158`.

The start file EXPLODING FIST prints the text of the crackers. The text has the line "WAIT FOR VERSION II" (**Observed** in the bytes of the file):

```text
THE WAY OF THE EXPLODING FIST.
SUPPLIED BY 2010 AND CHR..
WAIT FOR VERSION II
GREETING FROM THE PROFESSIONALS (2010)
```

The line tells that the crackers knew about a second version of the game when they released version I (**Conclusion**). Version II is the version of the SCC and Mr. Z releases.

The BAM marks 86 sectors as used, but no file holds them. They are all the sectors of tracks 4-7 and sectors 9 and 12 of track 8. They hold text and data of a different game, "THE DAM BUSTERS" by Sydney Development (**Observed** in the bytes of the sectors). Some of the texts are in this list:

- "THE DAM BUSTERS" and "1984 SYDNEY DEVELOPMENT"
- "CONCEPT: MICHAEL BATE", "STEVE ARMSTRONG" and "STUART EASTERBROOK"
- "THE PILOT IS DEAD. HOPE YOU BAILED OUT."
- the file names "DAM.001" and "DAM.002"

 These sectors are what remains of an older content of the disk. They are not part of Exploding Fist (**Conclusion**).

### The Shadow disk (SHADOW)

The disk has no name and two files (**Observed**).

| File | Blocks | Load range | Content |
|---|---|---|---|
| EXPLODING FIST | 43 | `$0801-$3201` | BASIC line `1984 SYS2117`, the intro of the crack |
| EXPLODING FIST2 | 184 | `$0801-$BE01` | BASIC line `1985 SYS2067`, the packed game |

The intro shows "Copenhagen Crackers presents Exploding Fist. Cracked by the SHADOW." and waits for a key (**Observed**).

### The SCC disk (SCC)

The disk name is "EXPLODING FIST" and the id is "10". The start file is a KERNAL chain loader at `$0200`. It opens the files A to I one after the other and reads each file with CHKIN (**Observed**).

Each of the files A to I starts with a header of 4 bytes. The first two bytes are the start address, and the next two bytes are the end address. The end address is the first address after the data (**Observed**: the data length of each file agrees with its header).

| File | Blocks | Header start | Header end | Data range | Content |
|---|---|---|---|---|---|
| EXPLODING FIST | 2 | – | – | `$0200-$0367` | The chain loader (a normal PRG) |
| A | 3 | `$C000` | `$C245` | `$C000-$C244` | The second stage of the loader |
| B | 9 | `$C400` | `$CC00` | `$C400-$CBFF` | Shapes and the period tables |
| C | 56 | `$5000` | `$8710` | `$5000-$870F` | `$5000-$5FFF` shapes for `$D000`, then the picture at `$6000-$870F` |
| D | 3 | `$8F10` | `$9110` | `$8F10-$910F` | The sample player, with M.MYTINY at `$9000-$910F` |
| E | 4 | `$9800` | `$9B00` | `$9800-$9AFF` | The count table of the sample player |
| F | 23 | `$2000` | `$3600` | `$2000-$35FF` | The speech sample |
| G | 190 | `$0400` | `$C000` | `$0400-$BFFF` | The game |
| H | 7 | `$E000` | `$E600` | `$E000-$E5FF` | The charset |
| I | 12 | `$F4F0` | `$FFF0` | `$F4F0-$FFEF` | More sprite and sample data |

The data of the files E and F is the same as M.SPCHTBL and M.TSOUND of the 2010 disk. The last 272 bytes of the file D are the same as M.MYTINY (**Observed** in a byte compare). The SCC crackers thus had the same original loading files as the 2010 crackers, in the files of version II (**Conclusion**).

### The Mr. Z disk (MRZ)

The disk has no name and two files (**Observed**).

| File | Blocks | Load range | Content |
|---|---|---|---|
| EXPLODING F/MR.Z | 3 | `$0801-$0AEC` | BASIC line `10 SYS2066`, the intro of the crack |
| FIST.OBJ | 207 | `$0801-$D557` | The packed game |

The intro shows "CRACKED BY MR Z..." and enters the game at `$115A` (**Observed**).

## The traces of the cracks in the program

This section gives only the traces that a crack left in the game bytes or in the machine state at the entry. Two switches of version I and one switch of version II come from these traces. The default build of each project gives the clean program. A build with `--release` gives the bytes of that release (**Observed**: each release build is identical to its capture).

### Shadow: a dump of a running game

The SHADOW release is a memory dump of a game that ran. 304 of the 307 different bytes hold run-time state in these areas (**Observed** in a byte compare):

- the self-modified operands of the raster handlers at `$263F-$2882`
- the music workspace and its state at `$0C8C-$0D3B`, `$0AD1`, `$0ADD` and `$0F53`
- the shape pointers of the shape builder at `$3194-$369D`, and `$8005`
- the sprite buffer bytes at `$C900-$C93E` and `$FD30-$FD4F`

The game writes each of these bytes when it runs, for example the row operand [`v1:irq_a_row2_y` `$263F`](../v1/src/irq_sprite_rows.asm#L13) of a raster handler (**Code**).

The switch RUN_STATE of version I holds these values in 96 patches. Its default is 0, which gives the R2010 bytes. The value 1 gives the SHADOW bytes (**Code**). The Bruce Lee project has a release of the same kind, the SAEGER release (**Conclusion**).

### Shadow: the zeroed bytes at $0800

The other 3 different bytes are at `$0800-$0802`. SHADOW has 0 there. R2010 has `$53 $43 $56`, which are bytes 13 to 15 of the pattern [`v1:music_t3_pattern_03` `$0800`](../v1/src/music_patterns.asm#L635) of tune 3 (**Observed**). No run of the game writes page `$08` (**Observed** in the coverage). Thus the 0 bytes come from the crack and not from the run.

The packed file of Shadow loads at `$0801`, and a BASIC program needs a 0 at `$0800`. The crack put the 0 there and did not restore the original bytes (**Conclusion**). Tune 3 is the music of the two-player game, so SHADOW plays this pattern with changed bytes (**Conclusion**). The switch CRACK_SHADOW_0800 of version I gives the SHADOW bytes. Its default is 0, which gives the original pattern (**Code**).

### SCC: the text in the title picture

The SCC crackers drew "CRACKED BY S.C.C." into the title picture. The file C and M.PICTURE differ only in the cells 27 to 37 of the rows 0 to 3. These cells are at the top right of the picture. The difference is in the bitmap, the screen data and the colour data (**Observed** in a byte compare). The file G loads later over `$6000-$870F`, and the captures leave out the picture areas. Thus the text is not in the game bytes (**Observed**).

The rebuild of version II shows the clean M.PICTURE of the 2010 disk at its start, from `v2/original/releases/2010_loading`. Then the start picture has no crack text. This image shows the clean picture.

![The Melbourne House title picture of M.PICTURE, without the crack text](../v1/docs/images/title_picture.png)

### SCC: the 0 in $DD0E

The chain loader of SCC ends with three instructions at `$0360` (**Observed** in the bytes of the file and in a run):

```text
$0360  LDA #$00
$0362  STA $DD0E   ; CIA2 control register A
$0365  JMP $115A   ; the entry of version II
```

Version II reads `$DD0E` at each scoring hit in [`v2:protect_cia2_check` `$2CAE`](../v2/src/hit_test.asm#L180). When the value is not 0, the game jumps to a false address and crashes (**Code**). The game itself never writes `$DD0E`. A C64 after a KERNAL reset has `$08` in it (**Code**). Thus this one store passes the copy protection check of version II, and SCC changes no byte of the game code to do it (**Conclusion**). The original protected loader probably left the 0 in `$DD0E` (**Conclusion**). The check and its effect are on [protection.md](protection.md).

The switch PROTECTION of version II is 1 in SCC and MRZ. Its default is 0, which replaces the read of `$DD0E` with `LDA #$00` and a NOP. Then the check always passes (**Code**).

### Mr. Z: the same game bytes as SCC

The game bytes of MRZ are identical to the game bytes of SCC (**Observed** in a byte compare). Thus the two releases have one project, and no switch separates them. At the entry, `$DD0E` holds 0 in MRZ also (**Observed** in the entry state). The protection check thus also passes in MRZ. Mr. Z possibly made his release from the SCC crack, but no fact shows that (**Conclusion**).

### 2010: the original files and a KERNAL loader

The 2010 crack keeps the original files of Melbourne House with their names and replaces only the protected loader with its own KERNAL loader (2010). It changes no byte of the game code (**Conclusion**: the files M.PROG, M.SHAPES, M.CHSET and M.XSPRITES give the game bytes of the base release). Version I has no copy protection check in the game, so the crack needs no patch (**Code**).

## How the project captured and compared the releases

The project ran each release in the emulator until the CPU arrived at the entry. Then it captured the memory and the machine state (**Observed**). Two intros wait for a key. The captures of SHADOW and MRZ moved the PC past the wait with a register step. The Mr. Z intro waits until the player releases all keys. In this VICE, the bits 5-7 of `$DC00` and `$DC01` read 0, so that wait never ends (**Observed**).

Each capture keeps the segments of the game and leaves out the areas that the loader or the picture use. The excluded areas are in the `image.json` of each release (**Observed**).

| Release | Segments | Excluded areas |
|---|---|---|
| R2010 | `$0400-$BFFF`, `$C900-$CBFF`, `$D000-$E5FF`, `$F540-$FFEF` | `$C000-$C435`, `$CC00-$CFE7`, `$E600-$F53F` |
| SHADOW | `$0400-$BFFF`, `$C900-$CBFF`, `$D000-$E5FF`, `$F540-$FFEF` | `$C000-$C8FF`, `$CC00-$CFFF`, `$E600-$F53F`, `$FFF0-$FFFF` |
| SCC | `$0400-$BFFF`, `$C400-$CBFF`, `$D000-$E5FF`, `$F540-$FFEF` | `$C000-$C3FF`, `$CC00-$CFFF`, `$E600-$F53F`, `$FFF0-$FFFF` |
| MRZ | `$0400-$BFFF`, `$C400-$CBFF`, `$D000-$E5FF`, `$F540-$FFEF` | `$C000-$C3FF`, `$CC00-$CFFF`, `$E600-$F53F`, `$FFF0-$FFFF` |

The excluded areas hold these parts:

- `$C000-$C435` holds the loader (2010) and M.PRERUN. In version II, `$C000-$C3FF` holds the second stage A of the SCC loader.
- `$CC00-$CFFF` holds the screen data of the title picture in VIC bank 3.
- `$E600-$F53F` holds the rest of the picture bitmap. The charset at `$E000-$E5FF` writes over the start of the bitmap.
- `$FFF0-$FFFF` is the top of the RAM with the CPU vectors. The last game file, M.XSPRITES or I, ends at `$FFEF`.

Junk tests show that the game does not need the excluded areas. The test runs filled these areas with junk bytes and played the same scenario as a clean run. The screens were the same. In memory, only `$C03F`, `$E600-$E63F` and the SID read-back byte `$0CDE` differed, and no code reads them (**Observed**). The scenarios [../v1/tests/leftovers_unused.json](../v1/tests/leftovers_unused.json) and [../v2/tests/leftovers_unused.json](../v2/tests/leftovers_unused.json) do the same test for the 25 unused regions in the segments of each version. They fill each region with `$A5`, and the game runs the same (**Observed**).

The comparison of the releases is byte by byte on the captured segments (**Observed**):

1. R2010 against SHADOW gives the 307 bytes of the section about Shadow.
2. SCC against MRZ gives no difference.
3. The build of each release is identical to its capture: R2010 and SHADOW in version I, SCC and MRZ in version II.

## Still open

- Which code of the Mr. Z release writes 0 into `$DD0E`? — A watchpoint on writes to `$DD0E` while the Mr. Z intro unpacks FIST.OBJ.
- Does SHADOW play the same as R2010 in a game? — A replay of a recording of `v1/tests/record` on the SHADOW capture, with a compare of the screens and of the state.
- What does a player hear in the two-player tune of SHADOW, with the 0 bytes in pattern 3 of tune 3? — A trace of the SID writes of voice 2 in a two-player game of SHADOW and of R2010.
- What did the original protected loader of Melbourne House do? — No release has it. A disk image of the original release is necessary.
