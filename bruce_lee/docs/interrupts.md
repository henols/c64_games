# Bruce Lee: the interrupts and the per-frame work

The C64 draws the screen 50 times a second. Bruce Lee uses the raster interrupt to do two jobs at that steady pace:

- It splits each screen into parts with their own charset and colours. The title has the big logo above the menu. The PLAYER n screen has a shaded banner. A room has a grey status line above coloured bands.
- In the game, it does the work that must not wait for the game logic. This work is the sound effects, the sprites, the joysticks, the clocks of the room and the countdowns.

The main loop waits for the interrupt to count frames, so the interrupt also sets the pace of the whole game. Each of the three screens has its own chain of raster handlers. The three screens are the title and game over screen, the PLAYER n screen, and the game screen with the attract demo.

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one PAL video frame: 312 raster lines, 19656 CPU cycles, 50 frames per second.
- A *pass* is one run of the main loop. It lasts at least 3 frames.
- A *line* is a raster line. Text row r of the screen starts at line 51 + 8r.
- A *handler* is a routine that the IRQ entry reaches through `irq_vector`. A *chain* is the handlers of one screen. Each handler of a chain sets the next one.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.
- The runs of this page start from two snapshots. The first run starts from `entry.vsf` (the cold start). It goes through the title, the attract demo, F7, the PLAYER 1 screen and room 0. To give F7, the run writes the key into `key_code` with `key_ready` = 1. The second run plays 300 frames of room 7 from `rooms/room07.vsf`. Traces of exec points and of writes to the VIC registers gave the raster lines.

## How it works

Every interrupt of the game is a VIC-II raster interrupt. [`init_game_irq` `$082D`](../src/game/play_init.asm#L114) turns the CIA 1 and CIA 2 interrupts off. One entry routine takes every interrupt and jumps through a vector to the handler of the current screen. Each handler does its part of the screen and then writes the line of the next interrupt. When the next handler is a different one, it also writes that handler into the vector. Thus a screen is a small loop of handlers, and a new screen only writes a new first handler. **Code**

~~~mermaid
flowchart TB
  HW["IRQ vector at $FFFE"] --> E["Save the registers (irq_entry)"]
  E --> D["Jump through irq_vector"]
  D --> T["Title and game over:<br/>logo / menu split, music"]
  D --> P["PLAYER n:<br/>shaded banner"]
  D --> G["Game and demo:<br/>status line, room, colour bands"]
  G --> F["Work of the frame (frame_update)"]
  N["NMI and RESET vectors"] --> R["Return at once (nmi_entry)"]
~~~

| Screen | Installed by | Handlers in a frame | Music | Per-frame work |
|---|---|---|---|---|
| Title | `show_title_screen` | `irq_title_frame` (line 253), `irq_title_split` (line 130) | `music_api_play` | `frame_countdown`, `title_countdown` |
| Game over | `game_over` | the same as the title (the first IRQ at line 251) | `music_api_play` is called. `lose_fall` has stopped the sound before | the same as the title |
| PLAYER n | `show_player_screen` | `irq_player_screen` (line 99) | none | `frame_countdown` |
| Game and demo | `init_game_irq` | `irq_game_bottom` (line 253), `irq_game_playfield` (line 64), `irq_game_colour_split` (0-2 times) | none (sound effects only) | `frame_update` |

### The IRQ entry and the vector

The game removes the KERNAL ROM from the memory map (`R6510` = `$35`), so the CPU reads the interrupt vectors from RAM. The IRQ vector `hw_irq_vector` points to [`irq_entry` `$1103`](../src/irq/interrupt_entry.asm#L10). **Code**

**RESTORE does nothing.** The NMI vector and the RESET vector both point to [`nmi_entry` `$1116`](../src/irq/interrupt_entry.asm#L25), which is a single RTI. A press of RESTORE returns at once. **Code**

`irq_entry` does three things:

1. It pushes A, X and Y.
2. It reads the stacked status register (LDA `$0104`,X after TSX) to test for a BRK. **The BRK test does not work**: the code does `AND #$00` at `$110C`. Thus the result is always zero, and the BRK branch (`JMP (io1_dummy)`) never runs. **Code**
3. `irq_dispatch` does `JMP (irq_vector)`.

**The vector is part of an instruction.** [`irq_vector` `$0408`](../src/game/cold_start.asm#L31) and `irq_vector_hi` are the two bytes of the `AND #$EF` instruction in [`cold_start` `$0400`](../src/game/cold_start.asm#L22). The instruction runs one time at the cold start. After that, the code stores the address of the next handler there. **Code**

Each handler ends with the same steps:

1. It writes 1 to `IRQMSK` and `VICIRQ`: the raster IRQ is on and acknowledged.
2. It clears bit 8 of the compare line in `SCROLY`.
3. It writes the next line to `RASTER`.
4. It returns with PLA/TAY/PLA/TAX/PLA/RTI. **Code**

The section [The chain of handlers](#the-chain-of-handlers) gives every change of the vector.

### The title and game over screen

The title shows the big logo (DATASOFT PRESENTS, BRUCE LEE, BY RON J FORTIER) in a multicolour logo charset. The menu below it shows in the text font. Two handlers change the charset in the middle of the screen, and change it again at the bottom. The bottom handler also plays the title music. It also counts the time to the attract demo.

| Handler | Line | Sets | Calls | Next |
|---|---|---|---|---|
| `irq_title_frame` | 253 (`$FD`) | `VMCSB` = `$30` (screen `game_screen`, charset `$8000` of the logo), `SCROLX` = `$18` (multicolour, 40 columns) for the top of the next frame | `music_api_play` | `irq_title_split` at line 130 |
| `irq_title_split` | 130 (`$82`) | after a short delay: `VMCSB` = `$32` (charset `text_font`), `SCROLX` = `$16` (multicolour, 38 columns, x-scroll 6) | none | `irq_title_frame` at line 253 |

[`irq_title_frame` `$152C`](../src/irq/screen_raster_irqs.asm#L81) also decrements [`frame_countdown` `$0048`](../src/constants.asm#L34) and the 16-bit `title_countdown`. Both stop at 0. **Code**

The first title IRQs came 2 frames after [`show_title_screen` `$0584`](../src/game/title_demo_start.asm#L83). `irq_title_split` ran at line 130. It wrote `VMCSB` at line 130, cycle 62 and `SCROLX` at line 131. `irq_title_frame` ran at line 253. It wrote `VMCSB` at line 253 and `SCROLX` at line 254. Then it called `music_api_play` at line 254. **Observed**

**The menu text is hires.** Text row 10 starts at line 131. Thus the logo rows 0-9 show in the logo charset, and the menu rows 10-24 show in the text font. The colour RAM of the menu rows is `$F1` (bit 3 clear: hires). Thus the menu text is hires, although `SCROLX` selects multicolour. **Conclusion**

[`game_over` `$188E`](../src/game/lose_fall_game_over.asm#L82) installs the same pair with a first compare line of 251 (`$FB`). After the first `irq_title_split` the line is 253 again. **Code**

~~~mermaid
flowchart LR
  A["lines 0-130<br/>logo charset, 40 columns"] --> B["line 130: irq_title_split<br/>text font, 38 columns, x-scroll 6"]
  B --> C["line 253: irq_title_frame<br/>logo charset for the next frame<br/>music, countdowns"]
  C --> A
~~~

![The title screen](images/screens/title.png)

The title screen: the logo rows above line 130, the menu in the text font below it.

### The PLAYER n screen

Before each turn, the game shows a big PLAYER 1 or PLAYER 2 banner for 64 frames, about 1.3 seconds. One handler gives the big letters a shading from dark grey to white and back. It changes a colour every two lines.

[`show_player_screen` `$0EA7`](../src/game/title_player_screens.asm#L71) does these steps:

1. It fills the screen with the blank logo character `$DC`.
2. It copies the big banner (`player_banner_top`) to rows 7 and 8.
3. It installs [`irq_player_screen` `$14A4`](../src/irq/screen_raster_irqs.asm#L10) at line 99 (`$63`).
4. It waits until `frame_countdown` is 0: 64 frames, or 128 frames in a two-player game. If the interrupt stops, the 24-bit counter `player_screen_wait` ends the wait. **Code**

| Handler | Line | Sets | Next |
|---|---|---|---|
| `irq_player_screen` | 99 (`$63`) | waits for line 110 (`irq_player_screen_sync`). Then `BGCOL1` = `$B`, `$C`, `$F`, `$1`, `$F`, `$C`, `$B` (dark grey, grey, light grey, white and back) about every 2 lines with `delay_raster_line`. Then `VMCSB` = `$30`, `SCROLX` = `$18`. Decrements `frame_countdown` | itself at line 99 |

`irq_player_screen` ran at line 99-100 in 64 frames after F7. The writes to `BGCOL1` came at lines 109, 112, 114, 116, 117, 119 and 121. `VMCSB` and `SCROLX` followed at line 121. **Observed**

Rows 7 and 8 cover lines 107-122. `BGCOL1` is multicolour 1 of the logo charset, so the big letters get a shading from grey to white and back. **Conclusion**

~~~mermaid
flowchart LR
  A["line 99: irq_player_screen<br/>wait for line 110"] --> B["lines 110-121<br/>BGCOL1: B, C, F, 1, F, C, B"]
  B --> C["line 121<br/>logo charset, 40 columns<br/>frame_countdown - 1"]
  C --> A
~~~

![The PLAYER 1 screen](images/screens/player_screen.png)

The PLAYER 1 screen with the shaded big text.

### The game screen

In a room, the screen has two parts. The status line at the top uses the hires text font on grey. The room below it uses the multicolour charset of the room. Some rooms also change their background colours at fixed lines, so one room can have up to three colour bands. The attract demo uses the same chain. Three handlers do this work:

- The handler at the bottom of the screen prepares the status line of the next frame and does the work of the frame.
- The handler at the top of the room changes to the room charset and the first colour band.
- The third handler runs at each colour split.

| Handler | Line | Sets | Next |
|---|---|---|---|
| `irq_game_bottom` | 253 (`$FD`) | `VMCSB` = `$32` (screen `game_screen`, charset `text_font`) and `BGCOL0` = `$FC` (grey) for the status line at the top of the next frame. Copies 12 bytes of the band palette of the room (`room_palette_ptr`) to `room_band_colours`. Copies the first 4 bytes of the split list of the room (`room_split_list_ptr`) to `raster_split_lines`. Calls `frame_update`. | `irq_game_playfield` at line 64 |
| `irq_game_playfield` | 64 (`$40`) | waits until the line is past 65 (`irq_playfield_wait`) plus a delay. `VMCSB` = `room_vmcsb` (the room charset). `BGCOL0` to `BGCOL2` = band 0 (`room_band_colours`). `raster_split_index` = 0, `band_palette_offset` = 3 | `irq_game_colour_split` at `raster_split_lines`[0], or `irq_game_bottom` when that is `$FD` |
| `irq_game_colour_split` | split line r | waits for line r+3 (`irq_split_wait`), writes `BGCOL0` to `BGCOL2` from the next 3 bytes of `room_band_colours` (`irq_split_set_colours`), `band_palette_offset` += 3, `raster_split_index` += 1 | the next split line, or `irq_game_bottom` when the next entry is `$FD` (`irq_chain_to_bottom`) |

[`irq_game_bottom` `$48C1`](../src/irq/game_irq.asm#L12) starts the chain of each frame. [`reset_play_state` `$0763`](../src/game/play_init.asm#L19) sets `VMCSB` = `$38` and `SCROLX` = `$18` one time. No game handler writes `SCROLX`. **Observed** (no write in a traced game frame).

Text rows 0-1 (lines 51-66) are the status line in the hires text font on grey. The room starts at text row 2 (line 67), the separator row. The room uses the multicolour room charset. The colour splits change the background and the two multicolours at fixed lines, 3 lines after the split line. **Conclusion**, from the trace in [The worked example](#the-worked-example-one-frame-of-room-0).

~~~mermaid
flowchart LR
  A["lines 51-66<br/>status line<br/>text font, grey"] --> B["line 64: irq_game_playfield<br/>room charset, band 0"]
  B --> C["split lines: irq_game_colour_split<br/>band 1, band 2"]
  C --> D["line 253: irq_game_bottom<br/>status setup, palette copy"]
  D --> E["line 259<br/>frame_update"]
  E --> A
~~~

### The work of each frame

In the game and in the attract demo, one routine does all the work of each frame: [`frame_update` `$15A8`](../src/game/frame_update.asm#L20). `irq_game_bottom` calls it in each frame of the game screen (**Observed** at line 259). It runs inside the interrupt, with interrupts disabled. The steps in the order of the code:

1. **Split index.** `raster_split_index` = 0.
2. **Sound effects.** The three effect voices play their next step, first [`sfx_voice1_update` `$EB03`](../src/sfx/sfx_voice1.asm#L19), with X = `room`. **There is no music in the game screen**: only `irq_title_frame` calls `music_api_play`. **Code**
3. **Random pointer.** `random_ptr` + 1 (`random_byte` also increments it). **Code**
4. **Sprites.** [`show_actor_sprites` `$25E2`](../src/actor/actor_sprites.asm#L75) writes the positions and colours of the actor sprites. **Code**
5. **Fall attack budget.** When `fall_attack_refill_timer` is 0, the code sets the three bytes of [`fall_attack_budget` `$4F45`](../src/constants.asm#L168) to 2. Then it decrements the timer. Thus a refill comes every 256 frames. **Code**
6. **Room charset.** `room_charset_hi` from `room_vmcsb` (see [The charset of the play area](#the-charset-of-the-play-area)). **Code**
7. **Handedness marks.** Status row 1, column 2 shows `L` (character `$2C`) when joystick 1 is left-handed ([`joystick_right_handed` `$1383`](../src/room/room_enemy_tables.asm#L114) = 0). Else it is blank. Column 37 does the same for joystick 2 (`joystick_right_handed+1`). But it does this only when port 2 is in use (`option_two_players` or `option_yamo_player2` set). **Code**
8. **Room time.** In a game (`game_mode` = 1) that is not paused (`pause_state` bit 7 clear), [`room_time` `$0087`](../src/constants.asm#L82) + 1. Its high byte stops at `$80`. `draw_room` sets it to 0. **Code**
9. **Frame counters and the idle timer.** `frame_counter` + 1. When it wraps (every 256 frames), [`idle_timer` `$0082`](../src/constants.asm#L77) + 1 while it is positive, and `frame_count_256` + 1 (16 bit). When `idle_timer` gets to `$80`, the code sets `pause_state` = `$86` (paused, debounce 6). Then it calls `show_paused` and [`start_screen_saver` `$102B`](../src/game/game_setup.asm#L139). **Code**
10. **Screen saver masks.** With `idle_timer` positive, `saver_and_mask` = `$FE` and `saver_eor_mask` = 0. With `idle_timer` negative (saver on), `idle_timer` = `$FE`, `saver_eor_mask` = `frame_count_256` and `saver_and_mask` = `$F7`. Then the 20 bytes of `room_band_colours` = ([`palette_backup` `$47B4`](../src/room/room_palettes_47a0.asm#L15) EOR `saver_eor_mask`) AND `saver_and_mask`. **Code**
11. **Protection check 1.** [`frame_update_check_ddr` `$166A`](../src/game/frame_update.asm#L140): `D6510` must hold `$EF`. Else the code branches back to step 9 for ever, inside the interrupt, and the game stops. The original loader leaves `$EF` there. **Code**
12. **Countdowns.** [`frame_countdown` `$0048`](../src/constants.asm#L34) - 1 and the 16-bit `title_countdown` - 1. Both stop at 0. In the game screen, `title_countdown` times the congratulations room ([`room19_init` `$425F`](../src/room/ending_room.asm#L7) sets `$0458`). **Code**
13. **Joysticks.** [`frame_update_read_input` `$1689`](../src/game/frame_update.asm#L171) saves the CIA 1 port directions (`CIADDRA`, `CIADDRB`) and makes both ports inputs. In the demo (`game_mode` = 0) it reads nothing: `update_actors` takes Bruce's input from the demo stream. In a game: **Code**
    - Bruce uses port 1 (`CIAPRB`) when `current_player` = 0, and port 2 (`CIAPRA`) when it is 1. Bits 0-3 go to `actor_joy_dir`, and fire (bit 4) goes to `actor_fire`.
    - A Yamo that a person plays (`option_yamo_player2` = 1) uses the other port. Its input goes to `actor_joy_dir+1` and `actor_fire+1`.
    - **The code turns a left-handed joystick by 90 degrees** (`joystick_right_handed`,X = 0): new = (old >> 2) OR [`joy_rotate_bits` `$4A85`](../src/room/room_tables.asm#L8)[old AND 3]. Up becomes right, down becomes left, left becomes up, right becomes down.
14. **Protection check 2.** [`frame_update_check_loader_mark` `$1703`](../src/game/frame_update.asm#L245): `prot_loader_mark` must hold `$32`. Else `frame_update_wipe_loop` writes over memory page by page, from the top page down. Its page counter is [`frame_update_wipe_counter` `$0539`](../src/game/title_demo_start.asm#L37), a byte of an instruction of `start_attract_demo`. The original loader leaves `$32` there. **Code**
15. **Port directions.** `frame_update_restore_ddr` restores the CIA 1 port directions. **Code**
16. **Idle reset.** [`frame_update_reset_idle` `$173B`](../src/game/frame_update.asm#L289) sets `idle_timer` = 0 in the demo, always. In a game, it does this when the game is not paused and Bruce's or Yamo's joystick has a direction or fire. **Code**
17. **Yamo player idle.** This step runs only in a game that is not paused, in a room with enemies (`room_no_enemy_flag` = 0), and with `option_yamo_player2` = 1. Without input on Yamo's joystick, [`yamo_idle_time` `$0089`](../src/constants.asm#L83) + 1 per frame. Input sets it to 0. At 7 * 256 = 1792 frames, Yamo goes back to the computer: **Code**
    - `option_yamo_player2` = 0, and `room_time+1` = `$20` (the top time level).
    - `play_open_sound` plays.
    - The code subtracts 5 falls from `falls_left` and from the parked player (`inactive_player_state`), but not below 0.
    - `show_falls_count` draws the count again.

The two copy-protection checks of `frame_update` never fail in the clean program with the entry state of the loader (**Observed**: all runs pass them). The [protection page](protection.md) lists them with the other checks.

While bit 7 of `pause_state` is 1, [`main_loop` `$1BC2`](../src/game/game_main_loop.asm#L23) skips the game work. But the interrupt and `frame_update` continue. Thus the sound effects, the countdowns and the idle timer also run during the pause. **Code**

### The timing

The main loop sets `frame_countdown` = 3. Then it waits until the interrupt counts it to 0. Thus a pass of the game logic takes at least 3 frames, and the game logic runs about 16.7 times a second. All other times of the game are also frame counts of the interrupt.

| Fact | Value | Evidence |
|---|---|---|
| Video standard | PAL, 50 frames per second, 312 lines, 19656 cycles per frame | **Observed** (the emulator runs PAL. The stopwatch gives 19656 cycles per frame) |
| Frames per handler | one `irq_title_frame` + one `irq_title_split` per frame. One `irq_player_screen` per frame. One `irq_game_bottom` + one `irq_game_playfield` + 0-2 `irq_game_colour_split` per frame | **Observed** |
| A pass of `main_loop` | at least 3 frames: it sets `frame_countdown` = 3 and waits at `main_loop_wait_frame` until the interrupt has counted it to 0 | **Code** |
| Pace in room 0 (demo) and room 7 | a pass starts every 3 frames, at line 264-277, just after `frame_update` of the third frame. In 300 frames of room 7 one pass took 4 frames. The next pass started at once. | **Observed** |
| Passes per second | 50 / 3 = 16.7 when no pass is late | **Conclusion** |
| Cold start to title | `restart_to_title` 79 frames after `cold_start`. The first title IRQ 4 frames later | **Observed** |
| Title countdown | `title_countdown` = `$0960` = 2400 frames = 48 s, then `start_attract_demo`. Each option key restarts it. | **Code**. **Observed**: 2394 frames from a countdown of `$095C` |
| Option message on the title | cleared about 350 frames after the last option key (`title_menu_check_message_timeout`, countdown `$0801`) | **Code** |
| Start of a game | F7 or fire: wait for the fire release, then 16 frames (`title_menu_start_game`) | **Code**. **Observed**: `start_new_game` 15 frames after the key |
| PLAYER n screen | 64 frames (128 in a two-player game) | **Observed**: 64 frames of `irq_player_screen` |
| Attract demo | ends when Bruce is knocked out, about 1714 frames (34 s) after `start_attract_demo`, or on fire of port 1 or F1 | **Observed** |
| Game over screen | 254 frames, then 64 more frames before the title (`game_over_wait`, `game_over_wait_title`) | **Code** |
| Congratulations room | `title_countdown` = `$0458` = 1112 frames (22 s). Bruce's joystick is forced up while `room_time+1` < 2 (512 frames) | **Code** |
| Room time levels | `room_time+1` >= `$19` (6400 frames, 128 s) and >= `$20` (8192 frames, 164 s) make the enemies faster | **Code** |
| Fall attack refill | every 256 frames | **Code** |
| Idle pause | 32768 frames (about 11 minutes) | **Code** |
| Player Yamo time-out | 1792 frames (36 s) | **Code** |

## The data

### The charset of the play area

Rooms 0-9 share one charset, and rooms 10-19 share another. The room of the wizard, room 18, has two charsets of its own. The second one is for the flash at the defeat of the wizard. The game keeps the charset of the room as the `VMCSB` value that `irq_game_playfield` writes at the top of the room. [`draw_room` `$09BC`](../src/room/draw_room.asm#L28) sets [`room_vmcsb` `$00F2`](../src/constants.asm#L117). Room 18 changes it during the wizard defeat (`room18_wizard_defeated`), and `frame_update` derives `room_charset_hi` from it every frame. **Code**

| `room_vmcsb` | Charset | `room_charset_hi` | Rooms |
|---|---|---|---|
| `$38` | `charset_rooms_0_9` | `$A0` | 0-9 |
| `$3A` | `charset_rooms_10_19` | `$A8` | 10-17, 19 |
| `$3C` | `charset_wizard` | `$B0` | 18 |
| `$3E` | `charset_wizard_flash` | `$B8` | 18, while the wizard flashes |

### The split lists and the band palettes

Each room has a split list (the lines where a new colour band starts) and a band palette (the colours of each band). `room_split_list_ptr` and `room_palette_ptr` hold one pointer per room. [`raster_split_lines` `$47F5`](../src/room/room_palettes_47a0.asm#L50) holds the split lines of the current frame. A list ends with `$FD`, the line of `irq_game_bottom`. A room with n split lines uses n + 1 records from its band palette. Each record has 3 bytes: `BGCOL0`, `BGCOL1` and `BGCOL2`. **Code**

| Rooms | Split list | Split lines | Band palette | Bands (`BGCOL0`/`BGCOL1`/`BGCOL2`, low nibble) |
|---|---|---|---|---|
| 0, 1, 2 | `split_list_r0`, `split_list_r1`, `split_list_r2` | `$78`, `$97` (120, 151) | `room_palette_r0_3` | B/1/E, B/2/1, C/2/1 |
| 3 | `split_list_r3` | `$62`, `$97` (98, 151) | `room_palette_r0_3` | B/1/E, B/2/1, C/2/1 |
| 4, 5, 6 | `split_list_none` | none | `room_palette_r4_6` | 6/E/1 |
| 7, 8, 9 | `split_list_none` | none | `room_palette_r7_9` | 8/9/1 |
| 10, 12, 14, 16 | `split_list_r10_12_14_16` | `$56` (86) | `room_palette_r10_12_14_16` | 6/E/B, C/E/B |
| 11 | `split_list_none` | none | `room_palette_r11` | 4/E/B |
| 13 | `split_list_none` | none | `room_palette_r13` | E/6/1 |
| 15 | `split_list_r15` | `$B6`, `$C7` (182, 199) | `room_palette_r15` | E/6/B, C/E/1, F/8/C |
| 17 | `split_list_none` | none | `room_palette_r17` | C/8/B |
| 18 | `split_list_none` | none | `room_palette_r18` | 0/E/4 |
| 19 | `split_list_none` | none | `room_palette_r19` | 6/2/1 |

The colour numbers are 0 black, 1 white, 2 red, 4 purple, 6 blue, 8 orange and 9 brown. B is dark grey, C is grey, E is light blue and F is light grey.

**The screen saver colours show one frame late.** [`irq_bottom_copy` `$4904`](../src/irq/game_irq.asm#L42) copies the palette of the room to [`room_band_colours` `$0153`](../src/constants.asm#L146) every frame, before it calls `frame_update`. The screen saver of `frame_update` writes `room_band_colours` after the copy, so its colours change the next frame only. **Code**

## The state machines

### The chain of handlers

`irq_vector` is the state of the interrupt: it names the handler of the next interrupt. A screen setup writes the first handler of its chain. After that, the handlers of the chain write the next handler. [`irq_entry` `$1103`](../src/irq/interrupt_entry.asm#L10) only follows the vector. **Code**

~~~mermaid
stateDiagram-v2
  state "Title frame (irq_title_frame)" as TF
  state "Title split (irq_title_split)" as TS
  state "PLAYER n (irq_player_screen)" as PS
  state "Game bottom (irq_game_bottom)" as GB
  state "Game playfield (irq_game_playfield)" as GP
  state "Colour split (irq_game_colour_split)" as CS
  [*] --> TF: title or game over
  TF --> TS
  TS --> TF
  [*] --> PS: PLAYER n screen
  PS --> PS
  [*] --> GB: game or demo starts
  GB --> GP
  GP --> CS: room has splits
  GP --> GB: no split
  CS --> CS: more splits
  CS --> GB: last split
~~~

| Handler | Runs at line | Condition | Next handler, at line | Code that writes `irq_vector` |
|---|---|---|---|---|
| any | - | the title screen is set up | `irq_title_frame`, 253 | `show_title_screen` |
| any | - | the game over screen is set up | `irq_title_frame`, 251 | `game_over` |
| any | - | the PLAYER n screen is set up | `irq_player_screen`, 99 | `show_player_screen` |
| any | - | `reset_play_state` (a game or the demo starts) | `irq_game_bottom`, 251 | `init_game_irq` |
| `irq_title_frame` | 253 | always | `irq_title_split`, 130 | `irq_title_frame` |
| `irq_title_split` | 130 | always | `irq_title_frame`, 253 | `irq_title_split` |
| `irq_player_screen` | 99 | always | itself, 99 | none (the vector stays) |
| `irq_game_bottom` | 253 | always | `irq_game_playfield`, 64 | `irq_game_bottom` |
| `irq_game_playfield` | 64 | `raster_split_lines`[0] is a line | `irq_game_colour_split`, that line | `irq_game_playfield` |
| `irq_game_playfield` | 64 | `raster_split_lines`[0] = `$FD` | `irq_game_bottom`, 253 | `irq_chain_to_bottom` |
| `irq_game_colour_split` | split line r | the next entry is a line | itself, that line | none (the vector stays) |
| `irq_game_colour_split` | split line r | the next entry is `$FD` | `irq_game_bottom`, 253 | `irq_chain_to_bottom` |

`init_game_irq` gives line 251 for the first interrupt of the game chain. After the first frame, `irq_game_bottom` runs at line 253. **Code**

### The idle timer and the screen saver

When nobody touches the joystick for about 11 minutes, the game pauses. It also starts a screen saver that cycles the colours of the room. The counter is `idle_timer`. `frame_update` increments it every 256 frames and sets it to 0 on input. A pause by the player starts it at `$51`, so a paused game starts the saver after about 4 minutes. The [main loop page](main_loop.md) tells how the pause keys work. **Code**

~~~mermaid
stateDiagram-v2
  state "Playing: idle_timer $00-$7F" as Play
  state "Paused by the player: idle_timer = $51" as Pause
  state "Paused with screen saver: idle_timer = $FE" as Saver
  [*] --> Play
  Play --> Play: input, idle_timer = 0
  Play --> Saver: idle_timer reaches $80
  Play --> Pause: SPACE or fire
  Pause --> Saver: idle_timer reaches $80
  Pause --> Play: SPACE or fire
  Saver --> Play: SPACE or fire
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Playing | joystick input (Bruce or player Yamo), or the demo | Playing, `idle_timer` = 0 | `frame_update_reset_idle` |
| Playing | 128 * 256 = 32768 frames without input (about 11 minutes) | Paused with screen saver | `frame_update`: `pause_state` = `$86`, `show_paused`, `start_screen_saver` |
| Playing | SPACE (`handle_game_keys`) or fire of the current player (`check_pause_fire`) | Paused, `idle_timer` = `$51` | `toggle_pause`, `show_paused` |
| Paused | `idle_timer` counts on from `$51`: 47 * 256 = 12032 frames (about 4 minutes) | Paused with screen saver | `frame_update` |
| Paused, or with saver | SPACE or fire | Playing. The saver stops (`stop_screen_saver`) | `toggle_pause` |

## The worked example: one frame of room 0

Room 0 has two colour splits. `room_split_list_ptr` entry 0 points to `split_list_r0` = `$78 $97 $FD`: splits at lines 120 and 151, then the end. `room_palette_ptr` entry 0 points to `room_palette_r0_3` = `$FB $F1 $FE`, `$FB $F2 $F1`, `$FC $F2 $F1`. These are three bands of `BGCOL0`/`BGCOL1`/`BGCOL2`. **Code** (the bytes of the image)

The runs traced the VIC writes in one frame of room 0, in the demo and in the game. These bytes arrive at the VIC three lines after each split line. **Observed**

| Line | Write |
|---|---|
| 253 | `irq_game_bottom`: `VMCSB` = `$32`, `BGCOL0` = `$FC` |
| 254 | `RASTER` = `$40` |
| 259 | `frame_update` starts |
| 64 | `irq_game_playfield` starts |
| 66-68 | `VMCSB` = `$38`, then `BGCOL0` = `$FB`, `BGCOL1` = `$F1`, `BGCOL2` = `$FE` (band 0) |
| 120 | `irq_game_colour_split` starts (split line `$78`) |
| 123-124 | `BGCOL0` = `$FB`, `BGCOL1` = `$F2`, `BGCOL2` = `$F1` (band 1) |
| 151 | `irq_game_colour_split` starts (split line `$97`) |
| 154 | `BGCOL0` = `$FC`, `BGCOL1` = `$F2`, `BGCOL2` = `$F1` (band 2). `RASTER` = `$FD` |

The second split finds `$FD` as the next entry. Thus it arms line 253 and writes `irq_game_bottom` into the vector again. **Code**

## Still open

- How long does `frame_update` take in the worst case? Which work made the 4-frame pass in room 7? A trace of the raster line at the RTS of `frame_update` and at `main_loop_wait_frame` can answer it. The run must be long and have all actors.
- Does the colour split of room 15 at line 199 show a visible seam with sprites over it? A screenshot of room 15 with Bruce on the split can answer it.
