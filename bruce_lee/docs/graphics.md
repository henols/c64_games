# Bruce Lee: graphics

How the program uses the VIC-II: the memory of VIC bank 2, the charsets and the double-height tiles, the colours
and raster splits of the rooms, and the software sprites of the three actors.

**Scope.**

- The VIC bank 2 memory map at run time, and the `$D018` / `$D016` values of each screen.
- The double-height tile scheme and the four room charsets (source and expanded), the title logo charset and the
  text font.
- The colours: colour RAM, the room palettes, the raster colour bands, the black cells, the screen saver.
- The sprites: the 1-bit frame format, the frame tables, the sprite builder [`build_actor_sprites`](../src/actor_sprites.asm#L12) [`$2584`](reference/modules/actor_sprites.md#build_actor_sprites), the
  double buffer, the sprite of each actor, the fireballs and the title TM sprite.
- Sources: [cold_start.asm](../src/cold_start.asm), [play_init.asm](../src/play_init.asm),
  [draw_room.asm](../src/draw_room.asm), [draw_helpers.asm](../src/draw_helpers.asm),
  [game_irq.asm](../src/game_irq.asm), [screen_raster_irqs.asm](../src/screen_raster_irqs.asm),
  [room_palettes.asm](../src/room_palettes.asm), [actor_sprites.asm](../src/actor_sprites.asm),
  [actor_frame_tables.asm](../src/actor_frame_tables.asm), [actor_frame_gfx_tables.asm](../src/actor_frame_gfx_tables.asm),
  [title_demo_start.asm](../src/title_demo_start.asm), [animated_chars.asm](../src/animated_chars.asm).
  The texts and the message printer are on the page [text_messages.md](text_messages.md).

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one video frame (one run of [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) in a game). A *pass* is one run of
  [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop); a pass lasts 3 frames.
- A *tile* is one cell of a room map: two characters on top of each other (8 x 16 pixels). A *text line* is one
  entry of the row tables [`text_line_top_lo`](../src/fireball_text_score_vars.asm#L33) [`$4338`](reference/modules/fireball_text_score_vars.md#text_line_top_lo) / [`text_line_bottom_lo`](../src/fireball_text_score_vars.asm#L43) [`$4360`](reference/modules/fireball_text_score_vars.md#text_line_bottom_lo): text line n (n >= 2) is screen
  rows 2n-1 and 2n.
- An *actor* is Bruce (actor 0), Yamo (actor 1) or the Ninja (actor 2). A *frame image* (short: *frame*, when
  the context is the sprites) is one 1-bit picture of the frame tables, number 0-209.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an
  interpretation.

## 1. Overview

~~~mermaid
flowchart TB
  CS["cold_start $0400"] --> FONT["ROM font copy to text_font $8800"]
  CS --> EXP["build_double_height_font $4892 x4"]
  EXP --> CH["charsets $A000 $A800 $B000 $B800"]
  CS --> MASK["build_contact_masks $512F"]
  RPS["reset_play_state $0763"] --> VIC["VIC bank 2, D018 $38, D016 $18"]
  DR["draw_room $09BC"] --> MAP["map decoder: tiles + colour RAM"]
  DR --> VM["room_vmcsb $F2"]
  ML["main_loop $1BC2"] --> BAS["build_actor_sprites $2584"]
  BAS --> BUF["sprite buffers $8180-$83FF"]
  IRQ["irq_game_bottom $48C1"] --> FU["frame_update $15A8"]
  FU --> SAS["show_actor_sprites $25E2"]
  SAS --> PTR["sprite_pointers $8FF8"]
  IRQ --> PF["irq_game_playfield $491E"]
  PF --> SPL["irq_game_colour_split $4982"]
~~~

1. [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start) builds the graphics data once: the text font from the character ROM, four expanded room
   charsets, and the contact masks of the actor frames (**Code**).
2. [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) selects VIC bank 2 and sets the game screen: [`game_screen`](../src/constants.asm#L199) [`$8C00`](reference/variables.md#game_screen), multicolour
   characters, X-expanded sprites (**Code**).
3. [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) decodes the room map into screen and colour RAM and chooses the room charset in
   [`room_vmcsb`](../src/constants.asm#L121) [`$F2`](reference/variables.md#room_vmcsb) (**Code**).
4. Each pass, [`build_actor_sprites`](../src/actor_sprites.asm#L12) [`$2584`](reference/modules/actor_sprites.md#build_actor_sprites) draws the frames of the actors into the hidden sprite buffer. Each
   frame, the raster interrupt shows that buffer ([`show_actor_sprites`](../src/actor_sprites.asm#L75) [`$25E2`](reference/modules/actor_sprites.md#show_actor_sprites)) and switches the charset and the
   background colours at fixed raster lines (**Code**).

## 2. VIC bank 2 at run time

[`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) writes [`CI2PRA`](../src/constants.asm#L282) = `$01` (bank 2, `$8000-$BFFF`). The title, the PLAYER n screen, the
game and the game over screen all use the same screen RAM, [`game_screen`](../src/constants.asm#L199) [`$8C00`](reference/variables.md#game_screen) (**Code**). **Observed** in the
room 0 snapshot: screen `$8C00`, charset `$A000` at raster line 150, charset `$8800` at raster line 55.

| Range | Name | VIC use | CPU use |
|---|---|---|---|
| `$8000-$817F` | [`room_map_19`](../src/room_maps_15_19.asm#L158) [`$7FE0`](reference/modules/room_maps_15_19.md#room_map_19) (end) | Characters `$00-$2F` of the charset at `$8000`, sprite blocks 0-5. No screen uses them. | The end of the map of room 19. |
| `$8180-$83FF` | [`sprite_buf_a_spr0`](../src/constants.asm#L183) [`$8180`](reference/variables.md#sprite_buf_a_spr0) .. [`sprite_buf_b_spr4`](../src/constants.asm#L192) [`$83C0`](reference/variables.md#sprite_buf_b_spr4) | Sprite blocks `$06-$0F`: the two sprite buffers (section 6). Also characters `$30-$7F` of the charset at `$8000` (not used). | Work RAM, written by the sprite builder. Not part of the image: the bytes that the original image had here (an older room charset) are kept in [leftovers.md](leftovers.md). |
| `$8400-$87FF` | [`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars) | Characters `$80-$FF` of the charset at `$8000` (`$D018` = `$30`): the logo, the big letters and the big digits. | No code reads or writes it. |
| `$8800-$8BFF` | [`text_font`](../src/constants.asm#L193) [`$8800`](reference/variables.md#text_font) | The text font (`$D018` = `$32`): title menu, status line. | Built by [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start). |
| `$8C00-$8FE7` | [`game_screen`](../src/constants.asm#L199) [`$8C00`](reference/variables.md#game_screen) | Screen RAM, 40 x 25. | All screens. |
| `$8FE8-$8FF7` | [`game_screen`](../src/constants.asm#L199) [`$8C00`](reference/variables.md#game_screen) (spare) | Not shown. | The map decoder writes 2 bytes here for rooms 4, 7, 10, 13, 17 and 18. |
| `$8FF8-$8FFF` | [`sprite_pointers`](../src/constants.asm#L200) [`$8FF8`](reference/variables.md#sprite_pointers) | Sprite pointers 0-7. | [`show_actor_sprites`](../src/actor_sprites.asm#L75) [`$25E2`](reference/modules/actor_sprites.md#show_actor_sprites), [`spawn_actor`](../src/actor_spawn.asm#L20) [`$0B8E`](reference/modules/actor_spawn.md#spawn_actor), the fireballs, the title. |
| `$9000-$9FFF` | [`room_charset_a`](../src/room_charset_a.asm#L12) [`$9000`](reference/graphics.md#room_charset_a) .. [`room_charset_d`](../src/room_charset_d.asm#L8) [`$9C00`](reference/graphics.md#room_charset_d) | The VIC sees the character ROM here. No `$D018` value of the program selects it. | The four room charset sources, then (after the start) the contact masks of the actor frames in `$9000-$9FBF`. |
| `$A000-$A7FF` | [`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9) | Room charset, `$D018` = `$38`. | Built at the start; chars `$61-$63` animated. |
| `$A800-$AFFF` | [`charset_rooms_10_19`](../src/constants.asm#L205) [`$A800`](reference/variables.md#charset_rooms_10_19) | Room charset, `$D018` = `$3A`. | Built at the start; chars `$61-$63` animated. |
| `$B000-$B7FF` | [`charset_wizard`](../src/constants.asm#L206) [`$B000`](reference/variables.md#charset_wizard) | Room 18 charset, `$D018` = `$3C`. | Built at the start. |
| `$B800-$BFFF` | [`charset_wizard_flash`](../src/constants.asm#L207) [`$B800`](reference/variables.md#charset_wizard_flash) | Room 18 after the defeat of the wizard, `$D018` = `$3E`. | Built at the start. |

**Conclusion.** The program puts only data that the VIC must see in `$8000-$BFFF`, except the end of the room 19
map at `$8000-$817F`. The VIC never reads that part: no screen uses characters `$00-$7F` of the charset at `$8000`
and no sprite pointer is `$00-$05`.

### 2.1 `$D018` and `$D016` of each screen

| Screen | Part | `$D018` | Charset | `$D016` | Written by |
|---|---|---|---|---|---|
| Title | rows 0-9 (from raster `$FD` of the frame before) | `$30` | `$8000` ([`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars)) | `$18`: multicolour, 40 columns | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) |
| Title | from raster `$82` (row 10 on) | `$32` | [`text_font`](../src/constants.asm#L193) [`$8800`](reference/variables.md#text_font) | `$16`: multicolour, 38 columns, X scroll 6 | [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) |
| PLAYER n | whole screen | `$30` | `$8000` | `$18` | [`show_player_screen`](../src/title_player_screens.asm#L71) [`$0EA7`](reference/modules/title_player_screens.md#show_player_screen), [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) |
| Game | rows 0-1 (status line) | `$32` | [`text_font`](../src/constants.asm#L193) [`$8800`](reference/variables.md#text_font) | `$18` | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) |
| Game | from raster `$40` (row 2 on) | [`room_vmcsb`](../src/constants.asm#L121) [`$F2`](reference/variables.md#room_vmcsb) | room charset (table below) | `$18` | [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) |
| Game over | as the title | `$30` / `$32` | `$8000` / `$8800` | `$18` / `$16` | [`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over) installs [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) |

`$D016` = `$18` of the game is written one time by [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state). The game interrupts do not change
it (**Code**). [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) and [`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over) first write `$D016` = `$08`; the title
interrupts overwrite it in the next frame (**Code**).

| [`room_vmcsb`](../src/constants.asm#L121) [`$F2`](reference/variables.md#room_vmcsb) | Charset | Rooms | Set by |
|---|---|---|---|
| `$38` | [`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9) | 0-9 | [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room), [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) |
| `$3A` | [`charset_rooms_10_19`](../src/constants.asm#L205) [`$A800`](reference/variables.md#charset_rooms_10_19) | 10-17, 19 | [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) |
| `$3C` | [`charset_wizard`](../src/constants.asm#L206) [`$B000`](reference/variables.md#charset_wizard) | 18 | [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room); [`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated) (random flashes back) |
| `$3E` | [`charset_wizard_flash`](../src/constants.asm#L207) [`$B800`](reference/variables.md#charset_wizard_flash) | 18, after the defeat of the wizard | [`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated) |

[`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) turns [`room_vmcsb`](../src/constants.asm#L121) [`$F2`](reference/variables.md#room_vmcsb) into the high byte of the charset, [`room_charset_hi`](../src/constants.asm#L77) [`$7C`](reference/variables.md#room_charset_hi)
(`$A0`, `$A8`, `$B0`, `$B8`). The contact test and the animated characters use it (**Code**).

### 2.2 The game screen layout

| Screen rows | Text lines | Content | Charset |
|---|---|---|---|
| 0 | 0 | 40 x character `$20` (a solid block, colour RAM black): a black bar. The V key shows the version line here; room 19 prints its message here. | [`text_font`](../src/constants.asm#L193) [`$8800`](reference/variables.md#text_font) |
| 1 | 0 (offset 40-79) and 1 | The status line: `1UP 000000 TOP 000000 FALLS 04`. | [`text_font`](../src/constants.asm#L193) [`$8800`](reference/variables.md#text_font) |
| 2 | — | 40 x character 6: a separator line. | room charset |
| 3-24 | 2-12 | The room: 11 rows of 40 tiles. | room charset |

![The game screen at the start of a game (room 0)](images/screens/game_start.png)

The game screen at the start of a game: the black row 0, the status line on a grey background, the room from row 3.

## 3. Double-height tiles and charsets

### 3.1 The tile scheme

A room tile is 8 x 16 pixels. The program stores it as two characters: character c is the upper half and
character c + `$80` is the lower half. A map byte or a message byte gives c; the code writes c to the upper screen
row and c OR `$80` to the lower screen row (**Code**: [`draw_room`](../src/draw_room.asm#L28) [`$0AEA`](../src/draw_room.asm#L190), [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message)).

[`build_double_height_font`](../src/draw_helpers.asm#L51) [`$4892`](reference/modules/draw_helpers.md#build_double_height_font) makes this charset from a source charset of 128 characters of 8 x 8 multicolour
pixels. It writes each source row two times:

| Source character n | Output |
|---|---|
| rows 0-3 | character n, rows 0-7 (row r of the source goes to rows 2r and 2r+1) |
| rows 4-7 | character n + `$80`, rows 0-7 (row r goes to rows 2(r-4) and 2(r-4)+1) |

So a tile has the shape of the source character, drawn two times as high. Its pixels are 2 x 2 screen pixels
(multicolour pixels are 2 pixels wide).

Decoder (pseudo-code of [`build_double_height_font`](../src/draw_helpers.asm#L51) [`$4892`](reference/modules/draw_helpers.md#build_double_height_font)):

```
for n in 0..127:                      ; column_counter = $7F .. 0
    for r in 0..3: top[8n+2r] = top[8n+2r+1] = src[8n+r]
    for r in 4..7: bot[8n+2(r-4)] = bot[8n+2(r-4)+1] = src[8n+r]
; top = output base, bot = output base + $400
```

**Worked example.** Tile 6 of [`room_charset_a`](../src/room_charset_a.asm#L12) [`$9000`](reference/graphics.md#room_charset_a) (bytes at `$9030`) is 8 x `$FF`. Character 6 of
[`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9) (at `$A030`) gets 8 x `$FF`, and character `$86` (at `$A430`) gets 8 x `$FF`. Every
pixel is code `%11`: the colour of the colour RAM. [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) fills screen row 2 with character 6
and the colour RAM with `$F8`: the black separator line of the game screen (**Code**).

### 3.2 The charsets

| Source | Range | Expanded to | `$D018` | Used by |
|---|---|---|---|---|
| [`room_charset_a`](../src/room_charset_a.asm#L12) [`$9000`](reference/graphics.md#room_charset_a) | `$9000-$93FF` | [`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9) (top `$A000-$A3FF`, bottom `$A400-$A7FF`) | `$38` | rooms 0-9 |
| [`room_charset_b`](../src/room_charset_b.asm#L6) [`$9400`](reference/graphics.md#room_charset_b) | `$9400-$97FF` | [`charset_rooms_10_19`](../src/constants.asm#L205) [`$A800`](reference/variables.md#charset_rooms_10_19) | `$3A` | rooms 10-17 and 19 |
| [`room_charset_c`](../src/room_charset_c.asm#L6) [`$9800`](reference/graphics.md#room_charset_c) | `$9800-$9BFF` | [`charset_wizard`](../src/constants.asm#L206) [`$B000`](reference/variables.md#charset_wizard) | `$3C` | room 18 |
| [`room_charset_d`](../src/room_charset_d.asm#L8) [`$9C00`](reference/graphics.md#room_charset_d) | `$9C00-$9FFF` | [`charset_wizard_flash`](../src/constants.asm#L207) [`$B800`](reference/variables.md#charset_wizard_flash) | `$3E` | room 18 during and after the defeat of the wizard |
| character ROM `$D000-$D1FF` | 64 characters | [`text_font`](../src/constants.asm#L193) [`$8800`](reference/variables.md#text_font) (with inverted copies) | `$32` | title menu, status line |
| — (in the image) | `$8400-$87FF` | [`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars) is used as it is | `$30` | title logo, big letters, big digits |

[`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start) expands the four sources with four calls of [`build_double_height_font`](../src/draw_helpers.asm#L51) [`$4892`](reference/modules/draw_helpers.md#build_double_height_font). Then
[`build_contact_masks`](../src/frame_builder.asm#L16) [`$512F`](reference/modules/frame_builder.md#build_contact_masks) overwrites `$9000-$9FBF` with the contact masks of the actor frames. After the start,
only the expanded copies exist (**Code**). [`warm_start_flag`](../src/cold_start.asm#L7) [`$03FF`](reference/modules/cold_start.md#warm_start_flag) would skip the first three expansions; it
is always 0 (**Code**).

The charset images below come from the reference. The reference shows each source in hires and in multicolour,
in pattern colours (not the colours of a room).

![room_charset_a in multicolour](reference/images/room_charset_a-multicolour.png)

[`room_charset_a`](../src/room_charset_a.asm#L12) [`$9000`](reference/graphics.md#room_charset_a) in multicolour: the tiles of rooms 0-9 (128 characters, 16 per row).

![room_charset_a in hires](reference/images/room_charset_a-hires.png)

[`room_charset_a`](../src/room_charset_a.asm#L12) [`$9000`](reference/graphics.md#room_charset_a) in hires: the same bytes as single pixels.

![room_charset_b in multicolour](reference/images/room_charset_b-multicolour.png)

[`room_charset_b`](../src/room_charset_b.asm#L6) [`$9400`](reference/graphics.md#room_charset_b) in multicolour: the tiles of rooms 10-17 and 19.

![room_charset_b in hires](reference/images/room_charset_b-hires.png)

[`room_charset_b`](../src/room_charset_b.asm#L6) [`$9400`](reference/graphics.md#room_charset_b) in hires.

![room_charset_c in multicolour](reference/images/room_charset_c-multicolour.png)

[`room_charset_c`](../src/room_charset_c.asm#L6) [`$9800`](reference/graphics.md#room_charset_c) in multicolour: the tiles of room 18, the wizard room.

![room_charset_c in hires](reference/images/room_charset_c-hires.png)

[`room_charset_c`](../src/room_charset_c.asm#L6) [`$9800`](reference/graphics.md#room_charset_c) in hires.

![room_charset_d in multicolour](reference/images/room_charset_d-multicolour.png)

[`room_charset_d`](../src/room_charset_d.asm#L8) [`$9C00`](reference/graphics.md#room_charset_d) in multicolour: the wizard flash charset. Many tiles equal those of [`room_charset_c`](../src/room_charset_c.asm#L6) [`$9800`](reference/graphics.md#room_charset_c); the
wizard tiles have other pixel codes.

![room_charset_d in hires](reference/images/room_charset_d-hires.png)

[`room_charset_d`](../src/room_charset_d.asm#L8) [`$9C00`](reference/graphics.md#room_charset_d) in hires.

![title_logo_chars in multicolour](reference/images/title_logo_chars-multicolour.png)

[`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars) in multicolour: characters `$80-$FF` of the charset at `$8000`.

![title_logo_chars in hires](reference/images/title_logo_chars-hires.png)

[`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars) in hires: the big 2 x 2 letters and digits, the small logo letters and the BRUCE LEE logo.

### 3.3 The text font

[`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start) sets `$01` = `$32` (character ROM visible) and copies 512 bytes (**Code**):

| Codes | Address | Content |
|---|---|---|
| `$00-$1F` | [`text_font`](../src/constants.asm#L193) [`$8800`](reference/variables.md#text_font) | ROM characters `$20-$3F`: space, punctuation, digits |
| `$20-$3F` | [`text_font_letters`](../src/constants.asm#L194) [`$8900`](reference/variables.md#text_font_letters) | ROM characters `$00-$1F`: @, A-Z, [ £ ] arrows |
| `$40-$5F` | [`text_font_inverse`](../src/constants.asm#L195) [`$8A00`](reference/variables.md#text_font_inverse) | inverted `$00-$1F` |
| `$60-$7F` | [`text_font_inverse_letters`](../src/constants.asm#L198) [`$8B00`](reference/variables.md#text_font_inverse_letters) | inverted `$20-$3F` |

So the screen code of a digit or a capital letter is its ASCII code - `$20`. Three characters are patched: code
`$20` (@) becomes a solid block, code `$42` ([`text_font_keycap_left`](../src/constants.asm#L196) [`$8A10`](reference/variables.md#text_font_keycap_left)) a 2-pixel bar at the right edge,
code `$56` ([`text_font_keycap_right`](../src/constants.asm#L197) [`$8AB0`](reference/variables.md#text_font_keycap_right)) a 2-pixel bar at the left edge. The bars are the ends of the key caps
F3, F5, F7 of the title menu (**Code**). Codes `$80-$FF` of this charset would be `$8C00-$8FFF` (screen RAM); no text
uses them, because the text in rows 0-1 and on the title is one row high (see [text_messages.md](text_messages.md)).

### 3.4 Characters changed at run time

- [`animate_scrolling_chars`](../src/animated_chars.asm#L12) [`$2C70`](reference/modules/animated_chars.md#animate_scrolling_chars) rewrites characters `$61-$63` (and `$E1-$E3`) of [`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9)
  or [`charset_rooms_10_19`](../src/constants.asm#L205) [`$A800`](reference/variables.md#charset_rooms_10_19) from the 8-byte patterns [`anim_char_patterns_low_rooms`](../src/options_and_patterns.asm#L41) [`$42F1`](reference/modules/options_and_patterns.md#anim_char_patterns_low_rooms) /
  [`anim_char_patterns_high_rooms`](../src/options_and_patterns.asm#L46) [`$4309`](reference/modules/options_and_patterns.md#anim_char_patterns_high_rooms), rotated by [`anim_chars_phase`](../src/constants.asm#L63) [`$0064`](reference/variables.md#anim_chars_phase). Each pattern row is written two times,
  as in [`build_double_height_font`](../src/draw_helpers.asm#L51) [`$4892`](reference/modules/draw_helpers.md#build_double_height_font). The rows of the tile move up or down: moving scenery in rooms 4, 5, 6,
  8, 9 and 11 (**Code**).
- [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) writes code `$20` of the text font to a solid block again (**Code**).

## 4. Colours

### 4.1 Pixel colours of a room

The game screen uses multicolour characters (`$D016` = `$18`). In a character with colour RAM bit 3 set, the
pixel pairs give: `%00` = [`BGCOL0`](../src/constants.asm#L235), `%01` = [`BGCOL1`](../src/constants.asm#L236), `%10` = [`BGCOL2`](../src/constants.asm#L237), `%11` = colour RAM bits 0-2. In a character
with colour RAM bit 3 clear (the status line), the character is hires in the colour of bits 0-2.

| Source of the colour | Value | Set by |
|---|---|---|
| Colour RAM rows 0-1 | `$00` (hires, black) | [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) |
| Colour RAM row 2 | `$F8` (multicolour, black) | [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) ([`fill_colour_ram`](../src/title_menu.asm#L151) [`$09A9`](reference/modules/title_menu.md#fill_colour_ram)) |
| Colour RAM rows 3-24 | [`room_colour_fill`](../src/room_palettes.asm#L13) [`$47A0`](reference/modules/room_palettes.md#room_colour_fill) [room] | [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room), before the map |
| Black cells | `$F8` | [`map_tile_set_black`](../src/draw_room.asm#L262) [`$0B5F`](reference/modules/draw_room.md#map_tile_set_black), for a map byte with bit 7 set |
| `BGCOL0-2` of each band | [`room_palette_ptr`](../src/room_palettes.asm#L75) [`$480B`](reference/modules/room_palettes.md#room_palette_ptr) [room] | the game raster interrupts |
| [`EXTCOL`](../src/constants.asm#L234) | `$F0` black ([`vic_start_colours`](../src/room_palettes.asm#L7) [`$479B`](reference/modules/room_palettes.md#vic_start_colours)) | [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) |
| [`BGCOL0`](../src/constants.asm#L235) of the status line | `$FC` grey | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) |

[`room_colour_fill`](../src/room_palettes.asm#L13) [`$47A0`](reference/modules/room_palettes.md#room_colour_fill) (20 bytes, index = room; the `%11` colour is bits 0-2):

| Room | 0-3 | 4-6 | 7 | 8-9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Byte | `$FE` | `$FC` | `$FF` | `$FA` | `$F9` | `$FB` | `$F9` | `$FA` | `$F9` | `$FC` | `$F9` | `$FF` | `$FE` | `$FF` |
| `%11` colour | 6 | 4 | 7 | 2 | 1 | 3 | 1 | 2 | 1 | 4 | 1 | 7 | 6 | 7 |

**Black cells.** A map byte with bit 7 set draws tile (byte AND `$7F`) and writes `$F8` to its two colour RAM cells
([`map_tile_set_black`](../src/draw_room.asm#L262) [`$0B5F`](reference/modules/draw_room.md#map_tile_set_black)). The `%11` pixels of that tile are black, in a room whose `%11` colour is not
black. The same tile code can be coloured or black. The contact test of the actors tells these two cases apart
(colour RAM colour 0 or not), so black and coloured `%11` pixels act differently for the actors (**Code**; see the
comments of [`contact_col0`](../src/constants.asm#L157) [`$4EED`](reference/variables.md#contact_col0)).

### 4.2 Raster colour bands

The room area can change `BGCOL0-2` at up to three raster lines. The chain of game interrupts (all reached
through [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry) and [`irq_vector`](../src/cold_start.asm#L31) [`$0408`](reference/modules/cold_start.md#irq_vector)) is a state machine of the value in [`irq_vector`](../src/cold_start.asm#L31) [`$0408`](reference/modules/cold_start.md#irq_vector):

~~~mermaid
stateDiagram-v2
  state "irq_game_bottom $48C1 (line $FD)" as Bottom
  state "irq_game_playfield $491E (line $40)" as Play
  state "irq_game_colour_split $4982 (split line)" as Split
  [*] --> Bottom: init_game_irq $082D (line $FB)
  Bottom --> Play
  Play --> Split: first split line is not $FD
  Play --> Bottom: first split line is $FD
  Split --> Split: next split line is not $FD
  Split --> Bottom: next split line is $FD
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | always: `$D018` = `$32`, [`BGCOL0`](../src/constants.asm#L235) = `$FC`, copy 12 bytes of the room palette to [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours) and 4 split lines to [`raster_split_lines`](../src/room_palettes.asm#L56) [`$47F5`](reference/modules/room_palettes.md#raster_split_lines), call [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) | [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) at line `$40` | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) |
| [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) | waits until line `$42`; `$D018` = [`room_vmcsb`](../src/constants.asm#L121) [`$F2`](reference/variables.md#room_vmcsb); `BGCOL0-2` = band 0 | split or bottom | [`irq_arm_next_split`](../src/game_irq.asm#L89) [`$4953`](reference/modules/game_irq.md#irq_arm_next_split) |
| [`irq_arm_next_split`](../src/game_irq.asm#L89) [`$4953`](reference/modules/game_irq.md#irq_arm_next_split) | [`raster_split_lines`](../src/room_palettes.asm#L56) [`$47F5`](reference/modules/room_palettes.md#raster_split_lines) [`raster_split_index` `$44`] = `$FD` | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) at line `$FD` | [`irq_chain_to_bottom`](../src/game_irq.asm#L108) [`$4975`](reference/modules/game_irq.md#irq_chain_to_bottom) |
| [`irq_arm_next_split`](../src/game_irq.asm#L89) [`$4953`](reference/modules/game_irq.md#irq_arm_next_split) | that line is not `$FD` | [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) at that line | [`irq_arm_next_split`](../src/game_irq.asm#L89) [`$4953`](reference/modules/game_irq.md#irq_arm_next_split) |
| [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) | waits until line r+3 (or r+2 plus a delay); writes `BGCOL0-2` of the next band; [`band_palette_offset`](../src/constants.asm#L123) [`$F4`](reference/variables.md#band_palette_offset) += 3 | [`irq_arm_next_split`](../src/game_irq.asm#L89) [`$4953`](reference/modules/game_irq.md#irq_arm_next_split) | [`irq_split_set_colours`](../src/game_irq.asm#L136) [`$49A0`](reference/modules/game_irq.md#irq_split_set_colours) |

The split lists and palettes ([`room_split_list_ptr`](../src/room_palettes.asm#L82) [`$4833`](reference/modules/room_palettes.md#room_split_list_ptr), [`room_palette_ptr`](../src/room_palettes.asm#L75) [`$480B`](reference/modules/room_palettes.md#room_palette_ptr)). Each palette record is
[`BGCOL0`](../src/constants.asm#L235), [`BGCOL1`](../src/constants.asm#L236), [`BGCOL2`](../src/constants.asm#L237) (colour numbers below):

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

**Observed.** At raster line 150 of the room snapshots the colours were 11, 2, 1 in room 0, 6, 14, 1 in room 4,
12, 14, 11 in room 10, 14, 6, 11 in room 15 and 0, 14, 4 in room 18. In room 15 the colour writes happened at
lines 184/185 and 202 (split lines `$B6` = 182 and `$C7` = 199, plus 2-3 lines).

![Room 0 with three colour bands](images/rooms/room00.png)

Room 0: the colour bands change the background from the sky (band 0) to the mountains and the ground.

![Room 15 with three colour bands](images/rooms/room15.png)

Room 15: band 0 (light blue sky) above line `$B6`, then a grey band and the light grey wall below line `$C7`.

**Dead data.** [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) also copies 20 bytes from [`room_aux_ptr`](../src/room_tables.asm#L26) [`$4AA8`](reference/modules/room_tables.md#room_aux_ptr) [room] to [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours)
`$0153`. [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) overwrites the first 12 bytes every frame, and no code reads the last 8: the
copy has no effect (**Code**; **Observed** by the analysis runs: the write at [`irq_game_bottom`](../src/game_irq.asm#L12) [`$4906`](../src/game_irq.asm#L44) happens
every frame).

### 4.3 Screen saver and flashes

- After 32768 frames without input ([`idle_timer`](../src/constants.asm#L81) [`$82`](reference/variables.md#idle_timer) reaches `$80`), [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) pauses the game and
  calls [`start_screen_saver`](../src/game_setup.asm#L139) [`$102B`](reference/modules/game_setup.md#start_screen_saver). It saves [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours) in [`palette_backup`](../src/room_palettes.asm#L21) [`$47B4`](reference/modules/room_palettes.md#palette_backup). Then every
  frame [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours) = ([`palette_backup`](../src/room_palettes.asm#L21) [`$47B4`](reference/modules/room_palettes.md#palette_backup) EOR [`frame_count_256`](../src/constants.asm#L80) [`$0080`](reference/variables.md#frame_count_256)) AND `$F7`: the band colours cycle.
  [`stop_screen_saver`](../src/game_setup.asm#L151) [`$103B`](reference/modules/game_setup.md#stop_screen_saver) restores them (**Code**).
- [`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated) writes random colours `$F8`-`$FF` to the colour RAM of the wizard area and
  switches [`room_vmcsb`](../src/constants.asm#L121) [`$F2`](reference/variables.md#room_vmcsb) between `$3E` and `$3C` (**Code**).

### 4.4 Colours of the other screens

| Screen | [`EXTCOL`](../src/constants.asm#L234) / [`BGCOL0`](../src/constants.asm#L235) | [`BGCOL1`](../src/constants.asm#L236) / [`BGCOL2`](../src/constants.asm#L237) | Colour RAM |
|---|---|---|---|
| Title | `$F6` blue | `$FF` light grey | `$FF` (multicolour, yellow) rows 0-11, `$F1` (hires, white) rows 12-24 |
| PLAYER n | `$06` blue | [`BGCOL1`](../src/constants.asm#L236) changes every 2 lines from line `$6E`: `$FB`, `$FC`, `$FF`, `$F1`, `$FF`, `$FC`, `$FB` | not written |
| Game over | `$06` blue | `$0F` light grey | `$0F` rows 0-11, `$F1` rows 12-24 |

[`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) makes the shading of the big PLAYER n text with the [`BGCOL1`](../src/constants.asm#L236) changes: the text uses
pixel code `%01` (**Code**; **Observed** on the PLAYER 1 screen, the letters go from dark grey to white and back).

![The PLAYER 1 screen](images/screens/player_screen.png)

The PLAYER 1 screen: the big letters of [`title_logo_chars`](../src/title_logo_charset.asm#L9) [`$8400`](reference/graphics.md#title_logo_chars), shaded by the raster bars on [`BGCOL1`](../src/constants.asm#L236).

![The title screen](images/screens/title.png)

The title screen: logo charset in rows 0-9 (multicolour), text font from row 10 (hires, white), the TM sprite.

## 5. The frame format of the actors

### 5.1 Where the frames are

The actors are drawn from 210 *frame images* (frames 0-209). Five tables of 210 bytes describe them; index = frame
number (**Code**):

| Table | Address | Bytes | Meaning |
|---|---|---|---|
| [`frame_gfx_lo`](../src/actor_frame_gfx_tables.asm#L10) | `$59BD` | 210 | low byte of the graphics address |
| [`frame_gfx_hi`](../src/actor_frame_gfx_tables.asm#L39) | `$5A8F` | 210 | high byte of the graphics address (`$0000` = no image: the Ninja's odd frames) |
| [`frame_last_row`](../src/actor_frame_gfx_tables.asm#L71) | `$5B61` | 210 | height code: narrow frame = index of the last row (rows = value + 1); wide frame = number of rows |
| [`frame_colour`](../src/actor_frame_gfx_tables.asm#L102) | `$5C33` | 140 | sprite colour of frames 0-139 (`$F7` yellow, `$F5` green, `$F0` black) |
| [`frame_is_wide`](../src/actor_frame_gfx_tables.asm#L124) | `$5CBF` | 210 | 0 = 8 pixels wide (1 byte per row), nonzero (`$01` or `$55`) = 16 pixels (2 bytes per row) |

| Frames | Actor | Base ([`actor_frame_base`](../src/actor_frame_tables.asm#L8) [`$59A5`](reference/modules/actor_frame_tables.md#actor_frame_base)) | Graphics |
|---|---|---|---|
| 0-69 | Bruce | 0 | [`bruce_frame_56`](../src/bruce_frames.asm#L8) [`$636A`](reference/modules/bruce_frames.md#bruce_frame_56) .. (region `$636A-$67FC`) |
| 70-139 | Yamo | 70 | region `$5D91-$6282` ([`yamo_frame_00`](../src/yamo_frames.asm#L289) [`$6187`](reference/modules/yamo_frames.md#yamo_frame_00) ...) |
| 140-209 | Ninja | 140 | `$6283-$6369` and [`ninja_frame_00`](../src/ninja_frames_b.asm#L7) [`$67FD`](reference/modules/ninja_frames_b.md#ninja_frame_00) .. `$68F8` |

[`actor_frame_base`](../src/actor_frame_tables.asm#L8) [`$59A5`](reference/modules/actor_frame_tables.md#actor_frame_base) is indexed by the actor *type* (bits 7-6 of [`actor_flags`](../src/constants.asm#L91) [`$95`](reference/variables.md#actor_flags): 0 Bruce, 1 Ninja,
2 Yamo), so its bytes are 0, 140, 70. A pose is an even number. [`set_actor_pose`](../src/actor_poses.asm#L324) [`$29A1`](reference/modules/actor_poses.md#set_actor_pose) sets
[`actor_frame_a`](../src/constants.asm#L175) [`$4F4E`](reference/variables.md#actor_frame_a) = base + pose (the main sprite) and [`actor_frame_b`](../src/constants.asm#L176) [`$4F51`](reference/variables.md#actor_frame_b) = base + pose + 1 (the overlay
sprite) (**Code**).

- Even frames are the main sprite of a pose, odd frames the overlay sprite. Bruce and Yamo have two layers: a
  coloured layer (skin: yellow for Bruce, green for Yamo) and a black layer (hair, clothes). The Ninja has one
  black sprite; [`setup_sprite_frame`](../src/actor_sprites.asm#L278) [`$2719`](reference/modules/actor_sprites.md#setup_sprite_frame) gives him `$F0` without reading [`frame_colour`](../src/actor_frame_gfx_tables.asm#L102) [`$5C33`](reference/modules/actor_frame_gfx_tables.md#frame_colour).
- The code never mirrors a frame. Each facing has its own frames (for example Bruce 0 and 2) (**Code**).
- Several frame numbers share graphics: Bruce 42-55 use frames 0/1, Bruce 68/69 use 32/33, Yamo 112/113, 118-125
  and 134-139 use 78/79, many Ninja frames use frame 140 (**Code**: the address tables).
- Wide frames: 4-7, 25, 29, 59, 63, 65, 67 (Bruce), 74-77, 94, 95, 98, 99, 128, 132, 133 (Yamo), 190, 194, 196,
  198, 200, 202 (Ninja) (**Code**).
- The original image held 42 more bytes in frame format at `$63C1-$63EA`, equal to frame 59, that no table entry
  points to: the frame ADWONL22 with a misspelt source label. It is a development leftover and not part of the
  rebuilt game ([adwonl22_unused_frame.asm](../leftovers/build_10f8_63ea/adwonl22_unused_frame.asm),
  [leftovers.md](leftovers.md#44-adwonl22-the-typo-and-the-unused-frame)) (**Code**).

### 5.2 The byte layout

| Width | Source bytes | Sprite rows |
|---|---|---|
| narrow ([`frame_is_wide`](../src/actor_frame_gfx_tables.asm#L124) [`$5CBF`](reference/modules/actor_frame_gfx_tables.md#frame_is_wide) = 0) | byte r = row r, r = 0 .. [`frame_last_row`](../src/actor_frame_gfx_tables.asm#L71) [`$5B61`](reference/modules/actor_frame_gfx_tables.md#frame_last_row) | sprite byte 3r = byte r; bytes 3r+1 and 3r+2 = 0 |
| wide ([`frame_is_wide`](../src/actor_frame_gfx_tables.asm#L124) [`$5CBF`](reference/modules/actor_frame_gfx_tables.md#frame_is_wide) <> 0) | bytes 2r (left) and 2r+1 (right) = row r, r = 0 .. [`frame_last_row`](../src/actor_frame_gfx_tables.asm#L71) [`$5B61`](reference/modules/actor_frame_gfx_tables.md#frame_last_row) - 1 | sprite byte 3r = byte 2r, 3r+1 = byte 2r+1, 3r+2 = 0 |

Each bit is one hires sprite pixel. All sprites are X-expanded ([`XXPAND`](../src/constants.asm#L232) = `$FF`, [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state)), so a
narrow frame is 16 screen pixels wide and a wide frame 32. The sprites are hires ([`SPMC`](../src/constants.asm#L231) = 0) and in front of the
background ([`SPBGPR`](../src/constants.asm#L230) = 0). The rows after the frame, up to byte 63, are 0 (**Code**).

**Frame height for the contact masks.** [`expand_contact_mask`](../src/frame_builder.asm#L93) [`$517E`](reference/modules/frame_builder.md#expand_contact_mask) reads [`frame_last_row`](../src/actor_frame_gfx_tables.asm#L71) [`$5B61`](reference/modules/actor_frame_gfx_tables.md#frame_last_row) + 1 rows for both
widths. For a wide frame that is one row more than the sprite builder draws (**Code**).

### 5.3 The decoder

[`build_actor_sprites`](../src/actor_sprites.asm#L12) [`$2584`](reference/modules/actor_sprites.md#build_actor_sprites), [`setup_sprite_frame`](../src/actor_sprites.asm#L278) [`$2719`](reference/modules/actor_sprites.md#setup_sprite_frame) and [`copy_sprite_frame`](../src/actor_sprites.asm#L190) [`$26A0`](reference/modules/actor_sprites.md#copy_sprite_frame) together:

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

[`setup_sprite_frame`](../src/actor_sprites.asm#L278) [`$2719`](reference/modules/actor_sprites.md#setup_sprite_frame) writes the source address into the operands [`copy_sprite_frame_narrow_src`](../src/actor_sprites.asm#L197) [`$26AB`](reference/modules/actor_sprites.md#copy_sprite_frame_narrow_src),
[`copy_sprite_frame_wide_src_a`](../src/actor_sprites.asm#L235) [`$26E4`](reference/modules/actor_sprites.md#copy_sprite_frame_wide_src_a) and [`copy_sprite_frame_wide_src_b`](../src/actor_sprites.asm#L242) [`$26EE`](reference/modules/actor_sprites.md#copy_sprite_frame_wide_src_b) (self-modified code). [`sprite_copy_counter`](../src/actor_sprites.asm#L335) [`$277F`](reference/modules/actor_sprites.md#sprite_copy_counter)
`$277F` counts the 64 bytes of the block (**Code**).

### 5.4 Worked example: Bruce standing, frames 2 and 3

At the start of room 0 Bruce has pose 2 (standing, facing right): [`actor_frame_a`](../src/constants.asm#L175) [`$4F4E`](reference/variables.md#actor_frame_a) = 2 (**Observed**: room 0
start snapshot, [`actor_pose`](../src/constants.asm#L173) [`$4F48`](reference/variables.md#actor_pose) = 2, [`actor_facing`](../src/constants.asm#L96) [`$A4`](reference/variables.md#actor_facing) = 1).

Table bytes:

| Table | Frame 2 | Frame 3 |
|---|---|---|
| low byte | [`frame_gfx_lo+2`](../src/actor_frame_gfx_tables.asm#L10) [`$59BF`](reference/modules/actor_frame_gfx_tables.md#frame_gfx_lo) = `$46` | [`frame_gfx_lo+3`](../src/actor_frame_gfx_tables.asm#L10) [`$59C0`](reference/modules/actor_frame_gfx_tables.md#frame_gfx_lo) = `$67` |
| high byte | [`frame_gfx_hi+2`](../src/actor_frame_gfx_tables.asm#L39) [`$5A91`](reference/modules/actor_frame_gfx_tables.md#frame_gfx_hi) = `$66` | [`frame_gfx_hi+3`](../src/actor_frame_gfx_tables.asm#L39) [`$5A92`](reference/modules/actor_frame_gfx_tables.md#frame_gfx_hi) = `$66` |
| graphics | [`bruce_frame_02`](../src/bruce_frames_b.asm#L207) [`$6646`](reference/modules/bruce_frames_b.md#bruce_frame_02) | [`bruce_frame_03`](../src/bruce_frames_b.asm#L220) [`$6667`](reference/modules/bruce_frames_b.md#bruce_frame_03) |
| height | [`frame_last_row+2`](../src/actor_frame_gfx_tables.asm#L71) [`$5B63`](reference/modules/actor_frame_gfx_tables.md#frame_last_row) = `$0B`: 12 rows | [`frame_last_row+3`](../src/actor_frame_gfx_tables.asm#L71) [`$5B64`](reference/modules/actor_frame_gfx_tables.md#frame_last_row) = `$14`: 21 rows |
| colour | [`frame_colour+2`](../src/actor_frame_gfx_tables.asm#L102) [`$5C35`](reference/modules/actor_frame_gfx_tables.md#frame_colour) = `$F7` yellow | [`frame_colour+3`](../src/actor_frame_gfx_tables.asm#L102) [`$5C36`](reference/modules/actor_frame_gfx_tables.md#frame_colour) = `$F0` black |
| width | [`frame_is_wide+2`](../src/actor_frame_gfx_tables.asm#L124) [`$5CC1`](reference/modules/actor_frame_gfx_tables.md#frame_is_wide) = 0: narrow | [`frame_is_wide+3`](../src/actor_frame_gfx_tables.asm#L124) [`$5CC2`](reference/modules/actor_frame_gfx_tables.md#frame_is_wide) = 0: narrow |

Graphics bytes: frame 2 = `00 10 30 28 38 38 30 70 78 6C 4E 38`; frame 3 = `30 60 48 50 40 00 00 00 00 11 31 00
38 38 2C 24 24 24 24 66 E7`. Each row of the picture is one byte, bit 7 left. `Y` is a pixel of frame 2 (sprite
0, yellow), `#` a pixel of frame 3 (sprite 1, black), `.` no pixel. Sprite 0 has priority over sprite 1, so `Y`
wins where both have a pixel:

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

Black hair on top, the yellow face and arms, the black trousers and feet. **Observed** in the same run: after
[`build_actor_sprites`](../src/actor_sprites.asm#L12) [`$2584`](reference/modules/actor_sprites.md#build_actor_sprites), [`sprite_buf_a_spr0`](../src/constants.asm#L183) [`$8180`](reference/variables.md#sprite_buf_a_spr0) held `00 00 00 10 00 00 30 00 00 28 ...` (the bytes of
frame 2 at offsets 0, 3, 6, ...) and [`sprite_buf_a_spr1`](../src/constants.asm#L184) [`$81C0`](reference/variables.md#sprite_buf_a_spr1) the 21 bytes of frame 3 in the same way. Sprites 0
and 1 were at X = 52, Y = 225 ([`actor_x`](../src/constants.asm#L94) [`$9E`](reference/variables.md#actor_x) = `$1A`, 52 = 2 x 26; [`actor_y`](../src/constants.asm#L95) [`$A1`](reference/variables.md#actor_y) = `$C4`, 225 = 196 + 29).

## 6. The sprite system

### 6.1 The sprites of each actor

| Hardware sprite | Use | Colour | Collision code |
|---|---|---|---|
| 0 | Bruce, main sprite (even frame) | [`frame_colour`](../src/actor_frame_gfx_tables.asm#L102) [`$5C33`](reference/modules/actor_frame_gfx_tables.md#frame_colour) (yellow) | 4 |
| 1 | Bruce, overlay sprite (odd frame) | [`frame_colour`](../src/actor_frame_gfx_tables.asm#L102) [`$5C33`](reference/modules/actor_frame_gfx_tables.md#frame_colour) (black) | 5 |
| 2 | Yamo, main sprite | [`frame_colour`](../src/actor_frame_gfx_tables.asm#L102) [`$5C33`](reference/modules/actor_frame_gfx_tables.md#frame_colour) (green) | 6 |
| 3 | Yamo, overlay sprite | [`frame_colour`](../src/actor_frame_gfx_tables.asm#L102) [`$5C33`](reference/modules/actor_frame_gfx_tables.md#frame_colour) (black) | 7 |
| 4 | the Ninja (one sprite) | `$F0` black | 3 |
| 5 | not used ([`spawn_actor`](../src/actor_spawn.asm#L20) [`$0B8E`](reference/modules/actor_spawn.md#spawn_actor) writes its pointer as a side effect) | — | — |
| 6, 7 | room 18: the two fireballs | random | — |
| 0 | title: the TM sign | `$FF` light grey | — |

[`actor_main_sprite`](../src/actor_sprites.asm#L319) [`$276D`](reference/modules/actor_sprites.md#actor_main_sprite) = 0, 2, 4 and [`actor_overlay_sprite`](../src/actor_sprites.asm#L322) [`$2770`](reference/modules/actor_sprites.md#actor_overlay_sprite) = 1, 3, `$FF` give the hardware sprites
of actors 0, 1, 2. [`actor_collision_code_first`](../src/actor_frame_tables.asm#L13) [`$59A8`](reference/modules/actor_frame_tables.md#actor_collision_code_first) / [`actor_collision_code_second`](../src/actor_frame_tables.asm#L17) [`$59AB`](reference/modules/actor_frame_tables.md#actor_collision_code_second) give the collision
codes by type; [`collision_code_to_sprite`](../src/actor_frame_tables.asm#L22) [`$59AE`](reference/modules/actor_frame_tables.md#collision_code_to_sprite) turns code 3-7 into sprite 4, 0, 1, 2, 3. [`set_sprite_slot_owner`](../src/actor_spawn.asm#L420) [`$0E21`](reference/modules/actor_spawn.md#set_sprite_slot_owner)
`$0E21` writes the actor into [`sprite_owner`](../src/constants.asm#L171) [`$4F40`](reference/variables.md#sprite_owner) [sprite]; [`check_fight_collisions`](../src/fight_hits.asm#L14) [`$29C3`](reference/modules/fight_hits.md#check_fight_collisions) reads it to find which
actor owns a sprite in a sprite-sprite collision (**Code**).

### 6.2 The sprite blocks

| Block | Address | Name | Buffer A / B | Other use |
|---|---|---|---|---|
| `$06` | `$8180` | [`sprite_buf_a_spr0`](../src/constants.asm#L183) | A, sprite 0 | |
| `$07` | `$81C0` | [`sprite_buf_a_spr1`](../src/constants.asm#L184) | A, sprite 1 | |
| `$08` | `$8200` | [`sprite_buf_a_spr2`](../src/constants.asm#L185) | A, sprite 2 | |
| `$09` | `$8240` | [`sprite_buf_a_spr3`](../src/constants.asm#L186) | A, sprite 3 | |
| `$0A` | `$8280` | [`sprite_buf_a_spr4`](../src/constants.asm#L187) | A, sprite 4 | |
| `$0B` | `$82C0` | [`sprite_buf_b_spr0`](../src/constants.asm#L188) | B, sprite 0 | |
| `$0C` | `$8300` | [`sprite_buf_b_spr1`](../src/constants.asm#L189) | B, sprite 1 | |
| `$0D` | `$8340` | [`sprite_buf_b_spr2`](../src/constants.asm#L190) | B, sprite 2 | room 18: fireball 0, sprite 6 ([`launch_fireball0`](../src/wizard_fireballs.asm#L141) [`$4201`](reference/modules/wizard_fireballs.md#launch_fireball0)) |
| `$0E` | `$8380` | [`sprite_buf_b_spr3`](../src/constants.asm#L191) | B, sprite 3 | room 18: fireball 1, sprite 7 ([`launch_fireball1`](../src/wizard_fireballs.asm#L156) [`$4220`](reference/modules/wizard_fireballs.md#launch_fireball1)) |
| `$0F` | `$83C0` | [`sprite_buf_b_spr4`](../src/constants.asm#L192) | B, sprite 4 | title: TM sprite; [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) points all eight sprites here |

[`sprite_buffer_addresses`](../src/actor_sprites.asm#L309) [`$274F`](reference/modules/actor_sprites.md#sprite_buffer_addresses) holds the ten block addresses and [`sprite_buffer_pointers`](../src/actor_sprites.asm#L315) [`$2763`](reference/modules/actor_sprites.md#sprite_buffer_pointers) the ten block
numbers, buffer A first. Index = sprite + 5 x buffer (**Code**). **Conclusion.** The fireballs can share blocks
`$0D`/`$0E` with Yamo's buffer B because room 18 has no enemies ([`room_no_enemies`](../src/room_tables.asm#L164) [`$4C9E`](reference/modules/room_tables.md#room_no_enemies) = `$FF`).

### 6.3 The double buffer

[`sprite_buffer_select`](../src/actor_sprites.asm#L331) [`$277D`](reference/modules/actor_sprites.md#sprite_buffer_select) (0 = A, 1 = B) is the buffer that the next build fills. [`sprite_images_shown`](../src/actor_sprites.asm#L333) [`$277E`](reference/modules/actor_sprites.md#sprite_images_shown)
`$277E` is the hand-shake between the main loop and the interrupt.

~~~mermaid
stateDiagram-v2
  state "Shown (sprite_images_shown = 1)" as Shown
  state "Ready (sprite_images_shown = 0)" as Ready
  [*] --> Shown
  Shown --> Ready: build_actor_sprites $2584 ends
  Ready --> Shown: show_actor_sprites $25E2 (next frame)
  Shown --> Shown: show_actor_sprites returns at once
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Shown | [`build_actor_sprites`](../src/actor_sprites.asm#L12) [`$2584`](reference/modules/actor_sprites.md#build_actor_sprites) has drawn all actors into buffer [`sprite_buffer_select`](../src/actor_sprites.asm#L331) [`$277D`](reference/modules/actor_sprites.md#sprite_buffer_select) | Ready | [`build_actor_sprites`](../src/actor_sprites.asm#L12) [`$25DE`](../src/actor_sprites.asm#L64) |
| Ready | [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) calls [`show_actor_sprites`](../src/actor_sprites.asm#L75) [`$25E2`](reference/modules/actor_sprites.md#show_actor_sprites) (raster line `$FD`) | Shown: positions and colours written, pointers 0-4 = blocks of buffer [`sprite_buffer_select`](../src/actor_sprites.asm#L331) [`$277D`](reference/modules/actor_sprites.md#sprite_buffer_select), then [`sprite_buffer_select`](../src/actor_sprites.asm#L331) [`$277D`](reference/modules/actor_sprites.md#sprite_buffer_select) EOR 1 | [`show_actor_sprites_pointers`](../src/actor_sprites.asm#L168) [`$2682`](reference/modules/actor_sprites.md#show_actor_sprites_pointers) |
| Shown | [`show_actor_sprites`](../src/actor_sprites.asm#L75) [`$25E2`](reference/modules/actor_sprites.md#show_actor_sprites) | Shown (nothing changes) | [`show_actor_sprites`](../src/actor_sprites.asm#L75) [`$25E2`](reference/modules/actor_sprites.md#show_actor_sprites) |

1. The main loop builds the images once per pass (every 3 frames) into the hidden buffer ([`main_loop`](../src/game_main_loop.asm#L23) [`$1C2C`](../src/game_main_loop.asm#L80)).
   [`change_room`](../src/background_touch.asm#L234) [`$2F9A`](reference/modules/background_touch.md#change_room) also builds them after a room is drawn.
2. The interrupt at line `$FD` shows them: the pointers change below the visible screen, so the new images
   start with the next frame (**Conclusion**: no tearing).
3. Then [`sprite_buffer_select`](../src/actor_sprites.asm#L331) [`$277D`](reference/modules/actor_sprites.md#sprite_buffer_select) flips, and the next build writes the other buffer, which the VIC does not
   show any more.

[`show_actor_sprites`](../src/actor_sprites.asm#L75) [`$25E2`](reference/modules/actor_sprites.md#show_actor_sprites) also places the sprites (**Code**):

- X = 2 x [`actor_x`](../src/constants.asm#L94) [`$9E`](reference/variables.md#actor_x) (bit 8 in [`MSIGX`](../src/constants.asm#L221)), Y = [`actor_y`](../src/constants.asm#L95) [`$A1`](reference/variables.md#actor_y) + `$1D`. Both sprites of an actor have the same
  position.
- A wide main frame moves 8 units (16 pixels) left when the actor faces left ([`actor_facing`](../src/constants.asm#L96) [`$A4`](reference/variables.md#actor_facing) <> 1).
- The overlay sprite moves 8 units left for the poses `$04`, `$3E`, `$42` and `$18` ([`actor_pose_b`](../src/constants.asm#L174) [`$4F4B`](reference/variables.md#actor_pose_b) =
  `$05`, `$3F`, `$43`, `$19`).
- [`actor_shown_x`](../src/constants.asm#L103) [`$B9`](reference/variables.md#actor_shown_x) keeps the X that is on the screen.

### 6.4 The fireballs (room 18)

[`update_fireballs`](../src/wizard_fireballs.asm#L13) [`$4133`](reference/modules/wizard_fireballs.md#update_fireballs) writes 4 random rows (byte 0 of rows 0-3, AND [`fireball_shape_mask`](../src/fireball_shape.asm#L8) [`$4322`](reference/modules/fireball_shape.md#fireball_shape_mask)) into blocks `$0D`
and `$0E` every pass, so the fireballs sparkle. They are sprites 6 and 7 with random colours.
[`clear_fireball_sprites`](../src/wizard_fireballs.asm#L171) [`$423F`](reference/modules/wizard_fireballs.md#clear_fireball_sprites) clears those rows (**Code**).

### 6.5 The title TM sprite

[`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) clears [`sprite_buf_b_spr4`](../src/constants.asm#L192) [`$83C0`](reference/variables.md#sprite_buf_b_spr4), copies [`title_tm_sprite_rows`](../src/title_sprite.asm#L22) [`$0E40`](reference/modules/title_sprite.md#title_tm_sprite_rows) (12 bytes)
to rows 4-7 of it and shows it as sprite 0: block `$0F`, X = `$10A` (266), Y = `$56` (86), X-expanded, light grey
(**Code**; **Observed** on the title screenshot, a small TM after BRUCE LEE).

```
row  bytes       pixels of byte 0
 4   EA 00 00    XXX.X.X.
 5   4E 00 00    .X..XXX.
 6   4A 00 00    .X..X.X.
 7   4A 00 00    .X..X.X.
```

## 7. Still open

- Why [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) writes `$D016` = `$16` (38 columns, X scroll 6) for the menu part of the title.
  **Observed**: at raster line 200 of the title the VIC had X scroll 6 and charset `$8800`. A screen capture with a
  grid can show how far the menu text moves.
- Whether charset source D was planned for more than the wizard flash. Only [`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated) selects
  it.
