# Sound and music (version I)

The game plays a three-voice tune during the demo and during each game. The tune depends on the game mode: one tune for the demo, one for one player and one for two players. A small driver steps the tune once per frame from the last raster interrupt of the frame. Thus the music never stops while the fighters move, and the game logic does not call the driver. The program also holds a fourth complete tune that nothing selects, and a 1-bit sample player that nothing can reach. Version I has no sound effects. **Code**

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one raster interrupt chain, from line 0 to line `$FF`: 50 frames each second on a PAL C64.
- A *tick* is one step of a voice. A tune has a *tempo*: the frames per tick. A tempo of 2 gives 25 ticks each second.
- A *voice* is voice 0, 1 or 2 of the driver. Voice X of the driver is SID voice X+1.
- An *order list* is the list of patterns of one voice. A *pattern* is a list of notes and instruments.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The raster handler [`irq_frame_end` `$2994`](../src/irq/irq_screen_split.asm#L295) runs at line `$FF`, under the playfield. It sets the text mode for the score panel and then calls [`music_play_frame` `$09A5`](../src/music/music_driver.asm#L6). The driver compares `game_mode` with the tune that plays now. A new value starts the new tune, and the same value plays one frame of it. **Code**

~~~mermaid
flowchart TB
  A["Frame-end IRQ at line $FF"] --> B{"game_mode"}
  B -- "0" --> C["Volume 0 (music_silence)"]
  B -- "new tune" --> D["Reset the SID and the voices, copy the tune tables (music_start_tune)"]
  B -- "same tune" --> E["Write volume, resonance and cutoff"]
  E --> F["For voices 2, 1, 0: count the tempo"]
  F -- "tick" --> G["Read the order list and the pattern"]
  F -- "no tick" --> H["Set or slide the frequency"]
  G --> H
  H --> I["LFOs, pulse width, filter sweep"]
  I --> J["Write the 7 registers of each voice to the SID"]
~~~

`music_play_frame` does these steps in this order:

1. **It reads the tune number.** `game_mode` is the tune number. The value 0 writes volume 0 to the SID and returns. **Code** No run executed this path. **Observed** (coverage)
2. **It starts a new tune.** When `game_mode` is not `music_current_tune`, [`music_start_tune` `$09CF`](../src/music/music_driver.asm#L26) clears the SID and the state of the three voices. It copies the volume, the tempo, the base address, the pattern offset table and the three order lists of the tune. It writes the offset table into the operands of two `LDA $CF00,Y` instructions. The tune starts to play in the next frame. **Code**
3. **It writes the global registers.** In each other frame it writes the volume, the resonance and the cutoff base to the SID. **Code**
4. **It steps the voices.** [`music_play_voices` `$0A51`](../src/music/music_driver.asm#L73) counts the tempo of each voice down. At 0 the voice gets a tick: it reads its order list and its pattern. In each frame the voice sets or slides its frequency. **Code**
5. **It updates the effects.** After the voices, the driver steps the three LFOs, sets the pulse widths and adds the filter sweep to the cutoff. **Code**
6. **It writes the voices.** [`music_write_sid_voice` `$0BB3`](../src/music/music_driver.asm#L279) writes the frequency, the pulse width, the envelope and the control byte of each voice that is on. **Code**

The driver keeps a copy of each SID register of a voice in its workspace. It writes all 7 registers of each voice that is on in each frame, also when no value changed. **Code**

### One tick of a voice

A tick reads the next byte of the order list or of the pattern. [`music_read_order` `$0A77`](../src/music/music_driver.asm#L91) reads the command byte at the order position of the voice. It jumps through `music_order_commands`, a table of four handler addresses. The command byte is not range-checked. A byte above 3 would jump through the driver variables after the table, but no order list has such a byte. **Code**

While a note plays, the pattern command only counts the note timer down. When the timer reaches 0, the voice gets one release tick with the gate off. After the release tick, [`music_next_byte` `$0B19`](../src/music/music_driver.asm#L196) reads the next pattern byte. An instrument byte and the end of a pattern do not use a tick. The driver reads the next byte or the next order entry in the same tick. **Code**

~~~mermaid
stateDiagram-v2
  state "Note: gate on" as On
  state "Release tick: gate off" as Rel
  state "Read the next byte" as Read
  [*] --> Read
  Read --> On: note byte and duration byte
  Read --> Read: instrument byte, or $FF and the next order entry
  On --> Rel: note timer = 0
  Rel --> Read: one tick later
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Read the next byte | a note or a rest | Note | `music_read_note` |
| Read the next byte | `$80-$FE` or `$FF` | Read the next byte | `music_pattern_instrument`, `music_read_order` |
| Note | `music_note_timer` = 0 | Release tick | `music_note_ended` |
| Release tick | `music_note_timer` = 0 again | Read the next byte | `music_next_byte` |

Bit 6 of the duration byte keeps the gate on through the release tick. Duration index 14 skips the release tick. No pattern uses index 14. **Code**

### The effects of each frame

The driver has five modulator slots. Slots 0-2 are triangle LFOs, one for each voice. [`music_step_modulators` `$0DFC`](../src/music/music_effects.asm#L100) adds or subtracts the LFO step of the voice in each frame and turns the direction at 0 and `$FF`. Slot 3 is a copy of ENV3, the envelope of SID voice 3. Slot 4 is a copy of OSC3. No instrument selects slot 4. **Code**

[`music_update_pulse` `$0E3E`](../src/music/music_effects.asm#L133) sets the pulse width of each modulated voice to the base width plus the LFO value, shifted left by the shift of the instrument. An instrument with flag `$80` keeps a fixed width. **Code**

[`music_update_filter` `$0E6D`](../src/music/music_effects.asm#L160) adds the sweep value to the cutoff base, or subtracts it. The sweep value is the modulator slot of the instrument, shifted left by the sweep shift. All instruments with a sweep use slot 3, the ENV3 copy. The voice of these instruments is voice 2, thus SID voice 3. The cutoff then follows the envelope of the same note. **Code**

[`music_slide_freq` `$0EB3`](../src/music/music_effects.asm#L197) moves the current frequency toward the note frequency in each frame. The step is the slide step of the instrument, shifted left by the octave of the note. Thus the slide takes the same time in each octave. The slide stops at the note. A slide instrument glides only when the duration byte of the previous note held bit 6 or bit 7. Else the driver sets the note frequency at once. **Code**

## The music data format

The music data fills `$0400-$09A4` (patterns and offset tables) and `$0F52-$1157` (tune tables, order lists and instruments). The driver code and its workspace are between them, at `$09A5-$0F51`. Each tune is one block of patterns in the order of their numbers. The offsets in the tables are relative to the block start. **Code**

**Conclusion.** A music tool or a converter wrote the pattern blocks as relocatable data. The game source placed the order lists and the tables with absolute addresses after the driver.

### Where the data is

The tune tables have 5 entries, for tunes 0-4. [`music_tune_bases` `$0F54`](../src/music/music_tables.asm#L17) holds the base address of each tune. [`music_tune_pattern_tables` `$0F5E`](../src/music/music_tables.asm#L21) holds the address of the offset table of each tune. The other tables follow them. **Code**

| Table | Address | Entry | Meaning |
|---|---|---|---|
| `music_tune_bases` | `$0F54` | word | Base address of the patterns of the tune |
| `music_tune_pattern_tables` | `$0F5E` | word | Address of the pattern offset table: word n is the offset of pattern n |
| `music_tune_orders_v0` | `$0F68` | word | Order list of voice 0 |
| `music_tune_orders_v1` | `$0F72` | word | Order list of voice 1 |
| `music_tune_orders_v2` | `$0F7C` | word | Order list of voice 2 |
| `music_instrument_ptrs` | `$0F86` | word | Address of instrument 0-24, for all tunes |
| `music_tune_volumes` | `$0FB8` | byte | Value for SIGVOL at the tune start |
| `music_tune_tempos` | `$0FBD` | byte | Frames per tick |

The address of pattern n of tune t is `music_tune_bases[t]` plus word n of the offset table of tune t. Tune 0 has placeholder entries: base `$0000`, offset table `$00FA`, order lists `$FFFF`, volume 2 and tempo 0. Nothing reads them, because `game_mode` 0 returns before the tune test. **Code**

### The order lists

Each voice has its own order list. The driver keeps a byte position in the list for each voice. A command reads its arguments at the next positions. **Code**

| Bytes | Command | What it does |
|---|---|---|
| `00` | stop | Resets the voice and stops it. Only tune 4 uses it. |
| `01 pp` | play | Plays pattern pp of the tune. At its `$FF` the position moves on 2 bytes. |
| `02 yy` | jump | The list continues at byte position yy. All tunes 1-3 loop with this command. |
| `03 yy nn` | repeat | Jumps to position yy, nn more times. Then it moves the position on 3 bytes. |

The repeat command has one counter for each voice. The first time, it sets the counter to nn and jumps. Each later time, it decrements the counter and jumps while the counter is not 0. All repeats in the data have nn = 1. Thus the code for a second jump at `$0C77-$0C7F` never runs. **Code**

Tune 1 and voice 1 use the repeat in a special form. The target yy is the position of the final `02` entry of the list. Thus the section before the repeat plays two times, then the pattern after the repeat plays, then the list loops. **Code**

### The patterns

A pattern is a list of bytes. [`music_read_pattern` `$0B1C`](../src/music/music_driver.asm#L198) reads it with the pattern position of the voice. **Code**

| Byte | Meaning |
|---|---|
| `$FF` | End of the pattern. The next order entry runs in the same tick. |
| `$80-$FE` | Instrument `b AND $7F` (0-24). The next byte follows at once. |
| `$00-$7F` | Note byte. Bits 0-3: the note, 0 = rest, 1 = C to 12 = B. Bits 4-6: the octave. A duration byte follows. |
| duration | Bits 0-3: the index into `music_durations`. Bit 6: gate on through the release tick, and the next note glides. Bit 7: the next note glides with the gate off (no pattern uses it). Bits 4-5: not used. |

The note frequency is `$0100` plus the entry of `music_note_freqs` for the note. The driver shifts it left by the octave of the note plus the octave offset of the instrument. A rest changes no frequency and leaves the gate as it is. **Code**

[`music_note_freqs` `$0D14`](../src/music/music_workspace_0cdb.asm#L53) holds the low bytes of octave 0, from C `$010C` to B `$01FA`. These values are the NTSC table of the Commodore 64 Programmer's Reference Guide. A4 is `$01C3` with 4 left shifts, thus `$1C30`. This gives 440 Hz at the NTSC clock. **Code**

### The durations

[`music_durations` `$0D21`](../src/music/music_workspace_0cdb.asm#L57) gives the note timer for each index. A note lasts the table value plus 1 ticks: the value in ticks with the gate on, then the release tick. **Code**

| Index | Byte | Ticks | Used by |
|---|---|---|---|
| 0 | `$02` | 3 | tune 1 |
| 1 | `$05` | 6 | tunes 1 and 2 |
| 2 | `$08` | 9 | tune 1 |
| 3 | `$0B` | 12 | tunes 1-4 |
| 4 | `$11` | 18 | tune 1 |
| 5 | `$17` | 24 | tunes 1-4 |
| 6 | `$23` | 36 | tunes 1-3 |
| 7 | `$2F` | 48 | tunes 1 and 2 |
| 8 | `$47` | 72 | tunes 1 and 2 |
| 9 | `$01` | 2 | no pattern |
| 10 | `$03` | 4 | tunes 1, 2, 3 and 4 |
| 11 | `$07` | 8 | tunes 1 and 3 |
| 12 | `$06` | 7 | no pattern |
| 13 | `$04` | 5 | only pattern 2 of tune 1, which never plays |
| 14 | `$01` | 1 (no release tick) | no pattern |
| 15 | `$01` | 2 | tunes 2 and 4 |

Indexes 0-8 give 3, 6, 9, 12, 18, 24, 36, 48 and 72 ticks. Indexes 9-15 have no order. **Code**

**Conclusion.** With 12 ticks for a quarter note, indexes 0-8 are the note values from a 1/16 note to a dotted whole note. Pattern 0 of tune 1 has 192 ticks, thus 4 bars of 4/4.

### The instrument records

[`music_instrument_ptrs` `$0F86`](../src/music/music_tables.asm#L37) points to 25 records at `$105E-$1156`. The records follow each other without a gap. [`music_set_instrument` `$0D3C`](../src/music/music_effects.asm#L6) reads a record. A record has 6, 11, 13 or 18 bytes, because the pulse part and the filter part are optional. **Code**

| Byte | Field | Meaning |
|---|---|---|
| 0 | waveform | `$10` triangle, `$20` sawtooth, `$40` pulse, `$80` noise. The gate bit of the voice does not change. |
| +1, +2 | pulse width | Only for `$40`: base width, low and high byte |
| +3 | LFO flag | Only for `$40`: bit 7 = fixed width, else the LFO of the own voice modulates the width |
| +4 | PWM shift | Only for `$40`: left shifts of the LFO value |
| +5 | LFO speed | Only for `$40`: step of the LFO of the voice in each frame |
| next | AD | Attack and decay |
| next | SR | Sustain and release |
| next | slide step | 0 = no slide |
| next | octave offset | Added to the octave of each note, `$FF` = -1 |
| next | filter flag | 0: the voice does not go through the filter, and the record ends. Else the voice goes through the filter. |
| +1 | mode | Filter mode bits 4-7 of SIGVOL, for example `$10` low-pass |
| +2 | resonance | Bits 4-7 of RESON |
| +3, +4 | cutoff | Base cutoff, low and high byte |
| +5 | sweep slot | Modulator slot of the sweep, `$80` = no sweep, 3 = ENV3 |
| +6 | sweep shift | Left shifts of the sweep value |
| +7 | sweep direction | 0 = add, 1 = subtract |

The LFO flag of a pulse record holds 0, 1 or 2 in the data. The code ignores the value and uses the LFO of the voice that plays the instrument. Each value is the voice of the order list that uses the instrument. **Code**

**Conclusion.** The LFO flag once selected the modulator slot of the pulse width, as the sweep slot does for the filter.

Instrument 0 is the first record at `$105E`: `40 00 08 80 00 00 05 37 00 00 00`. It is a pulse wave with width `$0800`, a fixed width, AD `$05`, SR `$37`, no slide, no octave offset and no filter. **Code**

### The decoder

```text
each frame:
  if game_mode = 0: SIGVOL = 0, return
  if game_mode <> current tune: start tune game_mode, return
  write SIGVOL, RESON, CUTLO, CUTHI
  for voice X = 2 down to 0, if the voice is on:
    tempo_count[X] -= 1
    if tempo_count[X] = 0:
      tempo_count[X] = tempo[X]
      loop:
        cmd = order[X][pos[X]]
        stop:   reset voice X, next voice
        jump:   pos[X] = order[X][pos[X]+1], continue loop
        repeat: if count[X] = 0: count[X] = nn, pos[X] = yy
                else: count[X] -= 1, if count[X] = 0: pos[X] += 3 else pos[X] = yy
                continue loop
        play:   if a new entry: pattern[X] = base + offset[pp], ppos[X] = 0, read bytes
                else: timer[X] -= 1
                      if timer[X] = 0 and no release yet: release tick (gate off unless bit 6)
                      if timer[X] = 0 after the release: read bytes
    if the instrument slides: slide the frequency, else frequency = note frequency
step LFOs, set pulse widths, set the filter cutoff
write the 7 registers of each voice that is on

read bytes:
  b = pattern[X][ppos[X]]
  $FF:      new entry, pos[X] += 2, back to the order loop
  $80-$FE:  set instrument b AND $7F, ppos[X] += 1, read bytes again
  else:     note = b AND $0F, octave = (b >> 4) + instrument octave
            d = next byte, timer[X] = durations[d AND $0F], flags[X] = d AND $C0
            if note <> 0: gate on
```

### Worked example: the first bytes of tune 1

Tune 1 is the tune of the demo. Entry 1 of the tune tables gives these values. **Code**

| Table | Entry 1 | Meaning |
|---|---|---|
| `music_tune_bases` | `$0400` | Patterns of tune 1 start at `$0400` |
| `music_tune_pattern_tables` | `$0957` | Offset table `music_t1_pattern_offsets` |
| `music_tune_orders_v0` | `$0FC2` | Order list of voice 0 |
| `music_tune_volumes` | `$0A` | Volume 10, no filter mode |
| `music_tune_tempos` | `$02` | 2 frames per tick, 25 ticks each second |

The order list of voice 0 at [`music_t1_order_v0` `$0FC2`](../src/music/music_tables.asm#L52) starts with `01 00`: play pattern 0. Word 0 of the offset table is `$0000`. Thus pattern 0 is at `$0400` + `$0000` = `$0400`, the start of [`music_t1_pattern_00` `$0400`](../src/music/music_patterns.asm#L6). **Code**

The first bytes of pattern 0 are `80 00 01 53 00 50 00 5A 00 50 00 58 00`. **Code**

| Bytes | Decoded | Frequency | Ticks |
|---|---|---|---|
| `80` | Instrument 0: pulse `$0800`, AD `$05`, SR `$37` | - | 0 |
| `00 01` | Rest, octave 0. Duration index 1 = `$05` | - | 6 (5 + release) |
| `53 00` | Octave 5, note 3 = D. Index 0 = `$02` | `$012D` << 5 = `$25A0` | 3 (2 gate on + release) |
| `50 00` | Rest. Index 0 | - | 3 |
| `5A 00` | Octave 5, note 10 = A. Index 0 | `$01C3` << 5 = `$3860` | 3 |
| `50 00` | Rest. Index 0 | - | 3 |
| `58 00` | Octave 5, note 8 = G. Index 0 | `$0191` << 5 = `$3220` | 3 |

The pattern thus starts with a 6-tick rest and then plays D5, A5 and G5 as short notes with rests between them. A note of 3 ticks lasts 6 frames, 0.12 seconds. The gate is on for 4 of the 6 frames. **Code**

The frequency `$25A0` is 9632. At the NTSC clock of 1022727 Hz this gives 587.2 Hz, the pitch of D5. At the PAL clock of 985248 Hz it gives 565.6 Hz. **Code**

## The tunes

Each game mode selects one tune. [`demo_play` `$17BF`](../src/game/game_modes.asm#L220) sets `game_mode` to 1, [`game_one_player` `$16A9`](../src/game/game_modes.asm#L81) sets 2, and [`game_two_players` `$161D`](../src/game/game_modes.asm#L6) sets 3. No code writes 4 to `game_mode`. **Code**

| Tune | game_mode | Patterns | Data | Volume | Tempo | Loop | Time of a loop |
|---|---|---|---|---|---|---|---|
| 1 demo | 1 | 14 | `$0400-$0602` | `$0A` | 2 | 6-tick start + 2130 ticks | 85 s |
| 2 one player | 2 | 12 | `$0603-$073F` | `$08` | 2 | 2400 ticks | 96 s |
| 3 two players | 3 | 9 | `$0740-$08D5` | `$0A` | 1 | 3072 ticks | 61 s |
| 4 (unused) | none | 4 | `$08D6-$0956` | `$0C` | 1 | one time, 384 ticks, then stop | 7.7 s |

The times are for 50 frames each second. Tune 1 starts with a 6-tick pattern in voices 1 and 2. The loops then jump to position 2, after that pattern. **Code**

Voice 2 of tune 2 uses instrument 24, and voice 2 of tune 3 uses instrument 18. These two instruments have a pulse LFO, a slide and a filter sweep on ENV3. Voice 0 of tune 2 plays a figure of 192 ticks. It repeats 12.5 times in one loop of voices 1 and 2. **Code**

### Tune 4, the unused jingle

Tune 4 is a complete short tune with its own patterns, offsets, order lists and instruments 19-21. Its data is at [`music_t4_pattern_00` `$08D6`](../src/music/music_patterns_04be.asm#L654), `$099D-$09A4` and [`music_t4_order_v0` `$1053`](../src/music/music_tables_0fd5.asm#L84). Each order list ends with the stop command, thus the tune plays one time and the voices stop. **Code**

A run that writes 4 to `game_mode` plays tune 4. The SID writes in the trace of that run show the tune. **Observed**

The tune is a fanfare on G# and D# over 384 ticks, 7.7 seconds. Voice 1 plays the melody from D#5. Voice 0 plays the same melody an octave and a fourth higher, because instrument 19 adds one octave. Voice 0 starts 2 ticks later, after its pattern 0 of a 2-tick rest. Voice 2 plays a bass line with notes of 24 ticks. **Code**

Tune 4 is the only user of three parts of the driver. These are the stop command at `$0C58`, the subtracting filter sweep at `$0EA0` (instrument 21), and the sharp notes C#, D#, F#, G# and A#. The coverage of the recorded game runs marks none of them. **Observed** (coverage)

**Conclusion.** Tune 4 was a jingle for an event of the game, for example a won bout or a new rank. The game logic does not call it, or no longer calls it. The driver tables have 5 entries for this tune.

## Bugs

- **Voice 0 of the demo tune skips pattern 2 and plays the melody of voice 1.** The order list of voice 0 is `01 00 01 00 01 01 01 01 01 01 01 01 03 13 01 01 02 02 00`. The repeat at `$0FCE` jumps to position `$13` = 19. The list ends at position 18. Position 19 is the first byte of the order list of voice 1 at `$0FD5`. Thus voice 0 plays the patterns of voice 1, 768 ticks after voice 1. These are P3 and then P4 P5 P4 P6 P7 P7 P7 P7 P4 P6. Then voice 0 reads the repeat entry of voice 1. The repeat counter of voice 0 is already 1, thus voice 0 plays P8 and jumps to its own position 2. **Code**

  After the first pass, the loop of voice 0 is 576 + 6 + 960 + 210 = 1752 ticks. The loop of voices 1 and 2 is 2130 ticks. Thus voice 0 moves out of time with the other voices in each loop of the demo music. Pattern 2 at `$0486-$04BD`, its offset, instrument 2 and the bytes `$0FD1-$0FD4` are never read. **Code** / **Observed** (coverage)

  **Conclusion.** The authors removed one entry of the list and did not change its repeat target. With one more `01 00` entry before the repeat, position 19 is the `02 00` entry. Voice 0 then plays 2 × 960 ticks and pattern 2 (210 ticks), thus 2130 ticks, the loop of voices 1 and 2. Voices 1 and 2 use the same form, and their targets are the positions of their final `02` entries.

- **The pitch table is for NTSC.** `music_note_freqs` gives the NTSC values of the Programmer's Reference Guide. On a PAL C64 the SID clock is 985248 Hz, not 1022727 Hz. Thus each note is 3.7 % low, about 2/3 of a semitone. A4 gives 423.8 Hz, not 440 Hz. The music stays in tune with itself. **Code**

- **The filter sweep is weak.** `music_update_filter` adds the shifted ENV3 value to the cutoff low and high bytes as one 16-bit value. The SID uses only bits 0-2 of CUTLO and all 8 bits of CUTHI, thus 11 bits. With ENV3 = `$FF`, instrument 18 (shift 2) moves the cutoff by at most 28 of 2047 steps. Instrument 24 (shift 1) moves it by at most 14 steps. **Code**

  **Conclusion.** The sweep was to move the cutoff over a large part of its range. Now it is almost inaudible. Three more left shifts would move the sweep into the 8 bits of CUTHI.

The source marks the repeat bug at `$0FCE` and the unread pattern in its comments. The rebuild keeps all three bugs, because the rebuild must give the bytes of the original. **Code**

## The dead sample player

The program holds a complete 1-bit sample player at `$29C8-$2A65`. No code can reach it. It plays a sample with clicks of the SID volume: each interrupt changes the volume from 15 to 0 or from 0 to 15. The time to the next click comes from the sample byte. **Code**

[`sfx_sample_start` `$2A0A`](../src/leftovers/leftover_2a0a.asm#L6) is the set-up, and nothing calls it. It does these steps:

1. It stops the CIA1 timers and sets the sample range to `$0804-$0A04`.
2. It clears the SID registers and sets `sfx_volume` to 15.
3. It starts CIA1 timer A with latch 8. Thus timer A underflows each 9 cycles.
4. It starts CIA1 timer B as a one-shot timer that counts the underflows of timer A. It enables the timer B interrupt.

The set-up writes `$7F` to `CIAICR` two times and 0 to `sfx_done` two times. **Code**

**Conclusion.** The duplicated writes are signs of edits to the routine.

[`sfx_sample_irq` `$29C8`](../src/sfx/sfx_sample_player.asm#L6) runs at each timer B underflow. It writes `sfx_volume` EOR `$0F` to SIGVOL, so each interrupt gives one click. It reads the next sample byte. The byte is an index into two 256-byte tables at `$0E00` (low bytes) and `$0F00` (high bytes). They give the next count of timer B. The time to the next click is about (count + 1) × 9 cycles. At the end of the range it sets `sfx_done` to `$7F` and leaves timer B stopped. **Code**

Each byte of the sample is thus one half-wave of a square wave. The range `$0804-$0A04` gives 513 half-waves. **Code**

The player cannot run in version I, for three reasons:

- `init_game_state` writes `$7F` to `CIAICR`. This stops all CIA1 interrupts.
- No code calls `sfx_sample_start`.
- No other code reads `sfx_done` or writes the sample pointers at `$2D-$32`.

The 15 raster handlers still start with `BIT $D019 / BMI / JMP sfx_sample_irq`. A CIA1 interrupt that is not a raster interrupt would go to the sample player. In the final game this test costs 7 cycles in each raster interrupt. No run executed the player. **Code** / **Observed** (coverage)

The data of the player is now music. `$0804-$0A04` holds the end of pattern 3 of tune 3, patterns 4-8 of tune 3 and all of tune 4. Then come the four offset tables and the first `$60` bytes of the driver code. All bytes up to `$09A4` decode as patterns, and none is sample data. `sfx_period_lo_old` at `$0E00` is in `music_step_modulators`, and `sfx_period_hi_old` at `$0F00` is in `music_slide_freq`. The rest of the two pages holds driver code, tune tables and order lists. If the player ran, it would play the music bytes as clicks. **Code**

**Conclusion.** An earlier build of the game had a short sample at `$0804` and its period tables at `$0E00` and `$0F00`. The music driver and its data later took that memory. The player, its set-up and the 15 jumps stayed in the program.

Version II uses the same player as a live part of the game. [`v2:sfx_sample_irq` `$311A`](../../v2/src/sfx/sfx_sample_player.asm#L6) plays four samples for the hits, the attack and a fighter on the floor. Version II keeps the samples in the floor bitmap at `$F540` and the period tables at `$0200` and `$0300`. The page [../../v2/docs/sound_music.md](../../v2/docs/sound_music.md) explains it. [../../docs/versions.md](../../docs/versions.md) lists all changes between the versions. **Code**

Before the game starts, the loading stage plays a speech sample. It uses a player of the same type: M.MYTINY at `$9000`, with its tables in M.SPCHTBL at `$9800`. That sample is not part of the game. The page [../../docs/loading_stage.md](../../docs/loading_stage.md) explains it. **Observed**

## Still open

- Is the drift of voice 0 in the demo music audible? Record the SID output of the demo for two loops (170 seconds), then compare it with a build where `$0FCF` is `$11`.
- What was tune 4 for? No code or text of version I names it. Compare the jingles of version II and the other Melbourne House games of 1985.
- What sample did the dead player play? Its data is not in the image. Find an earlier build or a disk with the old layout.
- Did the authors test the pitch on NTSC? Play the music on an NTSC C64 and compare the pitch with the PAL run.
