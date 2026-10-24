# The development of Boulder Dash

This page tells how the two builds of Boulder Dash came to be, as the code and the leftovers tell it. Each game file ends with a part of the assembler symbol table of the developer. The two parts give 44 original names, and their values are the addresses of each build. The page also compares the two builds with the release history that a forum post gives. It ends with the parts of the program that the game uses rarely or never.

**Evidence.** **Observed** marks a fact that a run or a byte compare of the files showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge. The label `v1:` or `v2:` gives the project of a name.
- *v1* is the Micro Fun build (US publisher). *v2* is the Statesoft build (UK publisher).
- A *record* is one 12-byte entry of a symbol table leftover. An *original name* is a name in a record, in upper case, for example `MUSPLY`.
- A *global name* is an original name without a colon. A *local name* starts with a colon, for example `:LOOP1`, and belongs to the global name before it.
- A *tick* is one pass of the cave scan, the game logic of one frame.

## The authors and the builds

The game shows its credits on the title: "BY PETER LIEPA" and "WITH CHRIS GREY". The program spells the name "GREY". Other sources write Chris Gray. The texts are the same in both builds. **Code** (`v1:text_by_peter_liepa` and `v1:text_with_chris_grey`).

The game holds no version text and no date of the build. The only year is 1984. The v1 title has "(C) 1984" under "LICENSED FROM FIRST STAR SOFTWARE". The v2 title has "(C)1984" in the First Star Software logo. **Code**.

| Build | Project | Publisher | Game file | Entry | Releases |
|---|---|---|---|---|---|
| v1 | `v1` | Micro Fun | `$5000-$8D8E` (BD.OBJ) | `$8AB3` | CHARSOFT |
| v2 | `v2` | Statesoft | `$5000-$8FFF` | `$8E6A` (tape), `$8E69` (cracks) | STATESOFT, DDC, ROAN |

The program part of v1 is `$5000-$8B85`, 15238 bytes. The program part of v2 is `$5000-$8F3C`, 16189 bytes. The bytes after the program are leftovers (see below). **Code**.

The two builds have the same game. The data `$5000-$66E7` has the same bytes at the same addresses. The only exception is the element handler table at `$5F68`, which holds code addresses. Most code of v1 is in v2 at an address $398 higher, with new 16-bit operands. The differences are on [versions.md](versions.md). **Observed** (byte compare of the files).

## The release lineage

A forum post of LogicDeLuxe on boulder-dash.nl lists four C64 releases of the first Boulder Dash. It gives each release by its memory range and its entry address. The forum post states these values:

| Release | Range | Entry |
|---|---|---|
| Microfun | `$5000-$8B86` | `$8AB3` |
| First Star Software | `$5000-$8F48` | `$8E50` |
| Statesoft | `$5000-$8F3D` | `$8E69` |
| Electronic Arts (Super Boulderdash) | `$4FF4-$8FC0` | `$4FF4` |

The forum post states that Statesoft branched from the First Star release. It lists three changes: the removal of duplicate tables, a faster joystick poll and a fix of the cave selection. The bug let a player select the caves E, I and M on the levels 4 and 5. The forum post also states that Micro Fun branched from Statesoft. It lists three changes: the First Star logo goes, the BD logo has a new layout, and some text is yellow.

Our two builds agree with two lines of the post. The program of v1 ends at `$8B85`, and the program of v2 ends at `$8F3C`. The post gives the end as the first address after the program. Each release of v1 starts at [`v1:cold_start` `$8AB3`](../v1/src/init/cold_start.asm#L9). The cracks DDC and ROAN of v2 start at [`v2:nmi_restart` `$8E69`](../v2/src/init/cold_start.asm#L6), a CLI one byte before `v2:cold_start`. The Statesoft tape loader jumps to `$8E6A`. **Code** / **Observed** (the file ranges and the entries of the releases).

Both builds have the fix of the cave selection. On level 4, the options screen sets the start cave back to A. Joystick right does not change the cave on the levels 4 and 5. **Observed** in the recording `options_two_players`. This agrees with the post: the fix came with Statesoft, and Micro Fun has it from Statesoft (**Conclusion**).

The project has no First Star release and no Electronic Arts release. Thus we cannot check the first two changes of Statesoft, or the code of First Star. The changes of Micro Fun are all in v1: see [The order of the builds](#the-order-of-the-builds) and [versions.md](versions.md).

## The symbol table leftovers

Each game file holds bytes after the end of the program. In both builds these bytes start with a part of a symbol table: original names with their values. No code reads them. **Code**.

- v1: [`v1:symbol_table_leftover` `$8B86`](../v1/src/leftovers/leftover_8b86.asm#L6) fills `$8B86-$8CF1`, 364 bytes. The disk check `v1:disk_protection` and 14 fill bytes follow it up to `$8D8E`, the end of BD.OBJ.
- v2: [`v2:symbol_table_leftover` `$8F3D`](../v2/src/dev/symbol_table.asm#L6) fills `$8F3D-$8FFF`, 195 bytes. It stops at the end of the game file, in the middle of a record.

**Observed** (the bytes of the files).

### The record format

Each record has 12 bytes:

| Bytes | Contents |
|---|---|
| 0-5 | The name in ASCII, 6 characters, with spaces after a short name. A local name starts with `:` and has at most 5 more characters. |
| 6-7 | Always `$A8 $00`. The meaning is not known. |
| 8-9 | The value, low byte first. |
| 10 | `$00` for a global name. For a local name, the number of the global name that it belongs to. |
| 11 | Always `$00`. |

Three records, byte by byte:

| Address | Bytes | Name | Value | Byte 10 |
|---|---|---|---|---|
| v1 `$8BB2` | `4F 50 54 49 4F 4E A8 00 F0 81 00 00` | `OPTION` | `$81F0` | global |
| v1 `$8BBE` | `3A 45 58 49 54 20 A8 00 0E 82 7A 00` | `:EXIT` | `$820E` | `$7A` |
| v2 `$8F8A` | `53 45 54 55 50 30 A8 00 B9 8A 00 00` | `SETUP0` | `$8AB9` | global |

In v1, `OPTION` is at `$81F0`, and its local `:EXIT` at `$820E` is the RTS at the end of the routine. **Code**.

### The number of the global name

Byte 10 of a local name counts the global names. The locals of one global name have the same number, and the next global name gets the next number. In v1 the numbers go from $79 to $7F, and in v2 from $85 to $89. **Observed** (the bytes).

| Global name | v1 number | Global name | v2 number |
|---|---|---|---|
| (the global of `$81D5`) | `$79` | `KEY1` | `$85` |
| `OPTION` | `$7A` | `KEY` | `$86` |
| `OUTWAL` | `$7B` (no locals) | `SETUP0` | `$87` (no locals) |
| `TTSCEN` | `$7C` | `GMINIT` | `$88` |
| `BLUE` | `$7D` | `NXTPLY` | `$89` |
| `YELLOW` | `$7E` | | |
| `MUSPLY` | `$7F` | | |

`FREQ` breaks the rule. It is a global name, but `:LOOPC` after it still has the number $7C of `TTSCEN`. The value of `FREQ` is `$8303`, an address inside the code of `TTSCEN`, not the start of a routine. [`v1:FREQ` `$8303`](../v1/src/title/draw_title_screen.asm#L128) is `tune_freq_table` minus $14. `play_title_tune` reads the table at `FREQ` plus 2 times the note number. Thus `FREQ` is an equate such as `FREQ = TABLE-20`, not a label (**Conclusion**). An equate does not start a new group of locals. **Code** / **Conclusion**.

### The names and the routines

The v1 part covers the values `$81D5-$842E`. The first record lost its name, and the last record breaks off after its name `:LOOP` and the bytes `$A8 $00`.

| Original name | Value | Name in the knowledge |
|---|---|---|
| `OPTION` | `$81F0` | `show_player_options` |
| `OUTWAL` | `$820F` | `draw_steel_border` |
| `TTSCEN` | `$8227` | `draw_title_screen` |
| `:LOOP1`, `:LOOP4` ... `:LOOPC` | `$8229-$8309` | the loops of `draw_title_screen` |
| `FREQ` | `$8303` | `FREQ` (`tune_freq_table` minus $14) |
| `BLUE` | `$838D` | `color_option_digits` |
| `YELLOW` | `$83A1` | `color_status_rows` |
| `MUSPLY` | `$83AC` | `play_title_tune` |
| `MASQUE` | `$842E` | `mask_title_chars` |

The v2 part covers the values `$8A63-$8B1F`:

| Original name | Value | Name in the knowledge |
|---|---|---|
| `KEY1` | `$8A66` | `irq_frame_work` |
| `KEY` | `$8A9B` | `irq_joystick_guard` |
| `SETUP0` | `$8AB9` | `start_cave` |
| `GMINIT` | `$8ADD` | `new_game_players` |
| `NXTPLY` | `$8B05` | `end_turn` |

**Code**.

The knowledge keeps `FREQ` as a name, because the table has no routine at that address. For each other global name, the comment of the routine gives the original name, for example "MUSPLY in the developer symbol table". The original names agree with what the routines do. `TTSCEN` draws the title scene, `OUTWAL` draws the outer wall, and `MUSPLY` plays the music. `BLUE` writes colour 14, light blue, and `YELLOW` writes colour 7. `GMINIT` starts a new game, and `NXTPLY` changes to the next player. **Code**.

`MASQUE` is the French word for "mask". The routine [`v1:mask_title_chars` `$842E`](../v1/src/title/title_animation.asm#L6) builds two title characters with an OR of a scrolled character into two fixed characters (**Code**). The French word is perhaps a joke of the author (**Conclusion**).

The loop names count in hex digits: `:LOOP1` to `:LOOP9`, then `:LOOPA`, `:LOOPB` and `:LOOPC`. The `SK` names mark the targets of skips, and `:EXIT` marks the RTS of a routine. **Code**.

### The values are the addresses of each build

Each value in a part agrees with the address of its build, not with the address in the other build. **Code**.

- v1 `OPTION` = `$81F0`, the address of `v1:show_player_options`. In v2 this routine is at `$8588`.
- v2 `SETUP0` = `$8AB9`, the address of `v2:start_cave`. In v1 this routine is at `$8722`.
- v2 `NXTPLY` = `$8B05`, the address of `v2:end_turn`. In v1 this routine is at `$876E`.

Thus each part comes from the assembly of its own build. Neither part is a copy of the other. The two parts cover different names, so no record occurs in both. **Conclusion**.

The records of both parts start on the same 12-byte grid. v1 has records at `$8B8E` plus 12 times n, and v2 at `$8F42` plus 12 times n. Both start addresses give the remainder 2 when divided by 12. This agrees with a symbol table at the same place in the memory of the assembler (**Conclusion**). A chance of 1 in 12 gives the same result, so this is not a proof.

### How the parts got into the files

Each part starts at the first byte after the program. The game file of v2 ends at `$8FFF`, at the end of a page. Its last record `:SK2` has the low byte $1F of its value `$8B1F` (`v2:end_turn_choose`). The next byte, at `$8FFF`, is $FF and not $8B. Roan's memory image continues with other bytes at `$9000`. **Observed** (the files of DDC and ROAN).

**Conclusion:** the authors saved a fixed memory range, for v2 `$5000-$8FFF`. The program was smaller than this range, so the save also took the bytes after it. These bytes held the symbol table of the assembler from the last assembly.

The default build of v1 omits its 521 bytes after the program: the switch `LEFTOVERS` is 0 and gives a `!skip 521`. The release CHARSOFT sets it to 1. The v2 part stays in each build of v2. The coverage of the runs marks two reads in it, at `$8FE6` and `$8FFC`. A trace of the same runs shows no instruction that reads them. **Observed** (coverage and trace). The two reads are most probably dummy reads of the 6502, not reads of the program (**Conclusion**).

## The order of the builds

The forum post states the order First Star, then Statesoft, then Micro Fun. The code of the two builds agrees with the last step: v1 has edits of a v2-like source. **Conclusion**, from this evidence:

1. **A gap in the loop names of `TTSCEN`.** The v1 part has `:LOOP1` at `$8229` and then `:LOOP4` at `$824E`. In v1, `TTSCEN` has one loop before the credits, `v1:title_copy_picture`. [`v2:draw_title_screen` `$85BF`](../v2/src/title/draw_title_screen.asm#L6) has three loops at the same place: it clears three bands, then it copies the logo words in two loops. Thus `:LOOP2` and `:LOOP3` were in the source, and the Micro Fun change removed them with the logo. **Code** / **Conclusion**.
2. **The author kept the numbers after an edit.** The local names of `GMINIT` in v2 are `:LOOP1`, `:LOOP3` and `:LOOP5`. The routine has the same bytes in both builds, so these gaps are older than both builds. The author did not number the loops again after a removal. **Code** / **Conclusion**.
3. **A branch that became a jump.** The title loop of v2 ends with a `BEQ` back to its start, 107 bytes back. The loop of v1 has 20 more bytes of colour code, and it ends with `BNE` over a `JMP`. Such an edit is typical when new code makes a branch too long. With the final v1 code, a `BEQ` would reach by one byte: the distance is 127 bytes, and a branch reaches 128 bytes back. **Code**. Thus the loop was perhaps longer for a time, or the author changed the branch without a count (**Conclusion**). See [`v1:title_options_loop` `$8518`](../v1/src/title/options.asm#L104).
4. **The Micro Fun changes are additions in v1.** v1 has the two colour routines `BLUE` and `YELLOW`, and v2 has no such routines. The yellow lines of the Micro Fun title come from `YELLOW` and from a colour loop in the title loop. v1 has no First Star logo, and its title picture has a new layout of the BOULDER DASH logo. **Code**. See [versions.md](versions.md).

## Unused and unfinished parts

### The disk check over the end of the symbol table

v1 has a disk check, [`v1:disk_protection` `$8CFF`](../v1/src/leftovers/leftover_8b86.asm#L61), in the bytes after the program. It sends the drive command [`v1:disk_check_command` `$8CF3`](../v1/src/leftovers/leftover_8b86.asm#L58), "U1:5,0,18,18", which reads track 18 sector 18 into the buffer channel 5. Then it reads the drive status. **Code**.

1. When the status starts with "23", a checksum error in a data block, the check closes the channels and jumps to `cold_start`.
2. Any other status writes 0 to `$7000-$70FF`, 32 times. Then the check also jumps to `cold_start`.

**Code**. The range `$7000-$70FF` holds `add_bonus_life`, `add_points`, the cave clock and the end of `handle_amoeba`. A 0 is the opcode BRK. Thus a copy without the bad sector starts, but crashes at the first score or the first clock tick (**Conclusion**).

The data of the check starts at `$8CF2` with the channel name "#". This byte follows the name `:LOOP` and the bytes `$A8 $00` of the last record. Thus the check came after the symbol table was in memory, and it lies over the rest of the table. **Code** / **Conclusion**.

No release calls the check. Each Micro Fun crack that we found starts with SYS 35507, that is `cold_start` at `$8AB3`. **Observed** (the BASIC boot of each crack). The original Micro Fun disk probably started the game at `disk_protection` (**Conclusion**). The project has no original Micro Fun disk, so no run showed it. v2 has nothing like this check (**Code**).

### The bonus life sparkle

When the player gets a bonus life, the spaces of the cave sparkle. [`v1:add_bonus_life` `$7039`](../v1/src/status/score_time.asm#L6) adds a life up to 9 and sets `bonus_life_timer` to $80. While the timer is not 0, the screen drawer calls [`v1:bonus_life_sparkle` `$7454`](../v1/src/screen/space_sparkle.asm#L18) in every second frame. It fills rows 0 and 4 of the four space characters with random bytes and counts the timer down. The last call clears the rows. Thus the sparkle lasts 128 calls, or 256 frames. **Code**.

Only a bonus life starts the timer. A bonus life comes each 500 points and after an intermission. The recording `extras` gets a score of 490, collects one more diamond, and shows the sparkle. **Observed**.

The call comes from `draw_screen` in bank1 at `$9E00`, the copy of the screen drawer that the cold start makes. In the code at `$5000-$8B85` no instruction refers to `bonus_life_sparkle`. Thus a static analysis without the copy finds no caller. **Code**. The cold start copies 512 bytes from `$7B58` to `$9E00`. The drawer takes only the first $139 bytes. The rest of the copy never runs at `$9E00`, because the same code runs at `$7C91` (**Code**).

### The copy of the cave seed

The cave set-up writes the seed of the level to `random_seed1` and to [`v1:random_seed_copy` `$0040`](../v1/src/constants.asm#L26). It writes 0 to `random_seed2` and to `random_seed_copy_hi`. The cave generator `next_cave_random` uses only `random_seed1` and `random_seed2`. No code reads `$40` or `$41`. Both builds have the same code. **Code**.

Perhaps an earlier version used the copy to make the same cave a second time without a new load of the seed (**Conclusion**).

### The second joystick

[`v1:read_joystick_port2` `$6B63`](../v1/src/input/joystick.asm#L11) reads CIA 1 port A, joystick port 2. Only the mode "2 players, 2 joysticks" uses it, and only for player 2. In the other modes both players use port 1. **Code**. The recording `extras` selects this mode with F3 and moves player 2 with port 2. **Observed**.

### The demo

When the title tune plays two times without fire, the title ends and the demo starts. [`v1:run_demo` `$8913`](../v1/src/title/demo.asm#L6) plays cave A at level 1 from [`v1:demo_moves` `$5EA8`](../v1/src/input/demo_moves.asm#L6). Each byte gives a joystick direction in bits 0-3 and a count of ticks in bits 4-7. **Code**.

The table has 63 moves and an end byte $00. The moves give 259 ticks in total, and the first two bytes give 30 ticks without a direction. **Code**. The coverage of the runs shows that the demo plays. The end of the demo has no coverage: no run reached the end byte or pressed fire in the demo. **Observed** (coverage). After the end, the demo ends the cave with `end_cave` when Rockford reached the exit, and it returns to the title (**Code**).

### A test that never succeeds

The options screen tests if `two_players` is $FF, and then adds 1. No code writes $FF to `two_players`, and no run executed the add. **Code** / **Observed** (coverage). The test is perhaps a part of an older player selection (**Conclusion**).

## Conclusion

The leftovers give a clear picture of the work (**Conclusion**):

1. The authors wrote the game in an assembler with short names of 6 characters. The names are global names and local names with a colon. Loops get numbers in hex digits, and the numbers stay after an edit.
2. Each build is a new assembly of the source. The symbol table in each file has the addresses of its own build.
3. The save of each build took a fixed memory range. Thus a part of the symbol table of the last assembly stayed in each file.
4. The Micro Fun build is an edit of the Statesoft source. The edit removed the First Star logo and two loops of the title. It added a new title picture and two colour routines. This agrees with the forum post.
5. Someone added a disk check to the Micro Fun file after the save, over the end of the symbol table. The cracks start the game after the check.
6. The parts that a player sees rarely are complete: the bonus life sparkle, the second joystick and the demo. Of the parts on this page, only the copy of the seed and one test of `two_players` do nothing.
