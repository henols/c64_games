# The releases and their cracks

This page tells about the three cracked releases of Blue Max in the project. Their labels are ANON, BANDIT and DR. For each crack, it gives the files and the start code. It also gives the bytes of the game image that the crack changed. Then it tells how the switches of the rebuild separate the releases. The [protection page](protection.md) explains the checks of the original loader. The [development page](development.md) tells about the leftovers of the development.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- The *game image* is the memory `$2800-$804C`, the game with its data.
- A *release* is one cracked disk. Its *capture* is the memory at the game entry, after the boot and the starter of the crack.
- A *starter* is the small machine code program of a crack that puts the loader marks in memory and jumps to the game.
- The *loader marks* are the values that the original loader leaves in memory and that the game reads.
- **Observed** marks a fact that a run, a capture or a byte compare showed. **Code** marks a fact from the code or the bytes of a file only. **Conclusion** marks an interpretation.

## The three releases

Each release is a crack. The project has no original disk. All three releases hold the same build of the game: the same code at the same addresses. The SHA-256 values come from sha256sum (**Observed**).

| Label | Group | CSDb | File | SHA-256 |
|---|---|---|---|---|
| ANON | no group name | 234766 | `original/anonymous/BlueMax.d64` | `728d314e2f8444e36f967431dddb482033bc3293ea237ea8b78e3a2cd1f2c0ae` |
| BANDIT | The Bandit | 174054 | `original/bandit/Blue Max (Synsoft)[cr The Bandit].d64` | `c52256673ae4dd5e674f1b57e851407c4d7d3eaa6840065e468de7709189001c` |
| DR | Derbyshire Ram | 80080 | `original/derbyshire_ram/BlueMax+2-DR.d64` | `b9c1ee2e60bf91700015fbfa70f81aee9e7972738eb0179bc8b4d46a9a6d2c5c` |

The folder of DR also holds the archive `BlueMax+2-DR.zip`, with the SHA-256 `1b760a20f69eff360ae54370ab3786f930dc3e83c51707200fd796f6eb1febac` (**Observed**).

Each release is a memory dump of a game that ran. The variables `$4003-$40F7` hold values of a game in all three releases. The start code sets them again, so they do no harm (**Code**). ANON is the base release. Its game image is the program of the knowledge (**Code**).

## What the original loader left

The game reads values that it never writes. The original loader left them in memory. A cracked copy must put them there too, or the game does not work correctly (**Code**). The [protection page](protection.md) tells the full story.

| Mark | Value | Read by | ANON | BANDIT | DR |
|---|---|---|---|---|---|
| Identity table at `$D100` | `$00-$FF` | the game start, copied to `$1000` | puts the table at `$1000` | yes | yes |
| `$0100-$0102` | `$05 $16 $04` | `$0100` and `$0101` | yes | yes | yes |
| Routine at `$0200` | `STA $FC / LDA $FB / RTS` | the map code | yes | yes | yes |
| `$0342` | `$04` | the F3 check | `$C8` | `$00` | `$04` |

The game start calls [`copy_d100_table` `$5ED8`](../src/protection/d100_table.asm#L6), which copies `$D100-$D1FF` to [`identity_table` `$1000`](../src/protection/identity_table.asm#L6). The F3 check in [`main_loop_check_loader` `$43AA`](../src/protection/loader_check.asm#L5) wants 4 at `$0342` (**Code**). Only DR passes it. On ANON and BANDIT, the key F3 in flight ends the game at the rank screen (**Observed**: the F3 run on ANON and the captures).

No code of the game reads `$0102` (**Code**: the references of the knowledge).

## ANON: a help page and a starter

The disk has the name "BLUE MAX" and three files (**Observed**):

| File | Blocks | Contents |
|---|---|---|
| `BLUE MAX` | 3 | BASIC: a help page with the keys, then the loads |
| `.BLUEM 1` | 89 | the game image, loads at `$2800` |
| `.BLUEM 2` | 1 | the starter, loads at `$033C` |

The help page lists the keys F1, F3, F5 and F7, and "FIRE & DOWN : DROP BOMB". It tells that the plane lifts off at speed 100 or more. It also explains the letters P, W and L, the alert colours and the damage letters M, G, B and F (**Observed**: the BASIC listing).

The BASIC program loads the two files in a chain. Line 100 is `ON F GOTO 400,500`. After each LOAD, BASIC starts the program again, and the variable F selects the next step. Line 500 does `SYS 828` (**Code**).

`.BLUEM 1` holds `$2800-$804B`. The capture has `$00` at `$804C` (**Observed**: the file and the capture).

### The starter

The starter at `$033C-$0371` does these steps (**Code**):

1. It fills `$1000-$10FF` with the values `$00-$FF` (`TYA`, `STA $1000,Y`).
2. It writes the routine `STA $FC / LDA $FB / RTS` at `$0200`.
3. It writes `$05 $16 $04` at `$0100-$0102`.
4. It jumps to [`program_entry` `$4000`](../src/init/entry.asm#L6).

The starter puts the identity table at `$1000`, not at `$D100`. The game copies `$D100` to `$1000` at the start. Thus the crack also writes three NOPs over the store `STA $1000,Y` at `$5EEA` of the copy loop. Without the NOPs, the copy writes the bytes of `$D100` over the table. The ANON starter does not fill `$D100` (**Code**).

The starter itself is the reason that ANON fails the F3 check. It loads at `$033C`, and `$0342` is the opcode `$C8` (INY) of its fill loop (**Code**). The game later reads this INY as the loader mark, and the mark is not 4 (**Conclusion**).

The bytes `$0372-$0437` of the starter file are a copy of the game bytes `$7F86-$804B`. Nothing executes them (**Observed**: a byte compare). **Conclusion**: the tool that saved the starter file saved too many bytes from a buffer.

## BANDIT: a memory dump in three files

The disk has no name and four files (**Observed**):

| File | Blocks | Load range | Contents |
|---|---|---|---|
| `BLUE MAX` | 2 | `$0801` | BASIC boot |
| `BLUE.C000` | 1 | `$C000` | the starter |
| `BLUE.2800-9000` | 105 | `$2800-$8FFF` | the memory of a game that ran |
| `BLUE.B000-B400` | 5 | `$B000-$B3FF` | pages 0-3 of the same game |

The BASIC boot prints "BLUE MAX - BROKEN BY THE BANDIT" and "LOADING (3 SECTIONS)...". It loads the three files in a chain with the variable A, then does `SYS 49152` (**Code**). The disk has 4 used sectors that no file uses (**Observed**). The project did not examine them.

### The starter and its copy error

The starter at `$C000` does these steps (**Code**):

1. It sets `$01` to `$36` and copies the four pages `$B000-$B3FF` to `$0000-$03FF`.
2. It sets `$01` to `$34` and fills `$D100-$D1FF` with `$00-$FF`, in the RAM under the I/O area.
3. It sets `$01` to `$2D` and jumps to `$4000`.

The copy loop has an error. For page 3 it has `STA $B300,Y` where `LDA $B300,Y` belongs. The two opcodes are `$99` and `$B9`, one bit apart. Thus `$0300-$03FF` gets the bytes of page 2, and `$B300` gets them too (**Code**).

The dumped page 3 has the loader marks: `$04` at `$B342`, `$02` at `$B300` and `$03` at `$B330`. The other bytes are `$20` (**Observed**: the file). Because of the copy error, `$0342` gets `$00` from page 2, and the F3 check fails (**Code**). **Conclusion**: the dump had the correct mark, and one wrong byte of the starter lost it.

### The run state

The dump keeps values of the game that ran. The switch RUN_STATE_BANDIT holds them (**Observed**: a byte compare with ANON):

- `$4006-$407B` and `$4085-$40F1`: variables of the game.
- `$4788-$4808`: the operands of the screen copy in [`irq_frame_copy_rows` `$4788`](../src/irq/frame_irq.asm#L254). The interrupt writes them at each copy. In the dump, the first source row is `$900E`, not `$802E`.
- `$483C-$483D`: `LDA #$DB` in place of `LDA #$FA`. The interrupt writes the next raster line into this operand.
- `$8000-$804C`: rows of the map buffer, in place of the stale code of ANON.
- `$3C50-$3C57` and `$3CA0-$3CAF`: bytes of the truck sprite and the boat sprite. No code of the knowledge writes there.

The map rows at `$8000` start with `$14 $80 $14 $80 $C3 $C2 $00 $38 $30`. These bytes are the form of a cartridge header "CBM80", with the "M" cleared to `$00` (**Code**). **Conclusion**: possibly a reset tool of the cracker wrote the header before the dump.

## DR: a trainer and a new text

The disk has no name and one file, `BLUE MAX +2  /DR`, with 65 blocks (**Observed**). Derbyshire Ram packed the file. It starts with `SYS 2055` in the BASIC line 1989 (**Code**).

A trainer menu asks "BOMBS CHEAT? [Y/N]" and "FUEL CHEAT? [Y/N]". It reads the keys with the KERNAL routine GETIN, at `$6857` of the packed stage. Each answer Y changes the packed data. Then the decrunch runs. The title interrupt of the game already runs during the decrunch (**Observed**). **Conclusion**: Derbyshire Ram packed the memory of a running game, with its interrupt vectors.

### The boot code at `$8000`

The crack has its own boot code in the map buffer. It starts with a cartridge header "CBM80" at `$8000`. The code does these steps (**Code**: the bytes of the capture):

1. It clears the two low bits of `$01`, so the CPU sees RAM at `$D100`. It fills `$D100-$D1FF` with `$00-$FF`.
2. It writes `$24` to `$DD01`, the port B of CIA 2.
3. It copies 10 bytes from `$8067` back to `$8000-$8009`, over its own header.
4. It writes the routine `STA $FC / LDA $FB / RTS` at `$0200`.
5. It writes `$04` to `$1142`, `$03` to `$1130` and `$02` to `$1100`.
6. It writes `$05 $16 $04` at `$0100-$0102`, then jumps to `$8100`.
7. At `$8100`, it reads `$8000-$80FF` in a loop with no store.
8. It sets `$01` to `$2D`, copies `$1100-$11FF` to `$0300-$03FF` and jumps to `$4000`.

Thus `$0300`, `$0330` and `$0342` get `$02`, `$03` and `$04`. This is the same pattern as the dumped page 3 of BANDIT (**Code**). **Conclusion**: Derbyshire Ram knew the loader marks of page 3, and DR passes the F3 check.

The 10 bytes that step 3 copies back are `$04 $80 $04 $80 $C3 $C2 $CD $38 $30 $FA`. They are a second "CBM80" header (**Code**). The capture of DR enters the game at [`game_start` `$4126`](../src/init/game_start.asm#L23), not at `$4000`. The game reaches its restart path first (**Observed**).

The game image holds only `$8000-$804C` of the boot code. The switch CRACK_DR_BOOT holds these bytes. The map buffer writes over them in play (**Code**).

### The Synsoft text

DR has the title line "COPYRIGHT 1983 SYNSOFT", centred, in place of "COPYRIGHT 1983 SYNAPSE SOFTWARE". The text starts after [`text_copyright_base` `$7360`](../src/text/title_texts.asm#L8), at `$7364-$7382`. No other byte of the game changed for this text (**Observed**: a byte compare). The switch EDITION_SYNSOFT holds the text.

![The title of the default build, with the Synapse line](images/title.png)

The title of the default build shows "COPYRIGHT 1983 SYNAPSE SOFTWARE".

**Conclusion**: Synsoft was the name on the U.S. Gold editions of Synapse games in the UK. Derbyshire Ram possibly cracked such an edition. The project has no original to check this.

### The trainers

Each trainer changes one instruction from DEC to LDA. The counter then never goes down (**Code**). The capture of DR has both trainers on (**Observed**).

| Switch | Address | ANON | DR | Effect |
|---|---|---|---|---|
| TRAINER_FUEL | `$4605` | `DEC fuel` | `LDA fuel` | the fuel stays at its value |
| TRAINER_BOMBS | `$63F0` | `DEC bombs` | `LDA bombs` | each drop keeps the bomb count |

The fuel instruction is in [`irq_frame_fuel` `$45FB`](../src/irq/frame_irq.asm#L73). It uses one unit every 50 frames, or every 25 frames with fuel damage (**Code**). A full tank of 200 thus lasts 200 seconds on a PAL C64 without the trainer (**Conclusion**). The bomb instruction is the first instruction of [`update_weapons_drop_bomb` `$63F0`](../src/plane/weapons.asm#L60) (**Code**).

### The run state

The switch RUN_STATE_DR holds the variables `$4006-$407B` and `$4085-$40F1` of the DR image. They are values of the game that ran (**Observed**: a byte compare with ANON). The start code sets them again (**Code**).

## Other cracks on CSDb

CSDb lists more cracks of Blue Max. The project does not have them (**Observed**: the CSDb pages):

- The Silents, 93545.
- Jack Alien, "+10D", 139218.
- The Bandit Boy, 144299, on a "Dungeon Master 4" compilation disk. Its dump holds `$2800-$9420` and `$1000-$141F`.
- Lord Vader and CIC, 153106.
- Dingo, 172038.
- "Me", 174053.
- WCS, 194433.
- Computerbrains, 200344.
- 1001 Crew, 203801.
- Catania Soft Cracked, 223805.
- Pepy, 240276.

"Blue Max 2001" on CSDb is a different game (**Observed**).

## How the rebuild separates the releases

ANON is the base release. Each change of a crack is a switch. Each switch is 0 by default. The default build is thus ANON without the F3 check and without the leftovers (**Code**: `src/config.asm`).

| Switch | Kind | Default | On in | Range |
|---|---|---|---|---|
| PROTECTION_LOADER_CHECK | protection | 0 | ANON, BANDIT, DR | `$43AE-$43B0` |
| PROTECTION_TABLE | protection | 0 | BANDIT, DR | `$5EEA-$5EEC` |
| TRAINER_FUEL | trainer | 0 | DR | `$4605-$4607` |
| TRAINER_BOMBS | trainer | 0 | DR | `$63F0-$63F2` |
| CHEAT_INVINCIBLE | cheat | 0 | none | `$5D46-$5D47` |
| EDITION_SYNSOFT | change | 0 | DR | `$7364-$7382` |
| CRACK_DR_BOOT | crack | 0 | DR | `$8000-$804C` |
| RUN_STATE_BANDIT | change | 0 | BANDIT | seven ranges, see above |
| RUN_STATE_DR | change | 0 | DR | `$4006-$407B`, `$4085-$40F1` |

The switches have these effects (**Code**):

- PROTECTION_LOADER_CHECK off puts `JMP main_loop_draw_status` at `$43AE`. F3 then has no effect, as with the original loader.
- PROTECTION_TABLE on puts back the store `STA identity_table,Y` at `$5EEA`. The build then needs the table at `$D100`.
- CHEAT_INVINCIBLE puts `AND #$78` at `$5D46`. No release has it. The [development page](development.md) explains it.
- The source refuses CRACK_DR_BOOT and RUN_STATE_BANDIT together, because both change `$8000-$804C`.
- LEFTOVERS builds the 148 bytes of 6 leftover ranges that nothing uses. Each release has them.

The build option `--release <label>` sets the switches of one release, and the build does not read `src/config.asm`. Each release build is byte for byte the same as its capture (**Observed**: the check of the source generator). The loader `build/clean_loader.prg` puts the loader marks in memory and starts the default build (**Observed**: the generator ran it to the jump at `$4000`).

## Still open

- How did the original loader set the loader marks, and why does it leave `$02` at `$0300` and `$03` at `$0330`? No release has the original loader. An original disk can answer it.
- Why does DR write `$24` to `$DD01`? A run of the DR boot with a watchpoint on `$DD01` and a look at the original loader can answer it.
- Why does the DR boot read `$8000-$80FF` with no store at `$8100`? Possibly the crack removed a store. A trace of the DR boot can show if it has an effect.
- Who wrote the "CBM80" headers at `$8000` in the dumps of BANDIT and DR? A comparison with other dumps of the same cracker tools can answer it.
- What changed the truck and boat sprite bytes `$3C50-$3C57` and `$3CA0-$3CAF` in the BANDIT dump? A watchpoint on these bytes during a long game can answer it.
- What do the 4 used sectors of the BANDIT disk that no file uses hold? A sector read of the disk can answer it.
- Is the Synsoft text from an original U.S. Gold edition, or did Derbyshire Ram write it? An original Synsoft disk can answer it.
