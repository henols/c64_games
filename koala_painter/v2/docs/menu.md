# The main menu

The main menu is the control screen of Koala Painter. The player moves the pen on the KoalaPad and presses a pad button on a cell. A cell selects a tool, a colour, a brush or a command. The program cannot show the menu and the picture at the same time, because both use the same screen memory and colour RAM. The menu therefore saves the colours of the picture before it draws itself. A tool puts them back when it shows the picture. The player changes between the menu and the picture with one gesture: lift the pen and hold a button.

![The main menu](images/menu.png)

The menu with Draw as the current tool. The Draw label is red in this phase of the flash.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- The *cursor* is the pen position in screen units: `cursor_x` 0-$9F (one multicolour pixel each), `cursor_y` 0-$C7 (one pixel row each). `cursor_x` = $FF means that the pen is off the pad.
- A *cell* is one rectangle of a hit table. A *code* is the byte that the cell gives to the program.
- A *command* is a code from 1 to $11. A *tool* is a command that draws on the picture: Draw to Xcolor (1-$0A), Copy ($0B) and Swap ($0E).
- The *long press* is the gesture of `long_press_off_pad`: the pen is off the pad for 16 reads and a button is down.
- The *undo buffer* is the copy of the picture at `$8000` (bitmap) and `$D000-$D7E8` (colours, RAM under the I/O).
- An *interrupt* is one CIA 1 timer interrupt. The latch is $4289 cycles, so a PAL C64 gets about 58 interrupts each second (**Conclusion**).
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The start code calls [`menu` `$0B05`](../src/menu/menu.asm#L6) one time. It sets Draw as the current tool, colour 0, brush 0 and mirror off. Then it continues into `menu_redraw`, which draws the full menu screen. Each tool, Zoom and Storage jump back to `menu_redraw` when they end. Mirror, Oops and Erase do not change the menu screen, so they return to `menu_refresh` (**Code**).

~~~mermaid
flowchart TB
  A["Draw the menu screen (menu_redraw)"] --> B["Mark the brush and the colour row (menu_refresh)"]
  B --> C["Wait until no button is down"]
  C --> D["Find the cell under the cursor (hit_test)"]
  D -->|no cell, pen on the pad| C
  D -->|no cell, long press| E["Run current_command (run_command)"]
  D -->|cell, no press| D
  D -->|cell, press| F{"Code"}
  F -->|$40-$5F| G["Select the colour"] --> B
  F -->|$80-$8E| H["Select the brush"] --> B
  F -->|1-$11| I["Flash the cell or run the command (SETFLASH)"]
  I --> D
  I --> E
~~~

[`menu_loop` `$0B85`](../src/menu/menu.asm#L67) does these steps (**Code**):

1. It waits until no pad button is down, then it clears `button_press_edge`. Thus the press that ended a tool does not also select a cell. A press before the release is lost. The recordings must press after this wait (**Observed**).
2. [`hit_test` `$1C87`](../src/input/hit_test_1c85.asm#L10) reads the cursor, finds the cell under it and moves the cursor sprites.
3. When no cell is under the cursor and the pen is on the pad, the loop starts again at step 1.
4. When the pen is off the pad, `long_press_off_pad` tests the long press. On a long press, `menu_to_picture` runs `current_command`. Only `menu` and `SETFLASH` write `current_command`, so the long press always starts a tool with a flash cell.
5. When a cell is under the cursor but no new press came, the loop repeats step 2 without the wait.
6. On a press, the code of the cell selects the action. Bit 6 means a colour, bit 7 means a brush, and other codes go to `NEWTOG`, which calls `SETFLASH`.

### The menu screen

The menu is a text screen in VIC-II bank 1. [`build_menu_charset` `$1C2F`](../src/init/menu_charset.asm#L6) runs one time at the start. It makes the ROM visible and runs `menu_charset_script`. That script copies the second charset of the character ROM to `$5000`. Then it writes the frame lines, the tool icons and the colour cells into characters $5E-$F1. The screen is at `$5C00` ($D018 = $74) (**Code**).

The bitmap of the picture is at `$6000` in the same bank, and the picture uses `$5C00` and the colour RAM for its colours. Thus `menu_redraw` must draw the full menu again after each tool. [`menu_screen_script` `$3EE7`](../src/menu/menu_screen_script.asm#L6) does this work. It sets the border and the background registers, fills the colour RAM with 6, and writes the frames, the names and the icons (**Code**).

The menu uses two character modes. The icons in the upper part are multicolour characters, and the palette rows are hires characters. [`irq_handler` `$0943`](../src/irq/irq.asm#L6) makes three raster splits when `menu_irq_on` sets `raster_split_enable` (**Code**):

| Raster line | Change | Next raster line |
|---|---|---|
| 0 | Background white, multicolour on | $B2 |
| $B2 | Multicolour off | $CA |
| $CA | Background = `mix_colour` | 0 |

Text row 0 starts at raster line $33. Thus multicolour ends at text row 16, and the new background starts in text row 18 (**Conclusion**). The dithered colours in rows 21-23 show each colour with `mix_colour` in the clear pixels. In menu.png each dithered cell is a checkerboard of its colour and black, the mix with colour 0 (**Observed**).

## The data

### The hit tables

A hit table gives the rectangles of one screen. Byte 0 is the count of cells. Each cell then has 5 bytes. `hit_table_ptr` points to the table of the screen that shows. `hit_lookup` compares the cursor with each cell in the order of the table. The first cell that holds the cursor gives `hit_code`. No cell gives 0 (**Code**).

| Byte | Meaning | Test |
|---|---|---|
| 0 | Y max | `cursor_y` <= byte |
| 1 | Y min | `cursor_y` >= byte |
| 2 | X end | `cursor_x` < byte |
| 3 | X min | `cursor_x` >= byte |
| 4 | Code | The value for `hit_code` |

`menu_hit_table` at `$260A` has 57 cells: 15 command cells in 3 rows of 5, Oops, 8 brushes, Erase, 16 plain colours and 16 dithered colours. The same format serves `zoom_hit_table` (19 cells) and `storage_hit_table`. The gaps between the cells give no code. Thus a press on a frame line does nothing (**Code**).

### The command codes and the command table

[`run_command` `$0BBB`](../src/menu/menu.asm#L100) multiplies the code by 2 and reads the address from `command_table` at `$0D74`. Then it jumps with `JMP (work_ptr)` at `$0C1E`. A command has a flash cell when `flash_cell_table` at `$0D98` gives an address for it (**Code**).

| Code | Item | Routine | Address | Flash cell | A press in the menu |
|---|---|---|---|---|---|
| 0 | none | `cmd_none` | `$0C21` | none | No cell has this code |
| 1 | Draw | `tool_draw` | `$1444` | `$D829` | Selects the tool |
| 2 | Line | `tool_line` | `$1025` | `$D8C9` | Selects the tool |
| 3 | Lines | `cmd_lines` | `$0DE2` | `$D969` | Selects the tool |
| 4 | Frame | `tool_frame` | `$11C9` | `$D830` | Selects the tool |
| 5 | Circle | `cmd_circle` | `$0EE1` | `$D838` | Selects the tool |
| 6 | Rays | `cmd_rays` | `$0E17` | `$D970` | Selects the tool |
| 7 | Box | `tool_box` | `$1192` | `$D8D0` | Selects the tool |
| 8 | Disc | `cmd_disc` | `$0EA2` | `$D8D8` | Selects the tool |
| 9 | Fill | `tool_fill` | `$13F2` | `$D978` | Selects the tool |
| $0A | Xcolor | `tool_xcolor` | `$166E` | `$D840` | Selects the tool |
| $0B | Copy | `copy_tool` | `$340E` | none | Runs at once |
| $0C | Zoom | `cmd_zoom` | `$0C39` | none | Runs at once |
| $0D | Mirror | `tool_mirror` | `$162D` | none (`$D848` at index $13) | Runs at once, mirror on or off |
| $0E | Swap | `swap_tool` | `$36A8` | none | Runs at once |
| $0F | Storage | `cmd_storage` | `$0C30` | none | Runs at once |
| $10 | Oops | `tool_oops` | `$165E` | none | Runs at once |
| $11 | Erase | `cmd_erase` | `$0C24` | none (`$DA28` at index $12) | First press arms, second press runs |

For the commands 1-6, `run_command` also puts the brush into the cursor sprite. It runs `clear_cursor_script` and the script of the brush from `brush_cursor_scripts`. Box, Disc and Fill keep the plain cursor (**Code**).

### The colours

A colour cell gives $40 + colour for a plain colour, or $50 + colour for a dithered colour. The palette does not show the colours in number order. The hit table gives 0-8, then 11, 9, 12, 10, 13, 15, 14, from left to right (**Code**). menu.png shows the colours in the same order (**Observed**).

[`select_colour` `$0C86`](../src/menu/menu.asm#L211) writes the colour to the border, to `current_colour` and to the 4 bytes of `dither_colours`. The plot code uses entry (y AND 1) * 2 + (x AND 1) of `dither_colours`. A plain colour also becomes `mix_colour`. A dithered colour writes `mix_colour` into entries 1 and 2 instead. The result is a checkerboard of the new colour and the last plain colour (**Code**).

Thus the player mixes two colours in two presses: first the plain colour, then the dithered colour. The lower palette row always shows the mixes with the current `mix_colour` (**Conclusion**). `menu_refresh` puts a mark at column 2 of row 18 or row 21. It uses `menu_mark_upper_colours` when `current_colour` = `mix_colour`, else `menu_mark_lower_colours` (**Code**).

### The brushes

The 8 brush cells give the even codes $80-$8E. [`select_brush` `$0C4D`](../src/menu/menu.asm#L178) stores code AND $7F in `brush_index` and reads `brush_ptr` from `brush_table` at `$0DC0`. Each brush is a list of signed (dx, dy) pairs that ends with $80. The brushes 0, 1 and 5 set `line_fill_corners` to 0, the other brushes set it to 1 (**Code**).

`show_brush_marker` marks the selected brush. It writes colour 6 to 24 cells of the brush row from `$DA87`, then colour 5 to the cell of the brush. `brush_marker_columns` gives that column (**Code**).

## The flash of the chosen cell

The flash shows the current tool. Its label changes between black and red. The labels of Mirror and Erase also flash while these modes are on. This part has 12 upper-case names, for example `SETFLASH`, `FLASHEM`, `DOFLASH`, `ONLSTFX`, `MIRRED`, `FLSHERA` and `NEWTOG`. They come from the symbol table leftover of version 1, at $4571 there. The v1 addresses are 3 lower than the v2 addresses (**Code**).

[`SETFLASH` `$0CC8`](../src/menu/flash.asm#L6) gets a command code in A. Its steps are (**Code**):

1. It stores code AND $1F in `chosen_command` and reads the flash cell of that code.
2. A code without a flash cell goes to `setflash_no_cell`. Erase with `erase_mode` 0 only sets `erase_mode` to 1. Each other code discards the return address and runs `run_command` at once.
3. A code with a flash cell sets `erase_mode` to 0 and clears `pad_read_enable`. The next pad sample sets that flag again.
4. It runs `menu_grid_colours`. That script writes colour 0 to the label rows 1, 5, 9 and 13. Thus the old label stops its flash.
5. It stores the code in `current_command` and sets `flash_enable`.

`irq_flash` counts `flash_timer` down in each timer interrupt. At 0 it calls [`FLASHEM` `$0CF0`](../src/menu/flash.asm#L26) and sets the timer to 20 again. `FLASHEM` changes `flash_colour` between 0 and 2. Then `DOFLASH` paints three cells. Each cell is 6 bytes of colour RAM, the label of one menu cell (**Code**):

- `ONLSTFX` paints the cell of `current_command`.
- `MIRRED` paints the Mirror cell with `flash_colour` when `mirror_mode` is on, else with colour 0.
- `FLSHERA` paints the Erase cell in the same way for `erase_mode`.

Thus each label stays black or red for 20 interrupts, about 0.35 seconds on a PAL C64 (**Conclusion**). No path reaches `COLORCHK` and `NOTCOLOR`, a second colour test (**Code**).

## The undo copy before each command

`run_command` copies the picture to the undo buffer before most commands. It runs `save_undo_script` at `$1E93`. That script copies the bitmap `$6000` to `$8000`, the saved colours `$C000` and `$C3E8` to `$D000` and `$D400`, and the background `$C7D0` to `$D7E8`. It skips the copy for Oops, and when `last_command` is Erase (**Code**).

Oops runs `restore_undo_script` at `$1EB5`, the copy in the other direction. Oops does not write the undo buffer. Thus a second Oops gives the same picture again and is not a redo (**Code**).

The long press from the menu also goes through `run_command`. Thus one Oops cancels all the work of the last visit to the picture (**Conclusion**). The copy also runs before Mirror, Zoom, Storage, Copy and Swap. After Mirror, Oops cannot cancel the drawing before Mirror any more (**Conclusion**). A press on a tool cell, a colour or a brush does not run `run_command`, so it keeps the undo buffer (**Code**). The copy also runs before Erase. The command after Erase skips the copy, so Oops then gives the picture from before Erase (**Conclusion**).

## The start and end of a tool

`run_command` prepares each command in this order: `erase_mode` 0, the screen off, `copy_mode`, the undo copy, `last_command`, then `menu_irq_off`. `copy_mode` gets 2 for Copy after Swap, else 0. `menu_irq_off` stops the raster splits and the flash, sets a white background and clears multicolour. Then `run_command` waits until no button is down (**Code**). The runs did not execute the path of Copy after Swap (**Observed**).

Each tool starts with A/Y = the script of its label sprite and calls [`start_tool` `$0DD0`](../src/tools/tool_start.asm#L6). `start_tool` builds the label, sets the screen on and runs `show_picture_script`. That script sets bitmap mode and copies the saved colours back to `$5C00`, the colour RAM and the background. Then `start_tool` sets the background register to `background_colour` (**Code**).

A tool ends on the long press. It discards its return addresses and jumps to [`tool_exit` `$1495`](../src/tools/tool_exit.asm#L6). `tool_exit` sets mirror mode again when `mirror_choice` is not 0. Copy calls `mirror_mode_off`, and this step puts back the choice of the player (**Conclusion**). Then it runs `save_colours_script`, which copies `$5C00`, the colour RAM and the background to `$C000`, `$C3E8` and `$C7D0`. Last, it jumps to `menu_redraw` (**Code**).

## The state machine of the menu and the picture

The program has no state variable for the screen. The code that runs is the state. `current_command` holds the tool that the long press starts. `erase_mode` holds the first Erase press (**Code**).

~~~mermaid
stateDiagram-v2
  state "Menu" as Menu
  state "Erase armed (erase_mode = 1)" as Armed
  state "Tool on the picture" as Tool
  state "Zoom screen" as Zoom
  state "Storage screen" as Storage
  [*] --> Menu
  Menu --> Menu: tool cell, colour, brush, Mirror, Oops
  Menu --> Tool: long press, or Copy, Swap
  Menu --> Zoom: Zoom
  Menu --> Storage: Storage
  Menu --> Armed: Erase
  Armed --> Menu: Erase (picture cleared), tool cell
  Armed --> Tool: Copy, Swap
  Tool --> Menu: long press
  Zoom --> Menu: end of Zoom
  Storage --> Menu: end of Storage
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Menu | Press on a tool cell (1-$0A) | Menu, new `current_command` | `SETFLASH` |
| Menu | Press on a colour or a brush | Menu | `select_colour`, `select_brush` |
| Menu | Press on Mirror or Oops | Menu | `tool_mirror`, `tool_oops` |
| Menu | Long press | Tool of `current_command` | `menu_to_picture` |
| Menu | Press on Copy or Swap | Tool | `setflash_no_cell` |
| Menu | Press on Zoom | Zoom screen | `cmd_zoom` |
| Menu | Press on Storage | Storage screen | `cmd_storage` |
| Menu | Press on Erase, `erase_mode` = 0 | Erase armed | `setflash_no_cell` |
| Erase armed | Press on Erase | Menu, picture cleared | `cmd_erase` |
| Erase armed | Press on a tool cell | Menu, `erase_mode` = 0 | `SETFLASH` |
| Erase armed | Press on a command $0B-$10 | The state of that command, `erase_mode` = 0 | `run_command` |
| Erase armed | Press on a colour or a brush | Erase armed | `select_colour`, `select_brush` |
| Tool | Long press | Menu | `tool_exit` |
| Zoom screen | The zoom ends | Menu | `cmd_zoom` |
| Storage screen | The player leaves Storage | Menu | `cmd_storage` |

## The worked example

The cursor is at `cursor_x` = $22, `cursor_y` = $30, and the player presses a button. `menu_hit_table` starts at `$260A` with the count $39 (57). `hit_lookup` examines the cells from `$260B` (**Code**):

| Cell | Address | Bytes | Y range | X range | Result |
|---|---|---|---|---|---|
| 1 | `$260B` | `23 05 1E 00 01` | $05-$23 | $00-$1D | $30 > $23, next cell |
| 2-5 | `$2610-$2623` | `23 05 ...` | $05-$23 | | Y max $23 again, next cell |
| 6 | `$2624` | `43 26 1E 00 02` | $26-$43 | $00-$1D | $22 >= $1E, next cell |
| 7 | `$2629` | `43 26 3E 1F 07` | $26-$43 | $1F-$3D | Hit: code $07 |

Code $07 has no bit 6 and no bit 7, so `NEWTOG` calls `SETFLASH`. Entry 7 of `flash_cell_table` is at `$0DA6`: the bytes $D0 $D8 give `$D8D0`. That address is colour RAM offset $D0 = 208 = 5 * 40 + 8: text row 5, column 8. This is the label "Box" in the menu. `current_command` becomes 7, and the Box label flashes. A later long press starts `tool_box` (**Code**).

The cursor units give the same place: X $1F-$3D is text columns 7-15 at 4 units for each column. Y $26-$43 is text rows 4-8 (**Conclusion**).

## Still open

- No run pressed Erase two times. The code from `$0C21` to `$0C2F` and `run_script_1e7c` did not execute. A recording that presses Erase twice and then Oops can show the undo after Erase.
- No run used Copy after Swap (`$0BD5-$0BDC`). A recording with Swap, then Copy, can show the effect of `copy_mode` = 2.
- No run showed the loss of the undo picture after Mirror. A recording with Draw, Mirror and Oops can show it.

The reference has each routine and each table entry: [menu](reference/modules/menu/menu.md), [flash](reference/modules/menu/flash.md), [tables](reference/modules/data/menu_tables.md), [hit tables](reference/modules/data/menu_zoom_hit_tables.md).
