# Bruce Lee: music format and the title tune

This page covers the data format of the MicroPearl Music Player (C) 1983 John A. Fitzpatrick at `$E000`:
- where the music data is: the tune table, the song list, the instruments, the length and frequency tables;
- the voice stream: each command byte, its arguments and what it does;
- the note timing (ticks, gate and release) and the end of a tune;
- the decoder, as pseudo-code of [`music_update`](../../src/music_player.asm#L449) [`$E49E`](../reference/modules/music_player.md#music_update);
- a worked example: the first bytes of the title tune, decoded from the image;
- an overview of the three voices of the title tune.

The entry points of the player, the calls of the game and the sound effects are on [sound.md](sound.md).

Sources: [music_player.asm](../reference/modules/music_player.md), [music_data.asm](../reference/modules/music_data.md). Assets: [title_tune.json](../../assets/sound/title_tune.json) (the three voice streams decoded), [title_tune_e8c0-eaac.bin](../../assets/sound/title_tune_e8c0-eaac.bin), [music_player_e000-eaff.bin](../../assets/sound/music_player_e000-eaff.bin).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one video frame. [`music_api_update`](../../src/music_player.asm#L13) [`$E006`](../reference/modules/music_player.md#music_api_update) runs once per frame, from [`irq_split_top`](../../src/raster_irq_screens.asm#L74) [`$152C`](../reference/modules/raster_irq_screens.md#irq_split_top) (title and game-over screens).
- A *tick* is one step of the note counters. The player makes one tick every [`music_tempo`](../../src/music_player.asm#L213) [`$E30D`](../reference/modules/music_player.md#music_tempo) frames. The title tune sets 2 frames per tick.
- A *voice* is one SID voice (1-3) with its own stream. Inside the player, [`music_cur_voice`](../../src/music_player.asm#L112) [`$E12E`](../reference/modules/music_player.md#music_cur_voice) holds the voice as 0-2.
- A *note* number n indexes [`note_freq_lo`](../../src/music_player.asm#L145) [`$E200`](../reference/modules/music_player.md#note_freq_lo) and [`note_freq_hi`](../../src/music_player.asm#L158) [`$E254`](../reference/modules/music_player.md#note_freq_hi): 1 = C1, 13 = C2, 82 = A7. In a music stream 0 is a rest.
- **Observed** marks a fact that a run showed (the coverage of all the recorded runs). **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## 1. Where the data is

| Name | Address | Layout | Read by |
|---|---|---|---|
| [`music_tune_table`](../../src/music_data.asm#L50) | `$E8C0` | 8 bytes per tune: stream address of voice 1, 2, 3, and an instrument table address that no code reads | [`music_set_voice_ptrs`](../../src/music_player.asm#L241) [`$E360`](../reference/modules/music_player.md#music_set_voice_ptrs) |
| [`music_last_tune`](../../src/music_data.asm#L26) | `$E86B` | highest tune number: 1 | [`music_set_voice_ptrs`](../../src/music_player.asm#L241), [`music_end_of_tune`](../../src/music_player.asm#L383) [`$E438`](../reference/modules/music_player.md#music_end_of_tune) |
| [`music_list_pos`](../../src/music_data.asm#L28) | `$E86C` | index of the next song list entry | [`music_list_continue`](../../src/music_player.asm#L406) [`$E45B`](../reference/modules/music_player.md#music_list_continue) |
| [`music_list_start`](../../src/music_data.asm#L30) | `$E86D` | index of the first song list entry: 0 | [`music_start_song_list`](../../src/music_player.asm#L427) [`$E479`](../reference/modules/music_player.md#music_start_song_list) |
| [`music_song_list`](../../src/music_data.asm#L34) | `$E870` | one byte per entry (section 4) | [`music_list_step`](../../src/music_player.asm#L408) [`$E45E`](../reference/modules/music_player.md#music_list_step) |
| [`music_instruments`](../../src/music_data.asm#L6) | `$E80A-$E849` | 8 instruments of 8 bytes: AD/SR for articulation 0, 1, 2, then 2 unused bytes | [`music_cmd_instrument`](../../src/music_player.asm#L772) [`$E720`](../reference/modules/music_player.md#music_cmd_instrument) |
| [`music_filter_presets`](../../src/music_data.asm#L16) | `$E84A-$E869` | 8 presets of 4 bytes: cutoff low, cutoff high, resonance, filter mode | [`music_cmd_filter`](../../src/music_player.asm#L820) [`$E779`](../reference/modules/music_player.md#music_cmd_filter) (as [`music_instruments+$40`](../../src/music_data.asm#L6)) |
| [`music_length_table`](../../src/music_player.asm#L764) | `$E6F9-$E718` | 16 lengths in ticks for the short table, 16 for the long table | [`music_calc_note_ticks`](../../src/music_player.asm#L719) [`$E6B6`](../reference/modules/music_player.md#music_calc_note_ticks) |
| [`note_freq_lo`](../../src/music_player.asm#L145) / [`note_freq_hi`](../../src/music_player.asm#L158) | `$E200-$E253` / `$E254-$E2A7` | 84 SID frequencies, notes 0-83 (NTSC tuning) | [`music_next_note`](../../src/music_player.asm#L551) [`$E578`](../reference/modules/music_player.md#music_next_note) and the effect players |
| [`music_waveforms`](../../src/music_player.asm#L769) | `$E71C-$E71F` | control bytes `$11`, `$21`, `$41`, `$81` for commands `$A0-$A3` | [`music_cmd_misc`](../../src/music_player.asm#L645) [`$E630`](../reference/modules/music_player.md#music_cmd_misc) |
| [`music_cmd_offsets`](../../src/music_player.asm#L185) | `$E2D6` | branch offsets into [`music_cmd_jump_table`](../../src/music_player.asm#L607) [`$E5E8`](../reference/modules/music_player.md#music_cmd_jump_table), by bits 4-6 of a command | [`music_read_command`](../../src/music_player.asm#L584) [`$E5C3`](../reference/modules/music_player.md#music_read_command) |
| [`music_state_template`](../../src/music_player.asm#L173) | `$E2A8-$E2D5` | 46 start values for `$E100-$E12D` | [`music_reset_state`](../../src/music_player.asm#L285) [`$E3A8`](../reference/modules/music_player.md#music_reset_state) |
| [`music_title_v1`](../../src/music_data.asm#L54) / [`music_title_v2`](../../src/music_data.asm#L79) / [`music_title_v3`](../../src/music_data.asm#L106) | `$E8D0-$E97C` / `$E97D-$EA30` / `$EA31-$EAAC` | the three streams of tune 0, the title tune | [`music_read_byte`](../../src/music_player.asm#L333) [`$E3EA`](../reference/modules/music_player.md#music_read_byte) |

**Code:** each voice reads its stream with a self-modified `LDA abs`. The stream pointers are the operands [`music_v1_ptr`](../../src/music_player.asm#L316) [`$E3DF`](../reference/modules/music_player.md#music_v1_ptr), [`music_v2_ptr`](../../src/music_player.asm#L322) [`$E3E3`](../reference/modules/music_player.md#music_v2_ptr) and [`music_v3_ptr`](../../src/music_player.asm#L328) [`$E3E7`](../reference/modules/music_player.md#music_v3_ptr) of [`music_fetch_v1`](../../src/music_player.asm#L315) [`$E3DE`](../reference/modules/music_player.md#music_fetch_v1), [`music_fetch_v2`](../../src/music_player.asm#L321) [`$E3E2`](../reference/modules/music_player.md#music_fetch_v2) and [`music_fetch_v3`](../../src/music_player.asm#L327) [`$E3E6`](../reference/modules/music_player.md#music_fetch_v3). [`music_read_byte`](../../src/music_player.asm#L333) [`$E3EA`](../reference/modules/music_player.md#music_read_byte) returns the byte, adds 1 to the pointer and stores the byte after it in [`music_lookahead`](../../src/music_player.asm#L116) [`$E130`](../reference/modules/music_player.md#music_lookahead).

Only tune 0 is used. Entry 1 of [`music_tune_table`](../../src/music_data.asm#L50) ([`music_tune_table+8`](../../src/music_data.asm#L50) [`$E8C8`](../reference/modules/music_data.md#music_tune_table)) holds `$EAB3`, `$EB60`, `$EC14`. `$EAB3` is a byte-for-byte copy of the start of [`music_title_v1`](../../src/music_data.asm#L54) [`$E8D0`](../reference/modules/music_data.md#music_title_v1). `$EB60` is in the code of [`sfx_v1_read_note`](../../src/sfx_voice1.asm#L56) [`$EB52`](../reference/modules/sfx_voice1.md#sfx_v1_read_note), and `$EC14` is in [`sfx_adsr_table`](../../src/sfx_data.asm#L19) [`$EC11`](../reference/modules/sfx_data.md#sfx_adsr_table) (**Code**). **Conclusion:** entry 1 is left over from an older layout of this memory. The song list never names tune 1.

### 1.1 The workspace

[`music_reset_state`](../../src/music_player.asm#L285) [`$E3A8`](../reference/modules/music_player.md#music_reset_state) copies [`music_state_template`](../../src/music_player.asm#L173) [`$E2A8`](../reference/modules/music_player.md#music_state_template) into `$E100-$E12D` at the start of each tune.

| Name | Address | Meaning | Start value |
|---|---|---|---|
| [`music_transpose`](../../src/music_player.asm#L46) | `$E100` | semitones added to each note | 0 |
| [`music_tie_v1`](../../src/music_player.asm#L48) ... [`music_tie_v3`](../../src/music_player.asm#L52) | `$E101-$E103` | 1 = tie: no gate-off, and the next note keeps the ADSR and the gate | 0 |
| [`music_dur_v1`](../../src/music_player.asm#L54) ... [`music_dur_v3`](../../src/music_player.asm#L58) | `$E104-$E106` | tick counter of the current note | 0 |
| [`music_release_end_v1`](../../src/music_player.asm#L60) ... [`music_release_end_v3`](../../src/music_player.asm#L64) | `$E107-$E109` | negative counter value at which the next note starts | `$FF` |
| [`music_gate_len_v1`](../../src/music_player.asm#L66) ... [`music_gate_len_v3`](../../src/music_player.asm#L70) | `$E10A-$E10C` | gate-on ticks of the next note | 7 |
| [`music_release_len_v1`](../../src/music_player.asm#L72) ... [`music_release_len_v3`](../../src/music_player.asm#L76) | `$E10D-$E10F` | negative release ticks of the next note | `$FF` |
| [`music_ad`](../../src/music_player.asm#L78) | `$E110-$E112` | attack/decay per voice | `$11` |
| [`music_sr`](../../src/music_player.asm#L80) | `$E113-$E115` | sustain/release per voice | `$97` |
| [`music_ctrl_v1`](../../src/music_player.asm#L82) ... [`music_ctrl_v3`](../../src/music_player.asm#L86) | `$E116-$E118` | control byte (waveform, gate on) per voice | `$21` |
| [`music_articulation`](../../src/music_player.asm#L88) | `$E119-$E11B` | articulation 0, 1 or 2 per voice | 0 |
| [`music_adsr_sets`](../../src/music_player.asm#L90) | `$E11C-$E12D` | 3 voices × 6 bytes: AD/SR of articulation 0, 1, 2 | `11 97 22 9B 00 93` |

Other state: [`music_tempo_counter`](../../src/music_player.asm#L114) [`$E12F`](../reference/modules/music_player.md#music_tempo_counter), [`music_tune_number`](../../src/music_player.asm#L205) [`$E309`](../reference/modules/music_player.md#music_tune_number), [`music_stop_request`](../../src/music_player.asm#L207) [`$E30A`](../reference/modules/music_player.md#music_stop_request), [`music_tune_ended`](../../src/music_player.asm#L209) [`$E30B`](../reference/modules/music_player.md#music_tune_ended) (no code reads it), [`music_playing`](../../src/music_player.asm#L211) [`$E30C`](../reference/modules/music_player.md#music_playing), [`music_tempo`](../../src/music_player.asm#L213) [`$E30D`](../reference/modules/music_player.md#music_tempo), [`music_end_flag`](../../src/music_player.asm#L215) [`$E30E`](../reference/modules/music_player.md#music_end_flag), [`music_filter_mode`](../../src/music_player.asm#L217) [`$E30F`](../reference/modules/music_player.md#music_filter_mode), [`music_filter_voice`](../../src/music_player.asm#L219) [`$E310`](../reference/modules/music_player.md#music_filter_voice), [`music_volume`](../../src/music_player.asm#L221) [`$E311`](../reference/modules/music_player.md#music_volume), [`music_end_action`](../../src/music_player.asm#L226) [`$E314`](../reference/modules/music_player.md#music_end_action), [`music_length_table_sel`](../../src/music_player.asm#L189) [`$E2E7`](../reference/modules/music_player.md#music_length_table_sel) and [`music_filter_reson`](../../src/music_player.asm#L191) [`$E2E8`](../reference/modules/music_player.md#music_filter_reson).

## 2. The voice stream

Each voice has one stream of bytes. A byte `$00-$7F` is a note. A byte `$80-$FF` is a command. A command changes the state of the voice, or of all voices, for the notes that follow it. The player dispatches a command by bits 4-6 ([`music_read_command`](../../src/music_player.asm#L584) [`$E5C3`](../reference/modules/music_player.md#music_read_command)): it writes [`music_cmd_offsets`](../../src/music_player.asm#L185) [group] into the operand of the `bcc` at [`music_cmd_branch`](../../src/music_player.asm#L604) [`$E5E7`](../reference/modules/music_player.md#music_cmd_branch).

| Byte | Arguments | What it does | Handler |
|---|---|---|---|
| `$00` | - | rest: frequency 0 for the current length; ADSR and control are not written | [`music_next_note`](../../src/music_player.asm#L551) [`$E578`](../reference/modules/music_player.md#music_next_note) |
| `$01-$7F` | - | note n: frequency of note n + [`music_transpose`](../../src/music_player.asm#L46); unless tied, writes AD, SR and the control byte (gate on) | [`music_next_note`](../../src/music_player.asm#L551) [`$E578`](../reference/modules/music_player.md#music_next_note) |
| `$80-$8F` | - | length index n = b & `$0F`: sets the gate and release ticks of the following notes (section 3) | [`music_cmd_length`](../../src/music_player.asm#L617) [`$E5FD`](../reference/modules/music_player.md#music_cmd_length) |
| `$90-$9F` | - | master volume n; the next note of this voice writes [`music_filter_mode`](../../src/music_player.asm#L217) OR n to `$D418` and [`music_filter_reson`](../../src/music_player.asm#L191) to `$D417` | [`music_cmd_volume`](../../src/music_player.asm#L630) [`$E617`](../reference/modules/music_player.md#music_cmd_volume) |
| `$A0-$A3` | - | waveform: `$11` triangle, `$21` sawtooth, `$41` pulse, `$81` noise ([`music_waveforms`](../../src/music_player.asm#L769) [`$E71C`](../reference/modules/music_player.md#music_waveforms)) | [`music_cmd_misc`](../../src/music_player.asm#L645) [`$E630`](../reference/modules/music_player.md#music_cmd_misc) |
| `$A4-$A6` | - | articulation 0, 1, 2; copies the matching AD/SR pair of [`music_adsr_sets`](../../src/music_player.asm#L90) to [`music_ad`](../../src/music_player.asm#L78)/[`music_sr`](../../src/music_player.asm#L80) | [`music_cmd_articulation`](../../src/music_player.asm#L661) [`$E64E`](../reference/modules/music_player.md#music_cmd_articulation) |
| `$A7` / `$A8` | - | tie on / off | [`music_cmd_tie`](../../src/music_player.asm#L696) [`$E68E`](../reference/modules/music_player.md#music_cmd_tie) |
| `$A9` / `$AA` | - | ring modulation on / off (bit 2 of the control byte) | [`music_cmd_ring_mod`](../../src/music_player.asm#L704) [`$E69D`](../reference/modules/music_player.md#music_cmd_ring_mod) |
| `$AB` | - | waveform `$51` (pulse + triangle) | [`music_cmd_misc`](../../src/music_player.asm#L645) [`$E630`](../reference/modules/music_player.md#music_cmd_misc) |
| `$AC-$AF` | - | bit 0: 0 = short, 1 = long length table, for all voices | [`music_cmd_length_table`](../../src/music_player.asm#L639) [`$E627`](../reference/modules/music_player.md#music_cmd_length_table) |
| `$B0-$BF` | - | instrument n & 7: copies 6 bytes of [`music_instruments`](../../src/music_data.asm#L6) + 8n into the voice's 6 bytes of [`music_adsr_sets`](../../src/music_player.asm#L90) | [`music_cmd_instrument`](../../src/music_player.asm#L772) [`$E720`](../reference/modules/music_player.md#music_cmd_instrument) |
| `$C0-$CF` | lo, hi | pulse width: writes lo and hi to the voice's pulse registers at once | [`music_cmd_pulse_width`](../../src/music_player.asm#L809) [`$E75E`](../reference/modules/music_player.md#music_cmd_pulse_width) |
| `$D0-$DF` | xx | filter preset n & 7: writes the cutoff to `$D415`/`$D416` at once; [`music_filter_reson`](../../src/music_player.asm#L191) = preset byte 2 OR xx, [`music_filter_mode`](../../src/music_player.asm#L217) = preset byte 3; the next note of this voice writes them | [`music_cmd_filter`](../../src/music_player.asm#L820) [`$E779`](../reference/modules/music_player.md#music_cmd_filter) |
| `$E0-$EF` | nn | tempo: nn frames per tick; also reloads [`music_tempo_counter`](../../src/music_player.asm#L114) | [`music_cmd_tempo`](../../src/music_player.asm#L850) [`$E7B2`](../reference/modules/music_player.md#music_cmd_tempo) |
| `$F0-$FE` | - | the same as `$80-$8E`: group 7 branches to the first byte after the JMP table, which is [`music_cmd_length`](../../src/music_player.asm#L617) [`$E5FD`](../reference/modules/music_player.md#music_cmd_length) | [`music_cmd_length`](../../src/music_player.asm#L617) [`$E5FD`](../reference/modules/music_player.md#music_cmd_length) |
| `$FF` | - | end of the tune: [`music_end_flag`](../../src/music_player.asm#L215) = `$FF`, [`music_tune_ended`](../../src/music_player.asm#L209) = 1; the voice stops reading | [`music_read_command`](../../src/music_player.asm#L584) [`$E5C3`](../reference/modules/music_player.md#music_read_command) |

**Code** facts:
- The low nibble of `$Cx` and `$Ex` is ignored. `$B8-$BF` act as `$B0-$B7`, and `$D8-$DF` as `$D0-$D7`.
- [`music_volume`](../../src/music_player.asm#L221) [`$E311`](../reference/modules/music_player.md#music_volume) and [`music_filter_voice`](../../src/music_player.asm#L219) [`$E310`](../reference/modules/music_player.md#music_filter_voice) are global. Only the last volume or filter command counts, and only the voice that gave it writes `$D418`.
- A stream must start with a command. At the start of a tune [`music_init_tune`](../../src/music_player.asm#L270) [`$E38C`](../reference/modules/music_player.md#music_init_tune) sets [`music_lookahead`](../../src/music_player.asm#L116) = `$FF`, so the first byte is read as a command.
- The title tune does not use the filter, the tie on, ring modulation, the short length table or the transpose. Their code did not run in any recorded run ([`music_cmd_filter`](../../src/music_player.asm#L820) [`$E779`](../reference/modules/music_player.md#music_cmd_filter), [`music_cmd_ring_mod`](../../src/music_player.asm#L704) [`$E69D`](../reference/modules/music_player.md#music_cmd_ring_mod); **Observed**).

## 3. Note timing

A length command `$8n` reads entry n of [`music_length_table`](../../src/music_player.asm#L764) [`$E6F9`](../reference/modules/music_player.md#music_length_table), plus 16 for the long table. It splits the length L into a gate time G and a release time r by the articulation of the voice ([`music_calc_note_ticks`](../../src/music_player.asm#L719) [`$E6B6`](../reference/modules/music_player.md#music_calc_note_ticks)):

| Articulation | Command | Gate G | Release r |
|---|---|---|---|
| 0 | `$A4` | L − r | max(1, L / 8) |
| 1 | `$A5` | L / 2 | L / 2 |
| 2 | `$A6` | L − 1 | 1 |

The command stores G in [`music_gate_len_v1`](../../src/music_player.asm#L66) and −r in [`music_release_len_v1`](../../src/music_player.asm#L72) (per voice). It does not change the note that plays now.

| Index n | 0 | 1 | 2 | 3 | 4 | 5 | 6, 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14, 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Short table (ticks) | 32 | 16 | 8 | 4 | 2 | 1 | 8 | 48 | 24 | 12 | 6 | 3 | 2 | 8 |
| Long table (ticks) | 64 | 32 | 16 | 8 | 4 | 2 | 8 | 96 | 48 | 24 | 12 | 6 | 4 | 8 |

**Conclusion:** entries 0-5 are the whole note down to the 32nd note, and entries 8-12 are 1.5 times entries 0-4 (dotted notes).

Per tick and per voice, [`music_update`](../../src/music_player.asm#L449) [`$E49E`](../reference/modules/music_player.md#music_update) decrements [`music_dur_v1`](../../src/music_player.asm#L54):
1. When the counter becomes 0 and the voice is not tied, it writes the control byte with bit 0 clear: gate off ([`music_update`](../../src/music_player.asm#L449) [`$E4F4`](../../src/music_player.asm#L491)).
2. When the counter is negative and equals [`music_release_end_v1`](../../src/music_player.asm#L60), the note is over. The counter gets the gate time of the next note and [`music_release_end_v1`](../../src/music_player.asm#L60) gets its release time. Then [`music_next_note`](../../src/music_player.asm#L551) [`$E578`](../reference/modules/music_player.md#music_next_note) reads the next note.

So a note sounds with the gate on for G ticks and has r ticks of release: G + r = L ticks in all (L − 1 for an odd L with articulation 1). At the start of a tune the counters are 0 and the release ends are `$FF`, so the first note of each voice starts at the first tick (**Code**).

## 4. The song list and the end of a tune

[`music_start_song_list`](../../src/music_player.asm#L427) [`$E479`](../reference/modules/music_player.md#music_start_song_list) sets [`music_list_pos`](../../src/music_data.asm#L28) [`$E86C`](../reference/modules/music_data.md#music_list_pos) = [`music_list_start`](../../src/music_data.asm#L30) [`$E86D`](../reference/modules/music_data.md#music_list_start) and reads entries from [`music_song_list`](../../src/music_data.asm#L34) [`$E870`](../reference/modules/music_data.md#music_song_list) ([`music_list_step`](../../src/music_player.asm#L408) [`$E45E`](../reference/modules/music_player.md#music_list_step)):

| Entry | Meaning |
|---|---|
| `$00-$3F` | play tune n; [`music_list_pos`](../../src/music_data.asm#L28) points to the next entry |
| `$40-$7F` | [`music_transpose`](../../src/music_player.asm#L46) = b & `$3F`, then read the next entry |
| `$80-$FF` | end of the list: go back to [`music_list_start`](../../src/music_data.asm#L30) when bit 0 of the end action is set (always set on the first start), else stop |

When a voice reads `$FF`, the next frame of [`music_update`](../../src/music_player.asm#L449) calls [`music_end_of_tune`](../../src/music_player.asm#L383) [`$E438`](../reference/modules/music_player.md#music_end_of_tune) with Y = [`music_end_action`](../../src/music_player.asm#L226) [`$E314`](../reference/modules/music_player.md#music_end_action):

| End action | What happens |
|---|---|
| 0 | stop ([`music_silence`](../../src/music_player.asm#L311) [`$E3DA`](../reference/modules/music_player.md#music_silence)) |
| bit 7 set | play tune b & `$7F` |
| bit 1 set | continue the song list at [`music_list_pos`](../../src/music_data.asm#L28) |
| else | play the next tune; after [`music_last_tune`](../../src/music_data.asm#L26), tune 0 when bit 0 is set, else stop |

Then it jumps back into [`music_update`](../../src/music_player.asm#L449), so the tempo counter of the new tune already counts in that frame.

The game sets [`music_end_action`](../../src/music_player.asm#L226) = 3 and the song list to `$00 $FF` (see [sound.md](sound.md)). So the title tune plays again each time it ends. Only the song-list path of [`music_end_of_tune`](../../src/music_player.asm#L383) ran in the recorded runs (**Observed**).

## 5. The decoder

```text
music_update:                                  ; $E49E, once per frame
  if stop_request: silence; return             ; never ran (Observed)
  if not playing: return
  if end_flag == $FF:
      if end_action == 0: silence; return
      music_end_of_tune(end_action); goto music_update
  if --tempo_counter != 0: return
  tempo_counter = tempo
  for v in voice 1, 2, 3:
      dur[v] -= 1
      if dur[v] >= 0:
          if dur[v] == 0 and not tie[v]: SID control[v] = ctrl[v] & $FE
      else if dur[v] == release_end[v]:
          dur[v] = gate_len[v]; release_end[v] = release_len[v]
          if filter_voice == v: $D418 = filter_mode | volume; $D417 = filter_reson
          music_next_note(v)

music_next_note(v):                            ; $E578
  n = read_byte(v)
  if n == 0: SID frequency[v] = 0
  else:
      SID frequency[v] = note_freq[n + transpose]
      if not tie[v]: SID AD[v] = ad[v]; SR[v] = sr[v]; control[v] = ctrl[v]
  music_process_commands(v)

music_process_commands(v):                     ; $E5BB
  while lookahead[v] >= $80:
      c = read_byte(v)
      if c == $FF: end_flag = $FF; tune_ended = 1; return
      run the handler of group (c >> 4) & 7   ; section 2
```

[`music_init_tune`](../../src/music_player.asm#L270) [`$E38C`](../reference/modules/music_player.md#music_init_tune) runs at the start of a tune:
1. [`music_set_voice_ptrs`](../../src/music_player.asm#L241) [`$E360`](../reference/modules/music_player.md#music_set_voice_ptrs) copies the three stream addresses of tune min([`music_tune_number`](../../src/music_player.asm#L205), [`music_last_tune`](../../src/music_data.asm#L26)) into the fetch routines.
2. [`music_reset_state`](../../src/music_player.asm#L285) [`$E3A8`](../reference/modules/music_player.md#music_reset_state) clears [`music_filter_mode`](../../src/music_player.asm#L217) and [`music_filter_reson`](../../src/music_player.asm#L191), copies the template, loads [`music_tempo_counter`](../../src/music_player.asm#L114) from [`music_tempo`](../../src/music_player.asm#L213), and falls into [`music_clear_flags`](../../src/music_player.asm#L299) [`$E3C5`](../reference/modules/music_player.md#music_clear_flags). That clears [`music_stop_request`](../../src/music_player.asm#L207), [`music_end_flag`](../../src/music_player.asm#L215), [`music_playing`](../../src/music_player.asm#L211) and [`music_transpose`](../../src/music_player.asm#L46), and writes 0 to `$D400-$D417`.
3. For voices 1, 2, 3: [`music_lookahead`](../../src/music_player.asm#L116) = `$FF`, then [`music_process_commands`](../../src/music_player.asm#L579). So the commands before the first note of each voice run at once.

[`music_start_tune`](../../src/music_player.asm#L233) [`$E352`](../reference/modules/music_player.md#music_start_tune) sets [`music_playing`](../../src/music_player.asm#L211) = 0 around this, then 1.

## 6. Worked example: the start of the title tune

[`music_tune_table`](../../src/music_data.asm#L50) [`$E8C0`](../reference/modules/music_data.md#music_tune_table) holds `$E8D0`, `$E97D`, `$EA31` and `$E80A`. The first bytes of [`music_title_v1`](../../src/music_data.asm#L54) [`$E8D0`](../reference/modules/music_data.md#music_title_v1) are:

```text
$E8D0: 9C A2 B3 A6 C0 02 08 AD E0 02 A8 83 18 83 24 83 1F 83 20
```

| Address | Bytes | Command | Effect |
|---|---|---|---|
| `$E8D0` | `9C` | volume 12 | [`music_volume`](../../src/music_player.asm#L221) = 12, [`music_filter_voice`](../../src/music_player.asm#L219) = 1 |
| `$E8D1` | `A2` | waveform 2 | [`music_ctrl_v1`](../../src/music_player.asm#L82) [`$E116`](../reference/modules/music_player.md#music_ctrl_v1) = `$41` (pulse, gate on) |
| `$E8D2` | `B3` | instrument 3 | copies `09 00 09 00 00 70` from [`music_instruments+$18`](../../src/music_data.asm#L6) [`$E822`](../reference/modules/music_data.md#music_instruments) to [`music_adsr_sets`](../../src/music_player.asm#L90) [`$E11C`](../reference/modules/music_player.md#music_adsr_sets) |
| `$E8D3` | `A6` | articulation 2 | AD = `$00`, SR = `$70` (the third pair: sustain 7, release 0) |
| `$E8D4` | `C0 02 08` | pulse width | `$D402` = `$02`, `$D403` = `$08`: `$0802`, a square wave |
| `$E8D7` | `AD` | long length table | [`music_length_table_sel`](../../src/music_player.asm#L189) [`$E2E7`](../reference/modules/music_player.md#music_length_table_sel) = 1 |
| `$E8D8` | `E0 02` | tempo 2 | 2 frames per tick |
| `$E8DA` | `A8` | tie off | [`music_tie_v1`](../../src/music_player.asm#L48) [`$E101`](../reference/modules/music_player.md#music_tie_v1) = 0 |
| `$E8DB` | `83` | length 3 | long entry 3 ([`music_length_table+$13`](../../src/music_player.asm#L764) [`$E70C`](../reference/modules/music_player.md#music_length_table)) = 8 ticks; articulation 2: G = 7, r = 1 |
| `$E8DC` | `18` | note 24 = B2 | frequency `$07E5`; the first note, at tick 1 |
| `$E8DD` | `83` | length 3 | the same length for the next note |
| `$E8DE` | `24` | note 36 = B3 | frequency `$0FC9`, at tick 9 |
| `$E8E0` | `1F` | note 31 = F#3 | `$0BD3`, at tick 17 |
| `$E8E2` | `20` | note 32 = G3 | `$0C89`, at tick 25 |

The init reads `$E8D0-$E8DB` at once: the lookahead after `$83` is `$18`, a note. The first tick comes 2 frames after the start. There [`music_next_note`](../../src/music_player.asm#L551) [`$E578`](../reference/modules/music_player.md#music_next_note) reads `$18`, writes the frequency, AD `$00`, SR `$70` and control `$41` to voice 1, and then reads the command `$83` that follows. Each note of this bass line lasts 8 ticks = 16 frames: 14 frames with the gate on, 2 frames of release.

The other voices start the same way:
- [`music_title_v2`](../../src/music_data.asm#L79) [`$E97D`](../reference/modules/music_data.md#music_title_v2): `9F A2 B5 A4 C0 CE 04 A8 80 00`: volume 15, pulse, instrument 5 (AD/SR `$00/$F0`), articulation 0, pulse width `$04CE`, tie off, length 0 (64 ticks: G = 56, r = 8), then a rest.
- [`music_title_v3`](../../src/music_data.asm#L106) [`$EA31`](../reference/modules/music_data.md#music_title_v3): `9F A2 B0 A4 C0 CE 04 A8 80 00`: the same with instrument 0 (AD/SR `$11/$97`).

**Code:** the init reads the voices in the order 1, 2, 3, so [`music_filter_voice`](../../src/music_player.asm#L219) ends as 3 and [`music_volume`](../../src/music_player.asm#L221) as 15. The volume `$9C` of voice 1 never reaches the SID. At the first tick voice 3 writes `$0F` to `$D418`. The branch of voice 1 that would write it ([`music_update`](../../src/music_player.asm#L449) [`$E4E9`](../../src/music_player.asm#L485)) did not run in any recorded run (**Observed**).

## 7. The title tune

**Code**, decoded with the timing of section 3 (a simulation of [`music_update`](../../src/music_player.asm#L449) over the image):

| Voice | Stream | Notes | Content |
|---|---|---|---|
| 1 | [`music_title_v1`](../../src/music_data.asm#L54) [`$E8D0-$E97C`](../reference/modules/music_data.md#music_title_v1) | 81 | the bass: pulse, AD/SR `$00/$70`; the figure B2 B3 F#3 G3 in eighth notes (8 ticks), then E3 E4, C#4 and F#3 |
| 2 | [`music_title_v2`](../../src/music_data.asm#L79) [`$E97D-$EA30`](../reference/modules/music_data.md#music_title_v2) | 86 | 3 rests of 64 ticks, then fast falling arpeggios G7 E7 B6 G6 E6 B5 G5 E5 in 2-tick notes, and a figure in 4-tick notes from B5 |
| 3 | [`music_title_v3`](../../src/music_data.asm#L106) [`$EA31-$EAAC`](../reference/modules/music_data.md#music_title_v3) | 57 | the melody: one rest of 64 ticks, then B4 A4 B4 and E5 D5 E5; from tick 161 instrument 5 (`B5 A4` at `$EA4B`) |

- All three voices read their `$FF` at tick 577, in the same tick. One loop of the tune is 576 ticks of music: 1154 frames with the restart, about 23 seconds at 50 frames per second.
- Each stream ends with two rests and `$FF`. The last rest never sounds: the `$FF` follows it at once, and the next frame starts the tune again.
- The tempo is 2 frames per tick, so an eighth note lasts 0.32 seconds on PAL. **Conclusion:** about 94 quarter notes per minute.

### 7.1 Leftover bytes

- `$E86E-$E8BF` is a copy of [`music_title_v1`](../../src/music_data.asm#L54) from its fifth byte (`C0 02 08 AD E0 02 A8 83 ...`). The game writes the song list over two of these bytes at [`music_song_list`](../../src/music_data.asm#L34) [`$E870`](../reference/modules/music_data.md#music_song_list) (**Code**).
- `$EAAD-$EAB2` holds `9F A1 B0 A4 00 FF`, a stream of one rest. `$EAB3-$EAFF` is again a copy of the start of [`music_title_v1`](../../src/music_data.asm#L54) (**Code**).
- **Conclusion:** the music data was built for a longer layout and then cut. Voice 1 of tune 1 in [`music_tune_table`](../../src/music_data.asm#L50) points to the copy at `$EAB3`.

## 8. Still open

- How the title tune sounds on the real machine with the NTSC frequency table on PAL. A recording of the SID output in the emulator (title screen, sound on) can answer it.
- Which values reach `$D418` during the title tune. The code says only `$0F`; a watchpoint on `$D418` during one loop of the title tune can confirm it.
