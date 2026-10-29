# Bruce Lee: graphics

Everything that the player sees comes from one 16 KB VIC bank. The program draws the rooms with tiles that are two characters high. The tiles come from four room charsets that the program expands at the start. Raster interrupts give each room up to three bands of background colours. They also put the status line in its own font above the room. Bruce, Yamo and the Ninja are software sprites. Each pass, the program draws their 1-bit frame images into a hidden set of sprite blocks, and the next interrupt below the screen shows them. Thus a new pose never shows half drawn. The texts and the message printer are on the page [text_messages.md](text_messages.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one video frame: one run of `irq_game_bottom` in a game. A *pass* is one run of the main loop. A pass lasts 3 frames.
- A *tile* is one cell of a room map: two characters on top of each other (8 x 16 pixels).
- A *text line* is one entry of the row tables `text_line_top_lo` / `text_line_bottom_lo`. Text line n (n >= 2) is screen rows 2n-1 and 2n.
- An *actor* is Bruce (actor 0), Yamo (actor 1) or the Ninja (actor 2).
- A *frame image* is one 1-bit picture of the frame tables, number 0-209. In the sprite sections of this page, "frame 2" means frame image 2.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  CS["Start: copy the text font, expand the 4 room charsets (cold_start)"] --> MASK["Contact masks of the frame images (build_contact_masks)"]
  RPS["New game: VIC bank 2, game screen, multicolour (reset_play_state)"] --> DR["Draw the room: tiles, colour RAM, charset (draw_room)"]
  DR --> ML["Each pass: draw the actors into the hidden sprite buffer (build_actor_sprites)"]
  ML -.-> BOT["Line $FD: status line font, show the new sprites (irq_game_bottom)"]
  BOT --> PF["Line $40: room charset, colour band 0 (irq_game_playfield)"]
  PF --> SPL["Split lines: next colour band (irq_game_colour_split)"]
  SPL --> BOT
~~~

1. **The start builds the graphics one time.** [`cold_start` `$0400`](../src/game/cold_start.asm#L22) copies the text font from the character ROM and expands the four room charsets to double height. Then it puts the contact masks of the frame images where the sources were (**Code**).
2. **A new game prepares the VIC.** [`reset_play_state` `$0763`](../src/game/play_init.asm#L19) selects VIC bank 2 and the game screen [`game_screen` `$8C00`](../src/constants.asm#L195). It sets multicolour characters and X-expanded sprites (**Code**).
3. **Each room selects its tiles, colours and charset.** [`draw_room` `$09BC`](../src/room/draw_room.asm#L28) decodes the room map into screen RAM and colour RAM. It puts the charset of the room into `room_vmcsb` (**Code**).
4. **The sprites are drawn in one place and shown in another.** Each pass, `build_actor_sprites` draws the actors into the hidden sprite buffer. Each frame, the raster interrupt shows that buffer. It also changes the charset and the background colours at fixed raster lines (**Code**).

### One VIC bank for every screen

The program never moves the screen. The title, the PLAYER n screen, the game and the game over screen all use the same screen RAM at `$8C00`. This is in VIC bank 2 (`$8000-$BFFF`). [`reset_play_state` `$0763`](../src/game/play_init.asm#L19) selects the bank with `CI2PRA` = `$01` (**Code**).

The charset changes between the screens and between the parts of one screen. The raster interrupts change it with `$D018`. **Observed** in the room 0 snapshot: screen `$8C00`, charset `$8800` at raster line 55 and charset `$A000` at raster line 150.

| Screen | Part | `$D018` | Charset | `$D016` | Written by |
|---|---|---|---|---|---|
| Title | rows 0-9 (from raster `$FD` of the frame before) | `$30` | `$8000` (`title_logo_chars`) | `$18`: multicolour, 40 columns | `irq_title_frame` |
| Title | from raster `$82` (row 10 on) | `$32` | `text_font` | `$16`: multicolour, 38 columns, X scroll 6 | `irq_title_split` |
| PLAYER n | whole screen | `$30` | `$8000` | `$18` | `show_player_screen`, `irq_player_screen` |
| Game | rows 0-1 (status line) | `$32` | `text_font` | `$18` | `irq_game_bottom` |
| Game | from raster `$40` (row 2 on) | `room_vmcsb` | room charset (table below) | `$18` | `irq_game_playfield` |
| Game over | as the title | `$30` / `$32` | `$8000` / `$8800` | `$18` / `$16` | `game_over` installs `irq_title_frame` |

In a game, `reset_play_state` writes `$D016` = `$18` one time. The game interrupts never change it (**Code**). [`show_title_screen` `$0584`](../src/game/title_demo_start.asm#L83) and [`game_over` `$188E`](../src/game/lose_fall_game_over.asm#L80) first write `$D016` = `$08`. The title interrupts overwrite it in the next frame (**Code**).

The room part of the game screen gets its charset from [`room_vmcsb` `$F2`](../src/constants.asm#L117). Most rooms use one of two charsets. The wizard room has two charsets of its own:

| `room_vmcsb` | Charset | Rooms | Set by |
|---|---|---|---|
| `$38` | `charset_rooms_0_9` | 0-9 | `draw_room`, `reset_play_state` |
| `$3A` | `charset_rooms_10_19` | 10-17, 19 | `draw_room` |
| `$3C` | `charset_wizard` | 18 | `draw_room`, and `room18_wizard_defeated` (random flashes back) |
| `$3E` | `charset_wizard_flash` | 18, after the defeat of the wizard | `room18_wizard_defeated` |

Code that reads the pixels of a tile needs the address of the charset, not the `$D018` value. [`frame_update` `$15A8`](../src/game/frame_update.asm#L20) turns `room_vmcsb` into the high byte of the charset, `room_charset_hi` (`$A0`, `$A8`, `$B0`, `$B8`). The contact test and the animated characters use it (**Code**).

### Tiles two characters high

A room is 11 rows of 40 tiles, and each tile is 8 x 16 pixels. The C64 has no characters of that height. Thus the program keeps a tile as two characters. Character c is the upper half and character c + `$80` is the lower half. A map byte or a message byte gives c. The code writes c to the upper screen row and c OR `$80` to the lower screen row (**Code**: [`draw_room` `$0AEA`](../src/room/draw_room.asm#L189), [`print_message` `$17E2`](../src/actor/actor_driver_text.asm#L59)).

The room charset sources hold 128 characters of 8 x 8 multicolour pixels. [`build_double_height_font` `$4892`](../src/room/draw_helpers.asm#L51) writes each source row two times. Thus a tile has the shape of its source character at two times the height. Its pixels are 2 x 2 screen pixels, because multicolour pixels are 2 pixels wide.

| Source character n | Output |
|---|---|
| rows 0-3 | character n, rows 0-7 (row r of the source goes to rows 2r and 2r+1) |
| rows 4-7 | character n + `$80`, rows 0-7 (row r goes to rows 2(r-4) and 2(r-4)+1) |

```
for n in 0..127:                      ; column_counter = $7F .. 0
    for r in 0..3: top[8n+2r] = top[8n+2r+1] = src[8n+r]
    for r in 4..7: bot[8n+2(r-4)] = bot[8n+2(r-4)+1] = src[8n+r]
; top = output base, bot = output base + $400
```

**Worked example.** Tile 6 of [`room_charset_a` `$9000`](../src/graphics/room_charset_a.asm#L12) (bytes at `$9030`) is 8 x `$FF`. Character 6 of `charset_rooms_0_9` (at `$A030`) gets 8 x `$FF`. Character `$86` (at `$A430`) also gets 8 x `$FF`. Every pixel is code `%11`, the colour of the colour RAM. `reset_play_state` fills screen row 2 with character 6 and the colour RAM with `$F8`. This is the black separator line under the status line (**Code**).

### Characters that move

Some rooms have moving scenery: rooms 4, 5, 6, 8, 9 and 11. [`animate_scrolling_chars` `$2C70`](../src/room/animated_chars.asm#L12) writes characters `$61-$63` again, and their lower halves `$E1-$E3`. It writes them in `charset_rooms_0_9` or `charset_rooms_10_19`. The data comes from the 8-byte patterns `anim_char_patterns_low_rooms` / `anim_char_patterns_high_rooms`, rotated by `anim_chars_phase`. It writes each pattern row two times, as the expansion does. Thus the rows of the tile move up or down (**Code**).

At each new game, `reset_play_state` also writes code `$20` of the text font to a solid block again (**Code**).

### The colours of a room

The game screen uses multicolour characters (`$D016` = `$18`). In a character with colour RAM bit 3 set, the pixel pairs give these colours:

- `%00` = `BGCOL0`
- `%01` = `BGCOL1`
- `%10` = `BGCOL2`
- `%11` = colour RAM bits 0-2

In a character with colour RAM bit 3 clear (the status line), the character is hires in the colour of bits 0-2. Thus a room has three background colours for the full width of a raster line. It has one colour for each cell for the `%11` pixels.

| Source of the colour | Value | Set by |
|---|---|---|
| Colour RAM rows 0-1 | `$00` (hires, black) | `reset_play_state` |
| Colour RAM row 2 | `$F8` (multicolour, black) | `reset_play_state` (`fill_colour_ram`) |
| Colour RAM rows 3-24 | `room_colour_fill` [room] | `draw_room`, before the map |
| Black cells | `$F8` | `map_tile_set_black`, for a map byte with bit 7 set |
| `BGCOL0-2` of each band | `room_palette_ptr` [room] | the game raster interrupts |
| `EXTCOL` | `$F0` black (`vic_start_colours`) | `reset_play_state` |
| `BGCOL0` of the status line | `$FC` grey | `irq_game_bottom` |

**Black cells.** A map byte with bit 7 set draws tile (byte AND `$7F`). It also writes `$F8` to the two colour RAM cells of the tile ([`map_tile_set_black` `$0B5F`](../src/room/draw_room_0b51.asm#L21)). Thus the `%11` pixels of that tile are black, also in a room whose `%11` colour is not black. The same tile code can be coloured or black. The contact test of the actors tells these two cases apart: colour RAM colour 0 or not. Thus black and coloured `%11` pixels act differently for the actors (**Code**, see the comment of [`contact_col0` `$4EED`](../src/constants.asm#L153)).

**Colour bands.** The game interrupts change `BGCOL0-2` at up to three raster lines of the room area. Thus room 0 has a sky, mountains and ground in different colours. [`irq_game_bottom` `$48C1`](../src/irq/game_irq.asm#L12) copies the palette and the split lines of the room each frame. `irq_game_playfield` sets band 0 at line `$40`. `irq_game_colour_split` sets each next band at its split line (**Code**). The chain is in [The raster interrupt chain](#the-raster-interrupt-chain). The palettes are in [The room colours](#the-room-colours).

**Dead data.** `draw_room` also copies 20 bytes from [`room_aux_ptr` `$4AA8`](../src/room/room_tables.asm#L26) [room] to [`room_band_colours` `$0153`](../src/constants.asm#L146). `irq_game_bottom` overwrites the first 12 bytes every frame, and no code reads the last 8. Thus the copy has no effect (**Code**). **Observed** by the analysis runs: the write at [`irq_game_bottom` `$4906`](../src/irq/game_irq.asm#L44) occurs every frame.

**The screen saver.** After 32768 frames without input, `idle_timer` reaches `$80`. Then `frame_update` pauses the game and calls [`start_screen_saver` `$102B`](../src/game/game_setup.asm#L137). This routine saves `room_band_colours` in `palette_backup`. Then every frame `room_band_colours` = (`palette_backup` EOR `frame_count_256`) AND `$F7`, so the band colours cycle. `stop_screen_saver` restores them (**Code**).

**The wizard flash.** When Bruce defeats the wizard, [`room18_wizard_defeated` `$3DAF`](../src/room/wizard_room.asm#L134) writes random colours `$F8-$FF` to the colour RAM of the wizard area. It also changes `room_vmcsb` between `$3E` and `$3C`. Thus the wizard flickers between two charsets (**Code**). See [The charsets](#the-charsets).

### The software sprites

Bruce and Yamo each have two sprites on top of each other. The main sprite has the colour of the skin: yellow for Bruce, green for Yamo. The overlay sprite is black, for the hair and the clothes. The Ninja is black and has one sprite. Thus the actors use five hardware sprites, 0-4.

The program does not keep a sprite block for each picture. It copies each frame image from a compact 1-bit format into a sprite block (see [The sprite frame format](#the-sprite-frame-format)). If the VIC shows a sprite block while the CPU writes it, the VIC can show half a picture. Thus there are two sets of five blocks, buffer A and buffer B.

[`build_actor_sprites` `$2584`](../src/actor/actor_sprites.asm#L12) draws into the buffer that the VIC does not show. [`show_actor_sprites` `$25E2`](../src/actor/actor_sprites.asm#L75) points the sprites to that buffer at raster line `$FD`, below the visible screen (**Code**). The hand-shake is in [The double buffer](#the-double-buffer).

When `show_actor_sprites` shows the sprites, it also sets their positions (**Code**):

- X = 2 x `actor_x` (bit 8 in `MSIGX`), Y = `actor_y` + `$1D`. The two sprites of an actor have the same position.
- A wide main frame moves 8 units (16 pixels) left when the actor faces left (`actor_facing` <> 1).
- The overlay sprite moves 8 units left for the poses `$04`, `$3E`, `$42` and `$18` (`actor_pose_b` = `$05`, `$3F`, `$43`, `$19`).
- `actor_shown_x` keeps the X that is on the screen.

Two other parts of the program use sprite blocks of the buffers:

- **The fireballs in room 18.** Every pass, [`update_fireballs` `$4133`](../src/room/wizard_fireballs.asm#L13) writes 4 random rows into blocks `$0D` and `$0E`. These are byte 0 of rows 0-3, AND `fireball_shape_mask`. Thus the two fireballs sparkle. They are sprites 6 and 7, with random colours. `clear_fireball_sprites` clears those rows (**Code**).
- **The TM sign on the title.** `show_title_screen` clears `sprite_buf_b_spr4` and copies the 12 bytes of [`title_tm_sprite_rows` `$0E40`](../src/game/title_sprite.asm#L22) to rows 4-7 of it. It shows the block as sprite 0: block `$0F`, X = `$10A` (266), Y = `$56` (86), X-expanded, light grey (**Code**). **Observed** on the title screenshot: a small TM after BRUCE LEE.

```
row  bytes       pixels of byte 0
 4   EA 00 00    XXX.X.X.
 5   4E 00 00    .X..XXX.
 6   4A 00 00    .X..X.X.
 7   4A 00 00    .X..X.X.
```

## The data

### VIC bank 2

The program puts in `$8000-$BFFF` only the data that the VIC must see. The one exception is at the start of the bank.

| Range | Name | VIC use | CPU use |
|---|---|---|---|
| `$8000-$817F` | `room_map_19` (end) | Characters `$00-$2F` of the charset at `$8000`, sprite blocks 0-5. No screen uses them. | The end of the map of room 19. |
| `$8180-$83FF` | `sprite_buf_a_spr0` .. `sprite_buf_b_spr4` | Sprite blocks `$06-$0F`: the two sprite buffers. Also characters `$30-$7F` of the charset at `$8000` (not used). | Work RAM. The sprite builder writes it. Not part of the image. The knowledge space `bank2` keeps the bytes that the image of the base release has here (an older room charset). |
| `$8400-$87FF` | `title_logo_chars` | Characters `$80-$FF` of the charset at `$8000` (`$D018` = `$30`): the logo, the big letters and the big digits. | No code reads or writes it. |
| `$8800-$8BFF` | `text_font` | The text font (`$D018` = `$32`): title menu, status line. | `cold_start` builds it. |
| `$8C00-$8FE7` | `game_screen` | Screen RAM, 40 x 25. | All screens. |
| `$8FE8-$8FF7` | `game_screen` (spare) | Not shown. | The map decoder writes 2 bytes here for rooms 4, 7, 10, 13, 17 and 18. |
| `$8FF8-$8FFF` | `sprite_pointers` | Sprite pointers 0-7. | `show_actor_sprites`, `spawn_actor`, the fireballs, the title. |
| `$9000-$9FFF` | `room_charset_a` .. `room_charset_d` | The VIC sees the character ROM here. No `$D018` value of the program selects it. | The four room charset sources. After the start, the contact masks of the frame images in `$9000-$9FBF`. |
| `$A000-$A7FF` | `charset_rooms_0_9` | Room charset, `$D018` = `$38`. | Built at the start. Chars `$61-$63` move. |
| `$A800-$AFFF` | `charset_rooms_10_19` | Room charset, `$D018` = `$3A`. | Built at the start. Chars `$61-$63` move. |
| `$B000-$B7FF` | `charset_wizard` | Room 18 charset, `$D018` = `$3C`. | Built at the start. |
| `$B800-$BFFF` | `charset_wizard_flash` | Room 18 after the defeat of the wizard, `$D018` = `$3E`. | Built at the start. |

**Conclusion.** The end of the room 19 map at `$8000-$817F` is safe in the VIC bank, because the VIC never reads it. No screen uses characters `$00-$7F` of the charset at `$8000`. No sprite pointer is `$00-$05`.

### The game screen

| Screen rows | Text lines | Content | Charset |
|---|---|---|---|
| 0 | 0 | 40 x character `$20` (a solid block, colour RAM black): a black bar. The V key shows the version line here. Room 19 prints its message here. | `text_font` |
| 1 | 0 (offset 40-79) and 1 | The status line: `1UP 000000 TOP 000000 FALLS 04`. | `text_font` |
| 2 | — | 40 x character 6: a separator line. | room charset |
| 3-24 | 2-12 | The room: 11 rows of 40 tiles. | room charset |

![The game screen at the start of a game (room 0)](images/screens/game_start.png)

The game screen at the start of a game: the black row 0, the status line on a grey background, the room from row 3.

### The charsets

The bank holds six charsets. Four come from the room charset sources at `$9000-$9FFF`. [`cold_start` `$0400`](../src/game/cold_start.asm#L22) expands them with four calls of `build_double_height_font`. Then [`build_contact_masks` `$512F`](../src/actor/frame_builder.asm#L16) writes the contact masks of the frame images over `$9000-$9FBF`. Thus after the start, only the expanded copies exist (**Code**). [`warm_start_flag` `$03FF`](../src/game/cold_start.asm#L7) can skip the first three expansions, but it is always 0 (**Code**).

| Source | Range | Expanded to | `$D018` | Used by |
|---|---|---|---|---|
| `room_charset_a` | `$9000-$93FF` | `charset_rooms_0_9` (top `$A000-$A3FF`, bottom `$A400-$A7FF`) | `$38` | rooms 0-9 |
| `room_charset_b` | `$9400-$97FF` | `charset_rooms_10_19` | `$3A` | rooms 10-17 and 19 |
| `room_charset_c` | `$9800-$9BFF` | `charset_wizard` | `$3C` | room 18 |
| `room_charset_d` | `$9C00-$9FFF` | `charset_wizard_flash` | `$3E` | room 18 during and after the defeat of the wizard |
| character ROM `$D000-$D1FF` | 64 characters | `text_font` (with inverted copies) | `$32` | title menu, status line |
| — (in the image) | `$8400-$87FF` | `title_logo_chars`, not changed | `$30` | title logo, big letters, big digits |

**The fourth charset is the wizard flash.** A full 2 KB charset serves one effect. [`room_charset_d` `$9C00`](../src/graphics/room_charset_d.asm#L8) becomes `charset_wizard_flash`, and only [`room18_wizard_defeated` `$3DAF`](../src/room/wizard_room.asm#L134) selects it. On each pass of the defeat sequence, it sets `room_vmcsb` = `$3E`. While more than 16 passes remain, it sets `$3C` (`charset_wizard`) again at random. Thus the wizard flickers between the two charsets. It sets `$3E` on every pass, so room 18 keeps the flash charset after the sequence. Many tiles of the flash charset are equal to those of `room_charset_c`, but the wizard tiles have other pixel codes (**Code**).

**One byte is different in the releases.** `$9B00` is the top row of character `$60` of [`room_charset_c` `$9800`](../src/graphics/room_charset_c.asm#L6). It is `$0F` in TBC and DC and `$55` in SAEGER. The expansion copies it into two rows of character `$60` of `charset_wizard`. **Observed**: a watchpoint on `$9B00` stops in `build_double_height_font` at the cold start. `$55` is a value of the KERNAL RAM test. Thus the default build uses `$0F` (switch `FIX_RAM_TEST_BYTE`, [releases.md](releases.md)).

The images below come from the reference. The reference shows each source in hires and in multicolour. It uses pattern colours, not the colours of a room.

![room_charset_a in multicolour](reference/images/room_charset_a-multicolour.png)

`room_charset_a` in multicolour: the tiles of rooms 0-9 (128 characters, 16 per row).

![room_charset_a in hires](reference/images/room_charset_a-hires.png)

`room_charset_a` in hires: the same bytes as single pixels.

![room_charset_b in multicolour](reference/images/room_charset_b-multicolour.png)

`room_charset_b` in multicolour: the tiles of rooms 10-17 and 19.

![room_charset_b in hires](reference/images/room_charset_b-hires.png)

`room_charset_b` in hires.

![room_charset_c in multicolour](reference/images/room_charset_c-multicolour.png)

`room_charset_c` in multicolour: the tiles of room 18, the wizard room.

![room_charset_c in hires](reference/images/room_charset_c-hires.png)

`room_charset_c` in hires.

![Room 18 with the wizard](images/rooms/room18.png)

Room 18 with `charset_wizard`: tiles of `room_charset_c` make the wizard at the top.

![room_charset_d in multicolour](reference/images/room_charset_d-multicolour.png)

`room_charset_d` in multicolour: the wizard flash charset.

![room_charset_d in hires](reference/images/room_charset_d-hires.png)

`room_charset_d` in hires.

![title_logo_chars in multicolour](reference/images/title_logo_chars-multicolour.png)

[`title_logo_chars` `$8400`](../src/graphics/title_logo_charset.asm#L9) in multicolour: characters `$80-$FF` of the charset at `$8000`.

![title_logo_chars in hires](reference/images/title_logo_chars-hires.png)

`title_logo_chars` in hires: the big 2 x 2 letters and digits, the small logo letters and the BRUCE LEE logo.

### The text font

The status line and the title menu use the letters of the C64 character ROM. `cold_start` sets `$01` = `$32` to make the character ROM visible. Then it copies 512 bytes. The order puts the digits and the capital letters first (**Code**):

| Codes | Address | Content |
|---|---|---|
| `$00-$1F` | `text_font` | ROM characters `$20-$3F`: space, punctuation, digits |
| `$20-$3F` | `text_font_letters` | ROM characters `$00-$1F`: @, A-Z, [ £ ] arrows |
| `$40-$5F` | `text_font_inverse` | inverted `$00-$1F` |
| `$60-$7F` | `text_font_inverse_letters` | inverted `$20-$3F` |

Thus the screen code of a digit or a capital letter is its ASCII code - `$20`. The program changes three characters (**Code**):

- Code `$20` (@) becomes a solid block.
- Code `$42` (`text_font_keycap_left`) becomes a 2-pixel bar at the right edge.
- Code `$56` (`text_font_keycap_right`) becomes a 2-pixel bar at the left edge.

The bars are the ends of the key caps F3, F5 and F7 of the title menu (**Code**). Codes `$80-$FF` of this charset are at `$8C00-$8FFF`, in the screen RAM. No text uses them, because the text in rows 0-1 and on the title is one row high (see [text_messages.md](text_messages.md)).

### The room colours

[`room_colour_fill` `$47A0`](../src/room/room_palettes_47a0.asm#L7) gives the colour RAM byte of each room (20 bytes, index = room). The `%11` colour is bits 0-2:

| Room | 0-3 | 4-6 | 7 | 8-9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Byte | `$FE` | `$FC` | `$FF` | `$FA` | `$F9` | `$FB` | `$F9` | `$FA` | `$F9` | `$FC` | `$F9` | `$FF` | `$FE` | `$FF` |
| `%11` colour | 6 | 4 | 7 | 2 | 1 | 3 | 1 | 2 | 1 | 4 | 1 | 7 | 6 | 7 |

[`room_split_list_ptr` `$4833`](../src/room/room_palettes_47a0.asm#L76) gives the split lines of each room, and [`room_palette_ptr` `$480B`](../src/room/room_palettes_47a0.asm#L69) gives the palette. A palette record is `BGCOL0`, `BGCOL1`, `BGCOL2`, with one record for each band. The table gives colour numbers:

| Rooms | Split lines | Band 0 | Band 1 | Band 2 |
|---|---|---|---|---|
| 0, 1, 2 | `$78`, `$97` | 11, 1, 14 | 11, 2, 1 | 12, 2, 1 |
| 3 | `$62`, `$97` | 11, 1, 14 | 11, 2, 1 | 12, 2, 1 |
| 4, 5, 6 | — | 6, 14, 1 | | |
| 7, 8, 9 | — | 8, 9, 1 | | |
| 10, 12, 14, 16 | `$56` | 6, 14, 11 | 12, 14, 11 | |
| 11 | — | 4, 14, 11 | | |
| 13 | — | 14, 6, 1 | | |
| 15 | `$B6`, `$C7` | 14, 6, 11 | 12, 14, 1 | 15, 8, 12 |
| 17 | — | 12, 8, 11 | | |
| 18 | — | 0, 14, 4 | | |
| 19 | — | 6, 2, 1 | | |

**Observed.** At raster line 150 of the room snapshots, the colours were:

- room 0: 11, 2, 1
- room 4: 6, 14, 1
- room 10: 12, 14, 11
- room 15: 14, 6, 11
- room 18: 0, 14, 4

In room 15 the colour writes occurred at lines 184/185 and 202. The split lines are `$B6` = 182 and `$C7` = 199, so the writes come 2-3 lines later (**Observed**).

![Room 0 with three colour bands](images/rooms/room00.png)

Room 0: the colour bands change the background from the sky (band 0) to the mountains and the ground.

![Room 15 with three colour bands](images/rooms/room15.png)

Room 15: band 0 (light blue sky) above line `$B6`, then a grey band, and the light grey wall below line `$C7`.

### The colours of the other screens

| Screen | `EXTCOL` / `BGCOL0` | `BGCOL1` / `BGCOL2` | Colour RAM |
|---|---|---|---|
| Title | `$F6` blue | `$FF` light grey | `$FF` (multicolour, yellow) rows 0-11, `$F1` (hires, white) rows 12-24 |
| PLAYER n | `$06` blue | `BGCOL1` changes every 2 lines from line `$6E`: `$FB`, `$FC`, `$FF`, `$F1`, `$FF`, `$FC`, `$FB` | not written |
| Game over | `$06` blue | `$0F` light grey | `$0F` rows 0-11, `$F1` rows 12-24 |

The big PLAYER n text uses pixel code `%01`. Thus [`irq_player_screen` `$14A4`](../src/irq/screen_raster_irqs.asm#L10) can shade it with a change of `BGCOL1` every 2 raster lines (**Code**). **Observed** on the PLAYER 1 screen: the letters go from dark grey to white and back.

![The PLAYER 1 screen](images/screens/player_screen.png)

The PLAYER 1 screen: the big letters of `title_logo_chars`, shaded by the raster bars on `BGCOL1`.

![The title screen](images/screens/title.png)

The title screen: the logo charset in rows 0-9 (multicolour), the text font from row 10 (hires, white), and the TM sprite.

### The sprites of each actor

[`actor_main_sprite` `$276D`](../src/actor/actor_sprites.asm#L319) = 0, 2, 4 and `actor_overlay_sprite` = 1, 3, `$FF` give the hardware sprites of actors 0, 1, 2. Each sprite also has a collision code. The fight code uses it to find who hit whom (**Code**):

| Hardware sprite | Use | Colour | Collision code |
|---|---|---|---|
| 0 | Bruce, main sprite (even frame) | `frame_colour` (yellow) | 4 |
| 1 | Bruce, overlay sprite (odd frame) | `frame_colour` (black) | 5 |
| 2 | Yamo, main sprite | `frame_colour` (green) | 6 |
| 3 | Yamo, overlay sprite | `frame_colour` (black) | 7 |
| 4 | the Ninja (one sprite) | `$F0` black | 3 |
| 5 | not used (`spawn_actor` writes its pointer as a side effect) | — | — |
| 6, 7 | room 18: the two fireballs | random | — |
| 0 | title: the TM sign | `$FF` light grey | — |

`actor_collision_code_first` / `actor_collision_code_second` give the collision codes for each actor type. [`collision_code_to_sprite` `$59AE`](../src/actor/actor_frame_tables.asm#L22) turns code 3-7 into sprite 4, 0, 1, 2, 3. `set_sprite_slot_owner` writes the actor into `sprite_owner` [sprite]. In a sprite-sprite collision, [`check_fight_collisions` `$29C3`](../src/actor/fight_hits.asm#L14) reads it to find the actor of a sprite (**Code**).

### The sprite blocks

| Block | Address | Name | Buffer A / B | Other use |
|---|---|---|---|---|
| `$06` | `$8180` | `sprite_buf_a_spr0` | A, sprite 0 | |
| `$07` | `$81C0` | `sprite_buf_a_spr1` | A, sprite 1 | |
| `$08` | `$8200` | `sprite_buf_a_spr2` | A, sprite 2 | |
| `$09` | `$8240` | `sprite_buf_a_spr3` | A, sprite 3 | |
| `$0A` | `$8280` | `sprite_buf_a_spr4` | A, sprite 4 | |
| `$0B` | `$82C0` | `sprite_buf_b_spr0` | B, sprite 0 | |
| `$0C` | `$8300` | `sprite_buf_b_spr1` | B, sprite 1 | |
| `$0D` | `$8340` | `sprite_buf_b_spr2` | B, sprite 2 | room 18: fireball 0, sprite 6 (`launch_fireball0`) |
| `$0E` | `$8380` | `sprite_buf_b_spr3` | B, sprite 3 | room 18: fireball 1, sprite 7 (`launch_fireball1`) |
| `$0F` | `$83C0` | `sprite_buf_b_spr4` | B, sprite 4 | title: TM sprite. `reset_play_state` points all eight sprites here. |

[`sprite_buffer_addresses` `$274F`](../src/actor/actor_sprites.asm#L309) holds the ten block addresses, and `sprite_buffer_pointers` holds the ten block numbers. Buffer A is first, and the index is sprite + 5 x buffer (**Code**).

**Conclusion.** The fireballs can share blocks `$0D` and `$0E` with buffer B of Yamo, because room 18 has no enemies ([`room_no_enemies` `$4C9E`](../src/room/room_tables.asm#L164) = `$FF`).

## The sprite frame format

### Where the frames are

The program draws the actors from 210 frame images, numbered 0-209. Five tables describe them, with the frame number as index (**Code**):

| Table | Address | Bytes | Meaning |
|---|---|---|---|
| `frame_gfx_lo` | `$59BD` | 210 | low byte of the graphics address |
| `frame_gfx_hi` | `$5A8F` | 210 | high byte of the graphics address (`$0000` = no image: the odd frames of the Ninja) |
| `frame_last_row` | `$5B61` | 210 | height code. Narrow frame: index of the last row (rows = value + 1). Wide frame: number of rows. |
| `frame_colour` | `$5C33` | 140 | sprite colour of frames 0-139 (`$F7` yellow, `$F5` green, `$F0` black) |
| `frame_is_wide` | `$5CBF` | 210 | 0 = 8 pixels wide (1 byte per row), nonzero (`$01` or `$55`) = 16 pixels (2 bytes per row) |

Each actor has a block of 70 frame numbers:

| Frames | Actor | Base (`actor_frame_base`) | Graphics |
|---|---|---|---|
| 0-69 | Bruce | 0 | `bruce_frame_56` .. (region `$636A-$67FC`) |
| 70-139 | Yamo | 70 | region `$5D91-$6282` (`yamo_frame_00` ...) |
| 140-209 | Ninja | 140 | `$6283-$6369` and `ninja_frame_00` .. `$68F8` |

The actor *type* is the index of [`actor_frame_base` `$59A5`](../src/actor/actor_frame_tables.asm#L8). The type is bits 7-6 of `actor_flags`: 0 Bruce, 1 Ninja, 2 Yamo. Thus the bytes of the table are 0, 140, 70. A pose is an even number. [`set_actor_pose` `$29A1`](../src/actor/actor_poses.asm#L324) sets `actor_frame_a` = base + pose for the main sprite. It sets `actor_frame_b` = base + pose + 1 for the overlay sprite (**Code**).

- Even frames are the main sprite of a pose, and odd frames are the overlay sprite (**Code**).
- The Ninja has one black sprite. [`setup_sprite_frame` `$2719`](../src/actor/actor_sprites.asm#L278) gives him `$F0` and does not read `frame_colour` (**Code**). This is why `frame_colour` has only 140 entries (**Conclusion**).
- The code never mirrors a frame. Each facing has its own frames, for example Bruce 0 and 2 (**Code**).
- Several frame numbers share graphics (**Code**: the address tables):
  - Bruce 42-55 use frames 0/1, and Bruce 68/69 use 32/33.
  - Yamo 112/113, 118-125 and 134-139 use 78/79.
  - Many Ninja frames use frame 140.
- The wide frames are (**Code**):
  - Bruce: 4-7, 25, 29, 59, 63, 65, 67.
  - Yamo: 74-77, 94, 95, 98, 99, 128, 132, 133.
  - Ninja: 190, 194, 196, 198, 200, 202.
- The image of the base release holds 42 more bytes in frame format at `$63C1-$63EA`. They are equal to frame 59, and no table entry points to them. This is the frame ADWONL22 with a misspelt source label. It is a development leftover and not part of the rebuilt game. The knowledge keeps it in space `bank1` (**Code**).

### The byte layout

A frame image has 1 bit for each pixel and one or two bytes for each row. It has no padding: the data holds only the rows that have pixels. The sprite builder spreads it over the 3-byte rows of a sprite block.

| Width | Source bytes | Sprite rows |
|---|---|---|
| narrow (`frame_is_wide` = 0) | byte r = row r, r = 0 .. `frame_last_row` | sprite byte 3r = byte r. Bytes 3r+1 and 3r+2 = 0. |
| wide (`frame_is_wide` <> 0) | bytes 2r (left) and 2r+1 (right) = row r, r = 0 .. `frame_last_row` - 1 | sprite byte 3r = byte 2r, 3r+1 = byte 2r+1, 3r+2 = 0 |

Each bit is one hires sprite pixel. All sprites are X-expanded (`XXPAND` = `$FF`, set by `reset_play_state`). Thus a narrow frame is 16 screen pixels wide and a wide frame is 32. The sprites are hires (`SPMC` = 0) and in front of the background (`SPBGPR` = 0). The rows after the frame, up to byte 63, are 0 (**Code**).

**Frame height for the contact masks.** [`expand_contact_mask` `$517E`](../src/actor/frame_builder.asm#L93) reads `frame_last_row` + 1 rows for the two widths. For a wide frame, that is one row more than the sprite builder draws (**Code**).

### The decoder

[`build_actor_sprites` `$2584`](../src/actor/actor_sprites.asm#L12) goes through the actors. `setup_sprite_frame` reads the five tables, and [`copy_sprite_frame` `$26A0`](../src/actor/actor_sprites.asm#L190) copies the rows:

```
for actor X in 2, 1, 0 with actor_flags[X] bit 0 set:
    dest = sprite_buffer_addresses[actor_main_sprite[X] + 5 * sprite_buffer_select]
    draw(actor_frame_a[X], dest)  -> actor_main_wide, actor_main_colour
    if X != 2 and actor_overlay_sprite[X] != $FF:
        dest = sprite_buffer_addresses[actor_overlay_sprite[X] + 5 * sprite_buffer_select]
        draw(actor_frame_a[X] + 1, dest) -> actor_overlay_wide, actor_overlay_colour
sprite_images_shown = 0

draw(f, dest):
    src = frame_gfx_hi[f] * 256 + frame_gfx_lo[f]      ; patched into three LDA abs,X operands
    h = frame_last_row[f]
    colour = (actor == 2) ? $F0 : frame_colour[f]
    if frame_is_wide[f] == 0:
        for r = h down to 0: dest[3r] = src[r]; dest[3r+1] = dest[3r+2] = 0
        clear dest[3h+3 .. 63]
    else:
        for r = h-1 down to 0: dest[3r] = src[2r]; dest[3r+1] = src[2r+1]; dest[3r+2] = 0
        clear dest[3h .. 63]
```

The copy loop uses self-modified code. `setup_sprite_frame` writes the source address into three operands: `copy_sprite_frame_narrow_src`, `copy_sprite_frame_wide_src_a` and `copy_sprite_frame_wide_src_b`. `sprite_copy_counter` counts the 64 bytes of the block (**Code**).

### Worked example: Bruce standing, frames 2 and 3

At the start of room 0, Bruce has pose 2: he stands and faces right. Thus [`actor_frame_a` `$4F4E`](../src/constants.asm#L171) = 2. **Observed** in the room 0 start snapshot: `actor_pose` = 2, `actor_facing` = 1. The table bytes are:

| Table | Frame 2 | Frame 3 |
|---|---|---|
| low byte | `frame_gfx_lo+2` = `$46` | `frame_gfx_lo+3` = `$67` |
| high byte | `frame_gfx_hi+2` = `$66` | `frame_gfx_hi+3` = `$66` |
| graphics | `bruce_frame_02` | `bruce_frame_03` |
| height | `frame_last_row+2` = `$0B`: 12 rows | `frame_last_row+3` = `$14`: 21 rows |
| colour | `frame_colour+2` = `$F7` yellow | `frame_colour+3` = `$F0` black |
| width | `frame_is_wide+2` = 0: narrow | `frame_is_wide+3` = 0: narrow |

The graphics bytes are:

- frame 2: `00 10 30 28 38 38 30 70 78 6C 4E 38`
- frame 3: `30 60 48 50 40 00 00 00 00 11 31 00 38 38 2C 24 24 24 24 66 E7`

Each row of the picture is one byte, with bit 7 at the left. Below, `Y` is a pixel of frame 2 (sprite 0, yellow). `#` is a pixel of frame 3 (sprite 1, black), and `.` is no pixel. Sprite 0 has priority over sprite 1, so `Y` shows where the two sprites have a pixel:

```
row  frame2  frame3  pixels (each = 2 screen pixels)
 0   $00     $30     ..##....
 1   $10     $60     .##Y....
 2   $30     $48     .#YY#...
 3   $28     $50     .#Y#Y...
 4   $38     $40     .#YYY...
 5   $38     $00     ..YYY...
 6   $30     $00     ..YY....
 7   $70     $00     .YYY....
 8   $78     $00     .YYYY...
 9   $6C     $11     .YY#YY.#
10   $4E     $31     .Y##YYY#
11   $38     $00     ..YYY...
12    -      $38     ..###...
13    -      $38     ..###...
14    -      $2C     ..#.##..
15    -      $24     ..#..#..
16    -      $24     ..#..#..
17    -      $24     ..#..#..
18    -      $24     ..#..#..
19    -      $66     .##..##.
20    -      $E7     ###..###
```

The picture shows black hair on top, the yellow face and arms, and the black trousers and feet. **Observed** in the same run, after `build_actor_sprites`:

- [`sprite_buf_a_spr0` `$8180`](../src/constants.asm#L179) held `00 00 00 10 00 00 30 00 00 28 ...`. These are the bytes of frame 2 at offsets 0, 3, 6, ...
- `sprite_buf_a_spr1` held the 21 bytes of frame 3 in the same layout.
- Sprites 0 and 1 were at X = 52, Y = 225. `actor_x` = `$1A`, and 52 = 2 x 26. `actor_y` = `$C4`, and 225 = 196 + 29.

## The state machines

### The raster interrupt chain

The game interrupts run as a chain. Each one sets the raster line and the vector of the next one. [`irq_entry` `$1103`](../src/irq/interrupt_entry.asm#L10) receives every interrupt and jumps through `irq_vector`. Thus the chain is a state machine of the value in `irq_vector`. [`init_game_irq` `$082D`](../src/game/play_init.asm#L114) starts it at line `$FB`.

~~~mermaid
stateDiagram-v2
  state "Bottom: status line, palette copy (line $FD)" as Bottom
  state "Playfield: room charset, band 0 (line $40)" as Play
  state "Colour split: next band (split line)" as Split
  [*] --> Bottom: init_game_irq (line $FB)
  Bottom --> Play
  Play --> Split: first split line is not $FD
  Play --> Bottom: first split line is $FD
  Split --> Split: next split line is not $FD
  Split --> Bottom: next split line is $FD
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| `irq_game_bottom` | always: `$D018` = `$32`, `BGCOL0` = `$FC`, copy 12 bytes of the room palette to `room_band_colours` and 4 split lines to `raster_split_lines`, call `frame_update` | `irq_game_playfield` at line `$40` | `irq_game_bottom` |
| `irq_game_playfield` | waits until line `$42`, `$D018` = `room_vmcsb`, `BGCOL0-2` = band 0 | split or bottom | `irq_arm_next_split` |
| `irq_arm_next_split` | `raster_split_lines` [`raster_split_index`] = `$FD` | `irq_game_bottom` at line `$FD` | `irq_chain_to_bottom` |
| `irq_arm_next_split` | that line is not `$FD` | `irq_game_colour_split` at that line | `irq_arm_next_split` |
| `irq_game_colour_split` | waits until line r+3 (or r+2 plus a delay), writes `BGCOL0-2` of the next band, `band_palette_offset` += 3 | `irq_arm_next_split` | `irq_split_set_colours` |

The three states are [`irq_game_bottom` `$48C1`](../src/irq/game_irq.asm#L12), [`irq_game_playfield` `$491E`](../src/irq/game_irq.asm#L62) and [`irq_game_colour_split` `$4982`](../src/irq/game_irq.asm#L117). The page [interrupts.md](interrupts.md) tells the full interrupt chain.

### The double buffer

[`sprite_buffer_select` `$277D`](../src/actor/actor_sprites.asm#L331) is the buffer that the next build fills (0 = A, 1 = B). [`sprite_images_shown` `$277E`](../src/actor/actor_sprites.asm#L333) is the hand-shake between the main loop and the interrupt. The value 0 means that a new set of images waits to be shown.

~~~mermaid
stateDiagram-v2
  state "Shown (sprite_images_shown = 1)" as Shown
  state "Ready (sprite_images_shown = 0)" as Ready
  [*] --> Shown
  Shown --> Ready: build_actor_sprites ends
  Ready --> Shown: show_actor_sprites (next frame)
  Shown --> Shown: show_actor_sprites returns at once
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Shown | `build_actor_sprites` drew all actors into buffer `sprite_buffer_select` | Ready | `build_actor_sprites` |
| Ready | `frame_update` calls `show_actor_sprites` (raster line `$FD`) | Shown: positions and colours written, pointers 0-4 = blocks of buffer `sprite_buffer_select`, then `sprite_buffer_select` EOR 1 | `show_actor_sprites_pointers` |
| Shown | `show_actor_sprites` | Shown (nothing changes) | `show_actor_sprites` |

1. The main loop builds the images one time in each pass (every 3 frames) into the hidden buffer ([`main_loop` `$1C2C`](../src/game/game_main_loop.asm#L80)). [`change_room` `$2F9A`](../src/actor/background_touch.asm#L234) also builds them after it draws a room.
2. The interrupt at line `$FD` shows them. The pointers change below the visible screen. Thus the new images start with the next frame (**Conclusion**: no tearing).
3. Then `sprite_buffer_select` flips. The next build writes the other buffer, which the VIC does not show now.

## Still open

- Why does [`irq_title_split` `$1574`](../src/irq/screen_raster_irqs.asm#L121) write `$D016` = `$16` (38 columns, X scroll 6) for the menu part of the title? **Observed**: at raster line 200 of the title, the VIC had X scroll 6 and charset `$8800`. A screen capture with a grid can show how far the menu text moves.
- Did the authors plan charset source D for more than the wizard flash? Only `room18_wizard_defeated` selects it.
