# Bruce Lee: copy protection

In eleven places, the game checks for three marks of the original loader in zero page and for key bytes at `$CF00`. Some checks fail at once: the game hangs, wipes memory or empties the maps of three rooms. Two checks fail late: they change their own code on each footstep, and the game crashes after 32 footsteps, long after the cause. The cracked releases keep every check and supply the marks and the key page. Thus their game passes every check (**Observed**: title, demo and game runs). In the rebuild, the switch `PROTECTION` gives each check its passing path by default, and the releases restore the checks.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of [`main_loop` `$1BC2`](../src/game/game_main_loop.asm#L23) (every 3 frames). A *frame* is one raster interrupt of the game screen ([`frame_update` `$15A8`](../src/game/frame_update.asm#L20)).
- A *footstep* is one call of `actor_play_step_sound`. Every walk, climb or fall step of any actor makes one (every 3 frames while Bruce walks).
- A *key pair* is a byte of the first half of the key page and the byte `$20` higher.
- The *loader marks* are `$00` = `$EF`, `$02` = `$32` and an RTS at `$0080`.
- *The protection runs* start from the room 0 snapshot of the exploration runs. Each run changes one protection byte or operand with a write step and traces the check.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The game has checks in all its parts:

- Two checks run one time at the cold start.
- One check runs on each title screen.
- Two checks run in every frame.
- Three checks are in the room code of rooms 2, 5 and 10.
- One check runs on each pass of a game.
- The last two checks compute a value in one place and use it in another place. They compute the value when Yamo enters a room or on each pass. They use it on each footstep of any actor.

**Code**. Thus a cracker who removes one check still meets the next check (**Conclusion**).

~~~mermaid
flowchart TB
  L["Original loader: the loader marks in zero page"] --> C["Cold start: checks 1 and 2"]
  K["Key page $CF79-$CFBA in the image"] --> C
  C --> T["Each title screen: check 3"]
  T --> F["Each frame: checks 4 and 5"]
  F --> R["Rooms 2, 5 and 10: checks 6, 7 and 8"]
  F --> P["Each pass of a game: check 9, value of check 11"]
  Y["Yamo enters: value of check 10"] --> S["Each footstep: checks 10 and 11 act"]
  P --> S
~~~

A check that fails does one of three things:

- **It hangs.** The code branches to itself or back to its start: checks 1, 4, 6 and 7.
- **It destroys.** Checks 3 and 5 wipe memory. Check 9 jumps into an I/O area. Check 8 cuts the maps of rooms 0, 1 and 5.
- **It waits.** Checks 10 and 11 move their own operands one key pair further on each footstep. After 32 steps, they write a TXS into the code. The crash comes many seconds after the cause, and this hides the source of the crash (**Conclusion**).

### All checks

| # | Check | Code | Reads | Passes when | On failure | Runs | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | contact mask builder | `build_contact_masks` | `prot_signature_a`, `prot_signature_b` | `$CF8F` = `$B9` and `$CFAF` = `$CF8F` | loops for ever | once, at the cold start | Code |
| 2 | zero-page RTS | `cold_start`, `build_masks_done` | `$0080` | `$0080` holds RTS (`$60`) | executes the byte at `$0080` | once, at the cold start | Code |
| 3 | title signature | `title_protection_check` | `$CF8F-$CF91`, `$CFAF-$CFB1` | the XOR of the six bytes is 0 | `title_protection_wipe` writes over all memory for ever | each title screen | Code |
| 4 | CPU port DDR, every frame | `frame_update_check_ddr` | `D6510` | `$00` = `$EF` | jumps back to `frame_update_count_frames`: an endless loop in the interrupt | each frame (game and demo) | Observed |
| 5 | loader mark, every frame | `frame_update_check_loader_mark` | `prot_loader_mark` | `$02` = `$32` | `frame_update_wipe_loop` wipes memory downward | each frame (game and demo) | Observed |
| 6 | room 2 | `room02_frame` | `D6510` | `$00` = `$EF` | loops for ever | each pass in room 2 | Code |
| 7 | room 5 | `room05_init` | `prot_loader_mark` | `$02` = `$32` | loops for ever | entering room 5 | Code |
| 8 | room 10 | `room10_frame_protection_check` | `D6510` | `$00` = `$EF` | `$80` into `room_map_00`, `room_map_05`, `room_map_01`, then a jump to `show_title_screen` | each pass in room 10 | Code |
| 9 | high-score trap | `update_high_score` | three key pairs at `$CF7B`, `$CF7E`, `$CF81` | at least one pair differs | `JMP (io1_dummy)` at `$31A1`: crash | each pass of a game | Observed |
| 10 | Yamo key, delayed | `spawn_yamo_protection_xor`, `actor_play_step_sound` | `prot_key_yamo` / `prot_key_yamo_pair`, moving | the pair differs | operands move, at the end `random_byte` becomes TXS | Yamo enters, each footstep | Observed |
| 11 | tick key, delayed | `main_loop_protection_check`, `step_sound_check_protection2` | `prot_key_tick` / `prot_key_tick_pair`, moving | the pair differs | operands move, at the end TXS at `step_sound_crash_point` | each pass, each footstep | Observed |

### Checks 4, 6 and 8: `$00` = `$EF`

The loader leaves `$EF` in the data direction register of the CPU port. A reset sets `$2F`. Thus a game that a person loads into a reset machine fails these three checks. **Code** (platform)

- **Check 4, every frame.** [`frame_update_check_ddr` `$166A`](../src/game/frame_update.asm#L140) reads `D6510`,X with X = 0. Any other value branches back to [`frame_update_count_frames` `$1628`](../src/game/frame_update.asm#L95). The code runs to the check again and loops inside the interrupt. The interrupt never returns, so the main loop stops. **Observed**: with `$00` = `$2F`, the trace hit `$166A` 60 times inside one frame. The trace did not reach `main_loop`.
- **Check 6, room 2.** [`room02_frame` `$36A6`](../src/room/room_frames_0_7.asm#L75) reads `D6510`,Y with Y = 0. When the value differs, the code branches to itself. The game hangs on the first pass in room 2. **Code**
- **Check 8, room 10.** When the value differs, [`room10_frame_protection_check` `$3CA7`](../src/room/room_frames_8_11.asm#L289) writes `$80` into the first byte of `room_map_00`, `room_map_05` and `room_map_01`. Then it jumps to [`show_title_screen` `$0584`](../src/game/title_demo_start.asm#L83). `$80` ends a map. Thus the game draws rooms 0, 1 and 5 empty in every later game, until a person loads the program again. **Code**

### Checks 5 and 7: `$02` = `$32`

Nothing in the program writes `$02`, so only the loader can leave `$32` there. **Code**

- **Check 5, every frame.** [`frame_update_check_loader_mark` `$1703`](../src/game/frame_update.asm#L244) compares `prot_loader_mark` with `$32`. When the value differs, the code stores that value into the high byte of `row_ptr_top`. Then [`frame_update_wipe_loop` `$170B`](../src/game/frame_update.asm#L264) writes the value over memory, 256 bytes per page, page by page downward. The page counter [`frame_update_wipe_counter` `$0539`](../src/game/title_demo_start.asm#L37) is the high byte (`$D0`) of the operand of `STA SCROLY` in `demo_start_blank_screen`. Thus the wipe covers `$D0` pages and also destroys that instruction. **Observed**: with `$02` = 0, the wipe started in the first frame. 60 frames later, the CPU was still in the loop, with the counter at `$54`.
- **Check 7, room 5.** [`room05_init` `$3428`](../src/room/room_specific_init.asm#L48) reads `prot_loader_mark`,X with X = 0. When the value is not `$32`, the code branches to itself. The game hangs when Bruce enters room 5. **Code**

### Check 2: the RTS at `$0080`

The cold start calls zero page two times and needs an RTS there. [`cold_start` `$0440`](../src/game/cold_start.asm#L68) executes `JSR $0080`. [`build_contact_masks` `$512F`](../src/actor/frame_builder.asm#L16) ends with `JMP $0080` at [`build_masks_done` `$517B`](../src/actor/frame_builder.asm#L76). The RTS at `$0080` returns to `cold_start`. Without the RTS, the CPU executes the byte that `$0080` holds. Later, `init_game_variables` clears zero page, and `$0080` becomes the counter `frame_count_256`. **Code**

### Checks 1, 3 and 9: the key page

The key page holds two halves of 32 bytes. The checks XOR a byte with the byte `$20` higher. Some pairs must be equal, and other pairs must differ.

**Check 1, the contact mask builder.** [`build_contact_masks` `$512F`](../src/actor/frame_builder.asm#L16) runs one time, from `cold_start`. It loads `prot_signature_a`, compares it with `$B9`, and then XORs `prot_signature_b`. Each failure branches back to `build_contact_masks`. The start of the game hangs with a blank screen. **Code**

**Check 3, the title signature.** [`title_protection_check` `$06DD`](../src/game/title_demo_start.asm#L245) runs on each title screen, after the music check. It XORs the three signature bytes of each half. When the result is not 0, [`title_protection_wipe` `$06F3`](../src/game/title_demo_start.asm#L253) stores A through (`demo_input_ptr`),Y. Then it increments the high byte of the pointer and repeats for ever. Thus it writes one byte in each page of the full address space, also in the I/O registers, and never returns. **Code** (the coverage marks `$06F3-$06F9` as not executed)

**Check 9, the high-score trap.** [`update_high_score` `$3184`](../src/game/score.asm#L65) runs on each pass of a game (not in the demo). It XORs the three trap pairs one after the other. When the first pair differs, it continues to the score. Only when all three pairs are equal does it execute `JMP (io1_dummy)` at `$31A1`. [`io1_dummy` `$DE00`](../src/constants.asm#L283) is the I/O area 1, which has no vector.

**Observed**: the protection run made the three pairs equal. It executed `JMP ($DE00)` in the first frame, and the CPU jammed at `$0147` within 4 frames.

### The delayed checks 10 and 11

Both delayed checks act in [`actor_play_step_sound` `$1FC4`](../src/actor/actor_step.asm#L556), the routine that requests the footstep sound `$80`. Each check reads an XOR value that other code stored. The procedure is:

1. When the value is 0, the check increments the low bytes of two operands. These are the `LDA`/`EOR` operands of the instruction pair that computes the value.
2. Thus the next computation reads the next key pair.
3. After 32 increments, the check writes the opcode of TXS (`$9A`) over an instruction.

**Code**

**Check 10, the Yamo key.**

1. When Yamo enters a room, `spawn_yamo` runs [`spawn_yamo_protection_xor` `$0CD8`](../src/actor/actor_spawn.asm#L205). It loads `prot_key_yamo` and XORs `prot_key_yamo_pair`.
2. It stores the result in [`protection_result` `$1166`](../src/room/room_enemy_tables.asm#L7). The result is `$89` with the original bytes. The image holds `$FF`.
3. On each footstep, when `protection_result` is 0, `actor_play_step_sound` increments [`spawn_yamo_prot_key_lo` `$0CD9`](../src/actor/actor_spawn.asm#L206) and `spawn_yamo_prot_pair_lo`.
4. When `spawn_yamo_prot_key_lo` reaches `$99`, the code writes `$9A` into the first byte of [`random_byte` `$1159`](../src/irq/interrupt_entry_1131.asm#L45). It writes it again on each later footstep.
5. The first byte of `random_byte` was the `LDA` of `LDA game_mode`. Now the routine starts with TXS. The stack pointer becomes the X of the caller, and the RTS of the routine returns to a wrong address.

`protection_result` changes only when Yamo enters again. Thus the operands move by one on every footstep until the next Yamo entry. **Code**

**Observed**: the protection run set `protection_result` = 0 and the operands to `$98`/`$B8`. In frame 3, the footstep code stored `$9A` at `$1159`. In frame 5, a call of `random_byte` executed TXS with X = `$FF`, and the CPU jammed at `$001B`.

**Check 11, the tick key.**

1. On each pass, [`main_loop_protection_check` `$1C13`](../src/game/game_main_loop.asm#L67) loads `prot_key_tick` and XORs `prot_key_tick_pair`.
2. It stores the result in [`protection_check_value` `$2007`](../src/actor/actor_step.asm#L627). The result is `$04` with the original bytes. The image holds `$FF`.
3. On each footstep, when `protection_check_value` is 0, [`step_sound_check_protection2` `$1FE5`](../src/actor/actor_step.asm#L586) increments `main_loop_prot_key_lo` and `main_loop_prot_pair_lo`.
4. When `main_loop_prot_key_lo` reaches `$9A`, the code loads X = 4. It writes `$9A` over the `CLC` at [`step_sound_crash_point` `$1FFE`](../src/actor/actor_step.asm#L610).
5. That instruction is the next instruction, so TXS runs at once. The stack pointer becomes 4, and the next `PLA`/RTS read the wrong stack bytes.

The main loop computes the value again on every pass. When the moved operands reach a pair that differs, the value is not 0, and the operands stop. **Code**

**Observed**:
- The protection run changed `prot_key_tick` to `$55`, the value of its pair. Within 60 frames of walking, the operands moved from `$7A`/`$9A` to `$7B`/`$9B`. `protection_check_value` became `$34` (`$CF7B` XOR `$CF9B`), and the check passed again.
- The protection run set the operands to `$99`/`$B9` and made `$CF99` = `$CFB9`. The first footstep stored `$9A` at `$1FFE` and executed TXS there with X = 4. The CPU jammed at `$0104` in the same frame.

### The warm-start flag `$03FF`

The cold start has a short path for a restart. [`cold_start` `$0400`](../src/game/cold_start.asm#L22) reads [`warm_start_flag` `$03FF`](../src/game/cold_start.asm#L7). When the flag is not 0, the cold start jumps to [`cold_start_expand_last_font` `$04D1`](../src/game/cold_start.asm#L149). It skips the random table, the copy of the ROM font and the expansion of three room charsets. Nothing in the program writes `$03FF`. The program image holds 0. **Code**

A run that wrote `$55` to `$03FF` at the entry showed the title with a garbage font. **Observed** (run of the variables analysis)

**Conclusion.** The flag is not a check of the key data. A loader of the original release may have used it for a restart. The flag is on this page because a crack that leaves a byte at `$03FF` breaks the game.

## The data

### The loader marks

The original loader leaves three values in zero page. Nothing in the program writes `$00` or `$02`. **Code**

| Address | Name | Value | Checks |
|---|---|---|---|
| `$00` | `D6510` | `$EF` | 4, 6, 8 |
| `$02` | `prot_loader_mark` | `$32` | 5, 7 |
| `$0080` | `frame_count_256` | `$60` (RTS) | 2 |

The entry state of the capture in the knowledge holds these three values. **Observed**

The RTS comes from the original loader. The release file still holds the last stage of this loader in encoded form. The stage starts with `LDA #$60` / `STA $80`. Then it decrypts the game into `$0400-$A0FF` and calls `$0400`. The stage does not set `$00` or `$02`. **Code**: the decoded stage is in the knowledge space `bank7`, and the encoded bytes are in space `bank6`.

### The key page `$CF00-$CFFF`

The checks read only `$CF79-$CFBA`. The page has two halves of 32 bytes: `$CF79-$CF98` and `$CF99-$CFB8`. Each check that compares bytes compares a byte with the byte `$20` higher. In the first 16 bytes, 15 pairs differ, and one pair is equal (`$CF83` = `$CFA3` = `$A2`). The last 16 bytes (`$CF89-$CF98` and `$CFA9-$CFB8`) are equal. **Code**

| Byte | Value | Pair | Value | XOR | Read by |
|---|---|---|---|---|---|
| `prot_key_yamo` | `$91` | `prot_key_yamo_pair` | `$18` | `$89` | check 10 (`spawn_yamo_protection_xor`) |
| `prot_key_tick` | `$51` | `prot_key_tick_pair` | `$55` | `$04` | check 11 (`main_loop_protection_check`) |
| `prot_key_trap1` | `$91` | `prot_key_trap1_pair` | `$A5` | `$34` | check 9 |
| `prot_key_trap2` | `$1A` | `prot_key_trap2_pair` | `$C4` | `$DE` | check 9 |
| `prot_key_trap3` | `$44` | `prot_key_trap3_pair` | `$22` | `$66` | check 9 |
| `prot_signature_a` | `$B9` | `prot_signature_b` | `$B9` | 0 | checks 1, 3 |
| `prot_signature_a_2` | `$B4` | `prot_signature_b_2` | `$B4` | 0 | check 3 |
| `prot_signature_a_3` | `$B4` | `prot_signature_b_3` | `$B4` | 0 | check 3 |
| `$CF7C-$CF98` | | `$CF9C-$CFB8` | | | the moving operands of checks 10 and 11 |

**Conclusion.** A page of zeros passes check 3 but hangs check 1. A page with two equal halves passes checks 1 and 3 and fails checks 9, 10 and 11. Only the original bytes pass all checks.

## The state machine of the delayed checks

Each delayed check is a small state machine in the code itself. The state is the low byte of its key operand. While the computed value is not 0, the check stays in the state Armed and does nothing. When the value is 0, each footstep moves the operands one pair further. When the key operand reaches its end mark, the check writes TXS into the code. [`step_sound_check_protection2` `$1FE5`](../src/actor/actor_step.asm#L586) makes the changes of check 11.

~~~mermaid
stateDiagram-v2
  state "Armed (value not 0)" as Armed
  state "Failing (value 0)" as Failing
  state "Sabotaged (TXS written)" as Sab
  state "Crashed" as Crash
  [*] --> Armed
  Armed --> Failing: the pair at the operands is equal
  Failing --> Failing: footstep, key operand below the end mark
  Failing --> Armed: a new value from a pair that differs
  Failing --> Sab: footstep, key operand reaches the end mark
  Sab --> Crash: TXS runs
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Armed | the key pair at the current operands is equal | Failing | `main_loop_protection_check` (11), `spawn_yamo_protection_xor` (10) |
| Failing | a footstep, the key operand stays below the end mark | Failing (operands + 1) | `step_sound_check_protection2` (11), `actor_play_step_sound` (10) |
| Failing | check 11: the next pass reads a pair that differs. Check 10: the next Yamo entry reads it. | Armed | `main_loop_protection_check` (11), `spawn_yamo_protection_xor` (10) |
| Failing | a footstep moves the key operand to `$9A` (11) or `$99` (10) | Sabotaged | `step_sound_check_protection2` (11), `actor_play_step_sound` (10) |
| Sabotaged | check 11: TXS at `step_sound_crash_point` runs at once. Check 10: the next call of `random_byte` runs TXS. | Crashed | `step_sound_crash_point`, `random_byte` |

**Conclusion.** The key operands start at `$79` and `$7A`, and the end marks are `$99` and `$9A`. That is 32 steps. Check 11 computes its value again on every pass, so its sabotage needs 32 equal pairs in a row. With a page of equal halves, or a blank page, it crashes after 32 footsteps, some seconds after Bruce first walks. Check 10 computes its value only when Yamo enters, so 32 footsteps before the next Yamo entry are sufficient. With the original bytes, neither check starts, because the first pairs differ.

The crash comes long after the cause, and this hides the source of the crash. **Conclusion**

## The worked example

The bytes `$CF79-$CFBA` of the image, with the second half under the first:

```
$CF79: 91 51 91 46 31 1A 11 45 44 B4 A2 91 AC 88 88 89
$CF89: E6 7C C9 F4 52 DA B9 B4 B4 26 EF A7 9E 6C 9A B3
$CF99: 18 55 A5 28 4A C4 2A 22 22 2A A2 22 22 8A 89 88
$CFA9: E6 7C C9 F4 52 DA B9 B4 B4 26 EF A7 9E 6C 9A B3
$CFB9: 00 00
```

Each check computes these values from the bytes:

1. Check 1: `$CF8F` = `$B9`, so the compare passes. `$B9` XOR `$CFAF` (`$B9`) = 0, so the code also does not take the second branch.
2. Check 3: `$B9` XOR `$B4` XOR `$B4` XOR `$B9` XOR `$B4` XOR `$B4` = 0. The title continues to its countdown.
3. Check 9: `$CF7B` (`$91`) XOR `$CF9B` (`$A5`) = `$34`. The first pair differs. Thus the high-score code continues at once and never reads the other two pairs.
4. Check 10: `$CF79` (`$91`) XOR `$CF99` (`$18`) = `$89` in `protection_result`. The value is not 0, so the check stays armed.
5. Check 11: `$CF7A` (`$51`) XOR `$CF9A` (`$55`) = `$04` in `protection_check_value`. The value is not 0, so the check stays armed.

The protection run made `$CF7A` equal to its pair. Check 11 then moved one step to `$CF7B`/`$CF9B` and read the trap pair of step 3. It got `$34`, and the check returned to the state Armed (**Observed**, see check 11 above). On a page with equal halves, each pair gives 0, and the operands move through all 32 pairs to the crash.

## What the releases changed

The project has three cracked releases of the same game image. [releases.md](releases.md) compares them byte by byte. For the protection, these facts are important:

- **The releases keep every check.** The check bytes are equal in the three releases. Their common relocator jumps to `cold_start` with the same loader marks. **Observed**
- **The rebuild loader sets the marks.** `src/loader.asm` copies the 24 program segments of [src/main.asm](../src/main.asm) (from `$03FF` to `$FFFF`) and the entry state `$0002-$03FE` into position. It writes `$00` = `$EF` and `$01` = `$36` and jumps to `cold_start`. Thus the loader marks are correct in the rebuild. **Code**
- **The image holds only the part of the key page that the checks read.** The bytes `$CF79-$CFBA` stay in the image. The unread bytes `$CF00-$CF78` and `$CFBB-$CFFF` are among 28 leftover blocks. The knowledge keeps these blocks in the spaces `bank1` to `bank7`. [tests/leftovers_unused.json](../tests/leftovers_unused.json) fills all of them with `$A5` at the game entry: PASS at all 10 checkpoints. **Observed**
- **The last loader stage is not crack code.** At the game entry, `$033C-$03FE` holds the encoded last stage of the original protected loader (83 bytes), then zeros. The crack relocator copied it from `$C13C`. The decoded stage writes the RTS at `$0080`. The entry state of the rebuild holds zeros there. `tests/original_loader_stage_033c.json` writes 195 bytes of `$A5` there at the entry: PASS. **Code**, **Observed**
- **The crack copies at `$A000-$A9FF`.** They hold a copy of the crack relocator and duplicates of the `$CF00` and `$E000` pages. `cold_start` expands the room charsets over them (**Code**). `tests/crack_leftover_a000.json` writes 2560 bytes of `$A5` there at the entry. The title, the demo, room 0 and walking stay the same. **Observed**

**No cheat or trainer.** No release has a trainer or cheat code. The three releases differ only in the bytes that [releases.md](releases.md) lists, and the game runs none of them as code. The game keys are only F1, S, SPACE and V ([`handle_game_keys` `$1B29`](../src/game/status_and_keys.asm#L57)). Only this code writes the number of falls, [`falls_left` `$0028`](../src/constants.asm#L27):

- `init_game_variables` sets 4, or 9 when player 2 controls Yamo.
- [`lose_fall` `$1818`](../src/game/lose_fall_game_over.asm#L14) subtracts 1 in every game. Its player swap also swaps the value.
- `frame_update_yamo_idle` subtracts 5 when a player-controlled Yamo times out.
- `award_extra_fall` and `collect_room16_bonus_check_y` add 1.

No code skips the decrement in `lose_fall`. **Code**

## The switch PROTECTION

The knowledge holds 13 patches under the switch `PROTECTION` (kind `protection`). The switch is on in the three releases and off in the default build. Each patch makes one check take its passing path. The registers and flags are the same as on the passing path of the original, where the code after the check uses them. The patches change 53 bytes and no length. **Code**

| Check | Patch range | Code with the switch off | Effect |
|---|---|---|---|
| 1 | `build_contact_masks`, `$5134-$5135` and `$5139-$513A` | `NOP` instead of the two `BNE` | no hang on `prot_signature_a` and `prot_signature_b` |
| 2 | `cold_start`, `$0440-$0442` | `NOP` instead of `JSR $0080` | no call of the loader's RTS |
| 2 | `build_masks_done`, `$517B-$517D` | `RTS` instead of `JMP $0080` | returns directly to `cold_start` |
| 3 | `title_protection_check`, `$06F1-$06F4` | `JMP title_start_countdown` | no memory wipe on the title |
| 4 | `frame_update_check_ddr`, `$166C-$1671` | `LDA #$EF` / `CMP #$EF` | no endless loop in the interrupt |
| 5 | `frame_update_check_loader_mark`, `$1703-$170A` | `LDA #$32` / `BIT $02` / `JMP frame_update_restore_ddr` (8 cycles) | no memory wipe |
| 6 | `room02_frame`, `$36A8-$36AD` | `LDX #$EF` / `CPX #$EF` | room 2 does not hang |
| 7 | `room05_init`, `$342A-$3430` | `LDA #$32` / `TAY` / `CPY #$32` | room 5 does not hang |
| 8 | `room10_frame_protection_check`, `$3CA9-$3CAE` | `NOP` / `NOP` / `NOP` / `JMP room10_frame_bursts` (9 cycles) | the maps of rooms 0, 1 and 5 stay intact |
| 9 | `update_high_score`, `$31A1-$31A3` | `JMP update_high_score_compare` | no crash through `JMP ($DE00)` |
| 10 | `actor_play_step_sound`, `$1FCE-$1FD2` | `NOP` / `NOP` / `JMP step_sound_check_protection2` (7 cycles) | the Yamo key never moves its operands, `random_byte` stays intact |
| 11 | `step_sound_check_protection2`, `$1FE5-$1FE9` | `NOP` / `NOP` / `JMP step_sound_restore_regs` (7 cycles) | the tick key never moves its operands, no TXS at `step_sound_crash_point` |

The checks still read their bytes. They still store [`protection_result` `$1166`](../src/room/room_enemy_tables.asm#L7) and [`protection_check_value` `$2007`](../src/actor/actor_step.asm#L627). But no code acts on a failed value. **Code**

**The builds.**

- `src/main.asm` and `src/loader.asm` without a define give the default build. In it, `PROTECTION` = 0, so the patches are in and the protection is off. The other switches of [releases.md](releases.md) also take their default values.
- `--release SAEGER` gives the original program byte for byte (`PROTECTION` = 1). `build/clean_loader.prg` is the loader of that build. c64-source builds it and checks it with the switch values of the base release.
- `--define PROTECTION=1` restores only the checks in the default build.

**The default build runs like the original without the protection data.** [tests/no_protection.json](../tests/no_protection.json) runs the default loader and destroys the protection data at the entry. It sets `$00` = `$2F`, `$02` = 0, `$0080` = 0 and the full `$CF00` page to 0. Its original is the TBC release, whose game bytes are the default build without the patches. The test plays the title, the demo and room 0, and enters rooms 2, 5 and 10. The screens and the memory are the same as in the original. Only the bytes of the patch ranges and the two check results differ. **Observed**: PASS.

The recording `all_rooms` in [tests/recordings/](../tests/recordings/) visits each of the 20 rooms. It replays on the default build with the same game state and the same screen memory as the original (**Observed**).

**The patches keep the cycles.** The patches of checks 5, 8, 10 and 11 run in each frame, in each pass of room 10 or on each footstep. They take the same number of cycles as the passing path of the original. For example, check 10 is `NOP` / `NOP` / `JMP`: 7 cycles, as `LDA` absolute and a taken `BNE`. Check 5 uses `BIT` on `$02` to get 8 cycles, and it does not use the value. Thus the default build keeps the timing of the original, and the replays can compare each pass (see [tests/README.md](../tests/README.md)).

## Still open

- Why the original loader leaves `$EF` in `$00` and `$32` in `$02`. The release file holds only the last loader stage (see the loader marks). That stage sets `$0080` but not `$00` or `$02`. The earlier stages are not on the disk.
- Whether a loader ever set `warm_start_flag`.
- No run tested checks 6, 7 and 8. A run from the snapshots of rooms 2, 5 and 10 with `$00` = `$2F` or `$02` = 0 can show their failure.
