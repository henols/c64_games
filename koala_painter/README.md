# Koala Painter

Koala Painter is the paint program of the KoalaPad, a touch tablet for the C64 control port. Audio Light wrote it, and Koala Technologies sold it with the pad. The title picture says "Copyright 1983". The user draws with 16 tools on a multicolour picture of 160 x 200 pixels. The program keeps the pictures on disk in the Koala file format. This documentation covers two builds of the program: v1, in the Mayday! release of 2023, and v2, in the TBC and MAM cracks of 1984.

**Evidence.** **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

![The title picture of Koala Painter](v2/docs/images/title.png)

The title picture of the KTITLE file. The rebuilt loader shows it as the start screen.

## The versions

| Version | Releases | Entry |
|---|---|---|
| [v1](v1/README.md) | MAYDAY (base) | `$092F` (cold start `$091B`) |
| [v2](v2/README.md) | TBC (base), MAM | `$0900` (cold start `$091B`) |

Both builds come from the same source. An alignment of the two programs finds 343 blocks of equal bytes. Between the blocks the code changes, and the same code moves by -38 to +351 bytes, v2 address minus v1 address. The routines have the same names in the two knowledges, so `v1:read_cursor` and `v2:read_cursor` are the same routine at two addresses (**Code**).

A switch of a project changes bytes at fixed addresses. The second build changes the address in almost each operand, so a set of patches cannot hold the difference. Thus each build has its own project, with its own knowledge, source, tests and documentation (**Conclusion**). The routine library in [library/](library/) holds 48 routines of v2. 14 of them are in v1 byte for byte (**Observed**).

v2 is the later build. It adds an idle beep and a Copy frame that stays on screen. It also adds a cancel for an empty name in Storage and a test of the high byte when a shape moves. It also has leftovers of the old fill code that v1 still runs (**Conclusion**). The full list of the differences is on [docs/versions.md](docs/versions.md).

## The development

The developer left two fragments of a symbol table in the program files. Each sits after the end of the program, where the assembler kept its table in memory. In v1 at `$4571` the fragment holds 12 names of the menu flash code, for example `SETFLASH` and `FLASHEM`, with their v1 addresses. These names are now the names of these routines in both knowledges, for example [`v1:SETFLASH` `$0CC5`](v1/src/menu/flash.asm#L6). In v2 at `$46D0` the fragment holds other names: CR11, CR12 and FC1 to FC4, with values from `$BA` to `$BF` (**Code**).

The KTITLE file of v2 holds 105 bytes of 8080 code after the title routine. They call the CP/M entry `$0005` with the functions 16 to 22. These functions close, find, delete, read, write and make files. The C64 never runs them. Thus the developer made or copied the title file on a CP/M machine. The end of a disk buffer of that machine went into the file (**Conclusion**).

Other traces show an earlier layout of the program. Script opcode 25 ends with a jump to `$091B`. That address is the cold start now. It is also the byte after the 9 entries of the jump table at `$0900`. The details are on [docs/development.md](docs/development.md).

## The copy protection

Each build hides its disk check behind the script interpreter. The start-up script calls the check with opcode 9, so no JSR in the code points to it. The check first writes `$01` and `$00` to `$8413` and reads them back. Then it sends drive commands that read two blocks of the disk (**Code**):

- v1 sends `B-R` commands for track 33, sectors 5 and 6. Sector 5 must give a read error, and sector 6 must read without an error.
- v2 sends `U1` commands for track 1, sectors 1 and 2, and keeps the first digit of the drive status.

A failed check runs a script that writes zero bytes over the program, so the program deletes itself. TBC put NOPs over the checks of v2, and the reads still run. MAM changed `U1` to `W1`, a command that the drive does not know. Mayday! put NOPs over the call of the v1 check. No release has the original bytes of these places (**Code**). The rebuild of v2 has the switch `PROTECTION`, and its default build ends the start-up script before the check. The details are on [docs/protection.md](docs/protection.md).

## Findings

- **The joystick cracks do not work with a KoalaPad.** MAM always replaces the reads of the paddle registers with a joystick routine. TBC does the same when the user selects the joystick at its start. The note file of the Mayday! release of 2023 says that all old cracks fail with a KoalaPad, and that Mayday! started from an image of an original disk for this reason (**Code**). The TBC mode for a paddle or a touch tablet keeps the paddle reads, so its result with a real pad is still open. See [docs/releases.md](docs/releases.md).
- **Mayday! changed the drive number.** The disk code of v1 takes the device from `$BA`, the device of the last load. After a program load into memory, `$BA` is not 8, and Storage waits for an answer from a drive that is not there (**Observed**). The switch `CRACK_MAYDAY` gives back the fixed drive 8. See [v1/README.md](v1/README.md).
- **v2 reads RAM before it writes it.** The start-up of v2 does not set all of its variables in `$4F3E-$4F7D`, for example the idle beep flag `$4F6A`. With the power-on pattern of the C64 there, a replay of a recording on the rebuild is equal to the original. With zero bytes there, the drawing differs (**Observed**). A test of v2 must set this RAM. See [v2/README.md](v2/README.md).
- **A KoalaPad position is the pad value, smoothed.** The interrupt keeps 5 samples of each axis, and a 1-4-6-4-1 filter makes the cursor. A pad Y of `$E6` or more is "no touch", and no touch with a long press changes between the menu and the picture (**Observed**). See [v2/docs/input.md](v2/docs/input.md).
- **The pictures are standard Koala files.** A save writes 10003 bytes: the load address `$6000`, the bitmap, the screen colours, the colour RAM and the background. A round trip run gave back the same bytes, apart from the upper nybbles of the colour RAM (**Observed**). See [docs/koala_format.md](docs/koala_format.md).

## How the program works

The two builds work in the same way. The v2 pages describe each part, and [docs/versions.md](docs/versions.md) gives what v1 does differently.

1. **The start.** The cold start sets the IRQ, and the start-up script runs the disk check. Then the program builds the menu screen and the character set (**Code**).
2. **The interrupt.** A timer interrupt reads the pad and the buttons. Raster interrupts split the menu screen into text and colours (**Code**). See [v2/docs/input.md](v2/docs/input.md).
3. **The menu.** The menu loop finds the cell under the cursor in a hit table. A press runs the command, the colour or the brush of the cell (**Code**). See [v2/docs/menu.md](v2/docs/menu.md).
4. **The tools.** Each tool draws on the bitmap with a brush or with XOR band lines, and keeps 3 colours in each cell (**Code**). See [v2/docs/tools.md](v2/docs/tools.md) and [v2/docs/pixels.md](v2/docs/pixels.md).
5. **The scripts.** A byte-code interpreter with 38 opcodes draws the menu, the icons and the texts, and copies the picture buffers (**Code**). See [v2/docs/scripts.md](v2/docs/scripts.md).
6. **Storage.** The disk menu lists 16 pictures and loads, saves and names them (**Observed**). See [v2/docs/storage.md](v2/docs/storage.md).

## The pages

| Page | Content |
|---|---|
| [docs/development.md](docs/development.md) | **The development.** The symbol-table fragments, the CP/M bytes and the traces of older builds. |
| [docs/protection.md](docs/protection.md) | **The copy protection.** The disk check of each build, its failure and the changes of each crack. |
| [docs/versions.md](docs/versions.md) | **The versions.** Each difference between v1 and v2, with the addresses of both. |
| [docs/releases.md](docs/releases.md) | **The releases.** The files of MAYDAY, TBC and MAM, and what each crack changed. |
| [docs/koala_format.md](docs/koala_format.md) | **The Koala file.** The layout of a picture file, the file names and a decoded cell. |

## Still open

- No run used a protected disk. A run with a G64 image of an original disk can show the result of each check.
- The emulator gives no paddle values, so each recording uses a test-only joystick hook. A run with a mouse as the KoalaPad, for example in VICE, can test the pad code itself.
- The project does not show which build came first on the market. A dated original disk of each build can tell.
