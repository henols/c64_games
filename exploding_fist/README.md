# The Way of the Exploding Fist

The Way of the Exploding Fist is a karate game for the C64. Melbourne House published it in 1985, and Beam Software programmed it. Two fighters fight in four scenes, and each scoring hit gives a half point or a full point. This documentation covers the two versions of the game program. Four cracked releases hold them: R2010 and SHADOW hold version I, and SCC and MRZ hold version II.

**Evidence.** **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The versions

| Version | Releases | Entry |
|---|---|---|
| [v1](v1/README.md) | R2010 (base), SHADOW | `$1158` |
| [v2](v2/README.md) | SCC (base), MRZ | `$115A` |

Version II is version I with five new features, three corrections and one copy protection check. The new features are keyboard control, a top-5 high score table, live samples, the bull bonus round and the judge. 4378 of the 4737 instructions of version I have a match in version II. **Code**.

The authors kept the order of the parts, but almost each part has a new address. The zero-page variables move by $0B, from v1 `$3A-$B5` to v2 `$45-$C0`. The music tables after tune 1 move by 2, so the entry moves from [`v1:program_entry` `$1158`](v1/src/game/entry_and_tables.asm#L6) to [`v2:program_entry` `$115A`](v2/src/game/entry_and_tables.asm#L6). The code moves by $4D4 at the init and by up to $7DE at the end of the shape builder. **Code**.

| Part | v1 | v2 | Move |
|---|---|---|---|
| Zero page, main variables | `$3A-$B5` | `$45-$C0` | +$0B |
| Music driver and music data | `$0400-$0FCD` | `$0400-$0FCD` | none |
| Entry and move tables | `$1158-$12CD` | `$115A-$12CF` | +2 |
| Init to the end of the shape builder | `$1414-$36A1` | `$18E8-$3E7F` | +$4D4 to +$7DE |
| Packed scene bitmaps | `$3994-$62FF` | `$3F5F-$68CA` | +$5CB |
| Hit zones, scripts, part tables | `$7200-$7DFF` | `$7200-$7DFF` | none |
| Fighter part graphics | `$8000-$BFFF` | `$8000-$BFFF` | none |

A switch of a project changes some bytes of one layout at their addresses. Version II changes the address in almost each operand, so a set of patches cannot hold the difference. Thus each version has its own project, with its own knowledge, source and tests. Each project builds its releases with switches. **Conclusion**. The full list of the differences is on [docs/versions.md](docs/versions.md).

## The development

The game holds no credit text, no date and no version text. The original file names on the 2010 disk are the only original names: M.PROG, M.SHAPES, M.PICTURE, M.TSOUND and five more. **Observed** (byte search and disk directory).

Version I came first. The 2010 crack of version I shows "WAIT FOR VERSION II" on its loading screen. Version II contains version I, corrects its bugs and finishes its unused parts. At [`v2:ai_choose_attack` `$24B8`](v2/src/ai/ai_opponent.asm#L288) the author inverted a branch of version I and added a `JMP`, because the new code made the branch too long. **Observed** (crack text) / **Code**.

The authors did not patch a memory image of version I. Version II keeps the dead code of version I, with the new addresses in its operands. The gaps between the tables hold RAM bytes that no program wrote, and the two versions have different gap patterns. Thus the authors assembled version II again from the source of version I, in another session. **Code** / **Conclusion**.

Version I prepared four parts and did not use them. Version II makes each of them live:

- **The bull round.** [`v1:dev_bull_test` `$138F`](v1/src/dev/dev_bull_test_138f.asm#L6) is a working test of a charging bull, and no code calls it. Version II calls a corrected copy, [`v2:bull_bonus_round` `$132C`](v2/src/game/bull_round_12f8.asm#L36), after the two wins of each scene 3 stage. **Observed** in [bull_test.json](v1/tests/bull_test.json) and [one_player_cpu_bull.json](v2/tests/one_player_cpu_bull.json).
- **The samples.** [`v1:sfx_sample_irq` `$29C8`](v1/src/sfx/sfx_sample_player.asm#L6) is the sample player of the loading stage inside the game. No code starts it, and the music data now fills its old sample area. [`v2:sfx_sample_irq` `$311A`](v2/src/sfx/sfx_sample_player.asm#L6) plays four game sounds. **Code** / **Observed** (renders).
- **The judge.** [`v1:winner_stub` `$1AB7`](v1/src/game/score_and_timer.asm#L43) is a lone `RTS` at the three places of a decision. [`v2:judge_show_winner` `$1F93`](v2/src/game/score_and_judge.asm#L43) shows a judge with a flag at the same three places. The flag sprite is already in the files of version I. **Code** / **Observed** (byte compare).
- **Tune 4.** Version I holds a fanfare that no event plays. [`v2:hs_name_entry` `$1762`](v2/src/game/high_score_table.asm#L382) plays it at the name entry of the high score table. **Observed** (SID writes in a trace and coverage).

Version II also corrects three bugs of version I. In a one-player game of version I, [`v1:game_one_player` `$16A9`](v1/src/game/game_modes.asm#L81) stops the promotions only after 22 promotions. [`v2:game_1p_rank_cap_test` `$1C27`](v2/src/game/game_modes.asm#L146) stops them at 10TH DAN. **Observed** in [rank_overflow.json](v1/tests/rank_overflow.json) and [rank_cap.json](v2/tests/rank_cap.json).

The second correction is in the demo tune. The order list [`v1:music_t1_order_v0` `$0FC2`](v1/src/music/music_tables.asm#L52) lost one entry, so voice 0 never plays pattern 2. Version II puts back the two bytes, and this moves the entry by 2. The third correction is the X limits. [`v1:anim_check_x_limits` `$30B5`](v1/src/fighter/anim_step_3041.asm#L74) refuses a step at the edge, and [`v2:anim_check_x_limits` `$384C`](v2/src/fighter/anim_step_37d8.asm#L74) clamps the position by the facing. **Code**.

Version II packs the scene maps to get space for the new code. The packed maps save 1483 bytes, and the scene bitmaps move up by exactly $5CB. **Code**.

![The bull of version I runs in from the right](v1/docs/images/bull_test_charge.png)

The image shows the bull test of version I, 90 frames after a stub started it. **Observed** in [bull_test.json](v1/tests/bull_test.json).

The leftovers give this order of the work (**Conclusion**):

1. The speech sample and its player of the loading stage came early. The game player is a copy of that code.
2. An early build kept the scene bitmaps unpacked. A packer then made space for more code.
3. An early build had a game sample in the area of the music. The music took that memory.
4. The bull test, the judge stub and tune 4 came late in version I. Version I shipped with them unused.
5. Version II came from the same source. It corrected the bugs and finished the prepared parts.

The full story is on [docs/development.md](docs/development.md).

## The copy protection

The original disk had a protected loader of Melbourne House. Each of the four releases is a crack that replaces this loader with its own. Thus the original loader is lost. **Conclusion**.

Only version II checks. On each scoring hit, [`v2:protect_cia2_check` `$2CAE`](v2/src/fighter/hit_test.asm#L180) reads CIA2 control A at `$DD0E`. The game never writes this register, so the value comes from the loader. A value other than 0 sends the CPU into a false return address and crashes the game. **Code**. With `$08` in `$DD0E`, the value after a KERNAL reset, the demo stops at its first point. **Observed** in [protection_trap_original.json](v2/tests/protection_trap_original.json).

Version I has no check, and [`v1:hit_record` `$2591`](v1/src/fighter/hit_test.asm#L175) has no read of `$DD0E`. The SCC loader writes 0 to `$DD0E` before it jumps to the game. The switch PROTECTION of version II has the default 0 and replaces the read with `LDA #$00`. **Code** / **Observed** (run of the SCC loader). The details are on [docs/protection.md](docs/protection.md).

## Findings

- **Version I promotes the player into garbage.** Ranks 12 to 22 read code bytes as rank numbers, and the panel shows texts such as "|||TH DANN". The AI level of the opponent reads the next tables. A player of version I sees it after 10TH DAN. **Observed** in the recording cpu_ranks. See [docs/development.md](docs/development.md#the-rank-cap).
- **Version II keeps 11 bugs of version I.** One example: [`v2:ai_setup_level` `$2593`](v2/src/ai/ai_opponent_2521.asm#L82) writes most AI masks without the index X, as version I does. Thus the level of fighter 1 sets the values of both fighters. Only the demo shows it, because the computer plays both fighters there. **Code**. See [docs/versions.md](docs/versions.md#the-bugs-of-version-i-that-version-ii-keeps).
- **Both versions hide graphics or sound in the floor.** The floor of the screen, bitmap rows 17-24 at `$F540`, has only yellow colours. Version I keeps the bull sprites there, and version II keeps the four samples there. A player sees only a plain floor. **Code**. See [docs/development.md](docs/development.md#the-samples).
- **A game sound comes from the loading speech.** Sample 1 of version II, the hit sound, is a 790-byte copy of M.TSOUND `$3214-$3529`. **Observed** (byte compare). See [docs/development.md](docs/development.md#the-live-samples-of-version-ii).
- **The gaps hold RAM of the machine of the authors.** The gap bytes repeat one 256-byte pattern in each version, and the two versions have different patterns. A preservation project can use these bytes to tell the versions apart. **Observed** (byte compare). See [docs/development.md](docs/development.md#the-ram-in-the-gaps).
- **The colour maps came from colour RAM.** The colour data of version I and of M.PICTURE has random high nybbles. A read of colour RAM gives such values. Thus an editor on a running C64 saved them. Version II packs only the low nybbles. **Observed** / **Conclusion**. See [docs/development.md](docs/development.md#the-tools-of-the-authors).
- **The music has NTSC notes.** The note table of the driver is the same in both versions and has NTSC values. **Code**. On a PAL C64 each note is about 3.7 % low. **Conclusion**. See [docs/versions.md](docs/versions.md#the-bugs-of-version-i-that-version-ii-keeps).

## The loading stage

While the game files load, the loader shows the Melbourne House title picture and plays a short speech sample. The files are M.PICTURE, M.MYTINY, M.SPCHTBL and M.TSOUND. They are not part of the game image, and both versions use the same files. **Observed** (disk files and byte compare).

| File | Load range | Content |
|---|---|---|
| M.PICTURE | `$6000-$870F` | The title picture, a Koala layout without the background byte |
| M.MYTINY | `$9000-$910F` | The 1-bit sample player |
| M.SPCHTBL | `$9800-$9AFF` | The timer counts of the sample player |
| M.TSOUND | `$2000-$35FF` | The speech sample |

The rebuild of each version shows the picture as its start screen and plays the sample. Then it waits for a key or a fire button and starts the game. Both versions take the picture from the 2010 release, because the SCC picture has a crack text. See [docs/loading_stage.md](docs/loading_stage.md#the-start-screen-of-the-rebuild).

![The Melbourne House title picture of M.PICTURE](v1/docs/images/title_picture.png)

The image shows the title picture, rendered from M.PICTURE of the 2010 disk.

The sample has 5590 bytes and plays for 2.23 seconds. Each byte gives the time to the next flip of the SID volume. The render is [loading_sample.wav](v1/docs/assets/loading_sample.wav). **Observed** (render). The details are on [docs/loading_stage.md](docs/loading_stage.md).

## The pages

| Page | Content |
|---|---|
| [v1/README.md](v1/README.md) | **Version I.** The entry page of version I, the program of R2010 and SHADOW. |
| [v2/README.md](v2/README.md) | **Version II.** The entry page of version II, the program of SCC and MRZ. |
| [docs/development.md](docs/development.md) | **The development.** How Beam Software made the two versions, as the code and the leftovers tell it. |
| [docs/versions.md](docs/versions.md) | **The versions.** Each difference between version I and version II, subsystem by subsystem. |
| [docs/releases.md](docs/releases.md) | **The releases.** The four cracked disks, their files and the traces of each crack in the game. |
| [docs/protection.md](docs/protection.md) | **The copy protection.** The CIA2 check of version II, its trap and the switch that disables it. |
| [docs/loading_stage.md](docs/loading_stage.md) | **The loading stage.** The title picture, the speech sample and its player. |

## Still open

- What did the original protected loader do, and why did it leave 0 in `$DD0E`? — An image of the original Melbourne House disk is necessary.
- Is the small figure of frames 67-71 of version I a first judge? — A run can point sprite 6 to its parts and capture the screen.
- What did the game sample of version I play? No byte of it stays. — An earlier build of the game is necessary.
- Which code of the Mr. Z crack writes 0 into `$DD0E`? — A watchpoint on `$DD0E` while the Mr. Z intro unpacks the game.
- Does a somersault at the X limit of version I move the fighter by 11 units? — A run of version I with a somersault at `fighter_x` $0C.
