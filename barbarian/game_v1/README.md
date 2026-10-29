# Barbarian, part 2, V 05 05 87

Barbarian: The Ultimate Warrior is a sword-fighting game by Palace Software, 1987. This project is part 2 of the C64 game, the story game. The barbarian fights opponents 0 to 7, one bout each. Then the sorcerer Drax throws bolts at him, and the barbarian must reach princess Mariana. The program has the version text "V 05 05 87". The documentation is for the releases RDI and HTL. The base release is RDI, the crack of Raw Deal Inc. of 19 May 1987. These cracks are the reference files. Nobody examined a Palace disk or tape. Thus "identical" on these pages means identical to the RDI capture, not to the commercial original. The parts that the four projects share are on [../README.md](../README.md).

**Evidence.** **Observed** marks a fact that a run, a byte compare or the coverage of the recordings showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

![The attract demo in the dungeon](docs/images/demo_dungeon.png)

The attract demo in the dungeon: Drax and the princess stand in the two right windows, and two computer fighters fight at the right (**Observed**).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge of `game_v1`.
- A *frame* is one PAL screen, 1/50 of a second. A *pass* is one run of the main loop. The main loop has no frame wait, so a pass takes about 10 frames in the demo.
- A *bout* is one fight against one opponent. The *opponent* is `opponent_index`, 0-7. The *final stage* is the fight against the bolts of Drax after opponent 7.
- *Fighter 0* is player 1, with the joystick in port 2. *Fighter 1* is the computer. In the demo, the computer moves both fighters.
- *Part 1* is Combat Practice, the other program of the game. *V 05 10 87* is the later build of both parts.

## The development

The program has no credit text, no author name and no copyright line. The traces of the work are a version text, bytes from the RAM of the machines of the authors and unused code. Each trace is also in the other programs of the group, so the full story is on [../docs/development.md](../docs/development.md). (**Observed** byte search)

**The version text.** CTRL+V shows [`text_version` `$BAAF`](src/text/texts.asm#L17), "V 05 05 87", while V stays pressed. As month, day and year, the date is 5 May 1987. The program of FLT has "V 05 10 87", five days later. That build adds guards and corrections to this code, and nothing goes in the other direction. Thus this program is the earlier build (**Code**, **Conclusion**). The differences are on [../docs/versions.md](../docs/versions.md).

**The Commodore 128 code.** [`unused_ff80` `$FF80`](src/leftovers/leftover_ff80.asm#L6) holds 32 bytes of code at `$FFD0-$FFEF`. The first half is 6502 code that writes the C128 MMU registers `$FF00` and `$D505` and jumps to `$1100`. The second half is Z80 code that returns the bus to the 8502. No code of the game jumps there (**Code**). Part 1 of the same RDI crack has the RAM fill pattern at these addresses. Thus the bytes were in the file of part 2 before each group cracked it (**Observed** byte compare, **Conclusion**). **Conclusion:** part 2 was in the memory of a C128 in C64 mode before the save.

**The cartridge header.** [`cart_cold_start_vector` `$8000`](src/init/cartridge_header.asm#L6) holds the address `$8009` two times and the signature "CBM80". At a hardware reset, the KERNAL finds the signature and starts the game again without a new load (**Code**). The game fills `$0800-$FFFF`, much more than a cartridge of 16 KB holds (**Code**). **Conclusion:** the authors used the header to restart a hung game fast during the tests.

**The RAM of the machine.** The bytes after the last table, [`unused_cf20` `$CF20`](src/data/unused_cf20.asm#L6) to `$CFFF`, hold the pattern `$00 $FF` of RAM after power-on. `$FFF0-$FFFE` hold a copy of `$9FF0-$9FFE`, inside `freq_table`. The stored arena at `$E000-$E7FF` is a copy of 1 KB of screen RAM and 1 KB of colour RAM. Its colours have random high nybbles. **Conclusion:** the authors saved memory ranges of a running machine, not the exact length of the code. (**Observed** byte compare)

**The shared source.** Part 2 keeps the two-player code of part 1. Eight instructions read `two_players`, but part 2 writes only 0 there (**Code**). The text "PAUSED" and a text "000" are in the text table, but no code prints them. At `$84BA`, the bolt code loads `wait_counter`, and the next instruction loads A again (**Code**). **Conclusion:** the authors made both parts from one source and changed only a few lines for each part.

## The copy protection

Nobody examined a Palace disk or tape. RDI and HTL are cracks, and each crack starts the game with its own intro and unpacker. The game code reads no disk, no loader value and no special memory state (**Code**). Thus no project of the group has a PROTECTION switch. **Conclusion:** the loader of the commercial original held the protection, and the cracks replaced it. The chain of each crack is on [../docs/releases.md](../docs/releases.md).

The game needs one service of its loader: the colours. The game writes colour RAM in the fight area, the texts and the snake heads. A scene change also swaps the colours of the centre. Rows 0-1, row 6, rows 23-24, the side columns and the centre of the first picture keep the colours of the loader (**Code**). RDI copies 1000 bytes from `$B000-$B3E7` to colour RAM `$D800` and then jumps to `$8009` (**Observed**). After the start, the game uses `$B000-$B3E7` as a part of the work bitmap and its background copy (**Code**). **Conclusion:** the loader of the commercial original also filled colour RAM before the jump. No reference file has that loader.

The game also takes the phase of its CIA 1 timers from the loader. It starts the timers without a force load, so the timer values at the entry decide when the sound interrupts come (**Code**). The demo AI also reads these timers as its random source. A loader of rc.19 entered with other timer values, and its replays went one frame off after about 500 checkpoints (**Observed**, see [tests/README.md](tests/README.md)).

## Findings

- **A bug of the hit check reads records from the stored picture.** [`get_hit_record` `$8832`](src/combat/hits.asm#L96) shifts the record number into the high byte of a pointer. `check_attack_hit` clears that byte only once, before the loop over the hit list. Thus the second entry for the same defender pose reads 4 bytes at `$E3D9`, `$E3E1`, `$E3ED`, `$E7E1` or `$E7ED`. 14 list entries can do this (**Code**). The bytes there are screen and colour bytes of the arena that is not on screen. They can give a move, a sound or a score above the end of its table (**Conclusion**). No run showed the case. The default build must keep these bytes, so the knowledge marks `$E3E8-$E3FF` and `$E7E8-$E7FF` as data and not as leftovers. See [combat.md](docs/combat.md#a-bug-the-second-entry-for-a-defender-pose).

- **Both fighters can lose in the same pass.** [`check_hits` `$879B`](src/combat/hits.asm#L6) tests `bout_loser` only before the two attacks, not between them. When fighter 1 hits first and fighter 0 dies, `bout_loser` becomes `$80`. Then fighter 0 can still hit and write `$81` (**Code**). **Conclusion:** player 1 then wins the bout with 0 energy. No run showed the case. V 05 10 87 tests `bout_loser` before each attack. See [combat.md](docs/combat.md#the-winner-move).

- **A raster bit chooses the path of each bolt of Drax.** [`final_stage_attack` `$84C7`](src/story/final_stage.asm#L20) reads `$D012` and keeps bit 0. Path 0 needs a crouch or a roll, and path 1 needs a jump. The program checks the goal only at a bolt contact (**Code**). The recording `final_win` passed each bolt of path 0 with rolls and a crouch. In `final_lose`, a bolt of path 1 killed the player who stood still (**Observed**). A player cannot predict the bit. Thus the last bolt at the princess is a 50 % chance for a player who holds one move (**Conclusion**). All replays of the two recordings pass with the same paths (**Observed**). **Conclusion:** a replay repeats the cycle timing of the run, and with it the raster bit. See [final_stage.md](docs/final_stage.md#the-contact-and-how-to-pass-a-bolt).

  ![The final stage: YOUR END HAS COME](docs/images/final_stage_drax.png)

  The end of `final_lose`: Drax at the right, the player on the floor at the left, the princess in her window (**Observed**).

- **A bout of part 2 has no time limit.** Only two-player code reads the bout clock: `check_time_out`, `show_counter` and `add_time_bonus`. Part 2 writes only 0 into `two_players`, so this code never runs (**Code**). No recording executed it (**Observed** coverage). A bout thus ends only with a death or a decapitation. A player who does nothing starts the idle move after 255 frames, and opponent 7 then decapitates him (**Observed** in the recording `decapitation`). See [game_flow.md](docs/game_flow.md#the-bout-clock-and-the-time-bonus).

- **The pause does not stop the sprites.** [`read_keys` `$939B`](src/input/keyboard.asm#L6) writes A into `sprites_frozen` for F5, but A is 0 at both stores. Thus the goblin and the bolt of Drax move during the pause, and the frame timers count (**Code**). The text "PAUSED" exists, but no code prints it. **Conclusion:** the authors wanted a pause with frozen sprites and a text. V 05 10 87 freezes the sprites. See [game_flow.md](docs/game_flow.md#the-pause-and-the-version-text).

- **The computer uses a counter, not a random number.** In a one-player game, [`ai_choose_moves` `$870C`](src/ai/computer_moves.asm#L6) adds 1 to `ai_random` in each pass. The value selects 1 of 32 entries in a sorted column table. Thus opponent 7 uses column 0 for 14 passes in a row (**Code**). **Conclusion:** column 0 holds the strongest answer, one cycle takes about 6 seconds, and a player can learn its phase. Only the demo reads the CIA timers. A test that gives the same timer values repeats each demo fight (**Observed**: 7 replays with no pins). See [ai.md](docs/ai.md#the-random-source).

- **Music or effects, and both in the wrong pitch for PAL.** Bit 7 of `sound_off` set means music on and effects off, in spite of the name. F3 changes the bit (**Code**). [`freq_table` `$9EBB`](src/music/freq_table.asm#L6) holds the NTSC values, so each note is 3.7 % low on a PAL C64 (**Code**). The timer latches give round tick rates at 1 MHz, so the tempo is 1.5 % slow on PAL (**Conclusion**). The music stays in tune with itself (**Code**). See [sound.md](docs/sound.md#findings-in-the-code).

- **The fighter drawing skips the last line.** A fighter image is 63 lines high, but [`draw_fighter` `$8B59`](src/fighter/draw.asm#L6) stops after 62 lines (**Code**). It is not known if a pose has pixels in line 62. See [fighters.md](docs/fighters.md#drawing-into-the-work-bitmap).

## How the program works

The crack jumps to `$8009`. The start code prepares the memory, the VIC-II, the interrupts and the sound. Then the demo starts: two computer fighters fight in the throne room and in the dungeon. The demo is the title of the game (**Code**).

F1 starts the set-up of a one-player game, and F7 starts the first bout. Each bout starts with a walk-in and ends with a kill. After a win, the next opponent fights in the other scene. A lost bout ends the game. After the win against opponent 7, the final stage starts. Each end of a game returns to the demo (**Code**).

~~~mermaid
flowchart TB
  S["Start: memory, VIC-II, interrupts, sound (start)"] --> M["Main loop: one pass, no frame wait (main_loop)"]
  M --> K["Status texts and keys (read_keys)"]
  M --> A["Joystick and computer (ai_choose_moves)"]
  A --> F["Moves, poses and drawing in the work bitmap (animate_fighters)"]
  F --> H["Hits, energy, score, decapitation (check_hits)"]
  H --> E["End of a bout, goblin, next opponent (end_bout)"]
  E --> D["Final stage: bolts of Drax (final_stage_attack)"]
  D --> Q["Quit to the demo (quit_to_demo)"]
  I["Raster IRQ at line $FA: sprites and timers (raster_irq)"] -.-> M
  T["CIA 1 timers: music tick and effects tick"] -.-> M
~~~

1. **The start runs after each load and each quit.** [`start` `$8009`](src/init/init.asm#L6) selects the effects mode and continues into `restart`. That code removes BASIC and the KERNAL from the memory map, selects VIC bank 1 and sets the interrupts. `init_game_state` sets the demo with opponent 4 (**Code**).
2. **The main loop sets the pace.** [`main_loop` `$80BB`](src/main/main_loop.asm#L6) calls 23 routines in each pass and never returns. Each routine tests its own flags, so one loop serves the demo, the set-up, the bouts and the final stage. In the attract recording, `read_keys` ran 1495 times in about 15500 frames (**Code**, **Observed**).
3. **The player and the computer obey the same rules.** The joystick and [`ai_choose_moves` `$870C`](src/ai/computer_moves.asm#L6) give a joystick value. The same move tables change each value into a move. Thus the computer has the same moves as the player (**Code**).
4. **Each pass draws the fighters again.** [`animate_fighters` `$893A`](src/fighter/animate.asm#L6) builds each pose from 9 pieces and draws it into a work bitmap. The main loop then copies the work bitmap to the screen in one copy, so the fighters do not flicker (**Code**, **Conclusion**).
5. **The hit test compares two poses.** [`check_hits` `$879B`](src/combat/hits.asm#L6) looks up the pose of the attacker and the pose of the defender in tables. A hit record gives the distances, the reaction, the damage, the sound and the points (**Code**).
6. **The final stage runs inside the same loop.** [`final_stage_attack` `$84AC`](src/story/final_stage.asm#L6) and `set_end_figure` do nothing before the final stage. Then they move the bolt and the figures of Drax and the princess (**Code**).
7. **The interrupts keep the time.** [`raster_irq` `$951A`](src/irq/irq_handler.asm#L42) copies the sprite registers, moves the sprites and counts the timers at line `$FA`. CIA 1 timer B runs [`music_tick` `$991F`](src/music/tick.asm#L6), and timer A runs the effects and writes the SID (**Code**).

## The pages

| Page | Content |
|---|---|
| [docs/game_flow.md](docs/game_flow.md) | **The game flow.** The start, the main loop, the demo, the keys, the set-up, the bouts, the scenes, the final stage and the quit. |
| [docs/fighters.md](docs/fighters.md) | **The fighters.** The joystick, the 30 moves, the poses, the work bitmap, the sprite parts, the turn and the idle move. |
| [docs/combat.md](docs/combat.md) | **Combat.** The hit lists and records, the energy, the score, the decapitation, the goblin and the hit-record bug. |
| [docs/ai.md](docs/ai.md) | **The computer opponent.** The AI tables, the level of each opponent, the counter and the CIA timers of the demo. |
| [docs/final_stage.md](docs/final_stage.md) | **The final stage.** Drax and his bolts, the two paths, the princess, the end scene and the lose path. |
| [docs/graphics.md](docs/graphics.md) | **The graphics.** The bitmap, the scene change, the work bitmap, the colours, the sprites, the raster IRQ and the text output. |
| [docs/sound.md](docs/sound.md) | **Sound and music.** The driver on two CIA timers, the tune format, the music, the effects and F3. |
| [tests/README.md](tests/README.md) | **The tests.** The recordings, the writes that are only for a test, and the replays on the default build. |
| [../docs/development.md](../docs/development.md) | **The development.** The traces of the work of the authors in the four programs. |
| [../docs/versions.md](../docs/versions.md) | **The versions.** Part 1 against part 2, and V 05 05 87 against V 05 10 87. |
| [../docs/releases.md](../docs/releases.md) | **The releases.** The three cracks, their files, the crack chain and the Hotline trainer. |

## The releases

| Label | File | SHA-256 |
|---|---|---|
| RDI | `releases/rdi/Barbarian (Palace) [Raw Deal Inc.].t64` | `3dd5163e552a0992ee6ab2158e8056a58301dbf52588987864384452e77e09d4` |
| RDI | `releases/rdi/barbarian_part2_rdi.prg` | `ba39ad343eaeef9ed43fda3dc6abcd99d20834cbb9ca4ec877bf10d0552da491` |
| RDI | `releases/rdi/BARBARIAN.d64` | `190eba60b94c7099135e30500cb27be9ba9d5e80c431be492bd86a53f84f02f9` |
| HTL | `releases/hotline/Barbarian.D64` | `b24e7f4156b35c1a2b8884a4813fb104e55e0d3a2e51ae41f2e0f290fe9685a2` |
| HTL | `releases/hotline/barbarian_ii_hotline.prg` | `2f9b267c7f9abbeae8f990a01a12242cec39626e97df37465ead9c3669e1bedf` |

- **RDI** (Raw Deal Inc., 19 May 1987, CSDb 22600): the T64 holds PART 1 and PART 2. `barbarian_part2_rdi.prg` is PART 2 of the T64. The D64 holds only part 1, as BARBARIAN CP/RDI. RDI changed no byte of the game (**Observed**, **Conclusion**).
- **HTL** (Hotline, 1 June 1987, CSDb 94591): a recrack of the RDI file with a trainer menu. The game bytes differ from RDI in 26 bytes, and the two switches of Hotline hold all of them (**Observed** byte compare).

The FLT release of Fairlight holds the other build, V 05 10 87. Its part 2 is the project `game_v2` of the group, see [../README.md](../README.md#the-projects).

**The Hotline trainer has a bug.** The key T in the trainer menu writes `JSR $CF20` and `NOP` at `$8880` in [`apply_hit_damage` `$8845`](src/combat/hits.asm#L109). The routine at `$CF20` skips the energy loss of player 1. But when a hit animation runs already, the game branches to `$8882`, inside the new JSR. With the trainer, the CPU there runs illegal opcodes from the bytes of the patch (**Code**). Thus no fighter loses energy while its hit animation runs, also the computer (**Conclusion**). The intro text says that player 1 can lose only by a decapitation. That is correct, because the decapitation does not use the energy (**Code**).

**Hotline also removed the cartridge header.** HTL writes 0 over the 9 bytes at `$8000`, so a reset goes to BASIC and does not restart the game. HTL also changed the byte `$D5A8` from `$FA` to `$80`, in the stored bitmap of the second arena (**Observed** byte compare). Why Hotline changed this byte is not known. The details are on [../docs/releases.md](../docs/releases.md#htl-the-hotline-trainer).

## The rebuild

**The base release.** The knowledge holds the memory of RDI at the game entry `$8009`. It has three segments: `$0800-$080F`, `$0838-$AFFF` and `$B3E8-$FFFF`, 62448 bytes. The capture leaves out three areas of the crack: the intro screen `$0400-$07E7`, the colour copier `$0810-$0837` and its colours `$B000-$B3E7`. The game uses `$B000-$B3E7` only as work RAM for the fighters, so it needs no bytes there (**Observed**, **Conclusion**).

**The entry state.** `build/clean_loader.prg` is a packed program that starts with RUN. Its copier puts the segments into place and writes the entry state at `$0002-$03FF`. It sets the VIC-II registers of the entry state. Then it waits for a raster line, loads the CIA 1 timers and jumps to `$8009` (**Code**). The timer load keeps the phase of the timer interrupts of the capture. A loader without it made the replays go one frame off after about 500 checkpoints (**Observed**).

**The colour RAM defect.** The entry state in the knowledge holds the 1000 colours of colour RAM. The loader of c64-re-tools 2.7.0-rc.1 does not write them. Thus `build/clean_loader.prg` shows the pictures in wrong colours (**Observed**). The game itself writes colour RAM only in the fight area, the texts, the snake heads and the centre at a scene change. The replays compare RAM and not colour RAM, so they pass. This is a defect of the toolkit, not of the knowledge or the source.

**The switches.** `src/config.asm` holds the value of each switch, and `src/switches.asm` holds the values of each release. Each switch is 0 in the default build, so the default build gives the clean RDI program without the leftovers (**Code**).

| Switch | Kind | Default | Releases with it on | What it changes |
|---|---|---|---|---|
| `TRAINER` | trainer | 0 | HTL | `JSR $CF20` / `NOP` at `$8880-$8883`, and the trainer routine at `$CF20-$CF2B` |
| `CRACK_HOTLINE` | crack | 0 | HTL | 0 over the cartridge header `$8000-$8008`, and `$80` at `$D5A8` |
| `LEFTOVERS` | leftovers | 0 | RDI, HTL | 285 bytes in 5 files of `src/leftovers/` that nothing uses |

**The builds.** From the project folder, with the scripts of the c64-source and c64-assembler skills:

1. `source.ts generate --out src --loader` writes the source and `build/clean_loader.prg`, the default build. It loads with `LOAD"...",8` and starts with RUN.
2. `assembler.ts build src main.asm --release RDI --compare` builds the RDI bytes, and `--release HTL` builds the HTL bytes. Each release build has the same bytes as its capture in all segments (**Observed**).

**The tests.** Seven recordings with scripted input replay on `build/clean_loader.prg`: `attract`, `decapitation`, `fight`, `final_lose`, `final_win`, `keys` and `win_bout`. Claude wrote the steps, and no person played. Each replay stops at `main_loop` and compares the energy, the position and the move of both fighters. It also compares the opponent, the scene, the loser and the final stage flag. The rebuild gives the same values at all 3744 checkpoints, with no pins (**Observed**). The notes of each recording are on [tests/README.md](tests/README.md).

**The code that no run executed.** After all recordings, 29 code ranges with 197 instructions stayed unexecuted (**Observed** coverage). The main groups are:

- The two-player code of the bout clock, the time bonus and the end of a two-player game: 87 instructions in 4 ranges.
- The commands and options of the sprite motions, the sprite animations, the corner animations and the move sequences that no table uses. Examples are the sprite expansion and the Y limits of a sprite: 57 instructions in 11 ranges.
- The paths of the sound driver that no tune uses, for example the command `$F1` and the frequency slide: 34 instructions in 7 ranges.
- The key Q and two paths of F1 and of the quit: 8 instructions in 4 ranges. The paths change the scene and restore the torso sprites.
- Three rare cases: a second hit sprite, a head at X 256 or more, and the goblin at the head. They have 11 instructions in 3 ranges.

## Still open

- What does the game do when the hit-record bug reads a record from the stored picture? — A fight with fire + back at distance 2 against an opponent in pose `$3F`, with a watch on `move_ptr`.
- Can both fighters lose their last energy in one pass? — A run with the energy of both fighters at 1 and two attacks in the same pass.
- Does a pause in the final stage change the bolt contact? — A run that presses F5 while a bolt flies.
- How many frames does a pass take in a bout, not in the demo? — A run that logs the frame at each `main_loop` in the recording `fight`.
- What does a player see after the bug of the Hotline trainer at `$8882`? — A run of HTL with the trainer and a second hit during a hit animation.
- Does line 62 of a pose have pixels? — A script that reads the bottom pieces of each pose record.
- Does fighter 1 win more demo bouts, because it answers a new move in the same pass? — A count of `bout_loser` at each bout end in the recording `attract`.
- Did the Palace disk have a loader with a copy protection? — No reference file has the Palace loader. Only an image of an authenticated Palace disk can tell.

## The reference

[docs/reference/index.md](docs/reference/index.md)
