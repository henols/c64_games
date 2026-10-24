# Koala Painter v2

*Koala Painter* is the paint program for the KoalaPad touch tablet. Audio Light wrote it, and Koala Technologies published it in 1983. The user moves a pen on the pad, selects a tool, a colour and a brush in a menu, and paints a multicolour picture. Storage saves the picture to disk and loads it again. This page is the entry page of version 2, the build of the 1984 cracks of TBC and MAM. TBC is the base release. The source in [src/](src/) assembles byte for byte to each release, and the default build has no copy protection and no crack code. Version 1 has its own project, [../v1/README.md](../v1/README.md), and [../README.md](../README.md) tells what the two versions share.

**Evidence.** **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

![The title picture that the loader shows at the start](docs/images/title.png)

The title picture of the file KTITLE: "Koala Technologies presents KoalaPainter by Audio Light". `build/clean_loader.prg` shows it as its start screen (**Observed**).

## The development

Version 1 and version 2 are two builds of the same source. An alignment of the two programs finds 343 blocks of equal bytes, and most code of version 2 is up to 351 bytes higher. Version 2 has more code. Examples are the idle tick, a working cell-colour cache, a Copy that clears its target and a cancel for an empty name in Storage (**Code**). Version 2 also keeps parts of the old fill loop at `$37D0`, `$3805`, `$3812`, `$3819` and `$3829`. These bytes have the structure of the version 1 code, and no code uses them (**Code**). Thus version 2 is the later build (**Conclusion**).

The bytes at `$46D0-$47FF` are a part of the symbol table of the assembler of the authors. Each entry has a name, a 16-bit value, a zero byte and the length of the next entry. The names are CR11 `$BA`, CR12 `$BB`, FC1-FC4 `$BC-$BF` and FCC `$7E40`, and a zero length byte follows (**Code**). The assembler left its table after the end of the program, and the save took that memory with it (**Conclusion**). The fragment of version 1 gives the 12 upper-case names of the menu flash, for example `SETFLASH` and `FLASHEM`. Version 2 uses the same names.

The title file KTITLE has 8080 code in its last bytes. [`title_unused_8080_code` `$5797`](src/data/title_picture.asm#L6) holds `MVI C,$10`, `CALL $0005`, `STA $1E5F` and `RET`, and the same code for C = `$11` to `$16`. These are the CP/M BDOS calls from "close file" to "make file" (**Code**). A CP/M machine thus built or copied the files, and the end of its disk buffer stayed in the file (**Conclusion**).

Script op 25 ends with `JMP $091B`. The JMP table at `$0900` has 9 entries, so `$091B` is the first byte after it, the cold start (**Code**). An earlier layout possibly had a tenth entry there (**Conclusion**). The details are on [../docs/development.md](../docs/development.md), and each difference between the versions is on [../docs/versions.md](../docs/versions.md).

## The copy protection

The protection runs one time, at the start. [`startup_script` `$1E1A`](src/script/picture_buffers.asm#L28) sets the background colours of the picture buffers. Then its op 9 at `$1E30` jumps to [`disk_protection` `$3A43`](src/protection/disk_protection.asm#L6). The routine first tests the RAM: `$8413` must keep `$01` and then `$00`. Then it sends "U1:5,0,1,1" and "U1:5,0,1,2" to the drive: block reads of track 1, sectors 1 and 2 (**Code**).

After each read, two checks test the command and the drive status, at `$3A65`, `$3A6A`, `$3A7B` and `$3A80`. `protection_result` at `$0850` gets the first digit of the status. A failed check jumps to `protection_failed`, which runs [`wipe_program_script` `$1E71`](src/script/picture_buffers.asm#L59). That script stops the interrupts and starts to write zero bytes over `$0900-$477F`: the program erases itself (**Code**).

TBC put NOPs over the four checks. The reads still run, but the result has no effect. The original bytes of the checks are in no release (**Code**). MAM changed U1 to W1, a command that the drive refuses, and put NOPs over the reads at `$3A59-$3A87` (**Code**). The switch `PROTECTION` is 0 by default and puts `$FF` at `$1E30`. The script then ends before op 9 (**Code**). No run executed the protection with a protected disk. The TBC start-up ran the reads with a copy of the Mayday! disk, and the program started (**Observed**). The details are on [../docs/protection.md](../docs/protection.md).

## Findings

- **The program reads RAM before it writes it.** The code reads RAM between `$4839` and `$5717` before it writes it, for example the variables at `$4F00-$4F7F`. `off_pad_beep_on` at `$4F6A` is one of them. With the power-on pattern of the C64 there (64 bytes `$00`, 64 bytes `$FF`), a replay is the same as the original. With zero bytes, the drawing differs (**Observed**). A test must write the pattern before the start, and the record files do this (**Observed**). See [docs/input.md](docs/input.md).
- **A press during the release wait has no effect.** The menu loop waits until no button is down, and then it clears the press flag. A press in the last instructions of this wait is lost (**Code**). The recordings must press after the wait, else the press does nothing (**Observed**). A fast player can thus lose a press in the menu (**Conclusion**). See [docs/input.md](docs/input.md) and [docs/menu.md](docs/menu.md).
- **The raster interrupt can lose a timer interrupt.** The raster path of the interrupt reads `$DC0D`, the interrupt flags of CIA 1 (**Code**). When the timer ends during a raster interrupt, this read clears the timer interrupt. Then the program loses one pad read, one button read and one clock tick (**Conclusion**). This can occur only while the menu shows. No run showed it. See [docs/input.md](docs/input.md).
- **Oops cancels a full visit to the picture, and it is not a redo.** The program copies the picture to the undo buffer only at the start of a command. Oops restores that copy and does not write the buffer (**Code**). Thus one Oops cancels all shapes of the last session, and a second Oops gives the same picture. The copy also runs before Mirror, so Oops after Mirror cannot cancel the drawing before Mirror (**Code**). See [docs/menu.md](docs/menu.md) and [docs/tools.md](docs/tools.md).
- **Swap tests the wrong register.** The touch test of Swap compares the A register with `$FF`, not the cursor X (**Code**). Thus a press can exchange the two pictures while the pen is off the pad, before the 16 reads of a long press. No run tested this case. See [docs/tools.md](docs/tools.md).
- **A fourth colour in a cell changes pixels that the brush did not touch.** A cell of 4 x 8 pixels has the background and 3 colour slots. A new colour takes the slot with the fewest pixels, and all pixels of that slot change colour (**Code**). The brush plot also gets a slot for its centre point. Brush 2 has no pixel there, so it can change a full cell where it paints nothing (**Conclusion**). See [docs/pixels.md](docs/pixels.md).
- **Copy reads the picture of the start of the session.** The source of Copy is the undo buffer, not the visible picture (**Code**). A copy of an area that got a copy in the same session thus gives the old content (**Code**). A user can expect the new content. See [docs/tools.md](docs/tools.md).
- **Storage has no limit of 16 pictures.** The directory read fills one slot for each file with the name prefix `$81` "PIC ", without a limit (**Code**). A disk with 17 such files puts slot 17 on the row of the Change Disk button (**Conclusion**). The list shows the files in the sequence of the directory. After a save and Change Disk, PIC I moved to slot 2 (**Observed**). See [docs/storage.md](docs/storage.md).

## How the program works

The loader of the release shows the title picture and loads the program. The cold start sets the timer interrupt and runs the start-up script. Then it draws the menu. From that point, the program is in one of three screens: the menu, the picture with a tool, or Storage. The interrupt reads the KoalaPad all the time. The main code reads the cursor position when a screen needs it.

The menu and the picture use the same screen memory at `$5C00` and the same colour RAM. Thus the menu saves the colours of the picture to `$C000-$C7D0` before it draws itself, and each tool restores them (**Code**).

Most screens are scripts. A script is a short byte code that sets registers, fills memory, copies the picture buffers and writes the texts of the menu. The interpreter runs a short 6502 routine for each opcode.

~~~mermaid
flowchart TB
  S["Start-up: timer, vectors, start-up script (cold_start)"] --> M["Menu loop: wait, hit test, select (menu_loop)"]
  I["Timer interrupt: pad, buttons, flash, tick (irq_handler)"] -.-> M
  I -.-> T
  M --> T["Tools: show the picture, draw (start_tool)"]
  M --> G["Storage: directory, save, get (storage_screen)"]
  T --> M
  G --> M
  S --> R["Script interpreter (run_script)"]
  M --> R
  T --> R
  G --> R
~~~

~~~mermaid
flowchart TB
  A["Title picture"] --> B["Main menu"]
  B --> C["Press on a cell: a tool, a colour or a brush"]
  C --> B
  B --> D["Lift the pen, press: the picture"]
  D --> E["Draw with the tool"]
  E --> F["Lift the pen, press: back to the menu"]
  F --> B
  B --> H["Storage: Save, Get, Name & Save"]
  H --> B
~~~

1. **The start runs one time.** [`cold_start` `$091B`](src/init/entry.asm#L23) stops the interrupts and sets CIA 1 timer A to 17034 cycles. That gives about 58 interrupts each second on a PAL C64. It sets the BRK vector to itself and the IRQ vector to the interrupt routine. Then it runs the start-up script and jumps to `start_main`, which builds the cursor sprites and calls the menu (**Code**).
2. **The interrupt reads the hardware.** [`irq_handler` `$0943`](src/irq/irq.asm#L6) has two paths. The timer path reads POT X and POT Y into buffers of 5 samples and reads the two pad buttons. It also flashes the menu cell and plays the idle tick. On the menu, the raster path makes three splits for the two character modes (**Code**).
3. **The menu loop selects.** [`menu_loop` `$0B85`](src/menu/menu.asm#L67) waits until no button is down. Then it finds the cell under the cursor in a hit table. A cell gives a code: a command, a colour or a brush. A long press with the pen off the pad starts the current tool (**Code**).
4. **Each tool has the same frame.** The command routine first copies the picture to the undo buffer. Each tool calls [`start_tool` `$0DD0`](src/tools/tool_start.asm#L6), which builds the label of the tool under the cursor and shows the picture. A long press jumps to [`tool_exit` `$1495`](src/tools/tool_exit.asm#L6), which saves the colours and draws the menu (**Code**).
5. **The scripts do the bulk work.** [`run_script` `$4361`](src/script/interpreter.asm#L6) gets the address of a script in A and Y. It has 38 opcodes, three stacks and a stack form of each opcode. The code calls it from 53 places (**Code**).
6. **Storage uses the drive.** [`storage_screen` `$2A09`](src/storage/storage_screen.asm#L6) reads the directory with the KERNAL serial routines and shows 16 slots. It saves and loads the Koala file of 10003 bytes: the bitmap and the colours (**Code**). A run loaded, saved, named and formatted with a disk in drive 8 (**Observed**).

![The main menu with Draw as the current tool](docs/images/menu.png)

The main menu after the start, from a run (**Observed**). Its hit table has 57 cells: 15 commands, Oops, Erase, 8 brushes and 32 colours (**Code**).

## The pages

| Page | Content |
|---|---|
| [docs/input.md](docs/input.md) | **The KoalaPad input.** The pad read, the smoothing, the buttons, the long press, the cursor sprites and the idle tick. |
| [docs/menu.md](docs/menu.md) | **The main menu.** The menu screen, the hit tables, the command codes, the flash and the undo copy before each command. |
| [docs/tools.md](docs/tools.md) | **The drawing tools.** How the user operates each of the 16 tools, and the facts that a user does not expect. |
| [docs/pixels.md](docs/pixels.md) | **Pixels, colours and buffers.** The pixel address, the colour slots, the dither, the brushes, the lines, the circles and the picture buffers. |
| [docs/scripts.md](docs/scripts.md) | **The script interpreter.** The byte code, its three stacks, the 38 opcodes and two scripts decoded by hand. |
| [docs/storage.md](docs/storage.md) | **Storage.** The disk menu, the directory read, the file names, the key entry and the format of a disk. |
| [tests/README.md](tests/README.md) | **The tests.** The recordings, the test hook of the joystick, the replays and the Storage tests. |
| [../docs/development.md](../docs/development.md) | **The development.** The traces of the authors in both versions. |
| [../docs/protection.md](../docs/protection.md) | **The copy protection.** The disk checks of both versions and the changes of each crack. |
| [../docs/releases.md](../docs/releases.md) | **The releases.** The disks, the files and the crack of each release. |
| [../docs/versions.md](../docs/versions.md) | **The versions.** Each difference between version 1 and version 2. |
| [../docs/koala_format.md](../docs/koala_format.md) | **The Koala file.** The layout of the picture file. |

## The releases

| Label | File | SHA-256 |
|---|---|---|
| TBC | `original/KoalaPainter.d64` (KMAIN and KTITLE) | `c2f29f1c2fe5cba6e4380b20853f7e6a4e015853c5e8302de1ea8fc13e216ce6` |
| MAM | `original/koala.d64` (KOALAPAINTER) | `97b874579164369b58c47c5db12436be3351fbebaa48e1a642bf7b7567a869fc` |

- **TBC** (Antiprotect of Terrestrial Breakin' Company). A BASIC menu asks for a joystick or a KoalaPad. The loader KP loads KTITLE, shows the title and loads KMAIN. In joystick mode it patches `$0999-$09A0` and `$09FC-$0A05`. The changes of the program are the NOPs over the four checks and the joystick routine at `$4800` (switch `CRACK_TBC`).
- **MAM.** A BASIC intro with German instructions loads PAINT.BOOT, which loads KTITLE and KOALAPAINTER. The changes of the program are the patches of the input and the protection (switch `CRACK_MAM`).

**TBC: the joystick routine at the end of KMAIN.** [`tbc_joystick` `$4800`](src/crack/tbc_joystick.asm#L6) is at `$4800-$4838`, after the end of the program. KP patches the interrupt to call it only in joystick mode. The KoalaPad mode never runs it (**Code**). The MAM file ends at `$47FF`. Thus no release gives the original bytes at `$4800-$4838`, and without `CRACK_TBC` the build has zero bytes there (**Code**). The recordings use this routine as their test hook for the pen position (**Observed**).

**MAM: code outside the program.** The patches of MAM call a joystick and keyboard routine at `$0829`, in the first page of the MAM file KOALAPAINTER (**Code**). The program of the knowledge starts at `$0900` and does not have that page. A build with `CRACK_MAM` thus needs the MAM file (**Conclusion**). The details of both cracks are on [../docs/releases.md](../docs/releases.md).

## The rebuild

**The base release.** The knowledge holds the memory of the TBC release in KoalaPad mode, captured at `$0900`. KMAIN is at `$0900-$4838`, and the title of KTITLE is at `$5718-$7F43`. The entry `$0900` is the first entry of the JMP table, a jump to the cold start (**Code**). `src/loader.asm` copies the segments into place, writes the pages `$0002-$03FF` of the capture and jumps to the entry (**Code**). The build of each release gives the bytes of that release (**Observed**, the generate check).

**The start screen.** `build/clean_loader.prg` first shows the title picture of KTITLE. Then it waits for a key, or for the fire button of joystick port 1 or 2. Set `START_SCREEN = 0` in `src/config.asm` to start the program at once. `LEFTOVERS = 1` builds the 540 bytes of the 16 leftover files in `src/leftovers/`. Each release has them.

**The switches.** `src/config.asm` holds the value of each switch, and `src/switches.asm` holds the values of each release.

| Switch | Kind | Default | Releases with it on |
|---|---|---|---|
| `PROTECTION` | protection | 0 | MAM, TBC |
| `CRACK_TBC` | crack | 0 | TBC |
| `CRACK_MAM` | crack | 0 | MAM |

**The build.** Run these commands in the project folder:

1. The default program, the clean build: `node ../../.claude/skills/c64-assembler/scripts/assembler.ts build src main.asm`. It writes `build/clean.prg`.
2. The default program with its loader: `build src loader.asm` with the same script writes `build/clean_loader.prg`. It starts with RUN and shows the title picture.
3. A release: add `--release TBC` or `--release MAM` to the command of step 1. It writes `build/release_TBC.prg` or `build/release_MAM.prg`.

**The tests.** The 16 recordings each do one tool of the menu. Each record file loads the TBC capture and writes a test hook first. The hook is the TBC joystick routine, because the emulator gives no paddle values. The replay runs the 16 recordings on the original and on `build/clean.prg`. At each checkpoint in the menu loop, the tool, the colour and the picture bytes are equal (**Observed**). The record files also write the power-on pattern into `$4839-$5717`, because the assembled program has zero bytes there.

The Storage tests start from a snapshot of the menu with a copy of the Mayday! disk in drive 8. The first test loads a picture, saves it, loads it again and saves it with a name. It expects the bytes of the file in memory. The second test formats the disk and expects an empty list with the new disk name (**Observed**). The details are in [tests/README.md](tests/README.md).

## Still open

- **The protection with a protected disk.** No run executed the checks with the original track 1. A run with an image of an original disk can show the drive status that the checks expect.
- **The pad noise.** The emulator gives no paddle values. A run with a real KoalaPad or with recorded POT values can show how often the smoothing ignores a read.
- **The lost timer interrupt.** A run with a breakpoint on the raster path and a test of the CIA 1 flags can show how often it occurs.
- **The stale cell cache.** A run can paint a cell, use Oops, and paint the same cell with a new colour.
- **Copy after Swap and Erase two times.** No recording used them. A recording with Swap and then Copy, and one with two presses on Erase and then Oops, can show them.
- **A save over a slot with a picture.** A run that saves into PIC A and reads the directory again can show the scratch command.

## The reference

[docs/reference/index.md](docs/reference/index.md)
