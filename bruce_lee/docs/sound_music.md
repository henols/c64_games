# Bruce Lee: sound and music

The title screen plays a tune. In the game, short sound effects tell the player what happens on the screen. Examples are a footstep of Bruce, a kick, the arrival of the Yamo, a lantern that Bruce takes and a passage that opens. Two sound drivers make these sounds. A third-party music player plays the title tune from three note streams, one for each SID voice. Three small effect players, one for each SID voice, play the effects of the game and of the attract demo. Thus up to three effects sound at the same time, and a priority table decides which effect stops when all three voices are busy. The two drivers never run at the same time. The title interrupt calls only the music player, and the game interrupt calls only the effect players.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one run of the raster interrupt that calls the driver: `irq_title_frame` for the music, `irq_game_bottom` (through `frame_update`) for the effects. The game runs on a PAL C64: 50 frames per second.
- A *tick* is the time step of the music player: `music_tempo` frames.
- A *voice* of the music player has a number from 0 to 2. Music voice 0 is SID voice 1, music voice 1 is SID voice 2, and music voice 2 is SID voice 3.
- A *note index* is an index into the frequency table `note_freq_lo` / `note_freq_hi`. Index n is the note n semitones above B0. Note names use the octave numbers of scientific pitch (A4 = 440 Hz).
- The *request value* `$80` + n starts *effect* n (0-14).
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  subgraph TITLE["Title screen"]
    T1["Show the title (show_title_screen)"] -->|"first title, then every 5th, unless S"| T2["Start the title tune (music_api_start)"]
    T3["Title interrupt (irq_title_frame)"] -->|"each frame"| T4["Play one frame of the tune (music_play_frame)"]
  end
  subgraph GAME["Game and demo"]
    G1["Game code: a step, a kick, a lantern"] -->|"Y = $80+n"| G2["Choose a voice (play_sound)"]
    G2 --> G3["Request in the state byte of the voice"]
    G4["Game interrupt (frame_update)"] -->|"each frame"| G5["Three effect players, one per SID voice"]
    G3 -.-> G5
  end
~~~

The title tune and the effects never share the SID. The title screen starts the tune, and the title interrupt plays it. Each exit from the title stops the tune. In the game and in the attract demo, the code that makes a sound only writes a request for a free voice. The game interrupt then plays the requests.

1. On the title screen, [`show_title_screen` `$0584`](../src/game/title_demo_start.asm#L83) starts the title tune with [`music_api_start` `$E003`](../src/music/music_player_state.asm#L10). It starts the tune on the first title and then on every fifth title (the count is `title_music_skip_count`). It does not start the tune when the S key disabled it. **Code**
2. The title interrupt [`irq_title_frame` `$152C`](../src/irq/screen_raster_irqs.asm#L81) calls [`music_api_play` `$E006`](../src/music/music_player_state.asm#L13) each frame. **Code**
3. `restart_to_title`, `start_attract_demo` and `show_title_screen` stop the tune with [`music_api_stop` `$E000`](../src/music/music_player_state.asm#L7). **Code**
4. In the game and in the demo, the game code calls [`play_sound` `$2509`](../src/sfx/sound_request.asm#L12) with Y = `$80` + effect number. `play_sound` writes the request into the state byte of a free effect player. **Code**
5. [`frame_update` `$15A8`](../src/game/frame_update.asm#L20) calls the three effect players each frame, from [`sfx_voice1_update` `$EB03`](../src/sfx/sfx_voice1.asm#L19) for SID voice 1 to `sfx_voice3_update` for SID voice 3. A player that sees a request starts the effect stream. **Code**
6. [`stop_all_sounds` `$255E`](../src/sfx/sound_request.asm#L63) frees the three effect players and writes 0 to the SID registers. The title screen, the room drawing (`draw_room`), the player screen, `init_game_variables` and `lose_fall` call it. **Code**

**The S key only switches the title tune.** In the game, the S key toggles [`title_music_off` `$1385`](../src/room/room_enemy_tables.asm#L118) and sets `title_music_skip_count` to 0 ([`handle_game_keys_check_s` `$1B4A`](../src/game/status_and_keys.asm#L73)). The only code that reads `title_music_off` is the tune check of the title screen, [`title_music_check` `$06BD`](../src/game/title_demo_start.asm#L228). `play_sound` and the effect players never read it, so the sound effects of the game always play. S only decides whether the next title screen plays the tune. Because S also clears the count, the next title plays the tune when the tune is on. **Code**

## The music player

The music player plays one song. A song is three streams of notes and commands, one for each voice, and the three voices use one tempo. Each frame, the player decrements the tick counter. At each tick, each voice decrements the counter of its note. The voice clears the gate bit when the release must start. At the end of the note, the voice reads the next note and the commands before it. The game uses only one song, the title tune.

**The music player is a third-party driver.** The player has a credit text at [`music_player_credit` `$E315`](../src/music/music_player.asm#L50): " MICROPEARL MUSIC PLAYER  COPYRIGHT 1983 JOHN A. FITZPATRICK ". Nothing reads the text. **Code**

The game calls the player through three `JMP` at `$E000-$E008`: stop, start the playlist, play one frame. A second set of three `JMP` at [`music_jump_stop` `$E300`](../src/music/music_player.asm#L7) is the inner interface: stop, start a song, start the playlist. The playlist and the end actions start a song through it.

| Entry | Goes to | Called by |
|---|---|---|
| `music_api_stop` | `music_jump_stop`, `music_stop`, `music_silence` | `restart_to_title`, `start_attract_demo`, `show_title_screen` |
| `music_api_start` | `music_jump_start_playlist`, `music_start_playlist` | `show_title_screen` |
| `music_api_play` | `music_play_frame` | `irq_title_frame`, each frame of the title and game over screens |
| `music_jump_start_song` | `music_init_song` | `music_start_song_x` (the playlist and the end actions) |

`start_attract_demo` and `show_title_screen` set `music_stop_request` to 1 before they call `music_api_stop`. **Code**

### The state of the player

A few global bytes control the play:

| Name | Meaning |
|---|---|
| `music_song` | the song that plays (0 = the title tune) |
| `music_playing` | 1 = the song plays, 0 = the player stopped or prepares the song |
| `music_stop_request` | nonzero: `music_play_frame` silences the SID and stops |
| `music_end_marker` | `$FF` when a voice read its end byte |
| `music_song_ended` | 1 when a voice reads its end byte `$FF` |
| `music_end_action` | what happens at the end of a song (see "Playlist and end actions") |
| `music_tempo` / `music_tempo_counter` | frames in a tick (command `$Ex`) / frames left in the current tick |
| `music_volume` / `music_volume_voice` | master volume (command `$9x`) / voice + 1 whose next note writes `$D418` and `$D417`. 0 = nothing pending. |
| `music_filter_mode` / `music_resonance` | the filter mode bits for the high nibble of `SIGVOL`, and the value for `RESON` (command `$Dx`) |
| `music_long_lengths` | 1 = the second row of `music_length_table` (commands `$AC-$AF`) |
| `music_lookahead` | the stream byte after the byte that the player read last |

**`music_song_ended` is never read.** The player writes it when a voice reads its end byte, but no code reads it. The player uses `music_end_marker`. **Code**

Each voice has its own state at `$E100-$E12D`. The state is a set of arrays of 3 bytes, with the voice as the index:

| Name | Meaning | Reset value |
|---|---|---|
| `music_transpose` | added to each note index (1 byte, all voices) | 0 |
| `music_voice_tie` | 1 = tied: no new envelope, no gate off | 0 |
| `music_voice_ticks` | tick counter of the current note | 0 |
| `music_voice_end_tick` | counter value that ends the note: minus the release ticks | `$FF` |
| `music_voice_gate_ticks` | gate ticks of the next note | 7 |
| `music_voice_end_reload` | end tick of the next note | `$FF` |
| `music_voice_attack_decay` | SID AD value | `$11` |
| `music_voice_sustain_release` | SID SR value | `$97` |
| `music_voice_control` | SID control value (waveform, gate bit 0 = 1) | `$21` |
| `music_voice_articulation` | 0 normal, 1 staccato, 2 legato | 0 |
| `music_envelopes` | 6 bytes per voice: AD/SR of articulation 0, 1, 2 of the current instrument | instrument 0 |

[`music_reset_state` `$E3A8`](../src/music/music_player_e38c.asm#L23) copies the 46 bytes of [`music_voice_init` `$E2A8`](../src/music/music_frequency_table.asm#L37) over `$E100-$E12D` before each song. **Code**

### Starting the title tune

Before it starts the tune, `show_title_screen` writes a playlist of one song. It sets `music_end_action` = 3, `music_playlist` = `$00` (song 0) and `music_playlist_end` = `$FF` (end of the list). Thus the title tune plays again and again while the title screen shows. **Code**

[`music_start_playlist` `$E479`](../src/music/music_player_e38c.asm#L189) is the routine behind the start entry. It does these steps:

1. Y = 1 (the "loop" bit). `music_playlist_pos` = `music_playlist_start`.
2. `music_playlist_read` reads the playlist entry. Entry `$00` gives song 0. `music_playlist_pos` increments.
3. `music_start_song_x` stores the song in `music_song`. It jumps through `music_jump_start_song` to [`music_init_song` `$E352`](../src/music/music_player.asm#L55).
4. `music_init_song` clears `music_playing`, calls [`music_setup_song` `$E38C`](../src/music/music_player_e38c.asm#L7) and sets `music_playing` = 1.

`music_setup_song` prepares the three voices:

1. `music_set_voice_pointers` copies the three stream addresses of the song from `music_song_table` into the operands of the fetch routines `music_fetch_voice0`, `music_fetch_voice1` and `music_fetch_voice2`. Each fetch routine is `LDA abs` / `RTS`. A song number above `music_last_song` (1) becomes `music_last_song`.
2. `music_reset_state` does these steps:
   1. Set the filter mode and the resonance to 0.
   2. Copy the voice state from `music_voice_init`.
   3. Set `music_tempo_counter` = `music_tempo`.
   4. `music_clear_and_silence` writes 0 to `$D400-$D417` and to the player flags.
3. For each voice: `music_lookahead` = `$FF`. Then `music_voice_commands` reads the commands before the first note of the voice. **Code**

[`music_read_byte` `$E3EA`](../src/music/music_player_e38c.asm#L89) reads a byte of the current voice with its fetch routine. It increments the operand of the fetch routine (self-modified code). Then it reads the next byte into `music_lookahead`. **Code**

### One frame of the music

[`music_play_frame` `$E49E`](../src/music/music_player_e38c.asm#L215) runs once per frame:

1. When `music_stop_request` is nonzero: `music_silence`, stop.
2. When `music_playing` is 0: return.
3. When `music_end_marker` = `$FF` and `music_end_action` is 0: silence and stop.
4. When `music_end_marker` = `$FF` and `music_end_action` is not 0: [`music_song_end_action` `$E438`](../src/music/music_player_e38c.asm#L141) chooses the next song (see "Playlist and end actions"). The routine then starts again.
5. Decrement `music_tempo_counter`. When it is not 0, return. Else reload it from `music_tempo`: a tick starts.
6. Do these steps for voice 0, 1 and 2. The code has three copies. The copies for voices 1 and 2 start at `music_voice1_update` and `music_voice2_update`.
   1. Decrement `music_voice_ticks`.
   2. When the counter is 0 and the voice is not tied: write `music_voice_control` AND `$FE` to the control register of the voice. The gate goes off and the release starts.
   3. When the counter is negative and equals `music_voice_end_tick`: the note is at its end. Reload the counter from `music_voice_gate_ticks` and the end tick from `music_voice_end_reload`. When `music_volume_voice` = voice + 1, call `music_apply_volume`. Call `music_voice_start_note`.

[`music_voice_start_note` `$E578`](../src/music/music_player_e38c.asm#L322) starts the next note:

1. Read the note byte.
2. Note 0 is a rest: write 0 to the frequency. The gate and the envelope stay as they are.
3. Else frequency = `note_freq_lo/hi` [note + `music_transpose`]. When the voice is not tied, write AD, SR and control (gate on) of the voice to the SID.
4. [`music_voice_commands` `$E5BB`](../src/music/music_player_e38c.asm#L353) reads the command bytes that follow, until the next note byte. Thus the commands before a note apply to that note.

The command loop jumps to the handler through a branch. The loop writes the offset of the branch into the code:

```
music_voice_commands:
  while music_lookahead >= $80:
    c = read_byte()
    if c == $FF: music_end_marker = $FF; return
    group = (c >> 4) & 7
    branch offset = music_cmd_offsets[group]      ; self-modified BCC at music_cmd_branch
    goto music_cmd_jumps + offset                  ; each handler loops back here
```

`music_cmd_offsets` has 17 branch offsets. The 8 groups use 8 of them. **Code**

**Conclusion.** A note lasts gate ticks + release ticks. The gate is on for the gate ticks. The release ticks follow with the gate off. "Note lengths and articulation" gives the two numbers.

### The state machine of the player

The player stays stopped until the title screen starts it. It plays until a voice reads the end byte. Then the end action chooses the next song or stops the player.

~~~mermaid
stateDiagram-v2
  state "Stopped (music_playing 0)" as Stopped
  state "Playing (music_playing 1)" as Playing
  state "Song ended (music_end_marker $FF)" as Ended
  [*] --> Stopped
  Stopped --> Playing: music_api_start
  Playing --> Ended: a voice reads $FF
  Ended --> Playing: end action chooses a song
  Ended --> Stopped: end action 0 or end of list
  Playing --> Stopped: music_stop_request or music_api_stop
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Stopped | `music_api_start` | Playing | `music_start_playlist`, `music_init_song` |
| Playing | a voice reads the end byte `$FF` | Song ended | `music_voice_read_command` |
| Song ended | `music_end_action` chooses a song or a playlist entry | Playing | `music_song_end_action` |
| Song ended | `music_end_action` = 0, or end of the playlist with bit 0 clear, or after the last song with bit 0 clear | Stopped | `music_play_frame`, `music_silence` |
| Playing | `music_stop_request` nonzero | Stopped | `music_play_frame` |
| any | `music_api_stop` | Stopped | `music_stop` |

## The music stream format

A song is three streams, one for each voice. Each stream is a list of notes. The commands before a note set how that note and the notes after it sound. They set the length, the waveform, the envelope, the volume, the filter and the tempo.

### Where the data is

[`music_song_table` `$E8C0`](../src/music/music_songs.asm#L7) has 8 bytes per song: the stream address of voice 0, 1, 2 and an instrument table address. The player ignores the instrument table address and always uses `music_instruments`. Song 0 is the title tune. Its streams are [`music_title_voice0` `$E8D0`](../src/music/music_songs_e8d0.asm#L7), `music_title_voice1` at `$E97D` and `music_title_voice2` at `$EA31`. `music_read_byte` reads the streams through the self-modified fetch routines.

**Song 1 points into the effect player.** Song 1 ([`music_song1_voices` `$E8C8`](../src/leftovers/leftover_e8c8.asm#L8)) points to `$EAB3`, `$EB60` and `$EC14`. Only `$EAB3` is a stream. The other two addresses point into the effect player. No code selects song 1. **Code**

### The byte layout

A byte below `$80` is a note. A byte from `$80` is a command. Bits 4-6 of a command select the handler.

| Byte | Arguments | Meaning | Handler |
|---|---|---|---|
| `$00` | - | rest: frequency 0 for one note length | `music_voice_start_note` |
| `$01-$7F` | - | note index n (+ `music_transpose`): frequency from `note_freq_lo/hi` | `music_voice_set_freq` |
| `$80-$8F` | - | length code n = low nibble, for the notes that follow | `music_cmd_length` |
| `$90-$9F` | - | master volume n. The next note of this voice writes `$D418` = `music_filter_mode` OR n and `$D417` = `music_resonance`. | `music_cmd_volume` |
| `$A0-$A3` | - | waveform: triangle `$11`, sawtooth `$21`, pulse `$41`, noise `$81` (gate bit set), from `music_waveforms` | `music_cmd_voice_option` |
| `$A4-$A6` | - | articulation 0, 1, 2. Loads AD/SR of that articulation from the instrument of the voice. | `music_cmd_articulation` |
| `$A7` / `$A8` | - | tie on / tie off | `music_cmd_tie_or_ring` |
| `$A9` / `$AA` | - | ring modulation bit on / off | `music_cmd_ring_mod` |
| `$AB` | - | waveform `$51` (pulse + triangle) | `music_cmd_voice_option` |
| `$AC`, `$AE` / `$AD`, `$AF` | - | normal / long length table, for all voices | `music_cmd_length_set` |
| `$B0-$BF` | - | instrument n AND 7: copies its 6 envelope bytes into `music_envelopes` of the voice | `music_cmd_instrument` |
| `$C0-$CF` | lo, hi | pulse width of the voice, written at once | `music_cmd_pulse_width` |
| `$D0-$DF` | routing | filter preset n AND 7. Cutoff to `$D415`/`$D416` at once. Mode to `music_filter_mode`. Routing OR preset resonance to `music_resonance`. The next note of the voice writes `$D417`/`$D418`. | `music_cmd_filter` |
| `$E0-$EF` | t | tempo: t frames per tick | `music_cmd_tempo` |
| `$F0-$FE` | - | length code n, the same as `$8n` | `music_cmd_length` |
| `$FF` | - | end of the song. The first voice that reads it ends the song for all voices. | `music_voice_read_command` |

**Code** for each row. The title tune uses no ring modulation, no filter and no tie on. The coverage marks `music_cmd_ring_mod` and `music_cmd_filter` as not executed. **Observed**

### Note lengths and articulation

A length command sets the length of the notes that follow. [`music_note_length` `$E6B6`](../src/music/music_player_e38c.asm#L510) changes the length code into L ticks with `music_length_table`. The table has two rows of 16 bytes:

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

The length command uses the current articulation of the voice. The articulation divides L into gate ticks G and release ticks R (G + R = L):

| Articulation | Command | G (gate on) | R (gate off) |
|---|---|---|---|
| 0 normal | `$A4` | L - L/8 | L/8, at least 1 |
| 1 staccato | `$A5` | L/2 | L/2 |
| 2 legato | `$A6` | L - 1 | 1 |

[`music_cmd_length` `$E5FD`](../src/music/music_player_e38c.asm#L403) stores G in `music_voice_gate_ticks` and -R in `music_voice_end_reload`. **Code**

### Instruments

An instrument is a set of three envelopes, one for each articulation. [`music_instruments` `$E80A`](../src/music/music_data.asm#L8) holds 8 instruments of 8 bytes. The bytes are AD and SR for articulation 0, 1 and 2, and 2 unused bytes.

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

The instrument command `$Bn` only copies the 6 bytes into `music_envelopes`. The AD/SR values of the voice change with the next articulation command `$A4-$A6`. The SID receives them at the next note that is not tied. **Code**

### Filter presets

[`music_filter_presets` `$E84A`](../src/music/music_data.asm#L19) holds 8 presets of 4 bytes. The bytes are:

- cutoff low (`$D415`)
- cutoff high (`$D416`)
- resonance in the high nibble (`$D417`)
- filter mode (`$10` low pass, `$20` band pass, `$40` high pass)

The title tune uses none of the presets.

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

### Tempo

The command `$Ex` t sets `music_tempo` and `music_tempo_counter` to t. One tick is t frames. The title tune uses t = 2. **Code**

### Playlist and end actions

The playlist is a list of songs that play one after the other. It starts at [`music_playlist` `$E870`](../src/music/music_data_e870.asm#L6). `music_playlist_start` is the first index.

| Entry | Meaning |
|---|---|
| `$00-$3F` | play song n |
| `$40-$7F` | transpose = n AND `$3F`, then read the next entry |
| `$80-$FF` | end of the list |

**Playlist transpose entries have no effect.** `music_reset_state` clears `music_transpose` before the song starts. **Code**

[`music_end_action` `$E314`](../src/music/music_player.asm#L26) tells what happens at the end of a song:

| Value | At the end of a song |
|---|---|
| 0 | stop |
| bit 7 set | play song (value AND `$7F`) |
| bit 1 set | next playlist entry. At the end of the list: bit 0 set = start the list again, bit 0 clear = stop. |
| else | next song number. After `music_last_song`: bit 0 set = song 0, bit 0 clear = stop. |

The title code sets 3. Thus the playlist `$00`, `$FF` plays song 0 again and again. **Code**. A run measured the restart of the tune 1154 frames after its start. **Observed** (run `a8-demo` of the naming analysis)

### The decoder

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

"The title tune" below decodes the first bytes of the three streams.

## The frequency table

The two drivers read the pitch of a note from one table. [`note_freq_lo` `$E200`](../src/music/music_frequency_table.asm#L9) and [`note_freq_hi` `$E254`](../src/music/music_frequency_table.asm#L22) hold 84 SID frequency values, for the note indexes 0-83. Index n is the note n semitones above B0. The music player uses index 0 as a rest. The effect players play index 0 as B0. **Code**

**The music is tuned for NTSC.** The values give the correct pitch on an NTSC C64 (CPU clock 1022727 Hz). Hz = value * clock / 2^24. On NTSC the notes are 4 to 8 cents flat. A PAL C64 has a CPU clock of 985248 Hz, 64.6 cents lower. Thus on PAL every note is about 69 cents (2/3 of a semitone) flat. Music and effects keep their intervals. **Code** (computed from the table)

| Index | Note | Value | NTSC Hz | PAL Hz | Exact Hz |
|---|---|---|---|---|---|
| 0 | B0 | `$01F8` | 30.7 | 29.6 | 30.9 |
| 1 | C1 | `$0216` | 32.6 | 31.4 | 32.7 |
| 13 | C2 | `$042D` | 65.2 | 62.8 | 65.4 |
| 24 | B2 | `$07E5` | 123.2 | 118.7 | 123.5 |
| 46 | A4 | `$1C21` | 439.0 | 422.9 | 440.0 |
| 58 | A5 | `$383D` | 877.6 | 845.5 | 880.0 |
| 83 | A#7 | `$EE54` | 3719.2 | 3583.0 | 3729.3 |

## The title tune

Song 0 is the only tune. It plays on the title screen. Voice 0 plays a bass ostinato, voice 1 plays high arpeggios, and voice 2 plays the melody. All three voices use the pulse waveform.

| Voice | Stream | Setup | Note bytes (with rests) | Content |
|---|---|---|---|---|
| 0 (bass) | `music_title_voice0` | volume 12, pulse, instrument 3 legato, pulse width `$0802`, long lengths, tempo 2 | 81 | eighth-note ostinato B2 B3 F#3 G3, then E3 E4, C#4/B3 and F#3 figures |
| 1 | `music_title_voice1` | volume 15, pulse, instrument 5 normal, pulse width `$04CE` | 86 | 3 bars of rest, falling arpeggios G7 E7 B6 G6 E6 B5 G5 E5 in 32nds. A B5 D5 F#5 G5 F#5 D5 C#6 B5 figure, repeated F#4, a final F#7 .. C#5 arpeggio. |
| 2 (melody) | `music_title_voice2` | volume 15, pulse, instrument 0 then 5, normal, pulse width `$04CE` | 57 | B4 A4 B4, then E5 E5 E5 E5 D5 E5 in 16ths, F#4 E4 F#4 C#5 ..., B5 B4 |

- One tick = 2 frames. With the long table, a whole note is 64 ticks: one bar of 4/4.
- Each voice reaches its end byte after 576 ticks: 9 bars, 1152 frames, 23.0 s on PAL. A quarter note is 32 frames, about 94 beats per minute. **Code**
- Each voice ends with two rests and `$FF`. The first voice that starts its last rest reads `$FF` at once. Thus the player never plays the last rest. **Code**
- **Conclusion.** The tune is in B minor.

**The volume of voice 0 has no effect.** The setup commands of the three voices all run before the first note. Each `$9x` command overwrites `music_volume` and `music_volume_voice`. The player applies only the last one (voice 2, volume 15). The coverage marks the calls of [`music_apply_volume` `$E489`](../src/music/music_player_e38c.asm#L202) for voices 0 and 1 (`$E4E9`, `$E523`) as not executed. Thus the volume 12 of voice 0 has no effect, and the master volume is 15. **Observed**

### Worked example: the first two bars

The first bytes of the three streams:

```
$E8D0 voice 0: 9C A2 B3 A6 C0 02 08 AD E0 02 A8 83 18 83 24 83 1F 83 20 ...
$E97D voice 1: 9F A2 B5 A4 C0 CE 04 A8 80 00 80 00 80 00 85 50 85 4D ...
$EA31 voice 2: 9F A2 B0 A4 C0 CE 04 A8 80 00 83 30 83 2E 82 30 81 00 ...
```

Voice 0, byte by byte:

| Bytes | Meaning |
|---|---|
| `9C` | volume 12 (voices 1 and 2 overwrite it later) |
| `A2` | waveform pulse: control `$41` |
| `B3` | instrument 3: envelopes `$09 $00`, `$09 $00`, `$00 $70` |
| `A6` | articulation 2 (legato): AD = `$00`, SR = `$70` |
| `C0 02 08` | pulse width `$0802` |
| `AD` | long length table |
| `E0 02` | tempo 2 frames per tick |
| `A8` | tie off |
| `83` | length code 3: eighth = 8 ticks. Legato: G = 7, R = 1. |
| `18` | note index `$18` = 24: B2 (`$07E5`) |
| `83 24` | eighth, index 36: B3 |
| `83 1F` | eighth, index 31: F#3 |
| `83 20` | eighth, index 32: G3 |

Voice 1 sets volume 15, pulse, instrument 5 (`$00 $F0`, sustain 15), articulation 0, pulse width `$04CE`, tie off. Then `80 00` three times gives three whole rests (64 ticks each). Then `85 50` gives a 32nd (2 ticks) of index 80, G7.

Voice 2 sets the same values, with instrument 0 (`$11 $97`). Then `80 00` is a whole rest, `83 30` an eighth B4, `83 2E` an eighth A4, `82 30` a quarter B4 and `81 00` a half rest.

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

The timing of one eighth of voice 0: the player loads the counter with 7 and the end tick with `$FF`. After 7 ticks the counter is 0 and the gate goes off. One tick later the counter is `$FF` = the end tick, and B3 starts. **Code**

## The effect players

Each SID voice has its own effect player, so three effects can sound at the same time. An example is the footsteps of Bruce, a kick of the Ninja and a lantern. The three players are copies of one player. Only the SID registers, the state bytes and the zero-page stream pointer are different:

| Player | State | Position | Timer | Stream pointer | SID registers |
|---|---|---|---|---|---|
| `sfx_voice1_update` | `sfx_voice1_state` | `sfx_voice1_pos` | `sfx_voice1_timer` | `sfx_voice1_stream` (`$F6`) | `$D400-$D406` |
| `sfx_voice2_update` | `sfx_voice2_state` | `sfx_voice2_pos` | `sfx_voice2_timer` | `sfx_voice2_stream` (`$F8`) | `$D407-$D40D` |
| `sfx_voice3_update` | `sfx_voice3_state` | `sfx_voice3_pos` | `sfx_voice3_timer` | `sfx_voice3_stream` (`$FA`) | `$D40E-$D414` |

[`frame_update` `$15A8`](../src/game/frame_update.asm#L20) calls the three players at `$15AF`, `$15B2` and `$15B5`, each frame of the game screen (game and demo). [`cold_start` `$0400`](../src/game/cold_start.asm#L22) and `stop_all_sounds` clear the three state bytes. **Code**

[`sfx_voice1_update` `$EB03`](../src/sfx/sfx_voice1.asm#L19) does these steps each frame:

1. State 0: return.
2. State `$80` + n (a request): `ASL` gives 2n. `sfx_voice1_stream` = `sfx_stream_table` [2n]. Timer = 1, state = 1, control register = 0 (gate off), position = 0.
3. `sfx_voice1_tick`: decrement the timer. When it is not 0, return.
4. Read the command byte at the position. Store `sfx_cmd_offsets` [command] into the branch offset `sfx_voice1_cmd_offset`.
5. The `BCC` at [`sfx_voice1_cmd_branch` `$EB38`](../src/sfx/sfx_voice1.asm#L47) jumps into the handlers at `sfx_voice1_cmd_jumps`.
6. The handler reads the arguments and writes the SID. It sets the timer to the duration and stores the new position.

Thus the first command of an effect runs in the frame in which the player sees the request. A new request on a busy voice restarts that voice with the new effect. **Code**

### The state machine of an effect player

A player stays idle until `play_sound` writes a request in its state byte. The player then plays the stream until command 0 ends it, or until a new request replaces the effect.

~~~mermaid
stateDiagram-v2
  state "Idle (0)" as Idle
  state "Request ($80+n)" as Req
  state "Playing (1)" as Play
  [*] --> Idle
  Idle --> Req: play_sound
  Play --> Req: play_sound replaces the effect
  Req --> Play: next frame, stream from sfx_stream_table
  Play --> Play: timer 0, next command
  Play --> Idle: command 0
  Play --> Idle: stop_all_sounds
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Idle `$00` | `play_sound` chooses this voice | Request `$80`+n | `play_sound_slot1` (voices 2, 3: `play_sound_slot2`, `play_sound_slot3`) |
| Request `$80`+n | the next frame | Playing `$01` | `sfx_voice1_check_request` |
| Playing `$01` | the timer reaches 0 | Playing `$01` (next command) | `sfx_voice1_tick` |
| Playing `$01` | command 0 | Idle `$00` | `sfx_voice1_cmd_end` |
| Playing `$01` | `play_sound` replaces the effect (all voices busy, priority not lower) | Request `$80`+n | `play_sound_by_priority` |
| any | `stop_all_sounds` | Idle `$00` | `stop_all_sounds` |

## The effect stream format

An effect is a short list of notes, each with its duration in frames. The first note prepares the sound: the envelope, the pulse width and the waveform. The notes after it often change only the pitch.

### Where the data is

[`sfx_stream_table` `$EBE5`](../src/sfx/sfx_data.asm#L6) holds the stream address of each effect 0-14 (the entries are in [the table reference](reference/tables.md#sfx_stream_table)). The streams are at `$EC31-$EE82`, from `sfx_footstep_stream` to `sfx_lantern_stream`. The three players share the streams and the tables.

### The byte layout

Each command is a command byte 0-7 and its arguments. The duration is in frames (0 = 256). The note is an index into `note_freq_lo/hi`.

| Command | Arguments | Action | Handler (voice 1) |
|---|---|---|---|
| 0 | - | end: frequency 0, state 0, position 0. The gate stays as it is. | `sfx_voice1_cmd_end` |
| 1 | duration, note | timer = duration, frequency of the note | `sfx_voice1_cmd_note` |
| 2 | duration, note, control | + control register | `sfx_voice1_cmd_note_control` |
| 3 | duration, note, ADSR index, control | + AD/SR = `sfx_adsr_table` [i], [i+1] | `sfx_voice1_cmd_note_adsr_control` |
| 4 | duration, note, ADSR index, pulse index, control | + pulse width = `sfx_pulse_table` [p] (word) | `sfx_voice1_cmd_note_adsr_pulse_control` |
| 5, 6 | duration, note, pulse index, control | note, pulse width and control (one handler) | `sfx_voice1_cmd_note_pulse_control` |
| 7 | control | control only. The command does not set the timer, so the next command runs 256 frames later. | `sfx_voice1_cmd_control` |

`sfx_cmd_offsets` has 14 branch offsets. The 8 commands use 8 of them. **Code**

**Effect commands 5 and 7 are not used.** No stream uses commands 5 and 7. The coverage marks their table entries as not executed. Streams use command 6. **Observed**

The envelopes come from [`sfx_adsr_table` `$EC11`](../src/sfx/sfx_data.asm#L18), with an even index:

| Index | AD | SR | Used by effects |
|---|---|---|---|
| 0 | `$11` | `$97` | 2, 4, 5, 7, 11, 12, 14 |
| 2 | `$00` | `$F0` | 0, 6, 8, 10 |
| 4 | `$89` | `$00` | 1 |
| 6 | `$09` | `$40` | 3 |
| 8 | `$08` | `$00` | 10 |
| 10 | `$0C` | `$07` | 13 (reads the first bytes of `sfx_pulse_table`) |
| 12 | `$02` | `$08` | 9 (reads `sfx_pulse_table+2`) |

**Two envelopes are pulse widths.** `sfx_adsr_table` has space for 5 pairs only. Index 10 and 12 read into [`sfx_pulse_table` `$EC1B`](../src/sfx/sfx_data.asm#L25). Effects 9 and 13 use them. **Code**

`sfx_pulse_table` holds 11 pulse widths (words, even index):

| Index | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Pulse width | `$070C` | `$0802` | `$04CE` | `$019A` | `$0334` | `$01EC` | `$011F` | `$00CD` | `$0052` | `$007B` | `$0668` |

### The decoder

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

### Worked example: effect 1

Effect 1 sounds when the Yamo arrives. Its stream [`sfx_yamo_arrives_stream` `$EC37`](../src/sfx/sfx_data.asm#L39) is `04 08 0B 04 00 41  01 10 0D  01 04 0C  01 04 0B  00`.

| Bytes | Command | Decoded | Frames |
|---|---|---|---|
| `04 08 0B 04 00 41` | 4 | 8 frames, index 11 = A#1, AD/SR `$89`/`$00`, pulse width `$070C`, control `$41` (pulse, gate on) | 8 |
| `01 10 0D` | 1 | 16 frames, index 13 = C2 | 16 |
| `01 04 0C` | 1 | 4 frames, B1 | 4 |
| `01 04 0B` | 1 | 4 frames, A#1 | 4 |
| `00` | 0 | end: frequency 0, the voice is idle | - |

The effect lasts 32 frames. AD `$89` is attack 8 (100 ms) and decay 9 (750 ms). SR `$00` is sustain 0. Thus the pulse fades during the 32 frames. **Code**

## Sound requests and priorities

The game code asks for an effect, and it does not choose the voice. [`play_sound` `$2509`](../src/sfx/sound_request.asm#L12) finds a free voice. When all three voices are busy, the effect with the higher priority wins. The input is Y = `$80` + n:

1. Write `$15` to `SIGVOL` (`$D418`): volume 5 and the low-pass mode bit. No voice goes through the filter, because `stop_all_sounds` writes 0 to `RESON` (`$D417`).
2. When `sfx_voice1_state` is 0: store Y there, and store `sound_priority_table` [Y AND `$0F`] in `voice1_sound_priority`. Return.
3. Else do the same with voice 2, then with voice 3.
4. All three voices are busy ([`play_sound_by_priority` `$2547`](../src/sfx/sound_request.asm#L48)). Let p be the priority of the new effect. Then:
   - When p >= `voice1_sound_priority`, take voice 1.
   - Else, when p >= `voice2_sound_priority`, take voice 2.
   - Else, when p >= `voice3_sound_priority`, take voice 3.
   - Else, ignore the request.

The request stays in the state byte until the player sees it in the next frame. **Code**

[`stop_all_sounds` `$255E`](../src/sfx/sound_request.asm#L63) writes 0 to the three state bytes and to `$D400-$D420` (33 bytes). The SID has no registers at `$D41D-$D41F`, and `$D420` mirrors `$D400`. **Code**

The priorities are in [`sound_priority_table` `$2572`](../src/sfx/sound_request.asm#L76), one byte per effect. A higher value wins:

| Effect | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Priority | 11 | 12 | 10 | 0 | 8 | 7 | 9 | 6 | 0 | 0 | 1 | 2 | 3 | 4 | 5 |

**Conclusion.** The fight sounds and the footstep have the highest priorities. When the three voices are busy, a footstep (priority 11) can replace a lantern, hazard or trap effect. Those effects cannot replace a footstep.

## The 15 effects

"Frames" is the sum of the durations of the stream. The evidence column tells how a run saw the request. **Observed** means one of two things. A trace of `play_sound` in a run had this Y value, or the coverage of the runs marks the requesting code as executed.

| n | Request | Stream | Frames | Priority | Sound | Requested by | Evidence |
|---|---|---|---|---|---|---|---|
| 0 | `$80` | `sfx_footstep_stream` | 1 | 11 | one frame of noise at C6 | `actor_play_step_sound`, from the moves of every actor: `actor_action_step`, `actor_move_up`, `actor_move_down`, `actor_move_left`, `actor_enemy_down` (at `$1F5C`), `actor_continue_action`. Every 3 frames while Bruce walks. | Observed |
| 1 | `$81` | `sfx_yamo_arrives_stream` | 32 | 12 | low pulse A#1 C2 B1 A#1 | `yamo_start_pose` (Yamo takes pose state `$12`). `room00_frame` and `room02_frame_mouth` (the statue mouth of rooms 0 and 2). | Observed |
| 2 | `$82` | `sfx_enemy_enters_stream` | 12 | 10 | fast high pulse notes | `play_enemy_spawn_sound`, from `spawn_yamo` and `spawn_ninja` | Observed |
| 3 | `$83` | `sfx_unused_3_stream` | 6 | 0 | noise chirp C7 C8 B7 C8 C5 C2 | no code | Code |
| 4 | `$84` | `sfx_kick_stream` | 21 | 8 | rising noise sweep | flying kick states `$0C`/`$0D` at step `$0C`: `act_check_kick_left`, `act_check_kick_right` | Observed |
| 5 | `$85` | `sfx_swing_stream` | 6 | 7 | short rising noise | Ninja strike state `$16` at step 12: `act_strike_phase`. The request in `act_check_punch` (punch at step 8) never runs: a punch starts at step 4. | Observed (`$22D2`), Code (`$227C`) |
| 6 | `$86` | `sfx_impact_stream` | 5 | 9 | falling noise C8 to C1 | `play_hit_sound`: hits in `check_fight_pair_done` (and at `$2AE6`, `$2B2C`). Fireball start `launch_fireball0`, `launch_fireball1` (room 18). | Observed |
| 7 | `$87` | `sfx_bokken_hit_stream` | 8 | 6 | rising triangle arpeggio C4 to G7 | the Ninja's bokken hits: `check_fight_strike` | Observed |
| 8 | `$88` | `sfx_unused_8_stream` | 20 | 0 | falling gated pulse arpeggio F#7 to C#5 | no code | Code |
| 9 | `$89` | `sfx_runner_step_stream` | 1 | 0 | one pulse note C6 | `play_runner_sound`, from `draw_runner_step` and `draw_runner_step_alt`: each step of a runner hazard (rooms 7, 9, 13, 17) | Observed |
| 10 | `$8A` | `sfx_passage_opens_stream` | 79 | 1 | 16 silent frames, a low wobble, then B6 for 47 frames | `play_open_sound`, from `open_passage`, `open_passage_dark`, `room01_frame`, `room02_frame`, `room03_frame`, `room04_frame` (and at `$37F7`), `room09_frame`, `room15_frame` (and at `$3F2D`, `$3F54`), and `frame_update_yamo_idle` (a player-controlled Yamo times out) | Observed (`$1771` not executed) |
| 11 | `$8B` | `sfx_wizard_defeated_stream` | 14 | 2 | A7 alternating noise and pulse+triangle, then E4, A3 | `room18_wizard_defeated_sound`: each step of the wizard defeat in room 18 | Observed |
| 12 | `$8C` | `sfx_hazard_death_stream` | 14 | 3 | pulse C#4/C4 with pulse-width steps, then falling | `touch_deadly_tile`: an actor touches a deadly tile. Then `set_actor_hazard_death` (Bruce) or `remove_actor` (an enemy). | Observed |
| 13 | `$8D` | `sfx_trap_burst_stream` | 103 | 4 | noise burst, then 96 frames of low noise | `play_burst_sound`, from `update_burst_traps`: the timer of a burst trap (started by `touch_trap_tile`) reaches 8 | Observed |
| 14 | `$8E` | `sfx_lantern_stream` | 26 | 5 | sawtooth arpeggios B minor, A minor, B minor | `collect_lantern` (Bruce takes a lantern). `collect_room16_bonus_check_y` (the room 16 extra fall). | Observed (`$2F36`), Code (`$2FEC`) |

The runs that traced `play_sound` are the runs `a8-sfx1`, `a8-demo` and `a8-rooms` of the naming analysis. They are room 0 with the joystick, the attract demo, and each room snapshot. They saw the requests `$80`, `$81`, `$82`, `$84`, `$85`, `$86`, `$87`, `$89`, `$8C`, `$8D` and `$8E`.

**Effects 3 and 8 are never requested.** No code loads `$83` or `$88` for `play_sound`. Thus [`sfx_unused_3_stream` `$EC7A`](../src/sfx/sfx_data.asm#L53) and [`sfx_unused_8_stream` `$ED0E`](../src/sfx/sfx_data.asm#L88) never play. Their priority is 0. **Code**

**The punch swing sound at step 8 never plays.** [`act_check_punch` `$226A`](../src/actor/actor_timed_actions.asm#L349) requests the swing sound when a punch reaches step 8. But a punch starts with timer 4, so that request (at `$227C`) never runs. The Ninja strike in `act_strike_phase` plays the same sound. **Code**, **Observed** (the coverage marks the request as not executed)

The bytes `$EE83-$EED5` are an effect stream, but no table entry points to it. `$EED6-$EF3F` is a copy of `sfx_lantern_stream`. **Code**

## Still open

- The title tune does not use the routing byte of the filter command. Its bit layout (`$D417` bits 0-3) follows from the SID. No run checked it.
- `room02_frame_mouth` and `room00_frame` request effect 1 with the statue mouth animation. A run with a trace of `$3656` and `$36DF` in rooms 0 and 2 would check the timing.
- No run reached the second request of effect 14 ([`collect_room16_bonus_check_y` `$2FEC`](../src/actor/touch_effects.asm#L23)). A run in room 16 that walks over the bonus tile can show it.
