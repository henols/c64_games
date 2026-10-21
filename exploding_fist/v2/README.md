# The Way of the Exploding Fist (version II)

*The Way of the Exploding Fist* is a karate game for one or two players. Melbourne House published it in 1985, and Beam Software programmed it. In the one-player game, the player fights the computer through four scenes and from NOVICE to 10TH DAN. This page is the entry page of version II, the program of the cracked releases SCC and MRZ. SCC is the base release, and the two releases have the same game bytes. The source in [src/](src/) assembles byte for byte to each release, and the default build is the game without its copy protection. Version I has its own project, [../v1/README.md](../v1/README.md), and [../README.md](../README.md) tells what the two versions share.

**Evidence.** **Observed** marks a fact that an emulator run, a byte compare or the coverage of the runs showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation. A scenario has the name of its file in [tests/](tests/).

## The development

Version II is version I with new parts. An alignment of the two programs finds 4378 of the 4737 instructions of version I in version II. The music driver at `$09A5-$0F51` has the same bytes in both versions. The 2010 crack of version I shows "WAIT FOR VERSION II" on its screen. Thus version I came first (**Observed** / **Code** / **Conclusion**).

Version II adds five features: keyboard control, a top-5 high score table with names, four live samples, a bull bonus round and a judge. Most of them grew from parts that version I already holds. Version I has a bull test, a sample player, a judge stub and a fourth tune, but no code uses them. Version II calls each of them from the game (**Code**). The [Findings](#findings) give each part.

Version II also corrects three bugs of version I. The rank now stops at 10TH DAN. The order list of tune 1 gets the 2 bytes that it did not have, so voice 0 stays in step and pattern 2 plays. The X limits clamp the position by facing, and three somersault frames moved one sprite column to the left (**Code**). The 2 new bytes of tune 1 moved all later data by 2. Thus the game entry moved from `$1158` to `$115A` (**Code**).

The new code needed space. Version II packs the colour maps and the screen maps of the four scenes with a new nybble run-length code. The maps now take 2357 bytes in place of 3840. The saving is 1483 bytes, that is `$5CB`, and the packed scene bitmaps moved exactly `$5CB` bytes higher (**Code** / **Observed**, byte compare). The samples took the floor bitmap at `$F540`. Thus the 41 bull blocks of version I moved, byte for byte, to free places in VIC bank 3 (**Observed**, byte compare).

The authors assembled version II from the source text of version I. They did not patch a memory image. The dead code of version I has the new addresses in its operands, for example the two unused patch routines of the sprite multiplexer. In the AI, new code made a branch too long. At [`ai_choose_attack` `$24B8`](src/ai_opponent.asm#L288) the author inverted the branch and added a JMP (**Code** / **Conclusion**).

Version II has leftovers of its own. [`dev_clear_part_ptrs` `$12ED`](src/bull_round.asm#L6) of the version I bull test stays with its 11 bytes, and nothing calls it. The bull round writes `$7F` to `sfx_done`, the end value of the version I sample player. The player of version II writes `$FF`. Three pointer tables of older scene layouts stay, and nothing reads them (**Code**).

More leftovers are in the new parts. The sample player has 8 start entries for 4 samples. Sample 2 has a tail of 511 bytes that no table entry covers. The key table `key_chars` holds all 64 keys, and a mask keeps only the keys of a name. The demo writes `$FF` to the music byte at `$04F0`, which holds `$FF` already (**Code**). The scenario [leftovers_unused.json](tests/leftovers_unused.json) fills 25 unused regions with `$A5`, and the game runs the same (**Observed**).

The gaps between the tables hold RAM contents that no program wrote before the save. These bytes differ from the gaps of version I. Thus the authors saved the two versions in different sessions (**Observed** / **Conclusion**). The high score module has a different code style, for example loops that end with `CPX #$FF`. Another programmer possibly wrote it (**Code** / **Conclusion**).

The details are on [../docs/development.md](../docs/development.md). Each difference between the two programs is on [../docs/versions.md](../docs/versions.md).

## The copy protection

The original Melbourne House disk had a protected loader. No release keeps it, because SCC and MRZ replace it with loaders of their own. The original loader left one mark in the machine: CIA2 control A at `$DD0E` holds 0 at the game entry. A C64 after a KERNAL reset has `$08` there. The game never writes this register (**Code** / **Conclusion**).

Version II tests the mark in [`protect_cia2_check` `$2CAE`](src/hit_test.asm#L180). This check is inside `hit_record`, the routine that records each scoring hit. After the store of `scoring_move`, it reads `$DD0E`. The value 0 continues to the hit reaction of the opponent, and each other value goes to the trap. Version I has no check (**Code**).

The check is well hidden. It runs at the first scoring hit, not at the start of the game. It has three instructions, no compare and no text. The trap jumps into `anim_update`, a normal target in the game, so the crash occurs far from the check (**Code** / **Conclusion**).

[`protect_cia2_trap` `$2CB3`](src/hit_test.asm#L194) pushes a false return address. Its high byte is the value of `$DD0E`, and its low byte is `opponent_index`. Then the trap jumps into `anim_update` with X = `$4E`, so the routine works on the wrong zero-page bytes. The last RTS of `anim_update` goes to `$DD0E` × 256 + `opponent_index` + 1, for example `$0802` in the music data. The CPU then executes data as code (**Code**).

The run [protection_trap_original.json](tests/protection_trap_original.json) writes `$08` to `$DD0E` at the entry and lets the demo play. The first scoring hit of the demo reaches the check with `$08`. 600 frames later, the CPU executes at `$902C`, in the fighter shape data. The panel shows no yin-yang for the hit, and the clock stops at 27 (**Observed**).

![The original game with $DD0E = $08: the first point crashed the game](docs/images/protection_trap_original.png)

The original game 600 frames after the first scoring hit: no yin-yang on the panel, and the clock stopped at 27.

Both cracks keep the check. The SCC loader writes 0 to `$DD0E` just before it jumps to the game, and MRZ also starts the game with 0 there (**Observed**). The switch `PROTECTION` in [src/config.asm](src/config.asm) is 0 by default. It replaces `LDA $DD0E` with `LDA #$00` and a NOP, so the check always passes (**Code**). The run [protection_trap_rebuild.json](tests/protection_trap_rebuild.json) writes `$08` to `$DD0E` too, and the default build continues to play (**Observed**). The details are on [../docs/protection.md](../docs/protection.md).

## Findings

- **The bull bonus round grew from a test of version I.** After the two wins of each stage in scene 3, a brown bull runs at the player. This occurs at 3RD DAN, at 7TH DAN and at each fourth stage after 10TH DAN. [`bull_bonus_round` `$132C`](src/bull_round.asm#L46) is the test routine of version I with corrections. A crouch punch, frame `$0D`, stops the bull for 3000 points at a distance of `$19-$1D`, but only in the first frame of the punch. A run without a hit gives 500 points. A reach table by fighter frame replaces the sprite collision test of version I. Thus a somersault or a flying kick lets the bull pass (**Code**). In [one_player_cpu_bull.json](tests/one_player_cpu_bull.json) the bull hits the fighter (**Observed**). No run stopped the bull, so the 3000 points are **Code** only. A fighter who does not move has a window of about 9 frames for the punch (**Conclusion**). See [docs/bull_round.md](docs/bull_round.md).
- **Four live samples, and one of them is cut by 2 pages.** Version II plays a knockdown, a hit, the swish of an attack and a fighter on the floor. The player [`sfx_sample_irq` `$311A`](src/sfx_sample_player.asm#L6) was dead code in version I. The samples are in the floor bitmap at `$F540`, and the yellow floor colour hides their bytes (**Code**). Sample 1 is a part of the speech of the loading stage: 790 bytes are equal to M.TSOUND `$3214-$3529` (**Observed**, byte compare). The end offset of sample 2 has the high byte 7, and the start offset of sample 3 has 9 with the same low byte. Thus the 511 bytes of `sfx_sample_attack_cut` have no reader (**Code**). The renders are in [docs/assets/](docs/assets/), and [sample2_attack_uncut.wav](docs/assets/sample2_attack_uncut.wav) plays sample 2 with its tail, 0.54 seconds (**Observed**). Each sample start clears all SID registers, so the music voices stop until their next note (**Conclusion**). See [docs/sound_music.md](docs/sound_music.md).
- **Keyboard control for both fighters.** F7 on the title selects JOYSTICK or KEYBOARD. Player 1 then uses `Q W E`, `A D` and `Z X C`, with the fire key `S` or LEFT SHIFT. Player 2 uses `P @ *`, `L ;` and `, . /`, with the fire key `:` or RIGHT SHIFT. Each key gives one joystick direction, and two keys never give a diagonal (**Code**). The scenario [keyboard_option.json](tests/keyboard_option.json) and the recording keyboard show it for player 1 (**Observed**). No run pressed the keys of player 2. A joystick in port 1 uses the same lines as the keyboard rows, so in keyboard mode it can give false keys (**Conclusion**). See [docs/fighters.md](docs/fighters.md).
- **A top-5 high score table, and a held fire button loses the name.** After a one-player game, [`hs_table_update` `$146A`](src/high_score_table.asm#L6) puts the score into a table of 5 entries with the rank and a name of 6 characters. The name entry plays tune 4, a jingle that version I holds but never plays (**Code**). The routine first writes the new score with the name "......", and then it reads the fire button. When the player holds fire, the routine returns, and the name stays "......" (**Code**). No run tested this bug. A player who holds fire to start again thus loses the name (**Conclusion**). The table is in RAM only, so each load starts with an empty table (**Code**). See [docs/high_scores.md](docs/high_scores.md).
- **A judge in the place of an RTS.** A grey judge (sprite 6) shows the winner with a flag in the colour of the winner (sprite 7). The judge comes at a decision by time and at the end of a two-player game. [`judge_show_winner` `$1F93`](src/score_and_judge.asm#L43) replaces `winner_stub` of version I, a lone RTS, at the same three calls. Version I already keeps sprites 6 and 7 in the multiplexer and holds the flag block, unused (**Code**). The runs executed all three calls, but no screen capture shows the judge yet (**Observed**, coverage). After the fourth bout, the two-player game decrements `stage_counter` from 4 to 3, so that the judge stands in scene 3 (**Code**). See [docs/game_flow.md](docs/game_flow.md).
- **The rank cap also protects the panel font.** Version I promotes the player past 10TH DAN, and the panel then shows garbage such as "|||TH DANN". [`game_1p_rank_cap_test` `$1C27`](src/game_modes.asm#L149) stops the promotions at stage 10. After that, the scenes continue, and the computer gets a random level from 7 to 10 (**Code**). In [rank_cap.json](tests/rank_cap.json) the rank stays 10TH DAN (**Observed**). Version II keeps only the 64 characters `$20-$5F` of the panel font, and bull parts fill the rest. Thus a text outside this range would show bull graphics, and the cap prevents such a text (**Code** / **Conclusion**). See [docs/game_flow.md](docs/game_flow.md) and [docs/graphics.md](docs/graphics.md).
- **The AI bugs of version I stay.** Version II adds new rules to the computer opponent but keeps four bugs. [`ai_setup_level` `$2593`](src/ai_opponent.asm#L424) writes most AI masks without the index X, so the level of fighter 1 sets the values of both fighters. Special action 8 writes the slot of fighter 0 for fighter 1. Special action 7 compares with the wrong register, and no run executed it. The tie break `bout_hit_value_add` reads `hit_points` of fighter 0 for both fighters (**Code**). Only the demo shows the first bug, because both fighters are computer players there (**Conclusion**). See [docs/ai.md](docs/ai.md) and [docs/combat.md](docs/combat.md).
- **The protection trap stops the demo after about 3 clock seconds.** A copy of version II that starts with `$08` in `$DD0E` shows the title and the demo. Then the first scoring hit crashes it (**Observed** in [protection_trap_original.json](tests/protection_trap_original.json)). The bout clock starts at 30 and stops at 27. Thus an SCC or MRZ game file that a KERNAL loader starts is not a working copy. The default build and `build/exploding_fist_v2.prg` have `PROTECTION` = 0, so they work on each C64 (**Conclusion**). See [../docs/protection.md](../docs/protection.md).

![The bull round in scene 3: the white fighter at the left, the brown bull runs at him from the right](docs/images/bull_round.png)

The bull round at 3RD DAN in scene 3, the scene with the Buddha statue (**Observed** in `one_player_cpu_bull.json`).

![The title panel over the demo with KEYBOARD above 1 PLAYER](docs/images/title_keyboard.png)

The title panel during the demo after F7. KEYBOARD is on row 3, and DEMO, the high score and 1 PLAYER are on row 4 (**Observed** in `keyboard_option.json`).

## How the program works

The game loads one time and fills memory from `$0400` to `$FFEF`. The start-up sets the vectors, the CIAs and the VIC-II one time. The program has no separate title screen. The panel at the top of the screen shows the title texts, and the demo plays below it. A key or the fire button starts a game from the demo (**Code**).

Each game mode is a loop of bouts, and each bout is a loop of exchanges. One pass of the bout loop runs in each frame, at raster line `$FD`. It updates the two fighters, steps the random value, reads the title keys and steps the clock. A chain of raster interrupts draws each frame: the panel in text mode, the scene in bitmap mode and the sprites of the fighters. A CIA1 timer interrupt plays the samples between them (**Code**).

~~~mermaid
flowchart TB
  D["Data: packed scenes, fighter parts, scripts, hit zones, music, samples"]
  S["Start-up, one time (init_game_state)"]
  T["Title loop and demo"]
  G["Game modes: one player, two players, bull round, high score table"]
  B["Bout loop: one pass in each frame"]
  F["Fighter update: hit test, control, move, animation"]
  C["Control: joystick, keyboard or computer (ai_update)"]
  H["Shape builder: the sprite parts of each frame"]
  I["Raster IRQ chain: panel, bitmap, sprite rows, music"]
  P["CIA1 IRQ: the samples"]
  N["CIA2 NMI: the yellow floor"]
  D --> S --> T --> G --> B --> F
  C --> F
  F --> H --> I
  P -. "same IRQ vector" .-> I
  N -.-> I
~~~

1. **The start runs one time.** [`program_entry` `$115A`](src/entry_and_tables.asm#L6) jumps to `cold_start`, which calls `init_game_state` and enters the title loop. The start-up disables the ROMs and sets the IRQ, NMI and RESET vectors in RAM. It copies the sample period tables from `$C700` to `$0200`. It writes the constant `$53` to `frame_random`, so the first demo is the same after each start (**Code** / **Conclusion**).
2. **The title loop never returns.** [`title_main_loop` `$1EE1`](src/title_and_scene.asm#L82) shows the high score, the mode and the control text, and then plays a demo of four bouts. F3 changes the mode, F7 the control and DEL the samples. A start key ends the demo and starts the game of the mode (**Code**). See [docs/game_flow.md](docs/game_flow.md).
3. **The game modes call the bouts.** [`game_one_player` `$1BA7`](src/game_modes.asm#L89) plays bouts until the first lost bout. Two wins give a promotion, and a clear in scene 3 also gives the bull round. The two-player game plays four bouts of 30 seconds. After a one-player game, the title loop shows the top-5 table (**Code**).
4. **The bout loop sets the pace.** [`bout_loop` `$1A7C`](src/bout_loop.asm#L54) waits for raster line `$FD` in each frame. Then it updates fighter 1 and fighter 0, steps `frame_random`, reads the title keys and steps the clock. A fall or the end of the time ends the exchange (**Code**).
5. **A fighter goes through moves.** [`fighter_update` `$2808`](src/fighter_input.asm#L6) first tests the hits of the opponent. Then it reads the control, selects the move and plays one frame of its animation script. The control is the joystick, the keyboard or the computer opponent `ai_update` (**Code**). See [docs/fighters.md](docs/fighters.md) and [docs/combat.md](docs/combat.md).
6. **The interrupts draw each frame.** [`irq_frame_start` `$31F2`](src/sprite_mux_plan.asm#L6) at line 0 plans the sprite rows of the two fighters. The chain then sets bitmap mode at line `$5A`, moves the sprites down the screen, shows the shadows and plays the music at line `$FF`. A CIA2 NMI makes the floor yellow (**Code**). See [docs/interrupts.md](docs/interrupts.md).
7. **The samples use the same IRQ vector.** Each raster handler first reads `$DC0D`. A CIA1 interrupt goes to `sfx_sample_irq`, which toggles the SID volume for each sample byte (**Code**). See [docs/sound_music.md](docs/sound_music.md).

The flow of a player through the game:

~~~mermaid
stateDiagram-v2
  state "Loading: title picture and speech" as Load
  state "Title panel and demo" as Demo
  state "One-player bout" as One
  state "Bull round" as Bull
  state "Top-5 table and name entry" as Table
  state "Two-player game: 4 bouts" as Two
  [*] --> Load
  Load --> Demo: game entry
  Demo --> Demo: 4 bouts, no start key
  Demo --> One: F1 or fire, 1 PLAYER
  Demo --> Two: F1 or fire, 2 PLAYER
  One --> One: two wins, next rank
  One --> Bull: two wins in scene 3
  Bull --> One: next rank
  One --> Table: a lost bout
  Table --> Demo: name complete
  Two --> Demo: the judge shows the winner
~~~

## The pages

| Page | Content |
|---|---|
| [docs/game_flow.md](docs/game_flow.md) | **The game flow.** The start-up, the title keys, the demo, the one-player and two-player games, the judge, the points and the clock. |
| [docs/fighters.md](docs/fighters.md) | **The fighters.** The joystick and keyboard input, the moves and their state machine, the animation scripts, the X limits and the samples of the moves. |
| [docs/ai.md](docs/ai.md) | **The computer opponent.** The order of the decisions in each frame, the new rules of version II, the level tables and the bugs that stay. |
| [docs/combat.md](docs/combat.md) | **Combat.** The hit test, the reach window, the hit reactions, the CIA2 check, the points and the tie break. |
| [docs/bull_round.md](docs/bull_round.md) | **The bull round.** When the round comes, the stop and the hit, the reach table, and how the test of version I became the round. |
| [docs/high_scores.md](docs/high_scores.md) | **The high score table.** The top-5 table, the name entry, the key scanner and the bug of the held fire button. |
| [docs/graphics.md](docs/graphics.md) | **The graphics.** The two paths of the shape builder, the bull blocks, the judge, the shadows, the panel font and the packed scene maps. |
| [docs/interrupts.md](docs/interrupts.md) | **The interrupts.** The raster chain, the dispatch of the sample IRQ, the sprite layouts and the timeline of a frame. |
| [docs/sound_music.md](docs/sound_music.md) | **Sound and music.** The music driver, the correction of tune 1, the jingle of tune 4, the sample player and the four samples. |
| [../docs/development.md](../docs/development.md) | **The development.** What the leftovers of the two versions tell about the work of the authors. |
| [../docs/versions.md](../docs/versions.md) | **Version I and version II.** Each difference between the two programs, part by part. |
| [../docs/protection.md](../docs/protection.md) | **The copy protection.** The CIA2 check of version II, its trap and the switch that disables it. |
| [../docs/releases.md](../docs/releases.md) | **The releases.** The four crack disks, their files and the traces of each crack in the program. |
| [../docs/loading_stage.md](../docs/loading_stage.md) | **The loading stage.** The title picture, the speech sample and its player, and the boot of the rebuild. |

## The releases

| Label | File | SHA-256 |
|---|---|---|
| SCC | `original/scc.d64` | `6a789804806c01c090c87ce32a31bd68be4e09b3865092f2592ebf3c1f48712c` |
| MRZ | `original/mr_z.d64` | `8495eff9f00ebb4748916bd1ba8a60082853a9039368a7c549dbdeedd5756137` |

**Observed** (sha256sum of each disk file).

- **SCC.** A KERNAL chain loader at `$0200` loads the nine files A to I, shows the title picture and plays the speech sample. Then it starts the game at `$115A`. No byte of the game differs from MRZ (**Observed**, byte compare).
- **MRZ.** The intro EXPLODING F/MR.Z shows "CRACKED BY MR Z..." and unpacks the file FIST.OBJ. The game bytes are identical to SCC (**Observed**, byte compare).

**SCC: the crack text in the title picture.** The SCC crackers drew "CRACKED BY S.C.C." into the top right of the title picture. The file C of the SCC disk differs from M.PICTURE of the 2010 disk only in a small area. That area is the cells 27 to 37 of the rows 0 to 3. The difference is in the bitmap, the screen data and the colour data (**Observed**, byte compare). The game file G loads over the picture later, so the text is not in the game bytes (**Observed**). The rebuild thus shows the clean M.PICTURE of the 2010 disk at its start (**Code**).

**SCC: the 0 in `$DD0E`.** The chain loader ends at `$0360` with `LDA #$00`, `STA $DD0E` and `JMP $115A` (**Observed**, run). This store sets the mark that [`protect_cia2_check` `$2CAE`](src/hit_test.asm#L180) reads. Thus SCC passes the check without a change to the game code (**Conclusion**). The entry state of the knowledge keeps the 0, and the MRZ capture also has 0 there (**Observed**). The code of the Mr. Z crack that writes it is not known. The disks and the traces of all four releases are on [../docs/releases.md](../docs/releases.md).

## The rebuild

**The base release.** The knowledge holds the memory of the SCC release at the game entry `$115A`. It has four segments: `$0400-$BFFF`, `$C400-$CBFF`, `$D000-$E5FF` and `$F540-$FFEF`. The capture excludes `$C000-$C3FF`, the second stage of the SCC loader. It also excludes `$CC00-$CFFF` and `$E600-$F53F`, the remains of the title picture, and `$FFF0-$FFFF`. Junk tests show that the game does not need these areas (**Observed**).

**The entry state.** [src/loader.asm](src/loader.asm) copies the segments into place and writes the pages `$0002-$03FF` of the capture. It sets the CIA timers, the VIC-II registers, `$DD0E` = 0, `$01` = `$37` and the stack. Then it jumps to `$115A` (**Code**). The pages `$0200-$03FF` hold the bytes of the SCC chain loader (**Observed**). `init_game_state` writes the sample period tables over them, so the game does not use the loader bytes (**Code**).

**The switches.** [src/config.asm](src/config.asm) holds the value of each switch. Change a value there, and build again. [src/switches.asm](src/switches.asm) holds the value of each switch for each release.

| Switch | Kind | Default | Releases with it on | What it changes |
|---|---|---|---|---|
| `PROTECTION` | protection | 0 | SCC, MRZ | `$2CAE-$2CB0`: `LDA $DD0E` (1) or `LDA #$00` and a NOP (0) |

No release has a trainer or a cheat. SCC and MRZ have the same game bytes, so no other switch is necessary (**Code**).

### Build

Run these steps from the project folder with the scripts `assembler.ts` of the c64-assembler skill and `packer.ts` of the c64-packer skill.

1. The default build, the clean game without the picture. The packed loader `build/fist_v2_loader.prg` starts with RUN and has `PROTECTION` = 0:

   ```text
   assembler.ts build src main.asm --out build/fist_v2_main.prg
   assembler.ts build src loader.asm --out build/fist_v2_copier.prg
   packer.ts pack build/fist_v2_main.prg build/fist_v2_copier.prg --entry '$cc00' --exit-memory '$34' --out build/fist_v2_loader.prg
   ```

2. A release. Each command gives the bytes of its capture (**Observed**, generate check):

   ```text
   assembler.ts build src main.asm --out build/fist_v2_scc.prg --release SCC
   assembler.ts build src main.asm --out build/fist_v2_mrz.prg --release MRZ
   ```

3. The three parts of the boot:

   ```text
   assembler.ts build src boot.asm --out build/boot.prg --include ../original/releases/2010_loading --include ../build
   assembler.ts build src boot_bitmap.asm --out build/boot_bitmap.prg --include ../original/releases/2010_loading --include ../build
   assembler.ts build src boot_stash.asm --out build/boot_stash.prg --include ../original/releases/2010_loading --include ../build
   ```

4. The boot file of the release:

   ```text
   packer.ts pack build/fist_v2_loader.prg original/releases/2010_loading/segment-2000-35ff.prg original/releases/2010_loading/segment-9000-910f.prg original/releases/2010_loading/segment-9800-9aff.prg build/boot_stash.prg build/boot.prg build/boot_bitmap.prg --entry '$c600' --out build/exploding_fist_v2.prg
   ```

**The boot file.** `build/exploding_fist_v2.prg` has 45983 bytes. It loads with `LOAD"...",8` and starts with RUN (**Observed**). It shows the clean Melbourne House picture M.PICTURE of the 2010 disk, from `original/releases/2010_loading`. Then it plays the speech sample M.TSOUND with the original player M.MYTINY, 2.23 seconds ([loading_sample.wav](../v1/docs/assets/loading_sample.wav)). It waits 8 seconds, or less after a key or a fire button. Then it restores the bytes of the default build at `$2000-$35FF` and `$9000-$93FF` and unpacks the game (**Code**).

The boot needs two values of `$01` that runs showed. It needs `$36` for the copy of the stash, because the sample player enables the BASIC ROM at its end. It needs `$37` before the Exomizer unpacker, because `$36` gives wrong bytes (**Observed**). [src/boot.asm](src/boot.asm), `src/boot_bitmap.asm` and `src/boot_stash.asm` are hand-written, and the source generator keeps them. The loading stage and the boot are on [../docs/loading_stage.md](../docs/loading_stage.md).

**The tests.** All tests PASS (**Observed**):

- The scenarios run the original loader `original/fist_v2_scc.prg` and the default build side by side: [demo.json](tests/demo.json), [one_player_cpu_bull.json](tests/one_player_cpu_bull.json), [two_player.json](tests/two_player.json), [rank_cap.json](tests/rank_cap.json), [keyboard_option.json](tests/keyboard_option.json) and [leftovers_unused.json](tests/leftovers_unused.json).
- The runs with expected values are [boot_title_picture.json](tests/boot_title_picture.json), `protection_trap_original.json` and `protection_trap_rebuild.json`. The boot run compares the picture while the sample plays, and the game bytes at the entry.
- The recordings in [tests/record/](tests/record/) replay on the rebuild from [tests/recordings/](tests/recordings/). They are one_player_moves (all 16 joystick moves and a name in the table), two_player (both joysticks), cpu_ranks (all ranks and the bull rounds) and keyboard. They pass 9262, 11107, 53394 and 6787 checkpoints. Each checkpoint compares `fighter_x`, `fighter_move`, `half_points`, `stage_counter` and the panel `$CC00-$CCC7`.

The emulator tools of this setup take no joystick input, but the recordings do. The runs of a game for the computer write `cpu_controlled` at `$65` and `$66` after the start of the game (**Observed**).

**The code that no run executed.** [src/not_executed.json](src/not_executed.json) lists 34 ranges of 209 instructions in 13 source files. The high score table has 8 ranges, for example the places 1 to 4 and DEL in the name entry. The bull round has 4, the stop of the bull and the 500 points among them. Other ranges are the trap, special action 7, the keys of player 2 and the two-player draw (**Observed**).

## Still open

- **The stop of the bull.** No run reached frame `$0D` at the right distance. A recording with a crouch and then down and forward at bull x 88 can show the 3000 points and the fall of the bull.
- **The 500 points of the bull round.** No run dodged the bull to the end. A recording with a somersault at the right moment can show them.
- **The judge on the screen.** No screen capture shows sprites 6 and 7. A run that forces a time-up decision in each scene can capture the judge and the flag.
- **The held fire button at the end of a one-player game.** No run held fire there. A recording with fire held at the last fall can show that the name stays "......".
- **The keys of player 2.** No run pressed them. A two-player game in keyboard mode that presses each key of player 2 can test them.
- **The Mr. Z write to `$DD0E`.** A watchpoint on writes to `$DD0E` while the Mr. Z intro unpacks FIST.OBJ can find the code.
- **The second piece of the stash.** No test compares `$9000-$93C1` at the game entry of the boot file. A memory compare at `$115A` can show it.
- **The original protected loader.** No release has it. An image of the original Melbourne House disk can show its format and why it left 0 in `$DD0E`.

## The reference

[docs/reference/index.md](docs/reference/index.md)
