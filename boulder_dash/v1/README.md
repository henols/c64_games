# Boulder Dash v1: the Micro Fun build

This is the Micro Fun build of Boulder Dash (Peter Liepa with Chris Gray, First Star Software, 1984), the release for the US market. The program of this project is the game file `BD.OBJ` of the Charsoft crack, `$5000-$8D8E`, with the cold start at `$8AB3`. The pages that the two builds share are in the [group folder](../README.md).

**Evidence.** **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

![The title of the Micro Fun build](docs/images/title.png)

## The development

The Micro Fun build is an edit of the Statesoft source. It has a new title picture with the yellow "MICRO FUN" and licence lines. It adds two colour routines for the title and has no First Star logo (**Observed**: a compare with v2). The end of the file holds a part of the symbol table of the developer's assembler. Its names have the addresses of this build: `OPTION`, `OUTWAL`, `TTSCEN`, `FREQ`, `BLUE`, `YELLOW`, `MUSPLY`, `MASQUE` and local loop names. For example, `MUSPLY` = `$83AC` is the title tune player (**Observed**). The knowledge keeps these names as comments at their routines. `FREQ` is the name of the base of the tune frequency table. The details are on [the development page](../docs/development.md).

## The copy protection

A disk check over the end of the symbol table, [`disk_protection` `$8CFF`](src/leftovers/leftover_8b86.asm#L61), reads track 18, sector 18 and expects drive error 23. With another status it writes zero bytes over `$7000-$70FF`, and the first cave stops at a BRK (**Code**). No release calls it: the Charsoft boot starts the game at `$8AB3`, after the check (**Observed**: the BASIC boot). The rebuild keeps the check in the leftovers and needs no switch. The details are on [the copy protection page](../docs/protection.md).

## Findings

- **A boulder in the magic wall stops the scan of that tick.** The handler leaves through `JMP play_diamond_sound`, so its RTS returns from the whole scan (**Observed** in a trace). See [docs/engine.md](docs/engine.md).
- **The snap with fire is in the code.** Fire and a direction take a diamond or dirt next to Rockford without a move (**Code**: no run used it). See [docs/rockford.md](docs/rockford.md).
- **The demo starts after two passes of the title tune.** It plays a table of joystick moves in cave A. It stops at the end of the table or at fire (**Observed** in the 3000 frames of the idle title). See [docs/title.md](docs/title.md).
- **The cave charset holds the title tune.** The 256 bytes of the tune notes are also characters `$00-$1F` of the cave charset at `$3000` (**Code**). See [docs/screen.md](docs/screen.md).
- **Levels 4 and 5 always start at cave A.** The options set the cave back to A when the level becomes 4. The forum post calls this the fix of the cave select bug (**Code**). See [docs/title.md](docs/title.md).

## How the program works

The cold start sets up the CIAs, the NMI vector and the raster interrupt. It copies the screen drawing routine to `$9E00` and builds the charsets. Then the top loop shows the title until the player presses fire, or until the demo starts. A game decodes a cave into the map at `$0850`, uncovers it and runs the main loop. Each tick of the main loop scans the cave once and moves each object. The raster interrupt scrolls the view, draws the screen that is not on show, plays the sounds and reads the keys.

~~~mermaid
flowchart TB
  A["Cold start: CIAs, NMI, copy of the drawing routine"] --> B["Top loop"]
  B --> C["Title, options, tune, demo"]
  B --> D["Start of a cave: decode, cover, uncover"]
  D --> E["Main loop: one scan of the cave in each tick"]
  E --> F["End of a life or of a cave"]
  F --> B
  G["Raster interrupt: splits, keys, clock, sound"] -.-> E
  G -.-> H["Drawing routine at $9E00: the hidden screen"]
~~~

~~~mermaid
flowchart LR
  T["Title"] -->|F1| O["Options"]
  O -->|fire| S["Cave starts, Rockford comes out of the inbox"]
  S --> P["Play: dig, collect diamonds"]
  P -->|enough diamonds, exit| B["Time bonus, next cave"]
  P -->|death or time out| L["Lose a life, fire to go on"]
  B --> S
  L -->|lives left| S
  L -->|no lives| T
~~~

1. **The start runs one time.** [`cold_start` `$8AB3`](src/init/cold_start.asm#L9) sets up the machine, then calls the top loop. RESTORE and F1 come back to it (**Code**).
2. **The top loop chooses the title or a game.** [`top_loop` `$8B2F`](src/init/cold_start.asm#L69) shows the title, starts a cave with `start_cave` and plays it (**Code**).
3. **The main loop sets the pace.** [`play_cave` `$88FB`](src/engine/play_loop.asm#L6) calls [`scan_cave` `$7DD9`](src/engine/cave_scan.asm#L39) until the cave ends. A tick takes about 8 frames on level 1 (**Observed** in the magic wall trace).
4. **The interrupt does the screen work.** [`irq_handler` `$8675`](src/irq/irq_handler.asm#L6) sets the raster splits, reads the keyboard rows and calls the frame work: the clock, the scroll, the animation and the sound (**Code**).
5. **The drawing routine runs from `$9E00`.** The cold start copies it there from `$7B58`. It draws the visible part of the cave buffer into the screen that is not on show, and the two screens change places (**Code**). It is in space bank1 of the knowledge.

## The pages

| Page | Content |
|---|---|
| [docs/main_loop.md](docs/main_loop.md) | **The main loop and the game flow.** The cold start, the top loop, the play of a cave, the end of a life, two players and the raster interrupt. |
| [docs/engine.md](docs/engine.md) | **The cave engine.** The scan of the cave and the behaviour of each element: boulders, diamonds, fireflies, butterflies, the amoeba and the magic wall. |
| [docs/rockford.md](docs/rockford.md) | **Rockford.** The joystick input, the moves, the push, the snap, the death, the birth and the animation. |
| [docs/screen.md](docs/screen.md) | **The screen.** The two screens, the cave buffer, the drawing routine at `$9E00`, the scroll and the reveal of a cave. |
| [docs/status_sound.md](docs/status_sound.md) | **The status line, the score, the time and the sound.** What the top row shows, the bonus life rules and the three SID voices. |
| [docs/title.md](docs/title.md) | **The title screen.** The title picture, the options, the tune, the demo and the score lines. |
| [../docs/cave_format.md](../docs/cave_format.md) | **The cave format.** The data of the 20 caves, shared with v2. |

## The releases

| Label | File | SHA-256 |
|---|---|---|
| CHARSOFT | `original/Boulder Dash.d64` | `ac00e1d5e184e4a70136556fb9d5070c99a35dc546d5af5bfafc628528ab91e6` |

- **CHARSOFT** (CSDb 185117): a BASIC boot `BOULDER DASH` prints a text screen, loads `BD.OBJ` and starts the game with SYS 35507 (`$8AB3`). The crack changed no byte of the game file. The game writes its cave map over the text and the BASIC boot before it reads them (**Observed**).

The other Micro Fun cracks on CSDb have the same game file and the same start address. The details are on [the releases page](../docs/releases.md).

## The rebuild

The base release is CHARSOFT: the program of the knowledge is its game file, captured at the cold start. The capture leaves out the text screen `$0400-$07E7` and the BASIC boot `$0801-$08B5` of the crack. The loader sets the zero page, the CIAs and the VIC-II as the boot left them at the cold start.

The knowledge has no switch: the crack changed no byte, and the program has no trainer and no correction. The leftovers are the symbol table and the disk check, `$8B86-$8D8E`. Only `LEFTOVERS = 1` builds them, so the default build has zero bytes there.

- The default build: `build src main.asm` of the c64-assembler skill gives `build/clean.prg`. `generate --loader` of the c64-source skill gives the verified loader `build/clean_loader.prg`, which starts with `RUN`.
- The release: `build src main.asm --release CHARSOFT --compare` gives the game file byte for byte (**Observed**).

Seven recordings of scripted play replay on the default build. The replays compare the state at each tick of the cave scan, 3900 ticks in all. The state is the cave map, the lives, the cave and the level. It also has the score, the diamonds, the exit flag, the end state and the position of Rockford. Each tick has the state of the original (**Observed**). The notes of the tests are in [tests/README.md](tests/README.md).

## Still open

- Code that no run executed: 32 ranges. Among them are the butterfly explosion and the amoeba that changes to diamonds or boulders. Others are a falling diamond in the magic wall, the end of the demo and the bonus life before an intermission. A recording of a longer play in the caves with these elements can reach them.
- Why the drawing routine runs at `$9E00`. The code fixes the address, but it does not tell the reason.

## The reference

[docs/reference/index.md](docs/reference/index.md)
