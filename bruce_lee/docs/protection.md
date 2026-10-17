# Bruce Lee: copy protection

The game holds eleven copy-protection checks. Three marks that the original loader leaves in zero page, and a page of key bytes at `$CF00`, must be present. Some checks fail at once: the game hangs or wipes memory. Two checks fail late: they change their own code step by step, and after 32 footsteps they make the game crash. The cracked release keeps all checks and supplies the marks and the key page: the captured game passes every check (**Observed**: title, demo and game runs). This page describes each check, and at the end what the release changed.

## Scope

- The zero-page loader marks `$00`, `$02` and `$0080`, and the checks that read them.
- The protection key page `$CF00-$CFFF` (`protection_key_page.asm`) and the checks that read it.
- The delayed checks in [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound), with a diagram of the escalation.
- The warm-start flag [`warm_start_flag`](../src/cold_start.asm#L7) [`$03FF`](reference/modules/cold_start.md#warm_start_flag).
- What the release on the disk changed.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) (every 3 frames). A *frame* is one raster interrupt of the game screen ([`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update)).
- A *footstep* is one call of [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound). Every walk, climb or fall step of any actor makes one (every 3 frames while Bruce walks).
- A *key pair* is a byte of the first half of the key page and the byte `$20` higher.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.
- The runs of this page start from the room 0 snapshot of the exploration runs, change one protection byte or operand with a write step, and trace the check. They are named "the protection runs" below.

## 1. All checks

| # | Check | Code | Reads | Passes when | On failure | Runs | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | contact mask builder | [`build_contact_masks`](../src/frame_builder.asm#L16) [`$512F`](reference/modules/frame_builder.md#build_contact_masks) | [`prot_signature_a`](../src/protection_key_page.asm#L43) [`$CF8F`](reference/modules/protection_key_page.md#prot_signature_a), [`prot_signature_b`](../src/protection_key_page.asm#L62) [`$CFAF`](reference/modules/protection_key_page.md#prot_signature_b) | `$CF8F` = `$B9` and `$CFAF` = `$CF8F` | loops for ever | once, at the cold start | Code |
| 2 | zero-page RTS | [`cold_start`](../src/cold_start.asm#L22) [`$0440`](../src/cold_start.asm#L68), [`build_masks_done`](../src/frame_builder.asm#L76) [`$517B`](reference/modules/frame_builder.md#build_masks_done) | `$0080` | `$0080` holds RTS (`$60`) | executes the byte at `$0080` | once, at the cold start | Code |
| 3 | title signature | [`title_protection_check`](../src/title_demo_start.asm#L245) [`$06DD`](reference/modules/title_demo_start.md#title_protection_check) | `$CF8F-$CF91`, `$CFAF-$CFB1` | the XOR of the six bytes is 0 | [`title_protection_wipe`](../src/title_demo_start.asm#L253) [`$06F3`](reference/modules/title_demo_start.md#title_protection_wipe) writes over all memory for ever | each title screen | Code |
| 4 | CPU port DDR, every frame | [`frame_update_check_ddr`](../src/frame_update.asm#L140) [`$166A`](reference/modules/frame_update.md#frame_update_check_ddr) | [`D6510`](../src/constants.asm#L11) [`$00`](reference/variables.md#D6510) | `$00` = `$EF` | jumps back to [`frame_update_count_frames`](../src/frame_update.asm#L95) [`$1628`](reference/modules/frame_update.md#frame_update_count_frames): an endless loop in the interrupt | each frame (game and demo) | Observed |
| 5 | loader mark, every frame | [`frame_update_check_loader_mark`](../src/frame_update.asm#L245) [`$1703`](reference/modules/frame_update.md#frame_update_check_loader_mark) | [`prot_loader_mark`](../src/constants.asm#L13) [`$02`](reference/variables.md#prot_loader_mark) | `$02` = `$32` | [`frame_update_wipe_loop`](../src/frame_update.asm#L265) [`$170B`](reference/modules/frame_update.md#frame_update_wipe_loop) wipes memory downward | each frame (game and demo) | Observed |
| 6 | room 2 | [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) | [`D6510`](../src/constants.asm#L11) [`$00`](reference/variables.md#D6510) | `$00` = `$EF` | loops for ever | each pass in room 2 | Code |
| 7 | room 5 | [`room05_init`](../src/room_specific_init.asm#L48) [`$3428`](reference/modules/room_specific_init.md#room05_init) | [`prot_loader_mark`](../src/constants.asm#L13) [`$02`](reference/variables.md#prot_loader_mark) | `$02` = `$32` | loops for ever | entering room 5 | Code |
| 8 | room 10 | [`room10_frame_protection_check`](../src/room_frames_8_11.asm#L289) [`$3CA7`](reference/modules/room_frames_8_11.md#room10_frame_protection_check) | [`D6510`](../src/constants.asm#L11) [`$00`](reference/variables.md#D6510) | `$00` = `$EF` | `$80` into [`room_map_00`](../src/room_maps_00_04.asm#L18) [`$68F9`](reference/modules/room_maps_00_04.md#room_map_00), [`room_map_05`](../src/room_maps_05_09.asm#L7) [`$6F82`](reference/modules/room_maps_05_09.md#room_map_05), [`room_map_01`](../src/room_maps_00_04.asm#L55) [`$6A09`](reference/modules/room_maps_00_04.md#room_map_01); jump to [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) | each pass in room 10 | Code |
| 9 | high-score trap | [`update_high_score`](../src/score.asm#L65) [`$3184`](reference/modules/score.md#update_high_score) | three key pairs at `$CF7B`, `$CF7E`, `$CF81` | at least one pair differs | `JMP (io1_dummy)` at `$31A1`: crash | each pass of a game | Observed |
| 10 | Yamo key, delayed | [`spawn_yamo_protection_xor`](../src/actor_spawn.asm#L205) [`$0CD8`](reference/modules/actor_spawn.md#spawn_yamo_protection_xor), [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound) | [`prot_key_yamo`](../src/protection_key_page.asm#L29) [`$CF79`](reference/modules/protection_key_page.md#prot_key_yamo) / [`prot_key_yamo_pair`](../src/protection_key_page.asm#L51) [`$CF99`](reference/modules/protection_key_page.md#prot_key_yamo_pair), moving | the pair differs | operands move; at the end [`random_byte`](../src/interrupt_entry.asm#L89) [`$1159`](reference/modules/interrupt_entry.md#random_byte) becomes TXS | Yamo enters; each footstep | Observed |
| 11 | tick key, delayed | [`main_loop_protection_check`](../src/game_main_loop.asm#L67) [`$1C13`](reference/modules/game_main_loop.md#main_loop_protection_check), [`step_sound_check_protection2`](../src/actor_step.asm#L584) [`$1FE5`](reference/modules/actor_step.md#step_sound_check_protection2) | [`prot_key_tick`](../src/protection_key_page.asm#L31) [`$CF7A`](reference/modules/protection_key_page.md#prot_key_tick) / [`prot_key_tick_pair`](../src/protection_key_page.asm#L53) [`$CF9A`](reference/modules/protection_key_page.md#prot_key_tick_pair), moving | the pair differs | operands move; at the end TXS at [`step_sound_crash_point`](../src/actor_step.asm#L606) [`$1FFE`](reference/modules/actor_step.md#step_sound_crash_point) | each pass; each footstep | Observed |

## 2. The zero-page loader marks

The original loader leaves three values in zero page. Nothing in the program writes `$00` or `$02`. **Code**

| Address | Name | Value | Checks |
|---|---|---|---|
| `$00` | [`D6510`](../src/constants.asm#L11) | `$EF` | 4, 6, 8 |
| `$02` | [`prot_loader_mark`](../src/constants.asm#L13) | `$32` | 5, 7 |
| `$0080` | [`frame_count_256`](../src/constants.asm#L80) | `$60` (RTS) | 2 |

The entry state of the capture in the knowledge holds these three values: `$00` = `$EF`, `$02` = `$32`, `$0080` = `$60`. **Observed**. The KERNAL sets `$00` = `$2F` at a reset, so a plain load into a reset machine fails checks 4, 6 and 8. **Code** (platform)

### 2.1 `$00` = `$EF`

- [`frame_update_check_ddr`](../src/frame_update.asm#L140) [`$166A`](reference/modules/frame_update.md#frame_update_check_ddr) reads [`D6510`](../src/constants.asm#L11),X with X = 0. Any other value branches back to [`frame_update_count_frames`](../src/frame_update.asm#L95) [`$1628`](reference/modules/frame_update.md#frame_update_count_frames). The code runs to the check again and loops inside the interrupt; the interrupt never returns, so the main loop stops. **Observed**: with `$00` = `$2F` the trace hit `$166A` 60 times inside one frame, and [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) was not reached.
- [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) reads [`D6510`](../src/constants.asm#L11),Y with Y = 0 and branches to itself when the value differs. The game hangs on the first pass in room 2. **Code**
- [`room10_frame_protection_check`](../src/room_frames_8_11.asm#L289) [`$3CA7`](reference/modules/room_frames_8_11.md#room10_frame_protection_check): when the value differs, it writes `$80` into the first byte of [`room_map_00`](../src/room_maps_00_04.asm#L18), [`room_map_05`](../src/room_maps_05_09.asm#L7) and [`room_map_01`](../src/room_maps_00_04.asm#L55), and jumps to [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen). `$80` ends a map, so rooms 0, 1 and 5 are drawn empty in every later game, until the program is loaded again. **Code**

### 2.2 `$02` = `$32`

- [`frame_update_check_loader_mark`](../src/frame_update.asm#L245) [`$1703`](reference/modules/frame_update.md#frame_update_check_loader_mark), each frame: when [`prot_loader_mark`](../src/constants.asm#L13) differs from `$32`, the code stores that value into the high byte of [`row_ptr_top`](../src/constants.asm#L15) [`$0004`](reference/variables.md#row_ptr_top) and writes it over memory with [`frame_update_wipe_loop`](../src/frame_update.asm#L265) [`$170B`](reference/modules/frame_update.md#frame_update_wipe_loop), 256 bytes per page, page by page downward. The page counter is [`frame_update_wipe_counter`](../src/title_demo_start.asm#L37) [`$0539`](reference/modules/title_demo_start.md#frame_update_wipe_counter): the high byte (`$D0`) of the operand of `STA SCROLY` in [`demo_start_blank_screen`](../src/title_demo_start.asm#L36) [`$0537`](reference/modules/title_demo_start.md#demo_start_blank_screen). So the wipe covers `$D0` pages and also destroys that instruction. **Observed**: with `$02` = 0, the wipe started in the first frame; 60 frames later the CPU was still in the loop and the counter was `$54`.
- [`room05_init`](../src/room_specific_init.asm#L48) [`$3428`](reference/modules/room_specific_init.md#room05_init) reads [`prot_loader_mark`](../src/constants.asm#L13),X with X = 0 and branches to itself when it is not `$32`. The game hangs when Bruce enters room 5. **Code**

### 2.3 `$0080` = RTS

[`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start) executes `JSR $0080` at `$0440`. [`build_contact_masks`](../src/frame_builder.asm#L16) [`$512F`](reference/modules/frame_builder.md#build_contact_masks) ends with `JMP $0080` at [`build_masks_done`](../src/frame_builder.asm#L76) [`$517B`](reference/modules/frame_builder.md#build_masks_done); the RTS there returns to [`cold_start`](../src/cold_start.asm#L22). Without the RTS the CPU executes whatever `$0080` holds. Later [`init_game_variables`](../src/game_setup.asm#L18) [`$0F72`](reference/modules/game_setup.md#init_game_variables) clears zero page, and `$0080` becomes the counter [`frame_count_256`](../src/constants.asm#L80). **Code**

## 3. The protection key page `$CF00-$CFFF`

Only `$CF79-$CFBA` is read. The page has two halves of 32 bytes: `$CF79-$CF98` and `$CF99-$CFB8`. Every check that compares bytes compares a byte with the byte `$20` higher. In the first 16 bytes, 15 pairs differ; one pair is equal (`$CF83` = `$CFA3` = `$A2`). The last 16 bytes (`$CF89-$CF98` and `$CFA9-$CFB8`) are equal. **Code**

| Byte | Value | Pair | Value | XOR | Read by |
|---|---|---|---|---|---|
| [`prot_key_yamo`](../src/protection_key_page.asm#L29) [`$CF79`](reference/modules/protection_key_page.md#prot_key_yamo) | `$91` | [`prot_key_yamo_pair`](../src/protection_key_page.asm#L51) [`$CF99`](reference/modules/protection_key_page.md#prot_key_yamo_pair) | `$18` | `$89` | check 10 ([`spawn_yamo_protection_xor`](../src/actor_spawn.asm#L205) [`$0CD8`](reference/modules/actor_spawn.md#spawn_yamo_protection_xor)) |
| [`prot_key_tick`](../src/protection_key_page.asm#L31) [`$CF7A`](reference/modules/protection_key_page.md#prot_key_tick) | `$51` | [`prot_key_tick_pair`](../src/protection_key_page.asm#L53) [`$CF9A`](reference/modules/protection_key_page.md#prot_key_tick_pair) | `$55` | `$04` | check 11 ([`main_loop_protection_check`](../src/game_main_loop.asm#L67) [`$1C13`](reference/modules/game_main_loop.md#main_loop_protection_check)) |
| [`prot_key_trap1`](../src/protection_key_page.asm#L33) [`$CF7B`](reference/modules/protection_key_page.md#prot_key_trap1) | `$91` | [`prot_key_trap1_pair`](../src/protection_key_page.asm#L55) [`$CF9B`](reference/modules/protection_key_page.md#prot_key_trap1_pair) | `$A5` | `$34` | check 9 |
| [`prot_key_trap2`](../src/protection_key_page.asm#L35) [`$CF7E`](reference/modules/protection_key_page.md#prot_key_trap2) | `$1A` | [`prot_key_trap2_pair`](../src/protection_key_page.asm#L57) [`$CF9E`](reference/modules/protection_key_page.md#prot_key_trap2_pair) | `$C4` | `$DE` | check 9 |
| [`prot_key_trap3`](../src/protection_key_page.asm#L37) [`$CF81`](reference/modules/protection_key_page.md#prot_key_trap3) | `$44` | [`prot_key_trap3_pair`](../src/protection_key_page.asm#L59) [`$CFA1`](reference/modules/protection_key_page.md#prot_key_trap3_pair) | `$22` | `$66` | check 9 |
| [`prot_signature_a`](../src/protection_key_page.asm#L43) [`$CF8F`](reference/modules/protection_key_page.md#prot_signature_a) | `$B9` | [`prot_signature_b`](../src/protection_key_page.asm#L62) [`$CFAF`](reference/modules/protection_key_page.md#prot_signature_b) | `$B9` | 0 | checks 1, 3 |
| [`prot_signature_a_2`](../src/protection_key_page.asm#L45) [`$CF90`](reference/modules/protection_key_page.md#prot_signature_a_2) | `$B4` | [`prot_signature_b_2`](../src/protection_key_page.asm#L64) [`$CFB0`](reference/modules/protection_key_page.md#prot_signature_b_2) | `$B4` | 0 | check 3 |
| [`prot_signature_a_3`](../src/protection_key_page.asm#L47) [`$CF91`](reference/modules/protection_key_page.md#prot_signature_a_3) | `$B4` | [`prot_signature_b_3`](../src/protection_key_page.asm#L66) [`$CFB1`](reference/modules/protection_key_page.md#prot_signature_b_3) | `$B4` | 0 | check 3 |
| `$CF7C-$CF98` | | `$CF9C-$CFB8` | | | the moving operands of checks 10 and 11 |

The full page in hex (`$CF79-$CFBA`):

```
$CF79: 91 51 91 46 31 1A 11 45 44 B4 A2 91 AC 88 88 89
$CF89: E6 7C C9 F4 52 DA B9 B4 B4 26 EF A7 9E 6C 9A B3
$CF99: 18 55 A5 28 4A C4 2A 22 22 2A A2 22 22 8A 89 88
$CFA9: E6 7C C9 F4 52 DA B9 B4 B4 26 EF A7 9E 6C 9A B3
$CFB9: 00 00
```

**Conclusion.** A page of zeros passes check 3 but hangs check 1. A page with two equal halves passes checks 1 and 3 and fails checks 9, 10 and 11. Only the original bytes pass all checks.

### 3.1 Check 1: the contact mask builder

[`build_contact_masks`](../src/frame_builder.asm#L16) [`$512F`](reference/modules/frame_builder.md#build_contact_masks) runs once, from [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start). It loads [`prot_signature_a`](../src/protection_key_page.asm#L43), compares it with `$B9`, then XORs [`prot_signature_b`](../src/protection_key_page.asm#L62). Each failure branches back to [`build_contact_masks`](../src/frame_builder.asm#L16): the start of the game hangs with a blank screen. **Code**

### 3.2 Check 3: the title signature

[`title_protection_check`](../src/title_demo_start.asm#L245) [`$06DD`](reference/modules/title_demo_start.md#title_protection_check) runs on each title screen, after the music check. It XORs [`prot_signature_a`](../src/protection_key_page.asm#L43), [`prot_signature_b_3`](../src/protection_key_page.asm#L66), [`prot_signature_a_2`](../src/protection_key_page.asm#L45), [`prot_signature_b`](../src/protection_key_page.asm#L62), [`prot_signature_a_3`](../src/protection_key_page.asm#L47) and [`prot_signature_b_2`](../src/protection_key_page.asm#L64). When the result is not 0, [`title_protection_wipe`](../src/title_demo_start.asm#L253) [`$06F3`](reference/modules/title_demo_start.md#title_protection_wipe) stores A through ([`demo_input_ptr`](../src/constants.asm#L28)),Y, increments the high byte of the pointer and repeats for ever: it writes one byte in each page of the whole address space, the I/O registers too, and never returns. **Code** (the coverage marks `$06F3-$06F9` as not executed)

### 3.3 Check 9: the high-score trap

[`update_high_score`](../src/score.asm#L65) [`$3184`](reference/modules/score.md#update_high_score) runs on each pass of a game (not in the demo). It XORs the three trap pairs one after the other. When the first pair differs, it goes on to the score. Only when all three pairs are equal does it execute `JMP (io1_dummy)` at `$31A1`. [`io1_dummy`](../src/constants.asm#L240) [`$DE00`](reference/variables.md#io1_dummy) is the I/O area 1, which has no vector. **Observed**: with the three pairs made equal, the protection run executed `JMP ($DE00)` in the first frame, and the CPU jammed at `$0147` within 4 frames.

## 4. The delayed checks

Both delayed checks live in [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound), the routine that requests the footstep sound `$80`. Each check reads a stored XOR value. When the value is 0, it increments the low bytes of the `LDA`/`EOR` operands of the instruction pair that computes the value. So the next computation reads the next key pair. After 32 increments it writes the opcode of TXS (`$9A`) over an instruction. **Code**

### 4.1 Check 10: the Yamo key

1. [`spawn_yamo`](../src/actor_spawn.asm#L203) [`$0CD5`](reference/modules/actor_spawn.md#spawn_yamo) runs when Yamo enters a room. [`spawn_yamo_protection_xor`](../src/actor_spawn.asm#L205) [`$0CD8`](reference/modules/actor_spawn.md#spawn_yamo_protection_xor) loads [`prot_key_yamo`](../src/protection_key_page.asm#L29), [`spawn_yamo_protection_eor`](../src/actor_spawn.asm#L208) [`$0CDB`](reference/modules/actor_spawn.md#spawn_yamo_protection_eor) XORs [`prot_key_yamo_pair`](../src/protection_key_page.asm#L51), and the result goes to [`protection_result`](../src/room_enemy_tables.asm#L7) [`$1166`](reference/modules/room_enemy_tables.md#protection_result) (`$89` with the original bytes). The image holds `$FF`.
2. Each footstep: when [`protection_result`](../src/room_enemy_tables.asm#L7) is 0, [`actor_play_step_sound`](../src/actor_step.asm#L556) increments [`spawn_yamo_prot_key_lo`](../src/actor_spawn.asm#L206) [`$0CD9`](reference/modules/actor_spawn.md#spawn_yamo_prot_key_lo) and [`spawn_yamo_prot_pair_lo`](../src/actor_spawn.asm#L209) [`$0CDC`](reference/modules/actor_spawn.md#spawn_yamo_prot_pair_lo).
3. When [`spawn_yamo_prot_key_lo`](../src/actor_spawn.asm#L206) reaches `$99`, it writes `$9A` into the first byte of [`random_byte`](../src/interrupt_entry.asm#L89) [`$1159`](reference/modules/interrupt_entry.md#random_byte). It does this again on each later footstep.
4. The first byte of [`random_byte`](../src/interrupt_entry.asm#L89) was the `LDA` of `LDA game_mode`. Now the routine starts with TXS: the stack pointer becomes the X of the caller, and the RTS of the routine returns to a wrong address.

[`protection_result`](../src/room_enemy_tables.asm#L7) changes only when Yamo enters again. So the operands move by one on every footstep until the next Yamo entry.

**Observed**: the protection run set [`protection_result`](../src/room_enemy_tables.asm#L7) = 0 and the operands to `$98`/`$B8`. In frame 3 the footstep code stored `$9A` at `$1159`. In frame 5 a call of [`random_byte`](../src/interrupt_entry.asm#L89) executed TXS with X = `$FF`, and the CPU jammed at `$001B`.

### 4.2 Check 11: the tick key

1. Each pass, [`main_loop_protection_check`](../src/game_main_loop.asm#L67) [`$1C13`](reference/modules/game_main_loop.md#main_loop_protection_check) loads [`prot_key_tick`](../src/protection_key_page.asm#L31) and XORs [`prot_key_tick_pair`](../src/protection_key_page.asm#L53). The result goes to [`protection_check_value`](../src/actor_step.asm#L623) [`$2007`](reference/modules/actor_step.md#protection_check_value) (`$04` with the original bytes; the image holds `$FF`).
2. Each footstep: when [`protection_check_value`](../src/actor_step.asm#L623) is 0, [`step_sound_check_protection2`](../src/actor_step.asm#L584) [`$1FE5`](reference/modules/actor_step.md#step_sound_check_protection2) increments [`main_loop_prot_key_lo`](../src/game_main_loop.asm#L68) [`$1C14`](reference/modules/game_main_loop.md#main_loop_prot_key_lo) and [`main_loop_prot_pair_lo`](../src/game_main_loop.asm#L70) [`$1C17`](reference/modules/game_main_loop.md#main_loop_prot_pair_lo).
3. When [`main_loop_prot_key_lo`](../src/game_main_loop.asm#L68) reaches `$9A`, it loads X = 4 and writes `$9A` over the `CLC` at [`step_sound_crash_point`](../src/actor_step.asm#L606) [`$1FFE`](reference/modules/actor_step.md#step_sound_crash_point). That instruction is the next one, so TXS runs at once: the stack pointer becomes 4, and the following `PLA`/RTS read the wrong stack bytes.

The value is computed again on every pass. When the moved operands reach a pair that differs, the value is not 0 any more and the operands stop.

**Observed**:
- With [`prot_key_tick`](../src/protection_key_page.asm#L31) changed to `$55` (equal to its pair), the operands moved from `$7A`/`$9A` to `$7B`/`$9B` within 60 frames of walking, and [`protection_check_value`](../src/actor_step.asm#L623) became `$34` (`$CF7B` XOR `$CF9B`). The check passed again.
- With the operands set to `$99`/`$B9` and `$CF99` = `$CFB9`, the first footstep stored `$9A` at `$1FFE` and executed TXS there with X = 4. The CPU jammed at `$0104` in the same frame.

### 4.3 How the delayed checks escalate

~~~mermaid
flowchart TB
  A["spawn_yamo_protection_xor $0CD8: V1 = key XOR pair"] --> B{"V1 = 0 ?"}
  C["main_loop_protection_check $1C13: V2 = key XOR pair, each pass"] --> D{"V2 = 0 ?"}
  B -- no --> OK1["nothing happens"]
  D -- no --> OK2["nothing happens"]
  B -- yes --> E["each footstep: key and pair operands +1"]
  D -- yes --> F["each footstep: key and pair operands +1"]
  F --> C
  E --> G{"key operand at $99 ?"}
  G -- no --> E
  G -- yes --> H["TXS written over random_byte $1159"]
  H --> I["next call of random_byte: wrong stack, crash"]
  F --> J{"key operand at $9A ?"}
  J -- yes --> K["TXS written at step_sound_crash_point $1FFE, X = 4"]
  K --> L["TXS runs at once: S = 4, crash"]
~~~

The state machine of check 11 (check 10 is the same, with "the next Yamo entry" in place of "the next pass"):

~~~mermaid
stateDiagram-v2
  state "Armed (value not 0)" as Armed
  state "Failing (value 0)" as Failing
  state "Sabotaged (TXS written)" as Sab
  state "Crashed" as Crash
  [*] --> Armed
  Armed --> Failing: the pair at the operands is equal
  Failing --> Failing: footstep, operand below $9A
  Failing --> Armed: next pass finds a differing pair
  Failing --> Sab: footstep, operand reaches $9A
  Sab --> Crash: TXS runs
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Armed | the key pair at the current operands is equal | Failing | [`main_loop_protection_check`](../src/game_main_loop.asm#L67) [`$1C13`](reference/modules/game_main_loop.md#main_loop_protection_check) |
| Failing | a footstep, the key operand stays below `$9A` | Failing (operands + 1) | [`step_sound_check_protection2`](../src/actor_step.asm#L584) [`$1FE5`](reference/modules/actor_step.md#step_sound_check_protection2) |
| Failing | the next pass reads a pair that differs | Armed | [`main_loop_protection_check`](../src/game_main_loop.asm#L67) [`$1C13`](reference/modules/game_main_loop.md#main_loop_protection_check) |
| Failing | a footstep moves the key operand to `$9A` | Sabotaged | [`step_sound_check_protection2`](../src/actor_step.asm#L584) [`$1FE5`](reference/modules/actor_step.md#step_sound_check_protection2) |
| Sabotaged | TXS at [`step_sound_crash_point`](../src/actor_step.asm#L606) runs | Crashed | [`step_sound_crash_point`](../src/actor_step.asm#L606) [`$1FFE`](reference/modules/actor_step.md#step_sound_crash_point) |

**Conclusion.** The key operands start at `$79` and `$7A` and the end marks are `$99` and `$9A`: 32 steps. Check 11 computes its value again on every pass, so its sabotage needs 32 equal pairs in a row; with a page whose halves are equal, or a blank page, it crashes after 32 footsteps, some seconds after Bruce first walks. Check 10 computes its value only when Yamo enters, so 32 footsteps before the next Yamo entry are enough. With the original bytes neither check starts, because the first pairs differ. The crash comes long after the cause, which hides where it comes from.

## 5. The warm-start flag `$03FF`

[`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start) reads [`warm_start_flag`](../src/cold_start.asm#L7) [`$03FF`](reference/modules/cold_start.md#warm_start_flag). When it is not 0, the cold start jumps to [`cold_start_expand_last_font`](../src/cold_start.asm#L149) [`$04D1`](reference/modules/cold_start.md#cold_start_expand_last_font). It skips the random table, the copy of the ROM font and the expansion of three room charsets. Nothing in the program writes `$03FF`; the program image holds 0. **Code**

A run that wrote `$55` to `$03FF` at the entry showed the title with a garbage font. **Observed** (run of the variables analysis)

**Conclusion.** The flag is not a check of the key data. A loader of the original release may have used it for a restart. It belongs here because a crack that leaves a byte at `$03FF` breaks the game.

## 6. What the release changed

- The disk `original/saeger.d64` (disk name "XIDEX") holds one file, "BRUCE LEE", 186 blocks. **Observed**
- The file (`original/bruce_lee.prg`) loads at `$0801-$C001`. It carries a cracktro, a mover and a relocator. They run before the game and are not part of the rebuild. **Observed**
- The rebuild loader (`src/loader.asm`) copies the program segments `$03FF-$9FFF`, `$CF00-$CFFF`, `$E000-$F5FF` and `$FE00-$FFFF` and the entry state `$0002-$03FE` into place, writes `$00` = `$EF` and `$01` = `$36`, and jumps to [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start). So the loader marks of section 2 hold in the rebuild. **Code**
- Two ranges are left out of the captured program:

| Range | Content at the game entry | Test | Result |
|---|---|---|---|
| `$A000-$A9FF` | a copy of the relocator and duplicates of the `$CF00` and `$E000` pages | `tests/crack_leftover_a000.json`: 2560 bytes of `$A5` written at the entry | PASS: title, demo, room 0 and walking are the same. **Observed** |
| `$033C-$03FE` | bytes that the crack relocator copied from `$C13C` | `tests/crack_leftover_033c.json`: 195 bytes of `$A5` written at the entry | PASS. **Observed** |

- [`cold_start`](../src/cold_start.asm#L22) expands the room charsets into `$A000-$BFFF`, over the first range. **Code**
- Message `$62`, [`msg_presents`](../src/messages.asm#L429) [`$4770`](reference/modules/messages.md#msg_presents), holds the text "DIABOLO  PRESENTS". No code prints message `$62`. The text lies inside the captured program, so the rebuild keeps it. **Code**
- No trainer or cheat code exists. The game keys are only F1, S, SPACE and V ([`handle_game_keys`](../src/status_and_keys.asm#L57) [`$1B29`](reference/modules/status_and_keys.md#handle_game_keys)). The writers of [`falls_left`](../src/constants.asm#L31) [`$0028`](reference/variables.md#falls_left) are: [`init_game_variables`](../src/game_setup.asm#L18) [`$0F72`](reference/modules/game_setup.md#init_game_variables) (4, or 9 when player 2 controls Yamo), [`lose_fall`](../src/lose_fall_game_over.asm#L14) [`$1818`](reference/modules/lose_fall_game_over.md#lose_fall) (minus 1, in every game), [`frame_update_yamo_idle`](../src/frame_update.asm#L295) [`$173F`](reference/modules/frame_update.md#frame_update_yamo_idle) (minus 5 when a player-controlled Yamo times out), [`award_extra_fall`](../src/score.asm#L25) [`$3146`](reference/modules/score.md#award_extra_fall) and [`collect_room16_bonus_check_y`](../src/touch_effects.asm#L14) [`$2FDA`](reference/modules/touch_effects.md#collect_room16_bonus_check_y) (plus 1), and the player swap of [`lose_fall`](../src/lose_fall_game_over.asm#L14). No code skips the decrement in [`lose_fall`](../src/lose_fall_game_over.asm#L14). **Code**

## 7. The switch `NO_PROTECTION`

The knowledge holds 13 patches under the switch `NO_PROTECTION`. Each patch makes one check take its passing path, with the same registers and flags as the passing path of the original. The patches change 47 bytes and no length. **Code**

| Check | Patch range | Code with the switch on | Effect |
|---|---|---|---|
| 1 | [`build_contact_masks`](../src/frame_builder.asm#L16) [`$5134-$5135`](../src/frame_builder.asm#L26), `$5139-$513A` | `NOP` instead of the two `BNE` | no hang on [`prot_signature_a`](../src/protection_key_page.asm#L43) [`$CF8F`](reference/modules/protection_key_page.md#prot_signature_a) and [`prot_signature_b`](../src/protection_key_page.asm#L62) [`$CFAF`](reference/modules/protection_key_page.md#prot_signature_b) |
| 2 | [`cold_start`](../src/cold_start.asm#L22) [`$0440-$0442`](../src/cold_start.asm#L68) | `NOP` instead of `JSR $0080` | no call of the loader's RTS |
| 2 | [`build_masks_done`](../src/frame_builder.asm#L76) [`$517B-$517D`](reference/modules/frame_builder.md#build_masks_done) | `RTS` instead of `JMP $0080` | returns directly to [`cold_start`](../src/cold_start.asm#L22) |
| 3 | [`title_protection_check`](../src/title_demo_start.asm#L245) [`$06F1-$06F4`](../src/title_demo_start.asm#L262) | `JMP title_start_countdown` | no memory wipe on the title |
| 4 | [`frame_update_check_ddr`](../src/frame_update.asm#L140) [`$166C-$1671`](../src/frame_update.asm#L151) | `LDA #$EF` / `CMP #$EF` | no endless loop in the interrupt |
| 5 | [`frame_update_check_loader_mark`](../src/frame_update.asm#L245) [`$1703-$170A`](reference/modules/frame_update.md#frame_update_check_loader_mark) | `LDA #$32` / `CMP #$32` / `JMP frame_update_restore_ddr` | no memory wipe |
| 6 | [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A8-$36AD`](../src/room_frames_0_7.asm#L86) | `LDX #$EF` / `CPX #$EF` | room 2 does not hang |
| 7 | [`room05_init`](../src/room_specific_init.asm#L48) [`$342A-$3430`](../src/room_specific_init.asm#L60) | `LDA #$32` / `TAY` / `CPY #$32` | room 5 does not hang |
| 8 | [`room10_frame_protection_check`](../src/room_frames_8_11.asm#L289) [`$3CA9-$3CAE`](../src/room_frames_8_11.asm#L301) | `LDX #$EF` / `CPX #$EF` / `BEQ room10_frame_bursts` | the maps of rooms 0, 1 and 5 stay intact |
| 9 | [`update_high_score`](../src/score.asm#L65) [`$31A1-$31A3`](../src/score.asm#L86) | `JMP update_high_score_compare` | no crash through `JMP ($DE00)` |
| 10 | [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FCE-$1FD2`](../src/actor_step.asm#L572) | `JMP step_sound_check_protection2` | the Yamo key never moves its operands, [`random_byte`](../src/interrupt_entry.asm#L89) [`$1159`](reference/modules/interrupt_entry.md#random_byte) stays intact |
| 11 | [`step_sound_check_protection2`](../src/actor_step.asm#L584) [`$1FE5-$1FE9`](reference/modules/actor_step.md#step_sound_check_protection2) | `JMP step_sound_restore_regs` | the tick key never moves its operands, no TXS at [`step_sound_crash_point`](../src/actor_step.asm#L606) [`$1FFE`](reference/modules/actor_step.md#step_sound_crash_point) |

The checks still read their bytes and still store [`protection_result`](../src/room_enemy_tables.asm#L7) [`$1166`](reference/modules/room_enemy_tables.md#protection_result) and [`protection_check_value`](../src/actor_step.asm#L623) [`$2007`](reference/modules/actor_step.md#protection_check_value), but nothing acts on a failed value. **Code**

**The builds.**

- `src/bruce_lee.asm` and `src/bruce_lee_loader.asm` are the default builds. They are hand-written and set `NO_PROTECTION` = 1 unless the build defines it, then include the generated `main.asm` or `loader.asm`. So the protection is off by default.
- `src/main.asm`, `src/loader.asm` and `src/loader.prg` are the original program. The generated `constants.asm` sets `NO_PROTECTION` = 0 when nothing defines it, so these builds are byte-identical to the game. `--define NO_PROTECTION=0` gives the original from the default builds too.
- `tests/no_protection.json` runs the default loader with the protection data destroyed at the entry: `$00` = `$2F`, `$02` = 0, `$0080` = 0 and the whole `$CF00` page 0. It plays the title, the demo and room 0, and enters rooms 2, 5 and 10. Screens and memory match the original; only the 47 patch bytes and the two check results differ. **Observed**: PASS.

## 8. Still open

- Why the original loader leaves `$EF` in `$00` and `$32` in `$02`. The release disk has only the cracked file, so the original loader cannot be read here.
- Whether a loader ever set [`warm_start_flag`](../src/cold_start.asm#L7) [`$03FF`](reference/modules/cold_start.md#warm_start_flag).
- Checks 6, 7 and 8 were not run. A run from the snapshots of rooms 2, 5 and 10 with `$00` = `$2F` or `$02` = 0 can confirm them.
