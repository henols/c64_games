# Tests of Koala Painter v2

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Each record file loads `program/tbc_0900.prg`, the memory `$0900-$7F43` of the capture of the TBC release (`KMAIN` and `KTITLE` as the TBC loader leaves them). It starts the program at its cold start `$0900`, and does one tool of the main menu. `all_tools` is older: it loads `original/kmain_tbc.prg` (the `KMAIN` file of the TBC disk) only.

Koala Painter reads only a KoalaPad: the position from the paddle registers `$D419`/`$D41A`, and the two buttons from joystick port 1. The emulator gives no paddle values. Thus each record file writes these bytes before it starts the program. Only the recordings have them. The project knowledge, the source and the builds do not.

| Address | Bytes | Why |
|---|---|---|
| `$0999` | `10 EA EA EA EA EA EA EA` | The button test reads the fire bit of port 1. These are the bytes that the TBC loader `KP` writes in its joystick mode. |
| `$09FC` | `20 00 48 EA EA EA EA EA EA EA` | The IRQ calls the TBC joystick routine at `$4800` in place of the paddle reads. These are also the bytes of `KP`. |
| `$1E30` | `FF` | The start-up script stops before its jump to the disk protection at `$3A43`. A recording has no disk drive, and the protection reads track 1 of the disk. |
| `$4800` | 53 bytes | The TBC joystick routine. The default build has zero bytes there (switch `CRACK_TBC`), so the record file writes the routine itself. |
| `$4839-$5717` | 3807 bytes | The power-on pattern of the C64 RAM (64 bytes `$00`, 64 bytes `$FF`), as the capture has it. The program reads variables in this range before it writes them, and an assembled program has zero bytes there. With the pattern, the original and the rebuild start in the same state. |

The steps move the cursor with writes to the position of the TBC routine. `$4833` is the pad Y and `$4834` is the pad X. The program converts the pad position to the screen. Screen X = (pad X - 20) * 4 / 5, and screen Y = pad Y - 20. A pad Y of `$E6` or more is "no touch". Fire on port 1 is the pad button.

The picture screen comes from the menu with "no touch" and a long press of the button. The same press goes back to the menu. Each step waits for the menu loop before it presses. A press during the release wait of the menu loop does not change the screen.

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

A recording has no disk drive. Thus the Storage tests are run files with expected values. They start from `runs/storage/menu_with_disk.vsf`: the main menu, with the joystick hook of the recordings in memory and a copy of the Mayday! disk in drive 8. The disk in the snapshot has eight pictures. The start-up of the snapshot ran the disk protection with that disk: the TBC release ignores its result.

| Test | What it does |
|---|---|
| `storage.json` | Get PIC D FARM, and expect its bytes in memory. Save it as PIC I. Get PIC A, then Get PIC I, and expect the bytes of PIC D again. Name & Save as PIC J with the name KOALA. Change Disk. |
| `init_disk.json` | Init Disk, `Y` to the question, the disk name PAINT. The disk of the snapshot is formatted. |

The Storage list shows the pictures in the sequence of the directory. A new picture can go into an early directory entry, and the list shows it there only when Storage reads the directory again.

In memory the program keeps the bitmap at `$6000-$7F3F`. The rest of the Koala file is at `$C000-$C7D0`: the screen colours, the colour RAM and the background colour. The second expectation compares only the low 4 bits of the colour RAM bytes. The colour RAM keeps 4 bits, and the save writes other upper bits than the file of the disk has.
