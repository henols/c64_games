# Barbarian: The Ultimate Warrior

Barbarian: The Ultimate Warrior is a sword-fighting game by Palace Software, 1987. This folder holds the rebuild of the C64 game, from three cracked releases. The C64 game has two programs. Part 1, Combat Practice, is a fight in an arena for one or two players. Part 2 is the story game: the barbarian fights eight opponents and then the sorcerer Drax, and frees princess Mariana.

Each part exists in two builds, V 05 05 87 and V 05 10 87. Thus this group folder has four projects, one for each program. Each project has a byte-identical source, a verified loader and recordings that replay on the default build. This is not the Barbarian of Psygnosis (1988).

**Evidence.** **Observed** marks a fact that an emulator run, a byte compare or the coverage of the runs showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

![The attract demo of part 2 in the throne room](game_v1/docs/images/demo_throne_room.png)

The attract demo of part 2 in the throne room. Drax sits on the throne, and the princess sits beside him (**Observed**).

## The projects

| Project | Program | Build | Releases (base first) | Entry |
|---|---|---|---|---|
| [practice_v1](practice_v1/README.md) | Part 1, Combat Practice | V 05 05 87 | RDI, HTL | `$8009` |
| [practice_v2](practice_v2/README.md) | Part 1, Combat Practice | V 05 10 87 | FLT | `$8009` |
| [game_v1](game_v1/README.md) | Part 2, the story game | V 05 05 87 | RDI, HTL | `$8009` |
| [game_v2](game_v2/README.md) | Part 2, the story game | V 05 10 87 | FLT | `$8009` |

The four programs share almost all code and data. Part 1 is part 2 without the final stage, with other pictures and with a two-player mode. The two builds of one part differ in small corrections. Most modules start at a new address in each program, but the order of the modules is the same. The page [docs/versions.md](docs/versions.md) gives each difference and each shift (**Code**).

`library/` holds 48 routines of `game_v1` as a routine library. The names of the other three projects came from a transfer of the `game_v1` names and a match against this library.

## The development

The programs hold no credit text. The only trace of the date is the version text that CTRL+V shows: "V 05 05 87" and "V 05 10 87". Read as month, day and year, these are 5 May and 10 May 1987. Both dates come before the cracks of 19 and 21 May 1987 (**Conclusion**). The later build also shows "WHY DID YOU PRESS ME" under the version text.

V 05 10 87 corrects V 05 05 87. It stops the sprites during a pause. It adds guards to the hit check, the damage, the score and the raster interrupt. It also changes AI rows, hit lists and the bout clock (60 s to 90 s). The graphics and the music data are the same in both builds (**Observed**, byte compare).

In each build, the authors made part 1 from the source of part 2. Part 1 keeps a dead copy of `set_end_figure`, the end-scene data and the end sprites of the story. Part 2 keeps the two-player code that it never uses (**Code**).

The page [docs/development.md](docs/development.md) tells the details. It covers the Commodore 128 code at `$FFD0-$FFEF` of part 2 and the cartridge header at `$8000`. It also covers the fill patterns of the RAM in the gaps, and the bugs.

## The releases

| Release | Group and date | Programs |
|---|---|---|
| RDI | Raw Deal Inc., 19 May 1987 | part 1 and part 2 of V 05 05 87 |
| HTL | Hotline, 1 June 1987: a recrack of RDI with a trainer | part 1 and part 2 of V 05 05 87 |
| FLT | Fairlight, 21 May 1987, crack by Strider | part 1 and part 2 of V 05 10 87 |

Each crack starts the game at `$8009` after its intro and after a copy of 1000 colour bytes into colour RAM. The game programs have no copy protection check. No release has a Palace loading picture. The Hotline trainer and the two changes of the Hotline crack are switches, `TRAINER` and `CRACK_HOTLINE`, off in the default build. The page [docs/releases.md](docs/releases.md) gives the files, the hashes, the crack chain and the traces of each crack.

## Findings

- **A bug of the hit check reads the wrong memory.** [`game_v1:check_attack_hit` `$87B9`](game_v1/src/combat/hits.asm#L25) clears the high byte of the record pointer only once, before the loop over the hit list. When an entry matches the pose but not the distance, the next entry for the same pose reads its record at a wrong address. 14 list entries can do this. In `game_v1` the wrong records are at `$E3D9-$E7F0`, in the screen and colour copy of the second picture. The knowledge records these reads, so the default build keeps those bytes (**Code**). Both builds and both parts have the bug. In part 1 most wrong reads go to the I/O area at `$DExx`, where they get open-bus values.
- **Two fighters can lose in the same pass in V 05 05 87.** The check tests `bout_loser` only once for both attacks of a pass. V 05 10 87 tests it for each attack (**Code** / **Conclusion**).
- **The Hotline trainer has a bug.** A branch of the hit code jumps into the middle of the trainer patch. There the CPU runs illegal opcodes, and no fighter loses energy while its hit animation runs (**Code**). See [docs/releases.md](docs/releases.md).
- **Part 2 has a dead two-player mode.** Part 2 writes only 0 to `two_players`, so its bout clock, time out and time bonus never run. A bout of part 2 has no time limit (**Code**, **Observed** in the coverage).
- **A raster bit chooses the path of Drax's bolt.** In the final stage, bit 0 of the raster line at the throw selects one of two bolt paths. One path needs a crouch or a roll, and the other path needs a jump (**Code** / **Observed** in the recordings `final_win` and `final_lose`).
- **The default build shows wrong colours.** The game writes only some areas of colour RAM. Each crack copies the rest before the jump to `$8009`. The entry state in the knowledge has these colours, but the loader of c64-re-tools 2.6.0-rc.20 does not write them. Thus `build/clean_loader.prg` shows the pictures in the wrong colours (**Observed**). The replays still pass, because they compare RAM, not colour RAM. This is a defect of the toolkit, not of the knowledge.

![Part 1 in the demo: the arena with the sunset](practice_v1/docs/images/practice_sunset.png)

Part 1 in the demo: the arena with the sunset (**Observed**).

## The pages

| Page | Content |
|---|---|
| [practice_v1/README.md](practice_v1/README.md) | **Part 1, V 05 05 87.** The entry page of Combat Practice of the RDI and HTL releases. |
| [practice_v2/README.md](practice_v2/README.md) | **Part 1, V 05 10 87.** The entry page of Combat Practice of the FLT release. |
| [game_v1/README.md](game_v1/README.md) | **Part 2, V 05 05 87.** The entry page of the story game of the RDI and HTL releases, with the subsystem pages. |
| [game_v2/README.md](game_v2/README.md) | **Part 2, V 05 10 87.** The entry page of the story game of the FLT release, with the subsystem pages. |
| [docs/development.md](docs/development.md) | **The development.** What the four programs tell about the work of the authors. |
| [docs/versions.md](docs/versions.md) | **The versions.** Each difference between part 1 and part 2, and between the two builds. |
| [docs/releases.md](docs/releases.md) | **The releases.** The three cracked releases, their files and the traces of each crack. |

## Still open

- Did the original Palace disk have a loader with a copy protection? No release has it. Only an image of the original disk can tell.
- What did the authors use the Commodore 128 code and the cartridge header for? The code does not tell.
- Does another release on CSDb hold a third build of the game?
