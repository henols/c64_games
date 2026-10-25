# Barbarian, part 1, V 05 10 87

Barbarian: The Ultimate Warrior is a sword-fighting game by Palace Software, 1987. This project is part 1 of the C64 game, Combat Practice. One player fights the computer at levels 0 to 7, or two players fight each other with a bout clock. Part 1 has no story and no final stage. The program has the version text "V 05 10 87". The documentation is for the release FLT, the crack of Fairlight of 21 May 1987. The parts that the four projects share are on [../README.md](../README.md).

**Evidence.** **Observed** marks a fact that a run, a byte compare or the coverage of the recordings showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

![The arena with the sunset, from build V 05 05 87](../practice_v1/docs/images/practice_sunset.png)

The arena with the sunset in the demo. The screenshot comes from `practice_v1`, build V 05 05 87. The picture bytes are the same in this build (**Observed** byte compare, see [../docs/development.md](../docs/development.md#the-pictures)).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge of `practice_v2`.
- A *frame* is one PAL screen, 1/50 of a second. A *pass* is one run of the main loop. The main loop has no frame wait, so a pass takes about 10 frames in the demo.
- A *bout* is one fight from the walk-in to the kill. The *level* is `opponent_index`, 0-7. It selects the AI tables of the computer.
- *Fighter 0* is player 1, with the joystick in port 2. *Fighter 1* is player 2 with the joystick in port 1, or the computer.
- *1PLR* and *2PLR* are the mode texts of a one-player game and a two-player game.
- *Part 2* is the story game, the other program of the game. *V 05 05 87* is the earlier build of both parts.

## The development

The program has no credit text, no author name and no copyright line. The traces of the work are a version text, unused code of part 2 and bytes from the RAM of a machine. The other programs of the group have most of these traces too, so the full story is on [../docs/development.md](../docs/development.md). (**Observed** byte search)

**The version text.** CTRL+V shows [`text_version` `$B967`](src/text/texts.asm#L17) while V stays pressed. The first line is "V 05 10 87", and a second line at column 10, row 18 says "WHY DID YOU PRESS ME" (**Code**). As month, day and year, the date is 10 May 1987, eleven days before the FLT crack. The programs of RDI and HTL have "V 05 05 87" and no second line (**Observed**). This build adds guards and corrections to the code of V 05 05 87, and no change goes in the other direction. Thus this program is the later build (**Code**, **Conclusion**). The differences are on [../docs/versions.md](../docs/versions.md).

**Part 1 comes from the source of part 2.** [`set_end_figure` `$8CC5`](src/leftovers/leftover_8cc5.asm#L6) is the routine of part 2 that sets the sprites of the end of the story. Nothing calls it in part 1. Each data address in it is `$16A` lower than in part 2, and this is the shift of the data of part 1 (**Observed** byte compare). [`end_scene_ptrs` `$CB84`](src/leftovers/leftover_cb84.asm#L6) and the bolt tables of Drax follow the same rule (**Observed**). Part 1 also holds the texts `YOUR END HAS COME` and `THANKS BIG BOY`. The 13 end sprites and the swaps of the end scene are also there (**Code**). **Conclusion:** the authors assembled part 1 again from the source of part 2 after they removed the final stage and its calls. They did not remove the data and the routines that only the final stage needs.

**The cartridge header.** [`cart_cold_start_vector` `$8000`](src/init/cartridge_header.asm#L6) holds the address `$8009` two times and the signature "CBM80". At a hardware reset, the KERNAL finds the signature and starts the game again without a new load (**Code**). RESTORE does nothing, because the NMI vector points to an RTI (**Code**). The game fills `$07E8-$FFFF`, much more than a cartridge of 16 KB holds. **Conclusion:** the authors used the header to restart a hung game fast during the tests.

**The RAM in the gaps.** The bytes in the gaps of this program differ from the other three programs. [`unused_ce07` `$CE07`](src/leftovers/leftover_ce07.asm#L6) holds 9 bytes `$FF` and then `$A3` up to `$CEFF`, and `$CF22-$CFFF` also holds `$A3`. `$FC04-$FC07` hold the `$00 $FF` fill pattern of RAM after power-on, and `$FC08-$FC3F` are 0. [`unused_ff80` `$FF80`](src/leftovers/leftover_ff80.asm#L6) is 0 up to `$FFF9` (**Observed** byte compare). Both programs of V 05 05 87 have the fill pattern in these areas, and part 2 of this build has it at `$FC04` and `$FF80`. Part 2 of both builds also has Commodore 128 code at `$FFD0-$FFEF`, and part 1 has none (**Observed**). **Conclusion:** the two parts of V 05 10 87 came from different RAM states, or the FLT unpacker wrote these bytes.

**The copies of the stored arena.** The forest arena waits at `$D000-$E7FF` while the sunset shows. `$E3E8-$E3FF` are equal to `$47E8-$47FF`, the end of the screen of the game. `$E7E8-$E7FF` hold the 24 colour bytes after the visible colours, with random high nybbles (**Observed** byte compare). **Conclusion:** the authors saved the second picture as a copy of 1 KB of screen RAM and 1 KB of colour RAM.

## The copy protection

The project has no original Palace disk. FLT is a crack, and it starts the game with its own intro and unpacker. The game code reads no disk, no loader value and no special memory state (**Code**). Thus the project has no PROTECTION switch. **Conclusion:** the original Palace loader held the protection, and the crack replaced it. The chain of the crack is on [../docs/releases.md](../docs/releases.md#the-chain-of-a-crack).

The game needs one service of its loader: the colours. The game writes colour RAM only in some areas, for example the fight area and the texts. A scene change also swaps the colours of the centre of the picture (**Code**). The FLT crack copies 1000 bytes from `$0400-$07E7` to colour RAM `$D800` with code at `$CF00-$CF21`. Then it jumps to `$8009` (**Observed**). **Conclusion:** the original loader also filled colour RAM before the jump.

The game also takes the phase of its CIA 1 timers from the loader. It starts the timers without a force load, so the timer values at the entry decide when the sound interrupts come (**Observed**, see [tests/README.md](tests/README.md#replays)). The demo AI also reads these timers as its random source (**Code**).

## Findings

- **The length of an F1 press selects one or two players.** [`read_keys_f1_clock` `$92AE`](src/input/keyboard.asm#L63) toggles `two_players` in each pass that finds F1 pressed. The routine has no edge test. A press that one pass finds gives 2PLR, and a press that two passes find gives 1PLR (**Code**). The recordings show the effect. The F1 press of 10 frames in `decapitation`, `fight` and `win_bout` gave two-player games. The F1 press of 3 frames in `two_decap`, `two_players` and `two_win` came before the first key read, so no pass found it (**Observed**). Thus most recordings played another mode than their names say. A record file for part 1 must check the mode text after F1 (**Conclusion**). See [game_flow.md](docs/game_flow.md#the-set-up-one-or-two-players) and [tests/README.md](tests/README.md#recordings).

- **The joystick of player 2 acts as keys.** The joystick in port 1 uses the same lines of CIA 1 as the keyboard columns. Left looks like CTRL, right looks like F7, and fire looks like F1 (**Code**). In the recording `two_players`, no pass found the F1 press. The fire button and the right direction of player 2 started the set-up and the game in its place (**Observed**). Thus player 2 can start a game and change the number of players before F7 (**Conclusion**). See [game_flow.md](docs/game_flow.md#the-keys).

- **A one-player game has no end.** After a win, `end_bout` increments the level and changes the scene. At level 7, the level stays 7, and the player fights level 7 again until he loses. The score stays from bout to bout (**Code**). In part 2, the same jump starts the final stage. No recording of this project executed the end of a one-player bout (**Observed** coverage). See [game_flow.md](docs/game_flow.md#a-one-player-game).

- **A two-player bout ends only with a kill.** [`check_time_out` `$830A`](src/combat/time_out.asm#L6) starts a time-out at time 0. Both fighters walk home, get energy 12 and start the bout again with a new walk-in. The scores stay (**Code**). The recordings `fight` and `two_players` executed each step of the time-out (**Observed** coverage). After the kill, the winner gets 10 points for each second left on the clock of 90 seconds (**Code**). See [game_flow.md](docs/game_flow.md#the-bout-clock-and-the-time-out).

- **No run of this project showed a decapitation.** `check_decapitation_begin` and the goblin code for the head did not run in any recording (**Observed** coverage). The recording `decapitation` became a two-player game with no input (**Observed**). With no input and no computer fighter, no fighter attacks (**Conclusion**). The decapitation code is the code of part 2, `$16C` lower (**Code**). Thus the replays of this project do not test the decapitation. A one-player recording against level 7 can test it (**Conclusion**). See [combat.md of game_v2](../game_v2/docs/combat.md#the-decapitation).

- **The hit-record bug reads the I/O area.** [`get_hit_record` `$86D9`](src/combat/hits.asm#L100) needs 0 in the high byte of `move_ptr`, but [`check_attack_hit` `$865B`](src/combat/hits.asm#L25) clears it only once for a list. Thus a second list entry for the same defender pose reads a wrong record. In this program the wrong records are at `$DEB0`, `$DEB8`, `$DEC4` and `$E2B8` (**Code**). The game runs with `$01` = `$25`, so `$DE00-$DEFF` is I/O and no RAM (**Code**). **Conclusion:** without a cartridge, these reads give the values of the open data bus, and a run can get other values from the same position. No run showed the case. Part 2 reads the font and the colours of the stored arena in its place. See [combat.md of game_v2](../game_v2/docs/combat.md#a-bug-the-second-entry-for-a-defender-pose).

- **The demo is random, a game is not.** In the demo, [`ai_choose_moves` `$8591`](src/ai/computer_moves.asm#L6) writes the low byte of CIA 1 timer B EOR timer A into `ai_random`. In a game, it only adds 1 to `ai_random` for each computer fighter in each pass (**Code**). The record files give the reads of `$DC04` and `$DC06` as inputs. All 8 recordings replay on the default build with no pins (**Observed**). **Conclusion:** a test that gives the same timer values repeats each demo fight. See [ai.md of game_v2](../game_v2/docs/ai.md#the-random-source).

- **The pause stops the sprites and the clock.** F5 writes `$80` into `sprites_frozen`, so the raster interrupt does not move the sprites and does not count the bout clock (**Code**). Build V 05 05 87 writes 0 there, and its sprites move during the pause. The text "PAUSED" is in the text table, but no code prints it (**Code**). See [game_flow.md](docs/game_flow.md#the-pause-and-the-version-text).

## How the program works

The crack jumps to `$8009`. The start code prepares the memory, the VIC-II, the interrupts and the sound. Then the demo starts: two computer fighters fight at level 4, and the scene changes between the sunset and the forest after each bout. The demo is the title of the game (**Code**).

F1 starts the set-up and selects 1PLR or 2PLR, and F7 starts the game. Each bout starts with a walk-in and ends with a kill. One player fights the next level after each win, until he loses. Two players fight one bout with a clock of 90 seconds. Each end of a game returns to the demo (**Code**).

~~~mermaid
flowchart TB
  S["Start: memory, VIC-II, interrupts, sound (start)"] --> M["Main loop: 22 calls, no frame wait (main_loop)"]
  M --> K["Status texts, time-out and keys (read_keys)"]
  M --> A["Joysticks and computer (ai_choose_moves)"]
  A --> F["Moves, poses and drawing in the work bitmap (animate_fighters)"]
  F --> H["Hits, energy, score, decapitation (check_hits)"]
  H --> E["End of a bout, goblin, next level, time bonus (end_bout)"]
  E --> Q["Quit to the demo (quit_to_demo)"]
  I["Raster IRQ at line $FA: sprites and timers (raster_irq)"] -.-> M
  T["CIA 1 timers: music tick and effects tick"] -.-> M
~~~

1. **The start runs after each load and each quit.** [`start` `$8009`](src/init/init.asm#L6) selects the effects mode and continues into `restart`. That code removes BASIC and the KERNAL from the memory map, selects VIC bank 1 and sets the interrupts. `init_game_state` sets the demo with level 4 and one player (**Code**).
2. **The main loop sets the pace.** [`main_loop` `$80BB`](src/main/main_loop.asm#L6) calls 22 routines in each pass and never returns. Part 2 of the same build calls 24. Each routine tests its own flags, so one loop serves the demo, the set-up, the bouts and the time-out. The attract recording has 1466 passes in about 15000 frames (**Code**, **Observed**).
3. **The player and the computer obey the same rules.** The joysticks and `ai_choose_moves` give a joystick value for each fighter. The same move tables change each value into a move. In a two-player game, the computer does nothing (**Code**).
4. **Each pass draws the fighters again.** [`animate_fighters` `$87EA`](src/fighter/animate.asm#L6) builds each pose and draws it into a work bitmap. The main loop then copies the work bitmap to the screen in one copy (**Code**).
5. **The hit test compares two poses.** [`check_hits` `$863D`](src/combat/hits.asm#L6) looks up the pose of the attacker and the pose of the defender in tables. A hit record gives the distances, the reaction, the damage, the sound and the points (**Code**).
6. **The end of a bout selects the next step.** [`end_bout` `$83F5`](src/combat/end_of_bout.asm#L6) waits for the goblin and the winner. Then it changes the scene, starts the next level or quits to the demo (**Code**).
7. **The interrupts keep the time.** [`raster_irq` `$93C6`](src/irq/irq_handler.asm#L42) copies the sprite registers, moves the sprites and counts the timers at line `$FA`. CIA 1 timer B runs [`music_tick` `$97D7`](src/music/tick.asm#L6), and timer A runs the effects and writes the SID (**Code**).

## The pages

Part 1 has one page of its own. For the subsystems that are the same code as part 2, the pages of `game_v2` give the details. The addresses of part 1 are lower by the shift in the table (**Code**, see [docs/game_flow.md](docs/game_flow.md#shared-with-part-2)).

| Page | Content | Shift of part 1 |
|---|---|---|
| [docs/game_flow.md](docs/game_flow.md) | **The game flow.** The start, the main loop, the demo, the keys, F1 and the players, the bouts, the clock, the time bonus, the scenes and the quit. | - |
| [tests/README.md](tests/README.md) | **The tests.** The recordings, the modes that they really played, the writes for a test and the replays on the default build. | - |
| [../game_v2/docs/fighters.md](../game_v2/docs/fighters.md) | **The fighters.** The joystick, the moves, the poses, the work bitmap, the sprite parts and the idle move. | -$16C (tables -$16A) |
| [../game_v2/docs/combat.md](../game_v2/docs/combat.md) | **Combat.** The hit lists and records, the energy, the score, the decapitation, the goblin and the hit-record bug. | -$16C (tables -$16A) |
| [../game_v2/docs/ai.md](../game_v2/docs/ai.md) | **The computer opponent.** The AI tables, the level, the counter and the CIA timers of the demo. | -$16C (tables -$16A) |
| [../game_v2/docs/graphics.md](../game_v2/docs/graphics.md) | **The graphics.** The bitmap, the scene change, the work bitmap, the colours, the sprites, the raster IRQ and the text output. | -$16C, IRQ -$16A, pictures from `$D000` 0 |
| [../game_v2/docs/sound.md](../game_v2/docs/sound.md) | **Sound and music.** The driver on two CIA timers, the tunes, the effects and F3. | -$16A |
| [../docs/development.md](../docs/development.md) | **The development.** The traces of the work of the authors in the four programs. | - |
| [../docs/versions.md](../docs/versions.md) | **The versions.** Part 1 against part 2, and V 05 05 87 against V 05 10 87, with each shift. | - |
| [../docs/releases.md](../docs/releases.md) | **The releases.** The three cracks, their files, the crack chain and the Hotline trainer. | - |

The status line, the walk-in and the end of a bout are 6 bytes lower than in part 2. The shift of the code becomes `$16A` at F3 in `read_keys` (**Code**). The page [../game_v2/docs/final_stage.md](../game_v2/docs/final_stage.md) explains the final stage of part 2. Part 1 has only dead copies of its data and of `set_end_figure`.

## The releases

| Label | File | SHA-256 |
|---|---|---|
| FLT | `original/fairlight/flt-barbarianpart1-2.d64` | `abf6320286ee4c60d37d0491bd4a505cac0f94a526092cfd3e874150660d8a34` |
| FLT | `original/fairlight/barbarian_p1_flt.prg` | `cb0f51b0b8a3f2d5ae08a064d776872ffc823c227e721724f2137a1506f99a99` |
| FLT | `original/fairlight/flt-barbarianpart1-2.zip` | `9403181e5caec190fe2d975af763f87a6071bf645d273b38e18d8703fb8e0dbb` |
| FLT | `original/fairlight/flt-barbarianpart1-2.nfo` | `1ad8a85237d636a90d8fee169578f4e4347798be9fa32639577a816a604a9495` |

- **FLT** (Fairlight, crack by Strider, 21 May 1987, CSDb 21950): the D64 holds BARBARIAN P1/FLT (161 blocks) and BARBARIAN P2/FLT (158 blocks). `barbarian_p1_flt.prg` is the file BARBARIAN P1/FLT. The .nfo says "Repacked for FairLight Archive 2019 November", so the files are a new pack of 2019. FLT changed no byte of the game (**Observed**, **Conclusion**).

The .nfo gives the keys "F1 for 1 or 2 Players", "F3 for Music/SFX" and "F7 to start the game". The line about F1 is correct only for part 1 (**Observed**, **Conclusion**). Part 2 of the same release is the project `game_v2`. The RDI and HTL releases hold the other build, V 05 05 87, in the projects `practice_v1` and `game_v1`. See [../README.md](../README.md#the-projects).

**The crack left a gap in the program.** The colour copy code of FLT runs at `$CF00-$CF21`, inside the unused RAM after the tables. The capture leaves out these bytes and the colour source `$0400-$07E7` (**Observed**). The bytes around the gap are `$FF` and `$A3`, not the fill pattern of the other programs. It is not known if the FLT unpacker wrote them. At `$0801-$0837`, [`unused_0801` `$0801`](src/leftovers/leftover_0801.asm#L6) holds 55 zero bytes, where the RDI files hold the colour copier of RDI (**Observed** byte compare). The details are on [../docs/releases.md](../docs/releases.md#flt-the-fairlight-crack-of-v-05-10-87).

## The rebuild

**The base release.** The knowledge holds the memory of FLT at the game entry `$8009`. It has two segments, `$07E8-$CEFF` and `$CF22-$FFFF`, 63478 bytes. The capture leaves out two areas of the crack: the colour source `$0400-$07E7` and the colour copier `$CF00-$CF21` (**Observed**). The game uses `$0400-$07FF` only as work RAM, for example for the composition buffer of the fighters (**Code**). The copier of the default build runs at `$0400`, and all replays pass (**Observed**). Thus the game needs no bytes of the crack there (**Conclusion**).

**The entry state.** `build/clean_loader.prg` is a program that Exomizer packed, and it starts with RUN. Its copier puts the segments into place and writes the entry state at `$0002-$03FF`. It sets the VIC-II registers of the entry state. Then it waits for raster line `$E8`, loads timer A of CIA 1 and jumps to `$8009` (**Code**). The timer load keeps the phase of the timer interrupts of the capture (**Observed**, see [tests/README.md](tests/README.md#replays)).

**The colour RAM defect.** The entry state in the knowledge holds the 1000 colours of colour RAM. The loader of c64-re-tools 2.6.0-rc.20 does not write them: the loader source has no store to `$D800-$DBE7` (**Code**). Thus `build/clean_loader.prg` shows the pictures in wrong colours. The game itself never writes most of colour RAM. FLT copies the 1000 colours from `$0400-$07E7` before the jump. The replays compare RAM and not colour RAM, so they pass. This is a defect of the toolkit, not of the knowledge or the source.

**The switches.** The knowledge of this project has no switch and no patch, because FLT changed no byte of the game. The generated source adds one switch for the leftovers. `src/config.asm` holds its value, and `src/switches.asm` holds the value of the release (**Code**).

| Switch | Kind | Default | Releases with it on | What it changes |
|---|---|---|---|---|
| `LEFTOVERS` | leftovers | 0 | FLT | 1006 bytes in 11 files of `src/leftovers/` that nothing uses |

The leftovers are the zero bytes at `$0801`, the dead copy of `set_end_figure` and its data, and the bytes in the gaps. The copies after the stored arena are also leftovers (**Code**).

**The builds.** From the project folder, with the scripts of the c64-source and c64-assembler skills:

1. `source.ts generate --out src --loader` writes the source and `build/clean_loader.prg`, the default build. It loads with `LOAD"...",8` and starts with RUN.
2. `assembler.ts build src main.asm --release FLT --compare` builds the FLT bytes. The release build has the same bytes as the capture in all segments (**Observed**).

**The tests.** Eight recordings with scripted input replay on `build/clean_loader.prg`: `attract`, `decapitation`, `fight`, `keys`, `two_decap`, `two_players`, `two_win` and `win_bout`. Claude wrote the steps, and no person played. Each replay stops at `main_loop` and compares the energy, the position and the move of both fighters. It also compares the level, the scene, the loser and the final stage flag. The rebuild gives the same values at all 4528 checkpoints, with no pins (**Observed**). The notes of each recording, and the mode that it really played, are on [tests/README.md](tests/README.md).

**The code that no run executed.** After all recordings, 36 code ranges with 449 instructions stayed unexecuted (**Observed** coverage). The main groups are:

- The dead code of the final stage: the swaps of the end scene and the copy of `set_end_figure`. They have 173 instructions in 2 ranges.
- The decapitation, the goblin at the head and one winner move: 108 instructions in 4 ranges. No recording had a decapitation.
- The sprite code that no table uses: commands and options of the motions, the animations, the sprite scripts and the corners. They have 99 instructions in 12 ranges.
- The paths of the sound driver that no tune uses, for example the restart command and the frequency slide: 33 instructions in 7 ranges.
- The end of a one-player bout and the key Q. Also the paths of F1 and of the quit that change the scene, mirror the sprites or restore the end scene. They have 25 instructions in 7 ranges.
- Four rare cases: a second hit sprite slot, two commands of the move sequences and a carry in the move selection. They have 11 instructions in 4 ranges.

## Still open

- Does the end of a one-player bout work as the code shows? — A recording with two short presses of F1 (1PLR) that wins one bout and loses the next.
- Does the decapitation of part 1 work as in part 2? — A one-player recording against level 7 with an idle player.
- How many passes find an F1 press of 10 frames in the middle of the demo? — A run that counts the calls of `read_keys_f1_clock` during the press.
- Can player 2 change the number of players with fire during the set-up? — A run that presses fire on port 1 between F1 and F7.
- What does Q do in each state? — A run that presses Q in the demo, the set-up, a bout and the time bonus.
- What values does the hit-record bug read at `$DE00-$DEFF`, and what does the game do with them? — A two-player run with the attacks of hit list 4 against the poses `$3F-$4B`, with a watch on the reads of `$DEB0`.
- Did the FLT unpacker write the `$FF`, `$A3` and `$00` bytes in the gaps? — An analysis of the FLT unpacker and its memory fill.
- Do the FLT files of 1987 and the repack of 2019 hold the same game bytes? — A compare with an FLT disk of 1987.

## The reference

[docs/reference/index.md](docs/reference/index.md)
