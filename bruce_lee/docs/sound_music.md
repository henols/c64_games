# Bruce Lee: sound and music

The game has two sound drivers. A third-party music player plays the title tune on the title screen. Three small effect players, one for each SID voice, play the sound effects of the game and of the attract demo. The two drivers never run at the same time: the title interrupt calls only the music player, and the game interrupt calls only the effect players.

## Scope

- The MicroPearl music player: entry points, state, per-frame play (`music_player_state.asm`, `music_player.asm`).
- The music stream format, the instruments, the filter presets, the playlist and the end actions (`music_data.asm`).
- The note frequency table, which the music player and the effect players share.
- The title tune, decoded, with a worked example of its first bars.
- The three effect players and the effect stream format (`sfx_voice1.asm`, `sfx_voice2.asm`, `sfx_voice3.asm`, `sfx_data.asm`).
- The sound requests of the game and their priorities (`sound_request.asm`).
- A catalogue of the 15 effects, with the code that requests each one.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one run of the raster interrupt that calls the driver: [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) for the music, [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) (through [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update)) for the effects. The game runs on a PAL C64: 50 frames per second.
- A *tick* is the time step of the music player: [`music_tempo`](../src/music_player.asm#L20) frames.
- A *voice* of the music player is numbered 0-2. SID voice 1-3 is the same voice: music voice 0 is SID voice 1.
- A *note index* is an index into [`note_freq_lo`](../src/music_frequency_table.asm#L9) [`$E200`](reference/modules/music_frequency_table.md#note_freq_lo) / [`note_freq_hi`](../src/music_frequency_table.asm#L22) [`$E254`](reference/modules/music_frequency_table.md#note_freq_hi). Index n is the note n semitones above B0. Note names use the octave numbers of scientific pitch (A4 = 440 Hz).
- An *effect* n (0-14) is started with the *request value* `$80` + n.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## 1. Overview

~~~mermaid
flowchart TB
  subgraph TITLE["Title screen"]
    T1["show_title_screen $0584"] -->|"every 5th title"| T2["music_api_start $E003"]
    T3["irq_title_frame $152C"] -->|"each frame"| T4["music_api_play $E006"]
    T4 --> T5["music_play_frame $E49E"]
  end
  subgraph GAME["Game and demo"]
    G1["game code"] -->|"Y = $80+n"| G2["play_sound $2509"]
    G2 -->|"request in the state byte"| G3["sfx_voiceN_state"]
    G4["irq_game_bottom $48C1"] --> G5["frame_update $15A8"]
    G5 --> G6["sfx_voice1_update $EB03"]
    G5 --> G7["sfx_voice2_update $EF73"]
    G5 --> G8["sfx_voice3_update $F073"]
  end
~~~

1. On the title screen, [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) starts the title tune with [`music_api_start`](../src/music_player_state.asm#L11) [`$E003`](reference/modules/music_player_state.md#music_api_start), on the first title and then on every fifth title ([`title_music_skip_count`](../src/title_menu.asm#L163) [`$09BB`](reference/modules/title_menu.md#title_music_skip_count)), unless the S key has turned the tune off ([`title_music_off`](../src/room_enemy_tables.asm#L118) [`$1385`](reference/modules/room_enemy_tables.md#title_music_off)). **Code**
2. The title interrupt [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) calls [`music_api_play`](../src/music_player_state.asm#L13) [`$E006`](reference/modules/music_player_state.md#music_api_play) each frame. **Code**
3. [`restart_to_title`](../src/title_demo_start.asm#L9) [`$050F`](reference/modules/title_demo_start.md#restart_to_title), [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$0531`](reference/modules/title_demo_start.md#start_attract_demo) and [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) stop the tune with [`music_api_stop`](../src/music_player_state.asm#L9) [`$E000`](reference/modules/music_player_state.md#music_api_stop). **Code**
4. In the game and in the demo, the game code calls [`play_sound`](../src/sound_request.asm#L12) [`$2509`](reference/modules/sound_request.md#play_sound) with Y = `$80` + effect number. [`play_sound`](../src/sound_request.asm#L12) writes the request into the state byte of a free effect player. **Code**
5. [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) calls [`sfx_voice1_update`](../src/sfx_voice1.asm#L19) [`$EB03`](reference/modules/sfx_voice1.md#sfx_voice1_update), [`sfx_voice2_update`](../src/sfx_voice2.asm#L19) [`$EF73`](reference/modules/sfx_voice2.md#sfx_voice2_update) and [`sfx_voice3_update`](../src/sfx_voice3.asm#L19) [`$F073`](reference/modules/sfx_voice3.md#sfx_voice3_update) each frame. A player that sees a request starts the effect stream. **Code**
6. [`stop_all_sounds`](../src/sound_request.asm#L63) [`$255E`](reference/modules/sound_request.md#stop_all_sounds) frees the three effect players and writes 0 to the SID registers. [`show_title_screen`](../src/title_demo_start.asm#L83), [`draw_room`](../src/draw_room.asm#L28), [`show_player_screen`](../src/title_player_screens.asm#L71), [`init_game_variables`](../src/game_setup.asm#L18) and [`lose_fall`](../src/lose_fall_game_over.asm#L14) call it. **Code**

## 2. Catalogue of the sound data

| Name | Address | Layout | Readers | Writers |
|---|---|---|---|---|
| [`music_api_stop`](../src/music_player_state.asm#L9) | `$E000-$E008` | 3 `JMP`: stop, start the playlist, play one frame | the game | - |
| [`music_transpose`](../src/music_voice_state.asm#L7) .. [`music_envelopes`](../src/music_voice_state.asm#L41) | `$E100-$E12D` | voice state, 46 bytes, arrays of 3 (section 3.2) | the player | [`music_reset_state`](../src/music_player.asm#L101) [`$E3A8`](reference/modules/music_player.md#music_reset_state), the commands |
| [`note_freq_lo`](../src/music_frequency_table.asm#L9) / [`note_freq_hi`](../src/music_frequency_table.asm#L22) | `$E200` / `$E254` | 84 bytes each: SID frequency of note index 0-83 | music and effect players | - |
| [`music_voice_init`](../src/music_frequency_table.asm#L37) | `$E2A8` | 46 bytes: reset image of `$E100-$E12D` | [`music_reset_state`](../src/music_player.asm#L101) [`$E3A8`](reference/modules/music_player.md#music_reset_state) | - |
| [`music_cmd_offsets`](../src/music_frequency_table.asm#L47) | `$E2D6` | 17 branch offsets, 8 used | [`music_voice_dispatch`](../src/music_player.asm#L430) [`$E5D7`](reference/modules/music_player.md#music_voice_dispatch) | - |
| [`music_jump_stop`](../src/music_player.asm#L6) | `$E300-$E308` | 3 `JMP`: stop, start song, start playlist | API, [`music_start_song_x`](../src/music_player.asm#L226) [`$E455`](reference/modules/music_player.md#music_start_song_x) | - |
| [`music_song`](../src/music_player.asm#L12) .. [`music_end_action`](../src/music_player.asm#L35) | `$E309-$E314` | player globals (section 3.2) | the player | the player, the title code |
| [`music_length_table`](../src/music_player.asm#L611) | `$E6F9` | 2 rows of 16 bytes: ticks of each length code | [`music_note_length`](../src/music_player.asm#L564) [`$E6B6`](reference/modules/music_player.md#music_note_length) | - |
| [`sid_voice_offsets`](../src/music_player.asm#L614) | `$E719` | `$00`, `$07`, `$0E` | the player | - |
| [`music_waveforms`](../src/music_player.asm#L616) | `$E71C` | `$11`, `$21`, `$41`, `$81` | [`music_cmd_voice_option`](../src/music_player.asm#L486) [`$E630`](reference/modules/music_player.md#music_cmd_voice_option) | - |
| [`music_instruments`](../src/music_data.asm#L8) | `$E80A` | 8 instruments of 8 bytes | [`music_cmd_instrument`](../src/music_player.asm#L620) [`$E720`](reference/modules/music_player.md#music_cmd_instrument) | - |
| [`music_filter_presets`](../src/music_data.asm#L19) | `$E84A` | 8 presets of 4 bytes | [`music_cmd_filter`](../src/music_player.asm#L670) [`$E779`](reference/modules/music_player.md#music_cmd_filter) | - |
| [`music_playlist`](../src/music_data.asm#L37) | `$E870` | playlist entries (2 bytes used) | [`music_playlist_read`](../src/music_player.asm#L233) [`$E45E`](reference/modules/music_player.md#music_playlist_read) | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) |
| [`music_song_table`](../src/music_songs.asm#L7) | `$E8C0` | 8 bytes per song: 3 stream addresses and an instrument table address | [`music_set_voice_pointers`](../src/music_player.asm#L53) [`$E360`](reference/modules/music_player.md#music_set_voice_pointers) | - |
| `music_title_voice0/1/2` | `$E8D0` / `$E97D` / `$EA31` | streams of the title tune | [`music_fetch_voice0`](../src/music_player.asm#L135) .. `2` | - |
| [`sfx_voice1_state`](../src/sfx_voice1.asm#L6) .. [`sfx_voice1_timer`](../src/sfx_voice1.asm#L10) | `$EB00-$EB02` | state, stream position, timer of SID voice 1 | [`sfx_voice1_update`](../src/sfx_voice1.asm#L19) [`$EB03`](reference/modules/sfx_voice1.md#sfx_voice1_update) | the player, [`play_sound`](../src/sound_request.asm#L12) [`$2509`](reference/modules/sound_request.md#play_sound) |
| [`sfx_voice2_state`](../src/sfx_voice2.asm#L6) / [`sfx_voice3_state`](../src/sfx_voice3.asm#L6) | `$EF70` / `$F070` | the same 3 bytes for SID voices 2 and 3 | the players | the players, [`play_sound`](../src/sound_request.asm#L12) |
| [`sfx_voice1_stream`](../src/constants.asm#L124) / [`sfx_voice2_stream`](../src/constants.asm#L125) / [`sfx_voice3_stream`](../src/constants.asm#L126) | `$00F6` / `$00F8` / `$00FA` | zero-page pointer to the stream of each voice | the players | the players |
| [`sfx_stream_table`](../src/sfx_data.asm#L6) | `$EBE5` | 15 words: stream address of each effect | the three players | - |
| [`sfx_cmd_offsets`](../src/sfx_data.asm#L13) | `$EC03` | 14 branch offsets, 8 used | the three players | - |
| [`sfx_adsr_table`](../src/sfx_data.asm#L18) | `$EC11` | AD/SR pairs, even index | the three players | - |
| [`sfx_pulse_table`](../src/sfx_data.asm#L25) | `$EC1B` | 11 pulse widths (words), even index | the three players | - |
| [`sfx_footstep_stream`](../src/sfx_data.asm#L35) .. [`sfx_lantern_stream`](../src/sfx_data.asm#L146) | `$EC31-$EE82` | the 15 effect streams | the three players | - |
| [`sound_priority_table`](../src/sound_request.asm#L76) | `$2572` | 15 bytes: priority of each effect | [`play_sound`](../src/sound_request.asm#L12) [`$2509`](reference/modules/sound_request.md#play_sound) | - |
| [`voice1_sound_priority`](../src/sound_request.asm#L80) .. [`voice3_sound_priority`](../src/sound_request.asm#L84) | `$2581-$2583` | priority of the effect on each voice | [`play_sound`](../src/sound_request.asm#L12) | [`play_sound`](../src/sound_request.asm#L12) |

## 3. The music player

The player has a credit text at [`music_player_credit`](../src/music_player.asm#L38) [`$E315`](reference/modules/music_player.md#music_player_credit): " MICROPEARL MUSIC PLAYER  COPYRIGHT 1983 JOHN A. FITZPATRICK ". Nothing reads the text. **Code**

### 3.1 Entry points

| Entry | Address | Goes to | Called by |
|---|---|---|---|
| [`music_api_stop`](../src/music_player_state.asm#L9) | `$E000` | [`music_jump_stop`](../src/music_player.asm#L6) [`$E300`](reference/modules/music_player.md#music_jump_stop) -> [`music_stop`](../src/music_player.asm#L199) [`$E434`](reference/modules/music_player.md#music_stop) -> [`music_silence`](../src/music_player.asm#L129) [`$E3DA`](reference/modules/music_player.md#music_silence) | [`restart_to_title`](../src/title_demo_start.asm#L9) [`$051C`](../src/title_demo_start.asm#L17), [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$054A`](../src/title_demo_start.asm#L45), [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0729`](../src/title_demo_start.asm#L295) |
| [`music_api_start`](../src/music_player_state.asm#L11) | `$E003` | [`music_jump_start_playlist`](../src/music_player.asm#L10) [`$E306`](reference/modules/music_player.md#music_jump_start_playlist) -> [`music_start_playlist`](../src/music_player.asm#L253) [`$E479`](reference/modules/music_player.md#music_start_playlist) | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$06DA`](../src/title_demo_start.asm#L241) |
| [`music_api_play`](../src/music_player_state.asm#L13) | `$E006` | [`music_play_frame`](../src/music_player.asm#L279) [`$E49E`](reference/modules/music_player.md#music_play_frame) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$154C`](../src/screen_raster_irqs.asm#L99), each frame of the title and game over screens |
| [`music_jump_start_song`](../src/music_player.asm#L8) | `$E303` | [`music_init_song`](../src/music_player.asm#L43) [`$E352`](reference/modules/music_player.md#music_init_song) | [`music_start_song_x`](../src/music_player.asm#L226) [`$E455`](reference/modules/music_player.md#music_start_song_x) (playlist and end actions) |

The game sets [`music_stop_request`](../src/music_player.asm#L14) [`$E30A`](reference/modules/music_player.md#music_stop_request) to 1 before it calls [`music_api_stop`](../src/music_player_state.asm#L9) in [`start_attract_demo`](../src/title_demo_start.asm#L32) and [`show_title_screen`](../src/title_demo_start.asm#L83). **Code**

Before [`music_api_start`](../src/music_player_state.asm#L11), [`show_title_screen`](../src/title_demo_start.asm#L83) writes the playlist: [`music_end_action`](../src/music_player.asm#L35) = 3, [`music_playlist`](../src/music_data.asm#L37) = `$00` (song 0) and [`music_playlist_end`](../src/music_data.asm#L39) = `$FF` (end of the list). So the title tune loops. **Code**

### 3.2 State

Globals of the player:

| Name | Address | Meaning |
|---|---|---|
| [`music_song`](../src/music_player.asm#L12) | `$E309` | song being played (0 = the title tune) |
| [`music_stop_request`](../src/music_player.asm#L14) | `$E30A` | nonzero: [`music_play_frame`](../src/music_player.asm#L279) silences the SID and stops |
| [`music_song_ended`](../src/music_player.asm#L16) | `$E30B` | 1 when a voice reads its end byte `$FF`; nothing reads it |
| [`music_playing`](../src/music_player.asm#L18) | `$E30C` | 1 = the song plays, 0 = stopped or being set up |
| [`music_tempo`](../src/music_player.asm#L20) | `$E30D` | frames per tick (command `$Ex`) |
| [`music_end_marker`](../src/music_player.asm#L22) | `$E30E` | `$FF` when a voice has read its end byte |
| [`music_filter_mode`](../src/music_player.asm#L24) | `$E30F` | filter mode bits for the high nibble of [`SIGVOL`](../src/constants.asm#L271) [`$D418`](reference/variables.md#SIGVOL) (command `$Dx`) |
| [`music_volume_voice`](../src/music_player.asm#L26) | `$E310` | voice + 1 whose next note writes `$D418`/`$D417`; 0 = nothing pending |
| [`music_volume`](../src/music_player.asm#L28) | `$E311` | master volume (command `$9x`) |
| [`music_temp`](../src/music_player.asm#L30) | `$E312` | scratch |
| [`music_end_action`](../src/music_player.asm#L35) | `$E314` | what happens at the end of a song (section 4.7) |
| [`music_long_lengths`](../src/music_frequency_table.asm#L51) | `$E2E7` | 1 = second row of [`music_length_table`](../src/music_player.asm#L611) (commands `$AC-$AF`) |
| [`music_resonance`](../src/music_frequency_table.asm#L53) | `$E2E8` | value for [`RESON`](../src/constants.asm#L270) [`$D417`](reference/variables.md#RESON) (command `$Dx`) |
| [`music_voice`](../src/music_voice_state.asm#L45) | `$E12E` | voice being processed |
| [`music_tempo_counter`](../src/music_voice_state.asm#L47) | `$E12F` | frames left in the current tick |
| [`music_lookahead`](../src/music_voice_state.asm#L49) | `$E130` | the stream byte after the byte just read |
| [`music_last_song`](../src/music_data.asm#L29) | `$E86B` | highest song number (1) |
| [`music_playlist_pos`](../src/music_data.asm#L31) / [`music_playlist_start`](../src/music_data.asm#L33) | `$E86C` / `$E86D` | next playlist index, first playlist index |

The voice state `$E100-$E12D` (arrays of 3 bytes, index = voice):

| Name | Address | Meaning | Reset value |
|---|---|---|---|
| [`music_transpose`](../src/music_voice_state.asm#L7) | `$E100` | added to each note index (1 byte, all voices) | 0 |
| [`music_voice_tie`](../src/music_voice_state.asm#L10) | `$E101` | 1 = tied: no new envelope, no gate off | 0 |
| [`music_voice_ticks`](../src/music_voice_state.asm#L14) | `$E104` | tick counter of the current note | 0 |
| [`music_voice_end_tick`](../src/music_voice_state.asm#L17) | `$E107` | counter value that ends the note: minus the release ticks | `$FF` |
| [`music_voice_gate_ticks`](../src/music_voice_state.asm#L20) | `$E10A` | gate ticks of the next note | 7 |
| [`music_voice_end_reload`](../src/music_voice_state.asm#L23) | `$E10D` | end tick of the next note | `$FF` |
| [`music_voice_attack_decay`](../src/music_voice_state.asm#L26) | `$E110` | SID AD value | `$11` |
| [`music_voice_sustain_release`](../src/music_voice_state.asm#L29) | `$E113` | SID SR value | `$97` |
| [`music_voice_control`](../src/music_voice_state.asm#L32) | `$E116` | SID control value (waveform, gate bit 0 = 1) | `$21` |
| [`music_voice_articulation`](../src/music_voice_state.asm#L36) | `$E119` | 0 normal, 1 staccato, 2 legato | 0 |
| [`music_envelopes`](../src/music_voice_state.asm#L41) | `$E11C` | 6 bytes per voice: AD/SR of articulation 0, 1, 2 of the current instrument | instrument 0 |

[`music_reset_state`](../src/music_player.asm#L101) [`$E3A8`](reference/modules/music_player.md#music_reset_state) copies [`music_voice_init`](../src/music_frequency_table.asm#L37) [`$E2A8`](reference/modules/music_frequency_table.md#music_voice_init) over `$E100-$E12D` before each song. **Code**

### 3.3 Starting a song

[`music_start_playlist`](../src/music_player.asm#L253) [`$E479`](reference/modules/music_player.md#music_start_playlist) (the start entry) does these steps:

1. Y = 1 (the "loop" bit). [`music_playlist_pos`](../src/music_data.asm#L31) = [`music_playlist_start`](../src/music_data.asm#L33).
2. [`music_playlist_read`](../src/music_player.asm#L233) [`$E45E`](reference/modules/music_player.md#music_playlist_read) reads the playlist entry. Entry `$00` gives song 0. [`music_playlist_pos`](../src/music_data.asm#L31) moves on.
3. [`music_start_song_x`](../src/music_player.asm#L226) [`$E455`](reference/modules/music_player.md#music_start_song_x) stores the song in [`music_song`](../src/music_player.asm#L12) and jumps through [`music_jump_start_song`](../src/music_player.asm#L8) [`$E303`](reference/modules/music_player.md#music_jump_start_song) to [`music_init_song`](../src/music_player.asm#L43) [`$E352`](reference/modules/music_player.md#music_init_song).
4. [`music_init_song`](../src/music_player.asm#L43) clears [`music_playing`](../src/music_player.asm#L18), calls [`music_setup_song`](../src/music_player.asm#L85) [`$E38C`](reference/modules/music_player.md#music_setup_song) and sets [`music_playing`](../src/music_player.asm#L18) = 1.

[`music_setup_song`](../src/music_player.asm#L85) [`$E38C`](reference/modules/music_player.md#music_setup_song):

1. [`music_set_voice_pointers`](../src/music_player.asm#L53) [`$E360`](reference/modules/music_player.md#music_set_voice_pointers) copies the three stream addresses of the song from [`music_song_table`](../src/music_songs.asm#L7) [`$E8C0`](reference/modules/music_songs.md#music_song_table) into the operands of the fetch routines [`music_fetch_voice0`](../src/music_player.asm#L135) [`$E3DE`](reference/modules/music_player.md#music_fetch_voice0), [`music_fetch_voice1`](../src/music_player.asm#L140) [`$E3E2`](reference/modules/music_player.md#music_fetch_voice1) and [`music_fetch_voice2`](../src/music_player.asm#L145) [`$E3E6`](reference/modules/music_player.md#music_fetch_voice2). Each fetch routine is `LDA abs` / `RTS`. A song number above [`music_last_song`](../src/music_data.asm#L29) becomes [`music_last_song`](../src/music_data.asm#L29).
2. [`music_reset_state`](../src/music_player.asm#L101) [`$E3A8`](reference/modules/music_player.md#music_reset_state): filter mode and resonance 0, voice state from [`music_voice_init`](../src/music_frequency_table.asm#L37), [`music_tempo_counter`](../src/music_voice_state.asm#L47) = [`music_tempo`](../src/music_player.asm#L20), then [`music_clear_and_silence`](../src/music_player.asm#L117) [`$E3C5`](reference/modules/music_player.md#music_clear_and_silence) writes 0 to `$D400-$D417` and to the player flags.
3. For each voice: [`music_lookahead`](../src/music_voice_state.asm#L49) = `$FF`, then [`music_voice_commands`](../src/music_player.asm#L417) [`$E5BB`](reference/modules/music_player.md#music_voice_commands). This reads the commands before the first note of the voice. **Code**

[`music_read_byte`](../src/music_player.asm#L153) [`$E3EA`](reference/modules/music_player.md#music_read_byte) reads a byte of the current voice with its fetch routine, increments the operand of the fetch routine (self-modified code), and reads the next byte into [`music_lookahead`](../src/music_voice_state.asm#L49). **Code**

### 3.4 Per-frame play

[`music_play_frame`](../src/music_player.asm#L279) [`$E49E`](reference/modules/music_player.md#music_play_frame) runs once per frame:

1. When [`music_stop_request`](../src/music_player.asm#L14) is nonzero: [`music_silence`](../src/music_player.asm#L129) [`$E3DA`](reference/modules/music_player.md#music_silence), stop.
2. When [`music_playing`](../src/music_player.asm#L18) is 0: return.
3. When [`music_end_marker`](../src/music_player.asm#L22) = `$FF`: when [`music_end_action`](../src/music_player.asm#L35) is 0, silence and stop; else [`music_song_end_action`](../src/music_player.asm#L205) [`$E438`](reference/modules/music_player.md#music_song_end_action) chooses the next song (section 4.7), and the routine starts again.
4. Decrement [`music_tempo_counter`](../src/music_voice_state.asm#L47). When it is not 0, return. Else reload it from [`music_tempo`](../src/music_player.asm#L20): a tick starts.
5. For voice 0, 1, 2 (code repeated three times, from [`music_voice1_update`](../src/music_player.asm#L329) [`$E503`](reference/modules/music_player.md#music_voice1_update) and [`music_voice2_update`](../src/music_player.asm#L356) [`$E53D`](reference/modules/music_player.md#music_voice2_update) for voices 1 and 2):
   1. Decrement [`music_voice_ticks`](../src/music_voice_state.asm#L14).
   2. When the counter is 0 and the voice is not tied: write [`music_voice_control`](../src/music_voice_state.asm#L32) AND `$FE` to the control register of the voice. The gate goes off and the release starts.
   3. When the counter is negative and equals [`music_voice_end_tick`](../src/music_voice_state.asm#L17): the note has ended. Reload the counter from [`music_voice_gate_ticks`](../src/music_voice_state.asm#L20) and the end tick from [`music_voice_end_reload`](../src/music_voice_state.asm#L23). When [`music_volume_voice`](../src/music_player.asm#L26) = voice + 1, call [`music_apply_volume`](../src/music_player.asm#L266) [`$E489`](reference/modules/music_player.md#music_apply_volume). Call [`music_voice_start_note`](../src/music_player.asm#L386) [`$E578`](reference/modules/music_player.md#music_voice_start_note).

[`music_voice_start_note`](../src/music_player.asm#L386) [`$E578`](reference/modules/music_player.md#music_voice_start_note):

1. Read the note byte.
2. Note 0 is a rest: write 0 to the frequency. The gate and the envelope stay as they are.
3. Else frequency = `note_freq_lo/hi` [note + [`music_transpose`](../src/music_voice_state.asm#L7)]. When the voice is not tied, write AD, SR and control (gate on) of the voice to the SID.
4. [`music_voice_commands`](../src/music_player.asm#L417) [`$E5BB`](reference/modules/music_player.md#music_voice_commands) reads the command bytes that follow, until the next note byte. So commands written before a note apply to that note.

```
music_voice_commands:
  while music_lookahead >= $80:
    c = read_byte()
    if c == $FF: music_end_marker = $FF; return
    group = (c >> 4) & 7
    branch offset = music_cmd_offsets[group]      ; self-modified BCC at music_cmd_branch
    goto music_cmd_jumps + offset                  ; each handler loops back here
```

**Conclusion.** A note lasts gate ticks + release ticks. The gate is on for the gate ticks; the release ticks follow with the gate off. Section 4.3 gives the two numbers.

### 3.5 The state machine of the player

~~~mermaid
stateDiagram-v2
  state "Stopped (music_playing 0)" as Stopped
  state "Playing (music_playing 1)" as Playing
  state "Song ended (music_end_marker $FF)" as Ended
  [*] --> Stopped
  Stopped --> Playing: music_api_start $E003
  Playing --> Ended: a voice reads $FF
  Ended --> Playing: end action chooses a song
  Ended --> Stopped: end action 0 or end of list
  Playing --> Stopped: music_stop_request or music_api_stop
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Stopped | [`music_api_start`](../src/music_player_state.asm#L11) | Playing | [`music_start_playlist`](../src/music_player.asm#L253) [`$E479`](reference/modules/music_player.md#music_start_playlist), [`music_init_song`](../src/music_player.asm#L43) [`$E352`](reference/modules/music_player.md#music_init_song) |
| Playing | a voice reads the end byte `$FF` | Song ended | [`music_voice_read_command`](../src/music_player.asm#L421) [`$E5C3`](reference/modules/music_player.md#music_voice_read_command) |
| Song ended | [`music_end_action`](../src/music_player.asm#L35) chooses a song or a playlist entry | Playing | [`music_song_end_action`](../src/music_player.asm#L205) [`$E438`](reference/modules/music_player.md#music_song_end_action) |
| Song ended | [`music_end_action`](../src/music_player.asm#L35) = 0, or end of the playlist with bit 0 clear, or after the last song with bit 0 clear | Stopped | [`music_play_frame`](../src/music_player.asm#L279) [`$E49E`](reference/modules/music_player.md#music_play_frame), [`music_silence`](../src/music_player.asm#L129) [`$E3DA`](reference/modules/music_player.md#music_silence) |
| Playing | [`music_stop_request`](../src/music_player.asm#L14) nonzero | Stopped | [`music_play_frame`](../src/music_player.asm#L279) [`$E49E`](reference/modules/music_player.md#music_play_frame) |
| any | [`music_api_stop`](../src/music_player_state.asm#L9) | Stopped | [`music_stop`](../src/music_player.asm#L199) [`$E434`](reference/modules/music_player.md#music_stop) |

## 4. The music stream format

### 4.1 Where the data is

- [`music_song_table`](../src/music_songs.asm#L7) [`$E8C0`](reference/modules/music_songs.md#music_song_table): 8 bytes per song: the stream address of voice 0, 1, 2 and an instrument table address. The player ignores the instrument table address and uses [`music_instruments`](../src/music_data.asm#L8) [`$E80A`](reference/modules/music_data.md#music_instruments).
- Song 0 is the title tune: [`music_title_voice0`](../src/music_songs.asm#L16) [`$E8D0`](reference/modules/music_songs.md#music_title_voice0), [`music_title_voice1`](../src/music_songs.asm#L40) [`$E97D`](reference/modules/music_songs.md#music_title_voice1), [`music_title_voice2`](../src/music_songs.asm#L65) [`$EA31`](reference/modules/music_songs.md#music_title_voice2).
- Song 1 ([`music_song1_voices`](../src/music_songs.asm#L12) [`$E8C8`](reference/modules/music_songs.md#music_song1_voices)) points to `$EAB3`, `$EB60` and `$EC14`. Only `$EAB3` is a stream; the other two point into the effect player. No code selects song 1. **Code**
- Readers: [`music_read_byte`](../src/music_player.asm#L153) [`$E3EA`](reference/modules/music_player.md#music_read_byte) through the self-modified fetch routines.

### 4.2 Byte layout

One stream for each voice. A byte below `$80` is a note. A byte from `$80` is a command. Bits 4-6 of a command select the handler.

| Byte | Arguments | Meaning | Handler |
|---|---|---|---|
| `$00` | - | rest: frequency 0 for one note length | [`music_voice_start_note`](../src/music_player.asm#L386) [`$E578`](reference/modules/music_player.md#music_voice_start_note) |
| `$01-$7F` | - | note index n (+ [`music_transpose`](../src/music_voice_state.asm#L7)): frequency from `note_freq_lo/hi` | [`music_voice_set_freq`](../src/music_player.asm#L396) [`$E590`](reference/modules/music_player.md#music_voice_set_freq) |
| `$80-$8F` | - | length code n = low nibble, for the following notes (section 4.3) | [`music_cmd_length`](../src/music_player.asm#L457) [`$E5FD`](reference/modules/music_player.md#music_cmd_length) |
| `$90-$9F` | - | master volume n; the next note of this voice writes `$D418` = [`music_filter_mode`](../src/music_player.asm#L24) OR n and `$D417` = [`music_resonance`](../src/music_frequency_table.asm#L53) | [`music_cmd_volume`](../src/music_player.asm#L470) [`$E617`](reference/modules/music_player.md#music_cmd_volume) |
| `$A0-$A3` | - | waveform: triangle `$11`, sawtooth `$21`, pulse `$41`, noise `$81` (gate bit set) | [`music_cmd_voice_option`](../src/music_player.asm#L486) [`$E630`](reference/modules/music_player.md#music_cmd_voice_option) |
| `$A4-$A6` | - | articulation 0, 1, 2; loads AD/SR of that articulation from the instrument of the voice | [`music_cmd_articulation`](../src/music_player.asm#L502) [`$E64E`](reference/modules/music_player.md#music_cmd_articulation) |
| `$A7` / `$A8` | - | tie on / tie off | [`music_cmd_tie_or_ring`](../src/music_player.asm#L538) [`$E68E`](reference/modules/music_player.md#music_cmd_tie_or_ring) |
| `$A9` / `$AA` | - | ring modulation bit on / off | [`music_cmd_ring_mod`](../src/music_player.asm#L546) [`$E69D`](reference/modules/music_player.md#music_cmd_ring_mod) |
| `$AB` | - | waveform `$51` (pulse + triangle) | [`music_cmd_voice_option`](../src/music_player.asm#L486) [`$E630`](reference/modules/music_player.md#music_cmd_voice_option) |
| `$AC`, `$AE` / `$AD`, `$AF` | - | normal / long length table, for all voices | [`music_cmd_length_set`](../src/music_player.asm#L479) [`$E627`](reference/modules/music_player.md#music_cmd_length_set) |
| `$B0-$BF` | - | instrument n AND 7: copies its 6 envelope bytes into [`music_envelopes`](../src/music_voice_state.asm#L41) of the voice | [`music_cmd_instrument`](../src/music_player.asm#L620) [`$E720`](reference/modules/music_player.md#music_cmd_instrument) |
| `$C0-$CF` | lo, hi | pulse width of the voice, written at once | [`music_cmd_pulse_width`](../src/music_player.asm#L657) [`$E75E`](reference/modules/music_player.md#music_cmd_pulse_width) |
| `$D0-$DF` | routing | filter preset n AND 7: cutoff to `$D415`/`$D416` at once; mode to [`music_filter_mode`](../src/music_player.asm#L24); routing OR preset resonance to [`music_resonance`](../src/music_frequency_table.asm#L53); the next note of the voice writes `$D417`/`$D418` | [`music_cmd_filter`](../src/music_player.asm#L670) [`$E779`](reference/modules/music_player.md#music_cmd_filter) |
| `$E0-$EF` | t | tempo: t frames per tick | [`music_cmd_tempo`](../src/music_player.asm#L700) [`$E7B2`](reference/modules/music_player.md#music_cmd_tempo) |
| `$F0-$FE` | - | length code n, the same as `$8n` | [`music_cmd_length`](../src/music_player.asm#L457) [`$E5FD`](reference/modules/music_player.md#music_cmd_length) |
| `$FF` | - | end of the song. The first voice that reads it ends the song for all voices. | [`music_voice_read_command`](../src/music_player.asm#L421) [`$E5C3`](reference/modules/music_player.md#music_voice_read_command) |

**Code** for each row. The title tune uses no ring modulation, no filter and no tie on ([`music_cmd_ring_mod`](../src/music_player.asm#L546) and [`music_cmd_filter`](../src/music_player.asm#L670) are marked not executed in the coverage). **Observed**

### 4.3 Note lengths and articulation

[`music_note_length`](../src/music_player.asm#L564) [`$E6B6`](reference/modules/music_player.md#music_note_length) turns a length code into L ticks with [`music_length_table`](../src/music_player.asm#L611) [`$E6F9`](reference/modules/music_player.md#music_length_table):

| Code | Value | Ticks, normal table | Ticks, long table |
|---|---|---|---|
| 0 | whole | 32 | 64 |
| 1 | half | 16 | 32 |
| 2 | quarter | 8 | 16 |
| 3 | eighth | 4 | 8 |
| 4 | 16th | 2 | 4 |
| 5 | 32nd | 1 | 2 |
| 8 | dotted whole | 48 | 96 |
| 9 | dotted half | 24 | 48 |
| 10 | dotted quarter | 12 | 24 |
| 11 | dotted eighth | 6 | 12 |
| 12 | dotted 16th | 3 | 6 |
| 13 | dotted 32nd | 2 | 4 |
| 6, 7, 14, 15 | - | 8 | 8 |

The articulation of the voice at the time of the length command splits L into gate ticks G and release ticks R (G + R = L):

| Articulation | Command | G (gate on) | R (gate off) |
|---|---|---|---|
| 0 normal | `$A4` | L - L/8 | L/8, at least 1 |
| 1 staccato | `$A5` | L/2 | L/2 |
| 2 legato | `$A6` | L - 1 | 1 |

[`music_cmd_length`](../src/music_player.asm#L457) stores G in [`music_voice_gate_ticks`](../src/music_voice_state.asm#L20) and -R in [`music_voice_end_reload`](../src/music_voice_state.asm#L23). **Code**

### 4.4 Instruments and ADSR

[`music_instruments`](../src/music_data.asm#L8) [`$E80A`](reference/modules/music_data.md#music_instruments): 8 instruments of 8 bytes: AD, SR for articulation 0, AD, SR for articulation 1, AD, SR for articulation 2, and 2 unused bytes.

| n | Articulation 0 (AD SR) | Articulation 1 | Articulation 2 | Used by the title tune |
|---|---|---|---|---|
| 0 | `$11` `$97` | `$00` `$93` | `$22` `$9B` | voice 2 |
| 1 | `$22` `$97` | `$11` `$95` | `$33` `$9B` | - |
| 2 | `$11` `$93` | `$11` `$92` | `$11` `$97` | - |
| 3 | `$09` `$00` | `$09` `$00` | `$00` `$70` | voice 0 (legato) |
| 4 | `$60` `$00` | `$60` `$00` | `$60` `$00` | - |
| 5 | `$00` `$F0` | `$00` `$F0` | `$00` `$F0` | voices 1 and 2 |
| 6 | `$66` `$00` | `$66` `$00` | `$66` `$00` | - |
| 7 | `$88` `$98` | `$55` `$95` | `$BB` `$9B` | - |

The instrument command `$Bn` only copies the 6 bytes into [`music_envelopes`](../src/music_voice_state.asm#L41). The AD/SR values of the voice change with the next articulation command `$A4-$A6`. The SID gets them at the next note that is not tied. **Code**

### 4.5 Filter presets

[`music_filter_presets`](../src/music_data.asm#L19) [`$E84A`](reference/modules/music_data.md#music_filter_presets): 8 presets of 4 bytes: cutoff low (`$D415`), cutoff high (`$D416`), resonance in the high nibble (`$D417`), filter mode (`$10` low pass, `$20` band pass, `$40` high pass).

| n | Cutoff lo | Cutoff hi | Resonance | Mode |
|---|---|---|---|---|
| 0 | `$00` | `$11` | `$F0` | `$10` |
| 1 | `$01` | `$44` | `$F0` | `$20` |
| 2 | `$02` | `$77` | `$F0` | `$40` |
| 3 | `$00` | `$22` | `$70` | `$10` |
| 4 | `$01` | `$44` | `$70` | `$20` |
| 5 | `$02` | `$55` | `$70` | `$40` |
| 6 | `$01` | `$44` | `$30` | `$30` |
| 7 | `$00` | `$22` | `$30` | `$60` |

### 4.6 Tempo

The command `$Ex` t sets [`music_tempo`](../src/music_player.asm#L20) and [`music_tempo_counter`](../src/music_voice_state.asm#L47) to t. One tick is t frames. The title tune uses t = 2. **Code**

### 4.7 Playlist and end actions

The playlist starts at [`music_playlist`](../src/music_data.asm#L37) [`$E870`](reference/modules/music_data.md#music_playlist); [`music_playlist_start`](../src/music_data.asm#L33) [`$E86D`](reference/modules/music_data.md#music_playlist_start) is the first index.

| Entry | Meaning |
|---|---|
| `$00-$3F` | play song n |
| `$40-$7F` | transpose = n AND `$3F`, then read the next entry |
| `$80-$FF` | end of the list |

A transpose entry has no effect: [`music_reset_state`](../src/music_player.asm#L101) clears [`music_transpose`](../src/music_voice_state.asm#L7) before the song starts. **Code**

[`music_end_action`](../src/music_player.asm#L35) [`$E314`](reference/modules/music_player.md#music_end_action):

| Value | At the end of a song |
|---|---|
| 0 | stop |
| bit 7 set | play song (value AND `$7F`) |
| bit 1 set | next playlist entry; at the end of the list: bit 0 set = start the list again, bit 0 clear = stop |
| else | next song number; after [`music_last_song`](../src/music_data.asm#L29): bit 0 set = song 0, bit 0 clear = stop |

The title code sets 3. So the playlist `$00`, `$FF` plays song 0 for ever. **Code**. A run measured the restart of the tune 1154 frames after its start. **Observed** (run `a8-demo` of the naming analysis)

### 4.8 Decoder

```
read_stream(voice):
  for each byte b:
    if b == $FF: song ends
    if b < $80:  note(b)                    ; 0 = rest
    else switch (b >> 4) & 7:
      0, 7: length code = b & $0F
      1:    volume = b & $0F (applied with the next note of this voice)
      2:    b <= $A3: waveform | b <= $A6: articulation | $A7/$A8: tie
            $A9/$AA: ring | $AB: wave $51 | b >= $AC: length table = b & 1
      3:    instrument b & 7
      4:    pulse width = next 2 bytes (lo, hi)
      5:    filter preset b & 7, routing = next byte
      6:    tempo = next byte
```

## 5. The frequency table

[`note_freq_lo`](../src/music_frequency_table.asm#L9) [`$E200`](reference/modules/music_frequency_table.md#note_freq_lo) and [`note_freq_hi`](../src/music_frequency_table.asm#L22) [`$E254`](reference/modules/music_frequency_table.md#note_freq_hi) hold 84 SID frequency values. Index n is the note n semitones above B0. The music player uses index 0 as a rest. The effect players play index 0 as B0. **Code**

The values are tuned for an NTSC C64 (CPU clock 1022727 Hz). Hz = value * clock / 2^24.

| Index | Note | Value | NTSC Hz | PAL Hz | Exact Hz |
|---|---|---|---|---|---|
| 0 | B0 | `$01F8` | 30.7 | 29.6 | 30.9 |
| 1 | C1 | `$0216` | 32.6 | 31.4 | 32.7 |
| 13 | C2 | `$042D` | 65.2 | 62.8 | 65.4 |
| 24 | B2 | `$07E5` | 123.2 | 118.7 | 123.5 |
| 46 | A4 | `$1C21` | 439.0 | 422.9 | 440.0 |
| 58 | A5 | `$383D` | 877.6 | 845.5 | 880.0 |
| 83 | A#7 | `$EE54` | 3719.2 | 3583.0 | 3729.3 |

On NTSC the notes are 4 to 8 cents flat. A PAL C64 has a CPU clock of 985248 Hz, 64.6 cents lower. So on PAL every note is about 69 cents (2/3 of a semitone) flat. Music and effects keep their intervals. **Code** (computed from the table)

## 6. The title tune

Song 0 is the only tune. It plays on the title screen.

| Voice | Stream | Setup | Note bytes (with rests) | Content |
|---|---|---|---|---|
| 0 (bass) | [`music_title_voice0`](../src/music_songs.asm#L16) [`$E8D0-$E97C`](reference/modules/music_songs.md#music_title_voice0) | volume 12, pulse, instrument 3 legato, pulse width `$0802`, long lengths, tempo 2 | 81 | eighth-note ostinato B2 B3 F#3 G3, then E3 E4, C#4/B3 and F#3 figures |
| 1 | [`music_title_voice1`](../src/music_songs.asm#L40) [`$E97D-$EA30`](reference/modules/music_songs.md#music_title_voice1) | volume 15, pulse, instrument 5 normal, pulse width `$04CE` | 86 | 3 bars of rest, falling arpeggios G7 E7 B6 G6 E6 B5 G5 E5 in 32nds, a B5 D5 F#5 G5 F#5 D5 C#6 B5 figure, repeated F#4, a final F#7 .. C#5 arpeggio |
| 2 (melody) | [`music_title_voice2`](../src/music_songs.asm#L65) [`$EA31-$EAAC`](reference/modules/music_songs.md#music_title_voice2) | volume 15, pulse, instrument 0 then 5, normal, pulse width `$04CE` | 57 | B4 A4 B4, then E5 E5 E5 E5 D5 E5 in 16ths, F#4 E4 F#4 C#5 ..., B5 B4 |

- One tick = 2 frames. With the long table a whole note is 64 ticks: one bar of 4/4.
- Each voice reaches its end byte after 576 ticks: 9 bars, 1152 frames, 23.0 s on PAL (quarter note = 32 frames, about 94 beats per minute). **Code**
- Each voice ends with two rests and `$FF`. The first voice that starts its last rest reads `$FF` at once, so the last rest is never played. **Code**
- **Conclusion.** The tune is in B minor.
- The setup commands of the three voices all run before the first note. Each `$9x` command overwrites [`music_volume`](../src/music_player.asm#L28) and [`music_volume_voice`](../src/music_player.asm#L26). Only the last one (voice 2, volume 15) is applied: the coverage marks the [`music_apply_volume`](../src/music_player.asm#L266) calls of voices 0 and 1 (`$E4E9`, `$E523`) as not executed. So the volume 12 of voice 0 has no effect; the master volume is 15. **Observed**

### 6.1 Worked example: the first two bars

The first bytes of the three streams:

```
$E8D0 voice 0: 9C A2 B3 A6 C0 02 08 AD E0 02 A8 83 18 83 24 83 1F 83 20 ...
$E97D voice 1: 9F A2 B5 A4 C0 CE 04 A8 80 00 80 00 80 00 85 50 85 4D ...
$EA31 voice 2: 9F A2 B0 A4 C0 CE 04 A8 80 00 83 30 83 2E 82 30 81 00 ...
```

Voice 0, byte by byte:

| Bytes | Meaning |
|---|---|
| `9C` | volume 12 (overwritten later by voices 1 and 2) |
| `A2` | waveform pulse: control `$41` |
| `B3` | instrument 3: envelopes `$09 $00`, `$09 $00`, `$00 $70` |
| `A6` | articulation 2 (legato): AD = `$00`, SR = `$70` |
| `C0 02 08` | pulse width `$0802` |
| `AD` | long length table |
| `E0 02` | tempo 2 frames per tick |
| `A8` | tie off |
| `83` | length code 3: eighth = 8 ticks; legato: G = 7, R = 1 |
| `18` | note index `$18` = 24: B2 (`$07E5`) |
| `83 24` | eighth, index 36: B3 |
| `83 1F` | eighth, index 31: F#3 |
| `83 20` | eighth, index 32: G3 |

Voice 1 sets volume 15, pulse, instrument 5 (`$00 $F0`, sustain 15), articulation 0, pulse width `$04CE`, tie off. Then `80 00` three times: three whole rests (64 ticks each). Then `85 50`: a 32nd (2 ticks) of index 80, G7.

Voice 2 sets the same, with instrument 0 (`$11 $97`). Then `80 00` a whole rest, `83 30` eighth B4, `83 2E` eighth A4, `82 30` quarter B4, `81 00` half rest.

The first two bars (one row = one eighth = 8 ticks = 16 frames):

| Tick | Voice 0 | Voice 1 | Voice 2 |
|---|---|---|---|
| 0 | B2 | rest | rest |
| 8 | B3 | | |
| 16 | F#3 | | |
| 24 | G3 | | |
| 32 | B2 | | |
| 40 | B3 | | |
| 48 | F#3 | | |
| 56 | G3 | | |
| 64 | B2 | rest | B4 |
| 72 | B3 | | A4 |
| 80 | F#3 | | B4 (quarter) |
| 88 | G3 | | |
| 96 | B2 | | rest (half) |
| 104 | B3 | | |
| 112 | F#3 | | |
| 120 | G3 | | |

Timing of one eighth of voice 0: the counter is loaded with 7 and the end tick with `$FF`. After 7 ticks the counter is 0 and the gate goes off. One tick later the counter is `$FF` = the end tick, and B3 starts. **Code**

## 7. The effect players

Three copies of one player, one for each SID voice:

| Player | Address | State | Position | Timer | Stream pointer | SID registers | Command branch |
|---|---|---|---|---|---|---|---|
| voice 1 | [`sfx_voice1_update`](../src/sfx_voice1.asm#L19) [`$EB03`](reference/modules/sfx_voice1.md#sfx_voice1_update) | [`sfx_voice1_state`](../src/sfx_voice1.asm#L6) [`$EB00`](reference/modules/sfx_voice1.md#sfx_voice1_state) | [`sfx_voice1_pos`](../src/sfx_voice1.asm#L8) [`$EB01`](reference/modules/sfx_voice1.md#sfx_voice1_pos) | [`sfx_voice1_timer`](../src/sfx_voice1.asm#L10) [`$EB02`](reference/modules/sfx_voice1.md#sfx_voice1_timer) | [`sfx_voice1_stream`](../src/constants.asm#L124) [`$00F6`](reference/variables.md#sfx_voice1_stream) | `$D400-$D406` | [`sfx_voice1_cmd_branch`](../src/sfx_voice1.asm#L47) [`$EB38`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_branch) |
| voice 2 | [`sfx_voice2_update`](../src/sfx_voice2.asm#L19) [`$EF73`](reference/modules/sfx_voice2.md#sfx_voice2_update) | [`sfx_voice2_state`](../src/sfx_voice2.asm#L6) [`$EF70`](reference/modules/sfx_voice2.md#sfx_voice2_state) | [`sfx_voice2_pos`](../src/sfx_voice2.asm#L8) [`$EF71`](reference/modules/sfx_voice2.md#sfx_voice2_pos) | [`sfx_voice2_timer`](../src/sfx_voice2.asm#L10) [`$EF72`](reference/modules/sfx_voice2.md#sfx_voice2_timer) | [`sfx_voice2_stream`](../src/constants.asm#L125) [`$00F8`](reference/variables.md#sfx_voice2_stream) | `$D407-$D40D` | [`sfx_voice2_cmd_branch`](../src/sfx_voice2.asm#L47) [`$EFA8`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_branch) |
| voice 3 | [`sfx_voice3_update`](../src/sfx_voice3.asm#L19) [`$F073`](reference/modules/sfx_voice3.md#sfx_voice3_update) | [`sfx_voice3_state`](../src/sfx_voice3.asm#L6) [`$F070`](reference/modules/sfx_voice3.md#sfx_voice3_state) | [`sfx_voice3_pos`](../src/sfx_voice3.asm#L8) [`$F071`](reference/modules/sfx_voice3.md#sfx_voice3_pos) | [`sfx_voice3_timer`](../src/sfx_voice3.asm#L10) [`$F072`](reference/modules/sfx_voice3.md#sfx_voice3_timer) | [`sfx_voice3_stream`](../src/constants.asm#L126) [`$00FA`](reference/variables.md#sfx_voice3_stream) | `$D40E-$D414` | [`sfx_voice3_cmd_branch`](../src/sfx_voice3.asm#L47) [`$F0A8`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_branch) |

[`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) calls the three players at `$15AF`, `$15B2` and `$15B5`, each frame of the game screen (game and demo). [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start) and [`stop_all_sounds`](../src/sound_request.asm#L63) [`$255E`](reference/modules/sound_request.md#stop_all_sounds) clear the three state bytes. **Code**

[`sfx_voice1_update`](../src/sfx_voice1.asm#L19) [`$EB03`](reference/modules/sfx_voice1.md#sfx_voice1_update), each frame:

1. State 0: return.
2. State `$80` + n (a request): `ASL` gives 2n. [`sfx_voice1_stream`](../src/constants.asm#L124) = [`sfx_stream_table`](../src/sfx_data.asm#L6) [2n]. Timer = 1, state = 1, control register = 0 (gate off), position = 0.
3. [`sfx_voice1_tick`](../src/sfx_voice1.asm#L38) [`$EB26`](reference/modules/sfx_voice1.md#sfx_voice1_tick): decrement the timer. When it is not 0, return.
4. Read the command byte at the position. Store [`sfx_cmd_offsets`](../src/sfx_data.asm#L13) [command] into the branch offset [`sfx_voice1_cmd_offset`](../src/sfx_voice1.asm#L48) [`$EB39`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_offset). The `BCC` at [`sfx_voice1_cmd_branch`](../src/sfx_voice1.asm#L47) [`$EB38`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_branch) jumps into [`sfx_voice1_cmd_jumps`](../src/sfx_voice1.asm#L52) [`$EB3A`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_jumps).
5. The handler reads the arguments, writes the SID, sets the timer to the duration and stores the new position.

So the first command of an effect runs in the frame in which the player sees the request. A new request on a busy voice restarts that voice with the new effect. **Code**

### 7.1 The state machine of an effect player

~~~mermaid
stateDiagram-v2
  state "Idle (0)" as Idle
  state "Request ($80+n)" as Req
  state "Playing (1)" as Play
  [*] --> Idle
  Idle --> Req: play_sound $2509
  Play --> Req: play_sound replaces the effect
  Req --> Play: next frame, stream from sfx_stream_table
  Play --> Play: timer 0, next command
  Play --> Idle: command 0
  Play --> Idle: stop_all_sounds $255E
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Idle `$00` | [`play_sound`](../src/sound_request.asm#L12) chooses this voice | Request `$80`+n | [`play_sound_slot1`](../src/sound_request.asm#L17) [`$2513`](reference/modules/sound_request.md#play_sound_slot1) (voices 2, 3: [`play_sound_slot2`](../src/sound_request.asm#L28) [`$2526`](reference/modules/sound_request.md#play_sound_slot2), [`play_sound_slot3`](../src/sound_request.asm#L39) [`$2539`](reference/modules/sound_request.md#play_sound_slot3)) |
| Request `$80`+n | the next frame | Playing `$01` | [`sfx_voice1_check_request`](../src/sfx_voice1.asm#L24) [`$EB09`](reference/modules/sfx_voice1.md#sfx_voice1_check_request) |
| Playing `$01` | the timer reaches 0 | Playing `$01` (next command) | [`sfx_voice1_tick`](../src/sfx_voice1.asm#L38) [`$EB26`](reference/modules/sfx_voice1.md#sfx_voice1_tick) |
| Playing `$01` | command 0 | Idle `$00` | [`sfx_voice1_cmd_end`](../src/sfx_voice1.asm#L95) [`$EB82`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_end) |
| Playing `$01` | [`play_sound`](../src/sound_request.asm#L12) replaces the effect (all voices busy, priority not lower) | Request `$80`+n | [`play_sound_by_priority`](../src/sound_request.asm#L48) [`$2547`](reference/modules/sound_request.md#play_sound_by_priority) |
| any | [`stop_all_sounds`](../src/sound_request.asm#L63) | Idle `$00` | [`stop_all_sounds`](../src/sound_request.asm#L63) [`$255E`](reference/modules/sound_request.md#stop_all_sounds) |

## 8. The effect stream format

### 8.1 Where the data is

[`sfx_stream_table`](../src/sfx_data.asm#L6) [`$EBE5`](reference/modules/sfx_data.md#sfx_stream_table) holds the stream address of each effect 0-14 (the entries are in [the table reference](reference/tables.md#sfx_stream_table)). The streams are at `$EC31-$EE82`.

### 8.2 Byte layout

Each command is a command byte 0-7 and its arguments. The duration is in frames (0 = 256). The note is an index into `note_freq_lo/hi`.

| Command | Arguments | Action | Handler (voice 1) |
|---|---|---|---|
| 0 | - | end: frequency 0, state 0, position 0; the gate stays as it is | [`sfx_voice1_cmd_end`](../src/sfx_voice1.asm#L95) [`$EB82`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_end) |
| 1 | duration, note | timer = duration, frequency of the note | [`sfx_voice1_cmd_note`](../src/sfx_voice1.asm#L113) [`$EBA2`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note) |
| 2 | duration, note, control | + control register | [`sfx_voice1_cmd_note_control`](../src/sfx_voice1.asm#L118) [`$EBA9`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_control) |
| 3 | duration, note, ADSR index, control | + AD/SR = [`sfx_adsr_table`](../src/sfx_data.asm#L18) [i], [i+1] | [`sfx_voice1_cmd_note_adsr_control`](../src/sfx_voice1.asm#L124) [`$EBB3`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_adsr_control) |
| 4 | duration, note, ADSR index, pulse index, control | + pulse width = [`sfx_pulse_table`](../src/sfx_data.asm#L25) [p] (word) | [`sfx_voice1_cmd_note_adsr_pulse_control`](../src/sfx_voice1.asm#L131) [`$EBC0`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_adsr_pulse_control) |
| 5, 6 | duration, note, pulse index, control | note, pulse width and control (one handler) | [`sfx_voice1_cmd_note_pulse_control`](../src/sfx_voice1.asm#L139) [`$EBD0`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_pulse_control) |
| 7 | control | control only; the timer is not set, so the next command runs 256 frames later | [`sfx_voice1_cmd_control`](../src/sfx_voice1.asm#L147) [`$EBDD`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_control) |

No stream uses commands 5 and 7 (the coverage marks their table entries as not executed). Command 6 is used. **Observed**

[`sfx_adsr_table`](../src/sfx_data.asm#L18) [`$EC11`](reference/modules/sfx_data.md#sfx_adsr_table), even index:

| Index | AD | SR | Used by effects |
|---|---|---|---|
| 0 | `$11` | `$97` | 2, 4, 5, 7, 11, 12, 14 |
| 2 | `$00` | `$F0` | 0, 6, 8, 10 |
| 4 | `$89` | `$00` | 1 |
| 6 | `$09` | `$40` | 3 |
| 8 | `$08` | `$00` | 10 |
| 10 | `$0C` | `$07` | 13 (reads the first bytes of [`sfx_pulse_table`](../src/sfx_data.asm#L25)) |
| 12 | `$02` | `$08` | 9 (reads [`sfx_pulse_table+2`](../src/sfx_data.asm#L25) [`$EC1D`](reference/modules/sfx_data.md#sfx_pulse_table)) |

[`sfx_pulse_table`](../src/sfx_data.asm#L25) [`$EC1B`](reference/modules/sfx_data.md#sfx_pulse_table), even index: 0 `$070C`, 2 `$0802`, 4 `$04CE`, 6 `$019A`, 8 `$0334`, 10 `$01EC`, 12 `$011F`, 14 `$00CD`, 16 `$0052`, 18 `$007B`, 20 `$0668`.

### 8.3 Decoder

```
on request n:  ptr = sfx_stream_table[n]; pos = 0; timer = 1; state = 1; ctrl = 0
each frame:    if state == 0: return
               timer -= 1; if timer != 0: return
               c = ptr[pos]
               case c of
                 0: freq = 0; state = 0; pos = 0
                 1: timer, note = next 2
                 2: timer, note, ctrl = next 3
                 3: timer, note, adsr, ctrl = next 4
                 4: timer, note, adsr, pulse, ctrl = next 5
                 5, 6: timer, note, pulse, ctrl = next 4
                 7: ctrl = next 1               ; timer stays 0
```

### 8.4 Worked example: effect 1

[`sfx_yamo_arrives_stream`](../src/sfx_data.asm#L39) [`$EC37`](reference/modules/sfx_data.md#sfx_yamo_arrives_stream): `04 08 0B 04 00 41  01 10 0D  01 04 0C  01 04 0B  00`.

| Bytes | Command | Decoded | Frames |
|---|---|---|---|
| `04 08 0B 04 00 41` | 4 | 8 frames, index 11 = A#1, AD/SR `$89`/`$00`, pulse width `$070C`, control `$41` (pulse, gate on) | 8 |
| `01 10 0D` | 1 | 16 frames, index 13 = C2 | 16 |
| `01 04 0C` | 1 | 4 frames, B1 | 4 |
| `01 04 0B` | 1 | 4 frames, A#1 | 4 |
| `00` | 0 | end: frequency 0, the voice is idle | - |

The effect lasts 32 frames. AD `$89` is attack 8 (100 ms) and decay 9 (750 ms); SR `$00` is sustain 0. So the pulse fades during the 32 frames. **Code**

## 9. Sound requests and priorities

[`play_sound`](../src/sound_request.asm#L12) [`$2509`](reference/modules/sound_request.md#play_sound), input Y = `$80` + n:

1. Write `$15` to [`SIGVOL`](../src/constants.asm#L271) [`$D418`](reference/variables.md#SIGVOL): volume 5 and the low-pass mode bit. No voice is routed to the filter: [`stop_all_sounds`](../src/sound_request.asm#L63) writes 0 to [`RESON`](../src/constants.asm#L270) [`$D417`](reference/variables.md#RESON).
2. When [`sfx_voice1_state`](../src/sfx_voice1.asm#L6) is 0: store Y there, and [`sound_priority_table`](../src/sound_request.asm#L76) [Y AND `$0F`] in [`voice1_sound_priority`](../src/sound_request.asm#L80). Return.
3. Else the same with voice 2, then with voice 3.
4. All three busy ([`play_sound_by_priority`](../src/sound_request.asm#L48) [`$2547`](reference/modules/sound_request.md#play_sound_by_priority)): p = the priority of the new effect. When p >= [`voice1_sound_priority`](../src/sound_request.asm#L80), take voice 1; else when p >= [`voice2_sound_priority`](../src/sound_request.asm#L82), voice 2; else when p >= [`voice3_sound_priority`](../src/sound_request.asm#L84), voice 3; else drop the request.

The request stays in the state byte until the player sees it in the next frame. **Code**

[`stop_all_sounds`](../src/sound_request.asm#L63) [`$255E`](reference/modules/sound_request.md#stop_all_sounds) writes 0 to the three state bytes and to `$D400-$D420` (33 bytes; `$D41D-$D41F` are unused SID addresses and `$D420` mirrors `$D400`). **Code**

[`sound_priority_table`](../src/sound_request.asm#L76) [`$2572`](reference/modules/sound_request.md#sound_priority_table) (a higher value wins):

| Effect | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Priority | 11 | 12 | 10 | 0 | 8 | 7 | 9 | 6 | 0 | 0 | 1 | 2 | 3 | 4 | 5 |

**Conclusion.** The fight sounds and the footstep have the highest priorities. When the three voices are busy, a footstep (priority 11) can replace a lantern, hazard or trap effect, but those effects cannot replace a footstep.

## 10. Catalogue of the effects

Frames = the sum of the durations of the stream. The evidence column tells how the request was seen: **Observed** means that a trace of [`play_sound`](../src/sound_request.asm#L12) in a run had this Y value, or that the coverage of the runs marks the requesting code as executed.

| n | Request | Stream | Frames | Priority | Sound | Requested by | Evidence |
|---|---|---|---|---|---|---|---|
| 0 | `$80` | [`sfx_footstep_stream`](../src/sfx_data.asm#L35) [`$EC31`](reference/modules/sfx_data.md#sfx_footstep_stream) | 1 | 11 | one frame of noise at C6 | [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound), from the moves of every actor: [`actor_action_step`](../src/actor_step.asm#L21) [`$1DDC`](../src/actor_step.asm#L243), [`actor_move_up`](../src/actor_step.asm#L258) [`$1E29`](../src/actor_step.asm#L290), [`actor_move_down`](../src/actor_step.asm#L300) [`$1E63`](../src/actor_step.asm#L325), [`actor_move_left`](../src/actor_step.asm#L349) [`$1EA4`](../src/actor_step.asm#L365), [`actor_enemy_down`](../src/actor_step.asm#L420) `$1F46`/`$1F5C`, [`actor_continue_action`](../src/actor_timed_actions.asm#L14) [`$21EB`](../src/actor_timed_actions.asm#L277). Every 3 frames while Bruce walks. | Observed |
| 1 | `$81` | [`sfx_yamo_arrives_stream`](../src/sfx_data.asm#L39) [`$EC37`](reference/modules/sfx_data.md#sfx_yamo_arrives_stream) | 32 | 12 | low pulse A#1 C2 B1 A#1 | [`yamo_start_pose`](../src/actor_timed_actions.asm#L326) [`$2244`](reference/modules/actor_timed_actions.md#yamo_start_pose) (Yamo takes pose state `$12`); [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3656`](../src/room_frames_0_7.asm#L21) and [`room02_frame_mouth`](../src/room_frames_0_7.asm#L106) [`$36DF`](../src/room_frames_0_7.asm#L114) (the statue mouth of rooms 0 and 2) | Observed |
| 2 | `$82` | [`sfx_enemy_enters_stream`](../src/sfx_data.asm#L44) [`$EC47`](reference/modules/sfx_data.md#sfx_enemy_enters_stream) | 12 | 10 | fast high pulse notes | [`play_enemy_spawn_sound`](../src/game_setup.asm#L225) [`$10B5`](reference/modules/game_setup.md#play_enemy_spawn_sound), from [`spawn_yamo`](../src/actor_spawn.asm#L203) [`$0CD5`](reference/modules/actor_spawn.md#spawn_yamo) and [`spawn_ninja`](../src/actor_spawn.asm#L398) [`$0DF8`](reference/modules/actor_spawn.md#spawn_ninja) | Observed |
| 3 | `$83` | [`sfx_unused_3_stream`](../src/sfx_data.asm#L53) [`$EC7A`](reference/modules/sfx_data.md#sfx_unused_3_stream) | 6 | 0 | noise chirp C7 C8 B7 C8 C5 C2 | no code | Code |
| 4 | `$84` | [`sfx_kick_stream`](../src/sfx_data.asm#L59) [`$EC90`](reference/modules/sfx_data.md#sfx_kick_stream) | 21 | 8 | rising noise sweep | flying kick states `$0C`/`$0D` at step `$0C`: [`act_check_kick_left`](../src/actor_timed_actions.asm#L48) [`$205A`](../src/actor_timed_actions.asm#L60), [`act_check_kick_right`](../src/actor_timed_actions.asm#L85) [`$209F`](../src/actor_timed_actions.asm#L96) | Observed |
| 5 | `$85` | [`sfx_swing_stream`](../src/sfx_data.asm#L68) [`$ECBE`](reference/modules/sfx_data.md#sfx_swing_stream) | 6 | 7 | short rising noise | Ninja strike state `$16` at step 12: [`act_strike_phase`](../src/actor_timed_actions.asm#L419) [`$22D2`](../src/actor_timed_actions.asm#L424). The request in [`act_check_punch`](../src/actor_timed_actions.asm#L349) [`$227C`](../src/actor_timed_actions.asm#L363) (punch at step 8) never runs: a punch starts at step 4. | Observed (`$22D2`), Code (`$227C`) |
| 6 | `$86` | [`sfx_impact_stream`](../src/sfx_data.asm#L75) [`$ECD8`](reference/modules/sfx_data.md#sfx_impact_stream) | 5 | 9 | falling noise C8 to C1 | [`play_hit_sound`](../src/actor_helpers.asm#L159) [`$2E29`](reference/modules/actor_helpers.md#play_hit_sound): hits in [`check_fight_pair_done`](../src/fight_hits.asm#L121) `$2AC0`/`$2AE6`/`$2B2C`; fireball start [`launch_fireball0`](../src/wizard_fireballs.asm#L141) [`$421D`](../src/wizard_fireballs.asm#L153), [`launch_fireball1`](../src/wizard_fireballs.asm#L156) [`$423C`](../src/wizard_fireballs.asm#L168) (room 18) | Observed |
| 7 | `$87` | [`sfx_bokken_hit_stream`](../src/sfx_data.asm#L81) [`$ECEC`](reference/modules/sfx_data.md#sfx_bokken_hit_stream) | 8 | 6 | rising triangle arpeggio C4 to G7 | the Ninja's bokken hits: [`check_fight_strike`](../src/fight_hits.asm#L126) [`$2A93`](../src/fight_hits.asm#L140) | Observed |
| 8 | `$88` | [`sfx_unused_8_stream`](../src/sfx_data.asm#L88) [`$ED0E`](reference/modules/sfx_data.md#sfx_unused_8_stream) | 20 | 0 | falling gated pulse arpeggio F#7 to C#5 | no code | Code |
| 9 | `$89` | [`sfx_runner_step_stream`](../src/sfx_data.asm#L101) [`$ED59`](reference/modules/sfx_data.md#sfx_runner_step_stream) | 1 | 0 | one pulse note C6 | [`play_runner_sound`](../src/room_hazard_draw.asm#L32) [`$4078`](reference/modules/room_hazard_draw.md#play_runner_sound), from [`draw_runner_step`](../src/room_hazard_draw.asm#L9) [`$404E`](reference/modules/room_hazard_draw.md#draw_runner_step) and [`draw_runner_step_alt`](../src/room_hazard_draw.asm#L21) [`$4063`](reference/modules/room_hazard_draw.md#draw_runner_step_alt): each step of a runner hazard (rooms 7, 9, 13, 17) | Observed |
| 10 | `$8A` | [`sfx_passage_opens_stream`](../src/sfx_data.asm#L107) [`$ED60`](reference/modules/sfx_data.md#sfx_passage_opens_stream) | 79 | 1 | 16 silent frames, a low wobble, then B6 for 47 frames | [`play_open_sound`](../src/wizard_fireballs.asm#L183) [`$424F`](reference/modules/wizard_fireballs.md#play_open_sound), from [`open_passage`](../src/passage_open.asm#L42) [`$3A8A`](reference/modules/passage_open.md#open_passage), [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark), [`room01_frame`](../src/room_frames_0_7.asm#L42) [`$3698`](../src/room_frames_0_7.asm#L58), [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36BA`](../src/room_frames_0_7.asm#L97), [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3719`](../src/room_frames_0_7.asm#L148), [`room04_frame`](../src/room_frames_0_7.asm#L195) `$379A`/`$37F7`, [`room09_frame`](../src/room_frames_8_11.asm#L149) [`$3BFA`](../src/room_frames_8_11.asm#L187), [`room15_frame`](../src/room_frames_12_17.asm#L106) `$3F05`/`$3F2D`/`$3F54`, and [`frame_update_yamo_idle`](../src/frame_update.asm#L295) [`$1771`](../src/frame_update.asm#L322) (a player-controlled Yamo times out) | Observed (`$1771` not executed) |
| 11 | `$8B` | [`sfx_wizard_defeated_stream`](../src/sfx_data.asm#L116) [`$ED8E`](reference/modules/sfx_data.md#sfx_wizard_defeated_stream) | 14 | 2 | A7 alternating noise and pulse+triangle, then E4, A3 | [`room18_wizard_defeated_sound`](../src/wizard_room.asm#L180) [`$3E0B`](reference/modules/wizard_room.md#room18_wizard_defeated_sound): each step of the wizard defeat in room 18 | Observed |
| 12 | `$8C` | [`sfx_hazard_death_stream`](../src/sfx_data.asm#L128) [`$EDC8`](reference/modules/sfx_data.md#sfx_hazard_death_stream) | 14 | 3 | pulse C#4/C4 with pulse-width steps, then falling | [`touch_deadly_tile`](../src/touch_effects.asm#L75) [`$3059`](../src/touch_effects.asm#L87): an actor touches a deadly tile; then [`set_actor_hazard_death`](../src/room_hazard_draw.asm#L37) [`$407D`](reference/modules/room_hazard_draw.md#set_actor_hazard_death) (Bruce) or [`remove_actor`](../src/touch_effects.asm#L38) [`$3001`](reference/modules/touch_effects.md#remove_actor) (an enemy) | Observed |
| 13 | `$8D` | [`sfx_trap_burst_stream`](../src/sfx_data.asm#L139) [`$EE07`](reference/modules/sfx_data.md#sfx_trap_burst_stream) | 103 | 4 | noise burst, then 96 frames of low noise | [`play_burst_sound`](../src/room_misc_support.asm#L122) [`$32CC`](reference/modules/room_misc_support.md#play_burst_sound), from [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$323D`](../src/room_misc_support.asm#L46): the timer of a burst trap (started by [`touch_trap_tile`](../src/touch_effects.asm#L101) [`$306B`](reference/modules/touch_effects.md#touch_trap_tile)) reaches 8 | Observed |
| 14 | `$8E` | [`sfx_lantern_stream`](../src/sfx_data.asm#L146) [`$EE19`](reference/modules/sfx_data.md#sfx_lantern_stream) | 26 | 5 | sawtooth arpeggios B minor, A minor, B minor | [`collect_lantern`](../src/background_touch.asm#L142) [`$2F36`](../src/background_touch.asm#L172) (Bruce takes a lantern); [`collect_room16_bonus_check_y`](../src/touch_effects.asm#L14) [`$2FEC`](../src/touch_effects.asm#L23) (the room 16 extra fall) | Observed (`$2F36`), Code (`$2FEC`) |

The runs that traced [`play_sound`](../src/sound_request.asm#L12) are the runs `a8-sfx1`, `a8-demo` and `a8-rooms` of the naming analysis (room 0 with the joystick, the attract demo, and each room snapshot). They saw the requests `$80`, `$81`, `$82`, `$84`, `$85`, `$86`, `$87`, `$89`, `$8C`, `$8D` and `$8E`.

The bytes `$EE83-$EED5` are an effect stream that no table entry points to. `$EED6-$EF3F` is a copy of [`sfx_lantern_stream`](../src/sfx_data.asm#L146). **Code**

## 11. Findings

| Finding | Evidence |
|---|---|
| The music player is a third-party driver: MicroPearl, John A. Fitzpatrick, 1983 ([`music_player_credit`](../src/music_player.asm#L38) [`$E315`](reference/modules/music_player.md#music_player_credit)). | Code |
| The frequency table is tuned for NTSC. On the PAL game every note is about 2/3 of a semitone flat. | Code |
| The volume command of voice 0 of the title tune has no effect; the master volume is 15. | Observed (coverage) |
| Playlist transpose entries have no effect: [`music_reset_state`](../src/music_player.asm#L101) clears [`music_transpose`](../src/music_voice_state.asm#L7). | Code |
| [`music_song_ended`](../src/music_player.asm#L16) [`$E30B`](reference/modules/music_player.md#music_song_ended) is written but never read. | Code |
| Song 1 points into the effect player; no code selects it. | Code |
| Effects 3 and 8 are never requested. Effect commands 5 and 7 are not used. | Code |
| [`sfx_adsr_table`](../src/sfx_data.asm#L18) index 10 and 12 read into [`sfx_pulse_table`](../src/sfx_data.asm#L25); effects 9 and 13 use them. | Code |
| The punch swing sound at step 8 never plays, because a punch starts with timer 4. | Code, Observed (not executed) |

## 12. Still open

- The routing byte of the filter command is not used by the title tune. Its bit layout (`$D417` bits 0-3) follows from the SID; no run checked it.
- [`room02_frame_mouth`](../src/room_frames_0_7.asm#L106) and [`room00_frame`](../src/room_frames_0_7.asm#L9) request effect 1 with the statue mouth animation. A run with a trace of `$3656` and `$36DF` in rooms 0 and 2 would confirm the timing.
- The second request of effect 14 ([`collect_room16_bonus_check_y`](../src/touch_effects.asm#L14) [`$2FEC`](../src/touch_effects.asm#L23)) was not reached. A run in room 16 that walks over the bonus tile can show it.
