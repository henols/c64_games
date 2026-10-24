# The development of Hover Bovver

This page tells what the program shows about its development. The facts come from the code, the texts and the leftovers of the block `$6000-$9FFF`. The block holds the bytes of the TFP release, the base release of the knowledge. The page also compares the C64 program with the instructions of the Atari 8-bit version. The [releases page](releases.md) tells about the cracks.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- The *block* is the memory `$6000-$9FFF`. It holds the tunes, the graphics, the setup code and the game.
- A *leftover* is a range of bytes that the game does not use.
- A *pass* is one run of the main loop.
- **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code or the bytes only. **Conclusion** marks an interpretation.

## The authors and the version

The title screen shows the credits from [`text_title_presents` `$830D`](../src/text/title_credits.asm#L6). The lines are "LLAMASOFT PRESENTS... JEFF MINTER'S", "MUSICAL ARRANGEMENTS BY JAMES LISNEY", "GAME PROGRAMMED BY JEFF MINTER" and "GAME DESIGN BY P.K. AND J.C. MINTER". The last line gives the year 1983 and "LLAMASOFT SOFTWARE". The program has no version text (**Code**).

Jeff Minter put his initials into the game two times (**Code**):

- [`lender_names` `$8AB6`](../src/status/draw_status.asm#L88) holds JIM, TOM, ALF and JCM. Gordon borrows the mowers of the first three. The status line shows the name of the lender with the mower number 1-3. At the number 4 the game of the player ends. Thus JCM is a fourth name that the normal play does not need.
- [`initial_hiscore_table` `$9E43`](../src/scores/hiscores.asm#L82) gives the names JCM, NOT, TEG, ZAP and POW, each with the score 0000000. The high-score screen has the title "MEGA  MOWER  MANIACS".

## The block and its save

The block has the parts of this table (**Code**).

| Range | Content | Run-time place |
|---|---|---|
| `$6000-$63BF` | the tune data | stays in place |
| `$63C0-$63FF` | a part of the source text | not used |
| `$6400-$67FF` | the charset, characters 0-127 | `$2000-$23FF` |
| `$6800-$6BFF` | a part of the memory of the assembler | `$2400-$27FF` |
| `$6C00-$7BFF` | 64 sprites | `$3000-$3FFF` |
| `$7C00-$7DDA` | the high-score screen and the setup screen | stays in place |
| `$7DDB-$7DFF` | fill bytes | not used |
| `$7E00-$7E62` | the copy routine of the graphics | stays in place |
| `$7E63-$7FFF` | NOP fill | not used |
| `$8000-$9FD4` | the game | stays in place |
| `$9FD5-$9FFF` | free bytes | not used |

At the cold start, [`copy_graphics` `$7E00`](../src/init/copy_graphics.asm#L6) copies `$6400-$6BFF` to `$2000-$27FF` and `$6C00-$7BFF` to `$3000-$3FFF`. The routine only copies. It does not unpack, although its name says so (**Code**).

The charset and the sprites thus have the offsets `$4400` and `$3C00` in the block. The memory `$2800-$2FFF` is not in the block (**Code**). **Conclusion**: Minter kept the graphics at their run-time addresses while he worked. For the file, he moved `$2000-$27FF` and `$3000-$3FFF` into the free space of the block. The range `$2000-$27FF` took with it the memory above the charset.

The TFP release starts with BASIC that holds the end of an older line, `MAIN",1,1:` at `$08F8` (**Code**). **Conclusion**: the loader of the original tape loaded a file with the name MAIN, and that file was most likely this block.

## The assembler in the charset

The bytes `$6800-$6BFF` go to `$2400-$27FF`, the characters 128-255 of the charset. The game does not use these characters (**Code**). The bytes are not graphics. They are a part of the memory of the assembler that Minter used. [`asm_leftover_2400` `$6800`](../src/data/assembler_leftover.asm#L6) starts the leftover in the source.

The leftover has four parts (**Code**):

1. **The error messages.** Records of 21 characters, padded with `*`. Examples are "DUPLICATE SYMBOL", "IMPROPER OPCODE", "RAN OFF END OF CARD" and "BRANCH OUT OF RANGE". Others are "MACRO STACK FULL", ".MAC WITHIN .MAC", ".MND UNMATCHED" and "TOO MANY (>9) PARAMS".
2. **The address table of the messages** at `$6A1B`. It has 29 words, from `$23F9` to `$2606`. Three words are `$0000`, so three error numbers have no message.
3. **The powers of ten** at `$6A55`: 1, 10, 100, 1000 and 10000, with the 5 low bytes first and then the 5 high bytes.
4. **6502 code** from `$6A5F` to `$6BFF`. It calls the KERNAL routines CHKIN, CHRIN, CHKOUT, CHROUT, CLRCHN, CLOSE, STOP and GETIN. At `$6BA6` it also calls `$E716`, the screen output of the C64 KERNAL.

The addresses of the leftover fit the place `$2400-$27FF`. The table points to the messages at `$23F9-$261A`, and the code jumps to `$2663` and `$2711`. These targets are in the same range (**Code**). The code also uses variables at `$0839-$098E` and calls routines up to `$2D40` (**Code**). **Conclusion**: the assembler occupied the memory from about `$0800` to above `$2D00`. The call of `$E716` shows that it ran on a C64.

The first message starts at `$23F9`, 7 bytes before the end of the charset. In the block, `$67F9-$67FF` holds the last 7 bytes of character 127, and the leftover starts with "ED SYMBOL". The address table and the length of the records show that the first message was "UNDEFINED SYMBOL" (**Code**). The charset wrote over the start of this message.

**Conclusion**: the charset came into `$2000-$23FF` after the assembler was in memory. The save took `$2000-$27FF`, so the upper half of the charset holds the memory of the assembler.

The messages name the directives `.MAC` and `.MND`, and six messages are about macros (**Code**). **Conclusion**: Minter used a macro assembler. The word CARD in "RAN OFF END OF CARD" points to an older assembler for punched cards. The name of the assembler is not known.

## The source text of lawn 14

The 64 bytes at [`source_text_leftover` `$63C0`](../src/data/source_leftover.asm#L6), after the tune data, are ASCII text (**Code**):

```text
$63C0  ,3,3,6,6,9,$F6,31,3,6,6,9          the end of a source line
$63D9  00 05 64 C4                         four bytes that are not text
$63DD  ; .BYTE $F6,0,16,40,1,4,$F6,10,7,20 the next line, cut at $63FF
```

The values are the bytes `$8ED9-$8EED` of the game, in [`lawn_layouts` `$8C6E`](../src/data/lawn_layouts.asm#L6). These bytes are a part of the layout of lawn 14 (**Code**):

| Bytes | Record |
|---|---|
| `$F6`,3,3,6,6,9 | a ring bed of flowers at column 3, row 3, 6 x 6 |
| `$F6`,31,3,6,6,9 | a ring bed of flowers at column 31, row 3, 6 x 6 |
| `$F6`,0,16,40,1,4 | a row of flowers at column 0, row 16, 40 x 1, colour 4 |
| `$F6`,10,7,20,... | a bed of flowers at column 10, row 7, width 20. The height 3 and the colour 7 follow in the game. |

The first `$F6` of the first line is at `$8ED8` in the game. It is not in the leftover, because the line starts before `$63C0` (**Code**).

The text tells how Minter wrote the layouts (**Conclusion**):

- He wrote each layout as `.BYTE` lines in the source.
- He wrote the flower character as `$F6` in hex and the columns, rows and sizes in decimal.
- He put two records in one line.

The four bytes `$00 $05 $64 $C4` are between the lines. The `$00` ends a line. **Conclusion**: the other three bytes are a line header of the editor, for example a link or a line number.

The second line starts with a semicolon. In most 6502 assemblers a semicolon starts a comment. But the game has the bytes of this line (**Code**). **Conclusion**: the text in memory was possibly not the same as the source of the game. Or this assembler does not read `;` as the start of a comment.

**Conclusion**: the source text was in the memory `$63C0-$63FF` when Minter saved the block. The tune data ends at `$63BF`, so the save took the rest of the text with it.

## The fill bytes and the free bytes

The block has four more ranges that the game does not use (**Code**):

| Range | Bytes | Comment |
|---|---|---|
| `$7DDB-$7DFF` | `$FF` x5, `$00` x29, `$FF`, `$00` x2 | after the setup screen |
| `$7E63-$7FFF` | `$EA` (NOP) up to `$7FFE`, then `$00` | after the copy routine |
| `$81C1` | `$0C` | one byte between the two tables of the notes |
| `$9FD5-$9FFF` | `$FF` x11, `$00` x27, then "LMONN" | after the last code |

The NOP fill closes the gap between the copy routine and the game at `$8000` (**Code**). **Conclusion**: the game starts at a fixed address, `$8000`, and the fill holds the bytes up to it.

"LMONN" at `$9FFB` is ASCII. Only TFP has these five bytes. KSX has `$FF $FF $FF $00 $00` there, and HF has `$00 $00 $00 $00 $2A` (**Observed**: a byte compare of the captures). TFP is a memory dump. **Conclusion**: "LMONN" can be a part of the original file or RAM of the computer that made the dump. The project cannot tell which.

## The bugs of the development

### The speed of the lawns

At the start of a lawn, the code at `$9021` sets two speeds from the lawn number (**Code**):

- [`actor_speed` `$50`](../src/constants.asm#L61) is the count of passes between two moves of the actors. A smaller value gives faster actors.
- [`loyalty_rate` `$60`](../src/constants.asm#L76) is the count of calls between two steps of the DOG LOYALTY scale while Rover attacks. A smaller value empties the scale faster.

After lawn 16 the code sets the maximum speed: `actor_speed` = 4 and `loyalty_rate` = 2. For lawns 1-16 it goes to [`speed_by_lawn_number` `$9042`](../src/actors/actor_speed_setup.asm#L23) (**Code**):

```text
$9042  LDX lawn_number      ; the value goes to X
$9044  JSR divide_by_4      ; but the routine divides A
$9047  STA $07
$9049  LDA #$06
$904B  SEC
$904C  SBC $07              ; loyalty_rate = 6 - A/4
```

A is 0 at `$9042`, because the AND before the branch gave 0. Thus `loyalty_rate` is always 6 on lawns 1-16 (**Code**). **Conclusion**: Minter wanted `LDA lawn_number`. Then `loyalty_rate` goes from 6 on lawns 1-3 down to 2 on lawn 16. The value 2 after lawn 16 continues this series.

`actor_speed` has a second error. The code computes 12 - (lawn number AND 15) / 2. Lawn 15 gives 5, but lawn 16 gives 12, the value of lawn 1 (**Code**). **Conclusion**: the AND was not necessary. Without it lawn 16 gives 4, and the value 4 after lawn 16 continues the series.

| Lawn | `actor_speed` | `loyalty_rate` | `loyalty_rate` with LDA (**Conclusion**) |
|---|---|---|---|
| 1 | 12 | 6 | 6 |
| 4 | 10 | 6 | 5 |
| 8 | 8 | 6 | 4 |
| 12 | 6 | 6 | 3 |
| 15 | 5 | 6 | 3 |
| 16 | 12 | 6 | 2 |
| 17 and higher | 4 | 2 | 2 |

In practice the neighbour and Rover get faster from lawn 1 to lawn 15. Lawn 16 is as slow as lawn 1. The DOG LOYALTY scale empties at the same rate on all 16 lawns (**Code**). The instructions say "Neighbour and dog speeds increase" (**Observed** in the HF docs).

### Message 10

[`msg_hit_the_dog` `$9CE1`](../src/text/messages.asm#L65) is message 10, "DAMNATION!!  I'VE HIT THE DOG!". The code at `$977A-$9782` prints it. No instruction jumps to `$977A` (**Code**). The loop at [`hit_dog_fill_overload` `$976A`](../src/actors/actor_collision.asm#L116) fills the MOWER OVERLOAD scale. Its exit at `$976E` goes to `$9783`, past the print. No run executed `$977A-$9782` (**Observed**: the coverage of all recordings).

The text has 41 bytes, one byte more than a row of 40 characters (**Code**). **Conclusion**: Minter removed the message from the play, possibly because it did not fit the row. The other messages have 40 characters.

### Other small traces

- `$8BDD` in the layout reader: `CMP #$1B`, then `BNE` to the next instruction. Both results go on to `$8BE1`, so the compare has no effect (**Code**). **Conclusion**: a test of a record type that Minter removed.
- [`install_interrupts` `$8076`](../src/irq/interrupts.asm#L6) starts with `LDX #$2F`, and nothing uses X. At `$8083` a `JMP` goes to the next instruction at `$8086` (**Code**). **Conclusion**: the NMI part was a separate routine before.
- `$80A2` writes the value of `$D011` to `$D412`, the control register of voice 3. The next instruction writes it back to `$D011` with bit 7 clear (**Code**). **Conclusion**: the write to `$D412` is a slip, possibly for a store to a variable.
- The game has tables for four actors, for example a fourth sprite colour, light red. `actor_count` is at most 3, so actor 4 never moves (**Code**). **Conclusion**: Minter planned a fourth actor.

## The NTSC note table

The tune player reads the SID frequencies from [`note_freq_lo` `$8184`](../src/music/note_frequencies.asm#L6) and [`note_freq_hi` `$81C2`](../src/music/note_frequencies_81c2.asm#L6). Each table has 61 notes, one semitone apart. The tunes use the notes 19-57 (**Code**).

Note 0 is `$0218`. With the NTSC clock of 1022727 Hz this is 32.7 Hz, the note C-1. With the PAL clock of 985248 Hz the same value gives 31.5 Hz. Note 57 is `$3863`, 880 Hz with the NTSC clock, the note A-5. With the NTSC clock, all 61 values are within 3 cents of equal temperament (**Code**).

On a PAL C64 the SID clock is 3.7% slower. Thus the tunes play about 0.65 semitone lower than on an NTSC C64 (**Conclusion**). The interrupt also comes 50 times each second, not 60 times. One step of the tune takes 3 interrupts (**Code**). Thus the tunes play at 5/6 of the NTSC tempo on PAL (**Conclusion**).

**Conclusion**: the game uses a note table for the NTSC C64. The table possibly comes from a published table.

## The relation to the Atari 8-bit version

The HF release shows instructions in its docs viewer before the game (**Observed**: a run of the HF disk). The text names the keys OPTION, SELECT and START. These are the console keys of the Atari 8-bit computers, and the C64 does not have them (**Observed**). **Conclusion**: HF used the instructions of the Atari 8-bit version.

The instructions and the C64 code agree in most points:

| Point | Atari instructions | C64 code |
|---|---|---|
| Joystick of player 1 | "Port 1" | `joy_port` = 1 reads port 1 |
| Entry lawn | FIRE, lawns 1-8 | F1, lawns 1-8 |
| Number of players | OPTION, 1 or 2 | F3, 1 or 2 |
| Number of sticks | SELECT, 1 or 2 | F5, 1 or 2 |
| Start | START | F7 |
| Pause | "+ letter P", any key continues | C= + P, any key continues |
| Music | M | C= + M |
| Lenders | Jim, Tom and Alf | JIM, TOM, ALF |
| After lawn 16 | "the speed is put at MAXIMUM", then lawn 1 again | maximum speed, layout of lawn 1 |
| Number of lawns | "There are 18 in all" | 16 layouts |
| Speeds | "Neighbour and dog speeds increase" | see the speed bug above |

The C64 setup screen keeps the order of the Atari controls. F1, F3, F5 and F7 take the places of FIRE, OPTION, SELECT and START (**Code**). [`setup_screen` `$7CDE`](../src/setup/setup_screen.asm#L6) reads the keys, and [`check_keys` `$9D0B`](../src/input/keys.asm#L6) reads C= + M and C= + P.

The number of lawns does not agree. The instructions say 18, but the game has 16 layouts and uses the lawn number AND 15 (**Code**). **Conclusion**: the Atari version possibly has 18 lawns, or the text has an error. The instructions say that the speed goes to the maximum after lawn 16. This agrees with the C64 code, so the "18" is most likely an error of the text.

## What the cracks did to the leftovers

All three releases are cracks. Two of them changed the leftovers (**Observed**: a byte compare of the captures):

- **KSX** changed 16 addresses in the code of the assembler leftover at `$6A9C-$6BFD` by `-$1BFC`. For example, `JSR $27FE` became `JSR $0C02`. [`copy_graphics` `$7E00`](../src/init/copy_graphics.asm#L6) of KSX copies the last page of the leftover to `$0B04`, not to `$2700`. **Conclusion**: Kraksnax treated the leftover as code of the game and moved it.
- The same change hit [`scale_chars` `$922B`](../src/status/scale_chars.asm#L6). In TFP the table starts with `$20 $2A $29`. These bytes look like `JSR $292A`, and KSX has `$20 $2E $0D`, the "JSR" moved by `-$1BFC`. The scales of KSX thus show two other characters at two of their 8 steps (**Code**). **Conclusion**: a tool for the relocation found the false JSR and changed it. This is a bug of the KSX release.
- **HF** has `$FF` at `$63C0-$7BFF`. The source text, the charset, the assembler leftover and the sprites are not in its block. HF puts the graphics in place with its own loader.

Thus only TFP and KSX keep the two leftovers of the development, and only TFP keeps them without a change.

## What the development tells

**Conclusion.**

1. Jeff Minter wrote the game in a 6502 macro assembler on a C64. The assembler lived in the memory from about `$0800` to above `$2D00`.
2. He kept the charset at `$2000` and the sprites at `$3000` while he worked. The charset damaged the start of the error messages of the assembler.
3. He made the file from one block `$6000-$9FFF`. The block took a part of the source text and a part of the assembler with it.
4. He wrote the lawn layouts as `.BYTE` lines, with the flower character in hex and the positions in decimal.
5. The tunes use an NTSC note table, so a PAL C64 plays them lower and slower.
6. He removed message 10 from the play, and he made an error in the speeds of lawns 1-16.
7. The instructions of the Atari 8-bit version describe the same game with other keys.

## Still open

- Which assembler has the directives `.MAC` and `.MND` and the message "RAN OFF END OF CARD"? A comparison with the C64 assemblers of 1983 can tell.
- Did the semicolon at `$63DD` make a comment? The assembler from the first question can tell.
- Does "LMONN" come from the original file? An original tape of the game can tell.
- Does the Atari 8-bit version have 18 lawns, and does it have the speed bug? A disassembly of the Atari version can tell.
- Can the status line show JCM? A run that loses the third mower of player 1 in a game for two players can tell.
- Which version came first, the C64 version or the Atari 8-bit version?
