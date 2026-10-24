# How v1 and v2 differ

Koala Painter exists in two builds of the same program. v1 is the program of the Mayday! release of 2023, which comes from a G64 image of an original disk. v2 is the program of the 1984 cracks of TBC and MAM. This page tells each difference between the two builds and what a user sees. The pages of each version explain each part in depth.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge. The label `v1:` marks a name of v1. The label `v2:` marks a name of v2.
- In the tables, the column v1 gives the address in v1, and the column v2 gives the address in v2. A dash means that the build does not have the part.
- A *move* is the v2 address minus the v1 address, for example +3.
- The *stylus* is the pen of the KoalaPad. *Off the pad* means that the stylus does not touch the pad.
- The *long press* is the gesture that changes between the menu and the picture: 16 reads off the pad, then a button down.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

The facts come from an alignment of the bytes of the two programs and from the knowledge of each build. A fact is **Code** when the text gives no other mark.

## Why two projects

The two builds have the same parts in the same order, and the routines have the same names in both knowledges. But the authors changed the code at many places, and each change moves all the code after it. The alignment finds 343 blocks of 8 or more equal bytes, 9855 bytes in total. Between the blocks, 351 ranges of v1 have no match, and 143 of them are 8 bytes or longer (**Code**).

From `$12FC` to the end of the code, v1 is 1 to 351 bytes lower than v2. In `$0A96-$0DBC`, v1 is 3 bytes lower. In `$0E07-$12F9`, v1 is 0 to 4 bytes higher. In the cold start and the interrupt, v1 is 11 to 38 bytes higher. No single relocation gives one build from the other, so each build has its own knowledge and its own source (**Code**).

The table gives the move of each range of v1 and the change that causes it.

| v1 range | v2 range | Move | Cause of the move |
|---|---|---|---|
| `$0900-$091A` | `$0900-$091A` | 0 | The jump table. The targets differ. |
| `$0932-$0950` | `$091E-$093C` | -20 | v1 starts with 20 bytes of KERNAL calls. |
| `$0968-$09DE` | `$0942-$09B8` | -38 | v1 runs the start-up in the cold start. |
| `$09E7-$09EF` | `$09D9-$09E1` | -14 | v2 adds the idle tick test, 24 bytes. |
| `$09F8-$0A7A` | `$09ED-$0A6F` | -11 | v2 reads `$DC0D` at the raster end. |
| `$0A96-$0DBC` | `$0A99-$0DBF` | +3 | The start-up, the buttons and the menu. |
| `$0E07-$12F9` | `$0E07-$12F9` | -4 to 0 | v2 keeps the background colour in zero page. The high-byte tests of the move add bytes. |
| `$12FC-$1585` | `$12FE-$1586` | +1 to +2 | The Box, Fill and Draw tools. |
| `$15C1-$168C` | `$15C4-$169B` | +3 to +15 | The cell-colour cache of v2. |
| `$16AB-$19E1` | `$16CE-$1A04` | +35 | The Xcolor test of v2, 20 bytes. |
| `$19EB-$1E11` | `$1A11-$1E3C` | +38 to +43 | The calls of the tick in `read_cursor`. |
| `$1E1C-$2AAE` | `$1E5D-$2AF0` | +65 to +66 | The colour clear script and the wipe script. |
| `$2B0C-$2D35` | `$2B46-$2D53` | +21 to +62 | Storage: the name cancel and the vector routines. |
| `$2D3C-$33FC` | `$2D7B-$3439` | +61 to +63 | Storage data, Zoom and the picture file. |
| `$345C-$35E5` | `$34A5-$3696` | +73 to +177 | Copy: the button wait, the frame and the clear step. |
| `$360B-$37F3` | `$36BB-$38EF` | +176 to +252 | Swap and Fill. |
| `$3907-$3AB1` | `$3A0E-$3BCC` | +254 to +283 | The end of Fill and the disk protection. |
| `$3ADE-$41F8` | `$3BF9-$4313` | +283 | Drive status, circles and the menu screen script. |
| `$420B-$4522` | `$436A-$4681` | +351 | The script interpreter, after the 68 bytes of the tick. |
| `$5800-$7F3F` | `$5800-$7F3F` | 0 | The title picture. |

## The memory map of both builds

| Part | v1 | v2 |
|---|---|---|
| Jump table and cold start | `$0900-$0968` | `$0900-$0942` |
| IRQ handler | `$0969-$0A3B` | `$0943-$0A30` |
| Timer, screen and start-up | `$0A3C-$0A97` | `$0A31-$0A9A` |
| Menu, menu flash and command tables | `$0A98-$0DCC` | `$0A9B-$0DCF` |
| Drawing tools, from Lines to the tool exit | `$0DCD-$14EC` | `$0DD0-$14EE` |
| Bitmap and text mode, cell colours, Mirror, Oops and Xcolor | `$14ED-$1789` | `$14EF-$17AC` |
| Brush plot, brush shapes and pixel routines | `$178A-$1987` | `$17AD-$19AA` |
| Cursor, pad, hit test and pad smoothing | `$1988-$1D97` | `$19AB-$1DC2` |
| Menu drawing and the scripts of the screens | `$1D98-$25A5` | `$1DC3-$25E7` |
| Hit tables and line drawing | `$25A6-$29C6` | `$25E8-$2A08` |
| Storage screen | `$29C7-$2D3B` | `$2A09-$2D7A` |
| Storage data and tool name labels | `$2D3C-$2F3B` | `$2D7B-$2F7A` |
| Zoom, brush marker and picture file | `$2F3C-$33CF` | `$2F7B-$340D` |
| Copy and Swap | `$33D0-$3658` | `$340E-$3708` |
| Fill and bit pair colour | `$3659-$393C` | `$3709-$3A42` |
| Disk protection and drive status | `$393D-$3A25` | `$3A43-$3B40` |
| Circle and Disc | `$3A26-$3DCB` | `$3B41-$3EE6` |
| Menu screen script | `$3DCC-$4201` | `$3EE7-$431C` |
| Idle tick (play_beep, stop_beep) | - | `$431D-$4360` |
| Script interpreter and opcode routines | `$4202-$44E4` | `$4361-$4643` |
| Reads with all RAM | `$44E5-$4524` | `$4644-$4683` |
| Opcode table, 38 entries | `$4525-$4570` | `$4684-$46CF` |
| Symbol table fragment | `$4571-$462A` | `$46D0-$47FF` |
| TBC joystick routine (crack) | - | `$4800-$4838` |
| Free RAM, script stacks, variables, workspace | `$462B-$5717` | `$4839-$5717` |
| Title code of KTITLE | - (zero bytes) | `$5718-$5796` |
| 8080 bytes of KTITLE | - (zero bytes) | `$5797-$57FF` |
| Title colours, screen and bitmap | `$5800-$7F3F` | `$5800-$7F3F` |
| Background colour of the picture | `$5BFF` | `$E1` |
| Disk command buffer | `$4F6A` | `$4F6E` |

## The differences

### The idle tick

v2 plays a short tick while the stylus is off the pad. v1 is silent: it has no SID code at all (**Code**).

[`v2:read_cursor` `$19FB`](../v2/src/input/cursor.asm#L58) sets `v2:off_pad_beep_on` when the pad Y is `$E6` or more. The test at [`v2:irq_idle_check` `$09BB`](../v2/src/irq/irq.asm#L73) counts `v2:idle_tick_timer` down from 32. At 0 it calls [`v2:play_beep` `$431D`](../v2/src/sound/beep.asm#L6), a triangle wave on SID voice 1. The first read with a touch calls `v2:stop_beep`. [`v1:read_cursor` `$19D8`](../v1/src/input/cursor.asm#L58) has no call of `stop_beep` and no flag (**Code**).

The user of v2 hears a tick each 33 interrupts, about 0.57 seconds on a PAL C64. The tick tells the user that the program waits for the stylus (**Conclusion**).

### The background colour and the zero page

v1 keeps the background colour of the picture at [`v1:background_colour` `$5BFF`](../v1/src/data/title_picture_5bff.asm#L5). This byte is the last byte of the 24 bytes after the colours of the title picture. v2 keeps it in zero page at [`v2:background_colour` `$E1`](../v2/src/constants.asm#L110) (**Code**).

To make space, v2 moves the next variables one byte higher. The cell colours are v1 `$E1-$E3` and v2 `$E2-$E4`. The pixel counts are v1 `$E4-$E6` and v2 `$E5-$E7`. `hit_cell_ptr` is v1 `$E8` and v2 `$E9`. `line_fill_corners` is v1 `$EB` and v2 `$EC` (**Code**).

Each access to the background colour in v2 is one byte shorter. That gives the moves of 0 to -4 in `$0E07-$12F9`. In v2, the background colour and the three cell colours are four bytes in a row. Thus `background_colour,x` gives the colour of the pixel value in X, and Fill uses this read (**Code**). **Conclusion:** the authors moved the colour to zero page for this indexed read.

### The cold start and the interrupt

[`v1:cold_start` `$091B`](../v1/src/init/entry.asm#L23) runs SEI, CLD, LDX #$FF and TXS. Then it calls IOINIT, CINT, RESTOR, UNTLK and UNLSN, and sets the IRQ. It then runs the start-up in line: the menu screen, the place of the protection call at `$0955`, and the picture script. [`v2:cold_start` `$091B`](../v2/src/init/entry.asm#L23) starts with SEI and the IRQ timer. It calls [`v2:start_script` `$0A76`](../v2/src/init/start.asm#L6), which runs the protection, and then jumps to [`v2:start_main` `$0A7F`](../v2/src/init/start.asm#L13) (**Code**).

Thus v1 runs the protection after `init_menu_screen`, and v2 runs it first. v1 also has [`v1:start_script` `$0A81`](../v1/src/leftovers/leftover_0a68.asm#L11), but in the Mayday! release no code calls it. The Mayday! release enters v1 at `$092F` and skips the KERNAL calls (**Code**).

The IRQ vector is [`v1:irq_handler` `$0969`](../v1/src/irq/irq.asm#L6) and [`v2:irq_handler` `$0943`](../v2/src/irq/irq.asm#L6). At the end of a raster interrupt, [`v2:irq_raster_end` `$09EA`](../v2/src/irq/irq.asm#L96) reads `$DC0D`. [`v1:irq_raster_end` `$09F8`](../v1/src/irq/irq.asm#L77) does not (**Code**). **Conclusion:** in v1, a timer interrupt that comes during a raster interrupt runs after the RTI. In v2, the read removes it, and that timer pass does not run.

### The long press

[`v1:long_press_off_pad` `$0AD7`](../v1/src/input/buttons.asm#L15) gives A = `off_pad_count` and keeps the count. [`v2:long_press_off_pad` `$0ADA`](../v2/src/input/buttons.asm#L15) clears the count and gives A = 1 (**Code**).

**Conclusion:** in v2, the next long press needs 16 new reads off the pad. In v1, the count stays at 16 until the stylus touches the pad. A second press off the pad thus counts as a long press at once.

### The move clamp bug of v1

Line, Box and Frame let the user move the whole shape with the stylus. The far end keeps its distance from the cursor. The code limits the far end to `max_x` and `max_y` (**Code**).

[`v1:line_move` `$1097`](../v1/src/tools/line_tool.asm#L62) and [`v1:rect_move` `$123B`](../v1/src/tools/box_frame_tool.asm#L89) compare only the low byte of the sum with the limit. The tests are at `$1136`, `$1158`, `$12DA` and `$12FC`. [`v2:line_move_check_x_max` `$1132`](../v2/src/tools/line_tool.asm#L150) first tests the high byte, and each other test of v2 does the same (**Code**).

The sum is 16 bits. A sum of 256 or more has a low byte below the limit. In v1, the far end then jumps to the left edge or to the top of the picture. In v2 it stops at the right edge or at the bottom (**Conclusion**, no run tested it).

### The cell-colour cache

Each pixel of the picture needs the three colours of its cell. `load_cell_colours` reads them, and it does nothing when the cell is the same as on the last call (**Code**).

[`v2:load_cell_colours` `$15B7`](../v2/src/graphics/colour_slots.asm#L101) compares the cell address with `v2:cell_cache_addr`, and `v2:read_cell_colours` stores the new address (**Code**).

[`v1:load_cell_colours` `$15B6`](../v1/src/graphics/colour_slots.asm#L100) compares the pixel X and Y with `v1:cached_pixel_x` and `v1:cached_pixel_y` at `$0800-$0801`. Only the set-up of the menu writes these bytes, with the value 6. Thus v1 reads the cell colours on each call (**Code**). The result is the same, but v1 does more work for each pixel (**Conclusion**).

### Xcolor

Xcolor replaces one colour of the picture with the current colour. Both builds change the screen nybbles and the colour RAM in the same way (**Code**).

[`v2:tool_xcolor` `$166E`](../v2/src/tools/xcolor_tool.asm#L6) adds two cases. When the user changes the background colour, it calls [`v2:clear_colour_pixels` `$1737`](../v2/src/tools/xcolor_tool.asm#L122) for the old and for the new colour. When the current colour is the background colour, it calls `clear_colour_pixels` in place of the replacement. This routine sets each pixel of the colour to bit pair 0, the background (**Code**).

[`v1:tool_xcolor` `$165F`](../v1/src/tools/xcolor_tool.asm#L6) only writes `$D021` and the background colour in the first case. The same two routines are in v1 at `$1714-$1789`, 118 bytes, but no instruction calls them (**Code**). **Conclusion:** in v1, a pixel can have a colour slot with the background colour. After a change of the background, such a pixel can keep the old colour and show as a spot. In v2 it changes with the background.

### Copy

Copy copies a rectangle of the picture to the place of the cursor. The user marks the rectangle, and then a frame of the same size follows the cursor (**Code**).

[`v2:copy_xor_frame` `$35ED`](../v2/src/tools/copy.asm#L255) keeps the frame on the screen until the cursor moves or the user presses. v2 also waits for the button up at `$347A` before it shows the frame. Before each copy, [`v2:copy_clear_target` `$359B`](../v2/src/tools/copy.asm#L213) sets the target pixels to bit pair 0 where the source pixel is not bit pair 0 (**Code**).

[`v1:copy_show_frame` `$3445`](../v1/src/tools/copy.asm#L68) draws the frame and removes it at once. The frame shows only between the two calls. v1 has no clear step (**Code**). **Conclusion:** the user of v1 sees the frame only as a flicker.

### Fill

Both builds fill from a stack of 3-byte entries at `$C100`. The code around the stack is different (**Code**).

- [`v1:flood_fill` `$3659`](../v1/src/tools/fill.asm#L6) gets the colour with `bit_pair_colour`. Each push goes through [`v1:fill_push_indirect` `$37C7`](../v1/src/tools/fill.asm#L228), a `JMP ($3B)`. The "right" direction code is `$10`.
- [`v2:flood_fill` `$3709`](../v2/src/tools/fill.asm#L6) reads the colour with `background_colour,x`. [`v2:fill_start` `$375D`](../v2/src/tools/fill.asm#L50) sets `line_fill_corners` to 1 when the dither colours differ. [`v2:fill_loop` `$3794`](../v2/src/tools/fill.asm#L77) reads the entry in line, and the "right" code is `$80`.

v2 still writes the vector `$3B/$3C`, but no instruction reads it. v2 also has dead bytes at `$37D0`, `$3805`, `$3812`, `$3819` and `$3829` (**Code**).

These bytes copy the structure of v1. `$37D0` is the code of `v1:fill_stack_prev`. In v1 each direction routine ends with RTS. In v2 they end with a jump to `fill_loop`, and the old RTS stays after the jump at `$3805` and `$3812` (**Code**).

### Storage

Storage loads, saves and names the pictures, and it formats a disk (**Code**).

- **The interrupt.** Before a disk command, [`v1:set_kernal_vectors` `$2C45`](../v1/src/storage/storage_screen.asm#L362) sets the KERNAL IRQ and NMI vectors. The Storage loop calls [`v1:set_program_irq` `$2C60`](../v1/src/storage/storage_screen.asm#L375) on each pass, and it sets the program IRQ again. v2 keeps its own IRQ during the disk work (**Code**).
- **The keys.** v1 reads the keys with GETIN in a loop. [`v2:wait_key` `$2D5A`](../v2/src/storage/storage_screen.asm#L486) lets the IRQ scan the keyboard. It first waits for 10 empty GETIN results, so an old key in the buffer has no effect (**Code**).
- **The empty name.** [`v2:enter_text` `$2CDA`](../v2/src/storage/storage_screen.asm#L407) sets the carry for an empty entry. Then [`v2:storage_name_cancel` `$2C6E`](../v2/src/storage/storage_screen.asm#L336) returns to the Storage screen. [`v1:enter_text` `$2CC1`](../v1/src/storage/storage_screen.asm#L448) gives no such result (**Code**).

Thus in v1 an empty disk name still formats the disk, and an empty picture name still saves the picture. In v2 RETURN without a name stops the action (**Code**). The Storage tests of both builds give a name, so no run tried an empty name (**Observed**).

v1 takes the device number from `$BA`. That is a change of the Mayday! release (switch `CRACK_MAYDAY`), not a change of the original (**Code**).

### The scripts

The program draws its screens with scripts: byte codes that `run_script` executes. The opcode table has the same 38 opcodes in both builds, at [`v1:script_ops` `$4525`](../v1/src/script/opcode_table.asm#L6) and [`v2:script_ops` `$4684`](../v2/src/script/opcode_table.asm#L6) (**Code**).

- **The wipe script.** [`v1:wipe_program_script` `$1E30`](../v1/src/script/picture_buffers.asm#L44) writes zero bytes over `$1000-$4E7F`, without SEI. [`v2:wipe_program_script` `$1E71`](../v2/src/script/picture_buffers.asm#L59) runs SEI and writes zero bytes over `$0900-$477F`. The failed protection runs it (**Code**).
- **The colour clear.** [`v1:clear_colours_script` `$1E09`](../v1/src/script/picture_buffers.asm#L34) fills the colour RAM copy at `$C3E8` with 0. [`v2:clear_colours_script` `$1E34`](../v2/src/script/picture_buffers.asm#L45) fills it with the pair `$00`, `$0B`. Both fill the screen colours at `$C000` with `$E8` (**Code**).

### The title file

v2 has the code of the file KTITLE at [`v2:title_show` `$5718`](../v2/src/leftovers/leftover_5718.asm#L6). It copies the colours to `$D800` and shows the title picture. After it, `$5797-$57FF` holds bytes that decode as 8080 code for CP/M. v1 has zero bytes at `$5718-$57FF`: Mayday! shows the picture with its own code at `$0810` (**Code**).

The bitmap and the screen of the title picture are equal in both builds. The colour block has the same low nybbles, except at `$5800`, the first cell: v1 has `$60` and v2 has `$6D` (**Code**).

### The disk protection

Both builds have a protection in the start-up script, at different places of the disk. [`v1:disk_protection` `$393D`](../v1/src/leftovers/leftover_393d.asm#L6) reads track 33, sectors 5 and 6, with `B-R`. [`v2:disk_protection` `$3A43`](../v2/src/protection/disk_protection.asm#L6) reads track 1, sectors 1 and 2, with `U1` (**Code**). The details are on [protection.md](protection.md).

## Which build is older

v1 is the older build, and v2 is a later build of the same source (**Conclusion**). The evidence:

1. **Remains of v1 in v2.** The dead bytes of the v2 Fill copy the v1 structure, with the RTS of the old subroutines. v2 still writes the fill vector that only v1 reads (**Code**).
2. **Corrections in v2.** v2 corrects the move clamp, makes the cell-colour cache work, and cancels a Storage action without a name (**Code**).
3. **New features in v2.** v2 adds the idle tick, the wait for a clean key and the Copy frame that stays on the screen (**Code**).
4. **Code that v1 does not call yet.** The Xcolor clear routines are in v1, but only v2 calls them. The authors most likely wrote them first and connected them later (**Conclusion**).

Both builds show the same title picture with "Copyright 1983". Thus the title picture does not tell the order of the builds (**Code**).

## Still open

- The original bytes at `$0955` of v1 and the original protection result. No release has them. A dump of an uncracked original disk can answer it.
- The release date of each build. A dated original disk of each build, or a dated advert, can answer it.
- What a user sees with the clamp bug of v1. A run that moves a long line to the right edge can show it.
- The effect of the `$00`, `$0B` colour pair of v2 on a new picture. A run that paints with the third colour slot on a new picture can show it.
- The effect of the copy clear step of v2. A run that copies a rectangle over pixels of other colours in both builds can show it.
