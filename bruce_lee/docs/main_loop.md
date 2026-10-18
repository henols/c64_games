# Bruce Lee: the main loop, the status line, the score and the turns

During play, the main loop is the game logic. About 17 times a second, it reads the game keys, brings the enemies into the room and runs the room. It checks what Bruce and the enemies touch and hit, then moves them and builds their sprites. Around the loop are the keys F1, S, SPACE and V, the pause, and the screen saver that starts when nobody plays. The status line shows the score, the top score and the falls, and the score earns extra falls. A lost fall restarts the room, gives the turn to the other player in a two-player game, or ends the game.

The start of a game, the demo and the PLAYER n screen are on the page [startup_title.md](startup_title.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one raster interrupt (50 per second on PAL). A *pass* is one run of `main_loop`.
- A *fall* is a life of Bruce. The status line calls them FALLS.
- The *player block* is zero page `$28-$43`, from `falls_left` to `score+2`: the state of the player who plays now. The *parked player* is the other player of a two-player game. His block waits in `inactive_player_state`.
- Scores are 24-bit binary numbers, high byte first.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.
- The runs named on this page are runs of c64-testing from the snapshot `explore1/entry.vsf`. "Run d1-flow" plays a two-player game with a pause and two game overs. "Run d1-top" sets the score seven times in a game.

## How it works

The game divides its work in two. The game interrupt does the work of each frame: the sound effects, the sprite positions, the joysticks, the counters and the idle timer. The main loop does the game logic at its own pace, one pass every 3 frames. The same loop runs a game and the demo. In the demo (`game_mode` = 0), the keys and the pause are off.

~~~mermaid
flowchart TB
  A["Start the pass: 3 frames to go"] --> B{"A game?"}
  B -- yes --> C["Game keys and the pause"]
  C --> D{"Paused?"}
  D -- yes --> W["Wait for the third frame"]
  D -- no --> E
  B -- demo --> E["Blink 1UP, flicker the lantern flames"]
  E --> F["Bring in the enemies"]
  F --> G["Run the room, the background contact and touch"]
  G --> H["Fights and the top score"]
  H --> I["Move the actors, build the sprites, check knock-outs"]
  I --> W
  W --> A
~~~

### The pacing

The pass starts with `frame_countdown` = 3. [`frame_update` `$15A8`](../src/frame_update.asm#L20), the frame work of the game interrupt, counts it down by 1 in each frame until 0. The pass ends in [`main_loop_wait_frame` `$1C32`](../src/game_main_loop.asm#L83), which waits for 0. So a pass takes 3 frames, and the game logic runs about 16.7 times a second on PAL. **Code.**

A pass that needs more than 3 frames finds the count at 0 already. Then the next pass starts at once. The game runs slower, but it does not skip work. A trace showed a new pass every 3 frames, right after `frame_update` of the third frame (raster line about 264-277). It also showed one pass of 4 frames in 300 frames of room 7. **Observed.**

### One pass

[`main_loop` `$1BC2`](../src/game_main_loop.asm#L23) does these steps, in this order. **Code.**

1. **Set the pace.** `frame_countdown` = 3, so the pass ends 3 frames after it starts.
2. **Let the player end the demo.** [`check_demo_abort` `$19B8`](../src/pause_status_line.asm#L7): in the demo, fire on port 1 or F1 waits until the player releases fire, waits 6 frames and jumps to `restart_to_title`. In a game it returns at once.
3. **Read the keys and the pause, in a game only.** When `game_mode` = 1, `handle_game_keys` acts on F1, S, SPACE and V, `pause_debounce` counts down the debounce of the pause, and `check_pause_fire` lets fire end a pause. While bit 7 of `pause_state` is 1, the pass jumps to step 13. A paused game only reads keys and fire.
4. **Cap the energy of the enemies.** [`main_loop_update` `$1BDF`](../src/game_main_loop.asm#L37) clears bit 6 of Yamo's `actor_energy+1` and bits 3-6 of the Ninja's `actor_energy+2`. Bit 7 (knocked out) stays, so the energy of a Ninja who stands is at most 7.
5. **Animate the screen.** `blink_player_label` blinks 1UP or 2UP, and `flicker_lantern_flames` animates the lantern flames.
6. **Bring in the enemies.** When `room_no_enemy_flag` = 0, `tick_spawn_timers`, `update_yamo_spawn` and `update_ninja_spawn` bring Yamo and the Ninja into the room.
7. **Toggle the pass parity.** [`main_loop_toggle_phase` `$1BFE`](../src/game_main_loop.asm#L52) toggles `pass_parity` between 1 and 0. Room handlers use it to act on every second pass.
8. **Run the room.** [`run_room_frame_handler` `$3A6F`](../src/passage_open.asm#L18) runs the code of the room. `check_background_contact` sets the terrain flags of each actor from its pixels and the background. [`check_background_touch` `$2E39`](../src/background_touch.asm#L10) checks the tiles under the actors: lanterns, exits and deadly tiles. An exit goes to `change_room`, which draws the next room, resets the stack and jumps to `main_loop`.
9. **Check the protection.** [`main_loop_protection_check` `$1C13`](../src/game_main_loop.asm#L67) stores `prot_key_tick` EOR `prot_key_tick_pair` in `protection_check_value`, and `actor_play_step_sound` checks this value later. See [protection.md](protection.md).
10. **Check the fights.** When `room_no_enemies` of the room is 0, [`check_fight_collisions` `$29C3`](../src/fight_hits.asm#L14) runs.
11. **Keep the top score.** `update_high_score` copies a higher score to the top score (see "The top score" below).
12. **Move the actors.** [`update_actors` `$179E`](../src/actor_driver_text.asm#L10) reads the input or runs the AI of each actor and does its action. `build_actor_sprites` makes the sprites. [`check_actor_knockouts` `$2D55`](../src/actor_helpers.asm#L8) sends a knocked-out Bruce to `lose_fall`.
13. **Wait.** `main_loop_wait_frame` waits until `frame_countdown` = 0, then jumps to `main_loop`.

The pass has more exits that do not return. They are F1 (`restart_to_title`), a room change (`change_room`) and a lost fall (`check_actor_knockouts`, or `act_dying_lose_fall` in `update_actors`). Each exit that continues the game resets the stack and enters `main_loop` again. **Code.**

### The keys of a game

Four keys work in a game, and only these four. [`handle_game_keys` `$1B29`](../src/status_and_keys.asm#L57) runs in each pass of a game, also during the pause. It sets `key_scan_mode` = 1. Thus [`scan_keyboard` `$139E`](../src/keyboard_scan.asm#L24) decodes only the four keys. It drives the column of each key and compares port B with the exact row pattern of `game_key_matrix`. Any other key gives code `$6F`, and a held key gives one code only. **Code.**

The routine clears `key_ready`, removes the shift bit and stores the code in `last_game_key`. Nothing reads that byte: three routines write it (`reset_play_state`, `pause_debounce` and `handle_game_keys`) and none reads it. **Code.**

| Key | Code | Action | Code path |
|---|---|---|---|
| F1 | `$04` | restart: back to the title | `handle_game_keys` jumps to `restart_to_title` |
| S | `$0D` | `title_music_off` EOR 1, and `title_music_skip_count` = 0 | `handle_game_keys_check_s` |
| SPACE | `$3C` | pause on / off | `handle_game_keys_pause` jumps to `toggle_pause` |
| V | `$1F` | the credit line on / off | `toggle_credit_line` |

**The S key only switches the title tune.** S does not change the sound of the game. [`title_music_off` `$1385`](../src/room_enemy_tables.asm#L118) has one reader, the title screen (`show_title_screen`). S also sets the count of the title tune to 0, so the next title plays the tune when the tune is on. **Code.** The tune itself is on the page [sound_music.md](sound_music.md).

**V** shows or hides the credit line in screen row 0. When row 0 starts with character `$20`, [`toggle_credit_line` `$1B68`](../src/status_and_keys.asm#L94) copies the 40 characters of `version_banner` ("BRUCE LEE (C) 1984 DATASOFT REV.2 BY RJF") to row 0. Else it fills row 0 with `$20`. `reset_play_state` also fills row 0 with `$20`. In the text font, `$20` is the solid block that the cold start made. It shows in black, so row 0 without the credit line is a black bar. **Code.**

**F1** restarts the program state but keeps `top_score`, the options and the handedness. In the demo there are no keys but F1: `check_demo_abort` scans with the same mode and reacts to F1 only. **Code.**

![The credit line after V](images/screens/status_line_v.png)

The game screen after V: the credit line in row 0 and the status line in row 1. The 1UP mark is in its dark phase. **Observed.**

### The pause, the idle timer and the screen saver

SPACE pauses the game, and SPACE or fire of the current player ends the pause. A game without input pauses itself after about 11 minutes. A long pause starts a screen saver that changes the colours of the room. One byte, `pause_state`, holds the paused bit and a debounce count. Its layout is in [The data](#the-data), and the states are in [The state machine of the pause](#the-state-machine-of-the-pause).

**The debounce.** [`pause_debounce` `$19EC`](../src/pause_status_line.asm#L36) lowers the count in each pass: 6, 5, 3, 1, 0 (it subtracts 1 from bits 1-2 and drops bit 0). So a change of the pause takes 4 passes to settle. While it runs, `last_game_key` = `$FF`. [`check_pause_fire` `$1A08`](../src/pause_status_line.asm#L53) acts only at count 0. The count does not block SPACE. **Code.**

**Fire ends the pause.** `check_pause_fire` reads the fire button of the current player: port 1 (`CIAPRB`) for player 1, port 2 (`CIAPRA`) for player 2. Fire while not paused does nothing. **Code.**

**The toggle.** [`toggle_pause` `$1A22`](../src/pause_status_line.asm#L69) sets `pause_state` = (`pause_state` EOR `$80`) OR 6. **Code.**

- Into the pause: `show_paused` sets `up_blink_timer` = `$11` and calls `blink_player_label`, so the label shows and stays. It sets `idle_timer` = `$51` and prints "** PAUSED **" (message `$0B`, `show_paused_message`) on the status line from column 15.
- Out of the pause: `clear_paused_message` prints 12 blanks over the message. When `idle_timer` is negative, `stop_screen_saver` restores the band colours. Then `idle_timer` = 0, and `print_top_label` and `show_high_score` draw TOP and the top score again, because the message covered them.

**The idle timer.** `frame_update` adds 1 to `idle_timer` every 256 frames while it is positive. Any direction or fire on Bruce's joystick or on the joystick of a player-moved Yamo resets it to 0, but not while paused. In the demo it is reset in each frame. When it reaches `$80` (32768 frames, about 11 minutes), the code at [`frame_update` `$1634`](../src/frame_update.asm#L105) sets `pause_state` = `$86` and calls `show_paused` and `start_screen_saver`. **Code.**

**The screen saver.** [`start_screen_saver` `$102B`](../src/game_setup.asm#L139) copies the 20 colours of the raster bands of the room, `room_band_colours`, to `palette_backup` and sets `idle_timer` = `$FE`. While `idle_timer` is negative, `frame_update` computes each band colour in each frame as (`palette_backup`+x EOR `frame_count_256`) AND `$F7`. `frame_count_256` counts once every 256 frames, so the colours change about every 5 seconds. **Code.**

**While paused,** the pass runs only steps 1-3 of [One pass](#one-pass). The interrupt still runs: the sprites stay, the sound effects play on, and `room_time` stops. F1, S, V and SPACE work. **Code.**

**A paused game also starts the screen saver.** `show_paused` sets `idle_timer` = `$51`, and input does not reset it while paused, so it reaches `$80` after 47 * 256 = 12032 frames (about 4 minutes). **Code.**

![The paused game](images/screens/paused.png)

The paused game: "** PAUSED **" covers TOP and the top score on the status line. **Observed.**

### The idle Yamo of player 2

In the opponent mode, player 2 moves Yamo with the second joystick. When player 2 stops playing, the computer moves Yamo again.

When `option_yamo_player2` = 1 and player 2 gives no input for 7 * 256 frames, [`frame_update_yamo_idle` `$173F`](../src/frame_update.asm#L295) sets `option_yamo_player2` = 0. It counts in `yamo_idle_time` only in a game, not paused, in a room with enemies. It also sets the high byte of `room_time` = `$20` and plays `play_open_sound`. Then it takes 5 falls (not below 0) from `falls_left` and from the parked player in `inactive_player_state`. **Code.** The 5 falls are the extra falls of the opponent mode, which starts with 9 falls instead of 4. **Conclusion.**

### The status line

The status line is screen row 1, one screen row high, in the text font. [`reset_play_state` `$0763`](../src/play_init.asm#L19) draws it at each start of a game, a turn and a fall. The digits are characters `$10-$19`. **Code.**

| Columns | Content | Written by |
|---|---|---|
| 2 | L when joystick 1 is left handed | `frame_update`, each frame |
| 4-6 | 1UP or 2UP, blinking | `blink_player_label` (messages 1 and 2, message 0 blanks it) |
| 8-13 | the score, 6 digits | `show_score` (screen offsets `$30`, `$32`, `$34`) |
| 16-18 | TOP | `print_top_label` (message 3) |
| 20-25 | the top score, 6 digits | `show_high_score` (offsets `$3C`, `$3E`, `$40`) |
| 28-32 | FALLS | `print_falls_label` (message 5) |
| 34-35 | the falls, 2 digits | `show_falls_count` (offset `$4A`) |
| 37 | L when joystick 2 is left handed and in use | `frame_update`, each frame |
| 15-26 | "** PAUSED **" over TOP and the top score | `show_paused_message` |

Screen row 0 holds the credit line or the black bar (see [The keys of a game](#the-keys-of-a-game)).

**The blink.** [`blink_player_label` `$1A96`](../src/pause_status_line.asm#L147) decrements `up_blink_timer` in each pass. At 0 it sets the timer to `$20` and prints 3 blanks. At `$10` it prints message 1 + `current_player`. So the label is on for 16 passes and off for 16 passes, a period of 96 frames. **Code.**

**The falls.** [`show_falls_count` `$1AED`](../src/status_and_keys.asm#L10) converts `falls_left` (0-99) to two decimal digits by repeated subtraction of 10. It packs them into one BCD byte and prints it with `print_hex_byte`. **Code.**

**The digits.** [`print_bcd_byte` `$1B17`](../src/status_and_keys.asm#L39) prints a BCD byte as two characters: each nibble OR `$10`. `print_hex_byte` does the same, and maps the nibbles A-F to `$21-$26` (the letters). Only the unused `debug_show_values` passes real hexadecimal values. **Code.**

![The status line at the start of a game](images/screens/game_start.png)

The status line at the start of a game: 1UP 000000 TOP 000000 FALLS 04. **Observed.**

### The score

Bruce earns points for hits, knock-outs, lanterns, new rooms and the wizard. [`add_score` `$3175`](../src/score.asm#L52) takes A = points and X = the byte: 2 for units, 1 for multiples of 256. It clears `points_to_add`, stores A at `points_to_add`+X and jumps to [`add_pending_score` `$312C`](../src/score.asm#L8). That adds the three bytes with carry from the low byte (X = 2) to the high byte, checks the extra fall and calls `show_score`. A sum above 255 needs two calls. **Code.**

| Event | Points | Calls |
|---|---|---|
| a punch of Bruce hits | 100 | `apply_fight_hits` |
| a kick of Bruce hits | 75 | `apply_fight_hits` |
| a fall attack of Bruce hits | 50 | `apply_fight_hits` |
| Bruce knocks out Yamo | 256 + 194 = 450 | `apply_fight_hits` |
| Bruce knocks out the Ninja | 200 | `apply_fight_hits` |
| a lantern | 125 | `handle_touched_tile` |
| the first visit of a room | 1792 + 208 = 2000 | `draw_room` |
| a height band of room 13 | 256 + 244 = 500 | `room13_frame` |
| Bruce defeats the wizard | 184 + 2816 = 3000 | `room18_frame` |

To show a score, [`score_to_bcd` `$32DC`](../src/room_misc_support.asm#L142) converts `score` to BCD, and `show_high_score` converts `top_score` with the same method. **Code.**

~~~
bin = score (24 bits); bcd = 0 (4 bytes)
SED
repeat 24 times:
    shift bin left by 1 (the top bit goes to carry)
    bcd = bcd + bcd + carry      ; ADC of each BCD byte with itself, low byte first
CLD (PLP restores the flag of the caller)
print bcd+1, bcd+2, bcd+3 as 6 digits
~~~

[The worked example](#the-worked-example-a-score-of-125) decodes a score of 125. The status line shows 6 of the 8 BCD digits, so a score of 1,000,000 or more shows only its low 6 digits. **Conclusion.**

### The top score

The game keeps one top score for both players and all games since the load. [`update_high_score` `$3184`](../src/score.asm#L65) runs in each pass. **Code.**

1. In the demo (`game_mode` = 0) it only calls `show_score`.
2. It checks the protection: when `prot_key_trap1` = `prot_key_trap1_pair`, and the same for the trap 2 and trap 3 pairs, it jumps through `io1_dummy` and crashes. With the right key bytes the first pair differs. In the default build (`PROTECTION` = 0) the jump goes to the compare. See [protection.md](protection.md).
3. [`update_high_score_compare_loop` `$31A6`](../src/score.asm#L91) compares `top_score` with `score` from the high byte. The first byte that differs decides. This is a correct 24-bit compare.
4. When the score is higher, `update_high_score_store` copies 4 bytes from `score` to `top_score` and then continues into `show_high_score`. The fourth byte is a bug, see [Extra falls](#extra-falls).

### Extra falls

The score earns extra falls: the intent is one at 40000 points, then one every 30000 points (70000, 100000 and so on). [`check_extra_fall_loop` `$313A`](../src/score.asm#L18) runs after each addition. When the score reaches `bonus_fall_next_score`, [`award_extra_fall` `$3146`](../src/score.asm#L25) adds `bonus_fall_score_step` to the limit, adds 1 to `falls_left` and calls `show_falls_count`. `init_game_variables` sets the limit of both players to `bonus_fall_first_score`. **Code.**

~~~
for x in 0..2:                              ; high byte first
    if score[x] < limit[x]: no extra fall    ; BCC show_score
award: limit += step; falls_left += 1
~~~

**Bug: extra falls come late, because the test compares byte by byte.** The loop needs each byte of the score to be at least the byte of the limit. It never stops early when a higher byte is greater. **Code.**

| Score | Bytes | Limit bytes | Byte test | Result |
|---|---|---|---|---|
| 40960 | `00 A0 00` | `00 9C 40` | `00` >= `00`, `A0` >= `9C`, `00` < `40` | no extra fall |
| 41060 (one more punch) | `00 A0 64` | `00 9C 40` | all bytes >= | extra fall, limit becomes `01 11 70` (70000) |
| 70500 | `01 13 64` | `01 11 70` | `64` < `70` | no extra fall |

An extra fall never comes early, because all bytes greater or equal means that the score is greater or equal. But it often comes late, at a later addition whose low bytes are high enough. **Conclusion.**

**Bug: a new top score moves the first extra fall of later games to 171072 points.** [`update_high_score_store` `$31B8`](../src/score.asm#L102) copies 4 bytes, `score` (`$0041-$0043`) and zero page `$44`, to `top_score` (`$4388-$438A`) and the first byte of [`bonus_fall_first_score` `$438B`](../src/fireball_text_score_vars.asm#L62). `$44` is [`raster_split_index` `$0044`](../src/constants.asm#L32), the index of the raster split in the game interrupt. The next game copies the damaged value to the limits. **Code.**

Run d1-top set the score seven times above the top score in a game. After each store, `top_score` held `00 00 xx 02 9C 40`: `bonus_fall_first_score` was `02 9C 40` each time. **Observed.** So after a game with a new top score, the first extra fall of each later game is at `$029C40` = 171072 points, not 40000. With the first bug, it also needs the middle byte to be `$9C` or more. **Conclusion.**

Other events change the falls too. **Code.**

| Change | Code |
|---|---|
| 4 falls at the game start, 9 when player 2 moves Yamo | `init_game_variables` |
| +1 at each extra fall of the score | `award_extra_fall` |
| +1 at a pickup in room 16, at most 5 per player (`extra_fall_pickups_left`) | `collect_room16_bonus` |
| -5 for both players when player 2 stops moving Yamo | `frame_update_yamo_idle` |
| -1 at each lost fall | `lose_fall` |

### Losing a fall and the next turn

A lost fall restarts the room. In a two-player game, the players take turns after each lost fall. Each player continues in his own room, with his own lanterns and score. [`lose_fall` `$1818`](../src/lose_fall_game_over.asm#L14) runs when Bruce's death ends (`act_dying_lose_fall`) or when Bruce is knocked out (`check_actor_knockouts`). It never returns. **Code.**

1. `stop_all_sounds` silences the sound.
2. In the demo (`game_mode` = 0): `title_music_skip_count` = 0, so the next title plays its tune, then `show_title_screen`.
3. `lose_fall_count` decrements `falls_left`. A negative result goes to `game_over`.
4. [`next_turn` `$182A`](../src/lose_fall_game_over.asm#L23) gives the three actors full energy (`actor_energy` = `$24`), sets `enemy_follow_x` = 0 (no enemy follows Bruce) and clears the fireball sprites.
5. In a two-player game, when the parked player is not out (`inactive_player_state` is positive): `current_player` EOR 1.
6. `show_player_screen` shows PLAYER n, also in a one-player game. Then it blanks the screen.
7. With the same condition as step 5: `next_turn_swap_block_loop` exchanges the player block with `inactive_player_state`, `swap_player_lanterns` exchanges the lanterns, and `next_turn_swap_score_loop` exchanges the limits of the extra falls.
8. [`next_turn_enter_room` `$1886`](../src/lose_fall_game_over.asm#L72): `reset_play_state` draws the game screen and the status line of this player and spawns Bruce. X = `room`, and `place_bruce_at_room_start` enters that room at its start point. That ends in `main_loop`.

### The game over

When the last fall is lost, [`game_over` `$188E`](../src/lose_fall_game_over.asm#L82) shows the game over screen of the current player, with his score in big digits. **Code.**

1. It clears the fireball sprites and the text screen (`clear_text_screen`). SEI. It blanks the screen and sets `SPENA` = 0, so no sprite shows.
2. `irq_vector` = `irq_title_frame` at raster line `$FB`. Blue border and background, colour RAM `$0F`, rows 12-24 white, rows 0-9 filled with `$DC`.
3. `game_over_text_loop` copies 18 characters of `game_over_letters_top` and `game_over_letters_bottom` to rows 1-2 from column 11: GAME OVER in big letters.
4. `game_over_digit_loop` patches the digit of the player into the PLAYER banner (see the bug below).
5. `game_over_player_loop` copies PLAYER n to rows 5-6 from column 12.
6. `score_to_bcd`, then `game_over_score_loop` draws 6 big digits on rows 8-9 from column 14 with `draw_big_digit` (2 x 2 characters, the first is `$B4` + digit * 4).
7. It shows the screen again. `game_over_wait` waits 254 frames.
8. In a two-player game, when the parked player is not out: jump to `next_turn`, the turn of the other player.
9. Else `game_over_to_title` waits 64 more frames and jumps to `show_title_screen`.

**The game over copies only one character of the player digit.** [`game_over_digit_loop` `$1909`](../src/lose_fall_game_over.asm#L144) runs only once (DEY/BPL from Y = 0), so it copies only the first character of each half of the big digit. **Code.** The bug does not show: the second character keeps the value of the last PLAYER n screen, and that screen always showed the same player. **Conclusion.** In run d1-flow the game over screens of player 1 and of player 2 both showed the right digit. **Observed.**

![The game over screen](images/screens/game_over.png)

The game over screen of player 1 with a score of 0. **Observed.**

## The data

### The player block

[`lose_fall` `$1818`](../src/lose_fall_game_over.asm#L14) exchanges these 28 bytes with [`inactive_player_state` `$439F`](../src/fireball_text_score_vars.asm#L89) when the turn passes to the other player. `init_game_variables` copies the start values to `inactive_player_state` at each game start. The last column was **Observed** in run d1-flow.

| Bytes | Name | Meaning | At the game start |
|---|---|---|---|
| `$28` | `falls_left` | falls left, negative = this player is out | `04` |
| `$29` | `room` | the room of the player | `00` |
| `$2A-$3D` | `room_lanterns_left` | lanterns not yet taken, one byte per room | `06 06 0A 02 02 0A 08 0D 04 05 03 03 03 00 04 06 02 02 01 00` |
| `$3E-$3F` | (no name) | two bytes of the block | `00 00` |
| `$40` | `game_loop_count` | completed loops of the game | `00` |
| `$41-$43` | `score` | the score | `00 00 00` |

The game keeps the other state of a player in other ways. **Code.**

| State | How each player keeps it |
|---|---|
| the present flag of each lantern | `swap_player_lanterns` exchanges it with `parked_lantern_flags` |
| `bonus_fall_next_score` | `next_turn_swap_score_loop` exchanges it with `bonus_fall_next_score_other` |
| `room_unvisited` | one byte per room and player, index room * 2 + `current_player` |
| `room13_band_bonus` | 4 bytes per player, index `current_player` * 4 |
| `extra_fall_pickups_left` | one byte per player, index `current_player` |

### The score bytes

The score variables are 24-bit binary numbers, high byte first. The top score and the limits of the extra falls are next to each other. Thus the 4-byte copy of the top score damages the first limit. **Code.**

| Name | Address | Layout |
|---|---|---|
| `score` | `$0041` | the score, the last 3 bytes of the player block |
| `points_to_add` | `$0025` | the points of one addition |
| `top_score` | `$4388` | one top score for both players and all games since the load |
| `bonus_fall_first_score` | `$438B` | `00 9C 40` = 40000, the score of the first extra fall |
| `bonus_fall_score_step` | `$438E` | `00 75 30` = 30000, the step between extra falls |
| `bonus_fall_next_score` | `$4392` | the score of the next extra fall of the current player |
| `bonus_fall_next_score_other` | `$4395` | the same for the parked player |
| `bcd_conv_binary` | `$4398` | 3 bytes, the work copy of the binary value |
| `bcd_conv_digits` | `$439B` | 4 bytes, 8 BCD digits, high first. The status line shows `+1..+3` as 6 digits. |

### The pause bytes

**Code.**

| Name | Address | Layout |
|---|---|---|
| `pause_state` | `$0105` | Bit 7 = paused. Bits 0-2 = the debounce count, 6 after each change. |
| `idle_timer` | `$0082` | Units of 256 frames without input, `$00-$7F`. At `$80` the game pauses itself. `$FE` while the screen saver runs. |

## The state machines

### The state machine of the pause

The pause has two settled states, playing and paused, and a debounce of 4 passes between them. The screen saver is a paused state with changing colours. [`toggle_pause` `$1A22`](../src/pause_status_line.asm#L69) makes each change by a key or fire, and [`pause_debounce` `$19EC`](../src/pause_status_line.asm#L36) counts the debounce down.

~~~mermaid
stateDiagram-v2
  state "Playing: pause_state $00" as Play
  state "Pausing: $86 to $81" as InDeb
  state "Paused: $80" as Paused
  state "Screen saver: $80, idle_timer $FE" as Saver
  state "Resuming: $06 to $01" as OutDeb
  [*] --> Play
  Play --> InDeb: SPACE
  Play --> InDeb: idle_timer = $80, saver on
  InDeb --> Paused: 4 passes
  InDeb --> OutDeb: SPACE
  Paused --> OutDeb: SPACE, or fire of the current player
  Paused --> Saver: idle_timer = $80
  Saver --> OutDeb: SPACE, or fire of the current player
  OutDeb --> Play: 4 passes
  OutDeb --> InDeb: SPACE
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Playing | SPACE | Pausing (`$86`) | `handle_game_keys_pause`, `toggle_pause`, `show_paused` |
| Playing | `idle_timer` reaches `$80` | Pausing (`$86`) with the screen saver | `frame_update`, `start_screen_saver` |
| Pausing | count 6, 5, 3, 1 in 4 passes | Paused (`$80`) | `pause_debounce` |
| Pausing | SPACE | Resuming (`$06`) | `toggle_pause` |
| Paused | SPACE, or fire on the port of `current_player` | Resuming (`$06`) | `check_pause_fire`, `toggle_pause` |
| Paused | `idle_timer` reaches `$80` (12032 frames) | Screen saver | `frame_update` (sets `$86` again) |
| Screen saver | SPACE or fire | Resuming (`$06`), colours restored | `toggle_pause`, `stop_screen_saver` |
| Resuming | count 6, 5, 3, 1 in 4 passes | Playing (`$00`) | `pause_debounce` |
| any | F1 | the title | `restart_to_title` |

In run d1-flow, after SPACE, `pause_state` was `$85`, `$83`, `$81`, `$80`, `$80` at 3-frame steps, with `idle_timer` = `$51` and `up_blink_timer` = `$10`. After fire on port 1, it was `$01` 12 frames later, and `idle_timer` was 0. **Observed.** At the first pass of a game `pause_state` is `$01`, because [`init_game_variables` `$0F72`](../src/game_setup.asm#L18) writes 1 to `$0100-$0107`. **Code.**

### The state machine of the turns

A game moves between play, the loss of a fall, the PLAYER n screen and the game over. [`lose_fall` `$1818`](../src/lose_fall_game_over.asm#L14) starts each change. [`next_turn` `$182A`](../src/lose_fall_game_over.asm#L23) and [`game_over` `$188E`](../src/lose_fall_game_over.asm#L82) choose who plays next. "Other player in" means `option_two_players` = 1 and `inactive_player_state` positive.

~~~mermaid
stateDiagram-v2
  state "Playing (main_loop)" as Play
  state "Lose a fall" as Lose
  state "Next turn" as Next
  state "Switch: current_player EOR 1" as Switch
  state "PLAYER n screen" as PScreen
  state "Swap the player blocks" as Swap
  state "Enter the room" as Enter
  state "Game over" as Over
  state "Title screen" as Title
  [*] --> Play: start_new_game
  Play --> Lose: Bruce dies or is knocked out
  Lose --> Title: demo
  Lose --> Over: falls_left negative
  Lose --> Next: falls_left 0 or more
  Next --> Switch: two players, other player in
  Next --> PScreen: else
  Switch --> PScreen
  PScreen --> Swap: two players, other player in
  PScreen --> Enter: else
  Swap --> Enter
  Enter --> Play
  Over --> Next: two players, other player in, 254 frames
  Over --> Title: else, 254 + 64 frames
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Playing | Bruce's death ends | `lose_fall` | `act_dying_lose_fall` |
| Playing | Bruce's energy is negative | `lose_fall` | `check_actor_knockouts` |
| `lose_fall` | `game_mode` = 0 | the title, tune next | `lose_fall` |
| `lose_fall` | `falls_left` negative after the decrement | `game_over` | `lose_fall_count` |
| `lose_fall` | `falls_left` 0 or more | `next_turn` | `lose_fall_count` |
| `next_turn` | other player in | Switch, then PLAYER n | `next_turn` |
| `next_turn` | else | PLAYER n of the same player | `next_turn_player_screen` |
| PLAYER n | other player in | swap the blocks, then enter the room | `next_turn_swap_block_loop` |
| PLAYER n | else | enter the room | `next_turn_enter_room` |
| Enter the room | always | Playing | `place_bruce_at_room_start` |
| `game_over` | other player in | `next_turn` | `game_over_wait` |
| `game_over` | else | the title | `game_over_to_title` |

In run d1-flow (two players), player 1 started with `falls_left` set to 0 and lost a fall. The game went to `game_over`, then to `next_turn` and to the PLAYER 2 screen. In the turn of player 2, `current_player` = 1, the player block held the start values of player 2, and `inactive_player_state` started with `$FF` (player 1 out). When player 2 lost his last fall, the game went to `game_over` and then to the title, with `option_two_players` still 1. **Observed.**

## The worked example: a score of 125

The demo scores 125: `score` = `00 00 7D`. [`score_to_bcd` `$32DC`](../src/room_misc_support.asm#L142) shifts the 24 bits in from the top. The first 16 bits are 0, so the BCD value stays 0. The low byte is `$7D` = `0111 1101`, and each bit doubles the BCD value and adds the bit:

| Bit | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 |
|---|---|---|---|---|---|---|---|---|
| BCD after the step | 0 | 1 | 3 | 7 | 15 | 31 | 62 | 125 |

`bcd_conv_digits` = `00 00 01 25`, and the status line shows 000125. **Observed** in run d1-flow: the score was `00 00 7D` at the end of the demo, and the demo screenshot on [startup_title.md](startup_title.md) shows 000125.

## Still open

- The two bytes `$3E-$3F` of the player block have no name, and the knowledge gives no use of them. A watchpoint run through a full game loop can show if any code writes them.
- Whether `raster_split_index` is always 2 when `update_high_score` runs, also in rooms with more raster bands. A run that stores a top score in each room can show it.
- How often a pass takes more than 3 frames in the busy rooms, for example in room 18 with the fireballs. Room 7 had one pass of 4 frames in 300 frames. A trace of `main_loop` with the raster line in room 18 can measure it.
