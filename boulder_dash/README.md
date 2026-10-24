# Boulder Dash

Boulder Dash is the cave game of Peter Liepa with Chris Gray, published by First Star Software in 1984. Rockford digs through 16 caves and 4 intermissions, collects diamonds and escapes before the time runs out. This documentation is for two builds of the C64 game: the **Micro Fun** build (v1) and the **Statesoft** build (v2). Each build has its own byte-identical source.

**Evidence.** **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The versions

| Version | Publisher | Releases | Game file | Entry |
|---|---|---|---|---|
| [v1](v1/README.md) | Micro Fun (US) | CHARSOFT | `$5000-$8D8E` | `$8AB3` |
| [v2](v2/README.md) | Statesoft (UK) | STATESOFT (original tape), DDC, ROAN | `$5000-$8FFF` | `$8E6A` (tape), `$8E69` (cracks) |

The two builds are two assemblies of one source. The graphics and the cave data at `$5000-$66E7` have the same bytes at the same addresses. Then the title data differs. v1 has one title picture of 1000 bytes. v2 has the logo words and a First Star Software logo in bitmap mode, 1920 bytes. Thus the code of v2 starts `$398` bytes higher, and each 16-bit operand is different. Patches cannot hold this difference, so each build is a project of its own (**Observed**: a byte compare of the two files). The details are on [docs/versions.md](docs/versions.md).

The title of the Micro Fun build (v1):

![The title of the Micro Fun build](docs/images/title_micro_fun.png)

The title of the Statesoft build (v2):

![The title of the Statesoft build](docs/images/title_statesoft.png)

## The development

The end of each game file holds a part of the symbol table of the developer's assembler. The records have a name of up to 6 characters, two bytes `$A8 $00`, the value and a number. The values are the addresses of the routines of that build. In v1, `MUSPLY` is `$83AC`, the title tune player [`v1:play_title_tune` `$83AC`](v1/src/sound/title_tune.asm#L6), and `TTSCEN` is the title scene. In v2, `GMINIT` is `$8ADD`, the start of a new game, and `NXTPLY` is `$8B05`, the change of player. Local names carry a colon and numbered loops (`:LOOP1`, `:SK2`). The assembler saved a fixed memory range, so the end of the table from the last assembly stayed in each file (**Observed**: the bytes. **Conclusion**: how they got there).

A forum post of LogicDeLuxe on boulder-dash.nl lists four C64 releases by their memory range and entry. It states that Statesoft branched from the First Star release with a cleanup. It also states that Micro Fun branched from Statesoft. Micro Fun removed the First Star logo, changed the logo layout and added yellow text. Our two builds have the ranges and the entries of the post. The leftovers agree with its order: the v1 title has `:LOOP1` and then `:LOOP4` where v2 still has three loops (**Observed**: the ranges. **Conclusion**: the order).

Some parts run only in rare cases: the bonus life sparkle, the second joystick, the demo and the snap with fire. The coverage of the runs shows them. Two parts do nothing: a copy of the cave seed that the game never reads, and one test of `two_players` that is never true (**Code**). The details are on [docs/development.md](docs/development.md).

## The copy protection

The Micro Fun file holds a disk check, [`v1:disk_protection` `$8CFF`](v1/src/leftovers/leftover_8b86.asm#L61). It sends `U1:5,0,18,18` to the drive, which reads track 18, sector 18, and it expects the drive error 23. An original disk has a bad checksum in that block. With another status, the check writes zero bytes over `$7000-$70FF` and starts the game. The title still works, but the first cave stops at a BRK after about one second (**Code**).

No release calls the check. Each Micro Fun crack in the project and on CSDb starts the game at `$8AB3`, and both exits of the check jump there. The check lies over the end of the symbol table. Thus the original boot most likely started the game at the check, and the cracks changed only the start address (**Conclusion**). No release has the bytes of the original call, so the rebuild has no protection switch. The Statesoft build has no check in the game code. Its tape has a turbo loader (**Code**). The details are on [docs/protection.md](docs/protection.md).

## Findings

- **A boulder in the magic wall stops the scan of that tick.** The boulder handler leaves with `JMP play_diamond_sound`, and the RTS of that routine returns from the whole cave scan. The rest of the cave and the key test skip one tick. **Observed** in a trace of cave H: in the tick of the first boulder, the scan starts again without `check_game_keys`. A player sees the objects below the wall pause for one tick. See [v1/docs/engine.md](v1/docs/engine.md).
- **The protection wipe writes one page, not 32.** The loop counts 32 times but never changes the high byte of its pointer, so it writes `$7000-$70FF` 32 times. A wipe of 32 pages would also clear the routine itself (**Code**). See [docs/protection.md](docs/protection.md).
- **The random numbers come from the CIA timers.** `random_from_timers` mixes CIA 1 timer A and CIA 2 timers A and B. The amoeba, the boulder push, the reveal of a cave and the blink of Rockford use it. The caves themselves come from a seeded generator and are the same each time (**Code**, **Observed** in the cave tour). A test that compares a rebuild with the original must compare state that these numbers do not change (**Conclusion**). See [docs/cave_format.md](docs/cave_format.md).
- **The bonus life of an intermission comes before it.** `show_next_cave_text` reads the flag of the next cave. Thus "B O N U S  L I F E" shows after the caves D, H, L and P. A death or the end of the time in an intermission costs no life (**Code**). See [v1/docs/main_loop.md](v1/docs/main_loop.md).
- **A cave second is 60 frames.** On a PAL C64 that is 1.2 real seconds (**Code**, **Conclusion**). See [v1/docs/status_sound.md](v1/docs/status_sound.md).
- **The Statesoft picture of the Roan release has KERNAL bytes in it.** Its bitmap differs from the tape at `$FD30-$FD4F` only. The KERNAL routine RESTOR writes its vector table there, into the RAM under the ROM (**Observed**: the bytes. **Conclusion**: the cause). See [docs/releases.md](docs/releases.md).

## The pages

| Page | Content |
|---|---|
| [docs/development.md](docs/development.md) | **The development.** The symbol table leftovers, the order of the builds and the parts that do not run. |
| [docs/protection.md](docs/protection.md) | **The copy protection.** The disk check of the Micro Fun build, its effect and why no release runs it. |
| [docs/versions.md](docs/versions.md) | **The two builds.** How the code moved and how the title screens differ. |
| [docs/releases.md](docs/releases.md) | **The releases.** The cracks, the Statesoft tape, the files and their traces. |
| [docs/cave_format.md](docs/cave_format.md) | **The cave format.** The header, the object commands, the random fill and a worked example of cave A. |
| [v1/README.md](v1/README.md) | **The Micro Fun build.** How the program works, with the pages of each subsystem. |
| [v2/README.md](v2/README.md) | **The Statesoft build.** The start screen of the tape and the Statesoft title. |

## Still open

- Which disk did Micro Fun ship, and did its boot start at the disk check? — a dump of an original Micro Fun disk.
- How do the First Star and Electronic Arts releases differ from these two builds? — a capture of those releases and a compare with v2.
- What do the header bytes 0, 22 and 23 of a cave do? No code reads them — a compare with the caves of other BD1 releases.
