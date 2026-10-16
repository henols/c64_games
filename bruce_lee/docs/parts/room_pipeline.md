# Bruce Lee: room data and room generation

Up: [the rooms](../rooms.md)

This page describes the room data of *Bruce Lee* (Datasoft 1984, C64 REV.2) and the code that turns it into a screen.

**Scope.**
- the per-room tables: where they are, their layout, their readers;
- the RLE format of the room maps and its decoder;
- [`draw_room`](../../src/room_draw.asm#L6) [`$09BC`](../reference/modules/room_draw.md#draw_room) step by step;
- the end of a room draw: the lantern redraw, the init handler and the first pass of the frame handler;
- the one-time preparation that the rooms need: the charset expansion and the text row tables;
- the colour bands of each room (the room part of the raster interrupt chain);
- the room transition, from the touch of an exit tile to the new room;
- a worked decode of the start of room 0;
- the screen memory layout.

Not on this page: the mechanics of the raster interrupt chain ([interrupts.md](interrupts.md)), the sprites and the collision masks ([sprites.md](sprites.md)), the main loop ([main_loop.md](main_loop.md)), the actors and the enemy spawning ([actors.md](actors.md)), the handlers of each room ([rooms_00_09.md](rooms_00_09.md), [rooms_10_19.md](rooms_10_19.md)) and the room-level game flow ([room_flow.md](room_flow.md)).

**Sources.**
- The generated source and its reference: [room_draw.asm](../reference/modules/room_draw.md), [room_maps.asm](../reference/modules/room_maps.md), [room_tables.asm](../reference/modules/room_tables.md), [room_colours.asm](../reference/modules/room_colours.md), [room_split_tables.asm](../reference/modules/room_split_tables.md), [charset_expand.asm](../reference/modules/charset_expand.md), [lanterns.asm](../reference/modules/lanterns.md), [room_init.asm](../reference/modules/room_init.md), [background_touch.asm](../reference/modules/background_touch.md), [room_entry_traps.asm](../reference/modules/room_entry_traps.md), [raster_irq_game.asm](../reference/modules/raster_irq_game.md), [init.asm](../reference/modules/init.md), [game_setup.asm](../reference/modules/game_setup.md), [actor_room_tables.asm](../reference/modules/actor_room_tables.md). The tables are decoded in [tables.md](../reference/tables.md).
- The image `unpacked/image.bin` (64 KiB of RAM at the entry `$0400`): every table on this page is decoded from it.
- The assets: the room renders and decoded maps in `assets/rooms/` (`roomNN.png`, `roomNN.json`) and the charsets in `assets/charsets/`.
- The runs: `rooms` (a snapshot of each room), `room_events2` and `room_events3` (lanterns taken), `room_special` (the room 11 diversion, the wizard defeat, the ending). The coverage of all runs is in the source as `; not executed` marks.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *room* is a screen, number 0-19 in [`current_room`](../../src/constants.asm#L28) [`$29`](../reference/variables.md#current_room). All per-room tables are indexed by it.
- A *pass* is one run of [`main_loop`](../../src/main_loop.asm#L6) [`$1BC2`](../reference/modules/main_loop.md#main_loop), at most one pass every 3 frames. A *frame* is one video frame: one run of the raster IRQ chain (50 per second on PAL).
- An *actor* is a moving figure, numbered by its index into the actor tables: actor 0 = Bruce, actor 1 = Yamo, actor 2 = Ninja. The names of actors 1 and 2 rest on their colours and on the opponent option (report.md).
- A *cell* is one map position: a double-height tile of 8 x 16 pixels, two chars on the screen. A *text row* is a row of the message printer [`print_message`](../../src/text.asm#L6) [`$17E2`](../reference/modules/text.md#print_message); map row R is text row R+2.
- A *message* is a string printed by [`print_message`](../../src/text.asm#L6) [`$17E2`](../reference/modules/text.md#print_message): text, or a string of tiles.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code or the image only. **Conclusion** marks an interpretation.

---

## 1. Overview

```
cold_start $0400 (once)
  expand_charset $4892 x4      charset sources $9000-$9FFF -> 4 VIC charsets $A000-$BFFF
  build_collision_masks $512F  actor frames -> collision masks (over $9000-$9FBF and in $C000-$CADF)
init_game_screen $0763 (title, game start, demo start, each lost fall)
  game IRQ chain, text row tables, colour RAM, VIC bank 2, status line, Bruce
draw_room $09BC (each room entry; IRQs off)
  blank, colour RAM <- room_char_colours, [room 11 -> room 13], entry bonus, room state,
  spawn timers, Atari colour set, charset choice ($F2), RLE map -> screen rows 3-24,
  redraw_taken_lanterns $336E -> room init handler, unblank, run_room_update $3A6F -> frame handler
each frame (raster IRQ chain)
  irq_frame_top $48C1 (line $FD) -> irq_playfield_top $491E (line $40) -> irq_colour_split $4982 (each listed line)
each pass of main_loop
  run_room_update -> frame handler; check_actors_background $2E39 -> exit -> enter_room $2F8E -> draw_room
```

---

## 2. The catalogue of the per-room data

### 2.1 The values of each room

Decoded from the image (**Code**). The handler columns give the targets: the table value plus 1.

| Room | Map | Colour RAM `$47A0` | `$F2` | Bands `$480B` | Raster list `$4833` | Atari set `$4AA8` | Lanterns `$4CCE` | Lantern list `$4CE2` | No combat `$4C9E` | Init handler | Frame handler |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | $68F9 | $FE | $38 | $47C8 | $47F9: $78,$97 | $4AD0 | 6 | $4D0C | $00 | $33F5 | $3642 |
| 1 | $6A09 | $FE | $38 | $47C8 | $47FC: $78,$97 | $4AD0 | 6 | $4D25 | $00 | $33F6 | $3679 |
| 2 | $6B3E | $FE | $38 | $47C8 | $47FF: $78,$97 | $4AD0 | 10 | $4D3E | $00 | $33F5 | $36A6 |
| 3 | $6C9D | $FE | $38 | $47C8 | $4802: $62,$97 | $4AD0 | 2 | $4D67 | $FF | $33FC | $3702 |
| 4 | $6E1B | $FC | $38 | $47D1 | $4805: - | $4AE4 | 2 | $4D70 | $00 | $3402 | $3760 |
| 5 | $6F82 | $FC | $38 | $47D1 | $4805: - | $4AE4 | 10 | $4D79 | $00 | $3428 | $38AB |
| 6 | $70DD | $FC | $38 | $47D1 | $4805: - | $4AE4 | 8 | $4DA2 | $00 | $33F5 | $39AA |
| 7 | $7227 | $FF | $38 | $47D4 | $4805: - | $4AE9 | 13 | $4DC3 | $00 | $3461 | $39C3 |
| 8 | $7311 | $FA | $38 | $47D4 | $4805: - | $4AE9 | 4 | $4DF8 | $FF | $3478 | $3AD4 |
| 9 | $7491 | $FA | $38 | $47D4 | $4805: - | $4AE9 | 5 | $4E09 | $FF | $348F | $3BB2 |
| 10 | $75D8 | $F9 | $3A | $47D7 | $4806: $56 | $4AEE | 3 | $4E1E | $00 | $33F5 | $3C90 |
| 11 | $774C | $FB | $3A | $47DD | $4805: - | $4AFD | 3 | $4E2B | $FF | $33F5 | $3CC0 |
| 12 | $7843 | $F9 | $3A | $47D7 | $4806: $56 | $4AEE | 3 | $4E38 | $00 | $34BD | $3E4C |
| 13 | $79C6 | $FA | $3A | $47E0 | $4805: - | $4B02 | 0 | $4E45 | $FF | $34C3 | $3E7C |
| 14 | $7A46 | $F9 | $3A | $47D7 | $4806: $56 | $4AEE | 4 | $4E4A | $00 | $358D | $3ECC |
| 15 | $7BB4 | $FC | $3A | $47E3 | $4808: $B6,$C7 | $4B0C | 6 | $4E5B | $00 | $3593 | $3EE6 |
| 16 | $7C5C | $F9 | $3A | $47D7 | $4806: $56 | $4AEE | 2 | $4E74 | $00 | $359F | $3F5B |
| 17 | $7D8D | $FF | $3A | $47EC | $4805: - | $4B1B | 2 | $4E7D | $FF | $35C4 | $3F71 |
| 18 | $7E90 | $FE | $3C | $47EF | $4805: - | $4B25 | 1 | $4E86 | $FF | $35FA | $3CDC |
| 19 | $7FE0 | $FF | $3A | $47F2 | $4805: - | $4B2A | 0 | $4E8B | $FF | $425F | $4272 |

The exits and the spawn points (**Code**). A `-` means that the destination, x and y are all 0.

| Room | Exit 2: dest / x / y | Exit 3 | Exit 4 | Exit 5 | Spawn A `$4BAE/$4BC2` | Spawn B `$4BD6/$4BEA` |
|---|---|---|---|---|---|---|
| 0 | 1 / $10 / $92 | - | - | 1 / $0F / $62 | $1A / $C4 | $9F / $62 |
| 1 | 0 / $A0 / $92 | 5 / $2C / $32 | 0 / $A1 / $62 | 2 / $10 / $62 | $18 / $62 | $95 / $92 |
| 2 | - | - | 1 / $A1 / $62 | 3 / $10 / $C4 | $30 / $C4 | $96 / $C4 |
| 3 | - | 10 / $10 / $B0 | 2 / $A1 / $C5 | 0 / $10 / $62 | $20 / $C0 | $38 / $C4 |
| 4 | 5 / $10 / $C2 | 7 / $1F / $32 | - | - | $94 / $B4 | $96 / $B4 |
| 5 | 4 / $9C / $51 | 6 / $10 / $40 | 6 / $10 / $74 | 1 / $58 / $66 | $22 / $51 | $28 / $C2 |
| 6 | 5 / $A0 / $80 | 5 / $A0 / $66 | 2 / $16 / $51 | 0 / $20 / $51 | $86 / $B3 | $81 / $72 |
| 7 | 0 / $30 / $51 | 8 / $0F / $46 | 8 / $10 / $C0 | 0 / $20 / $51 | $1C / $44 | $1F / $74 |
| 8 | 7 / $A0 / $74 | 9 / $10 / $53 | 7 / $A1 / $B5 | 9 / $0F / $C6 | $14 / $46 | $00 / $00 |
| 9 | 8 / $A0 / $47 | 8 / $A0 / $C0 | 6 / $9D / $C7 | - | $12 / $C6 | $00 / $00 |
| 10 | 3 / $A0 / $C4 | 11 / $10 / $C4 | - | - | $34 / $8C | $96 / $5C |
| 11 | 10 / $A0 / $5A | 12 / $10 / $5C | 14 / $10 / $5E | 16 / $10 / $5C | $40 / $4C | $00 / $00 |
| 12 | - | 11 / $34 / $BE | 14 / $10 / $BE | - | $18 / $5C | $70 / $5C |
| 13 | 15 / $10 / $C3 | - | - | - | $98 / $32 | $00 / $00 |
| 14 | - | 11 / $50 / $BE | 12 / $A0 / $BE | 16 / $10 / $BE | $18 / $5C | $92 / $BE |
| 15 | 13 / $A0 / $C4 | 17 / $10 / $B3 | - | - | $1C / $C3 | $7A / $C4 |
| 16 | - | 11 / $80 / $BE | 14 / $A0 / $BE | - | $18 / $5C | $81 / $8E |
| 17 | 15 / $A0 / $93 | 18 / $10 / $C6 | - | - | $18 / $B4 | $00 / $00 |
| 18 | 17 / $A0 / $44 | 19 / $10 / $96 | - | - | $18 / $C6 | $00 / $00 |
| 19 | - | - | - | - | $12 / $95 | $00 / $00 |

The enemy tables of each room (**Code**). The timers count passes. Their use is in [actors.md](actors.md).

| Room | [`ninja_first_spawn_delay`](../../src/actor_room_tables.asm#L69) [`$130B`](../reference/modules/actor_room_tables.md#ninja_first_spawn_delay) | [`ninja_respawn_delay`](../../src/actor_room_tables.asm#L74) [`$131F`](../reference/modules/actor_room_tables.md#ninja_respawn_delay) | [`ninja_entry_preference`](../../src/actor_room_tables.asm#L79) [`$1333`](../reference/modules/actor_room_tables.md#ninja_entry_preference) | [`yamo_first_spawn_delay`](../../src/actor_room_tables.asm#L84) [`$1347`](../reference/modules/actor_room_tables.md#yamo_first_spawn_delay) | [`yamo_respawn_delay`](../../src/actor_room_tables.asm#L89) [`$135B`](../reference/modules/actor_room_tables.md#yamo_respawn_delay) | [`yamo_entry_preference`](../../src/actor_room_tables.asm#L94) [`$136F`](../reference/modules/actor_room_tables.md#yamo_entry_preference) |
|---|---|---|---|---|---|---|
| 0 | $68 | $A0 | $02 | $F0 | $EE | $80 |
| 1 | $78 | $A0 | $02 | $EE | $EE | $80 |
| 2 | $78 | $A0 | $00 | $EE | $EE | $00 |
| 3 | $00 | $00 | $00 | $00 | $00 | $00 |
| 4 | $70 | $70 | $80 | $C0 | $EE | $80 |
| 5 | $18 | $0C | $80 | $C0 | $60 | $02 |
| 6 | $30 | $30 | $02 | $A0 | $EE | $00 |
| 7 | $50 | $18 | $02 | $B0 | $C0 | $80 |
| 8 | $00 | $00 | $00 | $00 | $00 | $00 |
| 9 | $00 | $00 | $00 | $00 | $00 | $00 |
| 10 | $08 | $0C | $02 | $30 | $30 | $80 |
| 11 | $00 | $00 | $00 | $00 | $00 | $00 |
| 12 | $04 | $04 | $80 | $20 | $20 | $80 |
| 13 | $12 | $08 | $00 | $C0 | $EE | $00 |
| 14 | $08 | $08 | $02 | $20 | $30 | $00 |
| 15 | $08 | $08 | $00 | $30 | $50 | $00 |
| 16 | $08 | $08 | $80 | $20 | $30 | $02 |
| 17 | $12 | $08 | $00 | $C0 | $EE | $00 |
| 18 | $00 | $00 | $00 | $00 | $00 | $00 |
| 19 | $00 | $00 | $00 | $00 | $00 | $00 |

### 2.2 Table by table

The "Readers" column gives the address of the instruction that reads the table. A reader that no run executed is marked *(not run)*. All rows are **Code**, except where a row says **Observed**.

| Table | Address, name | Size | Layout | Readers and writers |
|---|---|---|---|---|
| **Map pointers** | [`room_map_ptrs_lo`](../../src/room_tables.asm#L125) [`$4B34`](../reference/modules/room_tables.md#room_map_ptrs_lo), [`room_map_ptrs_hi`](../../src/room_tables.asm#L129) [`$4B49`](../reference/modules/room_tables.md#room_map_ptrs_hi) | 21 + 21 bytes | The low and the high byte of the address of the map stream. Entry 20 = entry 19 (`$7FE0`). | [`draw_room_map_setup`](../../src/room_draw.asm#L132) [`$0AAF`](../../src/room_draw.asm#L134) and `$0AB4`, at each room draw. Entry 20 is never read: the index is [`current_room`](../../src/constants.asm#L28) <= 19. |
| **Map streams** | [`room00_map`](../../src/room_maps.asm#L6) [`$68F9`](../reference/modules/room_maps.md#room00_map) .. [`room19_map`](../../src/room_maps.asm#L787) [`$7FE0`](../reference/modules/room_maps.md#room19_map), up to `$817F` | 6279 bytes, 128-416 per room | RLE byte stream (section 3), ended by `$80`. The streams follow each other with no gap. | [`room_decode_next`](../../src/room_draw.asm#L154) [`$0AD7`](../reference/modules/room_draw.md#room_decode_next), [`room_literal_loop`](../../src/room_draw.asm#L161) [`$0AE3`](../reference/modules/room_draw.md#room_literal_loop), [`room_run_loop`](../../src/room_draw.asm#L181) [`$0B0B`](../reference/modules/room_draw.md#room_run_loop), through [`work_ptr_b`](../../src/constants.asm#L12) [`$06`](../reference/variables.md#work_ptr_b), at each room draw. |
| **Charset choice** | Code at [`draw_room`](../../src/room_draw.asm#L6) [`$0A9B-$0AAD`](../../src/room_draw.asm#L121), no table. The result is in [`room_charset_d018`](../../src/constants.asm#L109) [`$F2`](../reference/variables.md#room_charset_d018). | 1 byte of RAM | The `$D018` value: `$38` for rooms 0-9 (set 0 at `$A000`), `$3C` for room 18 (set 2 at `$B000`), `$3A` for the others (set 1 at `$A800`). `$3E` (set 3 at `$B800`) is set only by the room 18 defeat effect. | **Writers:** [`init_game_screen`](../../src/game_setup.asm#L6) [`$07E3`](../../src/game_setup.asm#L65) (`$38`), [`draw_room_map_setup`](../../src/room_draw.asm#L132) [`$0AAD`](../reference/modules/room_draw.md#draw_room_map_setup), [`room18_defeat_effect`](../../src/room_update.asm#L1019) [`$3DAF`](../reference/modules/room_update.md#room18_defeat_effect) (`$3E` at [`room18_effect_next_column`](../../src/room_update.asm#L1049) [`$3DFA`](../../src/room_update.asm#L1055), `$3C` at [`room18_effect_next_column`](../../src/room_update.asm#L1049) [`$3E09`](../../src/room_update.asm#L1062)). **Readers:** [`irq_playfield_top`](../../src/raster_irq_game.asm#L54) [`$492A`](../../src/raster_irq_game.asm#L63) each frame; [`game_frame_update`](../../src/frame_update.asm#L6) [`$15D0`](../../src/frame_update.asm#L24) each frame, which sets [`charset_hi`](../../src/constants.asm#L67) [`$7C`](../reference/variables.md#charset_hi) = `$A0`/`$A8`/`$B0`/`$B8` for the background collision test and for [`animate_scrolling_chars`](../../src/animated_chars.asm#L6) [`$2C70`](../reference/modules/animated_chars.md#animate_scrolling_chars). |
| **Colour RAM value** | [`room_char_colours`](../../src/room_colours.asm#L12) [`$47A0`](../reference/modules/room_colours.md#room_char_colours) | 20 bytes | A colour RAM byte, always `$F8-$FF`. Bit 3 = multicolour; bits 0-2 = the colour of the `%11` pixels. | [`draw_room`](../../src/room_draw.asm#L6) [`$09DC`](../../src/room_draw.asm#L22). The value fills `$D878-$DBFF` at each room draw. |
| **Band colour pointers** | [`room_split_colour_ptrs`](../../src/room_split_tables.asm#L6) [`$480B`](../reference/modules/room_split_tables.md#room_split_colour_ptrs) | 20 words | A pointer to 12 bytes = 4 triplets (`$D021`, `$D022`, `$D023`) in the pool `$47C8-$47F4`. | [`irq_frame_top`](../../src/raster_irq_game.asm#L6) [`$48EE`](../../src/raster_irq_game.asm#L26) and `$48F3`, each frame. |
| **Band colour pool** | [`room_band_colours`](../../src/room_colours.asm#L25) [`$47C8`](../reference/modules/room_colours.md#room_band_colours) (rooms 0-3), [`band_colours_rooms_4_6`](../../src/room_colours.asm#L29) [`$47D1`](../reference/modules/room_colours.md#band_colours_rooms_4_6), [`band_colours_rooms_7_9`](../../src/room_colours.asm#L31) [`$47D4`](../reference/modules/room_colours.md#band_colours_rooms_7_9), [`band_colours_rooms_10_12_14_16`](../../src/room_colours.asm#L33) [`$47D7`](../reference/modules/room_colours.md#band_colours_rooms_10_12_14_16), [`band_colours_room11`](../../src/room_colours.asm#L36) [`$47DD`](../reference/modules/room_colours.md#band_colours_room11), [`band_colours_room13`](../../src/room_colours.asm#L38) [`$47E0`](../reference/modules/room_colours.md#band_colours_room13), [`band_colours_room15`](../../src/room_colours.asm#L40) [`$47E3`](../reference/modules/room_colours.md#band_colours_room15), [`band_colours_room17`](../../src/room_colours.asm#L44) [`$47EC`](../reference/modules/room_colours.md#band_colours_room17), [`band_colours_room18`](../../src/room_colours.asm#L46) [`$47EF`](../reference/modules/room_colours.md#band_colours_room18), [`band_colours_room19`](../../src/room_colours.asm#L48) [`$47F2`](../reference/modules/room_colours.md#band_colours_room19) | 45 bytes (15 triplets) | `$Fx` colour bytes. The low nibble is the colour; the VIC ignores the high nibble. Each room reads 12 bytes from its pointer, so the groups overlap. | [`irq_copy_room_colours`](../../src/raster_irq_game.asm#L36) [`$4904`](../reference/modules/raster_irq_game.md#irq_copy_room_colours) copies 12 bytes to [`raster_colours`](../../src/constants.asm#L136) [`$0153-$015E`](../reference/variables.md#raster_colours) each frame. |
| **Raster line pointers** | [`room_raster_line_ptrs`](../../src/room_split_tables.asm#L16) [`$4833`](../reference/modules/room_split_tables.md#room_raster_line_ptrs) | 20 words | A pointer to a list of raster lines, ended by `$FD`. | [`irq_frame_top`](../../src/raster_irq_game.asm#L6) [`$48F8`](../../src/raster_irq_game.asm#L30) and `$48FD`, each frame. |
| **Raster line lists** | [`room_raster_split_lists`](../../src/room_colours.asm#L53) [`$47F9`](../reference/modules/room_colours.md#room_raster_split_lists) (room 0), [`raster_lines_room1`](../../src/room_colours.asm#L55) [`$47FC`](../reference/modules/room_colours.md#raster_lines_room1), [`raster_lines_room2`](../../src/room_colours.asm#L57) [`$47FF`](../reference/modules/room_colours.md#raster_lines_room2), [`raster_lines_room3`](../../src/room_colours.asm#L61) [`$4802`](../reference/modules/room_colours.md#raster_lines_room3), [`raster_lines_none`](../../src/room_colours.asm#L63) [`$4805`](../reference/modules/room_colours.md#raster_lines_none) (`$FD` only), [`raster_lines_rooms_10_12_14_16`](../../src/room_colours.asm#L65) [`$4806`](../reference/modules/room_colours.md#raster_lines_rooms_10_12_14_16), [`raster_lines_room15`](../../src/room_colours.asm#L67) [`$4808`](../reference/modules/room_colours.md#raster_lines_room15) | 18 bytes | 0-2 raster lines, then `$FD`. | [`irq_copy_room_colours`](../../src/raster_irq_game.asm#L36) [`$490D`](../../src/raster_irq_game.asm#L41) copies 4 bytes to [`current_raster_splits`](../../src/room_colours.asm#L50) [`$47F5-$47F8`](../reference/modules/room_colours.md#current_raster_splits) each frame. The bytes after the `$FD` are copied too, and nothing uses them. |
| **Atari colour set** (left over) | [`room_atari_colour_ptrs`](../../src/room_tables.asm#L86) [`$4AA8`](../reference/modules/room_tables.md#room_atari_colour_ptrs) -> [`room_atari_colour_records`](../../src/room_tables.asm#L96) [`$4AD0`](../reference/modules/room_tables.md#room_atari_colour_records) | 20 words; a pool of 100 bytes = 20 records of 5 | 20 bytes per room = 4 records of 5, for example `04 00 06 88 0E`. | [`draw_room`](../../src/room_draw.asm#L6) [`$0A87`](../../src/room_draw.asm#L111) and `$0A8C`, then [`draw_room_copy_atari_set`](../../src/room_draw.asm#L116) [`$0A93`](../reference/modules/room_draw.md#draw_room_copy_atari_set) copies 20 bytes to [`raster_colours`](../../src/constants.asm#L136) [`$0153-$0166`](../reference/variables.md#raster_colours) at each room draw. [`irq_frame_top`](../../src/raster_irq_game.asm#L6) writes `$0153-$015E` again on the next frame. Only [`save_raster_colours`](../../src/room_state.asm#L6) [`$102B`](../reference/modules/room_state.md#save_raster_colours) *(not run)* reads `$015F-$0166`. Section 2.3. |
| **Exit destination** | [`exit2_room`](../../src/room_tables.asm#L134) [`$4B5E`](../reference/modules/room_tables.md#exit2_room), [`exit3_room`](../../src/room_tables.asm#L140) [`$4B72`](../reference/modules/room_tables.md#exit3_room), [`exit4_room`](../../src/room_tables.asm#L146) [`$4B86`](../reference/modules/room_tables.md#exit4_room), [`exit5_room`](../../src/room_tables.asm#L151) [`$4B9A`](../reference/modules/room_tables.md#exit5_room) | 4 x 20 bytes | The destination room of map tile 2, 3, 4 or 5. | [`take_exit_char02`](../../src/background_touch.asm#L165) [`$2F43`](../../src/background_touch.asm#L170), [`take_exit_char03`](../../src/background_touch.asm#L177) [`$2F58`](../../src/background_touch.asm#L181), [`take_exit_char04`](../../src/background_touch.asm#L188) [`$2F6D`](../../src/background_touch.asm#L193), [`take_exit_char05`](../../src/background_touch.asm#L200) [`$2F82`](../../src/background_touch.asm#L204), when an actor touches an exit tile. |
| **Exit entry x** | [`exit2_x`](../../src/room_tables.asm#L175) [`$4BFE`](../reference/modules/room_tables.md#exit2_x), [`exit3_x`](../../src/room_tables.asm#L191) [`$4C26`](../reference/modules/room_tables.md#exit3_x), [`exit4_x`](../../src/room_tables.asm#L199) [`$4C4E`](../reference/modules/room_tables.md#exit4_x), [`exit5_x`](../../src/room_tables.asm#L208) [`$4C76`](../reference/modules/room_tables.md#exit5_x) | 4 x 20 bytes | [`actor_x`](../../src/constants.asm#L85) in the destination room, in multicolour pixels: sprite X = 2 * x. **0 = go on with the next group** (2 -> 3 -> 4 -> 5; group 5 has no next group). | [`take_exit_char02`](../../src/background_touch.asm#L165) [`$2F4C`](../../src/background_touch.asm#L174), [`take_exit_char03`](../../src/background_touch.asm#L177) [`$2F61`](../../src/background_touch.asm#L185), [`take_exit_char04`](../../src/background_touch.asm#L188) [`$2F76`](../../src/background_touch.asm#L197), [`take_exit_char05`](../../src/background_touch.asm#L200) [`$2F8B`](../../src/background_touch.asm#L208). |
| **Exit entry y** | [`exit2_y`](../../src/room_tables.asm#L187) [`$4C12`](../reference/modules/room_tables.md#exit2_y), [`exit3_y`](../../src/room_tables.asm#L195) [`$4C3A`](../reference/modules/room_tables.md#exit3_y), [`exit4_y`](../../src/room_tables.asm#L204) [`$4C62`](../reference/modules/room_tables.md#exit4_y), [`exit5_y`](../../src/room_tables.asm#L212) [`$4C8A`](../reference/modules/room_tables.md#exit5_y) | 4 x 20 bytes | [`actor_y`](../../src/constants.asm#L86). Sprite Y = y + `$1D`. | [`take_exit_char02`](../../src/background_touch.asm#L165) [`$2F48`](../../src/background_touch.asm#L172), [`take_exit_char03`](../../src/background_touch.asm#L177) [`$2F5D`](../../src/background_touch.asm#L183), [`take_exit_char04`](../../src/background_touch.asm#L188) [`$2F72`](../../src/background_touch.asm#L195), [`take_exit_char05`](../../src/background_touch.asm#L200) [`$2F87`](../../src/background_touch.asm#L206). |
| **Spawn point A** | [`room_spawn_x`](../../src/room_tables.asm#L156) [`$4BAE`](../reference/modules/room_tables.md#room_spawn_x), [`room_spawn_y`](../../src/room_tables.asm#L161) [`$4BC2`](../reference/modules/room_tables.md#room_spawn_y) | 2 x 20 bytes | The start position of Bruce, and spawn point A of the enemies. | [`init_actor`](../../src/actors.asm#L6) [`$0BE9`](../../src/actors.asm#L52) and `$0BED` (Bruce, the enemies, and every actor in the demo); [`respawn_in_room`](../../src/room_entry_traps.asm#L6) [`$321E`](../../src/room_entry_traps.asm#L11) and `$3222`; [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24E3`](../../src/object_actions.asm#L710) and `$24E7`. |
| **Spawn point B** | [`room_alt_spawn_x`](../../src/room_tables.asm#L166) [`$4BD6`](../reference/modules/room_tables.md#room_alt_spawn_x), [`room_alt_spawn_y`](../../src/room_tables.asm#L171) [`$4BEA`](../reference/modules/room_tables.md#room_alt_spawn_y) | 2 x 20 bytes | Spawn point B of the enemies. It is 0/0 in rooms 8, 9, 11, 13, 17, 18 and 19. | [`init_actor`](../../src/actors.asm#L6) [`$0C20`](../../src/actors.asm#L82) and `$0C24` ([`actor_use_spawn_b`](../../src/actors.asm#L80) [`$0C1E`](../reference/modules/actors.md#actor_use_spawn_b)). |
| **First spawn delays** | [`ninja_first_spawn_delay`](../../src/actor_room_tables.asm#L69) [`$130B`](../reference/modules/actor_room_tables.md#ninja_first_spawn_delay), [`yamo_first_spawn_delay`](../../src/actor_room_tables.asm#L84) [`$1347`](../reference/modules/actor_room_tables.md#yamo_first_spawn_delay) | 2 x 20 bytes | The start value of [`ninja_spawn_timer`](../../src/constants.asm#L47) [`$5D`](../reference/variables.md#ninja_spawn_timer) and [`yamo_spawn_timer`](../../src/constants.asm#L48) [`$5E`](../reference/variables.md#yamo_spawn_timer). The timers count passes ([`tick_enemy_timers`](../../src/actors.asm#L304) [`$0DA4`](../reference/modules/actors.md#tick_enemy_timers)). | [`draw_room_spawn_timers`](../../src/room_draw.asm#L81) [`$0A4E`](../reference/modules/room_draw.md#draw_room_spawn_timers) and `$0A53`, at each room draw. |
| **Respawn delays** | [`ninja_respawn_delay`](../../src/actor_room_tables.asm#L74) [`$131F`](../reference/modules/actor_room_tables.md#ninja_respawn_delay), [`yamo_respawn_delay`](../../src/actor_room_tables.asm#L89) [`$135B`](../reference/modules/actor_room_tables.md#yamo_respawn_delay) | 2 x 20 bytes | The timer value after a spawn. | [`try_spawn_yamo`](../../src/actors.asm#L207) [`$0D20`](../../src/actors.asm#L216), [`try_spawn_ninja`](../../src/actors.asm#L315) [`$0DE4`](../../src/actors.asm#L341). [`reset_yamo_timer`](../../src/actors.asm#L243) [`$0D46`](../reference/modules/actors.md#reset_yamo_timer) and [`reset_ninja_timer`](../../src/actors.asm#L274) [`$0D76`](../reference/modules/actors.md#reset_ninja_timer) read them through a self-modified operand ([`reset_yamo_timer`](../../src/actors.asm#L243) [`$0D55`](../../src/actors.asm#L253), [`reset_ninja_timer`](../../src/actors.asm#L274) [`$0D85`](../../src/actors.asm#L284)). |
| **Entry preference** | [`ninja_entry_preference`](../../src/actor_room_tables.asm#L79) [`$1333`](../reference/modules/actor_room_tables.md#ninja_entry_preference), [`yamo_entry_preference`](../../src/actor_room_tables.asm#L94) [`$136F`](../reference/modules/actor_room_tables.md#yamo_entry_preference) | 2 x 20 bytes | 0 = spawn point A or B at random. Not 0 = in 3 of 4 cases (random < `$C0`) the sign of [`yamo_entry_preference`](../../src/actor_room_tables.asm#L94) chooses: positive = A, negative = B. The Ninja path also reads the **Yamo** table for the sign ([`actor_pick_spawn_ninja`](../../src/actors.asm#L86) [`$0C38`](../../src/actors.asm#L93)). | [`actor_pick_spawn`](../../src/actors.asm#L61) [`$0C04`](../../src/actors.asm#L67) and `$0C10`, [`actor_pick_spawn_ninja`](../../src/actors.asm#L86) [`$0C2C`](../../src/actors.asm#L88) and `$0C38`, at each enemy spawn. |
| **No-combat flag** | [`room_no_combat_flags`](../../src/room_tables.asm#L217) [`$4C9E`](../reference/modules/room_tables.md#room_no_combat_flags) | 20 bytes | 0 or `$FF`. `$FF` in rooms 3, 8, 9, 11, 13, 17, 18 and 19. | [`draw_room`](../../src/room_draw.asm#L6) [`$0A41`](../../src/room_draw.asm#L74) copies it to [`room_without_enemies`](../../src/constants.asm#L65) [`$7A`](../reference/variables.md#room_without_enemies); a value that is not 0 also clears [`enemy_entry_x`](../../src/constants.asm#L79) [`$8B`](../reference/variables.md#enemy_entry_x). [`main_loop`](../../src/main_loop.asm#L6) [`$1BF1`](../../src/main_loop.asm#L27) (through `$7A`) then skips [`tick_enemy_timers`](../../src/actors.asm#L304) and the spawn calls. [`main_loop`](../../src/main_loop.asm#L6) [`$1C1E`](../../src/main_loop.asm#L51) (the table itself) skips [`check_sprite_collisions`](../../src/combat_hits.asm#L6) [`$29C3`](../reference/modules/combat_hits.md#check_sprite_collisions). |
| **Lantern counts** | [`room_lantern_counts`](../../src/room_tables.asm#L229) [`$4CCE`](../reference/modules/room_tables.md#room_lantern_counts) | 20 bytes | The lanterns of each room, 90 in all. | [`reset_room_table_2a`](../../src/room_state.asm#L101) [`$10C7`](../../src/room_state.asm#L104) copies it to [`room_lanterns_left`](../../src/constants.asm#L29) [`$2A-$3D`](../reference/variables.md#room_lanterns_left) at game start ([`init_game_vars`](../../src/game_vars.asm#L6) [`$0F72`](../reference/modules/game_vars.md#init_game_vars)) and after the ending ([`room19_congratulations_update`](../../src/final_room.asm#L34) [`$4272`](../reference/modules/final_room.md#room19_congratulations_update); **Observed** in the `room_special` run). |
| **Lantern lists** | [`lantern_list_ptrs`](../../src/room_tables.asm#L238) [`$4CE2`](../reference/modules/room_tables.md#lantern_list_ptrs) -> [`lantern_list_room00`](../../src/room_tables.asm#L248) [`$4D0C`](../reference/modules/room_tables.md#lantern_list_room00) .. [`lantern_list_room20`](../../src/room_tables.asm#L382) [`$4E90`](../reference/modules/room_tables.md#lantern_list_room20) | 21 words; records of 4 bytes | A record: [state (not 0 = present), the cell drawn when the lantern is taken (bit 7 is ignored), column 0-39, **text row** (map row = text row - 2)]. A byte with bit 7 set ends the list. Rooms 13, 19 and 20 hold one placeholder record `01 00 00 00`. Entry 20 is never read: each reader indexes by a room 0-19 ([`swap_player_lantern_flags`](../../src/game_vars.asm#L76) [`$0FED`](../reference/modules/game_vars.md#swap_player_lantern_flags) stops at `cmp #$14`). | [`redraw_taken_lanterns`](../../src/lanterns.asm#L63) [`$3372`](../../src/lanterns.asm#L67) (room draw); [`collect_lantern_at`](../../src/lanterns.asm#L6) [`$3328`](../../src/lanterns.asm#L14) (lantern touched); [`reset_room_lanterns`](../../src/lanterns.asm#L138) [`$33DA`](../reference/modules/lanterns.md#reset_room_lanterns) (game start); [`swap_room_object_bytes`](../../src/game_vars.asm#L93) [`$1007`](../reference/modules/game_vars.md#swap_room_object_bytes) (change of player). |
| **Lanterns left (RAM)** | [`room_lanterns_left`](../../src/constants.asm#L29) [`$2A-$3D`](../reference/variables.md#room_lanterns_left) | 20 bytes | The count of each room. | [`draw_room_special`](../../src/room_draw.asm#L34) [`$09FC`](../../src/room_draw.asm#L38) (rooms 12, 14 and 16, for the room 11 diversion); [`collect_lantern_at`](../../src/lanterns.asm#L6) [`$3365`](../../src/lanterns.asm#L56) (decrement); the room frame handlers (passages open). |
| **Room init handlers** | [`room_setup_handlers`](../../src/room_tables.asm#L401) [`$4E9C`](../reference/modules/room_tables.md#room_setup_handlers) | 20 words, RTS addresses (target - 1) | Run once per room draw. | [`dispatch_room_init`](../../src/lanterns.asm#L110) [`$33C1`](../../src/lanterns.asm#L120) and `$33C5`. |
| **Room frame handlers** | [`room_frame_handlers`](../../src/room_tables.asm#L411) [`$4EC4`](../reference/modules/room_tables.md#room_frame_handlers) | 20 words, RTS addresses | Run once at the end of [`draw_room`](../../src/room_draw.asm#L6), then on each pass. | [`run_room_update`](../../src/room_update.asm#L571) [`$3A73`](../../src/room_update.asm#L575) and `$3A77`. |
| **Room script variables (RAM)** | [`room_script_vars`](../../src/room_tables.asm#L390) [`$4E97-$4E9B`](../reference/modules/room_tables.md#room_script_vars) | 5 bytes | The counters and one-shot flags of the room handlers. | Cleared by [`dispatch_room_init`](../../src/lanterns.asm#L110) [`$33B3`](../reference/modules/lanterns.md#dispatch_room_init) before each init handler. Their use is in [rooms_10_19.md](rooms_10_19.md). |
| **Entry bonus flags (RAM)** | [`room_entry_bonus_flags`](../../src/constants.asm#L138) [`$0300`](../reference/variables.md#room_entry_bonus_flags) | 40 bytes, index room * 2 + player | 1 = the 2000-point bonus of the first entry is still due. [`init_game_vars`](../../src/game_vars.asm#L6) [`$0FA8`](../../src/game_vars.asm#L37) sets all to 1, then clears room 0 for both players ([`init_game_vars`](../../src/game_vars.asm#L6) [`$0FB0`](../../src/game_vars.asm#L41)). | [`draw_room_bonus`](../../src/room_draw.asm#L46) [`$0A14`](../../src/room_draw.asm#L51) (test), `$0A19` (LSR clears it). [`reset_player_room_flags`](../../src/room_state.asm#L123) [`$10E0`](../reference/modules/room_state.md#reset_player_room_flags) sets them again (**Observed** in the `room_special` ending). |
| **Saved lantern flags (RAM)** | [`saved_lantern_flags`](../../src/casbuf.asm#L7) [`$0340`](../reference/modules/casbuf.md#saved_lantern_flags) | 97 bytes (92 used) | The lantern states of the waiting player, one byte per record of rooms 0-19. | [`swap_player_lantern_flags`](../../src/game_vars.asm#L76) [`$0FED`](../reference/modules/game_vars.md#swap_player_lantern_flags) (change of player). |
| **Unreferenced** | `$4CBA-$4CCD` | 20 bytes | `32 1F 1E 1A 18 1D 1B 33 35 30 72 5F 5E 5A 58 5D 5B 73 75 70`. The second 10 bytes are the first 10 plus `$40`. | No reader in the code or in the coverage. The meaning is not known. |

**Behaviour that the code ties to a room number** (no table, **Code**):
- [`check_exit_direction`](../../src/background_touch.asm#L392) [`$30D4`](../reference/modules/background_touch.md#check_exit_direction): room 11 takes exits in any direction.
- [`actor_char_coords`](../../src/actor_movement.asm#L6) [`$1C39`](../reference/modules/actor_movement.md#actor_char_coords): in room 13 the actor y gets +4.
- [`touch_deadly_char`](../../src/background_touch.asm#L316) [`$304B`](../reference/modules/background_touch.md#touch_deadly_char): no deadly chars in room 18.
- [`touch_char_66`](../../src/background_touch.asm#L122) [`$2EFA`](../reference/modules/background_touch.md#touch_char_66): char `$66` is deadly from room 10 on.
- [`touch_bonus_fall_chars`](../../src/background_touch.asm#L110) [`$2EEA`](../reference/modules/background_touch.md#touch_bonus_fall_chars): chars `$2D`/`$2E` are the bonus-fall object only in room 16.
- [`game_frame_update`](../../src/frame_update.asm#L6) [`$15AD`](../../src/frame_update.asm#L10): the sound effect players get the room in X.
- [`animate_scrolling_chars`](../../src/animated_chars.asm#L6) [`$2C70`](../reference/modules/animated_chars.md#animate_scrolling_chars): one set of texture patterns for rooms 0-9 and one for rooms 10-19.
- The charset choice at [`draw_room`](../../src/room_draw.asm#L6) [`$0A9B`](../../src/room_draw.asm#L121).
- The room 11 diversion at [`draw_room_special`](../../src/room_draw.asm#L34) [`$09F6`](../reference/modules/room_draw.md#draw_room_special) (section 4.3).

### 2.3 The Atari colour set ([`room_atari_colour_ptrs`](../../src/room_tables.asm#L86) [`$4AA8`](../reference/modules/room_tables.md#room_atari_colour_ptrs))

**Code.**
- The pool [`room_atari_colour_records`](../../src/room_tables.asm#L96) [`$4AD0-$4B33`](../reference/modules/room_tables.md#room_atari_colour_records) holds 20 records of 5 bytes. The rooms point at it in the same groups as [`room_split_colour_ptrs`](../../src/room_split_tables.asm#L6) [`$480B`](../reference/modules/room_split_tables.md#room_split_colour_ptrs):

  | Rooms | Pointer |
  |---|---|
  | 0-3 | `$4AD0` |
  | 4-6 | `$4AE4` |
  | 7-9 | `$4AE9` |
  | 10, 12, 14, 16 | `$4AEE` |
  | 11 | `$4AFD` |
  | 13 | `$4B02` |
  | 15 | `$4B0C` |
  | 17 | `$4B1B` |
  | 18 | `$4B25` |
  | 19 | `$4B2A` |

- Each room reads 20 bytes. For room 19 (`$4B2A`) the 20 bytes run past the pool into [`room_map_ptrs_lo`](../../src/room_tables.asm#L125) [`$4B34-$4B3D`](../reference/modules/room_tables.md#room_map_ptrs_lo).
- Some records:

  | Address | Bytes |
  |---|---|
  | `$4AD0` | `04 00 06 88 0E` |
  | `$4AD5` | `04 00 0A 0E 34` |
  | `$4AE4` | `84 00 70 0E 60` |
  | `$4B25` | `00 82 82 68 8C` |

- [`draw_room_copy_atari_set`](../../src/room_draw.asm#L116) [`$0A93`](../reference/modules/room_draw.md#draw_room_copy_atari_set) copies the 20 bytes to [`raster_colours`](../../src/constants.asm#L136) [`$0153-$0166`](../reference/variables.md#raster_colours). The next [`irq_frame_top`](../../src/raster_irq_game.asm#L6) [`$48C1`](../reference/modules/raster_irq_game.md#irq_frame_top) writes the C64 triplets over `$0153-$015E`. Only [`save_raster_colours`](../../src/room_state.asm#L6) [`$102B`](../reference/modules/room_state.md#save_raster_colours) reads `$015F-$0166`. The idle screen saver calls it ([`game_frame_update`](../../src/frame_update.asm#L6) [`$163C`](../../src/frame_update.asm#L88)), and no run reached it.

**Observed.** The coverage shows reads of `$015F-$0166`.

**Conclusions.**
- The coverage reads come from the dummy read of `STA abs,Y` at [`draw_room_copy_atari_set`](../../src/room_draw.asm#L116) [`$0A95`](../../src/room_draw.asm#L118): the 6510 reads the target address before it writes. They are no reads of the game.
- 5 bytes per band is the number of the Atari playfield colour registers (COLPF0-COLPF3 and COLBK). Values such as `$88`, `$0E` and `$34` are typical Atari hue and luminance values.
- The table is the colour set of the Atari version. The C64 version copies it, and the copy has no effect on the picture.

---

## 3. The map format

### 3.1 Where the data is

- The pointers: [`room_map_ptrs_lo`](../../src/room_tables.asm#L125) [`$4B34`](../reference/modules/room_tables.md#room_map_ptrs_lo) and [`room_map_ptrs_hi`](../../src/room_tables.asm#L129) [`$4B49`](../reference/modules/room_tables.md#room_map_ptrs_hi), indexed by [`current_room`](../../src/constants.asm#L28) [`$29`](../reference/variables.md#current_room).
- The data: [`room00_map`](../../src/room_maps.asm#L6) [`$68F9`](../reference/modules/room_maps.md#room00_map) .. [`room19_map`](../../src/room_maps.asm#L787) [`$7FE0`](../reference/modules/room_maps.md#room19_map), up to `$817F`.
- The decoder: [`room_decode_next`](../../src/room_draw.asm#L154) [`$0AD7`](../reference/modules/room_draw.md#room_decode_next) .. [`room_run_store`](../../src/room_draw.asm#L185) [`$0B12`](../reference/modules/room_draw.md#room_run_store) inside [`draw_room`](../../src/room_draw.asm#L6) [`$09BC`](../reference/modules/room_draw.md#draw_room).

### 3.2 The byte layout

| Byte | Meaning |
|---|---|
| `$80` | End of the map. |
| `$81-$FF` | Literal: the next `b & $7F` bytes are cells, one after the other. |
| `$01-$7F` | Run: the next byte is one cell, `b` times. |
| `$00` | Run of 256 cells (no map uses it). |

A cell byte:

| Bits | Meaning |
|---|---|
| 0-6 | The tile `t`. The top char of the cell is `t`, the bottom char is `t | $80`. |
| 7 | 1 = colour RAM `$F8` for both chars (multicolour, `%11` pixels black). 0 = the room colour from [`room_char_colours`](../../src/room_colours.asm#L12) [`$47A0`](../reference/modules/room_colours.md#room_char_colours) stays. |

The cells fill the map row by row, 40 cells per row, 11 rows, from screen row 3. The stream has no row marks. A run can cross the end of a row, because only [`draw_count`](../../src/constants.asm#L110) [`$F3`](../reference/variables.md#draw_count) counts the columns (**Code**).

### 3.3 The decoder

The registers and variables:

| Register or variable | Role |
|---|---|
| Y | Always 0. Each access is `(zp),Y` with Y = 0. |
| X | The count of a run or a literal. |
| A | The cell value. |
| [`work_ptr_b`](../../src/constants.asm#L12) [`$06`](../reference/variables.md#work_ptr_b) | The stream pointer. |
| [`work_ptr_a`](../../src/constants.asm#L11) [`$04`](../reference/variables.md#work_ptr_a) | The top-char pointer. |
| [`work_ptr_c`](../../src/constants.asm#L13) [`$08`](../reference/variables.md#work_ptr_c) | The bottom-char pointer. |
| [`colour_ptr_a`](../../src/constants.asm#L15) [`$10`](../reference/variables.md#colour_ptr_a) | The colour RAM pointer of the top char. |
| [`colour_ptr_b`](../../src/constants.asm#L16) [`$12`](../reference/variables.md#colour_ptr_b) | The colour RAM pointer of the bottom char. |
| [`draw_count`](../../src/constants.asm#L110) [`$F3`](../reference/variables.md#draw_count) | The columns left in the current map row, minus 1. |

The helpers:

| Helper | Action |
|---|---|
| [`inc_ptr_04`](../../src/pointer_helpers.asm#L6) [`$4786`](../reference/modules/pointer_helpers.md#inc_ptr_04) | `$04/$05` + 1 |
| [`inc_ptr_06`](../../src/pointer_helpers.asm#L13) [`$478D`](../reference/modules/pointer_helpers.md#inc_ptr_06) | `$06/$07` + 1 |
| [`inc_ptr_08`](../../src/pointer_helpers.asm#L20) [`$4794`](../reference/modules/pointer_helpers.md#inc_ptr_08) | `$08/$09` + 1 |
| [`inc_colour_ptr_a`](../../src/room_draw.asm#L219) [`$0B51`](../reference/modules/room_draw.md#inc_colour_ptr_a) | `$10/$11` + 1 |
| [`inc_colour_ptr_b`](../../src/room_draw.asm#L226) [`$0B58`](../reference/modules/room_draw.md#inc_colour_ptr_b) | `$12/$13` + 1 |
| [`set_tile_colour_f8`](../../src/room_draw.asm#L233) [`$0B5F`](../reference/modules/room_draw.md#set_tile_colour_f8) | Writes `$F8` through `$10` and `$12`, returns A AND `$7F`. |
| [`room_draw_next_cell`](../../src/charset_expand.asm#L6) [`$485B`](../reference/modules/charset_expand.md#room_draw_next_cell) | The row advance (below). |

The bytes at `$0B4A` (`E6 06 D0 02 E6 07 60`) are an unused copy of [`inc_ptr_06`](../../src/pointer_helpers.asm#L13). No code jumps there (**Code**).

```
room_decode_next:                          ; $0AD7
  b = (work_ptr_b)[0]
  if b < $80: goto room_run                ; BPL
  n = b & $7F
  if n == 0: goto room_decode_done         ; $80 = end of the map
  X = n; inc_ptr_06()                      ; skip the control byte
room_literal_loop:                         ; $0AE3   n different cells follow
  v = (work_ptr_b)[0]
  if v & $80: v = set_tile_colour_f8(v)    ; colour RAM top and bottom = $F8, v &= $7F
room_literal_store:                        ; $0AEA
  (work_ptr_a)[0] = v                      ; top char = tile
  (work_ptr_c)[0] = v | $80                ; bottom char = tile + 128
  inc_ptr_04(); inc_ptr_06(); inc_ptr_08(); inc_colour_ptr_a(); inc_colour_ptr_b()
  room_draw_next_cell()
  X -= 1; if X != 0: goto room_literal_loop
  goto room_decode_next
room_run:                                  ; $0B07   the next byte b times
  X = b; inc_ptr_06()                      ; point at the cell value
room_run_loop:                             ; $0B0B
  v = (work_ptr_b)[0]                      ; the same byte each time
  if v & $80: v = set_tile_colour_f8(v)
room_run_store:                            ; $0B12
  (work_ptr_a)[0] = v; (work_ptr_c)[0] = v | $80
  inc_ptr_04(); inc_ptr_08(); inc_colour_ptr_a(); inc_colour_ptr_b()   ; no inc_ptr_06 here
  room_draw_next_cell()
  X -= 1; if X != 0: goto room_run_loop
  inc_ptr_06()                             ; skip the value byte
  goto room_decode_next
```

**The colour rule (Code).** Only a cell with bit 7 writes colour RAM, and it always writes `$F8`. A cell without bit 7 keeps the room colour from the fill at [`draw_room_fill_colour`](../../src/room_draw.asm#L24) [`$09E1`](../reference/modules/room_draw.md#draw_room_fill_colour).

**[`room_draw_next_cell`](../../src/charset_expand.asm#L6) [`$485B`](../reference/modules/charset_expand.md#room_draw_next_cell) (Code):**
```
push A
draw_count -= 1
if draw_count < 0:                         ; after the 40th cell of a row
    draw_count = $27
    work_ptr_a += 40; work_ptr_c += 40; colour_ptr_a += 40; colour_ptr_b += 40
pop A; return
```
After 40 cells the four pointers have each moved 40 bytes, so they already point one screen row lower. The extra 40 skips the row of the other half of the cell:
- the top pointer goes from screen row 3+2R to 3+2R+2;
- the bottom pointer goes from screen row 4+2R to 4+2R+2.

### 3.4 Size and overrun

Decoded from the image (**Code**):
- The maps of rooms 0-3, 5, 6, 8, 9, 11, 12, 14-16 and 19 hold 440 cells (11 rows x 40).
- The maps of rooms 4, 7, 10, 13, 17 and 18 hold 442 cells. The two extra cells are tile 0 without bit 7. They go to `$8FE8/$8FE9`, in the screen RAM after the 1000 visible bytes, and as `$80` to `$9010/$9011`, inside collision mask 0 at `$9000`.
- The two extra cells write no colour RAM, because bit 7 is clear.
- `$8FE8`/`$9010` is text row 13 of the text row tables (section 6.3).

**Cost (Code).** A literal cell costs 6 JSRs, plus [`set_tile_colour_f8`](../../src/room_draw.asm#L233) for a cell with bit 7. A run cell costs 5 JSRs. Room 0 decodes 272 stream bytes into 440 cells.

### 3.5 The assets

`assets/rooms/roomNN.png` shows each room as [`draw_room`](../../src/room_draw.asm#L6) leaves it: the map, the colour RAM and the colour RAM changes of the init handler. `assets/rooms/roomNN.json` holds the decoded cells, the colours, the bands, the exits, the spawn points, the enemy delays, the lantern list and the handlers.

![Room 0 as draw_room leaves it](../../assets/rooms/room00.png)

Room 0 after the draw: the map of 40 x 11 cells in the three colour bands of rooms 0-2.

---

## 4. [`draw_room`](../../src/room_draw.asm#L6) [`$09BC`](../reference/modules/room_draw.md#draw_room) step by step

### 4.1 The callers

| Caller | Address | State before the call |
|---|---|---|
| [`start_game`](../../src/title.asm#L185) | [`start_game`](../../src/title.asm#L185) [`$074C`](../../src/title.asm#L210) | SEI at [`start_game`](../../src/title.asm#L185) [`$070E`](../reference/modules/title.md#start_game), display blanked. [`init_game_vars`](../../src/game_vars.asm#L6) [`$0F72`](../reference/modules/game_vars.md#init_game_vars) cleared zero page `$03-$F5`, so [`current_room`](../../src/constants.asm#L28) is 0. [`init_game_screen`](../../src/game_setup.asm#L6) [`$0763`](../reference/modules/game_setup.md#init_game_screen) built the IRQ chain and placed Bruce. |
| [`start_demo`](../../src/restart.asm#L24) | [`start_demo`](../../src/restart.asm#L24) [`$056D`](../../src/restart.asm#L49) | SEI at [`start_demo`](../../src/restart.asm#L24) [`$0531`](../reference/modules/restart.md#start_demo), then the same as [`start_game`](../../src/title.asm#L185). |
| [`enter_room`](../../src/background_touch.asm#L210) | [`enter_room`](../../src/background_touch.asm#L210) [`$2FCC`](../../src/background_touch.asm#L248) | SEI at [`enter_room`](../../src/background_touch.asm#L210) [`$2FC5`](../../src/background_touch.asm#L244), the stack reset to `$FF`, [`current_room`](../../src/constants.asm#L28) = the destination. Section 9. |

**Code:** each caller disables the IRQs before the call. The raster chain stops for the whole draw, and [`draw_room`](../../src/room_draw.asm#L6) also blanks the display.

### 4.2 The steps

All steps are **Code**.

1. **Blank.** [`draw_room`](../../src/room_draw.asm#L6) [`$09BC`](../reference/modules/room_draw.md#draw_room) clears bit 4 of `$D011` (the screen shows only the border colour). It keeps the enable bits of sprites 0-4 in [`saved_sprite_enable`](../../src/constants.asm#L33) [`$47`](../reference/variables.md#saved_sprite_enable) ([`draw_room`](../../src/room_draw.asm#L6) [`$09C4`](../../src/room_draw.asm#L10)) and writes 0 to `$D015`.
2. **Clear screen row 0.** [`draw_room_clear_row0`](../../src/room_draw.asm#L17) [`$09D4`](../reference/modules/room_draw.md#draw_room_clear_row0) writes `$20` to [`screen_ram`](../../src/vic_bank2.asm#L376) [`$8C00-$8C27`](../reference/modules/vic_bank2.md#screen_ram), the version-line row. The status line is screen row 1.
3. **Fill the colour RAM.** [`draw_room`](../../src/room_draw.asm#L6) [`$09DC`](../../src/room_draw.asm#L22) reads [`room_char_colours`](../../src/room_colours.asm#L12) [`$47A0`](../reference/modules/room_colours.md#room_char_colours) for the room. [`draw_room_fill_colour`](../../src/room_draw.asm#L24) [`$09E1`](../reference/modules/room_draw.md#draw_room_fill_colour) writes it to `$D878+X`, `$D900+X`, `$DA00+X` and `$DB00+X` for X = 0-255: `$D878-$DBFF`, the colour RAM of screen rows 3-24 and the unused `$DBE8-$DBFF`.
4. **Stop the effects.** [`clear_fireball_shapes`](../../src/fireballs.asm#L152) [`$423F`](../reference/modules/fireballs.md#clear_fireball_shapes) and [`silence_all_sound`](../../src/sound_effects.asm#L55) [`$255E`](../reference/modules/sound_effects.md#silence_all_sound).
5. **Room 11 diversion.** [`draw_room_special`](../../src/room_draw.asm#L34) [`$09F6`](../reference/modules/room_draw.md#draw_room_special): if the room is 11 and [`room_lanterns_left+12`](../../src/constants.asm#L29) [`$36`](../reference/variables.md#room_lanterns_left), [`room_lanterns_left+14`](../../src/constants.asm#L29) [`$38`](../reference/variables.md#room_lanterns_left) and [`room_lanterns_left+16`](../../src/constants.asm#L29) [`$3A`](../reference/variables.md#room_lanterns_left) are all 0, it restores `$D015` from [`saved_sprite_enable`](../../src/constants.asm#L33) and jumps to [`respawn_in_room`](../../src/room_entry_traps.asm#L6) [`$3217`](../reference/modules/room_entry_traps.md#respawn_in_room) with X = 13 (section 4.3).
6. **Entry bonus.** [`draw_room_bonus`](../../src/room_draw.asm#L46) [`$0A0E`](../reference/modules/room_draw.md#draw_room_bonus): X = room * 2 + [`current_player`](../../src/constants.asm#L10) [`$03`](../reference/variables.md#current_player). If [`room_entry_bonus_flags`](../../src/constants.asm#L138) [`$0300`](../reference/variables.md#room_entry_bonus_flags)+X is not 0, an LSR clears it ([`draw_room_bonus`](../../src/room_draw.asm#L46) [`$0A19`](../../src/room_draw.asm#L53)) and [`add_score`](../../src/score.asm#L47) [`$3175`](../reference/modules/score.md#add_score) adds `$07` to score byte 1 and `$D0` to score byte 2: `$0007D0` = 2000 points.
7. **Reset the room state.** [`draw_room_reset`](../../src/room_draw.asm#L61) [`$0A2A`](../reference/modules/room_draw.md#draw_room_reset):
   - [`draw_room_clear_moves`](../../src/room_draw.asm#L64) [`$0A2E`](../reference/modules/room_draw.md#draw_room_clear_moves) clears `$4F57-$4FDA`: [`actor_move_counters`](../../src/actor_vars.asm#L227) [`$4F57`](../reference/modules/actor_vars.md#actor_move_counters), [`actor_moved_left`](../../src/actor_vars.asm#L233) [`$4F5D`](../reference/modules/actor_vars.md#actor_moved_left), [`actor_moved_right`](../../src/actor_vars.asm#L236) [`$4F60`](../reference/modules/actor_vars.md#actor_moved_right) and the move history;
   - [`room_timer_lo`](../../src/constants.asm#L76) [`$87`](../reference/variables.md#room_timer_lo), [`room_timer`](../../src/constants.asm#L77) [`$88`](../reference/variables.md#room_timer) and [`scroll_direction`](../../src/constants.asm#L54) [`$65`](../reference/variables.md#scroll_direction) = 0;
   - [`anim_speed_index`](../../src/variables.asm#L43) [`$4321`](../reference/modules/variables.md#anim_speed_index) = 7;
   - [`room_without_enemies`](../../src/constants.asm#L65) [`$7A`](../reference/variables.md#room_without_enemies) = [`room_no_combat_flags`](../../src/room_tables.asm#L217) [`$4C9E`](../reference/modules/room_tables.md#room_no_combat_flags) of the room; if it is not 0, [`enemy_entry_x`](../../src/constants.asm#L79) [`$8B`](../reference/variables.md#enemy_entry_x) and [`enemy_entry_x+1`](../../src/constants.asm#L79) [`$8C`](../reference/variables.md#enemy_entry_x) = 0, so no enemy follows Bruce into this room.
8. **Enemy timers.** [`draw_room_spawn_timers`](../../src/room_draw.asm#L81) [`$0A4E`](../reference/modules/room_draw.md#draw_room_spawn_timers):
   - [`ninja_spawn_timer`](../../src/constants.asm#L47) [`$5D`](../reference/variables.md#ninja_spawn_timer) = [`ninja_first_spawn_delay`](../../src/actor_room_tables.asm#L69) [`$130B`](../reference/modules/actor_room_tables.md#ninja_first_spawn_delay) of the room, [`yamo_spawn_timer`](../../src/constants.asm#L48) [`$5E`](../reference/variables.md#yamo_spawn_timer) = [`yamo_first_spawn_delay`](../../src/actor_room_tables.asm#L84) [`$1347`](../reference/modules/actor_room_tables.md#yamo_first_spawn_delay) of the room;
   - if [`game_cycle`](../../src/constants.asm#L30) [`$40`](../reference/variables.md#game_cycle) is not 0, both = 3 (**Observed** executed in the `room_special` ending);
   - [`draw_room_human_yamo_delay`](../../src/room_draw.asm#L91) [`$0A62`](../reference/modules/room_draw.md#draw_room_human_yamo_delay): if [`human_opponent_mode`](../../src/variables.asm#L11) [`$42CA`](../reference/modules/variables.md#human_opponent_mode) is not 0, [`yamo_spawn_timer`](../../src/constants.asm#L48) = 8.
9. **Reset Bruce.** [`draw_room_reset_bruce`](../../src/room_draw.asm#L97) [`$0A6B`](../reference/modules/room_draw.md#draw_room_reset_bruce): [`actor_contact`](../../src/constants.asm#L92) [`$B6`](../reference/variables.md#actor_contact) = 1, [`actor_state_timer`](../../src/constants.asm#L98) [`$CE`](../reference/variables.md#actor_state_timer) = 4, [`actor_state`](../../src/constants.asm#L95) [`$BF`](../reference/variables.md#actor_state) = 0, [`actor_step_delay`](../../src/constants.asm#L122) [`$0106`](../reference/variables.md#actor_step_delay) = 0. [`tile_anim_timer`](../../src/actor_vars.asm#L285) [`$4FDE-$4FE0`](../reference/modules/actor_vars.md#tile_anim_timer) = 0 frees the three floor trap slots.
10. **Atari colour set.** [`draw_room`](../../src/room_draw.asm#L6) [`$0A83-$0A91`](../../src/room_draw.asm#L108) sets [`work_ptr_b`](../../src/constants.asm#L12) from [`room_atari_colour_ptrs`](../../src/room_tables.asm#L86) [`$4AA8`](../reference/modules/room_tables.md#room_atari_colour_ptrs); [`draw_room_copy_atari_set`](../../src/room_draw.asm#L116) [`$0A93`](../reference/modules/room_draw.md#draw_room_copy_atari_set) copies 20 bytes to [`raster_colours`](../../src/constants.asm#L136) [`$0153`](../reference/variables.md#raster_colours) (section 2.3).
11. **Charset.** [`draw_room`](../../src/room_draw.asm#L6) [`$0A9B-$0AAB`](../../src/room_draw.asm#L121): A = `$38`; for rooms 10 and up, A = `$3C` for room 18, else `$3A`. [`draw_room_map_setup`](../../src/room_draw.asm#L132) [`$0AAD`](../reference/modules/room_draw.md#draw_room_map_setup) stores it in [`room_charset_d018`](../../src/constants.asm#L109) [`$F2`](../reference/variables.md#room_charset_d018).
12. **Map set-up.** [`draw_room_map_setup`](../../src/room_draw.asm#L132) [`$0AAD`](../reference/modules/room_draw.md#draw_room_map_setup): [`work_ptr_b`](../../src/constants.asm#L12) [`$06`](../reference/variables.md#work_ptr_b) = the map of the room; [`work_ptr_a`](../../src/constants.asm#L11) [`$04`](../reference/variables.md#work_ptr_a) = `$8C78` (screen row 3, top chars) and [`colour_ptr_a`](../../src/constants.asm#L15) [`$10`](../reference/variables.md#colour_ptr_a) = `$D878`; [`work_ptr_c`](../../src/constants.asm#L13) [`$08`](../reference/variables.md#work_ptr_c) = `$8CA0` (screen row 4, bottom chars) and [`colour_ptr_b`](../../src/constants.asm#L16) [`$12`](../reference/variables.md#colour_ptr_b) = `$D8A0`; [`draw_count`](../../src/constants.asm#L110) [`$F3`](../reference/variables.md#draw_count) = `$27` (39 = the columns left minus 1); Y = 0.
13. **Decode the map** (section 3.3).
14. **Lanterns and init handler.** [`room_decode_done`](../../src/room_draw.asm#L199) [`$0B30`](../reference/modules/room_draw.md#room_decode_done) calls [`redraw_taken_lanterns`](../../src/lanterns.asm#L63) [`$336E`](../reference/modules/lanterns.md#redraw_taken_lanterns) (section 5).
15. **Unblank.** [`room_decode_done`](../../src/room_draw.asm#L199) [`$0B33`](../../src/room_draw.asm#L202) sets bit 4 of `$D011` (display on), and `$D015` gets [`saved_sprite_enable`](../../src/constants.asm#L33) back. This read-modify-write is the place of the PAL freeze bug ([../rooms.md](../rooms.md), section 3).
16. **First pass of the frame handler.** [`room_decode_done`](../../src/room_draw.asm#L199) [`$0B40`](../../src/room_draw.asm#L207) jumps to [`run_room_update`](../../src/room_update.asm#L571) [`$3A6F`](../reference/modules/room_update.md#run_room_update). The RTS of the frame handler returns to the caller of [`draw_room`](../../src/room_draw.asm#L6) (section 5.3).

### 4.3 The room 11 diversion ([`draw_room_special`](../../src/room_draw.asm#L34) [`$09F6-$0A0D`](../reference/modules/room_draw.md#draw_room_special))

**Code:**
- When room 11 is drawn and rooms 12, 14 and 16 have no lanterns left, [`draw_room`](../../src/room_draw.asm#L6) restores the sprite enable and jumps to [`respawn_in_room`](../../src/room_entry_traps.asm#L6) [`$3217`](../reference/modules/room_entry_traps.md#respawn_in_room) with X = 13.
- [`respawn_in_room`](../../src/room_entry_traps.asm#L6) sets [`current_actor`](../../src/constants.asm#L40) [`$51`](../reference/variables.md#current_actor) = 0 and `$4E` = 13, and loads A/Y = [`room_spawn_x`](../../src/room_tables.asm#L156)/[`room_spawn_y`](../../src/room_tables.asm#L161) of room 13 = `$98`/`$32`. It then jumps to [`enter_room`](../../src/background_touch.asm#L210) [`$2F8E`](../reference/modules/background_touch.md#enter_room).
- [`enter_room`](../../src/background_touch.asm#L210) places Bruce at (`$98`, `$32`) and sets [`current_room`](../../src/constants.asm#L28) = 13. It stores and removes the enemies, as in each transition (section 9). Then it calls [`draw_room`](../../src/room_draw.asm#L6) again, now for room 13.
- The diversion uses **no extra map data**. It does not use the map pointer entry 20: that entry is never read.
- The player sees **room 13**: map [`room13_map`](../../src/room_maps.asm#L576) [`$79C6`](../reference/modules/room_maps.md#room13_map), charset set 1, init handler [`room13_init`](../../src/room_init.asm#L131) [`$34C3`](../reference/modules/room_init.md#room13_init), frame handler [`room13_update`](../../src/room_update.asm#L1117) [`$3E7C`](../reference/modules/room_update.md#room13_update).
- Room 11 gives no entry bonus on this path, because the bonus code comes after the test. Room 13 gives its own bonus if it is due.

**Observed** in the `room_special` run (part `room11_special`):
- After the diverted entry, [`current_room`](../../src/constants.asm#L28) = `$0D`. The normal entry has `$0B`.
- [`draw_room_special`](../../src/room_draw.asm#L34) [`$0A04`](../../src/room_draw.asm#L42), [`respawn_in_room`](../../src/room_entry_traps.asm#L6) [`$3217`](../reference/modules/room_entry_traps.md#respawn_in_room), [`room13_init`](../../src/room_init.asm#L131) [`$34C3`](../reference/modules/room_init.md#room13_init) and [`room13_update`](../../src/room_update.asm#L1117) [`$3E7C`](../reference/modules/room_update.md#room13_update) executed. [`room11_update`](../../src/room_update.asm#L894) [`$3CC0`](../reference/modules/room_update.md#room11_update) did not execute in that part.
- Of the 678 screen cells that differ from a normal room 11 entry, 662 equal the decoded room 13 map (top char = cell AND `$7F`, bottom char = cell OR `$80`).
- The other 16 cells are at (screen row, column) (9,19), (9,31), (13,17), (13,22), (19,8), (19,31), (23,9), (23,29) and the rows below them. They hold `$66/$64` where the map has `$67/$65`.

**Conclusion:** the 16 cells are the sliders that [`room13_update`](../../src/room_update.asm#L1117) [`$3EC0`](../../src/room_update.asm#L1155) moves with [`animate_room_objects`](../../src/room_state.asm#L29) [`$104B`](../reference/modules/room_state.md#animate_room_objects). They are not a different map.

![Room 13](../../assets/rooms/room13.png)

Room 13, the room that the diversion draws, before its sliders move.

### 4.4 The charset after the wizard defeat

- **Observed** in the `room_special` run (part `wizard_defeat`): [`room_charset_d018`](../../src/constants.asm#L109) goes from `$3C` to `$3E` (charset set 3 at `$B800`). It is still `$3E` 400 frames later.
- **Code:**
  - [`room18_defeat_effect`](../../src/room_update.asm#L1019) [`$3DAF`](../reference/modules/room_update.md#room18_defeat_effect) writes `$3E` at [`room18_effect_next_column`](../../src/room_update.asm#L1049) [`$3DFA`](../../src/room_update.asm#L1055) on each step.
  - While its counter [`room_script_vars+1`](../../src/room_tables.asm#L390) [`$4E98`](../reference/modules/room_tables.md#room_script_vars) is `$11` or more, it writes `$3C` at [`room18_effect_next_column`](../../src/room_update.asm#L1049) [`$3E09`](../../src/room_update.asm#L1062) instead when the random value is below `$10`. This gives the flashing between set 2 and set 3.
  - Nothing restores `$F2` until the next [`draw_room`](../../src/room_draw.asm#L6). After the effect, room 18 stays on set 3.
  - The exits of room 18 lead to rooms 17 and 19, and [`draw_room`](../../src/room_draw.asm#L6) then chooses `$3A`.

---

## 5. The end of the draw: lanterns, init handler, first frame handler pass

### 5.1 [`redraw_taken_lanterns`](../../src/lanterns.asm#L63) [`$336E`](../reference/modules/lanterns.md#redraw_taken_lanterns)

**Code:**
1. [`lantern_ptr`](../../src/constants.asm#L17) [`$14`](../reference/variables.md#lantern_ptr) = [`lantern_list_ptrs`](../../src/room_tables.asm#L238) [`$4CE2`](../reference/modules/room_tables.md#lantern_list_ptrs) of the room ([`redraw_taken_lanterns`](../../src/lanterns.asm#L63) [`$3372`](../../src/lanterns.asm#L67)). Y = 0.
2. [`redraw_lantern_loop`](../../src/lanterns.asm#L72) [`$337E`](../reference/modules/lanterns.md#redraw_lantern_loop) reads the state byte of a record. Bit 7 set: the list ends, go to step 5. Not 0: the lantern is present, [`redraw_lantern_skip`](../../src/lanterns.asm#L102) [`$33AC`](../reference/modules/lanterns.md#redraw_lantern_skip) goes to the next record.
3. State 0 (taken, [`redraw_taken_lanterns`](../../src/lanterns.asm#L63) [`$3384-$33AB`](../../src/lanterns.asm#L76)): it reads the cell (byte 1), the column (byte 2) and the text row (byte 3). [`set_text_line_ptrs`](../../src/status.asm#L120) [`$1A67`](../reference/modules/status.md#set_text_line_ptrs) points [`work_ptr_a`](../../src/constants.asm#L11) at the top row of that text row. It writes cell AND `$7F` at the column, and the same value OR `$80` 40 bytes further (the bottom char).
4. Go to the next record (step 2).
5. [`dispatch_room_init`](../../src/lanterns.asm#L110) [`$33B3`](../reference/modules/lanterns.md#dispatch_room_init) clears [`room_script_vars`](../../src/room_tables.asm#L390) [`$4E97-$4E9B`](../reference/modules/room_tables.md#room_script_vars), pushes the address from [`room_setup_handlers`](../../src/room_tables.asm#L401) [`$4E9C`](../reference/modules/room_tables.md#room_setup_handlers) of the room and executes RTS. The RTS of the handler returns to [`room_decode_done`](../../src/room_draw.asm#L199) [`$0B33`](../../src/room_draw.asm#L202).

- **Code:** the lantern redraw does not change the colour RAM. The cell keeps the colour that the map gave it.
- **Observed** in the `room_events2` run: an entry into room 0 with every lantern taken shows the record cells, for example tile `$1F`/`$9F` at screen rows 13/14, column 31 (record `01 9F 1F 07` of [`lantern_list_room00`](../../src/room_tables.asm#L248) [`$4D0C`](../reference/modules/room_tables.md#lantern_list_room00)).

### 5.2 The init handlers ([`room_setup_handlers`](../../src/room_tables.asm#L401) [`$4E9C`](../reference/modules/room_tables.md#room_setup_handlers))

They run with the display still blanked and the IRQs off (**Code**). The details are in the room pages.

| Handler | Rooms | Action |
|---|---|---|
| [`room_init_none`](../../src/room_init.asm#L6) [`$33F5`](../reference/modules/room_init.md#room_init_none) | 0, 2, 6, 10, 11 | RTS only. |
| [`room01_init`](../../src/room_init.asm#L9) [`$33F6`](../reference/modules/room_init.md#room01_init), [`room03_init`](../../src/room_init.asm#L14) [`$33FC`](../reference/modules/room_init.md#room03_init) | 1, 3 | [`room_script_vars`](../../src/room_tables.asm#L390) = 3. |
| [`room04_init`](../../src/room_init.asm#L19) [`$3402`](../reference/modules/room_init.md#room04_init) | 4 | The three hazards. |
| [`room05_init`](../../src/room_init.asm#L40) [`$3428`](../reference/modules/room_init.md#room05_init) | 5 | Waits forever unless `$02` = `$32` (a protection remnant); colour cells `$FC`; the hazards. |
| [`room07_init`](../../src/room_init.asm#L72) [`$3461`](../reference/modules/room_init.md#room07_init) | 7 | The slider and a hazard. |
| [`room08_init`](../../src/room_init.asm#L86) [`$3478`](../reference/modules/room_init.md#room08_init) | 8 | The hazards. |
| [`room09_init`](../../src/room_init.asm#L100) [`$348F`](../reference/modules/room_init.md#room09_init) | 9 | Colour cells, the slider, the hazards. |
| [`room12_init`](../../src/room_init.asm#L126) [`$34BD`](../reference/modules/room_init.md#room12_init), [`room14_init`](../../src/room_init.asm#L221) [`$358D`](../reference/modules/room_init.md#room14_init) | 12, 14 | [`room_script_vars`](../../src/room_tables.asm#L390) = 1. |
| [`room13_init`](../../src/room_init.asm#L131) [`$34C3`](../reference/modules/room_init.md#room13_init) | 13 | The sliders; their columns depend on [`game_cycle`](../../src/constants.asm#L30). |
| [`room15_init`](../../src/room_init.asm#L226) [`$3593`](../reference/modules/room_init.md#room15_init) | 15 | [`room_script_vars`](../../src/room_tables.asm#L390) bytes 0-2 = 1. |
| [`room16_init`](../../src/room_init.asm#L233) [`$359F`](../reference/modules/room_init.md#room16_init) | 16 | Colour cells; erases the bonus-fall object when the player has no bonus falls left. |
| [`room17_init`](../../src/room_init.asm#L251) [`$35C4`](../reference/modules/room_init.md#room17_init) | 17 | A colour cell, the slider, the hazards. |
| [`room18_init`](../../src/room_init.asm#L279) [`$35FA`](../reference/modules/room_init.md#room18_init) | 18 | Fills the colour RAM with `$FE`, sets up the sprites and the fireball variables `$432E-$4337`. |
| [`room19_init`](../../src/final_room.asm#L21) [`$425F`](../reference/modules/final_room.md#room19_init) | 19 | Countdown [`attract_countdown`](../../src/constants.asm#L35) `$49`/[`title_timeout_hi`](../../src/constants.asm#L36) `$4A` = `$0458`, clears screen row 0. |

The colour RAM changes of these handlers are included in `assets/rooms/roomNN.png` (the `setup_changes` of the JSON).

### 5.3 The last step: [`run_room_update`](../../src/room_update.asm#L571) [`$3A6F`](../reference/modules/room_update.md#run_room_update)

**Code:**
- [`draw_room`](../../src/room_draw.asm#L6) jumps here at [`room_decode_done`](../../src/room_draw.asm#L199) [`$0B40`](../../src/room_draw.asm#L207), after the display is on and `$D015` is restored.
- [`run_room_update`](../../src/room_update.asm#L571) pushes the address from [`room_frame_handlers`](../../src/room_tables.asm#L411) [`$4EC4`](../reference/modules/room_tables.md#room_frame_handlers) of the room ([`run_room_update`](../../src/room_update.asm#L571) [`$3A73`](../../src/room_update.asm#L575), `$3A77`) and executes RTS.
- The frame handler runs once. Its RTS returns to the instruction after the `JSR draw_room` of the caller.
- So the frame handler runs once per room draw before the main loop, with the IRQs still off. After that, [`main_loop`](../../src/main_loop.asm#L6) calls [`run_room_update`](../../src/room_update.asm#L571) on each pass ([`main_loop_room_and_actors`](../../src/main_loop.asm#L40) [`$1C0A`](../reference/modules/main_loop.md#main_loop_room_and_actors)).

---

## 6. After [`draw_room`](../../src/room_draw.asm#L6), and the one-time preparation

### 6.1 Actor placement and the sprites

**Code:**
- **Bruce is placed before the draw.** [`enter_room_bruce`](../../src/background_touch.asm#L217) [`$2F9A`](../reference/modules/background_touch.md#enter_room_bruce) stores [`actor_x`](../../src/constants.asm#L85) [`$9E`](../reference/variables.md#actor_x) and [`actor_y`](../../src/constants.asm#L86) [`$A1`](../reference/variables.md#actor_y). At game start, [`init_game_screen`](../../src/game_setup.asm#L6) [`$082A`](../../src/game_setup.asm#L95) jumps to [`init_actor`](../../src/actors.asm#L6) [`$0B8E`](../reference/modules/actors.md#init_actor), which reads [`room_spawn_x`](../../src/room_tables.asm#L156)/[`room_spawn_y`](../../src/room_tables.asm#L161) of the room and writes the sprite registers ([`actor_place_sprites`](../../src/actors.asm#L105) [`$0C4D`](../reference/modules/actors.md#actor_place_sprites)).
- **The enemies are not placed at the room draw.** Their spawn timers run in [`main_loop`](../../src/main_loop.asm#L6), and [`init_actor`](../../src/actors.asm#L6) places each enemy when it spawns ([`actor_pick_spawn`](../../src/actors.asm#L61) [`$0BFA`](../reference/modules/actors.md#actor_pick_spawn)): at the follow entry point ([`enemy_entry_x`](../../src/constants.asm#L79) [`$8B`](../reference/variables.md#enemy_entry_x), [`enemy_entry_y`](../../src/constants.asm#L80) [`$8D`](../reference/variables.md#enemy_entry_y)), or at spawn point A or B (section 9.3, and [actors.md](actors.md)).
- **After the draw, per caller:**
  - [`enter_room`](../../src/background_touch.asm#L210) [`$2FCF`](../../src/background_touch.asm#L249) calls [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites), which builds the sprite data of the active actors. Then CLI ([`enter_room`](../../src/background_touch.asm#L210) [`$2FD2`](../../src/background_touch.asm#L250)) and `JMP main_loop` ([`enter_room`](../../src/background_touch.asm#L210) [`$2FD3`](../../src/background_touch.asm#L251)).
  - [`start_game`](../../src/title.asm#L185) and [`start_demo`](../../src/restart.asm#L24) set [`demo_input_ptr`](../../src/constants.asm#L24) = [`demo_input_data`](../../src/demo_input.asm#L6) [`$F300`](../reference/modules/demo_input.md#demo_input_data), set bit 4 of `$D011` (already set by [`draw_room`](../../src/room_draw.asm#L6)), CLI and `JMP main_loop`.

The sprite registers and the sprite data are described in [sprites.md](sprites.md).

### 6.2 The charset expansion [`expand_charset`](../../src/charset_expand.asm#L43) [`$4892`](../reference/modules/charset_expand.md#expand_charset)

[`cold_start`](../../src/init.asm#L6) [`$0400`](../reference/modules/init.md#cold_start) calls it four times ([`boot_expand_charsets`](../../src/init.asm#L71) [`$047A`](../reference/modules/init.md#boot_expand_charsets)) (**Code**):

| Call | Source | Destination |
|---|---|---|
| [`boot_expand_charsets`](../../src/init.asm#L71) [`$0494`](../../src/init.asm#L85) | [`charset_src_0`](../../src/room_charset_src.asm#L6) [`$9000`](../reference/graphics.md#charset_src_0) | [`room_charset_0`](../../src/constants.asm#L142) [`$A000`](../reference/variables.md#room_charset_0) (top halves) and `$A400` (bottom halves) |
| [`boot_expand_charsets`](../../src/init.asm#L71) [`$04B1`](../../src/init.asm#L99) | [`charset_src_1`](../../src/room_charset_src.asm#L150) [`$9400`](../reference/modules/room_charset_src.md#charset_src_1) | [`room_charset_1`](../../src/constants.asm#L143) [`$A800`](../reference/variables.md#room_charset_1), `$AC00` |
| [`boot_expand_charsets`](../../src/init.asm#L71) [`$04CE`](../../src/init.asm#L113) | [`charset_src_2`](../../src/room_charset_src.asm#L279) [`$9800`](../reference/modules/room_charset_src.md#charset_src_2) | [`room_charset_2`](../../src/constants.asm#L144) [`$B000`](../reference/variables.md#room_charset_2), `$B400` |
| [`boot_warm_start`](../../src/init.asm#L114) [`$04ED`](../../src/init.asm#L130) | [`charset_src_3`](../../src/room_charset_src.asm#L408) [`$9C00`](../reference/modules/room_charset_src.md#charset_src_3) | [`room_charset_3`](../../src/constants.asm#L145) [`$B800`](../reference/variables.md#room_charset_3), `$BC00` |

The fourth call starts at [`boot_warm_start`](../../src/init.asm#L114) [`$04D1`](../reference/modules/init.md#boot_warm_start), which code at `$0412` also jumps to. [`draw_count`](../../src/constants.asm#L110) [`$F3`](../reference/variables.md#draw_count) = `$7F` for each call. The input pointers: [`work_ptr_a`](../../src/constants.asm#L11) = the source, [`work_ptr_b`](../../src/constants.asm#L12) = the top-half destination, [`work_ptr_c`](../../src/constants.asm#L13) = the bottom-half destination.

```
expand_charset:                            ; $4892
  Y = 0
  repeat:                                  ; once per source char, draw_count+1 = 128 times
    for k = 0..3:                          ; source rows 0-3
        A = (work_ptr_a); (work_ptr_b) = A; work_ptr_b++; (work_ptr_b) = A; work_ptr_b++; work_ptr_a++
    for k = 0..3:                          ; expand_charset_bottom $48AA: source rows 4-7
        A = (work_ptr_a); (work_ptr_c) = A; work_ptr_c++; (work_ptr_c) = A; work_ptr_c++; work_ptr_a++
    draw_count -= 1
  until draw_count < 0
```

**The result (Code):**
- Char `c` (0-127) of the VIC charset = source rows 0,0,1,1,2,2,3,3 of tile `c`.
- Char `c+128` = source rows 4,4,5,5,6,6,7,7.
- A map cell with tile `t` shows char `t` above char `t|$80`: one 8 x 16 multicolour tile, each source row two pixel rows high.

**Observed** in the `rooms` snapshots: the expansion of the image source equals `$A000-$BFFF` in the snapshots, except the bytes that the light flicker changes at run time. Example: tile `$0A` has the source `AA AA AA AA AA A8 80 00`. It gives char `$0A` = `AA` x 8 at `$A050` and char `$8A` = `AA AA A8 A8 80 80 00 00` at `$A450`, as in the snapshot of room 0.

![Charset set 0](../../assets/charsets/charset_0.png)

The 128 tiles of charset source 0 (rooms 0-9), each shown 8 x 16 pixels as the expansion makes it.

**Why `$9000` is not used directly (Code).** In VIC bank 2 (`$8000-$BFFF`) the VIC sees the character ROM at `$9000-$9FFF`, so RAM there cannot hold a charset or a screen for the VIC. The game keeps the packed sources there. Right after the four expansions, [`build_collision_masks`](../../src/collision.asm#L21) [`$512F`](../reference/modules/collision.md#build_collision_masks) (called at [`boot_warm_start`](../../src/init.asm#L114) [`$04F0`](../../src/init.asm#L131)) writes collision masks over `$9000-$9FBF`. So the masks need the charsets to be expanded first. The masks are described in [sprites.md](sprites.md).

**Link to the room (Code).** The background collision test [`actor_background_collision`](../../src/collision.asm#L149) [`$5212`](../reference/modules/collision.md#actor_background_collision) reads the char bitmaps of the room charset at [`charset_hi`](../../src/constants.asm#L67) * 256 + 8 * char, and the colour RAM through [`colour_row_hi`](../../src/collision.asm#L16) [`$5117`](../reference/modules/collision.md#colour_row_hi). So the contact bits in [`actor_contact`](../../src/constants.asm#L92) [`$B6`](../reference/variables.md#actor_contact) depend on the pixel colours of the room: `%01`, `%10`, and `%11` with the room colour or with `$F8`.

### 6.3 The text row tables [`build_text_row_tables`](../../src/game_setup.asm#L124) [`$0869`](../reference/modules/game_setup.md#build_text_row_tables)

**When it runs (Code).** [`cold_start`](../../src/init.asm#L6) does not build the tables. [`init_game_screen`](../../src/game_setup.asm#L6) [`$0763`](../reference/modules/game_setup.md#init_game_screen) builds them ([`init_game_screen`](../../src/game_setup.asm#L6) [`$0773-$078F`](../../src/game_setup.asm#L14)) each time it runs:
- before the title ([`restart_to_title`](../../src/restart.asm#L6) [`$052B`](../../src/restart.asm#L21));
- at game start ([`start_game`](../../src/title.asm#L185) [`$0749`](../../src/title.asm#L209)) and demo start ([`start_demo`](../../src/restart.asm#L24) [`$0553`](../../src/restart.asm#L40));
- after each lost fall ([`respawn_after_fall`](../../src/game_over.asm#L62) [`$1886`](../reference/modules/game_over.md#respawn_after_fall)).

The content is always the same.

```
build_text_row_tables(A=$D8, Y=$8B):       ; $0869
  top[0] = $8BD8
  for k = 1..13: top[k] = top[k-1] + $50                 ; text_row_top_lo/hi $4338/$434C
  bottom[0] = top[0] + $28 = $8C00
  for k = 1..13: bottom[k] = bottom[k-1] + $50           ; text_row_bottom_lo/hi $4360/$4374
init_game_screen then patches ($077A-$078F):
  top[0] = $8C00; bottom[0] = bottom[1] = $DE00          ; I/O area: a write there has no effect
```

The values (**Code**; the same in the `rooms` snapshot of room 0):

| Text row k | Top | Bottom | Screen rows | Map row |
|---|---|---|---|---|
| 0 | `$8C00` | `$DE00` | 0 (version line) | - |
| 1 | `$8C28` | `$DE00` | 1 (status line) | - |
| 2 | `$8C78` | `$8CA0` | 3, 4 | 0 |
| k (2-12) | `$8BD8+$50k` | top + `$28` | 2k-1, 2k | k-2 |
| 12 | `$8F98` | `$8FC0` | 23, 24 | 10 |
| 13 | `$8FE8` | `$9010` | (25, 26: outside the screen) | 11 |

**The users (Code):**
- [`set_text_line_ptrs`](../../src/status.asm#L120) [`$1A67`](../reference/modules/status.md#set_text_line_ptrs) sets [`work_ptr_a`](../../src/constants.asm#L11) and [`work_ptr_c`](../../src/constants.asm#L13) from these tables. With [`text_single_height`](../../src/constants.asm#L118) [`$0100`](../reference/variables.md#text_single_height) set, it sends the bottom half to `$DE00`.
- [`print_message`](../../src/text.asm#L6) [`$17E2`](../reference/modules/text.md#print_message) uses it: the tile strings of the room handlers, and the status texts. The lantern redraw also uses it.
- [`check_three_cells`](../../src/background_touch.asm#L36) [`$2E6E`](../reference/modules/background_touch.md#check_three_cells) uses it for the background touch. The [`actor_char_row`](../../src/constants.asm#L106) [`$E9`](../reference/variables.md#actor_char_row) = (y-12)/16 of [`actor_char_coords`](../../src/actor_movement.asm#L6) [`$1C39`](../reference/modules/actor_movement.md#actor_char_coords) is a text row.

---

## 7. The colour bands of a room

The raster chain is described in [interrupts.md](interrupts.md). This section gives the room part of it (**Code**):

1. [`irq_frame_top`](../../src/raster_irq_game.asm#L6) [`$48C1`](../reference/modules/raster_irq_game.md#irq_frame_top) runs at raster line `$FD`. It sets `$D018` = `$32` and `$D021` = `$FC` for the status rows 0-1 of the next frame. It reads [`room_split_colour_ptrs`](../../src/room_split_tables.asm#L6) [`$480B`](../reference/modules/room_split_tables.md#room_split_colour_ptrs) and [`room_raster_line_ptrs`](../../src/room_split_tables.asm#L16) [`$4833`](../reference/modules/room_split_tables.md#room_raster_line_ptrs) of [`current_room`](../../src/constants.asm#L28), and [`irq_copy_room_colours`](../../src/raster_irq_game.asm#L36) [`$4904`](../reference/modules/raster_irq_game.md#irq_copy_room_colours) copies 12 band colours to [`raster_colours`](../../src/constants.asm#L136) [`$0153-$015E`](../reference/variables.md#raster_colours) and 4 raster-list bytes to [`current_raster_splits`](../../src/room_colours.asm#L50) [`$47F5`](../reference/modules/room_colours.md#current_raster_splits). So a new room takes effect in the first frame after the draw.
2. [`irq_playfield_top`](../../src/raster_irq_game.asm#L54) [`$491E`](../reference/modules/raster_irq_game.md#irq_playfield_top) runs at raster line `$40`. It waits for line `$42`, then sets `$D018` from [`room_charset_d018`](../../src/constants.asm#L109) [`$F2`](../reference/variables.md#room_charset_d018) ([`irq_playfield_top`](../../src/raster_irq_game.asm#L54) [`$492A`](../../src/raster_irq_game.asm#L63)) and `$D021-$D023` from triplet 0. The room charset starts at screen row 2.
3. [`irq_colour_split`](../../src/raster_irq_game.asm#L107) [`$4982`](../reference/modules/raster_irq_game.md#irq_colour_split) runs once for each listed line L. It sets the next triplet at line L+2 (late in the line) or L+3.

**The band boundaries of each room (Code):**

| Rooms | Lines L | Triplets shown | Band starts (raster line; playfield pixel row y = raster - `$4B`) |
|---|---|---|---|
| 0, 1, 2 | `$78`, `$97` | 0, 1, 2 | `$7B` (y 48 = start of map row 3), `$9A` (y 79 = last line of map row 4) |
| 3 | `$62`, `$97` | 0, 1, 2 | `$65` (y 26, inside map row 1), `$9A` |
| 10, 12, 14, 16 | `$56` | 0, 1 | `$59` (y 14, inside map row 0) |
| 15 | `$B6`, `$C7` | 0, 1, 2 | `$B9` (y 110), `$CA` (y 127) |
| the others | - | 0 only | - |

The renders in `assets/rooms` start each band at L+3. Screen row n covers raster lines `$33+8n` to `$3A+8n`, so the playfield (screen rows 3-24) covers lines `$4B-$FA`.

- The triplets after the last listed line are copied each frame and never shown. For example, rooms 4-6 copy 4 triplets from [`band_colours_rooms_4_6`](../../src/room_colours.asm#L29) [`$47D1`](../reference/modules/room_colours.md#band_colours_rooms_4_6) and show only `F6 FE F1`.
- Only rooms 0-3 and 15 show three bands. Rooms 10, 12, 14 and 16 show two. All other rooms show one.

**The effect of a triplet.** `%00` pixels use `$D021`, `%01` pixels `$D022`, `%10` pixels `$D023`, and `%11` pixels the colour RAM (the room colour, or `$F8` = black). Screen row 2 (`$8C50-$8C77`, char `$06` written by [`init_game_screen`](../../src/game_setup.asm#L6) [`$07AB`](../../src/game_setup.asm#L37), colour RAM `$F8`) is drawn with the room charset and triplet 0.

**Other changes of the room picture during play.** None of them is part of [`draw_room`](../../src/room_draw.asm#L6) (**Code**):
- [`flicker_lights`](../../src/light_flicker.asm#L6) [`$40BC`](../reference/modules/light_flicker.md#flicker_lights) (from [`main_loop`](../../src/main_loop.asm#L6)) writes random pixels into the light chars of charsets 0 and 1.
- [`animate_scrolling_chars`](../../src/animated_chars.asm#L6) [`$2C70`](../reference/modules/animated_chars.md#animate_scrolling_chars) writes three chars of the current charset through [`charset_hi`](../../src/constants.asm#L67) [`$7C`](../reference/variables.md#charset_hi).
- The room frame handlers draw tile strings with [`print_message`](../../src/text.asm#L6) and change the colour RAM. Examples: the colour flip of room 17 and the random colours of room 19.
- The idle screen saver in [`game_frame_update`](../../src/frame_update.asm#L6) ([`screen_saver_colours`](../../src/frame_update.asm#L95) [`$1645`](../reference/modules/frame_update.md#screen_saver_colours)) changes [`raster_colours`](../../src/constants.asm#L136) after [`irq_frame_top`](../../src/raster_irq_game.asm#L6) copied them.

---

## 8. Screen memory layout

**VIC bank 2.** [`init_game_screen`](../../src/game_setup.asm#L6) [`$07DB`](../../src/game_setup.asm#L62) writes `$01` to `$DD00`, which selects `$8000-$BFFF` (**Code**).

| VIC address | Content | Notes |
|---|---|---|
| `$8000-$83FF` | [`sprite_blocks`](../../src/vic_bank2.asm#L6) [`$8180-$83FF`](../reference/modules/vic_bank2.md#sprite_blocks) = 10 sprite blocks (blocks 6-15) | Built by [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites). |
| `$8400-$87FF` | [`title_font`](../../src/vic_bank2.asm#L124) [`$8400`](../reference/graphics.md#title_font): the big title font (chars `$80-$FF` of the charset at `$8000`) | Title only. |
| `$8800-$8BFF` | [`title_charset`](../../src/vic_bank2.asm#L254) [`$8800`](../reference/modules/vic_bank2.md#title_charset): the ROM font copy and its inverse | The status line and the title texts. `$D018` = `$32`/`$33`. |
| `$8C00-$8FE7` | [`screen_ram`](../../src/vic_bank2.asm#L376) [`$8C00`](../reference/modules/vic_bank2.md#screen_ram) (1000 bytes) | `$D018` high nibble 3. |
| `$8FE8-$8FF7` | Unused screen RAM | The 2 extra cells of rooms 4, 7, 10, 13, 17 and 18 land at `$8FE8/$8FE9`. |
| `$8FF8-$8FFF` | [`sprite_pointers`](../../src/vic_bank2.asm#L574) [`$8FF8`](../reference/modules/vic_bank2.md#sprite_pointers) | |
| `$9000-$9FFF` | The VIC sees the char ROM; the CPU sees the charset sources, then the collision masks | Not usable by the VIC. |
| `$A000-$A7FF` | [`room_charset_0`](../../src/constants.asm#L142) [`$A000`](../reference/variables.md#room_charset_0): set 0 | `$D018` = `$38`, rooms 0-9 |
| `$A800-$AFFF` | [`room_charset_1`](../../src/constants.asm#L143) [`$A800`](../reference/variables.md#room_charset_1): set 1 | `$3A`, rooms 10-17 and 19 |
| `$B000-$B7FF` | [`room_charset_2`](../../src/constants.asm#L144) [`$B000`](../reference/variables.md#room_charset_2): set 2 | `$3C`, room 18 |
| `$B800-$BFFF` | [`room_charset_3`](../../src/constants.asm#L145) [`$B800`](../reference/variables.md#room_charset_3): set 3 | `$3E`, the room 18 defeat effect |

Each 2 KB set holds the top halves in chars 0-127 and the bottom halves in chars 128-255.

**The screen rows (Code):**

| Screen rows | Address | Content | Charset | Colour RAM |
|---|---|---|---|---|
| 0 | `$8C00` | The version line (V key) or blank. [`draw_room`](../../src/room_draw.asm#L6) clears it to `$20`. Room 19 prints CONGRATULATIONS here. | `$8800` (`$D018` = `$32`) | `$D800`: 0 (hi-res black) |
| 1 | `$8C28` | The status line: score, TOP, FALLS (text row 1, single height). | `$8800` | `$D828`: 0 |
| 2 | `$8C50` | Char `$06` x 40, written by [`init_game_screen`](../../src/game_setup.asm#L6) [`$07AB`](../../src/game_setup.asm#L37): a border strip drawn with the room charset. | The room (`$F2`) | `$D850`: `$F8` |
| 3-24 | `$8C78-$8FE7` | The playfield: 11 map rows x 40 cells, each cell 2 chars high. Map row R = screen rows 3+2R (top char `t`) and 4+2R (bottom char `t|$80`) = text row R+2. | The room | `$D878-$DBE7`: the room colour, or `$F8` for cells with bit 7 |

The status rows get colour RAM 0 from [`init_game_screen`](../../src/game_setup.asm#L6) [`$079C`](../../src/game_setup.asm#L31).

**The colour RAM rules (Code):**
- The colour RAM address = the screen address + `$4C00`. [`trigger_floor_trap`](../../src/background_touch.asm#L341) [`$306B`](../reference/modules/background_touch.md#trigger_floor_trap) uses exactly this: it adds `$4C` to the high byte.
- [`draw_room`](../../src/room_draw.asm#L6) fills `$D878-$DBFF` with one value. The decoder then writes `$F8` for the cells with bit 7. The init and frame handlers change single cells.
- A colour RAM value of the playfield is always `$F8-$FF`: multicolour is on for each playfield char.

**Double-height cells.** A cell is one 8 x 16 tile. The top char is tile `t` (rows 0-3 of the source, doubled) and the bottom char is `t+128` (rows 4-7, doubled). Both chars have the same colour RAM value. Each writer of room cells writes both halves: the decoder, [`print_message`](../../src/text.asm#L6) and the lantern code (**Code**).

**Coordinates (Code):**
- Sprite X = 2 * [`actor_x`](../../src/constants.asm#L85). Sprite Y = [`actor_y`](../../src/constants.asm#L86) + `$1D`.
- Cell column = ([`actor_x`](../../src/constants.asm#L85) - 12) / 4. Text row = ([`actor_y`](../../src/constants.asm#L86) - 12) / 16.

---

## 9. The room transition

### 9.1 From the touch to the exit

All steps are **Code**.

1. **[`check_actors_background`](../../src/background_touch.asm#L6) [`$2E39`](../reference/modules/background_touch.md#check_actors_background).** [`main_loop`](../../src/main_loop.asm#L6) calls it on each pass ([`main_loop_room_and_actors`](../../src/main_loop.asm#L40) [`$1C10`](../../src/main_loop.asm#L43)). For each actor X = 2, 1, 0 that is active and not dying (state `$19`):
   - [`actor_char_coords`](../../src/actor_movement.asm#L6) [`$1C39`](../reference/modules/actor_movement.md#actor_char_coords) gives [`actor_char_col`](../../src/constants.asm#L105) [`$E6`](../reference/variables.md#actor_char_col) = (x-12)/4 and [`actor_char_row`](../../src/constants.asm#L106) [`$E9`](../reference/variables.md#actor_char_row) = (y-12)/16, with y+4 in room 13;
   - [`check_three_cells`](../../src/background_touch.asm#L36) [`$2E6E`](../reference/modules/background_touch.md#check_three_cells) reads the three top chars at columns col..col+2 of text row `row` ([`check_actors_background`](../../src/background_touch.asm#L6) [`$2E5E`](../../src/background_touch.asm#L26)), then of `row+1` ([`check_actors_background`](../../src/background_touch.asm#L6) [`$2E65`](../../src/background_touch.asm#L29)), through [`set_text_line_ptrs`](../../src/status.asm#L120). It passes each char with bit 7 cleared to [`handle_touched_char`](../../src/background_touch.asm#L53) [`$2E89`](../reference/modules/background_touch.md#handle_touched_char).
2. **[`handle_touched_char`](../../src/background_touch.asm#L53) [`$2E89`](../reference/modules/background_touch.md#handle_touched_char).** The chars `$05`, `$02`, `$03` and `$04` jump to [`take_exit_char05`](../../src/background_touch.asm#L200), [`take_exit_char02`](../../src/background_touch.asm#L165), [`take_exit_char03`](../../src/background_touch.asm#L177) and [`take_exit_char04`](../../src/background_touch.asm#L188). The exit chars are tested first, for each actor.
3. **[`take_exit_char02`](../../src/background_touch.asm#L165) [`$2F3C`](../reference/modules/background_touch.md#take_exit_char02)** ([`take_exit_char03`](../../src/background_touch.asm#L177) [`$2F51`](../reference/modules/background_touch.md#take_exit_char03), [`take_exit_char04`](../../src/background_touch.asm#L188) [`$2F66`](../reference/modules/background_touch.md#take_exit_char04) and [`take_exit_char05`](../../src/background_touch.asm#L200) [`$2F7B`](../reference/modules/background_touch.md#take_exit_char05) are the same):
   ```
   if check_exit_direction() gives C=1: return
   $4E = exitN_room[room]; Y = exitN_y[room]; A = exitN_x[room]
   if A != 0: goto enter_room
   else fall into take_exit_char(N+1)       ; N=5 goes to enter_room with A = x, also when x is 0
   ```
4. **[`check_exit_direction`](../../src/background_touch.asm#L392) [`$30D4`](../reference/modules/background_touch.md#check_exit_direction).** It gives C = 0 (exit allowed) when one of these is true:
   - the room is 11;
   - [`actor_x`](../../src/constants.asm#L85) < `$10` and [`actor_moved_left`](../../src/actor_vars.asm#L233) [`$4F5D`](../reference/modules/actor_vars.md#actor_moved_left) of the actor is not 0;
   - [`actor_x`](../../src/constants.asm#L85) > `$A1` and [`actor_moved_right`](../../src/actor_vars.asm#L236) [`$4F60`](../reference/modules/actor_vars.md#actor_moved_right) of the actor is not 0;
   - [`actor_y`](../../src/constants.asm#L86) > `$C5` and [`actor_state`](../../src/constants.asm#L95) [`$BF`](../reference/variables.md#actor_state) of the actor is `$0E` (*not run*);
   - [`actor_y`](../../src/constants.asm#L86) < `$31` and [`actor_move_counters`](../../src/actor_vars.asm#L227) [`$4F57`](../reference/modules/actor_vars.md#actor_move_counters) of the actor is not 0 (*not run*).

   Else C = 1.

**Conclusion:** an exit tile works only when the actor moves out across the matching edge of the screen.

### 9.2 [`enter_room`](../../src/background_touch.asm#L210) [`$2F8E`](../reference/modules/background_touch.md#enter_room)

The inputs: A = entry x, Y = entry y, `$4E` = the destination, [`current_actor`](../../src/constants.asm#L40) [`$51`](../reference/variables.md#current_actor) = the actor (**Code**).

1. **An enemy walked out** (X is not 0): [`remove_actor`](../../src/background_touch.asm#L280) [`$3001`](../reference/modules/background_touch.md#remove_actor) ([`enter_room`](../../src/background_touch.asm#L210) [`$2F92`](../../src/background_touch.asm#L213)), two PLAs drop the return address into [`check_three_cells`](../../src/background_touch.asm#L36), and `JMP next_actor_background` `$2E68` goes on with the next actor.
2. **Bruce** ([`enter_room_bruce`](../../src/background_touch.asm#L217) [`$2F9A`](../reference/modules/background_touch.md#enter_room_bruce)): [`actor_x`](../../src/constants.asm#L85) = A, [`actor_y`](../../src/constants.asm#L86) = Y, [`current_room`](../../src/constants.asm#L28) = `$4E` ([`enter_room_bruce`](../../src/background_touch.asm#L217) [`$2FA1`](../../src/background_touch.asm#L222)).
3. **The enemies** ([`enter_room_enemy_loop`](../../src/background_touch.asm#L225) [`$2FA5`](../reference/modules/background_touch.md#enter_room_enemy_loop)), for X = 2, then 1:
   - an active enemy: [`enemy_saved_energy`](../../src/constants.asm#L81) [`$8F`](../reference/variables.md#enemy_saved_energy) + X - 1 = its energy, [`enemy_entry_x`](../../src/constants.asm#L79) [`$8B`](../reference/variables.md#enemy_entry_x) + X - 1 = [`actor_x`](../../src/constants.asm#L85) of Bruce, [`enemy_entry_y`](../../src/constants.asm#L80) [`$8D`](../reference/variables.md#enemy_entry_y) + X - 1 = [`actor_y`](../../src/constants.asm#L86) of Bruce. These are Bruce's **new** coordinates;
   - an inactive enemy: [`enter_room_no_follow`](../../src/background_touch.asm#L236) [`$2FB9`](../reference/modules/background_touch.md#enter_room_no_follow) sets both entry bytes to 0;
   - then [`enter_room_remove_enemy`](../../src/background_touch.asm#L240) [`$2FBF`](../reference/modules/background_touch.md#enter_room_remove_enemy) calls [`remove_actor`](../../src/background_touch.asm#L280) [`$3001`](../reference/modules/background_touch.md#remove_actor): the flags, the `$D015` bits, the sprite data, and the spawn timer.
4. SEI ([`enter_room`](../../src/background_touch.asm#L210) [`$2FC5`](../../src/background_touch.asm#L244)). [`reset_enemy_timer`](../../src/actors.asm#L239) [`$0D42`](../reference/modules/actors.md#reset_enemy_timer) with X = 0 reloads both timers from the respawn delays. [`draw_room`](../../src/room_draw.asm#L6) writes them again (section 4.2, step 8), so this reload has no effect.
5. The stack = `$FF` ([`enter_room`](../../src/background_touch.asm#L210) [`$2FC9`](../../src/background_touch.asm#L246)): the call chain of the main loop is dropped.
6. [`draw_room`](../../src/room_draw.asm#L6) [`$09BC`](../reference/modules/room_draw.md#draw_room) ([`enter_room`](../../src/background_touch.asm#L210) [`$2FCC`](../../src/background_touch.asm#L248)), [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites) ([`enter_room`](../../src/background_touch.asm#L210) [`$2FCF`](../../src/background_touch.asm#L249)), CLI and `JMP main_loop` ([`enter_room`](../../src/background_touch.asm#L210) [`$2FD3`](../../src/background_touch.asm#L251)).

**What a transition keeps:** the score, the falls, the lantern states (the lantern lists and [`room_lanterns_left`](../../src/constants.asm#L29)), [`room_entry_bonus_flags`](../../src/constants.asm#L138), [`game_cycle`](../../src/constants.asm#L30) and Bruce's energy.

**What a transition resets:** the enemies are removed. [`draw_room`](../../src/room_draw.asm#L6) resets the timers, the movement history, Bruce's state, the room script variables, the charset and the colour sets.

**The other ways into [`enter_room`](../../src/background_touch.asm#L210):**
- [`respawn_in_room`](../../src/room_entry_traps.asm#L6) [`$3217`](../reference/modules/room_entry_traps.md#respawn_in_room): after a lost fall ([`respawn_after_fall`](../../src/game_over.asm#L62) [`$188B`](../../src/game_over.asm#L65)), after the ending ([`room19_congratulations_update`](../../src/final_room.asm#L34) [`$4295`](../../src/final_room.asm#L54); **Observed** in the `room_special` ending) and in the room 11 diversion. It uses [`room_spawn_x`](../../src/room_tables.asm#L156)/[`room_spawn_y`](../../src/room_tables.asm#L161) of room X.
- [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24DB`](../../src/object_actions.asm#L706): when an actor in state `$18` still overlaps an obstacle and its move history is empty, the code sets [`current_actor`](../../src/constants.asm#L40) = 0 and calls [`enter_room`](../../src/background_touch.asm#L210) with spawn point A of the current room. So Bruce enters the room again, and the room is drawn again. Whether an enemy can reach this path is Still open (E7).

### 9.3 How the enemies follow

The room part (**Code**); the spawn itself is in [actors.md](actors.md):
1. When Bruce leaves, each active enemy gets [`enemy_entry_x`](../../src/constants.asm#L79)/[`enemy_entry_y`](../../src/constants.asm#L80) = Bruce's entry point and [`enemy_saved_energy`](../../src/constants.asm#L81) = its energy (step 3 above).
2. [`draw_room`](../../src/room_draw.asm#L6) clears [`enemy_entry_x`](../../src/constants.asm#L79) when the new room has a [`room_no_combat_flags`](../../src/room_tables.asm#L217) value that is not 0 ([`draw_room`](../../src/room_draw.asm#L6) [`$0A48`](../../src/room_draw.asm#L77)). [`init_game_screen`](../../src/game_setup.asm#L6) [`$0763`](../reference/modules/game_setup.md#init_game_screen) and [`next_player_turn`](../../src/game_over.asm#L15) [`$1834`](../../src/game_over.asm#L21) also clear it.
3. In [`main_loop`](../../src/main_loop.asm#L6), [`tick_enemy_timers`](../../src/actors.asm#L304) [`$0DA4`](../reference/modules/actors.md#tick_enemy_timers), [`try_spawn_yamo`](../../src/actors.asm#L207) [`$0D0F`](../reference/modules/actors.md#try_spawn_yamo) and [`try_spawn_ninja`](../../src/actors.asm#L315) [`$0DB1`](../reference/modules/actors.md#try_spawn_ninja) spawn an enemy when its timer is 0. The timer starts at the first-spawn delay of the room, or 3 or 8 (section 4.2, step 8).
4. [`spawn_yamo`](../../src/actors.asm#L177) [`$0CD5`](../reference/modules/actors.md#spawn_yamo) and [`spawn_ninja`](../../src/actors.asm#L355) [`$0DF8`](../reference/modules/actors.md#spawn_ninja) call [`init_actor`](../../src/actors.asm#L6) [`$0B8E`](../reference/modules/actors.md#init_actor) with X = 1 or 2:
   - in the demo, each enemy goes to spawn point A;
   - if [`enemy_entry_x`](../../src/constants.asm#L79) of the enemy is not 0 ([`actor_pick_spawn`](../../src/actors.asm#L61) [`$0BFA`](../reference/modules/actors.md#actor_pick_spawn)), [`actor_use_entry_pos`](../../src/actors.asm#L97) [`$0C3F`](../reference/modules/actors.md#actor_use_entry_pos) sets [`actor_x`](../../src/constants.asm#L85), [`actor_y`](../../src/constants.asm#L86) and [`actor_energy`](../../src/constants.asm#L99) from the entry bytes and clears [`enemy_entry_x`](../../src/constants.asm#L79);
   - else the entry preference and [`random_byte`](../../src/interrupts.asm#L75) choose spawn point A or B ([`actor_pick_spawn`](../../src/actors.asm#L61) [`$0C04-$0C3C`](../../src/actors.asm#L67), [`actor_random_spawn`](../../src/actors.asm#L76) [`$0C17`](../reference/modules/actors.md#actor_random_spawn)).
5. [`spawn_yamo`](../../src/actors.asm#L177) then limits the energy to `$14`, and [`spawn_ninja`](../../src/actors.asm#L355) to `$07`.

**Conclusion:** a following enemy appears at the point where Bruce entered, with its old energy (limited), after the first-spawn delay of the new room.

### 9.4 How the main loop starts again

- [`enter_room`](../../src/background_touch.asm#L210) resets the stack to `$FF` and jumps to [`main_loop`](../../src/main_loop.asm#L6) [`$1BC2`](../reference/modules/main_loop.md#main_loop). The pass that found the exit is dropped from [`check_actors_background`](../../src/background_touch.asm#L6) on (**Code**).
- [`main_loop`](../../src/main_loop.asm#L6) sets [`frame_countdown`](../../src/constants.asm#L34) [`$48`](../reference/variables.md#frame_countdown) = 3 and runs a full pass. The frame handler of the new room has already run once inside [`draw_room`](../../src/room_draw.asm#L6) (**Code**).
- The raster chain goes on at the CLI. The first [`irq_frame_top`](../../src/raster_irq_game.asm#L6) after the draw copies the triplets and the raster list of the new room (**Code**).
- Until then, the handler that was due before the SEI runs with the values that [`draw_room`](../../src/room_draw.asm#L6) left in `$0153-$015E`: the Atari set (**Code**).

**Conclusion:** at most one part of a frame can show wrong band colours. The display is already on then. No run showed it (Still open, E4).

**An enemy exit and the stack (Code).** When an enemy takes an exit, [`enter_room`](../../src/background_touch.asm#L210) drops only the return address into [`check_three_cells`](../../src/background_touch.asm#L36) and jumps to [`next_actor_background`](../../src/background_touch.asm#L30) [`$2E68`](../reference/modules/background_touch.md#next_actor_background), which goes on with the loop over the actors. The return address into [`check_actors_background`](../../src/background_touch.asm#L6) stays on the stack. The last RTS of the loop ([`check_actors_background`](../../src/background_touch.asm#L6) [`$2E6D`](../../src/background_touch.asm#L34)) uses it:
- If the exit was found in the first [`check_three_cells`](../../src/background_touch.asm#L36) call ([`check_actors_background`](../../src/background_touch.asm#L6) [`$2E5E`](../../src/background_touch.asm#L26)), the RTS returns to [`check_actors_background`](../../src/background_touch.asm#L6) [`$2E61`](../../src/background_touch.asm#L27). [`current_actor`](../../src/constants.asm#L40) is 0 after the loop, so the code there checks Bruce's cells again one row lower, then returns to [`main_loop`](../../src/main_loop.asm#L6).
- If the exit was found in the second call ([`check_actors_background`](../../src/background_touch.asm#L6) [`$2E65`](../../src/background_touch.asm#L29)), the RTS returns to [`next_actor_background`](../../src/background_touch.asm#L30) [`$2E68`](../reference/modules/background_touch.md#next_actor_background), which returns to [`main_loop`](../../src/main_loop.asm#L6) at once.

**Observed:** the enemy exit path ran ([`enter_room`](../../src/background_touch.asm#L210) [`$2F92`](../../src/background_touch.asm#L213) is executed in the coverage). The effect on the stack is Still open (E3).

---

## 10. Worked example: the start of room 0

[`room_map_ptrs_lo`](../../src/room_tables.asm#L125)/[`room_map_ptrs_hi`](../../src/room_tables.asm#L129) of room 0 = `$68F9` ([`room00_map`](../../src/room_maps.asm#L6)). The stream bytes (**Code**, from the image):

```
$68F9: 16 89 8D 8A A3 B5 B3 B5 B6 8A A3 B3 B5 A3 B5 B6 05 89 84 A3 B3 B4 B3 02 B4 86 B3 B4 B5 B6 A3 8C 02 B4 88 B5 B6 8A A3 B5 B6 8A 8E 03 00 ...
```

The start state: [`work_ptr_a`](../../src/constants.asm#L11) = `$8C78`, [`work_ptr_c`](../../src/constants.asm#L13) = `$8CA0`, [`colour_ptr_a`](../../src/constants.asm#L15) = `$D878`, [`colour_ptr_b`](../../src/constants.asm#L16) = `$D8A0`, [`draw_count`](../../src/constants.asm#L110) = `$27`. The colour RAM is already `$FE` ([`room_char_colours`](../../src/room_colours.asm#L12) of room 0) from `$D878` on.

| Stream | Bytes | Meaning | Cells (map row, columns) | Screen (top / bottom) |
|---|---|---|---|---|
| `$68F9` | `16 89` | run of `$16` = 22 cells of `$89` | row 0, columns 0-21 | `$8C78-$8C8D` = `$09`; `$8CA0-$8CB5` = `$89`; colour `$D878-$D88D` and `$D8A0-$D8B5` = `$F8` (bit 7) |
| `$68FB` | `8D` + 13 bytes | literal of 13: `8A A3 B5 B3 B5 B6 8A A3 B3 B5 A3 B5 B6` | row 0, columns 22-34 | top `$8C8E-$8C9A` = `0A 23 35 33 35 36 0A 23 33 35 23 35 36`; bottom `$8CB6-$8CC2` = `8A A3 B5 B3 B5 B6 8A A3 B3 B5 A3 B5 B6`; all colour `$F8` |
| `$6909` | `05 89` | run of 5 x `$89` | row 0, columns 35-39 | top `$8C9B-$8C9F` = `$09`, bottom `$8CC3-$8CC7` = `$89` |
| (after cell 40) | - | [`room_draw_next_cell`](../../src/charset_expand.asm#L6): [`draw_count`](../../src/constants.asm#L110) - 1 -> reload `$27`; the four pointers + 40 | - | [`work_ptr_a`](../../src/constants.asm#L11) = `$8CC8` (screen row 5), [`work_ptr_c`](../../src/constants.asm#L13) = `$8CF0` (row 6), colour `$D8C8`/`$D8F0` |
| `$690B` | `84` + 4 | literal: `A3 B3 B4 B3` | row 1, columns 0-3 | top `$8CC8-$8CCB` = `23 33 34 33`, bottom `$8CF0-$8CF3` = `A3 B3 B4 B3` |
| `$6910` | `02 B4` | run of 2 x `$B4` | row 1, columns 4-5 | `34 34` / `B4 B4` |
| `$6912` | `86` + 6 | literal: `B3 B4 B5 B6 A3 8C` | row 1, columns 6-11 | `33 34 35 36 23 0C` / `B3 B4 B5 B6 A3 8C` |
| `$6919` | `02 B4` | run of 2 x `$B4` | row 1, columns 12-13 | `34 34` / `B4 B4` |
| `$691B` | `88` + 8 | literal: `B5 B6 8A A3 B5 B6 8A 8E` | row 1, columns 14-21 | `35 36 0A 23 35 36 0A 0E` / `B5 B6 8A A3 B5 B6 8A 8E` |
| `$6924` | `03 00` | run of 3 x `$00` | row 1, columns 22-24 | `00` / `80`, the colour stays `$FE` (bit 7 clear) |

**The check against the snapshot (Observed** in the `rooms` run, room 0). Screen row 3 (`$8C78`):
```
09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 09 0A 23 35 33 35 36 0A 23 33 35 23 35 36 09 09 09 09 09
```
Screen row 4 (`$8CA0`) holds the same values with bit 7 set. The colour RAM of rows 3 and 4 holds `$8` (the low nibble of `$F8`) in each column.

**The pixels (Code).**
- Tile `$09` (source `$9048` = `AA` x 8) is all `%10` pixels. It shows `$D023` of triplet 0 of [`room_band_colours`](../../src/room_colours.asm#L25) [`$47C8`](../reference/modules/room_colours.md#room_band_colours) (`FB F1 FE`) = `$FE`, light blue, in band 0.
- Tile `$23` (source `$9118` = `AA AA AA A5 95 51 01 05`) gives:
  - char `$23` = `AA AA AA AA AA AA A5 A5`;
  - char `$A3` = `95 95 51 51 01 01 05 05`: `%01` (`$D022`), `%00` (`$D021`) and `%11` (colour RAM `$F8`, black).

The top map row of the render of room 0 in section 3.5 shows these cells: the background of tile `$09`, with the tiles of the literal at columns 22-34.

---

## 11. Still open

These need a run. The emulator belongs to other agents in this job, so no new runs are on this page.

| # | Question | The run that can answer it |
|---|---|---|
| E2 | Do enemies that are active when Bruce loses a fall follow him into the room of the respawn? [`next_player_turn`](../../src/game_over.asm#L15) [`$1834`](../../src/game_over.asm#L21) clears [`enemy_entry_x`](../../src/constants.asm#L79), but [`enter_room`](../../src/background_touch.asm#L210) then sets it again for each active enemy. | Lose a fall with Yamo active. Read `$8B/$8C` and `$8F/$90` after [`enter_room`](../../src/background_touch.asm#L210) [`$2FC5`](../../src/background_touch.asm#L244), and see where Yamo spawns. |
| E3 | An enemy exit leaves one return address on the stack (section 9.4). | Break at [`enter_room`](../../src/background_touch.asm#L210) [`$2F92`](../../src/background_touch.asm#L213). Note S and which [`check_three_cells`](../../src/background_touch.asm#L36) call was active, then step to the RTS at [`check_actors_background`](../../src/background_touch.asm#L6) [`$2E6D`](../../src/background_touch.asm#L34) and see whether it returns to `$2E61`. |
| E4 | The first frame after the CLI of [`enter_room`](../../src/background_touch.asm#L210) may show the Atari bytes from `$0153` before [`irq_frame_top`](../../src/raster_irq_game.asm#L6) copies the triplets. | Break at [`enter_room`](../../src/background_touch.asm#L210) [`$2FD2`](../../src/background_touch.asm#L250), read `$0408` and `$D012`, step one frame and watch the writes to `$D021`. |
| E5 | The meaning of the 20 unreferenced bytes `$4CBA-$4CCD`. | No code reads them. Compare with the Atari version if one is available. |
| E6 | The exit conditions with state `$0E` (y > `$C5`) and with an upward move (y < `$31`) never ran. | Find a room with an exit tile at the bottom or top edge (for example exit 3 of room 4, y = `$32`) and record [`check_exit_direction`](../../src/background_touch.asm#L392) [`$30F7`](../../src/background_touch.asm#L413) and `$3103`. |
| E7 | Can an enemy reach [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24DB`](../../src/object_actions.asm#L706) with an empty move history? The code sets [`current_actor`](../../src/constants.asm#L40) = 0, so it would move Bruce, not the enemy. | Put Yamo into state `$18` inside an obstacle with an empty move history and watch [`current_room`](../../src/constants.asm#L28) and Bruce's position. |

**Settled here:**
- **The room 11 diversion** goes to room 13 (section 4.3). It is no separate map.
- **The Atari colour set** is copied and has no effect (section 2.3).
- **Map pointer entry 20** and **lantern list entry 20** are never read.
- **The taken-lantern redraw** ([`redraw_taken_lanterns`](../../src/lanterns.asm#L63) [`$3384-$33AB`](../../src/lanterns.asm#L76)) ran in the `room_events2` and `room_events3` runs (section 5.1).
- **The [`game_cycle`](../../src/constants.asm#L30) timers** ([`draw_room`](../../src/room_draw.asm#L6) [`$0A5C`](../../src/room_draw.asm#L88)) ran in the `room_special` ending.
