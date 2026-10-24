# The Micro Fun build and the Statesoft build

Boulder Dash exists in two builds of the same game. The project `v1` is the Micro Fun build, and the project `v2` is the Statesoft build. The caves, the elements, the sound and the play are the same. The builds differ in the title screen, in the colours of the title, and in the bytes after the program. This page lists each difference and tells how the code moved. The history of the two builds is on [development.md](development.md).

**Evidence.** **Observed** marks a fact that a run or a byte compare of the files showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge. The label `v1:` marks a name of the Micro Fun build, and `v2:` a name of the Statesoft build.
- In the tables, the column v1 gives the address in v1 and the column v2 the address in v2. A dash means that the build does not have the part.
- A *move* is the v2 address minus the v1 address, for example +$398.
- The *map* is the title screen at `$0800`. Each character of a text line takes two map cells, the character and the character plus $34.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## Overview

The two game files have the same data at `$5000-$66E7`. Only one table differs there: the element handler table at `$5F68` holds 60 bytes of code addresses, and the code moved. **Observed** (byte compare of the files).

The code follows the title data. In v1 it fills `$6AD0-$8B85`, and in v2 `$6E68-$8F3C`. The v2 program is 951 bytes ($3B7) longer. **Code**. The differences:

1. **The title data.** v1 has one title picture of 1000 bytes. v2 has a logo in text characters and a First Star Software logo in bitmap cells, 1920 bytes together. This moves the start of the code by +$398.
2. **The title code.** v2 draws the logo and a frame, and it shows the bitmap logo in the lower rows. v1 copies its picture and shows the lower rows from a second screen.
3. **The colour routines.** v1 has two colour routines and more colour writes on the title. They give the yellow lines and the light blue digits of the Micro Fun title. v2 has only the light blue digits.
4. **The end of the file.** Both files hold a part of a symbol table after the program. Only v1 has a disk check there.

**Code**.

## How the code moved

Most of the code keeps its order and its bytes. Only the 16-bit operands change, because each address moved. In `$6AD0-$8226` of v1, 678 of 5975 bytes differ from v2 at the address plus $398. Each difference is the low byte or the high byte of a moved address. **Observed** (byte compare).

The move changes in each routine where one build has more bytes than the other:

| v1 | v2 | Move | Contents and cause |
|---|---|---|---|
| `$6AD0-$8226` | `$6E68-$85BE` | +$398 | The title data of v2 is 920 bytes longer. |
| `$8227-$8316` | `$85BF-$86DD` | changes | `draw_title_screen`: v2 has three loops in place of one (+26 bytes) and a frame (+21 bytes). |
| `$8317-$838C` | `$86DE-$8753` | +$3C7 | The frequency table and the animation flags of the caves. |
| `$838D-$83AB` | - | - | The colour routines `BLUE` and `YELLOW` of v1, 31 bytes. |
| `$83AC-$8517` | `$8754-$88BF` | +$3A8 | The title tune, the title interrupt work and the options keys. |
| `$8518-$859A` | `$88C0-$892B` | changes | The title loop: v1 has 20 more bytes of colour code, and `BNE` and `JMP` in place of `BEQ`. |
| `$859B-$861A` | `$892C-$89AB` | +$391 | `run_title` and the title split values. |
| `$861B-$8655` | `$89AC-$89EC` | changes | `title_screen_setup`: v2 covers the lower rows (+19 bytes), v1 calls the colour routines (+13 bytes). |
| `$8656-$8979` | `$89ED-$8D10` | +$397 | The interrupt, the game turns, the scores, the play loop and the demo. |
| `$897A-$8A14` | `$8D11-$8DCB` | changes | `init_screens`: v1 fills the two game screens (+37 bytes), v2 copies the First Star logo (+69 bytes). |
| `$8A15-$8B85` | `$8DCC-$8F3C` | +$3B7 | The variables, the interrupt set-up and the cold start. |

**Code** (the addresses of the same names in both knowledges).

The equate `FREQ` shows how the moves work. In both builds `play_title_tune` reads the notes at `tune_freq_table` minus $14. This operand is `$8303` in v1 and `$86CA` in v2. It moves +$3C7 with the table, although the value lies in the code of `draw_title_screen`, which moves +$3B2 there. **Code**.

The cold start copies 512 bytes of code to `$9E00`, the screen drawer `draw_screen` in bank1. v1 copies `$7B58-$7D57` and v2 copies `$7EF0-$80EF`. The two copies differ only in 40 operand bytes. The drawer calls two routines in the main code, and the rest of the copy holds code that moved. **Observed** (byte compare).

The entries keep the same form. [`v1:cold_start` `$8AB3`](../v1/src/init/cold_start.asm#L9) and [`v2:cold_start` `$8E6A`](../v2/src/init/cold_start.asm#L9) each have `nmi_restart`, a CLI, one byte before them. RESTORE jumps there in both builds. **Code**.

## The title screens

![The title of the Micro Fun build](images/title_micro_fun.png)

The image shows the title of v1. Yellow lines "MICRO FUN * MICRO FUN" frame the screen. The logo has a frame of blocks from map row 2. The licence lines "LICENSED FROM FIRST STAR SOFTWARE" and "(C) 1984" fill the lower rows. **Observed** (screen capture).

![The title of the Statesoft build](images/title_statesoft.png)

The image shows the title of v2. The BOULDER DASH logo has a frame from map row 0. The lower rows show the First Star Software logo with a shooting star and "(C)1984". **Observed** (screen capture).

### The picture of v1

[`v1:title_screen` `$66E8`](../v1/src/data/title_screen_text.asm#L6) is a full screen of 40 by 25 screen codes. It holds "MICRO FUN PRESENTS" in rows 0-1 and the framed logo in rows 2-18. The licence lines are in rows 19-22, and a second "MICRO FUN" line is in row 23. **Code**.

[`v1:draw_title_screen` `$8227`](../v1/src/title/draw_title_screen.asm#L6) copies the bytes 0-767 to the map at `$0800`. It also copies the bytes 744-999 to `$0EE8`, the same rows of the game screen at `$0C00`. The title interrupt then changes `$D018` to $38 from raster line $C2. Below that line, the VIC-II shows the second screen with the licence lines. **Code**.

### The logo of v2

v2 builds the same logo from smaller data. [`v2:title_logo_boulder` `$66E8`](../v2/src/data/title_logo.asm#L6) holds the word BOULDER, and `v2:title_logo_dash` at `$67E8` holds the word DASH. Each word is 16 cells for the top row and 240 cells for 6 more rows. The cells are text characters: $03 is a block, $08-$0A are edges and $1D-$1F are the TM sign. **Code**.

[`v2:draw_title_screen` `$85BF`](../v2/src/title/draw_title_screen.asm#L6) works in three steps:

1. It clears the map rows 1-2, 9-10 and 17-18.
2. It copies BOULDER to the map rows 2-8 and DASH to the rows 10-16.
3. After the text lines, it draws a box of element $03 around the map rows 0-18, 40 cells wide, with `draw_box_outline`.

The same box routine draws the steel border and the box objects of the caves. **Code**.

| Part | v1 | v2 |
|---|---|---|
| Title data | `$66E8-$6ACF`, 1000 bytes | `$66E8-$6E67`, 1920 bytes |
| Logo | in the picture, frame from map row 2 | two words, frame from map row 0 |
| Top rows | "MICRO FUN PRESENTS" | part of the frame |
| Lower rows (credits shown) | licence lines from the screen at `$0C00` | First Star logo in bitmap mode |
| Split line | $C2 | $CA |
| Split values (`$D011`, `$D016`, `$D018`, `$D012`) | `$1B,$1B`, `$18,$18`, `$38,$28`, `$28,$C2` | `$3B,$1B`, `$18,$18`, `$28,$28`, `$28,$CA` |

**Code** (`v1:irq_title_values` at `$860B`, `v2:irq_title_values` at `$899C`).

### The options rows

The options use the same lower rows as the licence lines or the bitmap logo. Both builds change the split values when F1 shows the options. v1 writes $28 to the `$D018` value, so the lower rows show the map again. v2 writes $1B to the `$D011` value, so the lower rows show text again. Thus the two builds handle the same case with a different register. **Code**.

## The First Star logo bitmap

Only v2 has the First Star Software logo. [`v2:first_star_logo_r19_right` `$68E8`](../v2/src/data/first_star_logo.asm#L6) starts 1408 bytes of multicolour bitmap cells, 8 bytes for each cell. The data has 8 blocks: the columns 16-39 of the rows 19-24, and the columns 0-15 of the rows 23 and 24. The other cells of the rows 19-22 are empty. **Code**.

[`v2:init_screens` `$8D11`](../v2/src/init/init_screens.asm#L21) copies the blocks to `$37C0-$3F3F`. With `$D018` = $28, the bitmap starts at `$2000`, so these bytes are the bitmap rows 19-24. The bitmap rows 0-18 would be the two character sets, but the title uses bitmap mode only below line $CA. **Code**.

The space fits closely. The sprite data at `$3780-$37BF` ends one byte before the logo rows at `$37C0` (**Code**). The bitmap uses the map rows 19-24 as its screen colours. When the credits show, `v2:title_screen_setup` fills these 240 cells with $6E: colour 6 (blue) and colour 14 (light blue). **Code**.

v1 has no bitmap and no copy loop. Its `init_screens` fills the top row of the screen at `$0C00` with spaces, and the two game screens with character $60. v2 does not fill the screens. **Code**.

## The colour routines

The Micro Fun title has more colours. v1 has two routines that v2 does not have:

- [`v1:color_option_digits` `$838D`](../v1/src/title/title_colours.asm#L6) writes colour 14 to the player, joystick, cave and level digits. The symbol table calls it `BLUE`.
- [`v1:color_status_rows` `$83A1`](../v1/src/title/title_colours.asm#L18) writes colour 7 to the two top rows, the "MICRO FUN" and "PRESENTS" lines. The symbol table calls it `YELLOW`.

**Code**.

The title loop of v1, [`v1:title_options_loop` `$8518`](../v1/src/title/options.asm#L104), has three more colour writes. While the credits show, it writes colour 7 to rows 0 and 23 in each pass. When F1 opens the options, it fills the colour RAM with colour 9 from offset $50. While the options show, it calls both colour routines in each pass and writes colour 1 to the cave line. **Code**.

[`v2:title_options_loop` `$88C0`](../v2/src/title/options.asm#L107) keeps only the light blue digits. It writes colour 14 to the same four digit pairs with an inline loop, `v2:options_colour_digits`. The loop is the body of `BLUE` without the call. **Code**.

The set-up of the title has the same difference. `v1:title_screen_setup` calls `YELLOW`, and it calls `BLUE` when the options show. Then it draws the title. `v2:title_screen_setup` draws the title first and calls no colour routine. **Code**.

The forum post on [development.md](development.md#the-release-lineage) states that Micro Fun added yellow text. These routines and writes are that change (**Conclusion**).

## The end of the file

Both game files continue after the program with a part of the developer's symbol table. The details and the decoded records are on [development.md](development.md#the-symbol-table-leftovers).

| Part | v1 | v2 |
|---|---|---|
| End of the program | `$8B85` | `$8F3C` |
| Symbol table part | `$8B86-$8CF1`, 364 bytes | `$8F3D-$8FFF`, 195 bytes |
| Original names | `OPTION` to `MASQUE` | `KEY1` to `NXTPLY` |
| Disk check | `$8CF2-$8D80` | - |
| Fill bytes | `$8D81-$8D8E` | - |
| End of the file | `$8D8E` | `$8FFF` |
| In the default build | no (`LEFTOVERS` = 0) | yes |

**Observed** (the files).

The v1 part ends in the middle of a record, where the data of the disk check `v1:disk_protection` starts. No release calls the check. The v2 part ends at the last byte of the file, also in the middle of a record. **Code** / **Observed**.

The default build of v1 omits its 521 bytes after the program, because nothing uses them. The default build of v2 keeps its part, because the coverage marks two reads in it. A trace shows no instruction that reads them, so they are most probably dummy reads of the 6502 (**Conclusion**).
