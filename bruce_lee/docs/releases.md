# Bruce Lee: the three releases

The project has three cracked releases of *Bruce Lee*. This page compares their game bytes, tells what each difference is, and shows how the switches of the source give each release and the clean default build.

**Scope.** The game bytes of the three releases at [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start), the switches `CRACK_DIABOLO`, `FIX_RAM_TEST_BYTE`, `RUN_STATE` and `PROTECTION`, and the release files in `original/`.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *release* is one cracked file. Its *capture* is the memory at the jump to [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start), with the segments of the program of the knowledge.
- The *base release* is the release whose bytes are the program of the knowledge: SAEGER.
- **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## 1. The releases

| Label | File | Disk | Crack | Packed | Capture |
|---|---|---|---|---|---|
| SAEGER (base) | `original/bruce_lee.prg` | `original/saeger.d64`, "BRUCE LEE", 186 blocks | "CRACKED IN OKTOBER 1984 BY SAEGER SOFT GROUP": an intro that waits for SPACE | no | `original/releases/saeger/`: the 24 segments of the program |
| TBC | `original/bruce_lee_tbc.prg` | — (a PRG file, 49,423 bytes) | `6368 SYS 2087 CRACKED BY TBC`: the Datasoft title picture with "CRACKED BY TBC" as the intro, a wait for a key | no | `original/releases/tbc/`: 23 segments; the key bytes `$CF79-$CFBA` are in memory but not in a segment |
| DC | `original/bruce_lee_dc.prg` | `original/danish.d64`, "BRUCE LEE   (DC)", 178 blocks | `1985 SYS 2073 TCS-CRUNCH!`: a Danish Crackers intro "DC-011/P", "hit any key" | yes | `original/releases/dc/`: 23 segments; no demo input at `$F300-$F538` |

How each release gets to the game (**Observed**: c64-unpacker `stages`, and runs to `$0400` in the emulator):

1. SAEGER: the intro, then a mover that copies parts of the file to `$C000`, `$CF00`, `$E000` and `$FE00`.
2. TBC: a copier at `$0100` moves the file into place, the intro shows a bitmap and waits at `$0872` for a key through the KERNAL buffer, then a mover at `$089C` copies `$A500`, `$A600`, `$A700`, `$BE00` and `$BF00` to `$C000`, `$C100`, `$CF00`, `$FE00` and `$FF00`.
3. DC: a decruncher at `$0152` unpacks `$0801-$BF35`, then the intro at `$0847` waits for a key.
4. All three end in the same relocator at `$C000`. It moves the game down and jumps through `($C0B0)` to [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start). The loader marks are the same: `$02` = `$32`, an RTS at `$0080`, and [`warm_start_flag`](../src/cold_start.asm#L7) [`$03FF`](reference/modules/cold_start.md#warm_start_flag) = 0.

## 2. The differences

The compare covers the 24 segments of the program of the knowledge (40,075 bytes), in the full memory of each capture (**Observed**: c64-provenance `compare`, and a byte compare of the three captures).

- TBC and DC are equal in every byte, except the demo input that DC does not hold.
- SAEGER differs from TBC in 76 bytes, in 12 ranges.

| Range | SAEGER | TBC and DC | What it is | Switch |
|---|---|---|---|---|
| [`msg_presents`](../src/messages_rooms.asm#L322) [`$4771-$4777`](../src/messages_rooms.asm#L332) | `IABOLO ` | `ATASOFT` | Message `$62`: `DIABOLO  PRESENTS` against `DATASOFT PRESENTS`. No code prints it. | `CRACK_DIABOLO` |
| `$9B00` in [`room_charset_c`](../src/room_charset_c.asm#L6) [`$9800`](reference/graphics.md#room_charset_c) | `$55` | `$0F` | The top row of character `$60`. [`build_double_height_font`](../src/draw_helpers.asm#L51) [`$4892`](reference/modules/draw_helpers.md#build_double_height_font) copies it into [`charset_wizard`](../src/constants.asm#L202) [`$B000`](reference/variables.md#charset_wizard) at the cold start. | `FIX_RAM_TEST_BYTE` |
| [`music_transpose`](../src/music_voice_state.asm#L7) [`$E100-$E130`](reference/modules/music_voice_state.md#music_transpose) | voice state of a tune | other bytes | The workspace of the music voices. [`music_reset_state`](../src/music_player.asm#L113) [`$E3A8`](reference/modules/music_player.md#music_reset_state) writes it for each song. | `RUN_STATE` |
| [`music_long_lengths`](../src/music_frequency_table.asm#L51) [`$E2E7-$E2E8`](reference/modules/music_frequency_table.md#music_long_lengths) | `$01 $00` | `$B7 $DE` | Written by the length commands of a song. | `RUN_STATE` |
| [`music_stop_request`](../src/music_player.asm#L17) [`$E30A-$E314`](reference/modules/music_player.md#music_stop_request) | flags of a tune | other bytes | The stop request and the other flags of the player. [`music_reset_state`](../src/music_player.asm#L113) and the song setup write them. | `RUN_STATE` |
| [`music_fetch_voice0`](../src/music_player.asm#L147) [`$E3DE`](reference/modules/music_player.md#music_fetch_voice0), [`music_fetch_voice1`](../src/music_player.asm#L150) [`$E3E2`](reference/modules/music_player.md#music_fetch_voice1), [`music_fetch_voice2`](../src/music_player.asm#L153) [`$E3E6`](reference/modules/music_player.md#music_fetch_voice2): the operands `$E3DF-$E3E8` | `LDA $E8E0`, `LDA $E988`, `LDA $EA3C` | `LDA $1234` three times | The stream pointers of the three voices, in the operands of the fetch routines. [`music_set_voice_pointers`](../src/music_player.asm#L65) writes them for each song. `$1234` is a placeholder of the assembler source. | `RUN_STATE` |
| [`music_cmd_offset`](../src/music_player.asm#L468) [`$E5E7`](reference/modules/music_player.md#music_cmd_offset) | `$00` | `$FE` | The operand of a branch into the command table. The command dispatch writes it before the branch. | `RUN_STATE` |
| [`music_playlist_pos`](../src/music_data.asm#L31) [`$E86C`](reference/modules/music_data.md#music_playlist_pos) | `$01` | `$00` | The index of the next playlist entry. | `RUN_STATE` |

The table lists the ranges by variable; the byte compare splits `$E30A-$E314` and `$E3DF-$E3E8` into the bytes that differ.

**Code**: the game writes each `RUN_STATE` byte before it reads it. **Observed**: in the TBC release, a watchpoint on `$E3DF-$E3E8` stops first at the store of [`music_set_voice_pointers`](../src/music_player.asm#L65) [`$E376`](../src/music_player.asm#L81), 83 frames after the entry. A compare with 900 frames from the entry of each release (c64-provenance `--frames`) shows a write as the first access of the voice state and the flags in SAEGER and DC.

## 3. What the differences tell

- **The SAEGER image was saved from a game that had run.** The music state is the state after a tune, and the self-modified operands point into the songs. TBC and DC have the values before any run: `$1234` is what the assembler source wrote (**Conclusion**).
- **A reset left `$55` at `$9B00`.** The KERNAL RAM test at `$FD6E-$FD83` reads each byte, writes `$55`, compares, writes `$AA`, compares, and writes the old byte back. A reset that stops the test after the write of `$55` at `$9B00` leaves `$55` there (**Code**: the KERNAL; **Conclusion**: how the byte got into the image). A cracker who resets a running game to save its memory can get this byte.
- **The game reads the damaged byte.** At the cold start, [`build_double_height_font`](../src/draw_helpers.asm#L51) [`$4892`](reference/modules/draw_helpers.md#build_double_height_font) reads `$9B00` as source data (**Observed**: a watchpoint on `$9B00` in the TBC release). So SAEGER builds character `$60` of the wizard room charset with a different top row. Whether room 18 shows character `$60` is not checked.
- **The DIABOLO edit is only in SAEGER.** TBC and DC have the original text. So a cracker who signed as Diabolo edited a copy of the image that SAEGER packed later (**Conclusion**).
- **All three come from one crack.** The relocator at `$C000` and the copies at `$A000-$A9FF` are the same in TBC and SAEGER, except for the copies of the music state (**Observed**: byte compare of the captures). DC holds other bytes at `$A000`, where its decruncher worked.
- **DC lost the demo input.** The packed file ends at `$F200`. [`demo_input_stream`](../src/demo_input.asm#L12) [`$F300`](reference/modules/demo_input.md#demo_input_stream) holds whatever RAM held: zeros and `$FF`. The attract demo then gives Bruce no input, and it ends at his first lost fall (**Observed**: the DC release from [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$0531`](reference/modules/title_demo_start.md#start_attract_demo) to [`lose_fall`](../src/lose_fall_game_over.asm#L14) [`$1818`](reference/modules/lose_fall_game_over.md#lose_fall) and the title).
- **No release has a trainer or a cheat.** None of the differences is code that the game runs as a cheat, and the protection checks are equal in the three releases (**Observed**: the byte compare).

## 4. The switches

| Switch | Kind | Default | Releases with it on | Patches |
|---|---|---|---|---|
| `PROTECTION` | protection | 0 | SAEGER, TBC, DC | 13 patches, 47 bytes ([protection.md](protection.md#7-the-switch-protection)) |
| `CRACK_DIABOLO` | crack | 0 | SAEGER | `$4771-$4777` |
| `FIX_RAM_TEST_BYTE` | fix | 1 | TBC, DC | `$9B00` |
| `RUN_STATE` | change | 0 | SAEGER | `$E100-$E130`, `$E2E7-$E2E8`, `$E30A-$E314`, `$E3DE-$E3E8`, `$E5E6-$E5E7`, `$E86C` |

The default build is the clean game: no protection, the original text, the clean charset byte, and the music bytes before a run. It is the TBC game without the protection checks (**Observed**: the byte compare of the builds).

| Build | Command (c64-assembler, from the project folder) | Result |
|---|---|---|
| Default game | `assembler.ts build src main.asm --out build/bruce_lee.prg` | the clean game |
| Default runnable loader | `assembler.ts build src loader.asm --out build/bruce_lee_loader.prg` | a PRG with `10 SYS 2061` |
| SAEGER | `assembler.ts build src main.asm --release SAEGER --compare --out build/bruce_lee_SAEGER.prg` | identical to the program of the knowledge |
| TBC | `... --release TBC --compare` | identical to `original/releases/tbc/` in each of its 23 segments |
| DC | `... --release DC --compare` | identical to `original/releases/dc/` in each of its 23 segments |

`src/loader.prg` is the loader of the SAEGER build. c64-source checks it in the emulator against the entry state of the capture.

## 5. The tests

- `tests/no_protection.json` and `tests/all_rooms_no_protection.json` compare the default loader with the TBC release.
- The other scenarios in [tests/](../tests/) compare the SAEGER release with `src/loader.prg`.
- The recording `tests/recordings/first-rooms` replays on `src/loader.prg` and on the default loader: PASS at 1075 checkpoints of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) each (**Observed**).

## 6. Still open

- Whether room 18 draws character `$60` of [`charset_wizard`](../src/constants.asm#L202) [`$B000`](reference/variables.md#charset_wizard). A run of `tests/all_rooms.json` on the SAEGER and TBC releases, with a compare of the screen of room 18, can show it.
- The order of the cracks. TBC and DC could come from the same clean copy, or one from the other.
