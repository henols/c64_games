# The releases and their cracks

This page tells about the three cracked releases of Hover Bovver in the project: TFP, KSX and HF. For each crack, it gives the files and the bytes of the block that the crack changed. It also tells how the switches of the rebuild separate the releases. The [development page](development.md) tells about the leftovers of the development.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- The *block* is the memory `$6000-$9FFF`, the game with its data.
- A *release* is one cracked file or disk. Its *capture* is the memory of the block at the entry `$8000`, after the intro and the loader of the crack.
- **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code or the bytes of a file only. **Conclusion** marks an interpretation.

## The three releases

Each release is a crack. The project has no original tape. Thus the original bytes of the places that the cracks changed are not known (**Conclusion**). The SHA-256 values come from sha256sum (**Observed**).

| Label | Group, year | File | SHA-256 |
|---|---|---|---|
| TFP | The Friendly Programmer, 1984 | `original/friendly_programmer/Hover Bovver.t64` | `6e96ddbff253050d00bab42609a14c77ad41d7a6cba4c929cf12f78ef1fb5e80` |
| KSX | Kraksnax, 2022 | `original/kraksnax/HoverBovver-US-Canadian-Edition-ksx/HoverBovver-US-Canadian-Edition-ksx.d64` | `4c4ffaa0bae6f311e663328ab1599f8be0d8c81f3e3ac63a18ecd30ac87a8171` |
| HF | Hokuto Force, 2008 | `original/hokuto_force/Hover Bovver+6D+HS.d64` | `792a88489f07e7d7918344766ae48795bf007b72ab65472bd0bf984c693d820d` |

CSDb lists TFP as release 24125, KSX as release 215611 and HF as release 74063 (**Code**: the release records of the knowledge).

The HF disk gives three captures, one for each answer of its menu. Thus the knowledge has five releases (**Observed**):

| Label | Capture |
|---|---|
| TFP | the block of the T64 file, at `$8000` |
| KSX | the block after the depacker of KSX, at `$8000` |
| HF | the block after the answer T, with no trainer |
| HF_TRAINERS | the block after the answer T, with all six trainers |
| HF_SCORES | the block after the answer H, the high-score saver |

TFP and KSX have the same start code. `$8000-$8001` and `$8005-$8009` hold NOPs, and the JSR to `copy_graphics` is between them (**Observed**). HF has NOPs at `$8000-$8004` and `LDA #$80`, `STA $0291` at `$8005` (**Observed**). The NOPs can be the place of an older call, for example of a protection. No release gives other bytes there (**Conclusion**).

## TFP: a memory dump

The T64 file has one entry, "HOVER BOVVER", with the load range `$0801-$A000` (**Observed**). The file is a dump of the memory of a C64, from the BASIC start to the end of the block.

The crack has no intro, only BASIC lines with the text "COPIED BY THE FRIENDLY PROGRAMMER 1984". The BASIC line 63001 does `POKE 53280,1: IF PEEK(53280)=241 THEN SYS 32768`. On a C64 the four upper bits of `$D020` always read as 1, so the test is always true. The program thus starts at `$8000` at once (**Code**, **Conclusion** for the test).

The dump keeps three traces of the computer that made it (**Code**):

- `$08F8` holds `MAIN",1,1:`, the end of an older BASIC line. The loader of the original tape most likely loaded a file MAIN (**Conclusion**).
- `$0801-$5FFF` holds RAM of that computer. It has blocks of "2222" and the texts of a text adventure. Examples are "I'M IN A FIELD", "I'M ON WASTE GROUNG" and "I'M ON TOP OF A BEANSTORK".
- `$5650` holds "4891 REMMARGORP YLDNEIRF EHT" and "YB DEKCARC". These are "THE FRIENDLY PROGRAMMER 1984" and "CRACKED BY" in reverse order.

The rebuild does not keep `$0801-$5FFF`. TFP is the base release, and its block is the program of the knowledge. The project shows no change of TFP in the block, except possibly the NOPs of the start code (**Code**).

## KSX: the US/Canadian edition

The disk has the name "KRANSNAX" and one file, `HOVERBOVVER/KSX`, with 37 blocks. The other entries of the directory are a frame with the text "BEWARE OF THE HOSER. WELCOME TO DA KRAKSNAX US/CANADIAN EDITION OF... *HOVER BOVVER*" (**Observed**). Kraksnax packed the file, and it loads at `$0801`. The folder also has a PRG with the same bytes as the file, and a TAP image.

KSX has the layout of the TFP block. The two blocks differ only in the ranges of the two KSX switches (**Observed**: a byte compare). **Conclusion**: Kraksnax most likely made KSX from the TFP block.

### The texts

The switch CRACK_KSX_TEXTS holds the new texts. Kraksnax changed only text bytes (**Observed**):

| Text | TFP | KSX |
|---|---|---|
| Title, last line | "1983 LLAMASOFT SOFTWARE" | "1983 LLAMAS ++ KRAKSNAX! 2022 US/CA ED." |
| High-score title | "MEGA  MOWER  MANIACS" | "BY-TOR'S BEST SCORES" |
| Lenders | JIM, TOM, ALF, JCM | MO, JO, DOC, KSX |
| End of a lawn | "WELL DONE!", "CANINE FIDELITY BONUS" | "YIPPEEEE", "+DOGGY FIDELITY BONUS" |
| Messages 0-10 | for example "OI! OFF MY FLOWERS, YOU LUNATIC!" | for example "GEEZADS! OFF MY FLOWERS, HOSER!!!!" |
| High-score names | JCM, NOT, TEG, ZAP, POW | KSX, MOD, RAW, JOS, ZIL |

The new messages call Rover "FRISCO" and "THE MUTT". Kraksnax also changed message 10, which the game never shows (**Code**).

The capture of KSX holds a copy of the TFP bytes `$98B8-$9FBF` at `$40F8-$47FF`, outside the block. In the copy, the texts of the lawn end and the high-score names are the new texts. The 11 messages at `$4387-$454A` still have the TFP texts (**Observed**: a byte compare). **Conclusion**: the copy is a work state of Kraksnax, before the change of the messages. The rebuild does not keep it.

### The relocation

The switch CRACK_KSX_RELOCATE holds a change that Kraksnax did not need for the texts (**Observed**: a byte compare):

1. [`copy_graphics` `$7E00`](../src/init/copy_graphics.asm#L6) copies its last page to `$0B04`, not to `$2700`. The bytes at `$7E2F` are `STA $0B04,X`.
2. 16 addresses in the assembler leftover at `$6A9C-$6BFD` changed by `-$1BFC`. For example, `JSR $27FE` became `JSR $0C02`.
3. The bytes `$922C-$922D` of [`scale_chars` `$922B`](../src/status/scale_chars.asm#L6) changed from `$2A $29` to `$2E $0D`.
4. `$9FE0-$9FFD` holds `$FF`, and `$9FFE-$9FFF` holds `$00`. The text "LMONN" of TFP is not there.

The table `scale_chars` starts with `$20`, the opcode of JSR. Thus the first three bytes look like `JSR $292A`, and `$292A - $1BFC = $0D2E` (**Code**). **Conclusion**: a relocation tool found this false JSR and changed it.

In practice the scales DOG LOYALTY, DOG TOLERANCE and MOWER OVERLOAD of KSX show the characters `$2E` and `$0D` at two of their 8 steps (**Code**). This is a bug of the KSX release. The other releases do not have it.

## HF: trainers and a high-score saver

The disk has the name "HOKUTO FORCE" and two files: `HOVERBOV+6DHS/HF` with 82 blocks and `-HOVERSCORES/HF-` with 1 block (**Observed**). The menu of the crack says "TRAINED BY IAN COOG AND THE OVERKILLER" (**Observed**: the capture).

The intro shows the Hokuto Force logo and "GIVES YA FOR X'MAS 2008 HOVER BOVVER +6 +DOX +HS" (**Observed**). Then the docs viewer InfoLinker 2.1 shows the instructions of the Atari 8-bit version. The [development page](development.md) compares them with the C64 code.

Then the menu asks "DO U WANT TRAINERS OR HS SAVER? [T/H]". The answer T asks for each of the six trainers. The answer H loads the high-score file. The trainers and the saver thus exclude each other (**Observed**).

### The changes of CRACK_HF

The switch CRACK_HF holds the changes that all three HF captures have (**Observed**: a byte compare):

- `$FF` over `$63C0-$7BFF`. The HF loader puts the charset and the sprites in place, so the copies in the block are not necessary. The source text and the assembler leftover are not in the HF block.
- `$00` over the fill bytes `$7DDB-$7DDF` and `$7DFD`.
- The saver code at `$7E00-$7EB5`, over the copy routine and the NOP fill.
- [`cold_start` `$8000`](../src/init/cold_start.asm#L6) without the call of the copy routine. `$8002-$8009` holds 3 NOPs, `LDA #$80` and `STA $0291`. These two instructions are the end of the copy routine.
- Zero bytes at `$9FD6-$9FFE` and `$2A` at `$9FFF`.

### The high-score saver

The saver code has three entries (**Code**):

| Address | What it does |
|---|---|
| `$7E00` | saves the 50 bytes of the high-score table at `$4C01` as "@0:-HOVERSCORES/HF-" to the last drive in `$BA` |
| `$7E79` | calls `$7E00`, then jumps to `$9E04`, the next step after the entry of the initials |
| `$7E80` | loads the file to `$9E43`, writes `$7E79` into the JMP at `$9F9D`, then jumps to `$8000` |

The file loads over [`initial_hiscore_table` `$9E43`](../src/scores/hiscores.asm#L82). The game copies this table to `$4C01` at the start, so the saved names and scores come back (**Code**). The JMP at [`enter_initials_done` `$9F9D`](../src/scores/hiscores.asm#L256) goes to `$7E79` after each entry of the initials. The switch CRACK_HF_SCORES holds this JMP.

The file `-HOVERSCORES/HF-` on the disk has the load address `$4C01` and 50 zero bytes (**Observed**).

### The menu byte

The HF menu stores its answer at `$9FD5`, a free byte of the block. The capture has `$2C` after T and `$00` after H (**Observed**). The switch CRACK_HF_MENU holds the value `$2C`. CRACK_HF_SCORES holds the value `$00`.

### The trainers

Each trainer has its own switch. Each switch changes one instruction of the game (**Observed**: a byte compare of HF and HF_TRAINERS):

| Switch | Address | TFP | HF | Effect |
|---|---|---|---|---|
| TRAINER_LIVES | `$98B9` | `INC $20` | `LDA $20` | the mower number does not go up |
| TRAINER_INVINCIBLE | `$9718` | `CPX #$01` | `RTS` | no actor catches or bites Gordon |
| TRAINER_NO_OVERLOAD | `$9234` | `DEC $3F` | `LDA #$00` | the mower cools at each call |
| TRAINER_HYPERSPEED | `$9082` | `JSR $9094` | `LDA $9094` | the main loop has no delay |
| TRAINER_DOG_TOLERANCE | `$9624` | `LDA $2B` | `RTS` | DOG TOLERANCE does not go down |
| TRAINER_SKIP_LEVEL | `$917A` | `JSR $864A` | `JSR $2A00` | the key S ends the lawn |

TRAINER_SKIP_LEVEL calls `$2A00`, a routine of HF outside the block. The routine clears the grass counter when S is down. Then it reads the joystick (**Code**: the bytes at `$2A00` of the HF_TRAINERS capture). The rebuild does not have this routine. Thus a build with only this switch does not work (**Conclusion**).

The HF menu says about the hyperspeed trainer: "WILL LOOSE HIS EFFECT IF YOU HIT YOUR DOG WITH THE MOWER" (**Observed**).

## How the rebuild separates the releases

TFP is the base release. Each change of a crack is a switch. Each switch is 0 by default, so the default build gives the TFP block (**Code**: `src/config.asm`). The source refuses CRACK_HF and CRACK_KSX_RELOCATE together, because both change `$7E2F-$7E31` (**Code**).

| Switch | Kind | Default | On in |
|---|---|---|---|
| CRACK_HF | crack | 0 | HF, HF_TRAINERS, HF_SCORES |
| CRACK_HF_MENU | crack | 0 | HF, HF_TRAINERS |
| CRACK_HF_SCORES | crack | 0 | HF_SCORES |
| CRACK_KSX_TEXTS | crack | 0 | KSX |
| CRACK_KSX_RELOCATE | crack | 0 | KSX |
| TRAINER_LIVES | trainer | 0 | HF_TRAINERS |
| TRAINER_INVINCIBLE | trainer | 0 | HF_TRAINERS |
| TRAINER_NO_OVERLOAD | trainer | 0 | HF_TRAINERS |
| TRAINER_HYPERSPEED | trainer | 0 | HF_TRAINERS |
| TRAINER_DOG_TOLERANCE | trainer | 0 | HF_TRAINERS |
| TRAINER_SKIP_LEVEL | trainer | 0 | HF_TRAINERS |

The switch LEFTOVERS builds the spare byte `$81C1` between the two note tables. Each release has the byte. The default build has `LEFTOVERS = 0` and skips the byte (**Code**).

The build option `--release <label>` sets the switches of one release, and the build does not read `src/config.asm`. The builds `build/release_TFP.prg`, `build/release_KSX.prg`, `build/release_HF.prg`, `build/release_HF_TRAINERS.prg` and `build/release_HF_SCORES.prg` are byte for byte the same as the five captures (**Observed**: cmp).
