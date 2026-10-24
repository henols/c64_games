# The development

This page tells what the game file shows about the work of Steve Lee. The game file is one 16 KB block. It keeps traces of how the author placed, changed and tested the code. These traces are:

- the layout of the code at fixed addresses,
- older copies of routines,
- routines that nothing calls,
- tests that the author turned off,
- RAM that went into the file with the game.

**Evidence.** **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## Code at fixed addresses

Most routines start at a round address: `$4200`, `$4400`, `$4800`, `$5000`, `$5700`, `$5800` and many addresses at a step of `$10` or `$20`. The bytes between the end of a routine and the next start are `$EA`, the NOP opcode. 784 bytes of the file are such NOP fill, in 75 ranges (**Code**).

Some routines also have NOP runs inside them. Examples are 6 NOPs at `$4176-$417B` in [`game_life_begin` `$4173`](../src/game/main_loop.asm#L31), 10 NOPs at `$42B8-$42C1` in [`check_collisions` `$4200`](../src/game/collisions.asm#L6), and NOPs at `$575E` and `$577C-$577F` in [`read_input` `$5700`](../src/input/read_input.asm#L6). Each crack whose game image the byte compare read has them, so they are in the original game (**Observed**).

**Conclusion.** The author assembled each routine at a fixed address, probably with a machine-code monitor or a small assembler without a linker. A routine got room for growth, and a deleted instruction became NOPs in place, so that no other routine moved. This also explains the `JMP` at `$47FC`: it jumps to `$4891` inside [`refuel_tone` `$4886`](../src/sound/sound_update_4880.asm#L11). Nothing refers to it. It is a jump that stayed when the routine at `$4880` grew.

## Older copies of routines

Two routines have an older copy in the file (**Code**):

- `$5470-$5494`, before [`jet_flight` `$5495`](../src/player/flight.asm#L32), holds the input masks for "on the pad" and "forced down" that `read_input` now applies. The old code runs on into `jet_flight`. Nothing jumps to its start.
- `$5900-$595F` is an older `enemy_shot_spawn`. The final routine at `$5B00` also tests the half of the screen and the falling state. The old copy tests sprite 1 differently, and its branch at `$5954` goes into the middle of an instruction at `$5960`. Nothing calls it.

**Conclusion.** The author wrote the new routine at a new address and left the old one in place. The second copy shows how the enemy fire changed: the first version did not check if the enemy was shot down.

## Routines that nothing calls

| Address | What it does |
|---|---|
| `$5020-$502A` | Writes the spare jets to `$0767` in colour 6. The panel of the game writes them to `$0777`. |
| `$5040-$5050` | A delay loop with a counter in `$10`. |
| `$5180-$518F` | Fills screen rows 20-24 with character `$A0` in colour 5, one byte past the screen. |
| `$5190-$51AF` | Fills screen rows 0-10 with character `$1E`, with NOPs inside the loop. |
| `$5220` (it runs) | Writes `$6400-$662B` at each new jet: 8 rows of `$0B`, then the digits 1, 2 and 3 with `$AE`, and zeros. |

The first four have no caller (**Code**). The fifth runs at each new jet, but no code reads `$6400-$662B`. The game never changes the VIC bank, so the VIC-II never shows it (**Code**).

**Conclusion.** `$5020` and `$5180` are from an older panel at another screen row. `$5220` builds a 40-column screen in a second buffer. It can be a test screen for the radar or the panel that the author never showed. The game still writes these 556 bytes at each new jet.

## Tests that the author turned off

Some tests have a fixed result (**Code**):

- `AND #$00` before a branch at `$5422` (the refuel), `$5872` (the missile movement) and `$5982` (the enemy shots). The branch after each test never goes. At `$5872` and `$5982` this test takes the place of a tick test, so the missiles and the shots move in each pass.
- Branches that the CPU always takes: `$4C83` and `$4D2B` in the name entry, `$549D` and `$54E8` in the flight, `$57CE` in `missile_launch`. The code after each branch never runs.

**Conclusion.** The author first moved the missiles and the shots only on some ticks, and then made them faster by a change of one immediate value. This is the quickest change in a monitor: one byte, and no other address moves.

## Data that the game does not use

| Range | Contents |
|---|---|
| `$21C0-$21FF` | Sprite `$87`: a small debris shape. No code selects it. |
| `$27C0-$27FF` | Sprite `$9F`: empty. |
| `$2800-$29FF`, `$2D80-$2DFF`, `$2EC8-$2F7F` | A regular pattern of `$00` and `$FF`. |
| `$2AD9`, `$2AE0` | Bytes of the title tune that the code never reads. |
| `$2FA8-$2FB4` | The text "FALCON PATROL" in screen codes + `$80`. The game reads the credit line before it, but not this text. |
| `$59F0-$59FF` | `$90 $FF $90 $FF $92 $FF $02 $FF`, then pairs of `$00`/`$FF`. |
| Characters `$71-$7C` and others | Shapes that look like letters. No map, panel or text uses them. |

No code and no table reads these bytes, and no run read them (**Code**, **Observed** by the coverage of five recordings).

**Conclusion.** The `$00`/`$FF` pattern is the pattern of C64 RAM after power-on. The author saved the memory `$2000-$5FFF` (and one byte more) as the game file, and these gaps kept what the RAM had. The text at `$2FA8` is an earlier title. The game now draws its title logo from `$5B80`.

## The start-up hang

[`cold_start` `$4100`](../src/init/cold_start.asm#L6) turns off the CIA 1 interrupts at `$4116`, but no code of the game reads `$DC0D`. A run that starts the game from the READY prompt hangs: the CIA 1 interrupt status stays `$81`, and [`raster_irq` `$4AC0`](../src/irq/raster_irq.asm#L6) runs without end (**Observed**). The KERNAL timer runs out every 16422 cycles, and the window from the SEI at `$4100` to the store at `$4118` is about 2775 cycles (**Observed**).

**Conclusion.** About one start in six from BASIC hangs with a blank title screen. The Virgin loader probably started the game in a state without this risk. An example is a start right after its own interrupt code read `$DC0D`. A crack that starts the game with SYS 16640 has the risk. The loader of the rebuild sets the CIA timers to the state of the capture. Thus the clean build always starts (**Observed** by the loader check).

## What the traces tell

**Conclusion.** The file is a snapshot of the memory of the development machine, not the output of a build with a linker. The author placed the code by hand at round addresses. The author patched the code in place with NOPs and changed immediates, and kept old copies beside the new ones. The game is complete and stable, but its last changes are small patches: the faster missiles, the new enemy fire and the new title logo.
