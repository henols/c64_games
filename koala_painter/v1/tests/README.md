# Tests of Koala Painter v1

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Each record file loads `program/mayday_0900.prg`, the memory `$0900-$7F3F` of the capture of the Mayday! release, and starts the program at its entry `$092F`. The coverage map starts there. `all_tools` is older: it starts `original/koalapainter_myd.prg` and goes through the Mayday! intro (SPACE) and the title picture (fire on port 2), so a rebuild cannot replay it.

Koala Painter reads only a KoalaPad: the position from the paddle registers `$D419`/`$D41A`, and the two buttons from joystick port 1. The emulator gives no paddle values, and this version has no joystick mode. Thus each record file writes these bytes before it starts the program (`all_tools` writes them while the title picture of Mayday! shows). Only the recordings have them. The project knowledge, the source and the builds do not.

| Address | Bytes | Why |
|---|---|---|
| `$4630` | 52 bytes | The joystick routine of the TBC release of v2 (`$4800` there), moved to empty RAM. Its variables are `$4663` (pad Y) and `$4664` (pad X). |
| `$09BF` | `10 EA EA EA EA EA EA EA` | The button test reads the fire bit of port 1, as in the TBC joystick mode. |
| `$0A07` | `20 30 46 EA EA EA EA EA EA EA` | The IRQ calls the routine at `$4630` in place of the paddle reads. |

The steps move the cursor with writes to `$4663` and `$4664`. The program converts the pad position to the screen. Screen X = (pad X - 20) * 4 / 5, and screen Y = pad Y - 20. A pad Y of `$E6` or more is "no touch". Fire on port 1 is the pad button.

The picture screen comes from the menu with "no touch" and a long press of the button. The same press goes back to the menu. Each step waits for the menu loop before it presses. A press during the release wait of the menu loop does not change the screen. `lines` waits one more frame before it presses: without that frame, the press came during the release wait.

| Recording | What it does |
|---|---|
| `all_tools` | Each tool once in one session, then Oops and Erase. Some tools in it work on the menu by mistake: the session lost its sequence. Use it only for its coverage. |
| `draw` | Draw: a drag and three taps. |
| `line`, `lines`, `frame`, `box`, `rays`, `circle`, `disc`, `fill`, `xcolor`, `mirror` | First a Disc and a drag, so that the tool has a picture. Then the tool with a colour and a brush, a drag and three taps in the picture. |
| `copy`, `swap`, `zoom` | The same, but these tools go to the picture without the long press. |
| `oops`, `erase` | A Disc and a drag, then Oops or Erase from the menu. |

## Replays

A replay on the default build uses `build/clean.prg`, the build of `src/main.asm`. The recordings load a program and set the PC, so they cannot start the loader. The checkpoint is the menu loop or the pad routine. The state is the current tool, the colour and the picture (`$6000-$7F3F`, `$C000-$C7D0`).

## Storage

A recording has no disk drive. Thus the Storage tests are run files with expected values. They start from `runs/storage/menu_with_disk.vsf`: the main menu, with the joystick hook of the recordings in memory and a copy of the Mayday! disk in drive 8. The disk in the snapshot has the eight pictures of the release.

The snapshot comes from an autostart of the disk image. Mayday! changed the disk code: it takes the device number from `$BA`, the device of the last load (switch `CRACK_MAYDAY`). A snapshot from a reset with the program loaded into memory did not work, because no load from drive 8 set `$BA`. Storage sent its commands to another device, and the CPU waited at `$EDD9` for an answer. v2 uses drive 8 directly.

| Test | What it does |
|---|---|
| `storage.json` | Get PIC D FARM, and expect its bytes in memory. Save it as PIC I. Get PIC A, then Get PIC I, and expect the bytes of PIC D again. Name & Save as PIC J with the name KOALA. Change Disk. |
| `init_disk.json` | Init Disk, `Y` to the question, the disk name PAINT. The disk of the snapshot is formatted. |

In memory the program keeps the bitmap at `$6000-$7F3F`. The rest of the Koala file is at `$C000-$C7D0`: the screen colours, the colour RAM and the background colour. The second expectation compares only the low 4 bits of the colour RAM bytes. The colour RAM keeps 4 bits, and the save writes other upper bits than the file of the disk has.
