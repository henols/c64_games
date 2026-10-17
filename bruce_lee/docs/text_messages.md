# Bruce Lee: text and messages

How the program writes text and small graphic pieces to the screen: the message printer [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message),
the message format, the status line, the title texts, the big banners (PLAYER n, GAME OVER) and the catalogue of
all 101 messages.

**Scope.**

- [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message), the message format, the text line tables and the height of the text.
- The status line (rows 0-1 of the game screen), the pause message, the version line.
- The title menu texts, the joystick messages, the PLAYER n and GAME OVER screens.
- The catalogue of the messages of [`message_ptrs`](../src/messages.asm#L11) [`$43BE`](reference/modules/messages.md#message_ptrs), the unused messages and the texts without a pointer.
- Sources: [messages.asm](../src/messages.asm), [actor_driver_text.asm](../src/actor_driver_text.asm),
  [pause_status_line.asm](../src/pause_status_line.asm), [status_and_keys.asm](../src/status_and_keys.asm),
  [banners.asm](../src/banners.asm), [options_and_patterns.asm](../src/options_and_patterns.asm),
  [title_demo_start.asm](../src/title_demo_start.asm), [title_menu.asm](../src/title_menu.asm),
  [title_player_screens.asm](../src/title_player_screens.asm), [lose_fall_game_over.asm](../src/lose_fall_game_over.asm).
  The charsets and the VIC set-up are on the page [graphics.md](graphics.md).

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *message* is an entry of [`message_ptrs`](../src/messages.asm#L11) [`$43BE`](reference/modules/messages.md#message_ptrs), numbered `$00-$64`. The room code calls a graphic message a
  *tile*. A *text line* is an entry of the row tables [`text_line_top_lo`](../src/fireball_text_score_vars.asm#L40) [`$4338`](reference/modules/fireball_text_score_vars.md#text_line_top_lo) / [`text_line_bottom_lo`](../src/fireball_text_score_vars.asm#L50) [`$4360`](reference/modules/fireball_text_score_vars.md#text_line_bottom_lo)
  (section 2). A *cell code* is the character code that a message byte gives.
- A *pass* is one run of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) (3 frames).
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an
  interpretation.

## 1. Overview

~~~mermaid
flowchart TB
  CALL["caller: A = message, X = text line, Y = offset"] --> PM["print_message $17E2"]
  PM --> STR["set_text_row_pointers $1A67"]
  STR --> TAB["text_line_top/bottom tables $4338-$4387"]
  STR --> H{"text_single_height $0100 nonzero?"}
  H -- yes --> DUM["lower row = io1_dummy $DE00"]
  PM --> PTR["message_ptrs $43BE"]
  PM --> LOOP["byte - $20 to upper row, OR $80 to lower row, until $A0"]
~~~

All text and all small changes of a room go through [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message), except four direct writers:
the score digits ([`print_bcd_byte`](../src/status_and_keys.asm#L39) [`$1B17`](reference/modules/status_and_keys.md#print_bcd_byte)), the falls count ([`print_hex_byte`](../src/status_and_keys.asm#L116) [`$1B84`](reference/modules/status_and_keys.md#print_hex_byte)), the version line
([`toggle_credit_line`](../src/status_and_keys.asm#L94) [`$1B68`](reference/modules/status_and_keys.md#toggle_credit_line)) and the big banners ([`show_player_screen`](../src/title_player_screens.asm#L71) [`$0EA7`](reference/modules/title_player_screens.md#show_player_screen), [`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over)) (**Code**).

## 2. [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message) and the message format

### 2.1 Where the data is

| Name | Address | Layout | Readers | Writers |
|---|---|---|---|---|
| [`message_ptrs`](../src/messages.asm#L11) | `$43BE` | 101 words, index = message number | [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message) | — |
| messages | `$4488-$4785` | byte strings, each ended by `$A0`; not in number order | [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message) | — |
| [`text_line_top_lo`](../src/fireball_text_score_vars.asm#L40) / [`text_line_top_hi`](../src/fireball_text_score_vars.asm#L45) | `$4338` / `$434C` | 20 + 20 bytes; entries 0-13 used: address of the upper screen row of text line n | [`set_text_row_pointers`](../src/pause_status_line.asm#L117) [`$1A67`](reference/modules/pause_status_line.md#set_text_row_pointers) | [`build_screen_row_tables`](../src/play_init.asm#L144) [`$0869`](reference/modules/play_init.md#build_screen_row_tables), [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) |
| [`text_line_bottom_lo`](../src/fireball_text_score_vars.asm#L50) / [`text_line_bottom_hi`](../src/fireball_text_score_vars.asm#L55) | `$4360` / `$4374` | the same for the lower screen row | [`set_text_row_pointers`](../src/pause_status_line.asm#L117) [`$1A67`](reference/modules/pause_status_line.md#set_text_row_pointers) | the same |
| [`text_single_height`](../src/constants.asm#L130) | `$0100` | 0 = two rows high, nonzero = one row high | [`set_text_row_pointers`](../src/pause_status_line.asm#L117) [`$1A67`](reference/modules/pause_status_line.md#set_text_row_pointers) | section 2.4 |

### 2.2 The text lines

[`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) calls [`build_screen_row_tables`](../src/play_init.asm#L144) [`$0869`](reference/modules/play_init.md#build_screen_row_tables) with [`game_screen`](../src/game_screen.asm#L9) [`$8C00`](reference/modules/game_screen.md#game_screen) - 40. Entry n gets
the upper row `$8BD8` + 80n and the lower row `$8C00` + 80n. Then it patches the first two entries (**Code**):

| Text line | Upper row | Lower row | Use |
|---|---|---|---|
| 0 | screen row 0 (`$8C00`) | [`io1_dummy`](../src/constants.asm#L240) [`$DE00`](reference/variables.md#io1_dummy) | status line: offsets 0-39 = row 0, offsets 40-79 = row 1 |
| 1 | screen row 1 (`$8C28`) | [`io1_dummy`](../src/constants.asm#L240) [`$DE00`](reference/variables.md#io1_dummy) | status line (the pause message) |
| n = 2-12 | screen row 2n-1 | screen row 2n | the room (tile row n-2), the title menu |
| 13 | screen row 25 (`$8FE8`) | screen row 26 | not used |

The offset Y can be 40 or more: then the text starts on the next screen row. The title uses this: text line 6,
offset `$31` (49) is screen row 12, column 9 (**Code**). Writes to [`io1_dummy`](../src/constants.asm#L240) [`$DE00`](reference/variables.md#io1_dummy) go to the I/O area 1 and are
lost (**Conclusion**: no cartridge is present).

### 2.3 The byte layout

| Byte b | Meaning |
|---|---|
| `$A0` | End of the message. |
| any other | One cell. Cell code c = (b - `$20`) AND `$7F`. c goes to the upper row, c OR `$80` to the lower row. |

| Byte b | Cell code c | In [`text_font`](../src/text_font.asm#L9) [`$8800`](reference/modules/text_font.md#text_font) (rows 0-1, title) | In a room charset (rows 3-24) |
|---|---|---|---|
| `$20-$3F` | `$00-$1F` | space, punctuation, digits (ASCII - `$20`) | tiles `$00-$1F` |
| `$40-$5F` | `$20-$3F` | @ (a solid block), A-Z, [ £ ] arrows | tiles `$20-$3F` |
| `$60-$7F` | `$40-$5F` | the same as `$00-$1F`, inverted; `$42` and `$56` = key cap ends | tiles `$40-$5F` |
| `$80-$9F`, `$00-$1F` | `$60-$7F` | `$20-$3F` inverted | tiles `$60-$7F` |
| `$A1-$FF` | `$01-$5F` | as byte b - `$80` | as byte b - `$80` |

So an ASCII text prints as text with the text font, and in a room the same printer draws tile c (upper half c,
lower half c + `$80`, see [graphics.md](graphics.md#3-double-height-tiles-and-charsets)). The source writes the
text messages with `!pet` (ACME turns lower-case letters into `$41-$5A`).

### 2.4 Double and single height

- [`text_single_height`](../src/constants.asm#L130) [`$0100`](reference/variables.md#text_single_height) = 0: the lower row gets c OR `$80`. In a room charset that is the lower half of the
  tile: the cell is 8 x 16 pixels.
- [`text_single_height`](../src/constants.asm#L130) [`$0100`](reference/variables.md#text_single_height) nonzero: [`set_text_row_pointers`](../src/pause_status_line.asm#L117) [`$1A67`](reference/modules/pause_status_line.md#set_text_row_pointers) sets the lower row pointer to
  [`io1_dummy`](../src/constants.asm#L240) [`$DE00`](reference/variables.md#io1_dummy); only the upper row is drawn.
- Text lines 0 and 1 are always one row high, because their lower rows are [`io1_dummy`](../src/constants.asm#L240) [`$DE00`](reference/variables.md#io1_dummy).

| Writer of [`text_single_height`](../src/constants.asm#L130) [`$0100`](reference/variables.md#text_single_height) | Value | Effect |
|---|---|---|
| [`clear_text_screen`](../src/pause_status_line.asm#L104) [`$1A56`](reference/modules/pause_status_line.md#clear_text_screen), [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) (start) | 0 | double height |
| [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) (before the menu) | `$FF` | the title menu and the joystick messages are one row high |
| [`print_top_label`](../src/pause_status_line.asm#L170) [`$1ABB`](reference/modules/pause_status_line.md#print_top_label) | 3 | one row (status line) |
| [`show_paused_message`](../src/status_and_keys.asm#L141) [`$1BA4`](reference/modules/status_and_keys.md#show_paused_message) / [`clear_paused_message`](../src/status_and_keys.asm#L154) [`$1BB6`](reference/modules/status_and_keys.md#clear_paused_message) | `$0B` / `$0C` (the message number) | one row |
| [`print_status_row_message`](../src/status_and_keys.asm#L148) [`$1BAD`](reference/modules/status_and_keys.md#print_status_row_message) (after the print) | 0 | back to double height |

[`start_new_game`](../src/title_demo_start.asm#L283) [`$070E`](reference/modules/title_demo_start.md#start_new_game) and [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$0531`](reference/modules/title_demo_start.md#start_attract_demo) call [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state), which calls
[`clear_text_screen`](../src/pause_status_line.asm#L104) [`$1A56`](reference/modules/pause_status_line.md#clear_text_screen): the game starts with double height (**Code**).

### 2.5 The decoder

```
print_message(A = message, X = text line, Y = offset):
    set_text_row_pointers(X)            ; row_ptr_top, row_ptr_bottom (io1_dummy when single height)
    data_ptr = message_ptrs[A] - Y      ; so (data_ptr),Y is the first byte
    loop:
        c = (data_ptr),Y - $20
        if c == $80: return              ; byte $A0
        (row_ptr_top),Y    = c AND $7F
        (row_ptr_bottom),Y = (c AND $7F) OR $80
        Y = Y + 1
        if Y == 0: increment the high bytes of the three pointers   ; never executed
```

One index register serves the message and the screen row, because the message pointer is moved back by the start
offset (**Code**: [`print_message`](../src/actor_driver_text.asm#L59) [`$17E9`](../src/actor_driver_text.asm#L65)). The page-crossing code at [`print_message`](../src/actor_driver_text.asm#L59) [`$180E`](../src/actor_driver_text.asm#L86) never ran in the
coverage (**Observed**: coverage).

### 2.6 Worked examples

**Message `$0B`, [`msg_paused`](../src/messages.asm#L101) [`$457E`](reference/modules/messages.md#msg_paused).** [`show_paused_message`](../src/status_and_keys.asm#L141) [`$1BA4`](reference/modules/status_and_keys.md#show_paused_message) calls it with X = 1, Y = `$0F` and
[`text_single_height`](../src/constants.asm#L130) [`$0100`](reference/variables.md#text_single_height) = `$0B`.

| Byte | `$2A` | `$2A` | `$20` | `$50` | `$41` | `$55` | `$53` | `$45` | `$44` | `$20` | `$2A` | `$2A` | `$A0` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cell code | `$0A` | `$0A` | `$00` | `$30` | `$21` | `$35` | `$33` | `$25` | `$24` | `$00` | `$0A` | `$0A` | end |
| Character | * | * | space | P | A | U | S | E | D | space | * | * | |

Text line 1 starts at `$8C28` (row 1). The cells go to `$8C37-$8C42`: row 1, columns 15-26. They cover "TOP" and
the top score. The lower row goes to [`io1_dummy`](../src/constants.asm#L240) [`$DE00`](reference/variables.md#io1_dummy) (**Code**; **Observed**: the pause screenshot).

![The pause message on the status line](images/screens/paused.png)

The pause message covers TOP and the top score; 1UP stays on.

**Message `$1D`, [`msg_statue_mouth_a`](../src/messages.asm#L173) [`$45E4`](reference/modules/messages.md#msg_statue_mouth_a).** [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3642`](reference/modules/room_frames_0_7.md#room00_frame) calls it with X = 9, Y = 7. The byte `$E6`
gives c = (`$E6` - `$20`) AND `$7F` = `$46`. Text line 9 has its upper row at `$8BD8` + 9 x 80 = `$8EA8` (screen row
17). The printer writes `$46` to `$8EAF` (row 17, column 7) and `$C6` to `$8ED7` (row 18, column 7): tile `$46` of
[`charset_rooms_0_9`](../src/constants.asm#L157) [`$A000`](reference/variables.md#charset_rooms_0_9), the open mouth of the statue (**Code**).

## 3. The status line

The status line is screen rows 0 and 1, drawn with [`text_font`](../src/text_font.asm#L9) [`$8800`](reference/modules/text_font.md#text_font) (`$D018` = `$32` from raster `$FD` to
raster `$42`). The colour RAM of rows 0-1 is black with bit 3 clear: hires black characters on the grey
background `$FC` (**Code**: [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state), [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom)).

| Row | Columns | Content | Writer |
|---|---|---|---|
| 0 | 0-39 | 40 x code `$20` (solid block): a black bar | [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state), [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) |
| 0 | 0-39 | the version line `BRUCE LEE (C) 1984 DATASOFT REV.2 BY RJF` | [`toggle_credit_line`](../src/status_and_keys.asm#L94) [`$1B68`](reference/modules/status_and_keys.md#toggle_credit_line) (V key) |
| 0 | 10-30 | `** CONGRATULATIONS **` (message `$04`) | [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame) |
| 1 | 2 | `L` (code `$2C`) when joystick 1 is left-handed | [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) |
| 1 | 4-6 | `1UP` / `2UP` (messages `$01`/`$02`), blinking | [`blink_player_label`](../src/pause_status_line.asm#L147) [`$1A96`](reference/modules/pause_status_line.md#blink_player_label) |
| 1 | 8-13 | the score, 6 digits | [`show_score`](../src/score.asm#L39) [`$315A`](reference/modules/score.md#show_score) via [`print_bcd_byte`](../src/status_and_keys.asm#L39) [`$1B17`](reference/modules/status_and_keys.md#print_bcd_byte) (offsets `$30`, `$32`, `$34`) |
| 1 | 16-18 | `TOP` (message `$03`) | [`print_top_label`](../src/pause_status_line.asm#L170) [`$1ABB`](reference/modules/pause_status_line.md#print_top_label) |
| 1 | 20-25 | the top score | [`show_high_score`](../src/score.asm#L112) [`$31C2`](reference/modules/score.md#show_high_score) (offsets `$3C`, `$3E`, `$40`) |
| 1 | 28-32 | `FALLS` (message `$05`) | [`print_falls_label`](../src/pause_status_line.asm#L177) [`$1AC7`](reference/modules/pause_status_line.md#print_falls_label) |
| 1 | 34-35 | the falls left, 2 digits | [`show_falls_count`](../src/status_and_keys.asm#L10) [`$1AED`](reference/modules/status_and_keys.md#show_falls_count) via [`print_hex_byte`](../src/status_and_keys.asm#L116) [`$1B84`](reference/modules/status_and_keys.md#print_hex_byte) (offset `$4A`) |
| 1 | 37 | `L` when joystick 2 is in use and left-handed | [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) |
| 1 | 15-26 | `** PAUSED **` (message `$0B`), erased with message `$0C` | [`show_paused_message`](../src/status_and_keys.asm#L141) [`$1BA4`](reference/modules/status_and_keys.md#show_paused_message), [`clear_paused_message`](../src/status_and_keys.asm#L154) [`$1BB6`](reference/modules/status_and_keys.md#clear_paused_message) |

A digit is code `$10` + digit ([`print_bcd_byte`](../src/status_and_keys.asm#L39) [`$1B17`](reference/modules/status_and_keys.md#print_bcd_byte)). [`print_hex_byte`](../src/status_and_keys.asm#L116) [`$1B84`](reference/modules/status_and_keys.md#print_hex_byte) adds 7 for the nibbles A-F;
only the unused [`debug_show_values`](../src/pause_status_line.asm#L187) [`$1AD1`](reference/modules/pause_status_line.md#debug_show_values) would need that (**Code**). Leaving the pause draws `TOP` and the top
score again ([`toggle_pause`](../src/pause_status_line.asm#L69) [`$1A22`](reference/modules/pause_status_line.md#toggle_pause)).

![The status line with the version line](images/screens/status_line_v.png)

After the V key: row 0 shows the version line in black on grey, row 1 the status line.

![Room 19 with the congratulations message](images/rooms/room19.png)

Room 19: message `$04` in row 0; the 1UP mark is in its blank phase.

### 3.1 The blink of 1UP / 2UP

[`blink_player_label`](../src/pause_status_line.asm#L147) [`$1A96`](reference/modules/pause_status_line.md#blink_player_label) runs once per pass (from [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop), not while paused). [`up_blink_timer`](../src/fireball_text_score_vars.asm#L110) [`$43BD`](reference/modules/fireball_text_score_vars.md#up_blink_timer)
`$43BD` counts down:

~~~mermaid
stateDiagram-v2
  state "Label shown" as Shown
  state "Blank" as Blank
  [*] --> Shown: reset_play_state $0763 (timer $11)
  Shown --> Blank: timer reaches 0
  Blank --> Shown: timer reaches $10
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Shown | [`up_blink_timer`](../src/fireball_text_score_vars.asm#L110) [`$43BD`](reference/modules/fireball_text_score_vars.md#up_blink_timer) - 1 = 0 | Blank: timer = `$20`, print message `$00` at line 0, offset `$2C` | [`blink_player_label`](../src/pause_status_line.asm#L147) [`$1A96`](reference/modules/pause_status_line.md#blink_player_label) |
| Blank | [`up_blink_timer`](../src/fireball_text_score_vars.asm#L110) [`$43BD`](reference/modules/fireball_text_score_vars.md#up_blink_timer) - 1 = `$10` | Shown: print message 1 + [`current_player`](../src/constants.asm#L14) [`$03`](reference/variables.md#current_player) at line 0, offset `$2C` | [`blink_player_label_show`](../src/pause_status_line.asm#L156) [`$1AA8`](reference/modules/pause_status_line.md#blink_player_label_show) |

The period is 32 passes, 96 frames. [`show_paused`](../src/pause_status_line.asm#L88) [`$1A42`](reference/modules/pause_status_line.md#show_paused) sets the timer to `$11` and calls the routine: the label
appears and stays while the game is paused (**Code**; **Observed**: the paused screenshot shows 1UP).

## 4. Title texts

![The title screen](images/screens/title.png)

The title: three logo rows from [`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars), the menu from message `$4F-$51` in the text font.

[`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) draws (**Code**; **Observed**: title screenshots):

| Screen rows | Content | Source |
|---|---|---|
| 0-8 | blank logo character `$DC` | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) |
| 2 | `DATASOFT PRESENTS` in small logo letters (2 characters per letter) | [`title_logo_row2`](../src/banners.asm#L20) [`$4A0D`](reference/modules/banners.md#title_logo_row2), each byte OR `$80` |
| 5-6 | `BRUCE LEE` in big letters (2 x 2 characters) | [`title_logo_row5`](../src/banners.asm#L8) [`$49BD`](reference/modules/banners.md#title_logo_row5), [`title_logo_row6`](../src/banners.asm#L14) [`$49E5`](reference/modules/banners.md#title_logo_row6) |
| 9 | `BY RON J FORTIER` in small logo letters | [`title_logo_row9`](../src/banners.asm#L26) [`$4A35`](reference/modules/banners.md#title_logo_row9) |
| 12 | `F3 - 1 PLAYER - 2 PLAYERS` (message `$4F`, line 6, offset `$31`) | [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message) |
| 14 | `PRESS F5 - COMPUTER - OPPONENT` (message `$50`, line 7, offset `$2B`) | [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message) |
| 16 | `F7 - TO BEGIN GAME` (message `$51`, line 8, offset `$31`) | [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message) |
| 19 | a joystick message (messages `$08`, `$09`, `$0A`, `$0D`, line 10, offset 2) | [`title_menu_loop`](../src/title_menu.asm#L14) [`$08B1`](reference/modules/title_menu.md#title_menu_loop) |

- The menu messages draw the key caps with the bytes `$62` (code `$42`, left end) and `$76` (code `$56`, right
  end). [`title_highlight_defaults`](../src/title_demo_start.asm#L188) [`$066D`](reference/modules/title_demo_start.md#title_highlight_defaults) adds `$40` to the key names (columns 11-12 of rows 12, 14, 16) and to
  columns 16-25 of rows 12 and 14: inverted text for `F3`, `F5`, `F7`, `1 PLAYER` and `COMPUTER`.
- [`title_show_players_choice`](../src/title_player_screens.asm#L27) [`$0E65`](reference/modules/title_player_screens.md#title_show_players_choice) and [`title_show_opponent_choice`](../src/title_player_screens.asm#L10) [`$0E4C`](reference/modules/title_player_screens.md#title_show_opponent_choice) toggle bit 6 of columns 16-35
  (except code `$4D`) and move the box ends, when F3 or F5 changes the option.
- The keys L, D, shift-L, shift-D print a joystick message: [`title_set_joy1_left_handed`](../src/title_menu.asm#L117) [`$0969`](reference/modules/title_menu.md#title_set_joy1_left_handed) (message `$08`),
  [`title_set_joy1_right_handed`](../src/title_menu.asm#L133) [`$0988`](reference/modules/title_menu.md#title_set_joy1_right_handed) (`$09`), [`title_set_joy2_left_handed`](../src/title_menu.asm#L125) [`$0979`](reference/modules/title_menu.md#title_set_joy2_left_handed) (`$0A`),
  [`title_set_joy2_right_handed`](../src/title_menu.asm#L141) [`$0998`](reference/modules/title_menu.md#title_set_joy2_right_handed) (`$0D`). [`title_menu_check_message_timeout`](../src/title_menu.asm#L37) [`$08E0`](reference/modules/title_menu.md#title_menu_check_message_timeout) erases it with message
  `$0E` (36 spaces) when [`title_countdown`](../src/constants.asm#L39) [`$49`](reference/variables.md#title_countdown) reaches `$08xx` with a low byte below 2: about 350 frames after the
  last option change (**Code**).

![The title with two players and a human opponent](images/screens/title_two_players_opponent_left_handed.png)

After F3, F5 and L: the boxes on `2 PLAYERS` and `OPPONENT`, and message `$08` on row 19.

![The title after shift-D](images/screens/title_port2_right_handed.png)

After shift-D: message `$0D` on row 19.

## 5. The big banners

### 5.1 The big glyphs

The PLAYER n screen, the GAME OVER screen and the title logo use [`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars) (characters `$80-$FF`
of the charset at `$8000`, `$D018` = `$30`). A table byte g is written as g OR `$80`. A big glyph is 2 x 2
characters (**Code**):

| Position | Character |
|---|---|
| upper left | g |
| lower left | g + 1 |
| upper right | g + 2 |
| lower right | g + 3 |

| Glyph | A | B | C | E | G | L | M | O | P | R | U | V | Y | digit d | blank |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g | `$00` | `$04` | `$08` | `$0C` | `$10` | `$14` | `$18` | `$1C` | `$20` | `$24` | `$28` | `$2C` | `$30` | `$34` + 4d | `$5C` |

(**Code**: the bytes of [`title_logo_row5`](../src/banners.asm#L8) [`$49BD`](reference/modules/banners.md#title_logo_row5), [`player_banner_top`](../src/banners.asm#L36) [`$4A5D`](reference/modules/banners.md#player_banner_top), [`game_over_letters_top`](../src/options_and_patterns.asm#L28) [`$42CD`](reference/modules/options_and_patterns.md#game_over_letters_top) and
[`draw_big_digit`](../src/lose_fall_game_over.asm#L214) [`$1984`](reference/modules/lose_fall_game_over.md#draw_big_digit).) The set holds only the letters that the program needs.

### 5.2 PLAYER n

[`show_player_screen`](../src/title_player_screens.asm#L71) [`$0EA7`](reference/modules/title_player_screens.md#show_player_screen) (at the start of a game and of each turn):

1. Blanks the screen, sprites off, blue border and background, fills `$8C00-$8FFF` with `$DC`.
2. Copies 2 bytes of [`player_banner_digit_top`](../src/banners.asm#L43) [`$4A7D`](reference/modules/banners.md#player_banner_digit_top) / [`player_banner_digit_bottom`](../src/banners.asm#L46) [`$4A81`](reference/modules/banners.md#player_banner_digit_bottom) (index
   [`current_player`](../src/constants.asm#L14) [`$03`](reference/variables.md#current_player) x 2) into [`player_banner_top+14`](../src/banners.asm#L36) [`$4A6B`](reference/modules/banners.md#player_banner_top) / [`player_banner_bottom+14`](../src/banners.asm#L39) [`$4A7B`](reference/modules/banners.md#player_banner_bottom).
3. Copies the 16 bytes of [`player_banner_top`](../src/banners.asm#L36) [`$4A5D`](reference/modules/banners.md#player_banner_top) / [`player_banner_bottom`](../src/banners.asm#L39) [`$4A6D`](reference/modules/banners.md#player_banner_bottom), OR `$80`, to screen rows 7
   and 8, columns 12-27.
4. Installs [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) (line `$63`), which shades the letters with [`BGCOL1`](../src/constants.asm#L189), and waits 64 frames
   (128 with two players).

Worked example: [`player_banner_top`](../src/banners.asm#L36) [`$4A5D`](reference/modules/banners.md#player_banner_top) = `20 22 14 16 00 02 30 32 0C 0E 24 26 5C 5C 38 3A`. The pairs give
P (`$20`), L (`$14`), A (`$00`), Y (`$30`), E (`$0C`), R (`$24`), blank (`$5C`), 1 (`$38` = `$34` + 4). Row 7 gets
`$A0 $A2 $94 $96 ...`, row 8 (from [`player_banner_bottom`](../src/banners.asm#L39) [`$4A6D`](reference/modules/banners.md#player_banner_bottom)) `$A1 $A3 $95 $97 ...` (**Observed**: the
PLAYER 1 screenshot).

![The PLAYER 1 screen](images/screens/player_screen.png)

### 5.3 GAME OVER

[`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over) uses the title interrupts ([`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame)) and a blue screen, and draws:

| Screen rows | Columns | Content | Source |
|---|---|---|---|
| 1-2 | 11-28 | `GAME OVER` | [`game_over_letters_top`](../src/options_and_patterns.asm#L28) [`$42CD`](reference/modules/options_and_patterns.md#game_over_letters_top) / [`game_over_letters_bottom`](../src/options_and_patterns.asm#L34) [`$42DF`](reference/modules/options_and_patterns.md#game_over_letters_bottom), 18 bytes each, OR `$80` |
| 5-6 | 12-27 | `PLAYER n` | [`player_banner_top`](../src/banners.asm#L36) [`$4A5D`](reference/modules/banners.md#player_banner_top) / [`player_banner_bottom`](../src/banners.asm#L39) [`$4A6D`](reference/modules/banners.md#player_banner_bottom) |
| 8-9 | 14-25 | the score, 6 big digits | [`draw_big_digit`](../src/lose_fall_game_over.asm#L214) [`$1984`](reference/modules/lose_fall_game_over.md#draw_big_digit): glyph `$34` + 4d OR `$80` |

Then it waits 254 frames, and 64 more before [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) (**Code**).

**Bug.** [`game_over_digit_loop`](../src/lose_fall_game_over.asm#L144) [`$1909`](reference/modules/lose_fall_game_over.md#game_over_digit_loop) runs one time only (`DEY` / `BPL` from Y = 0). It copies only the left
half of the player digit into the banner; the right half keeps the value of the last PLAYER n screen (**Code**).
**Conclusion.** The bug has no visible effect: [`lose_fall`](../src/lose_fall_game_over.asm#L14) [`$1818`](reference/modules/lose_fall_game_over.md#lose_fall) shows the PLAYER n screen of the current player
at the start of each fall, so the last PLAYER n screen before a game over is always for the same player.

## 6. The catalogue of the messages

Message number = index in [`message_ptrs`](../src/messages.asm#L11) [`$43BE`](reference/modules/messages.md#message_ptrs). "Line/offset" are the X / Y of the call; for a text line n >= 2,
offset y < 40 is screen row 2n-1, column y. A graphic message is listed with its cell codes (upper row; the lower
row is each code OR `$80`).

### 6.1 Text messages

| # | Name | Text | Printed by | Line / offset |
|---|---|---|---|---|
| `$00` | [`msg_blank3`](../src/messages.asm#L40) [`$4488`](reference/modules/messages.md#msg_blank3) | 3 spaces | [`blink_player_label`](../src/pause_status_line.asm#L147) [`$1A96`](reference/modules/pause_status_line.md#blink_player_label) (erase 1UP/2UP); [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps) (top row after a burst) | 0 / `$2C`; trap position |
| `$01` | [`msg_1up`](../src/messages.asm#L44) [`$448C`](reference/modules/messages.md#msg_1up) | `1UP` | [`blink_player_label_show`](../src/pause_status_line.asm#L156) [`$1AA8`](reference/modules/pause_status_line.md#blink_player_label_show) (A = 1 + [`current_player`](../src/constants.asm#L14) [`$0003`](reference/variables.md#current_player)) | 0 / `$2C` |
| `$02` | [`msg_2up`](../src/messages.asm#L48) [`$4490`](reference/modules/messages.md#msg_2up) | `2UP` | [`blink_player_label_show`](../src/pause_status_line.asm#L156) [`$1AA8`](reference/modules/pause_status_line.md#blink_player_label_show) | 0 / `$2C` |
| `$03` | [`msg_top`](../src/messages.asm#L52) [`$4494`](reference/modules/messages.md#msg_top) | `TOP` | [`print_top_label`](../src/pause_status_line.asm#L170) [`$1ABB`](reference/modules/pause_status_line.md#print_top_label) | 0 / `$38` |
| `$04` | [`msg_congratulations`](../src/messages.asm#L417) [`$4750`](reference/modules/messages.md#msg_congratulations) | `** CONGRATULATIONS **` | [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame) | 0 / `$0A` |
| `$05` | [`msg_falls`](../src/messages.asm#L56) [`$4498`](reference/modules/messages.md#msg_falls) | `FALLS` | [`print_falls_label`](../src/pause_status_line.asm#L177) [`$1AC7`](reference/modules/pause_status_line.md#print_falls_label) | 0 / `$44` |
| `$08` | [`msg_joy1_left_handed`](../src/messages.asm#L72) [`$44CF`](reference/modules/messages.md#msg_joy1_left_handed) | `JOYSTICK # 1 IS IN LEFT HANDED MODE ` | [`title_set_joy1_left_handed`](../src/title_menu.asm#L117) [`$0969`](reference/modules/title_menu.md#title_set_joy1_left_handed) | 10 / 2 |
| `$09` | [`msg_joy1_right_handed`](../src/messages.asm#L77) [`$44F4`](reference/modules/messages.md#msg_joy1_right_handed) | `JOYSTICK # 1 IS IN RIGHT HANDED MODE` | [`title_set_joy1_right_handed`](../src/title_menu.asm#L133) [`$0988`](reference/modules/title_menu.md#title_set_joy1_right_handed) | 10 / 2 |
| `$0A` | [`msg_joy2_left_handed`](../src/messages.asm#L82) [`$4519`](reference/modules/messages.md#msg_joy2_left_handed) | `JOYSTICK # 2 IS IN LEFT HANDED MODE ` | [`title_set_joy2_left_handed`](../src/title_menu.asm#L125) [`$0979`](reference/modules/title_menu.md#title_set_joy2_left_handed) | 10 / 2 |
| `$0B` | [`msg_paused`](../src/messages.asm#L101) [`$457E`](reference/modules/messages.md#msg_paused) | `** PAUSED **` | [`show_paused_message`](../src/status_and_keys.asm#L141) [`$1BA4`](reference/modules/status_and_keys.md#show_paused_message) | 1 / `$0F` |
| `$0C` | [`msg_blank12`](../src/messages.asm#L105) [`$458B`](reference/modules/messages.md#msg_blank12) | 12 spaces | [`clear_paused_message`](../src/status_and_keys.asm#L154) [`$1BB6`](reference/modules/status_and_keys.md#clear_paused_message) | 1 / `$0F` |
| `$0D` | [`msg_joy2_right_handed`](../src/messages.asm#L87) [`$453E`](reference/modules/messages.md#msg_joy2_right_handed) | `JOYSTICK # 2 IS IN RIGHT HANDED MODE` | [`title_set_joy2_right_handed`](../src/title_menu.asm#L141) [`$0998`](reference/modules/title_menu.md#title_set_joy2_right_handed) | 10 / 2 |
| `$0E` | [`msg_blank36`](../src/messages.asm#L67) [`$44AA`](reference/modules/messages.md#msg_blank36) | 36 spaces | [`title_menu_check_message_timeout`](../src/title_menu.asm#L37) [`$08E0`](reference/modules/title_menu.md#title_menu_check_message_timeout) | 10 / 2 |
| `$13` | [`msg_blank1`](../src/messages.asm#L130) [`$45C2`](reference/modules/messages.md#msg_blank1) | 1 space | [`open_passage`](../src/passage_open.asm#L42) [`$3A8A`](reference/modules/passage_open.md#open_passage) (two cells) | passage |
| `$16` | [`msg_blank4`](../src/messages.asm#L141) [`$45C8`](reference/modules/messages.md#msg_blank4) | 4 spaces | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) (removes a barrier when a lantern is taken) | 8 and 9 / 11 or 25 |
| `$4F` | [`msg_option_players`](../src/messages.asm#L334) [`$46A3`](reference/modules/messages.md#msg_option_players) | ` [F3]-[1 PLAYER -]2 PLAYERS` (key cap codes `$42`/`$56`) | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) | 6 / `$31` |
| `$50` | [`msg_option_opponent`](../src/messages.asm#L346) [`$46BF`](reference/modules/messages.md#msg_option_opponent) | ` PRESS [F5]-[COMPUTER -]OPPONENT` | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) | 7 / `$2B` |
| `$51` | [`msg_option_begin`](../src/messages.asm#L358) [`$46E0`](reference/modules/messages.md#msg_option_begin) | ` [F7]- TO BEGIN GAME` | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) | 8 / `$31` |
| `$56` | [`msg_blank2`](../src/messages.asm#L382) [`$472F`](reference/modules/messages.md#msg_blank2) | 2 spaces | [`draw_room16_bonus_taken`](../src/touch_effects.asm#L26) [`$2FEF`](reference/modules/touch_effects.md#draw_room16_bonus_taken) (the extra-fall pickup of room 16) | 10 and 11 / `$24` |
| `$57` | [`msg_room15_gap_top`](../src/messages.asm#L386) [`$4732`](reference/modules/messages.md#msg_room15_gap_top) | 1 space | [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) | 3 / 17 or 23 |

### 6.2 Graphic messages (room pieces)

| # | Name | Cell codes | What it draws | Printed by | Line / offset |
|---|---|---|---|---|---|
| `$06` | [`msg_room3_ledge_a`](../src/messages.asm#L61) [`$449E`](reference/modules/messages.md#msg_room3_ledge_a) | 7 x `$4B` | room 3 ledge, look A | [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3702`](reference/modules/room_frames_0_7.md#room03_frame) (swaps with `$60`) | 6 / 9 and 21 |
| `$07` | [`msg_room2_gap_bottom`](../src/messages.asm#L64) [`$44A6`](reference/modules/messages.md#msg_room2_gap_bottom) | `$11 $11 $11` | room 2 passage, lower piece | [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) | 12 / 37 |
| `$0F` | [`msg_trapdoor_open_4`](../src/messages.asm#L126) [`$45BC`](reference/modules/messages.md#msg_trapdoor_open_4) | `$22 $22 $03 $03 $03` | trapdoor, last step (open) | [`room01_frame`](../src/room_frames_0_7.asm#L42) [`$3679`](reference/modules/room_frames_0_7.md#room01_frame), [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3702`](reference/modules/room_frames_0_7.md#room03_frame) (message `$10` + [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a)) | 12 / 17 (room 1), 29 (room 3) |
| `$10` | [`msg_trapdoor_open_3`](../src/messages.asm#L122) [`$45B6`](reference/modules/messages.md#msg_trapdoor_open_3) | `$5C $5D $5E $03 $03` | trapdoor, step 3 | the same | the same |
| `$11` | [`msg_trapdoor_open_2`](../src/messages.asm#L119) [`$45B0`](reference/modules/messages.md#msg_trapdoor_open_2) | `$11 $22 $22 $03 $03` | trapdoor, step 2 | the same | the same |
| `$12` | [`msg_trapdoor_open_1`](../src/messages.asm#L116) [`$45AA`](reference/modules/messages.md#msg_trapdoor_open_1) | `$11 $5C $5D $5E $5F` | trapdoor, first step | the same | the same |
| `$14` | [`msg_wall_gap_base`](../src/messages.asm#L134) [`$45C4`](reference/modules/messages.md#msg_wall_gap_base) | `$3E` | bottom cell of an opened wall (rooms 0-9) | [`open_passage`](../src/passage_open.asm#L42) [`$3A8A`](reference/modules/passage_open.md#open_passage) (rooms 5, 8, 9) | passage |
| `$15` | [`msg_room5_gap_edge`](../src/messages.asm#L138) [`$45C6`](reference/modules/messages.md#msg_room5_gap_edge) | `$02` | room 5 wall edge | [`room05_frame`](../src/room_frames_0_7.asm#L378) [`$38AB`](reference/modules/room_frames_0_7.md#room05_frame) | 11 / 0 |
| `$17` | [`msg_wall_gap_floor`](../src/messages.asm#L145) [`$45CD`](reference/modules/messages.md#msg_wall_gap_floor) | `$11` | bottom cell in place of `$14` | [`open_passage_ledge`](../src/passage_open.asm#L54) [`$3AA0`](reference/modules/passage_open.md#open_passage_ledge) (rooms 6, 7) | passage |
| `$18` | [`msg_room9_opening`](../src/messages.asm#L149) [`$45CF`](reference/modules/messages.md#msg_room9_opening) | `$61 $04 $04 $63` | room 9 opening | [`room09_frame`](../src/room_frames_8_11.asm#L149) [`$3BB2`](reference/modules/room_frames_8_11.md#room09_frame) | 2 / 35 |
| `$19` | [`msg_room5_opening`](../src/messages.asm#L153) [`$45D4`](reference/modules/messages.md#msg_room5_opening) | `$61 $05 $63` | room 5 opening | [`room05_frame`](../src/room_frames_0_7.asm#L378) [`$38AB`](reference/modules/room_frames_0_7.md#room05_frame) | 2 / 34 |
| `$1A` | [`msg_room2_gap_top`](../src/messages.asm#L157) [`$45D8`](reference/modules/messages.md#msg_room2_gap_top) | `$00 $00 $05` | room 2 passage, upper piece | [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) | 11 / 37 |
| `$1B` | [`msg_runner_a`](../src/messages.asm#L160) [`$45DC`](reference/modules/messages.md#msg_runner_a) | `$64` | runner hazard | [`draw_runner_step`](../src/room_hazard_draw.asm#L9) [`$404E`](reference/modules/room_hazard_draw.md#draw_runner_step) (rooms 7, 9, 17; room 13 through [`update_floor_movers`](../src/game_setup.asm#L169) [`$104B`](reference/modules/game_setup.md#update_floor_movers)) | runner position |
| `$1C` | [`msg_runner_track_a`](../src/messages.asm#L163) [`$45DE`](reference/modules/messages.md#msg_runner_track_a) | `$65` | runner track | [`draw_runner_step`](../src/room_hazard_draw.asm#L9) [`$404E`](reference/modules/room_hazard_draw.md#draw_runner_step) | old runner column |
| `$1D` | [`msg_statue_mouth_a`](../src/messages.asm#L173) [`$45E4`](reference/modules/messages.md#msg_statue_mouth_a) | `$46` | statue mouth open | [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3642`](reference/modules/room_frames_0_7.md#room00_frame), [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) | 9 / 7 (room 0), 33 (room 2) |
| `$1E` | [`msg_statue_mouth_b`](../src/messages.asm#L176) [`$45E6`](reference/modules/messages.md#msg_statue_mouth_b) | `$47` | statue mouth closed | the same | the same |
| `$1F` | [`msg_slider_a_0`](../src/messages.asm#L180) [`$45E8`](reference/modules/messages.md#msg_slider_a_0) | `$56` | slider frame 0, look A | [`draw_slider0`](../src/room_hazard_draw.asm#L46) [`$4086`](reference/modules/room_hazard_draw.md#draw_slider0) / [`draw_slider1`](../src/room_hazard_draw.asm#L53) [`$4090`](reference/modules/room_hazard_draw.md#draw_slider1) / [`draw_slider2`](../src/room_hazard_draw.asm#L60) [`$409A`](reference/modules/room_hazard_draw.md#draw_slider2) (message `$1F` + frame; rooms 4, 5, 8, 17) | slider position |
| `$20` | [`msg_slider_a_1`](../src/messages.asm#L183) [`$45EA`](reference/modules/messages.md#msg_slider_a_1) | `$55` | slider frame 1, look A | the same | |
| `$21` | [`msg_slider_a_2`](../src/messages.asm#L186) [`$45EC`](reference/modules/messages.md#msg_slider_a_2) | `$55 $56` | slider frame 2, look A | the same | |
| `$22` | [`msg_slider_a_3`](../src/messages.asm#L189) [`$45EF`](reference/modules/messages.md#msg_slider_a_3) | `$54 $55` | slider frame 3, look A | the same | |
| `$23` | [`msg_slider_a_4`](../src/messages.asm#L192) [`$45F2`](reference/modules/messages.md#msg_slider_a_4) | `$00 $55` | slider frame 4, look A | the same | |
| `$24` | [`msg_slider_a_5`](../src/messages.asm#L195) [`$45F5`](reference/modules/messages.md#msg_slider_a_5) | `$00 $54` | slider frame 5, look A | the same | |
| `$25` | [`msg_slider_a_6`](../src/messages.asm#L198) [`$45F8`](reference/modules/messages.md#msg_slider_a_6) | `$00 $00` | slider gone | the same | |
| `$26` | [`msg_slider_b_0`](../src/messages.asm#L202) [`$45FB`](reference/modules/messages.md#msg_slider_b_0) | `$5A` | slider frame 0, look B | [`draw_slider0_alt`](../src/room_hazard_draw.asm#L68) [`$40A4`](reference/modules/room_hazard_draw.md#draw_slider0_alt) / [`draw_slider1_alt`](../src/room_hazard_draw.asm#L75) [`$40AC`](reference/modules/room_hazard_draw.md#draw_slider1_alt) / [`draw_slider2_alt`](../src/room_hazard_draw.asm#L82) [`$40B4`](reference/modules/room_hazard_draw.md#draw_slider2_alt) (frame + 7; rooms 4, 5, 7, 9) | slider position |
| `$27` | [`msg_slider_b_1`](../src/messages.asm#L205) [`$45FD`](reference/modules/messages.md#msg_slider_b_1) | `$59` | slider frame 1, look B | the same | |
| `$28` | [`msg_slider_b_2`](../src/messages.asm#L208) [`$45FF`](reference/modules/messages.md#msg_slider_b_2) | `$59 $5A` | slider frame 2, look B | the same | |
| `$29` | [`msg_slider_b_3`](../src/messages.asm#L211) [`$4602`](reference/modules/messages.md#msg_slider_b_3) | `$58 $59` | slider frame 3, look B | the same | |
| `$2A` | [`msg_slider_b_4`](../src/messages.asm#L214) [`$4605`](reference/modules/messages.md#msg_slider_b_4) | `$00 $59` | slider frame 4, look B | the same | |
| `$2B` | [`msg_slider_b_5`](../src/messages.asm#L217) [`$4608`](reference/modules/messages.md#msg_slider_b_5) | `$00 $58` | slider frame 5, look B | the same | |
| `$2C` | [`msg_slider_b_6`](../src/messages.asm#L220) [`$460B`](reference/modules/messages.md#msg_slider_b_6) | `$00 $00` | slider gone | the same | |
| `$2D` | [`msg_wall_gap_floor_alt`](../src/messages.asm#L224) [`$460E`](reference/modules/messages.md#msg_wall_gap_floor_alt) | `$11` | as `$17` | [`open_passage_ledge_b`](../src/passage_open.asm#L61) [`$3AAA`](reference/modules/passage_open.md#open_passage_ledge_b) (room 8; never ran in the coverage) | passage |
| `$2F` | [`msg_burst_small_top`](../src/messages.asm#L231) [`$4612`](reference/modules/messages.md#msg_burst_small_top) | `$71 $72 $73` | burst trap, small burst, top | [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps) (rooms 6, 7, 10, 11, 12, 14, 16, 17) | trap row / column |
| `$30` | [`msg_burst_small_bottom`](../src/messages.asm#L234) [`$4616`](reference/modules/messages.md#msg_burst_small_bottom) | `$74 $75 $76` | small burst, bottom | the same | trap row + 1 |
| `$31` | [`msg_burst_large_top`](../src/messages.asm#L237) [`$461A`](reference/modules/messages.md#msg_burst_large_top) | `$77 $78 $79` | large burst, top | the same | trap row |
| `$32` | [`msg_burst_large_bottom`](../src/messages.asm#L240) [`$461E`](reference/modules/messages.md#msg_burst_large_bottom) | `$7A $7B $7C` | large burst, bottom | the same | trap row + 1 |
| `$33` | [`msg_burst_trap_rearmed`](../src/messages.asm#L245) [`$4622`](reference/modules/messages.md#msg_burst_trap_rearmed) | `$7D $60 $7D` | the trap after the burst | the same | trap row + 1 |
| `$34` | [`msg_room4_lantern1_lit`](../src/messages.asm#L249) [`$4626`](reference/modules/messages.md#msg_room4_lantern1_lit) | `$13` | room 4 lantern 1, lit | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) (every 32 passes) | 4 / 11 |
| `$35` | [`msg_room4_lantern2_lit`](../src/messages.asm#L252) [`$4628`](reference/modules/messages.md#msg_room4_lantern2_lit) | `$14` | room 4 lantern 2, lit | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) | 4 / 28 |
| `$36` | [`msg_room4_lantern1_dark`](../src/messages.asm#L255) [`$462A`](reference/modules/messages.md#msg_room4_lantern1_dark) | `$66` | room 4 lantern 1, dark | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) | 4 / 11 |
| `$37` | [`msg_room4_lantern2_dark`](../src/messages.asm#L258) [`$462C`](reference/modules/messages.md#msg_room4_lantern2_dark) | `$67` | room 4 lantern 2, dark | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) | 4 / 28 |
| `$38` | [`msg_wizard_face_top_left`](../src/messages.asm#L277) [`$464B`](reference/modules/messages.md#msg_wizard_face_top_left) | `$00 $67-$6C $00` | wizard face, top, Bruce on the left | [`room18_frame_draw_gaze`](../src/wizard_room.asm#L72) [`$3D4E`](reference/modules/wizard_room.md#room18_frame_draw_gaze) (message `$38` + zone) | 2 / 16 |
| `$39` | [`msg_wizard_face_top_centre`](../src/messages.asm#L261) [`$462E`](reference/modules/messages.md#msg_wizard_face_top_centre) | `$07-$0E` | wizard face, top, Bruce in the middle | the same | 2 / 16 |
| `$3A` | [`msg_wizard_face_top_right`](../src/messages.asm#L293) [`$4668`](reference/modules/messages.md#msg_wizard_face_top_right) | `$00 $28 $0F $59 $79 $7A $7B $00` | wizard face, top, Bruce on the right | the same | 2 / 16 |
| `$3B` | [`msg_wizard_face_mid_left`](../src/messages.asm#L281) [`$4654`](reference/modules/messages.md#msg_wizard_face_mid_left) | `$10 $11 $70 $71` | wizard face, middle, left, look A | [`draw_wizard_face_top`](../src/wizard_room.asm#L98) [`$3D81`](reference/modules/wizard_room.md#draw_wizard_face_top) (message `$3B` + 0 or 6 + zone) | 3 / 18 |
| `$3C` | [`msg_wizard_face_mid_centre`](../src/messages.asm#L265) [`$4637`](reference/modules/messages.md#msg_wizard_face_mid_centre) | `$1D $1E $1F $20` | middle, centre, look A | the same | 3 / 18 |
| `$3D` | [`msg_wizard_face_mid_right`](../src/messages.asm#L297) [`$4671`](reference/modules/messages.md#msg_wizard_face_mid_right) | `$63 $53 $29 $2A` | middle, right, look A | the same | 3 / 18 |
| `$3E` | [`msg_wizard_face_low_left`](../src/messages.asm#L284) [`$4659`](reference/modules/messages.md#msg_wizard_face_low_left) | `$16 $1C $21 $77` | wizard face, lower, left, look A | [`draw_wizard_face_bottom`](../src/wizard_room.asm#L106) [`$3D8E`](reference/modules/wizard_room.md#draw_wizard_face_bottom) (message `$3E` + 0 or 6 + zone) | 4 / 18 |
| `$3F` | [`msg_wizard_face_low_centre`](../src/messages.asm#L268) [`$463C`](reference/modules/messages.md#msg_wizard_face_low_centre) | `$72 $78 $7C $34` | lower, centre, look A | the same | 4 / 18 |
| `$40` | [`msg_wizard_face_low_right`](../src/messages.asm#L300) [`$4676`](reference/modules/messages.md#msg_wizard_face_low_right) | `$72 $30 $31 $32` | lower, right, look A | the same | 4 / 18 |
| `$41` | [`msg_wizard_face_mid_left_b`](../src/messages.asm#L287) [`$465E`](reference/modules/messages.md#msg_wizard_face_mid_left_b) | `$6E $6F $70 $71` | middle, left, look B | [`draw_wizard_face_top`](../src/wizard_room.asm#L98) [`$3D81`](reference/modules/wizard_room.md#draw_wizard_face_top) | 3 / 18 |
| `$42` | [`msg_wizard_face_mid_centre_b`](../src/messages.asm#L271) [`$4641`](reference/modules/messages.md#msg_wizard_face_mid_centre_b) | `$1D $33 $3D $20` | middle, centre, look B | the same | 3 / 18 |
| `$43` | [`msg_wizard_face_mid_right_b`](../src/messages.asm#L303) [`$467B`](reference/modules/messages.md#msg_wizard_face_mid_right_b) | `$63 $53 $54 $60` | middle, right, look B | the same | 3 / 18 |
| `$44` | [`msg_wizard_face_low_left_b`](../src/messages.asm#L290) [`$4663`](reference/modules/messages.md#msg_wizard_face_low_left_b) | `$74 $75 $76 $77` | lower, left, look B | [`draw_wizard_face_bottom`](../src/wizard_room.asm#L106) [`$3D8E`](reference/modules/wizard_room.md#draw_wizard_face_bottom) | 4 / 18 |
| `$45` | [`msg_wizard_face_low_centre_b`](../src/messages.asm#L274) [`$4646`](reference/modules/messages.md#msg_wizard_face_low_centre_b) | `$72 $3E $4F $34` | lower, centre, look B | the same | 4 / 18 |
| `$46` | [`msg_wizard_face_low_right_b`](../src/messages.asm#L306) [`$4680`](reference/modules/messages.md#msg_wizard_face_low_right_b) | `$72 $65 $66 $15` | lower, right, look B | the same | 4 / 18 |
| `$47` | [`msg_wizard_flash_1a`](../src/messages.asm#L310) [`$4685`](reference/modules/messages.md#msg_wizard_flash_1a) | `$17 $18 $19` | defeat of the wizard, piece 1, frame A | [`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated) (message + [`room_state_d`](../src/room_dispatch.asm#L13) [`$4E9A`](reference/modules/room_dispatch.md#room_state_d)) | 3 / 12 |
| `$48` | [`msg_wizard_flash_1b`](../src/messages.asm#L313) [`$4689`](reference/modules/messages.md#msg_wizard_flash_1b) | `$1C $18 $7C` | piece 1, frame B | the same | 3 / 12 |
| `$49` | [`msg_wizard_flash_2a`](../src/messages.asm#L316) [`$468D`](reference/modules/messages.md#msg_wizard_flash_2a) | `$24 $25 $26` | piece 2, frame A | the same | 3 / 25 |
| `$4A` | [`msg_wizard_flash_2b`](../src/messages.asm#L319) [`$4691`](reference/modules/messages.md#msg_wizard_flash_2b) | `$10 $25 $21` | piece 2, frame B | the same | 3 / 25 |
| `$4B` | [`msg_wizard_flash_3a`](../src/messages.asm#L322) [`$4695`](reference/modules/messages.md#msg_wizard_flash_3a) | `$55 $56 $57` | piece 3, frame A | the same | 6 / 14 |
| `$4C` | [`msg_wizard_flash_3b`](../src/messages.asm#L325) [`$4699`](reference/modules/messages.md#msg_wizard_flash_3b) | `$1E $1F $78` | piece 3, frame B | the same | 6 / 14 |
| `$4D` | [`msg_wizard_flash_4a`](../src/messages.asm#L328) [`$469D`](reference/modules/messages.md#msg_wizard_flash_4a) | `$52 $62` | piece 4, frame A | the same | 6 / 23 |
| `$4E` | [`msg_wizard_flash_4b`](../src/messages.asm#L331) [`$46A0`](reference/modules/messages.md#msg_wizard_flash_4b) | `$11 $16` | piece 4, frame B | the same | 6 / 23 |
| `$54` | [`msg_runner_b`](../src/messages.asm#L166) [`$45E0`](reference/modules/messages.md#msg_runner_b) | `$66` | runner hazard, look B | [`draw_runner_step_alt`](../src/room_hazard_draw.asm#L21) [`$4063`](reference/modules/room_hazard_draw.md#draw_runner_step_alt) (room 13, rows 5 and 10) | runner position |
| `$55` | [`msg_runner_track_b`](../src/messages.asm#L169) [`$45E2`](reference/modules/messages.md#msg_runner_track_b) | `$67` | runner track, look B | [`draw_runner_step_alt`](../src/room_hazard_draw.asm#L21) [`$4063`](reference/modules/room_hazard_draw.md#draw_runner_step_alt) | old runner column |
| `$58` | [`msg_room15_gap_bottom`](../src/messages.asm#L390) [`$4734`](reference/modules/messages.md#msg_room15_gap_bottom) | `$2F` | room 15 passage, lower cell | [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) | 4 / 17 or 23 |
| `$59` | [`msg_room15_ladder_bottom`](../src/messages.asm#L393) [`$4736`](reference/modules/messages.md#msg_room15_ladder_bottom) | `$2F $2F $2F` | room 15 right edge | [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) | 9 / 37 |
| `$5A` | [`msg_room15_ladder_mid`](../src/messages.asm#L397) [`$473A`](reference/modules/messages.md#msg_room15_ladder_mid) | `$00 $00 $03` | room 15 right edge | [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) | 8 / 37 |
| `$5B` | [`msg_room15_ladder_top`](../src/messages.asm#L401) [`$473E`](reference/modules/messages.md#msg_room15_ladder_top) | `$00 $00 $03` | room 15 right edge | [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) | 7 / 37 |
| `$5C` | [`msg_room17_gap_a`](../src/messages.asm#L404) [`$4742`](reference/modules/messages.md#msg_room17_gap_a) | `$49 $49 $49` | room 17 floor opening | [`room17_frame`](../src/room_frames_12_17.asm#L188) [`$3F71`](reference/modules/room_frames_12_17.md#room17_frame) | 10 / 24 |
| `$5D` | [`msg_room17_gap_b`](../src/messages.asm#L407) [`$4746`](reference/modules/messages.md#msg_room17_gap_b) | `$44 $44` | room 17 floor opening | [`room17_frame`](../src/room_frames_12_17.asm#L188) [`$3F71`](reference/modules/room_frames_12_17.md#room17_frame) | 10 / 37 |
| `$5E` | [`msg_wizard_exit_top`](../src/messages.asm#L411) [`$4749`](reference/modules/messages.md#msg_wizard_exit_top) | `$00 $00 $03` | room 18 exit | [`room18_wizard_gone`](../src/wizard_room.asm#L115) [`$3D9B`](reference/modules/wizard_room.md#room18_wizard_gone) (never ran in the coverage) | 11 / 37 |
| `$5F` | [`msg_wizard_exit_bottom`](../src/messages.asm#L414) [`$474D`](reference/modules/messages.md#msg_wizard_exit_bottom) | `$5A $5A` | room 18 exit | [`room18_wizard_gone`](../src/wizard_room.asm#L115) [`$3D9B`](reference/modules/wizard_room.md#room18_wizard_gone) | 12 / 38 |
| `$60` | [`msg_room3_ledge_b`](../src/messages.asm#L421) [`$4766`](reference/modules/messages.md#msg_room3_ledge_b) | 7 x `$09` | room 3 ledge, look B | [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3702`](reference/modules/room_frames_0_7.md#room03_frame) | 6 / 9 and 21 |
| `$61` | [`msg_wizard_left_marker`](../src/messages.asm#L425) [`$476E`](reference/modules/messages.md#msg_wizard_left_marker) | `$06` | room 18 piece after the lantern is taken | [`room18_frame_wizard_alive`](../src/wizard_room.asm#L18) [`$3CE4`](reference/modules/wizard_room.md#room18_frame_wizard_alive) | 11 / 0 |
| `$63` | [`msg_passage_dark_cell`](../src/messages.asm#L434) [`$4782`](reference/modules/messages.md#msg_passage_dark_cell) | `$07` | passage cell, rooms 10-17 | [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark) (rooms 10, 12, 14, 16; two cells) | passage |
| `$64` | [`msg_passage_dark_base`](../src/messages.asm#L438) [`$4784`](reference/modules/messages.md#msg_passage_dark_base) | `$0E` | passage bottom cell, rooms 10-17 | [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark) | passage + 2 |

The passage helpers take the top line in A and the column in Y; [`draw_passage_cell`](../src/passage_open.asm#L80) [`$3ACA`](reference/modules/passage_open.md#draw_passage_cell) prints each cell and
moves [`passage_row`](../src/constants.asm#L67) [`$006C`](reference/variables.md#passage_row) one line down (**Code**). The room handlers are described on the room pages.

### 6.3 Unused messages

These entries of [`message_ptrs`](../src/messages.asm#L11) [`$43BE`](reference/modules/messages.md#message_ptrs) have no caller: no code loads their number before [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message)
(**Code**; **Observed**: the coverage of the title, demo and play runs has no print of them).

| # | Name | Text |
|---|---|---|
| `$2E` | [`msg_unused_j`](../src/messages.asm#L227) [`$4610`](reference/modules/messages.md#msg_unused_j) | `J` |
| `$52` | [`msg_unused_player_1`](../src/messages.asm#L366) [`$46F5`](reference/modules/messages.md#msg_unused_player_1) | `PLAYER 1` |
| `$53` | [`msg_unused_player_2`](../src/messages.asm#L370) [`$46FE`](reference/modules/messages.md#msg_unused_player_2) | `PLAYER 2` |
| `$62` | [`msg_presents`](../src/messages.asm#L429) [`$4770`](reference/modules/messages.md#msg_presents) | `DIABOLO  PRESENTS` (two spaces) |

### 6.4 Texts without a pointer

The message area also holds texts in message format that no pointer and no code reaches (**Code**):

| Name | Text |
|---|---|
| [`msg_unused_bruce_lee`](../src/messages.asm#L92) [`$4563`](reference/modules/messages.md#msg_unused_bruce_lee) | `BRUCE LEE` |
| [`msg_unused_by`](../src/messages.asm#L95) [`$456D`](reference/modules/messages.md#msg_unused_by) | `BY` |
| [`msg_unused_author`](../src/messages.asm#L97) [`$4570`](reference/modules/messages.md#msg_unused_author) | `RON J FORTIER` |
| [`msg_unused_game_over`](../src/messages.asm#L109) [`$4598`](reference/modules/messages.md#msg_unused_game_over) | `GAME OVER` |
| [`msg_unused_player`](../src/messages.asm#L112) [`$45A2`](reference/modules/messages.md#msg_unused_player) | `PLAYER ` |

**Conclusion.** With messages `$52`, `$53` and `$62` they are the texts of the title, PLAYER n and GAME OVER
screens in the message format. This version draws those screens with the big glyphs of [`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars)
instead (section 5).

[`version_banner`](../src/messages.asm#L375) [`$4707`](reference/modules/messages.md#version_banner) is used: it is 40 screen codes (not message format), which [`toggle_credit_line`](../src/status_and_keys.asm#L94) [`$1B68`](reference/modules/status_and_keys.md#toggle_credit_line)
copies to row 0.

### 6.5 "DIABOLO PRESENTS" over "DATASOFT PRESENTS"

Message `$62`, [`msg_presents`](../src/messages.asm#L429) [`$4770`](reference/modules/messages.md#msg_presents), reads `DIABOLO  PRESENTS`. The actor workspace still holds an older copy of
the end of the message area. [`contact_col0`](../src/actor_workspace.asm#L18) [`$4EED`](reference/modules/actor_workspace.md#contact_col0) .. [`contact_count_c10`](../src/actor_workspace.asm#L57) [`$4F3D`](reference/modules/actor_workspace.md#contact_count_c10) (81 bytes) equal the bytes
`$4731-$4781` (from the second byte of [`msg_blank2`](../src/messages.asm#L382) [`$472F`](reference/modules/messages.md#msg_blank2) to the end of [`msg_presents`](../src/messages.asm#L429) [`$4770`](reference/modules/messages.md#msg_presents)), except the text of
message `$62` (**Code**: the image bytes):

| Bytes | Message `$62` now ([`msg_presents`](../src/messages.asm#L429) [`$4770`](reference/modules/messages.md#msg_presents)) | The copy ([`contact_col2+17`](../src/actor_workspace.asm#L26) [`$4F2C`](reference/modules/actor_workspace.md#contact_col2)) |
|---|---|---|
| 0-5 | `44 49 41 42 4F 4C` `DIABOL` | `44 41 54 41 53 4F` `DATASO` |
| 6-11 | `4F 20 20 50 52 45` `O  PRE` | `00 00 00 00 00 00` |
| 12-16 | `53 45 4E 54 53` `SENTS` | `53 45 4E 54 53` `SENTS` |
| 17 | `A0` end | `A0` end |

**Conclusion.** The original text of message `$62` was `DATASOFT PRESENTS` (17 characters; the six zero bytes
held `FT PRE`). This release changed it to `DIABOLO  PRESENTS`, with two spaces to keep the length. The change has
no visible effect: no code prints message `$62`, and the title shows `DATASOFT PRESENTS` from
[`title_logo_row2`](../src/banners.asm#L20) [`$4A0D`](reference/modules/banners.md#title_logo_row2) in logo letters (**Observed**: the title screenshot). [`init_game_variables`](../src/game_setup.asm#L18) [`$0F72`](reference/modules/game_setup.md#init_game_variables)
clears the copy at the first game start, so it is image residue only.

## 7. Still open

- The meaning of the room pieces is named after their place and use. A screen capture before and after each
  opening (rooms 2, 3, 5, 9, 15, 17) would show what each piece looks like.
- [`msg_unused_j`](../src/messages.asm#L227) [`$4610`](reference/modules/messages.md#msg_unused_j) (`J`): its purpose is unknown.
- [`room18_wizard_gone`](../src/wizard_room.asm#L115) [`$3D9B`](reference/modules/wizard_room.md#room18_wizard_gone) and [`open_passage_ledge_b`](../src/passage_open.asm#L61) [`$3AAA`](reference/modules/passage_open.md#open_passage_ledge_b) never ran in the coverage. A run that defeats the
  wizard can show messages `$5E` and `$5F`.
- A two-player game over run can confirm that the [`game_over_digit_loop`](../src/lose_fall_game_over.asm#L144) [`$1909`](reference/modules/lose_fall_game_over.md#game_over_digit_loop) bug has no visible effect.
