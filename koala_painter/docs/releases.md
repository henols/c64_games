# The releases and their cracks

This page tells about the three cracked releases of Koala Painter in the project. Version v1 has the Mayday! release. Version v2 has the releases of TBC and MAM. For each crack, the page gives the files of the disk and tells how the crack starts the program. It also tells which bytes of the program each crack changed. The test notes [../v1/tests/README.md](../v1/tests/README.md) and [../v2/tests/README.md](../v2/tests/README.md) describe the runs.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge, with the label `v1:` or `v2:` of their project.
- A *release* is one cracked disk or file. Its *capture* is the memory of the program at its entry, without the intro and the loader of the crack.
- The *pad* is the KoalaPad. The program reads its position from the paddle registers `$D419` and `$D41A`, and its two buttons from joystick port 1.
- **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code or the bytes of a file only. **Conclusion** marks an interpretation.

## The three releases

Each release is a crack. No release has the original protected disk of Koala Technologies. Thus the original bytes of the protection checks are not known (**Conclusion**). The SHA-256 values come from sha256sum (**Observed**).

| Label | Version | File | SHA-256 |
|---|---|---|---|
| MAYDAY | v1 | `v1/original/koalapainter_myd.prg` | `74bf7dfc05af5d778b65a58a700b57cd1533b3d9f98cbe2e28955843465271fe` |
| TBC | v2 | `v2/original/KoalaPainter.d64` | `c2f29f1c2fe5cba6e4380b20853f7e6a4e015853c5e8302de1ea8fc13e216ce6` |
| MAM | v2 | `v2/original/koala.d64` | `97b874579164369b58c47c5db12436be3351fbebaa48e1a642bf7b7567a869fc` |

The project also has these files of the releases (**Observed**):

- `v1/original/koalapainter_myd.d64` is the Mayday! disk. It holds `koalapainter_myd.prg` byte for byte.
- `v2/original/kmain_tbc.prg` and `v2/original/ktitle_tbc.prg` are the files KMAIN and KTITLE of the TBC disk.
- `v2/original/koalapainter_mam.prg` is the file KOALAPAINTER of the MAM disk.
- `v2/original/KOALA_PAINTER.T64` is a tape file with one more copy of the MAM file. It differs only in `$0829-$08C0`, the crack code of MAM. Its code reads only the joystick in port 2, and no key.

The captures have these ranges (**Observed**: `knowledge.ts releases`):

- MAYDAY: `$0900-$7F3F`, at the entry `$092F`, after the intro and the title screen of Mayday!.
- TBC: `$0900-$4838` (KMAIN) and `$5718-$7F43` (KTITLE), at `$0900`, in the KoalaPad mode of the crack.
- MAM: `$0900-$47FF`, at `$0900`. The capture does not include `$0801-$08FF`, the BASIC line and the code of MAM at the start of the file.

CSDb lists the three releases. MAM is release 46888 of 1984. TBC is release 67839, "Crack by Antiprotect of Terrestrial Breakin' Company". Mayday! is release 236080 of 7 October 2023, with the crack by TheRyk and the test by Retroluzzer of Excess (**Observed** on csdb.dk).

## TBC: the question, KP and the joystick routine

The disk has the name "KOALA PAINTER" and the id "AN". It holds four files (**Observed**).

| File | Blocks | Load range | Content |
|---|---|---|---|
| KOALA PAINTER | 2 | `$0801-$0968` | The BASIC menu of the crack |
| KP | 1 | `$C000-$C061` | The loader |
| KTITLE | 41 | `$5718-$7F43` | The title picture and its show code |
| KMAIN | 64 | `$0900-$4838` | The program, with the joystick routine at `$4800` |

The MAM disk also has a file KTITLE at `$5718`. Thus KTITLE and KMAIN are probably the names of the original files (**Conclusion**).

### How TBC starts the program

The BASIC menu prints "KOALAPAINT : CRACKED AND ADAPTED FOR JOYSTICK BY ANTIPROTECT". Then it starts the program in these steps (**Code**: the bytes of KOALA PAINTER and KP):

1. The menu asks "USE A JOYSTICK OR A PADDLE/TOUCHBOARD?" and accepts only J, P or T.
2. It writes 0 to `$FE`, or `$FF` for J. Then it prints "PLUG IT INTO PORT ONE" and loads KP to `$C000`.
3. KP loads KTITLE and calls [`v2:title_show` `$5718`](../v2/src/leftovers/leftover_5718.asm#L6), which shows the title picture.
4. KP loads KMAIN. When `$FE` is 0, KP jumps to `$0900`, the first entry of `v2:entry_jump_table`.
5. For J, KP first writes the joystick patches, then jumps to `$0900`.

### The joystick patches at run time

In the joystick mode, KP writes two patches into the program (**Code**: the bytes of KP):

- `$0999-$09A0` gets `$10` and 7 NOPs. The button test of [`v2:irq_timer` `$098C`](../v2/src/irq/irq.asm#L39) then reads the fire bit of port 1, not the two pad buttons.
- `$09FC-$0A05` gets JSR `$4800` and 7 NOPs. [`v2:read_pad_registers` `$09F8`](../v2/src/irq/irq.asm#L108) then calls the joystick routine in place of its reads of `$D419` and `$D41A`.

The routine [`v2:tbc_joystick` `$4800`](../v2/src/crack/tbc_joystick.asm#L6) reads joystick port 1. It changes a Y position at `$4833` and an X position at `$4834`, and writes them to `v2:pad_y_raw` and `v2:pad_x_raw`. The rest of the program reads these two bytes as the position of the pad (**Code**).

The routine is part of the file KMAIN, which ends at `$4838`. The program of MAM ends at `$47FF`. Thus no release gives the original bytes of `$4800-$4838` (**Observed**: the load ranges). The switch CRACK_TBC holds the routine, and the default build has zero bytes there (**Code**).

The tests use the same patches. The emulator gives no paddle values, so each record file writes the two patches of KP and the routine before it starts the program. The v1 tests put a copy of the routine at `$4630`. The steps move the cursor with writes to the two positions of the routine (**Observed**: the replays of both versions).

### The protection NOPs

The start-up script calls [`v2:disk_protection` `$3A43`](../v2/src/protection/disk_protection.asm#L6). It reads track 1, sectors 1 and 2, with U1 commands. TBC put two NOPs at each of `$3A65`, `$3A6A`, `$3A7B` and `$3A80`, over the checks after the reads (**Code**). The reads still run, but the program ignores the result. The Storage snapshot of v2 ran the protection with a copy of the Mayday! disk, and the program started (**Observed**). The original bytes of the checks are in no release. The switch PROTECTION is on in TBC.

## MAM: German instructions and PAINT.BOOT

The disk has the name "KOALA" and the id " 4". Only 2 blocks are free (**Observed**).

| File | Blocks | Load range | Content |
|---|---|---|---|
| ` KOALAPAINTER` | 6 | `$0401-$09B7` | The BASIC intro of the crack. The name starts with a space. LOAD puts it at `$0801`. |
| KOALAPAINTER | 65 | `$0801-$47FF` | The BASIC line and the code of MAM, then the program |
| KTITLE | 41 | `$5718-$7F3F` | The title picture and its show code |
| PAINT.BOOT | 1 | `$C000-$C08F` | The loader |
| LOAD-PIC., VIEW CONTINUESLY | 4, 1 | `$0401`, `$0801` | A BASIC picture loader and a slide show |
| PIC A to PIC M | 40 each | `$6000-$8710` | 13 sample pictures. PIC M ZAXXON is shorter and ends at `$8514`. |
| KATZEN SYS 16384, GIGALOAD, GL.ASS | 12, 3, 9 | `$4000`, `$0801`, `$C800` | Other programs |

GIGALOAD is a fast loader with German text. The text names the drives 1570 and 1571, the C128 and GEOS. These products are from after 1984. Thus somebody added these files to the disk later (**Conclusion**).

### How MAM starts the program

The intro is a BASIC program in German. It prints "KOALAPAINTER CRACKED 1984 BY MAM", "JOYSTICK/KEYBOARD" and "'I' FUER ANLEITUNG", which means "I for the instructions". The instructions give the keys and the joystick control (**Code**: the BASIC lines):

- The keys 1-5, QWERT, ASDFG and ZXCVB move the cursor to the boxes of the menu. For example, Q moves it to Draw.
- F1, F3, F5 and F7 move the cursor up, down, left and right in small steps.
- Joystick 2 moves the cursor. Fire or SPACE selects a box.
- In the zoom mode the keys are slow, so you must sometimes press a key more than one time.

Then MAM starts the program in these steps (**Code**: the bytes of the intro and of PAINT.BOOT):

1. After 500 key reads, or after a key other than I, the intro loads PAINT.BOOT to `$C000` and calls it.
2. PAINT.BOOT loads KTITLE and calls `v2:title_show` at `$5718`.
3. PAINT.BOOT loads KOALAPAINTER to `$0801` and jumps to `$0900`.

The file KOALAPAINTER starts with the BASIC line `0 SYS(2304) KOALAPAINTER CRACKED BY MAM`. 2304 is `$0900`, so a RUN of the file also starts the program (**Code**).

### The joystick and keyboard code at $0829

The code of MAM is at `$0829-$08C0` in the file KOALAPAINTER, before the program. When `v2:scan_keys_enable` is 0, it reads a key with GETIN and the joystick in port 2. Both parts change `v2:pad_x_raw` and `v2:pad_y_raw`. Else the code does nothing (**Code**: the bytes of the file).

MAM changed two parts of the program to use this code (**Code**: switch CRACK_MAM):

- `$0998-$09A0` in `v2:irq_timer`: the button test reads the fire bit of port 1 and of port 2.
- `$09FC-$0A05` in `v2:read_pad_registers`: JSR `$0829` and 7 NOPs, in place of the reads of `$D419` and `$D41A`.

These patches are in the file. Thus the MAM release always uses its joystick and keyboard code, and it never reads the pad (**Code**). The source starts at `$0900` and does not have the code at `$0829`. A build of MAM thus needs the first page of the MAM file at `$0801-$08FF` (**Conclusion**).

### The W1 change

MAM changed the protection in a different way from TBC (**Code**: switch CRACK_MAM):

- `$3A59-$3A87` in `v2:disk_protection`: NOPs over the two reads and their checks. The program sends no command to the drive.
- `$3A97` and `$3AA2` in [`v2:protection_commands` `$3A96`](../v2/src/protection/disk_protection.asm#L60): "W" in place of "U", so the commands are W1. The drive does not know W1.
- [`v2:protection_open_buffer` `$3AAD`](../v2/src/protection/disk_protection.asm#L89) writes 2 to `$0850` and returns. `v2:protection_read_status` gives 2 in place of the first digit of the status.

The only calls of the last two routines are in `$3A59-$3A87`. Thus the changes in them have no effect (**Code**). The switch PROTECTION is on in MAM too.

The KTITLE file of MAM differs from KTITLE of TBC at `$571B`. TBC has `LDA #$00` there, and MAM has `LDA $0B`. The next instruction writes A to `$D011`. MAM's file is also 4 bytes shorter (**Observed**: a byte compare).

## Mayday!: a crack for the KoalaPad

The disk has the name "FUN NOT FAME" and the id "20". The pictures have some names of the MAM disk, but their bytes are different (**Observed**: a byte compare).

| File | Blocks | Load range | Content |
|---|---|---|---|
| KOALAPAINTER/MYD | 71 | `$0801-$4D94` | The packed program, with the intro and the title screen of the crack |
| READMENOTE | 21 | `$0801-$1C5B` | The note file |
| PIC A to PIC H | 40 each | `$6000-$8710` | 8 sample pictures |

### Why Mayday! made the crack

The note file "NOTE FILE - MAKING OF..." tells the reason. Stefan Both made "CommoPad", a replica of the KoalaPad. The old crackers changed the I/O code of their cracks for a joystick. The note says that this made all the old cracks unusable with a KoalaPad. Somebody then put a G64 image of an original disk on the internet (**Observed**: the text of the note in memory). CSDb names Groepaz for the original. Thus Mayday! most likely made the crack from this G64 (**Conclusion**).

The note says that Retroluzzer/EX tested the release on a real KoalaPad. It also says: without a KoalaPad or a replica, use an emulator, for example the mouse grab of VICE. The note has the music "Up And Down 3" by Froyd and a scroller by Achim/MYD! (**Observed**).

### How Mayday! starts the program

The file unpacks in two stages. The intro of Mayday! waits for SPACE. Then the code of the title screen at `$0810` shows the title picture. It waits for fire on port 2 (**Observed**: the stages of the unpacker and the `all_tools` recording of v1).

Then this code jumps to [`v1:cold_start_irq_setup` `$092F`](../v1/src/init/entry.asm#L34) (**Observed**: the capture). Thus the release does not execute the KERNAL calls of `v1:cold_start` at `$091B` (**Code**). In v1, `$5718-$57FF` holds zero bytes, not the show code of KTITLE (**Code**).

### The device number from $BA

The note says: "all hard-coded disk operations were bent to get device no. from ZP-reg $BA". Mayday! tested the device numbers 8-11. Mayday! changed four places (**Code**: switch CRACK_MAYDAY):

- [`v1:set_picture_file` `$2C33`](../v1/src/storage/storage_screen.asm#L342) and [`v1:send_command_close` `$2C83`](../v1/src/storage/storage_screen.asm#L400): LDX `$BA` in place of LDX #8.
- `v1:protection_open_buffer` at `$39BA`: also LDX `$BA`.
- [`v1:drive_status` `$39C4`](../v1/src/storage/drive_status.asm#L6): LDA `$BA` in place of STA `$BA`. The original wrote 8 to `$BA` here.

Thus Storage uses the device of the last load. That is correct after a normal load from a drive. After a program load without a drive, `$BA` was not 8. Storage then sent its commands to a different device, and the CPU waited at `$EDD9` (**Observed**: the Storage test of v1). The v1 tests thus start from a snapshot after an autostart of the disk.

The note also warns about JiffyDOS. SAVE and NAME & SAVE over a file can give strange error messages, because JiffyDOS changed the scratch routine (**Observed**: the text of the note).

### The removed protection call

Mayday! put three NOPs at `$0955` in `v1:cold_start_irq_setup` (**Code**). The original bytes are in no release. They were most likely JSR `$0A81`, because v2 calls `v2:start_script` at the same point of its cold start, at `$093D` (**Conclusion**). Thus nothing calls [`v1:start_script` `$0A81`](../v1/src/leftovers/leftover_0a68.asm#L11).

That routine runs `v1:startup_script`, whose op 9 calls `v1:disk_protection`. The protection reads track 33, sectors 5 and 6, with B-R commands. It is in the source as a leftover that nothing calls (**Code**). v1 has no switch PROTECTION, because no release has the bytes of the call (**Code**).

## Why the old cracks do not work with a KoalaPad

The program reads the pad position from `$D419` and `$D41A` in `v2:read_pad_registers`. The joystick patches replace exactly these reads (**Code**):

- MAM replaces them in the file. The MAM release never reads the pad.
- TBC replaces them only in the joystick mode. In the P and T modes, KP jumps to the program without the patches.

The note of Mayday! says that no old crack worked with a KoalaPad. For MAM, the code shows the cause. For the P and T modes of TBC, the code does not show a cause, and no run used a real pad (**Conclusion**).

## The switches and the builds

The default build of each project is the clean program. It has no crack change and no protection (**Observed**: `knowledge.ts switches`). LEFTOVERS and START_SCREEN are switches of the generated source, not of the knowledge.

| Project | Switch | Kind | Default | MAYDAY | TBC | MAM |
|---|---|---|---|---|---|---|
| v1 | CRACK_MAYDAY | crack | 0 | 1 | – | – |
| v2 | PROTECTION | protection | 0 | – | 1 | 1 |
| v2 | CRACK_TBC | crack | 0 | – | 1 | 0 |
| v2 | CRACK_MAM | crack | 0 | – | 0 | 1 |
| v1, v2 | LEFTOVERS | leftovers | 0 | 1 | 1 | 1 |
| v1, v2 | START_SCREEN | start screen | 1 | 0 | 0 | 0 |

Run these commands of c64-assembler from the project folder `v1` or `v2`:

| Build | Command | Result |
|---|---|---|
| Default program | `assembler.ts build src main.asm` | `build/clean.prg` |
| MAYDAY | `assembler.ts build src main.asm --release MAYDAY --compare` | identical to `$0900-$7F3F` of the release |
| TBC | `assembler.ts build src main.asm --release TBC --compare` | identical to `$0900-$4838` and `$5718-$7F43` |
| MAM | `assembler.ts build src main.asm --release MAM --compare` | identical to `$0900-$47FF` |

**Observed**: each release build gave PASS in a copy of the projects. The runnable default program is `build/clean_loader.prg`. The command `source.ts generate --out src --loader` of c64-source makes it.

## Other cracks on CSDb

CSDb lists more cracks of Koala Painter. The project does not have them, so it knows nothing about their changes (**Observed** on csdb.dk):

- JXR, release 193797: a recrack of the MAM release.
- Mr. Crossbones, release 100680.
- Carlo, release 140037.
- Lakeland Cracking Services (LCS), release 141574.
- Verminman, release 237750.

## Still open

- Does the TBC release in the P or T mode work with a real KoalaPad? — A run on a real C64 with a KoalaPad, or on an emulator with paddle values.
- Which KTITLE byte at `$571B` is the original, `LDA #$00` of TBC or `LDA $0B` of MAM? — A disk image of the original release, for example the G64 that Mayday! used.
- Mayday! skips `v1:startup_script`, which writes 1 to the background of the picture at `$C7D0`. Does the Mayday! release start with a different background? — A run of the release with a watchpoint on `$C7D0`, compared with a run of v2.
- What are the original bytes at `$0955` in v1, of the checks in `v2:disk_protection` and of `$4800-$4838` in v2? — The original disk.
- What did JXR change in its recrack of MAM? — A copy of release 193797 and a byte compare with the MAM file.
