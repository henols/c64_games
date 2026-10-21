# Version I and version II

The Way of the Exploding Fist exists in two versions of the game program. Version I is the program of the releases R2010 and SHADOW. Version II is the program of the releases SCC and MRZ. The 2010 crack screen of version I says "WAIT FOR VERSION II". This page lists each difference between the two programs, subsystem by subsystem. The pages of each version explain each part in depth.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge. The label `v1:` marks a name of version I. The label `v2:` marks a name of version II.
- In the tables, the column v1 gives the address in version I. The column v2 gives the address in version II. A dash means that the version does not have the part.
- A *move* is the v2 address minus the v1 address, for example +$0B.
- A *scene* is one of the four backgrounds. Scene 3 is the Buddha statue.
- *Fighter 0* is player 1, the white fighter. *Fighter 1* is player 2, the red fighter, or the computer, or the bull.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

The tables come from an instruction alignment of the two programs and from the generated source of each version. 4378 of the 4737 instructions of version I have a match in version II. A fact in a table is **Code** when the table does not give a different mark.

## Overview

Version II is the same game with five new features, three corrections and one copy protection check. The authors kept almost all code of version I and moved it to make space for the new parts (**Code**).

The new features:

- **Keyboard control.** F7 on the title selects JOYSTICK or KEYBOARD. With KEYBOARD, player 1 uses the keys `Q W E`, `A D`, `Z X C` and fire `S` or LEFT SHIFT. In version I, F7 does nothing. **Observed** in [keyboard_option.json](../v2/tests/keyboard_option.json).
- **A high score table with names.** After each one-player game, a table shows the 5 best scores with the rank and a name of 6 letters. A new entry gets a name entry with tune 4 as its music. Version I keeps only one high score for each mode. **Observed** in the recording one_player_moves of version II.
- **Live samples.** Four digitized sounds play: a knockdown, a hit, the swish of an attack and a fall to the floor. DEL on the title disables and enables them. Version I has the sample player, but no code calls it. **Observed** (renders of the samples) and **Code**.
- **The bull bonus round.** After each promotion in scene 3, a bull runs at the player. A low punch at the right time stops it for 3000 points. A run without a hit gives 500 points. In version I, the round is a test routine that nothing calls. **Observed** in [one_player_cpu_bull.json](../v2/tests/one_player_cpu_bull.json).
- **The judge.** At a decision by time and at the end of a two-player game, a judge sprite shows the winner with a flag. Version I calls a lone RTS at the same three places (**Code**).

The corrections:

- **The rank cap.** Version II stops the promotions at 10TH DAN. Version I promotes the player to rank 22 and shows garbage text after 10TH DAN. **Observed** in [rank_overflow.json](../v1/tests/rank_overflow.json) and [rank_cap.json](../v2/tests/rank_cap.json).
- **The correction of tune 1.** In version I, voice 0 of the demo tune continues in the order list of voice 1 and never plays pattern 2. Version II adds 2 bytes, and the three voices loop together (**Code**).
- **The X limits by facing.** Version I refuses each step out of the range $0C-$94. Version II clamps the position to a limit that depends on the facing of the fighter (**Code**).

The copy protection: only version II has a check. On each scoring hit, the hit test reads CIA2 control A at $DD0E. A value that is not 0 sends the CPU into a trap. After a KERNAL reset, $DD0E holds $08, and the game crashes at the first point. **Observed** in [protection_trap_original.json](../v2/tests/protection_trap_original.json). The details are on [protection.md](protection.md).

Version II also changes the computer opponent, packs the scene maps and gives the bull new sprite places. The sections below list each change.

![Version I after 10TH DAN: the rank text shows garbage](../v1/docs/images/rank_overflow.png)

The image shows the panel of version I after the rank overflow.

## How the layout moved

Version II has the same order of parts as version I, but most parts start at a new address. Four rules give most of the moves (**Code**):

1. **The zero page moves by +$0B.** The variables v1 `$3A-$B5` are at v2 `$45-$C0`. The variables `$00-$38` keep their addresses. The new variables are at `$3E-$44`, for the sample player and the map unpacker. More new variables are at `$C2-$CF`, for the bull, the keyboard, the high score table and the sample switch. The copy pointers v1 `$AC-$AF` have no use in version II.
2. **The music and the tables after it move by +2.** The music driver and the music data `$0400-$0FCD` keep their addresses. The correction of tune 1 adds 2 bytes at `$0FCE`. Thus the entry goes from `$1158` to `$115A`, and the move tables go from `$115B` to `$115D`.
3. **The code moves by +$4D4 to +$7DE.** New code goes between the old parts, so the move grows from the start to the end. The init moves by +$4D4, the bout set-up by +$4EC and the AI by +$587. The fighter update moves by +$5D5 and the raster handlers by +$72D. The animation moves by +$797, and the end of the shape builder by +$7DE.
4. **The scene bitmaps move by +$5CB.** The packed bitmaps v1 `$3994-$62FF` are at v2 `$3F5F-$68CA`, with the same bytes.

The move of the bitmaps has an exact cause. Version I keeps the 8 scene maps unpacked, 3840 bytes at `$6300-$71FF`. Version II packs them with a nibble run-length code into 2357 bytes at `$68CB-$71FF`. The difference is 1483 bytes, that is $5CB, the move of the bitmaps (**Code**). **Conclusion:** the authors packed the maps to get space for the new code. They kept the end of the maps at `$71FF` and moved the bitmaps up against the maps.

The old bull test code moves down by $67, from v1 `$1354` to v2 `$12ED`. It now sits in front of the new high score code. From `$7200` on, the data tables start at the same addresses. Inside them, the animation scripts move by +4 and more, because the script table has 2 new entries (**Code**).

The sprite graphics change place where the samples need memory. Version I keeps the bull at `$F540-$FF7F` and copies it with the CPU. Version II puts the 4 samples there. It moves the 41 bull blocks to places that the VIC-II can show without a copy (**Code**).

### The memory map of both versions

| Contents | v1 | v2 | Move or change |
|---|---|---|---|
| Zero page, low part | `$00-$38` | `$00-$38` | same |
| Zero page, main variables | `$3A-$B5` | `$45-$C0` | +$0B |
| New zero-page variables | - | `$3E-$44`, `$C2-$CF` | new |
| Sample period tables | `$0E00`, `$0F00` (music code) | `$0200-$03FF` | new place, copied from `$C700-$C8FF` |
| Music data and driver | `$0400-$0FCD` | `$0400-$0FCD` | same |
| Music tables after tune 1 | `$0FCE-$1157` | `$0FCE-$1159` | +2 |
| Entry | `$1158` | `$115A` | +2 |
| Move tables, scores, texts | `$115B-$12CD` | `$115D-$12CF` | +2 |
| AI substitution, X limits | - | `$12D0-$12EC` | new |
| Bull round code | `$1354-$1413` (dead) | `$12ED-$1469` | -$67, live |
| High score table and key scanner | - | `$146A-$17BA` | new |
| Scene bitmap unpacker | `$12CE-$1353` | `$17BB-$1840` | +$4ED |
| Scene map unpacker | `$19F6-$1A62` (copy) | `$1841-$18E7` | new code |
| Init | `$1414-$1535` | `$18E8-$1A21` | +$4D4 to +$4EA |
| Bout loop, game modes, scores, texts | `$1536-$1D47` | `$1A22-$22CE` | +$4EC to +$587 |
| AI and AI tables | `$1D48-$2232` | `$22CF-$2807` | +$587 to +$5D5 |
| Fighter update, input, hit test | `$2233-$2634` | `$2808-$2D61` | +$5D5 to +$72D |
| Raster handlers, NMI, sample player | `$2635-$2A65` | `$2D62-$31F1` | +$72D to +$78C |
| Frame-start IRQ, multiplexer | `$2A66-$3025` | `$31F2-$37BC` | +$78C to +$797 |
| Animation, shape builder | `$3026-$36A1` | `$37BD-$3E7F` | +$797 to +$7DE |
| RAM pattern | `$36A2-$3993` | `$3E80-$3F5E` | smaller |
| Packed scene bitmaps | `$3994-$62FF` | `$3F5F-$68CA` | +$5CB, same bytes |
| Scene maps | `$6300-$71FF` (plain) | `$68CB-$71FF` (packed) | packed |
| Hit zones, scripts, part tables | `$7200-$7DFF` | `$7200-$7DFF` | same start, see the graphics |
| Mirror table, part page table | `$7E00-$7FFF` | `$7E00-$7FFF` | same |
| Fighter part graphics | `$8000-$BFFF` | `$8000-$BFFF` | same bytes |
| Sprite buffers | `$C000-$C93F` | `$C000-$C93F` | same |
| Sprites `$C940-$CBFF` | unused figures | bull blocks | changed |
| Sprites `$D000-$DFFF` | figures, shadows, old bull copy | judge, shadows, bull blocks | changed |
| Panel charset | `$E000-$E3FF`, 128 characters | `$E100-$E2FF`, 64 characters | cut, bull blocks around it |
| Scene bitmap rows 5-16 | `$E640-$F53F` | `$E640-$F53F` | same |
| `$F540-$FFDD` | bull sprites (M.XSPRITES) | sample table and 4 samples | changed |
| NMI, RESET, IRQ vectors | `$28A5`, `$14A6`, `$2A66` | `$2FF2`, `$1990`, `$31F2` | moved code |

The memory maps of the reference give each variable: [v1](../v1/docs/reference/memory-map.md) and [v2](../v2/docs/reference/memory-map.md).

## The routines of version I in version II

The table gives the routines of version I with their addresses in version II, in groups. The routines of a group keep their order. A routine that changed has a row of its own. The subsystem sections below give the details.

| v1 routine | v1 | v2 | Change |
|---|---|---|---|
| music_play_frame and the music driver | `$09A5-$0F51` | `$09A5-$0F51` | none |
| scene_unpack_bitmap, scene_dest_back, scene_src_back | `$12CE` | `$17BB` | none |
| dev_clear_part_ptrs | `$1354` | `$12ED` | none, still not called |
| dev_update_fighter | `$135F` | `$12FC` | used by the bull round, new entry `$12F8` |
| dev_setup_fighter0 | `$1371` | `$130E` | called by the bull round |
| dev_bull_test | `$138F` | `$132C` | now bull_bonus_round |
| init_game_state | `$1414` | `$18E8` | SEI, sample tables, new switches |
| panel_colour_fill to init_vectors_cias | `$142B-$1459` | `$1915-$1943` | new vectors only |
| init_vic_screen | `$14A7` | `$1991` | sprites 0-5 on, not 0-7 |
| bout_setup_fighters, bout_reset_fighter, bout_loop | `$1536-$1590` | `$1A22-$1A7C` | new shape entry at time up |
| cold_start, clear_blank_sprite, frame_random_step | `$1601-$1613` | `$1AED-$1AFF` | none |
| game_two_players | `$161D` | `$1B09` | pauses, judge |
| game_one_player | `$16A9` | `$1BA7` | bull round, rank cap |
| demo_play | `$17BF` | `$1CD2` | random seed, store to `$04F0` |
| bout exchanges, points, yin-yangs, bows | `$175F-$1928` | `$1C72-$1E44` | new yin-yang characters |
| read_title_keys | `$1948` | `$1E64` | F7 and DEL |
| title_main_loop | `$19A7` | `$1EE1` | high score table, no restart on fire |
| scene_blank_rows | `$19E2` | `$1F1E` | now scene_clear_bitmap |
| scene_copy_maps | `$19F6` | `$1849` | now scene_unpack_maps |
| scene_draw_if_new | `$1A63` | `$1F3F` | maps before the bitmap |
| score_clear, score_compare_players | `$1A81-$1A98` | `$1F5D-$1F74` | none |
| winner_stub | `$1AB7` | `$1F93` | now judge_show_winner |
| high_score_update to bout_hit_value_add | `$1AB8-$1C17` | `$200A-$2169` | none |
| timer_show_30 to time_bonus_count | `$1C29-$1C8E` | `$217B-$21DF` | none |
| print_rank_text | `$1CAA` | `$21FB` | text offset for the high score table |
| clear_rank_text | `$1D22` | `$227F` | none |
| ai_update | `$1D48` | `$22CF` | new rules |
| ai_next_random, ai_setup_level, special actions 1-8 | `$1FF3-$20F3` | `$2589-$2689` | none |
| fighter_update | `$2233` | `$2808` | none |
| fighter_get_input | `$225F` | `$2834` | keyboard path |
| move_update_state | `$22B7` | `$29B4` | sample 3 |
| move_anim_end, move_fix_input | `$2381-$23E4` | `$2A8F-$2AF2` | end of a low attack |
| move_start_anim | `$2438` | `$2B46` | sample 2 |
| hit_check, hit_test, hit_range_test | `$2459-$25D3` | `$2B70-$2D00` | protection check, samples 0 and 1 |
| raster row handlers | `$2635-$2813` | `$2D62-$2F59` | new IRQ entry test, waits in two handlers |
| irq_bitmap_on | `$2869` | `$2FB0` | IRQ one line earlier, then a wait |
| nmi_floor_colour, row-4 handlers, irq_frame_end | `$28A5-$2994` | `$2FF2-$30E5` | new IRQ entry test |
| sfx_sample_irq | `$29C8` | `$311A` | live |
| sfx_sample_start | `$2A0A` | `$3186` | 8 entries in front of it |
| irq_frame_start and the multiplexer patches | `$2A66-$2FE0` | `$31F2-$3777` | new IRQ entry test, earlier IRQ for one layout |
| anim_update, anim_step, anim_setup | `$3026-$30DE` | `$37BD-$3885` | X limits by facing |
| shape_build | `$316D` | `$3914` | new entry for direct pointers |
| shape_copy_mirrored_part | `$365F` | `$3E3D` | none |

## Game flow and title

The pages: [v1 game flow](../v1/docs/game_flow.md) and [v2 game flow](../v2/docs/game_flow.md).

The game flow of version II has the same modes as version I: the demo, one player and two players. The title loop [`v1:title_main_loop` `$19A7`](../v1/src/title_and_scene.asm#L64) is [`v2:title_main_loop` `$1EE1`](../v2/src/title_and_scene.asm#L82) in version II. After a one-player game, version II shows the high score table. Version I started a new game at once when fire was still down. In the one-player game [`v2:game_one_player` `$1BA7`](../v2/src/game_modes.asm#L89), the test [`v2:game_1p_rank_cap_test` `$1C27`](../v2/src/game_modes.asm#L149) stops the promotions at stage 10 (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| `$1948` | `$1E64` | read_title_keys | F7 toggles keyboard_control and shows JOYSTICK or KEYBOARD. DEL toggles samples_off. The v1 F7 code (LDA #0, RTS) stays as the tail at `$1ECE`. |
| `$19A7` | `$1EE1` | title_main_loop | Calls show_control_text. The one-player path calls hs_table_update and hs_clear_panel. The v1 restart while fire is down (`$19D0`) is gone. |
| `$16A9` | `$1BA7` | game_one_player | Sets rank_text_offset and player_rank. Calls bull_bonus_round at `$1C24` when stage_counter AND 3 is 3. |
| `$1719` | `$1C29` | rank cap | CMP #$0A in place of CMP #$16. After 10TH DAN, the next stages wrap, and the level of the opponent is random 7-10 (v1: 2-10). The rank text stays 10TH DAN (**Observed**). |
| `$161D` | `$1B09` | game_two_players | A pause of 90 frames between the bouts. After bout 4, stage_counter goes back to 3 for the judge. The judge shows the winner. A pause of 120 frames at the end. |
| `$17BF` | `$1CD2` | demo_play | Copies frame_random to ai_random (v1: no seed). Writes $FF to `$04F0`, a music byte that already holds $FF. |
| `$1AB7` | `$1F93` | winner_stub, now judge_show_winner | A lone RTS in version I. The judge in version II. |
| `$1CAA` | `$21FB` | print_rank_text | A column offset for the rank text, also in the high score table. The ST, ND, RD and TH suffixes are the same in both versions. |
| `$1C53` | `$21A5` | clear_demo_text_old, now clear_panel_texts | Unused in version I. Version II clears 8 cells of two texts and calls it from both game modes. |
| `$1D2D-$1D47` | `$22B4-$22CE` | rank texts and rank_number_table | Same bytes. Version II reads only the entries 0-10. |
| - | `$228A-$22B3` | show_control_text, text_joystick, text_keyboard | New. |
| - | `$1F3A` | bout_prepare_scene | New: switches the judge sprites 6 and 7 off before each bout. |
| `$14A7` | `$1991` | init_vic_screen | Sprites 0-5 on (v1: 0-7). |
| `$1414` | `$18E8` | init_game_state | Starts with SEI. Clears samples_off and keyboard_control. Copies the sample period tables. |

![The title of version II with the control option](../v2/docs/images/title_keyboard.png)

The image shows KEYBOARD above "1 PLAYER" on the title of version II.

## The high score table

The page: [v2 high scores](../v2/docs/high_scores.md). Version I has no table. Its two high scores stay in version II at `$1299` and `$129F`.

After each one-player game, [`v2:hs_table_update` `$146A`](../v2/src/high_score_table.asm#L6) puts the score into a table of 5 entries. A new entry gets a name entry [`v2:hs_name_entry` `$1762`](../v2/src/high_score_table.asm#L400). The name entry sets game_mode to 4, and the music driver then plays tune 4. Tune 4 is in version I too, but no event plays it (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| - | `$146A` | hs_table_update | New. Finds the place, shows the table, and starts the name entry. |
| - | `$150F`, `$155A` | key_scan, key_get_char | New: a keyboard scanner that gives one PETSCII character for each key press. |
| - | `$163A` | hs_find_place | New: compares the score with the 5 entries and moves the lower entries down. |
| - | `$1762` | hs_name_entry | New: 6 characters, DEL deletes, RETURN or fire ends the entry. |
| - | `$1715`, `$1733`, `$1751` | hs_names, hs_scores, hs_ranks | New data: 5 names, 5 scores, 5 ranks. |
| `$1297`, `$129D` | `$1299`, `$129F` | high_score_1p, high_score_2p | Same use, +2. |

## The bull round

The pages: [v2 bull round](../v2/docs/bull_round.md) and, for the test code of version I, [development.md](development.md).

Version I has a complete test of a bull run, [`v1:dev_bull_test` `$138F`](../v1/src/dev_bull_test.asm#L42), but nothing calls it. **Observed** in the test [bull_test.json](../v1/tests/bull_test.json): a stub starts it, and the bull runs at the white fighter. Version II makes it the bonus round [`v2:bull_bonus_round` `$132C`](../v2/src/bull_round.asm#L46). The one-player game calls it after the two wins of each stage in scene 3. A new table [`v2:bull_reach_by_frame` `$142F`](../v2/src/bull_round.asm#L195) replaces the sprite collision test (**Code**).

| Point | v1 `$138F-$1413` | v2 `$132C-$1469` |
|---|---|---|
| Caller | none | game_one_player at `$1C24`, each stage with stage_counter AND 3 = 3 |
| Set-up | only the bull | sprites 0-5, fighter 0, the bull in the front sprites, bull_state 0 |
| Contact | sprite collision `$D01E` AND $18 | bull_reach_by_frame: a reach for each frame of fighter 0, $80 = no reach |
| Stop | frame $0D at distance $1A-$1E, in each frame | frame $0D only at the start of a new step, distance $19-$1D |
| After a stop | the run starts again | bull_state $80, the bull falls, the round ends |
| A hit | hit reaction $16 in each contact frame | one hit reaction $16, sample 1, bull_state 1 |
| End | bull x = 0 after any step | at the end of a run, then exit animations $1E or $1F |
| Points | 3000 for the stop | 3000 for the stop, 500 for a run without a hit |
| Speed | 10 frames for each pose | 4 frames for each pose |
| Sprites | CPU copy from `$F540`, page offset $40 | direct sprite pointers (shape_direct_ptrs) |

**Conclusion:** a somersault or a flying kick lets the bull pass, because their frames have no reach. The plain jump frames are in reach.

## The judge

The page: [v2 game flow](../v2/docs/game_flow.md).

Version I calls [`v1:winner_stub` `$1AB7`](../v1/src/score_and_timer.asm#L43) at a decision by time and at the end of a two-player game. It is a lone RTS. Version II calls [`v2:judge_show_winner` `$1F93`](../v2/src/score_and_judge.asm#L43) at the same three places. Sprite 6 shows the judge in grey. Sprite 7 shows a flag in the colour of the winner. The position comes from 4 tables by scene (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| `$1AB7` | `$1F93` | winner_stub, now judge_show_winner | A lone RTS, now the judge code. |
| - | `$1FFA-$2009` | judge_ptr_by_scene, judge_x_by_scene, judge_msb_by_scene, judge_y_by_scene | New tables. |
| - | `$D400`, `$D700` | judge_sprite_scene23, judge_sprite_scene01 | New graphics. |
| `$D500` | `$D440` | judge_flag_sprite | The flag is already in the file of version I, unused. |

## Fighters and input

The pages: [v1 fighters](../v1/docs/fighters.md) and [v2 fighters](../v2/docs/fighters.md).

The fighter update of version II is the same as in version I, with three additions. [`v2:fighter_get_input` `$2834`](../v2/src/fighter_input.asm#L30) reads the keyboard when keyboard_control is not 0. The new path [`v2:kbd_read_move` `$288C`](../v2/src/fighter_input.asm#L75) gives a direction and a fire bit, and the joystick table makes the move from them. The move code starts samples 2 and 3 (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| `$225F` | `$2834` | fighter_get_input | Tests keyboard_control and goes to the keyboard path. |
| - | `$288C-$29B3` | kbd_read_move, kbd0_read_fire, kbd0_read_direction, kbd1_read_fire, kbd1_read_direction | New, 296 bytes. Fighter 1 uses `P @ *`, `L` `;` `/`, `, . /` and `:` or RIGHT SHIFT for fire. |
| `$2270` | `$284C` | joystick_read_move | Version I writes $FF to `$DC02` after the read. Version II does not. Each keyboard reader sets `$DC02` itself. |
| `$2297` | `$286C` | joystick_move_table | Same 32 bytes. |
| `$22D0` | `$29CD` | move_start_hit_reaction | Starts sample 3 (a fall) at frame $28 or $2C. |
| `$23D6` | `$2AE4` | anim_end_rise_crouch, now anim_end_back_to_crouch | Version I plays the crouch backwards and stands. Version II holds the crouch after a sweep or a low punch. |
| `$2438` | `$2B46` | move_start_anim | Starts sample 2 (the swish) when an attack starts. |
| `$30B5` | `$384C` | anim_check_x_limits | Clamps fighter_x to fighter_x_min and fighter_x_max by facing. Version I refuses the step. |
| - | `$12E9`, `$12EB` | fighter_x_min, fighter_x_max | New: facing 0 $0C-$95, facing 1 $00-$89. |
| `$780A` | `$780E` | script_crouch | 2 frames of stance before the crouch, then 16 frames of crouch (v1: 15). |
| `$7832`, `$7856` | `$7842`, `$785E` | script_down_back, script_up_back | The steps of dx -11 and +11 are gone. |
| `$790E` | `$7912` | script_hit_reaction_16 | The first three poses take 8 frames (v1: 15). |

**Conclusion:** version I drew three somersault frames one column to the right. Steps of dx -11 and +11 moved the fighter back to the right position. Near a limit, version I could refuse the -11 step and then do the +11 step, so the fighter moved by 11 units. Version II moves the three frames one column left and clamps the position.

## The computer opponent

The pages: [v1 AI](../v1/docs/ai.md) and [v2 AI](../v2/docs/ai.md).

The AI of version II starts at [`v2:ai_update` `$22CF`](../v2/src/ai_opponent.asm#L6). It has the same structure as [`v1:ai_update` `$1D48`](../v1/src/ai_opponent.asm#L6), but more rules. The response choice has a fourth kind: a random low kick or somersault. The new routine [`v2:ai_substitute_move` `$2698`](../v2/src/ai_opponent.asm#L586) changes a high attack into a low attack against a low opponent (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| `$1D67-$1D7B` | `$22EC` | ai_check_opponent | The held-crouch test of the levels 5 and up is gone, 21 bytes. |
| `$1E0B` | `$237D` | ai_choose_response | Bit 7 attack, bits 4-6 counter, bits 0-3 special action. No bit: ai_response_random_move gives $0B or $09. |
| - | `$2521-$252A` | flying kick rule | Levels 7 and up walk forward in place of a flying kick $0E. |
| - | `$2698` | ai_substitute_move | New: an opponent in move $0A, $10, $04 or $07 gets a low attack from the table ai_move_substitute at `$12D0`. |
| `$1FD8-$1FE0` | `$2567` | ai_attack_variant | The variant $09 is gone. A zero random value keeps the move. |
| - | `$26B8` | ai_spec_high_kick_or_duck | New special action 9 against a flying kick. |
| `$21A1` | `$2774` | ai_special_jump_table | 9 words, now 10 words. |
| `$21B3` | `$2788` | ai_special_by_move | Move $0E gives action 9 (v1: 1). |
| `$21EC` | `$27C1` | ai_level_attack_mask | Levels 6-11 changed. Level 6 can wait 127 frames, as level 0. |
| `$21F8` | `$27CD` | ai_level_walk_mask | Level 8 changed. |
| `$2203` | `$27D8` | ai_level_stop_mask | Levels 8-11 stop again. Version I never stops from level 7. |
| `$221B` | `$27F0` | ai_level_response_mask | All 12 levels changed. |
| `$1FFD` | `$2593` | ai_setup_level | Same code, with the same bugs. |

The table of the response masks shows how the choice changed. The values come from the generated source of each version.

| Level | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | $80 | $8F | $8F | $60 | $60 | $0F | $0F | $FF | $0F | $0F | $0F | $0F |
| v2 | $A3 | $B2 | $F1 | $F0 | $70 | $8F | $7F | $0F | $7F | $7F | $7F | $7F |

**Conclusion:** the opponent of version II blocks or jumps much more often. At the levels 4, 6 and 8-11, 88 % of the responses are a counter move. At the levels 0-3, half of the responses are an attack.

The game flow also changes the AI. The demo seeds ai_random from frame_random, and the rank cap keeps the level of the opponent at 10 or less (**Code**).

## Combat and the copy protection

The pages: [v1 combat](../v1/docs/combat.md), [v2 combat](../v2/docs/combat.md) and [protection.md](protection.md).

The hit test of version II is the same code as in version I. The hit-zone tables keep their bytes and their address. Two additions go into [`v2:hit_record` `$2CA8`](../v2/src/hit_test.asm#L175). The first is the protection check [`v2:protect_cia2_check` `$2CAE`](../v2/src/hit_test.asm#L180). The second is a sample call for each hit reaction (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| `$2591` | `$2CA8` | hit_record | New check of `$DD0E` after the store of scoring_move. |
| - | `$2CAE` | protect_cia2_check | New: LDA `$DD0E`, BEQ. A value that is not 0 goes to protect_cia2_trap. |
| - | `$2CB3` | protect_cia2_trap | New: pushes two bytes and jumps into anim_update with a bad stack. |
| `$25B1-$25C8` | `$2CD5-$2CF6` | hit reactions $1B, $16, $1A | New sample calls: samples 1, 0 and 1. |
| `$7200-$7711` | `$7200-$7711` | hit-zone tables | Same bytes. The pointer words move by +2. |
| `$12A3` | `$12A5` | move_score_values | Same bytes. |

The switch PROTECTION of version II (default 0) replaces the read of `$DD0E` with LDA #$00. With the original bytes and $08 in `$DD0E`, the CPU runs into graphics data after the first scoring hit. The clock stops at 27. **Observed** in [protection_trap_original.json](../v2/tests/protection_trap_original.json) and [protection_trap_rebuild.json](../v2/tests/protection_trap_rebuild.json).

## Scenes and graphics

The pages: [v1 graphics](../v1/docs/graphics.md) and [v2 graphics](../v2/docs/graphics.md).

The four scenes look the same in both versions. Version II unpacks the colour and screen maps with the new routine [`v2:scene_unpack_maps` `$1849`](../v2/src/scene_unpack.asm#L90). Version I copies them with [`v1:scene_copy_maps` `$19F6`](../v1/src/title_and_scene.asm#L110). The bitmap unpacker is the same code at a new address. The sprite graphics change where the bull and the samples need space (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| `$3994-$62FF` | `$3F5F-$68CA` | packed scene bitmaps | Same 10604 bytes, +$5CB. The pointers move from `$134C` to `$1839`. |
| `$6300-$71FF` | `$68CB-$71FF` | scene maps | Packed with a nibble run-length code. Unpacked, the maps are equal to version I. The random high nibbles of the v1 colour maps are gone. |
| `$19F6` | `$1849` | scene_copy_maps, now scene_unpack_maps | A copy of 2 x 480 bytes, now a nibble unpacker. |
| `$19E2` | `$1F1E` | scene_blank_rows, now scene_clear_bitmap | Version I fills the colour RAM and the screen of rows 5-16 with $33. Version II clears the bitmap `$E640-$F53F` with 0. |
| `$1A63` | `$1F3F` | scene_draw_if_new | The maps come before the bitmap (v1: after). |
| `$7720` | `$7720` | anim_script_table | 31 entries, now 33. The scripts move by +4 or more. |
| `$7AE0` | `$7AE0` | frame part tables | 72 frames, now 79. Stride $48, now $4F. |
| `$316D` | `$3914` | shape_build | A new entry tests shape_page_offset and goes to shape_direct_ptrs. |
| - | `$3B95` | shape_direct_ptrs | New: the bull frames get their sprite pointers without a copy. |
| `$33B7-$33E6` | `$3B65-$3B94` | shape_row4_left, mid, right | The shadow sprites have new pointers. Three entries move one column. |
| `$F540-$FF7F` | `$C940-$E5BF` | bull sprite blocks | The same 41 blocks in 5 runs at new places. |
| `$C980-$CBFF`, `$D000-$D13F` | `$D000-$D3BF` | unused figure sprites | One run at a new place. The part tables keep two of these frames, $4D and $4E. No animation uses them. The other figure blocks are gone. |
| `$D540-$DEFF` | `$D480-$DC3F` | shadow sprites | Same blocks, packed closer. |
| `$E000-$E3FF` | `$E100-$E2FF` | panel charset | 64 characters in place of 128. The yin-yang moves from characters $01-$08 to $21-$28. |
| `$18C2`, `$18D7` | `$1DDE`, `$1DF3` | draw_yin_yang_full, draw_yin_yang_half | Use the characters $21-$28. |

## Interrupts and samples

The pages: [v1 interrupts](../v1/docs/interrupts.md), [v2 interrupts](../v2/docs/interrupts.md), [v1 sound and music](../v1/docs/sound_music.md) and [v2 sound and music](../v2/docs/sound_music.md).

Version I has the sample player [`v1:sfx_sample_irq` `$29C8`](../v1/src/sfx_sample_player.asm#L6), but no code starts a sample. Its period tables at `$0E00` and `$0F00` hold music code. Version II plays 4 samples with [`v2:sfx_sample_irq` `$311A`](../v2/src/sfx_sample_player.asm#L6). It copies the period tables to `$0200-$03FF` and keeps the samples in the floor bitmap at `$F580-$FFDD`. The floor colour $77 hides these bytes on the screen (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| each raster handler | each raster handler | IRQ entry test | v1: BIT `$D019`, BMI, JMP to the sample player, never used. v2: BIT `$DC0D`, BPL, CLI, JMP `$311A`. A CIA1 interrupt goes to the sample player. |
| `$29C8` | `$311A` | sfx_sample_irq | Live. Reads the tables `$0300` and `$0200`. The end value is $FF (v1: $7F). |
| `$2A0A` | `$3158-$3186` | sfx_sample_start | 8 entries in front of it (4 used). Tests samples_off. Reads the start and the end from sfx_sample_table. |
| - | `$F540` | sfx_sample_table | New: 8 pairs of start and end offsets. |
| - | `$F580-$FFDD` | 4 samples | New: knockdown 0.08 s, hit 0.46 s, attack 0.36 s, floor 0.18 s. |
| `$0E00`, `$0F00` | `$0200`, `$0300` | sample period tables | Copied from `$C700` and `$C800` at the init. |
| `$271B`, `$276C` | `$2E4C`, `$2EA7` | irq_ab_row2, irq_ab_row3 | The IRQ comes 2 lines earlier. A new loop waits for a raster line that the planner writes. |
| `$2869` | `$2FB0` | irq_bitmap_on | The IRQ comes at line $59 (v1: $5A). A loop waits for line $5A, then starts CIA2 timer B. |
| `$28A5` | `$2FF2` | nmi_floor_colour | Same code. |
| `$2B7A` | `$3307` | mux_layout_same_y | ADC #$12 (v1: #$14) for the earlier IRQ. Writes the wait lines. |
| `$2A66` | `$31F2` | irq_frame_start | Same planner, new IRQ entry test. |

The renders of the 4 samples are WAV files: [knockdown](../v2/docs/assets/sample0_knockdown.wav), [hit](../v2/docs/assets/sample1_hit.wav), [attack](../v2/docs/assets/sample2_attack.wav) and [floor](../v2/docs/assets/sample3_floor.wav). The renders are **Observed**. **Conclusion:** the authors had the sample player in version I, but they cut the feature, and the music used the old table area. For version II they recorded 4 sounds and put them into the hidden floor bitmap.

## Music

The pages: [v1 sound and music](../v1/docs/sound_music.md) and [v2 sound and music](../v2/docs/sound_music.md).

The music driver is the same code at the same addresses in both versions. The tune data is the same, with one correction. In the order list [`v2:music_t1_order_v0` `$0FC2`](../v2/src/music_tables.asm#L43), version II adds the entry P0 at `$0FCE`. The repeat target 19 then falls on the jump to 0 in the same list (**Code**).

| v1 | v2 | Part | Change |
|---|---|---|---|
| `$0FC2-$0FD4` | `$0FC2-$0FD6` | music_t1_order_v0 | 2 bytes more. One loop takes 2 x 960 + 210 = 2130 ticks, as in voices 1 and 2. Pattern 2 now plays. |
| `$0F6C-$0FB7` | `$0F6C-$0FB7` | order list and instrument pointers | Each pointer after the correction is the old value + 2. |
| `$0FCE-$1157` | `$0FCE-$1159` | order lists and instruments | +2. |
| `$0F5E` | `$0F5E` | music_tune_pattern_tables, tune 0 | $00FA, now $0000. Nothing reads it. |
| `$08D6-$0956` | `$08D6-$0956` | tune 4 | Same data. Version II plays it in the name entry. |
| `$0C8C-$0D03` | `$0C8C-$0D03` | music workspace in the file | 23 bytes of RAM noise differ. |

**Conclusion:** the differences in the workspace come from the RAM of the machine that saved each file. The authors saved the two versions in different sessions.

## The bugs of version I that version II keeps

Version II corrects the rank overflow, the order list of tune 1 and the X limit test. These bugs of version I stay in version II (**Code**):

- **The shared AI parameters.** [`v2:ai_setup_level` `$2593`](../v2/src/ai_opponent.asm#L424) writes most AI masks without the index X. Thus the level of fighter 1 sets the values of both fighters. Only the demo shows it, because both fighters are computer players there.
- **A store without X in special action 8.** [`v2:ai_spec_set_crouch_punch` `$2646`](../v2/src/ai_opponent.asm#L527) writes ai_special_action of fighter 0 also for fighter 1.
- **A compare with the wrong register in special action 7.** [`v2:ai_spec_sweep_by_facing` `$2661`](../v2/src/ai_opponent.asm#L548) compares the facing with `fighter_facing,Y` and Y = 14. It reads fighter_move of fighter 0. No run executed this code.
- **The tie break of fighter 1.** [`v2:bout_hit_value_add` `$2169`](../v2/src/timer_and_texts.asm#L59) reads hit_points without X. The value of fighter 1 uses the hit points of fighter 0.
- **F5 during a game.** [`v2:title_key_f5` `$1ED1`](../v2/src/title_and_scene.asm#L69) jumps to the title loop from inside the bout loop and does not reset the stack. The stack wraps, so the game does not crash.
- **A two-player draw.** [`v2:game_2p_draw` `$1B61`](../v2/src/game_modes.asm#L47) calls high_score_update with X = 0. The scores are equal, so this has no effect. No run executed this code.
- **The collision latch.** [`v2:fighter_update` `$2808`](../v2/src/fighter_input.asm#L6) reads `$D01E` for each fighter. The first read clears the latch, so the second read sees only new collisions.
- **No negative dy in reverse play.** [`v2:anim_apply_move` `$3837`](../v2/src/anim_step.asm#L82) subtracts dx for a reversed animation, but it always adds dy.
- **Old row-4 pointers.** When a frame is not in the list of the shadow frames, the shape builder keeps the old pointers of the 4th sprite row.
- **The music on a PAL machine.** The note table music_note_freqs at `$0D14` has the NTSC values. On PAL, each note is about 3.7 % low (**Conclusion**).
- **A weak filter sweep.** The sweep code at `$0E8D-$0E9C` moves the 11-bit cutoff by very few steps. Version II uses it also for instrument 21 of tune 4.

Version II also adds one bug of its own. When fire is down at the end of a one-player game, the new entry of the high score table keeps the name "......" (**Code**).

## Still open

- Do the judge sprites stay on the screen after a game until the next demo bout? — a run of a two-player game to its end, with a screen capture in the pause.
- Does a raster wait of version II miss its line and then wait a full frame? — a trace of `$2FB0` and `$2E4C` while samples play.
- Does a sample cut the notes of the music? Each sample start clears all SID registers. — a listening test of the SID output during a hit.
- Why does the demo of version II write $FF to `$04F0`, a byte that already holds $FF? — no run can answer it. An older layout of the program can.
- Does a somersault at the X limit of version I move the fighter by 11 units? — a run of version I with a somersault at fighter_x $0C.
