# Koala Painter v1

*Koala Painter* is the paint program for the KoalaPad touch tablet, by Audio Light for Koala Technologies, 1983. The player paints a multicolour picture of 160 x 200 pixels with 16 tools, and saves it on disk. This documentation is for v1: the program of the Mayday! release of October 2023 by TheRyk. Mayday! made the release from a G64 image of an original disk. The program fills `$0900-$7F3F`, and its entry is `$092F`. The group page [../README.md](../README.md) compares v1 with v2, the build of the 1984 cracks.

**Evidence.** **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The development

v1 and v2 come from the same source. An alignment of the two programs finds 343 blocks of equal bytes. Most code of v1 is up to 351 bytes lower than the same code in v2. The routines have the same names in the two knowledges, at different addresses (**Code**). v2 keeps unused remains of the fill loop of v1, so v2 is the later build (**Conclusion**).

**The original names.** `$4571-$462A` holds a part of the symbol table of the assembler of the authors. Each entry holds a name, its 16-bit value, a zero byte and the length of the next entry. The values are v1 addresses of the flash code of the menu, for example [`COLORCHK` `$0CB6`](src/menu/menu_0cb6.asm#L6) and `FLASHEM` at `$0CED` (**Code**). The assembler left its table in memory, and the save of the program took that memory with it (**Conclusion**). The knowledge uses these original names.

**Routines that v1 does not call yet.** `$1714-$1789` holds two routines that clear the pixels of one colour in each cell. No instruction of v1 calls them. v2 has the same routines, and its Xcolor tool calls them (**Code**). The authors thus wrote this code before the v1 build, and connected it only in v2 (**Conclusion**).

**An older layout.** Script op 25 ends with a jump to `$091B`. That address is the cold start, the first byte after the 9 entries of the jump table at `$0900`. No script uses op 25 (**Code**). An earlier layout probably had a tenth table entry at `$091B` (**Conclusion**).

The title code of the original file KTITLE at `$5718-$57FF` is not in v1: Mayday! replaced it with zero bytes. The CP/M bytes that v2 has there are thus not in v1 (**Code**). The details are on [../docs/development.md](../docs/development.md).

## The copy protection

The original start-up script [`startup_script` `$1DEF`](src/script/picture_buffers.asm#L28) sets the background of the picture. Then its op 9 calls [`disk_protection` `$393D`](src/leftovers/leftover_393d.asm#L6). The routine first writes `$01` and then `$00` to `$8413`, and checks that the byte keeps each value (**Code**).

Then the routine sets the KERNAL IRQ and NMI vectors, and opens file 5 with the name `#`, a buffer in the drive. It sends two block reads: `B-R: 5  0 33  5` and `B-R: 5  0 33  6`. The read of track 33 sector 5 must give a drive error, and the read of sector 6 must give none. Only an original disk has the bad sector 5 (**Code**).

A failed check runs the script `wipe_program_script` at `$1E30`. It starts to write zero bytes over `$1000-$4E7F`, without SEI. The script and the interpreter are in that range, so the program erases itself while it runs (**Code**). The details are on [../docs/protection.md](../docs/protection.md).

In the Mayday! release, three NOPs at `$0955` replace the call of the protection. Thus nothing calls [`start_script` `$0A81`](src/leftovers/leftover_0a68.asm#L11), the routine that runs the start-up script. The original bytes are in no release. Most likely they were `JSR $0A81`, because v2 calls its start-up script from the same place (**Conclusion**).

The rebuild therefore has no switch for the protection. The protection code is a leftover in the source, and only `LEFTOVERS = 1` builds it. No run executed it (**Code**). The details are on [../docs/protection.md](../docs/protection.md).

## Findings

- **No idle beep.** v2 plays a beep every 33 interrupts while the pen is off the pad. v1 has no SID code at all. Its timer interrupt [`irq_timer` `$09B2`](src/irq/irq.asm#L39) reads the pad, the buttons and the keys, and it changes the flash and the cursor colour (**Code**). A v1 session is silent. A test of v1 can ignore the SID (**Conclusion**). See [input.md](../v2/docs/input.md).
- **The move clamp compares only the low byte.** When the player moves a line or a box, the program adds the move to the far end. [`line_move_check_x_max` `$1136`](src/tools/line_tool.asm#L150) and `rect_move_check_x_max` compare only the low byte of the sum with the right edge. v2 checks the high byte first (**Code**). A far end past X 255 thus appears at X - 256, near the left edge, and not at the right edge (**Conclusion**). See [tools.md](../v2/docs/tools.md).
- **The Xcolor clear routines are dead code.** v1 Xcolor writes the new colour only into the colour tables of the cells. It does not call the two routines at `$1714-$1789` (**Code**). After an Xcolor to the background colour, the pixels thus keep their values 1-3, and they still use a colour slot of their cell (**Conclusion**). See [tools.md](../v2/docs/tools.md).
- **An empty name does not cancel.** [`storage_init_disk` `$2B2F`](src/storage/storage_screen.asm#L197) formats the disk also with an empty disk name. [`storage_name_save_slot` `$2C06`](src/storage/storage_screen.asm#L321) also saves a picture with an empty name. v2 cancels the action in both cases (**Code**). In v1, RETURN at the name prompt erases the disk. No run tried an empty name. See [storage.md](../v2/docs/storage.md).
- **The cell-colour cache matches only the pixel (6, 6).** [`load_cell_colours` `$15B6`](src/graphics/colour_slots.asm#L100) skips the read when the pixel is the cached pixel. Only `menu` writes the two cache bytes `$0800` and `$0801`, always with `$06`. The read of the colours does not write them (**Code**). v1 thus reads the colours of the cell at almost each call. The result is correct, and the cost is only time. A test can expect `$06` in the two bytes (**Conclusion**). See [pixels.md](../v2/docs/pixels.md).
- **Mayday! changed the device number.** The disk code takes the device number from `$BA`, the device of the last load, and not the constant 8. The release thus works with drives 8 to 11 (**Code**). The default build uses drive 8, as v2 does. A Storage test started from a reset with the program loaded into memory. No load from drive 8 set `$BA`, so Storage sent its commands to another device. The CPU then waited at `$EDD9` (**Observed**). The Storage tests thus start from a snapshot after an autostart of the disk image. See [tests/README.md](tests/README.md).
- **The protection call is gone.** The three NOPs at `$0955` disable the disk check, so a copy of the disk works. The Mayday! entry `$092F` also skips the KERNAL calls at the start of `cold_start`. No run executed `$091B-$092E` (**Observed**: the coverage of all runs). See [protection.md](../docs/protection.md).

## How the program works

The intro of Mayday! shows the title picture with its own code at `$0810`. After a press of fire on port 2, it jumps to `$092F`. The program then starts the timer interrupt and draws the main menu. The interrupt comes about 58 times each second (the CIA 1 latch is `$4289`). At each interrupt it reads the pad and the buttons (**Code**).

The player moves the pen on the pad, and a sprite cursor follows it. A press on a menu cell selects a tool, a colour, a brush or a command. With the pen off the pad, a long press of the button shows the picture with the current tool. The menu and the picture use the same screen memory. Thus the menu saves the colours of the picture before it draws itself, and a tool puts them back (**Code**).

~~~mermaid
flowchart TB
  IRQ["Timer interrupt: pad, buttons, flash, keys"] --> VARS["Cursor and button state"]
  VARS --> MENU["Main menu loop"]
  VARS --> TOOLS["The 16 tools"]
  MENU --> TOOLS
  MENU --> STORE["Storage screen"]
  SCRIPTS["Script interpreter"] --> SCREENS["Menu, labels, undo and swap copies"]
  MENU --> SCRIPTS
  TOOLS --> SCRIPTS
  TOOLS --> PIXELS["Pixels and cell colours"]
  PIXELS --> BITMAP["Picture: bitmap at $6000"]
  STORE --> DISK["KERNAL disk calls"]
~~~

~~~mermaid
flowchart TB
  A["Mayday! intro"] --> B["Title picture, fire on port 2"]
  B --> C["Main menu"]
  C -- "press on a cell" --> C
  C -- "pen off the pad, long press" --> D["Picture with the current tool"]
  D -- "long press" --> C
  C -- "Storage" --> E["Disk menu: Get, Save, Name & Save, Init Disk"]
  E --> C
  C -- "Zoom, Copy, Swap" --> D
~~~

1. **The start runs one time.** [`cold_start_irq_setup` `$092F`](src/init/entry.asm#L34) starts the CIA 1 timer interrupt and sets the IRQ vector. It prepares the menu screen, runs the script of a new picture and draws the menu (**Observed**).
2. **The interrupt reads the pad.** [`irq_handler` `$0969`](src/irq/irq.asm#L6) makes the raster splits of the menu screen. On a timer interrupt, it reads the pad position and the two buttons into the state of the cursor (**Observed**).
3. **The menu loop waits for a choice.** [`menu_loop` `$0B82`](src/menu/menu.asm#L67) tests the cursor against the cells of the menu. A long press with the pen off the pad goes to the picture (**Observed**).
4. **Scripts draw the screens.** [`run_script` `$4202`](src/script/interpreter.asm#L6) runs a small byte-code program. Scripts draw the menu and the labels, and they copy the picture for Oops and Swap (**Observed**).
5. **A tool paints the picture.** [`start_tool` `$0DCD`](src/tools/tool_start.asm#L6) shows the bitmap, and the tool reads the pen. [`plot_brush` `$178A`](src/graphics/plot_brush.asm#L6) plots the brush, and the cell colours decide the 2-bit value of each pixel (**Observed**).
6. **Storage uses the KERNAL.** [`storage_screen` `$29C7`](src/storage/storage_screen.asm#L6) reads the directory and shows 16 slots. Before each disk action it sets the KERNAL vectors, and after the action it sets the program IRQ again (**Observed**).

## The pages

v1 has no subsystem pages of its own. The pages of v2 tell the same mechanisms. Each row tells what v1 does differently. All differences are on [../docs/versions.md](../docs/versions.md).

| Page | Content |
|---|---|
| [../docs/development.md](../docs/development.md) | **The development.** The traces of the authors in the two builds, and why v2 is the later build. |
| [../docs/protection.md](../docs/protection.md) | **The copy protection.** The disk checks of v1 and v2, and how each crack disabled them. |
| [../docs/releases.md](../docs/releases.md) | **The releases.** The files of the Mayday!, TBC and MAM releases, and the changes of each crack. |
| [../docs/versions.md](../docs/versions.md) | **The versions.** Each difference between v1 and v2, with the addresses in the two builds. |
| [../docs/koala_format.md](../docs/koala_format.md) | **The picture file.** The 10003 bytes of a picture file. v1 uses the same layout as v2. |
| [../v2/docs/input.md](../v2/docs/input.md) | **The KoalaPad input.** v1 has no idle beep, and its long press test keeps the count of the pen off the pad. |
| [../v2/docs/menu.md](../v2/docs/menu.md) | **The main menu.** v1 has the same menu, and its symbol table gives the original names of the flash code. |
| [../v2/docs/scripts.md](../v2/docs/scripts.md) | **The script interpreter.** v1 has the same 38 opcodes, but its wipe script clears `$1000-$4E7F` without SEI. |
| [../v2/docs/tools.md](../v2/docs/tools.md) | **The drawing tools.** In v1, Copy shows its frame only for a moment, and Xcolor does not clear pixels. |
| [../v2/docs/pixels.md](../v2/docs/pixels.md) | **Pixels and colours.** v1 keeps the background colour at `$5BFF`, and its cell-colour cache almost never matches. |
| [../v2/docs/storage.md](../v2/docs/storage.md) | **Storage.** v1 sets the KERNAL vectors for each disk action, and it does not cancel on an empty name. |

## The releases

| Label | File | SHA-256 |
|---|---|---|
| MAYDAY | `original/koalapainter_myd.prg` | `74bf7dfc05af5d778b65a58a700b57cd1533b3d9f98cbe2e28955843465271fe` |

The disk image `original/koalapainter_myd.d64` holds the same file and eight sample pictures.

- **Mayday! (MYD!, 2023).** A cracktro with the tune "Up And Down 3" by Froyd, a note scroller by Achim, and its own title code at `$0810`. The program changes: three NOPs at `$0955`, the device number at four places, and zero bytes at `$5718-$57FF`.

The note of the release tells why Mayday! made it. The old cracks changed the input code for a joystick, so they did not work with a KoalaPad. Retroluzzer/EX tested the release on a real KoalaPad. The device change is a trace in the program: [`set_picture_file` `$2C33`](src/storage/storage_screen.asm#L342) loads the device number from `$BA` (**Code**). It matters for each test that loads the program without the disk. The other releases are on [../docs/releases.md](../docs/releases.md).

## The rebuild

**The base release.** The knowledge holds the memory `$0900-$7F3F` of the MAYDAY release, 30,272 bytes. The capture stopped at `$092F`, after the intro and the title picture of Mayday!. `build/clean_loader.prg` copies the program into place, sets the entry state of the capture and jumps to `$092F` (**Code**).

**The start screen.** `build/clean_loader.prg` first shows the title picture of the original disk. Then it waits for a key, or for fire on joystick port 1 or 2. The picture is in the program at `$5800-$7F3F`. Set `START_SCREEN = 0` in `src/config.asm` to start the program at once.

![The title picture of Koala Technologies and Audio Light](../v2/docs/images/title.png)

The title picture that the loader shows (the same picture as in v2).

**The leftovers.** No code uses 632 bytes in 17 ranges, for example the symbol table and the protection. The source keeps them in `src/leftovers/`. `LEFTOVERS = 1` builds them, and each release build has them.

**The switches.** `src/config.asm` holds the value of each switch. The default build uses drive 8, as v2 does.

| Switch | Kind | Default | Releases with it on | What it changes |
|---|---|---|---|---|
| `CRACK_MAYDAY` | crack | 0 | MAYDAY | the device of the last load in place of drive 8, at `$2C3E`, `$2C88`, `$39BA` and `$39CD` |

**The builds.** From the project folder, with the c64-assembler skill:

- `build/clean_loader.prg` is the clean program with the start screen. Start the program with this file. `source.ts generate --out src --loader` makes it again.
- `assembler.ts build src main.asm` gives `build/clean.prg`, the clean program without a loader. Its source is `src/main.asm`.
- `assembler.ts build src main.asm --release MAYDAY --compare` builds the release and compares it with the capture byte for byte.

**The tests.** 16 recordings each use one tool, from Draw to Erase. Each recording replays on the original and on `build/clean.prg`. At each checkpoint the tool, the colour and the picture are equal (**Observed**). The emulator gives no paddle values. Thus each recording puts a joystick routine into memory, and the steps write the pen position. Two Storage tests start from a snapshot with the Mayday! disk in drive 8. They get, save, name and save, read the directory and format the disk, and each expectation passes (**Observed**). [tests/README.md](tests/README.md) gives the details.

## Still open

- **The bytes at `$0955`.** Which call did Mayday! replace? A file of an uncracked original disk can tell.
- **The protection on a protected disk.** No run executed the check. A run with the G64 of an original disk can show the result of the two block reads.
- **The move clamp.** A recording that moves a line or a box far to the right can show the wrap.
- **The pad reads.** The runs used a joystick routine in place of the paddle registers. A run with paddle input in the emulator can test the real pad code.
- **An empty name.** A Storage run with RETURN at the name prompt can show the format and the save.

## The reference

[docs/reference/index.md](docs/reference/index.md)
