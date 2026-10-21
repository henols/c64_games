# The game flow (version II)

The game flow takes the player from the power-on to the fight and back to the title. After the start-up, the program shows the title panel over a demo of two computer fighters. A key or the fire button starts a one-player game against the computer or a two-player game. A one-player game climbs the ranks from NOVICE to 10TH DAN, with a bull round after each fourth scene. One lost bout ends it. A two-player game has four bouts of 30 seconds, and a judge shows the winner. At the end of a game, the program tests the high scores and starts the demo again.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge of v2.
- A *frame* is one pass of the bout loop at raster line `$FD`, 50 each second on a PAL C64.
- A *bout* is one fight in one scene, with the clock at 30 at its start.
- An *exchange* is one run of `bout_loop` from the start positions. It ends when a fighter falls, the time ends or a start key comes.
- A *full point* is two *half points*. A fighter with 4 half points wins a one-player bout.
- A *stage* is one value of `stage_counter` in a one-player game. The scene is `stage_counter` AND 3.
- A *clear* is two won bouts in one stage. A clear gives the next rank.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The program has no separate title screen. The title is the text panel at the top of the screen, and the demo plays under it. Each game mode is a loop of bouts, and each bout is a loop of exchanges. The bout loop reads the title keys in each frame, so the keys work only while fighters are on the screen.

~~~mermaid
flowchart TB
  A["Cold start: init the machine (init_game_state)"] --> B["Title panel: high score, mode, control text"]
  B --> C["Demo: 4 bouts of two computer fighters"]
  C -- "no start key" --> B
  C -- "F1 or fire, 1 PLAYER" --> D["One-player game (game_one_player)"]
  C -- "F1 or fire, 2 PLAYER" --> E["Two-player game (game_two_players)"]
  D --> F["Top-5 high score table and name entry"]
  F --> B
  E --> B
~~~

[`cold_start` `$1AED`](../src/bout_loop.asm#L110) calls the start-up routine and jumps into the title loop. The title loop never returns. Version I has the same structure, but it has no judge, no top-5 table and no F7 or DEL key. See [../../v1/docs/game_flow.md](../../v1/docs/game_flow.md), and [../../docs/versions.md](../../docs/versions.md) for the full list of changes. (**Code**)

### The cold start and the start-up

[`program_entry` `$115A`](../src/entry_and_tables.asm#L6) jumps to `cold_start`. `cold_start` calls [`init_game_state` `$18E8`](../src/init_machine.asm#L6) and then jumps to `title_main_loop`. After the JMP, `cold_start_unused_rts` holds an RTS that no code reaches. Version I has the same byte. (**Code**) This byte is a trace of an older cold start that called the title loop with a JSR (**Conclusion**).

`init_game_state` does these steps in this order:

1. It disables the interrupts with SEI. Version I has no SEI here.
2. It writes 0 to `samples_off`, `game_mode`, `front_fighter`, `shape_page_offset` and `keyboard_control`. Thus each power-on starts with the samples on and the joystick control.
3. It calls `init_vectors_cias`. This routine switches the ROMs out (`$01` = `$05`) and sets the raster IRQ and the IRQ, NMI and RESET vectors. It also sets the CIA 2 timer B for the NMI of the floor colour. See [interrupts.md](interrupts.md).
4. It copies the two sample period tables, 256 bytes each, from [`sfx_period_lo_init` `$C700`](../src/sfx_period_tables.asm#L103) and `sfx_period_hi_init` at `$C800` to `sfx_period_lo` at `$0200` and `sfx_period_hi` at `$0300`. The loop is `init_copy_periods`.
5. It calls `init_vic_screen`. This routine sets VIC bank 3, the screen at `$CC00`, the bitmap and the panel characters at `$E000`, the colours and the panel. It enables sprites 0-5 only. Version I enabled all 8 sprites.
6. It writes `$53` to `frame_random` and 1 to `scene_shown`. The value 1 makes sure that the first bout draws scene 0.

(**Code**)

The copy of step 4 is necessary because the program uses `$C700-$C8FF` as a sprite buffer after the start-up. In the SCC release, the loader file B puts the tables there with the shapes. The sample player reads them at `$0200-$03FF` for each sample byte, see [sound_music.md](sound_music.md). (**Code**)

The seed of step 6 is a constant. The first demo after the power-on reads `frame_random` before any frame steps it. Thus the first demo is the same at each power-on (**Conclusion**). The one-player game seeds the AI from `frame_random` too. The seed then depends on the number of frames that the demo played before the start key (**Code**).

### The title loop and its keys

[`title_main_loop` `$1EE1`](../src/title_and_scene.asm#L82) writes 0 to `two_player_mode`. The loop at `title_demo_loop` then does these steps again and again:

1. It shows the single high score of the mode, with `high_score_show`.
2. It writes 1 PLAYER or 2 PLAYER, with `show_mode_text`.
3. It writes JOYSTICK or KEYBOARD, with `show_control_text`. This step is new in version II.
4. It writes 0 to `in_game` and clears both scores.
5. It plays the demo. When the demo ends without a start key, the loop starts again at step 1.
6. On a start key, it starts the game of `two_player_mode`. After a one-player game it calls `hs_table_update` and `hs_clear_panel`. Then the loop starts again at step 1.

(**Code**)

Step 6 does not go through `title_main_loop`, so `two_player_mode` keeps its value. After a two-player game, the panel shows 2 PLAYER and the two-player high score (**Code**). In version I, the title loop started a new one-player game at once when the player held the fire button. Version II has the high score table at that place (**Code**).

![The title panel over the demo: DEMO, the high score 0, KEYBOARD and 1 PLAYER](images/title_keyboard.png)

The image shows the title panel during the demo after F7. KEYBOARD is on row 3, and DEMO, the high score and 1 PLAYER are on row 4 (**Observed**).

[`read_title_keys` `$1E64`](../src/title_and_scene.asm#L6) reads the keyboard column 0 and the fire button of port 2. The bout loop calls it in each frame. The routine acts on a key only when the row value is different from `last_key_row`. It compares the full row value, so it finds a key only when the player presses no other key of column 0. (**Code**)

| Key | Row value | Effect | With `in_game` = 1 |
|---|---|---|---|
| F1 | `$EF` | Starts the game of `two_player_mode` (A = `$80`) | No effect |
| F3 | `$DF` | Changes `two_player_mode` 0 / 1, shows the mode text and the high score of the mode | No effect |
| F5 | `$BF` | Jumps to `title_main_loop` | Also works |
| F7 | `$F7` | Changes `keyboard_control` 0 / 1, shows JOYSTICK or KEYBOARD | No effect |
| INST/DEL | `$FE` | Changes `samples_off` 0 / 1 | No effect |
| Fire on port 2 | bit 4 of `$DC00` = 0 | Starts the game (A = `$80`), in each frame that the button is down | No effect |

(**Code**)

F7 and DEL are new in version II. F7 selects the keyboard control of the fighters, see [fighters.md](fighters.md). DEL stops all samples, because `sfx_sample_start` starts no sample while `samples_off` is not 0. The v1 F7 code, `LDA #$00` and RTS, stays as the last two instructions of the v2 F7 handler. (**Code**) The test `tests/keyboard_option.json` enters the F7 and the DEL handler with a register step. The panel then shows KEYBOARD, and `keyboard_control` and `samples_off` change to 1 (**Observed**).

[`title_key_f5` `$1ED1`](../src/title_and_scene.asm#L69) does not test `in_game`. Thus F5 stops a game at any time and returns to the title. The JMP does not reset the stack, so each F5 leaves 8 bytes of return addresses on the stack. (**Code**) The 6502 stack pointer wraps in page 1, and the memory map gives page 1 only to the stack. Thus many F5 presses do no damage (**Conclusion**).

A start key returns A = `$80` only while `in_game` is 0. In a game, F1 and fire have no effect, so the `BMI` tests after each exchange of a game never branch (**Conclusion**).

### The demo

[`demo_play` `$1CD2`](../src/game_modes.asm#L245) shows DEMO at the place of the rank text and gives both fighters to the computer. It writes 1 to `game_mode`, so the music driver plays tune 1. It plays 4 bouts, one in each scene, from scene 0 to scene 3. A bout ends when a fighter has 4 half points or when the time ends. The demo shows half points as yin-yang symbols, but it gives no score and calls no judge. (**Code**) The test `tests/demo.json` shows the four bouts and the scene changes (**Observed**).

The demo gives each fighter a random AI level from 3 to 11. New in version II, it seeds `ai_random` from `frame_random` first. It also writes `$FF` to `music_t1_p4_end` at `$04F0`, the end mark of a music pattern. The file already holds `$FF` there, and no other instruction writes this byte. (**Code**) The store is a leftover of a removed change to the music data, or a test (**Conclusion**).

### The one-player game

[`game_one_player` `$1BA7`](../src/game_modes.asm#L89) gives fighter 0 to the player and fighter 1 to the computer. It clears the panel texts and both scores, and it blanks the score of player 2. It seeds `ai_random` from `frame_random`, writes NOVICE at `$CCA0` and writes 2 to `game_mode` for tune 2. (**Code**)

Each bout starts with the clock at 30 and the scene of the stage. `bout_1p_exchanges` returns one of four results:

| Result | Condition | What the game does |
|---|---|---|
| 1, won | Player 1 has 4 half points, or wins the decision at time up | Bow, time bonus, and one win less to the next rank |
| 0, lost | The computer has 4 half points, or wins the decision | Bow, the game ends |
| `$81`, draw | Equal half points and equal `bout_hit_value` at time up | Both fighters bow, the same bout again |
| `$80`, key | A start key | Not possible in a game, see the title keys |

(**Code**)

One lost bout ends the game. Thus a one-player game is a series of wins, and the first loss sends the player to the high score table (**Code**).

After two won bouts, the game tests the stage. When `stage_counter` AND 3 = 3, it calls [`bull_bonus_round` `$132C`](../src/bull_round.asm#L46) first. That is after each clear in scene 3. See [bull_round.md](bull_round.md). Then [`game_1p_rank_cap_test` `$1C27`](../src/game_modes.asm#L149) compares `stage_counter` with 10. (**Code**)

- **Below 10, a promotion.** The game increments the rank index in `cpu_skill+1` and `stage_counter`. It reads `rank_number_table`, keeps the rank in `player_rank` and prints the new rank text. The rank index is also the AI level of the computer, so the opponent gets stronger with each rank. (**Code**)
- **10 or more, the wrap.** [`game_1p_rank_wrap` `$1C5B`](../src/game_modes.asm#L176) increments `stage_counter` and keeps only the scene: the value becomes `$20` + (n AND 3). The AI level of the computer becomes 7 + a random value 0-3. The rank text stays 10TH DAN. (**Code**)

The rank cap corrects the rank overflow of version I. Version I compared `stage_counter` with `$16`. Its rank index went past the 12 entries of the rank table into code bytes, and the rank text broke, for example "|||TH DANN". See [../../v1/docs/game_flow.md](../../v1/docs/game_flow.md). (**Observed** in v1 `tests/rank_overflow.json`) In version II, `tests/rank_cap.json` sets the stage 9 and wins the next clear. The rank text stays 10TH DAN (**Observed**). That test sets the rank index to 10 at stage 9, so its promotion reads entry 11 of the table. Entry 11 also holds 10. In a normal game the rank index equals `stage_counter`, so the game never reads entry 11 (**Code**).

The wrap also gives a weaker opponent. At 10TH DAN the computer has AI level 10, and in the next stages it has 7 to 10 (**Code**). The test `tests/one_player_cpu_bull.json` lets the computer play for player 1. It wins three ranks and reaches the bull round (**Observed**).

### The two-player game

[`game_two_players` `$1B09`](../src/game_modes.asm#L6) gives both fighters to the players. It writes 3 to `game_mode` for tune 3. It plays 4 bouts, one in each scene, and each bout lasts the full 30 seconds. No fighter wins a bout. Each hit gives score points to the player who hits. The hit code draws a yin-yang symbol at the moment of the hit, and `bout_2p_exchanges` clears it after the exchange. (**Code**)

The two-player game has two pauses that version I does not have. Between two bouts, `wait_frames_x6` waits 90 frames, about 1.8 seconds. After the high score test at the end, it waits 120 frames, about 2.4 seconds. (**Code**)

After the fourth bout, [`game_2p_last_bout` `$1B5A`](../src/game_modes.asm#L43) decrements `stage_counter` from 4 to 3. Thus the judge stands at the place of scene 3, the scene on the screen. `score_compare_players` compares the six digits of both scores. The winner gets the judge and the bow. Equal scores give a bow of both fighters and no judge. Then `high_score_update` tests the score of the winner against the two-player high score. (**Code**) This decrement is a patch for the judge, in place of a change of the bout loop (**Conclusion**).

The recording `tests/record/two_player.json` plays a two-player game with both joysticks to the judge at the end (**Observed**). No run reached equal scores (**Observed**: the coverage shows no run of `$1B61-$1B68`).

### The judge

[`judge_show_winner` `$1F93`](../src/score_and_judge.asm#L43) shows the winner of a decision with two sprites. Sprite 6 is the judge, in grey (colour `$0C`). Sprite 7 is the flag of the judge, in the colour of the winner: 1 (white) for fighter 0, 2 (red) for fighter 1. The scene selects the judge sprite and its place from four tables. Then the routine enables sprites 6 and 7. (**Code**)

The judge comes at three places: a one-player decision for player 1, a one-player decision for the computer, and the end of a two-player game. The demo calls no judge. (**Code**) The runs executed all three calls (**Observed**: coverage).

In version I, these three calls go to `winner_stub`, a lone RTS. The v1 sprite multiplexer already keeps the X bit 8 of sprites 6 and 7. The v1 bout loop also keeps sprites 6 and 7 in the enable register. (**Code**) Thus the authors planned the judge in version I and completed it in version II (**Conclusion**). See [../../docs/versions.md](../../docs/versions.md).

The judge sprites stay on after the decision. [`bout_prepare_scene` `$1F3A`](../src/title_and_scene.asm#L134) switches them off with `SPENA` = `$3F` before each bout. No other code writes `SPENA` between the end of a game and the first bout of the demo. (**Code**) Thus the judge is visible during the end pause of a two-player game. After a one-player loss by decision, the judge stays visible during the high score table too (**Conclusion**).

![The judge sprite of scenes 2 and 3 at $D400, in multicolour](reference/images/judge_sprite_scene23-multicolour.png)

The image shows the judge sprite `judge_sprite_scene23`, decoded from the bytes of the program (**Code**).

### The bout loop

[`bout_loop` `$1A7C`](../src/bout_loop.asm#L54) plays one exchange. It puts both fighters at the start positions, x `$3E` and `$5A`. Then it waits for raster line `$FD` in each frame and does these steps:

1. It updates fighter 1 and then fighter 0, with `fighter_update`.
2. It steps `frame_random` once.
3. It calls `read_title_keys`. A start key ends the exchange with A = `$80`.
4. It ends the exchange when `bout_knockdown` is not 0, that is when a fighter falls.
5. It steps the clock with `timer_tick`. It does this only when no fighter is in a hit reaction and fighter 0 is not in the start move `$17`.
6. At time up, it shows frame `$37` of both fighters on the ground and returns A = 1.

(**Code**) The loop is the same as in version I. Only the time-up redraw calls the new entry of `shape_build` (**Code**).

Step 5 stops the clock while a fighter falls. Thus a bout lasts longer than 30 seconds of real time. The clock also waits until player 1 moves at the start of each exchange. (**Code**)

The mode handlers call `bout_loop` again and again. After each exchange, they look at `hit_reaction` of both fighters. The value of each reaction move has a 1 in bit 4. The handler gives the points only when exactly one fighter has a hit reaction. (**Code**) See [combat.md](combat.md) for the hits.

### Points, scores and the clock

A full-point hit gives 2 half points, and a half-point hit gives 1. [`add_half_points` `$1D5F`](../src/game_modes.asm#L321) adds them and draws the symbols. One half point is a half yin-yang, and two are a full yin-yang. The symbols of player 1 grow from column 6 to column 3, and the symbols of player 2 from column 32 to column 35. (**Code**)

[`score_add_move` `$206C`](../src/score_and_judge.asm#L173) adds the value of the scoring move from `move_score_values`. A full point gives 200, 400, 600, 800 or 1000 points by the move. A half point gives half of that. The routine adds the points as steps of 100 with `score_add_100`. A score above 999900 becomes 000000, but no run reached this. (**Code**) In a one-player game, only player 1 gets score points. The computer gets only half points (**Code**).

At a time-up decision of a one-player bout, the fighter with more half points wins. With equal half points, the larger `bout_hit_value` wins, the sum of the move values of the hits. `bout_hit_value_add` reads `hit_points` of fighter 0 also for fighter 1, a bug of version I that stays. (**Code**) See [combat.md](combat.md).

[`timer_tick` `$212F`](../src/timer_and_texts.asm#L24) counts 50 frames for each second. It decrements the clock digits at `$CC3B` and `timer_seconds`, and it writes a space for the tens digit below 10. At 0 it sets `time_up`. (**Code**)

When player 1 wins a bout with 4 half points, [`time_bonus_count` `$21DF`](../src/timer_and_texts.asm#L140) counts the clock to 0. It adds 100 points for each second, with a pause of 6 frames each. Thus the bonus is 100 times the number on the clock. A win by decision gives no bonus, because the clock is already at 0. (**Code**)

### The high score at the end of a game

The program keeps two single high scores, `high_score_1p` and `high_score_2p`, and shows the score of the mode on row 4 of the panel. [`high_score_update` `$200A`](../src/score_and_judge.asm#L102) copies the score of a player when it is higher. (**Code**)

At the end of a one-player game, `game_1p_over` updates and shows the one-player high score. The title loop then calls [`hs_table_update` `$146A`](../src/high_score_table.asm#L6), the top-5 table with the rank and a name of 6 letters. This table is new in version II. A held fire button skips the table, and the new entry keeps the name "......". See [high_scores.md](high_scores.md). (**Code**) A two-player game updates only the single two-player high score (**Code**).

## The data

### The panel

The panel is the text rows 0-4 of the screen at `$CC00`, with the characters of `panel_font`. The colour RAM of these rows is 6 (blue), and the yin-yang cells are `$0E`. The raster interrupt sets the background colour 3 for the panel. See [graphics.md](graphics.md). (**Code**)

| Cells | Row, columns | Content |
|---|---|---|
| `$CC03-$CC07`, `$CC2B-$CC2F` | rows 0-1, columns 3-7 | Yin-yang symbols of player 1 (2 x 2 characters each) |
| `$CC20-$CC24`, `$CC48-$CC4C` | rows 0-1, columns 32-36 | Yin-yang symbols of player 2 |
| `$CC31-$CC36` | row 1, columns 9-14 | Score of player 1 |
| `$CC3B-$CC3C` | row 1, columns 19-20 | The clock, 30 to 0 |
| `$CC41-$CC46` | row 1, columns 25-30 | Score of player 2, blank in a one-player game |
| `$CC97-$CC9E` | row 3, columns 31-38 | JOYSTICK or KEYBOARD (new in version II) |
| `$CCA0-$CCA7` | row 4, columns 0-7 | The rank text or DEMO |
| `$CCB1-$CCB6` | row 4, columns 17-22 | The high score of the mode |
| `$CCBF-$CCC6` | row 4, columns 31-38 | 1 PLAYER or 2 PLAYER |

(**Code**) The title image shows the texts of rows 1, 3 and 4 (**Observed**).

### The rank texts

[`print_rank_text` `$21FB`](../src/timer_and_texts.asm#L157) writes the rank X at `text_dest_ptr` + `rank_text_offset`. Rank 0 is NOVICE. Ranks 1-9 are the digit and ST, ND, RD or TH and DAN, for example 2ND DAN. Rank 10 is the text 10TH DAN. The panel uses the offset 0. The high score table uses the offset 1, and then the three forms end in the same column. (**Code**) The 1ST, 2ND and 3RD suffixes are also in version I (**Code**).

`rank_number_table` holds 0, 1-9, 10, 10. The game reads it with the rank index. (**Code**)

### The judge tables

`judge_show_winner` reads four tables of 4 bytes by scene: `judge_ptr_by_scene`, `judge_x_by_scene`, `judge_msb_by_scene` and `judge_y_by_scene`. The pointer selects the place of the flag. With pointer `$5C`, the flag is 2 pixels left of the judge and 6 lines lower. With pointer `$50`, the flag is 4 pixels right of the judge, on the same line. (**Code**)

| Scene | Judge pointer | Judge block | Judge X, Y | Flag X, Y |
|---|---|---|---|---|
| 0 | `$5C` | `judge_sprite_scene01` | `$112`, `$9E` | `$110`, `$A4` |
| 1 | `$5C` | `judge_sprite_scene01` | `$120`, `$99` | `$11E`, `$9F` |
| 2 | `$50` | `judge_sprite_scene23` | `$58`, `$94` | `$5C`, `$94` |
| 3 | `$50` | `judge_sprite_scene23` | `$46`, `$96` | `$4A`, `$96` |

The flag uses pointer `$51`, `judge_flag_sprite` at `$D440`, in each scene. The X values are sprite coordinates with bit 8 from `judge_msb_by_scene`. Thus the judge stands at the right in scenes 0 and 1 and at the left in scenes 2 and 3. (**Code**) The routine reads back the pointer that it stored and compares it with `$5C`. The authors added the place of the flag after the four tables (**Conclusion**).

## The state machine of the game modes

`game_mode` holds the mode: 0 at the start-up, 1 demo, 2 one player, 3 two players, 4 name entry. The music driver also plays the tune of this number. [`demo_play` `$1CD2`](../src/game_modes.asm#L245), the two game routines and the name entry make the changes. (**Code**)

~~~mermaid
stateDiagram-v2
  state "Start-up (0)" as Boot
  state "Demo (1)" as Demo
  state "One player (2)" as One
  state "Two players (3)" as Two
  state "Name entry (4)" as Name
  [*] --> Boot
  Boot --> Demo: title loop
  Demo --> Demo: 4 bouts, no start key
  Demo --> One: F1 or fire, mode 0
  Demo --> Two: F1 or fire, mode 1
  One --> Name: lost bout, score in the top 5
  One --> Demo: lost bout, not in the top 5
  Name --> Demo: 6 letters, RETURN or fire
  Two --> Demo: 4 bouts, judge, pause
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Start-up `0` | `cold_start` jumps to the title loop | Demo `1` | `demo_play` |
| Demo `1` | The fourth bout ends with no start key | Demo `1` | `title_demo_loop` |
| Demo `1` | F1 or fire, `two_player_mode` = 0 | One player `2` | `game_one_player` |
| Demo `1` | F1 or fire, `two_player_mode` = 1 | Two players `3` | `game_two_players` |
| One player `2` | A lost bout, the score is in the top 5 | Name entry `4` | `hs_name_entry` |
| One player `2` | A lost bout, the score is not in the top 5, or the player holds fire | Demo `1` | `demo_play` |
| Name entry `4` | 6 letters, RETURN or fire | Demo `1` | `demo_play` |
| Two players `3` | The end pause of the fourth bout | Demo `1` | `demo_play` |
| Any | F5 | Demo `1`, mode 1 PLAYER | `title_key_f5` |

(**Code**)

## The state machine of a one-player bout

A one-player bout is a loop of exchanges. The clock and the half points stay from one exchange to the next. [`bout_1p_exchanges` `$1C72`](../src/game_modes.asm#L189) makes each change. The demo has the same states without the score, the judge and the time bonus. The two-player bout has only the exchange and the score, until time up. (**Code**)

~~~mermaid
stateDiagram-v2
  state "Exchange (bout_loop)" as Ex
  state "Points" as Pts
  state "Decision" as Dec
  state "Judge" as Judge
  state "Bow" as Bow
  state "Time bonus" as Bonus
  [*] --> Ex
  Ex --> Pts: a fighter falls
  Pts --> Ex: less than 4 half points
  Pts --> Bow: 4 half points
  Ex --> Dec: time up
  Dec --> Judge: more half points or hit value
  Dec --> [*]: draw, both bow
  Judge --> Bow
  Bow --> Bonus: player 1 won
  Bow --> [*]: computer won
  Bonus --> [*]
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Exchange | A fighter falls (`bout_knockdown` not 0) | Points | `bout_loop` |
| Exchange | `time_up` = 1 | Decision | `bout_loop` |
| Points | Exactly one fighter has a hit reaction, less than 4 half points | Exchange | `add_half_points` |
| Points | A fighter has 4 half points | Bow | `bow_winner` |
| Decision | Different half points, or equal half points and different `bout_hit_value` | Judge | `judge_show_winner` |
| Decision | Equal half points and equal `bout_hit_value` | End, result `$81` | `bout_1p_draw` |
| Judge | The sprites are on | Bow | `bow_winner` |
| Bow | Fighter 0 won | Time bonus | `time_bonus_count` |
| Bow | Fighter 1 won | End, result 0 | `bout_1p_lost` |
| Time bonus | The clock is at 0 | End, result 1 | `time_bonus_count` |

(**Code**)

## The worked example: the stages of a one-player game

This table follows a one-player game from the code of `game_one_player`, clear by clear. A clear is two won bouts. (**Code**)

| Clear | `stage_counter` before | Scene | Bull round | `stage_counter` after | Rank text after | AI level of the computer after |
|---|---|---|---|---|---|---|
| (start) | - | 0 | - | 0 | NOVICE | 0 |
| 1 | 0 | 0 | no | 1 | 1ST DAN | 1 |
| 2 | 1 | 1 | no | 2 | 2ND DAN | 2 |
| 3 | 2 | 2 | no | 3 | 3RD DAN | 3 |
| 4 | 3 | 3 | yes | 4 | 4TH DAN | 4 |
| 8 | 7 | 3 | yes | 8 | 8TH DAN | 8 |
| 10 | 9 | 1 | no | 10 | 10TH DAN | 10 |
| 11 | 10 (`$0A`) | 2 | no | `$23` | 10TH DAN | 7-10 |
| 12 | `$23` | 3 | yes | `$20` | 10TH DAN | 7-10 |
| 13 | `$20` | 0 | no | `$21` | 10TH DAN | 7-10 |
| 16 | `$23` | 3 | yes | `$20` | 10TH DAN | 7-10 |

Clear 11 is the first wrap: 10 + 1 = 11, and 11 AND 3 = 3, so the value is `$20` + 3 = `$23`. The scenes go on in the order 0, 1, 2, 3. Thus the bull round comes after clears 4, 8, 12, 16 and each fourth clear after them. (**Code**) The recording `tests/record/cpu_ranks.json` lets the computer play for player 1 through all ranks and several bull rounds (**Observed**).

## Still open

- F1, F3 and F5 — no run pressed these keys. The runs write `two_player_mode` and start the game with fire or a register step. A run that types F3 and F5 in the demo can show the mode change and the return to the title.
- The judge on the screen — no screen of this page shows sprites 6 and 7. A run that forces a time-up decision in each scene can show the shapes, the place of the flag and the colours.
- The judge after a one-player loss by decision — the code leaves sprites 6 and 7 on during the high score table. A run that loses a bout by decision can show it.
- The draw of a two-player game (`$1B61-$1B68`) — no run executed it. A run with equal scores after four bouts can show the bow of both fighters.
- The score overflow above 999900 — no run reached it. A run that writes a high score into the panel digits can test it.
