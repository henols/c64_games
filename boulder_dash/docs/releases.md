# The releases and their cracks

This page tells about the releases of Boulder Dash in the project. The game files of the cracks show two builds of the game: the Micro Fun build (v1) and the Statesoft build (v2). The project has one Micro Fun crack, the Statesoft tape and two Statesoft cracks. For each release, the page gives the files and tells how the release starts the game. It also tells which traces each crack left around the game.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge, with the label `v1:` or `v2:` of their project.
- A *release* is one disk image or tape image. Its *capture* is the memory of the game at its entry, without the boot of the crack.
- The *game file* is the file that holds the game at `$5000`.
- A *boot* is the small program of a crack that loads the game file and starts it.
- **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code or the bytes of a file only. **Conclusion** marks an interpretation.

## Two builds

CSDb lists 22 cracks of Boulder Dash for the C64. The game files of the cracks that we examined have one of two forms (**Observed**: a byte compare of the files):

| Build | Project | Game file | Cold start | Title screen |
|---|---|---|---|---|
| Micro Fun (US) | v1 | `$5000-$8D8E`, or `$5000-$8E7F` with 240 zero bytes more | `$8AB3` | "MICRO FUN PRESENTS" and the licence lines |
| Statesoft (UK) | v2 | `$5000-$8FFF` on the tape, `$5000-$9001` in the DDC crack | `$8E6A` | The First Star Software logo |

The title screen of the Micro Fun build has yellow lines with the name of the publisher:

![The title screen of the Micro Fun build](images/title_micro_fun.png)

The title screen of the Statesoft build has the logo of First Star Software in a bitmap at the bottom:

![The title screen of the Statesoft build](images/title_statesoft.png)

The data at `$5000-$66E7` is the same in both builds. The code of v2 is the code of v1, moved up by `$398` bytes. The title screen, its colours and the end of the game file are different (**Code**).

A forum post of LogicDeLuxe on boulder-dash.nl lists four C64 releases of the first Boulder Dash, with their memory ranges and entries. The forum post states these facts:

- Micro Fun: `$5000-$8B86`, entry `$8AB3`. First Star Software: `$5000-$8F48`, entry `$8E50`. Statesoft: `$5000-$8F3D`, entry `$8E69`. Electronic Arts (Super Boulderdash): `$4FF4-$8FC0`, entry `$4FF4`.
- Statesoft made its build from the First Star release. Statesoft removed duplicate tables, made the joystick poll faster and corrected the cave selection of caves E, I and M on levels 4 and 5.
- Micro Fun made its build from the Statesoft build. Micro Fun removed the First Star logo, changed the layout of the Boulder Dash logo and added the yellow text.

The ranges and the entries of our two builds agree with the lines of Micro Fun and Statesoft. The project has no First Star release and no Electronic Arts release, so we cannot examine the other claims (**Conclusion**).

## The releases of the project

The SHA-256 values come from sha256sum (**Observed**).

| Label | Build | File | SHA-256 |
|---|---|---|---|
| CHARSOFT | v1 | `v1/original/Boulder Dash.d64` | `ac00e1d5e184e4a70136556fb9d5070c99a35dc546d5af5bfafc628528ab91e6` |
| STATESOFT | v2 | `v2/original/Boulder Dash (1984)(State Soft).tap` | `6b2fd79a36084dc0a35474704879f005b87fb59cf529d69cb5ca915025a0a1bc` |
| DDC | v2 | `v2/original/BoulderDash-DonaldDuck&Co.d64` | `71bc27c343b8931948fe804684ceeeee02233fc5345268cec21836b25a975612` |
| ROAN | v2 | `v2/original/boulderdash-Roan-Cardboard5.d64` | `bf95c01dc2f55445676bc43f452c426a9f4ec2088c4c78bc2b7b3bce0eb93954` |

The project also has the files of the releases as PRG files. Each PRG file is a file of the disk image, byte for byte (**Observed**):

| Release | File | SHA-256 |
|---|---|---|
| CHARSOFT | `v1/original/boulder_dash_charsoft.prg` | `025704b3724c2de1d033ae3f05a004904a2804cac0c564ea39895e9e885fd346` |
| CHARSOFT | `v1/original/bd_obj_charsoft.prg` | `2396f331e86b415a665927a912d357c4b70c48170fa7d95e6d6645c4d390912a` |
| STATESOFT | `v2/original/Boulder Dash (1984)(State Soft).zip` | `a7581e14eb14a15b3769de25b07d440d0a983253c0562ba3c4abe4462ebb0554` |
| DDC | `v2/original/boulder_dash_ddc.prg` | `4f1fdec65c3cdced1ae776a42909d17dd633ce461c8f2bbd369d959d09f572b4` |
| DDC | `v2/original/boulder_1_ddc.prg` | `a631270bf0ebd2e8d5a65c82e706f8f8eedb1fcfc8fb5112d149568130282235` |
| ROAN | `v2/original/boulder_dash_roan.prg` | `25cf28c20038752fdcab97a2fc1fcc36b408049bba9734cfd8dcad1006a4dd73` |
| ROAN | `v2/original/bdboot_roan.prg` | `3cfb9183e20a2453ff7927414dd7c40617c9d82926cc78706f6a76efebd1041f` |
| ROAN | `v2/original/bd_roan.prg` | `ba74debd50c7c012c86ef62ba3dadfa276a17708e65987c19aea54bb914544c7` |
| ROAN | `v2/original/bd1_roan.prg` | `05637f7fa39d8f03706db81eeb205b7eb5f9f13bc33be685987a489168ad00cf` |
| ROAN | `v2/original/bde000_roan.prg` | `46a1280ca25e37b9f162fdd6f1b09e8fb597f93f227f0a7ed11500808e99ed4a` |

The zip file holds the TAP file, with the date 24 December 1996 (**Observed**). These are the four releases:

- CHARSOFT: CSDb release 185117, the Micro Fun build, cracked by Charsoft Inc.
- STATESOFT: the original tape of Statesoft, a TAP dump of 1996 from Planet Emulation. It is the only release without a crack.
- DDC: CSDb release 150877, cracked by Donald Duck & Co.
- ROAN: CSDb release 199178, cracked by Roan, on the disk Cardboard 5.

Each project has one base release, the program of its knowledge. CHARSOFT is the base release of v1. STATESOFT is the base release of v2 (**Code**: the releases of the knowledge).

## CHARSOFT: the Micro Fun build

The disk has the name "CHARSOFT INC." and two files (**Observed**):

| File | Blocks | Load range | Content |
|---|---|---|---|
| BOULDER DASH | 1 | `$0801-$08AE` | The BASIC boot |
| BD.OBJ | 63 | `$5000-$8D8E` | The game file |

The BASIC boot clears the screen and prints "CHARSOFT INC.", "BOULDER DASH...NOW LOADING" and "DISTRIBUTED BY CHARSOFT INC.". Then it loads BD.OBJ with `LOAD "BD.OBJ",8,1`. The load starts the BASIC program again, and a flag in the variable A skips the second load. Line 50 is `SYS 35507`. 35507 is `$8AB3`, so the boot jumps to [`v1:cold_start` `$8AB3`](../v1/src/init/cold_start.asm#L9) (**Code**: the BASIC lines).

### The text screen and the BASIC boot

The boot leaves two things in memory at the entry: its text screen at `$0400-$07E7`, and its BASIC program with its variables at `$0801-$08B5`. The game puts its cave map at `$0800-$0BBF` and shows its own screens at `$0C00` and `$2C00`. A run of the title and of cave A showed these facts (**Observed**):

- The game writes the cave map over `$0800-$08FF` in frame 5, before it reads a byte there. Thus the BASIC boot is lost.
- No instruction reads `$0400-$07E7`. The text screen stays in memory, but the game never shows it.

Thus the capture of v1 does not include the two areas. The game does not need a byte of the crack (**Conclusion**).

## The other Micro Fun cracks

We also examined the disks of four other Micro Fun cracks. Their game files are the same as BD.OBJ, byte for byte (**Observed**: a byte compare):

- Killer Kamakazi, distributed by Doctor Amoeba: the file BOUL, `$5000-$8E7F`. It is BD.OBJ with 240 zero bytes more at `$8D8F-$8E7F`.
- The menu disk of Jeff the Ripper: the same file BOUL, with a BASIC boot of its own.
- Lord Markus: the file BOULDER DASH, `$5000-$8D8E`, with the boot BOULDER.BOOT.
- Two more disks with the file BOULDER 1, `$5000-$8D8E`. Their boot is a BASIC program that Austro-Comp compiled.

The BASIC boots of Charsoft, Killer Kamakazi, Jeff the Ripper and Lord Markus all end with `SYS 35507` (**Code**: the BASIC lines). We did not decode the compiled boot of the last two disks.

### All cracks start at the cold start

Every Micro Fun crack that we examined starts the game at `v1:cold_start`. No crack changed a byte of the game file. The game file also holds the disk check [`v1:disk_protection` `$8CFF`](../v1/src/leftovers/leftover_8b86.asm#L61), which jumps to `v1:cold_start` at its end. A start at `$8AB3` skips the check (**Code**).

**Conclusion:** the original disk of Micro Fun most likely started the game at the disk check. The crackers only had to write a new boot with `SYS 35507`. All the cracks used the same simple method, so none of them has the original boot. The page [protection.md](protection.md) explains the check.

## STATESOFT: the original tape

The tape has a turbo loader. The border shows flashing stripes while the game loads. The loader shows the Statesoft loading picture: a multicolour bitmap at `$E000` with its screen at `$CC00`. Then it jumps to [`v2:cold_start` `$8E6A`](../v2/src/init/cold_start.asm#L9) (**Observed**: a run of the TAP file).

![The Statesoft loading picture of the tape](images/statesoft_picture.png)

The picture shows a map of the United States with the flag, the name "Statesoft" and "PRESENTS Boulder Dash (C)1984".

At the entry, the picture is still in memory. No run of the title and of cave A read `$CC00-$CFE7` or `$E000-$FF3F`, so the capture of v2 does not include them (**Observed**). The rebuild of v2 shows the picture as its start screen. The knowledge uses the entry state of the DDC boot. The tape capture had `$27` in `$01`. The PLAY key holds the cassette sense line low, and no loader can set that bit (**Observed**: a check of the entry state).

## DDC: Donald Duck & Co

The disk has an empty name and two files (**Observed**):

| File | Blocks | Load range | Content |
|---|---|---|---|
| BOULDER DASH | 1 | `$0302-$03C0` | The boot |
| BOULDER 1 | 65 | `$5000-$9001` | The game file and two more bytes |

The boot loads into the vector area of BASIC. The first two bytes that it loads put `$033C` into the vector at `$0302`, the main loop of BASIC. Thus BASIC starts the boot after `LOAD "BOULDER DASH",8,1` ends. The boot prints "LOADING BOULDER DASH!" and "CRACKED BY DONALD DUCK & CO!". Then it loads BOULDER 1 and jumps to [`v2:nmi_restart` `$8E69`](../v2/src/init/cold_start.asm#L6). That is a CLI, and then the cold start (**Code**: the bytes of the boot).

### The two bytes after the game file

BOULDER 1 has two more bytes, `$FF` and `$00`, at `$9000-$9001`. The bytes `$5000-$8FFF` are the same as the game of the tape (**Observed**: a byte compare). No instruction of the source refers to `$9000` or `$9001` (**Code**). Thus the capture of DDC does not include the two bytes. **Conclusion:** the crack saved two bytes too many, and the bytes have no effect.

## ROAN: a memory image

The disk has the name "ROAN" and five files (**Observed**):

| File | Blocks | Load range | Content |
|---|---|---|---|
| BOULDER DASH | 1 | `$0801-$08A1` | The BASIC boot |
| BDBOOT | 1 | `$033C-$037B` | The loader of BD |
| BDE000 | 33 | `$E000-$FFFF` and one byte more | The bitmap of the Statesoft picture |
| BD1 | 5 | `$CC00-$D000` | The screen of the Statesoft picture |
| BD | 154 | `$0801-$A000` | A memory image with the game |

The BASIC boot prints "\*\*\* LOADING BOULDER DASH \*\*\*". It loads BD1, BDE000 and BDBOOT, and calls BDBOOT with `SYS 828`. BDBOOT prints "CRACKED BY ROAN", loads BD to `$0801` and jumps to `v2:nmi_restart` at `$8E69` (**Code**: the BASIC lines and the bytes of BDBOOT).

### BD is a memory image

BD is not the game file of the tape. It holds all the RAM from `$0801` to `$A000` of a C64 that ran the game. The game at `$5000-$8FFF` is the same as the tape, byte for byte. Outside the game, BD has these traces of a run (**Observed**: a byte compare):

- `$3000-$33FF` holds the cave charset. The game copies it there from its data when it starts.
- `$9E00-$9FFF` holds the copy of the screen drawing routine. It differs from its source in the game in 4 operand bytes, which the routine changes when it runs.
- Many other pages hold the pattern `$FF $FF $00 $00`, the RAM pattern of a C64 after power on.

Thus Roan saved the memory of a machine after the game started (**Conclusion**). The capture of ROAN includes only the game range `$5000-$8FFF`.

### The picture without colour RAM

BD1 and BDE000 are the screen and the bitmap of the Statesoft picture. The release has no file for the colour RAM at `$D800`. In a multicolour bitmap, the colour RAM gives the colour of the bit pair `%11` of each cell. The release does not have these colours (**Code**).

BD1 is the same as `$CC00-$CFE7` of the tape. BDE000 is the same as the tape bitmap, except for the 32 bytes at `$FD30-$FD4F` (**Observed**: a byte compare with the capture of the tape picture). In BDE000, these bytes hold the vector table of the KERNAL ROM, from `$31 $EA` (`$EA31`) to `$ED $F5` (`$F5ED`). The tape has zero bytes there.

**Conclusion:** the KERNAL routine RESTOR copies the table at `$FD30` to `$0314`. It also writes each byte back to `$FD30`, and with the ROM in, that write goes to the RAM under the ROM. A reset or a RUN/STOP-RESTORE after the picture loaded thus put the ROM bytes into the RAM copy. In the picture, the 32 bytes are 4 cells of row 23, in columns 14 to 17.

The BASIC boot and BDBOOT write no register of the VIC-II. We did not find code in the release that shows the picture (**Code**).

## The builds of the releases

Each release has a build of its own. The build of a release sets the switches to the values of that release (**Code**: `switches.asm` of each project):

| Project | Build | LEFTOVERS | START_SCREEN | Bytes of main.asm |
|---|---|---|---|---|
| v1 | CHARSOFT | 1 | – | `$5000-$8D8E`, as BD.OBJ |
| v1 | default | 0 | – | `$5000-$8D8E`, with 521 zero bytes at `$8B86-$8D8E` |
| v2 | STATESOFT, DDC, ROAN | – | 0 | `$5000-$8FFF`, the same for the three releases |
| v2 | default | – | 1 | `$5000-$8FFF`, the same as the releases |

The command `assembler.ts build src main.asm --release <label> --compare` of c64-assembler gave PASS for CHARSOFT, STATESOFT, DDC and ROAN (**Observed**). The build of CHARSOFT is identical to `v1/original/bd_obj_charsoft.prg`. The three release builds of v2 and the default build of v2 have the same SHA-256, because the game bytes are the same (**Observed**). In v2, START_SCREEN changes only the loader: with 1, the loader shows the Statesoft picture before it starts the game (**Code**).

No build makes a boot of a crack, a text screen of a crack or the two bytes of DDC. These parts are not part of the game.

## Still open

- How do the two disks with the compiled boot start the game? — A run of each disk with a breakpoint at `$8AB3` and at `$8CFF`.
- Does any code of the Roan release show the Statesoft picture? — A run of the Roan disk that records each write to `$D011`, `$D018` and `$DD00`.
- Which event wrote the KERNAL vector table into the RAM copy of the picture? — The Roan release alone cannot tell this. A run that loads BDE000 and then does a reset can show if the 32 bytes change in the same way.
- What do the other cracks of CSDb change? — A byte compare of their game files with BD.OBJ and with the tape.
