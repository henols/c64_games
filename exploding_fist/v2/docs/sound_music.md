# Sound and music (version II)

The game makes two kinds of sound. A three-voice music driver plays one tune for each part of the game. The parts are the demo, a one-player game, a two-player game and the high score name entry. A 1-bit sample player adds four short digitized sounds to the fight. They are two hit sounds, an attack sound and the sound of a fighter on the floor. Version I has the same sample player, but nothing calls it and its data is not in memory. Version II is the first version where a player hears the samples. The full list of changes between the versions is on [versions.md](../../docs/versions.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one PAL screen, 1/50 second. A *tick* is one step of the music, a number of frames that the tempo of the tune gives.
- A *sample byte* is one byte of a sample. A *half-wave* is the time between two changes of the SID volume.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The music

The music driver and the tune data are the same as in version I, byte for byte, with two exceptions. The format of the patterns, the order lists and the instruments is on the music page of version I: [../../v1/docs/sound_music.md](../../v1/docs/sound_music.md). The frame-end raster IRQ calls [`music_play_frame` `$09A5`](../src/music_driver.asm#L6) once in each frame. The value in `game_mode` selects the tune. A new value starts the tune. (**Code**)

| Tune | `game_mode` | Part of the game | Tempo (frames for each tick) |
|---|---|---|---|
| 1 | 1 | The demo | 2 |
| 2 | 2 | A one-player game | 2 |
| 3 | 3 | A two-player game | 2 |
| 4 | 4 | The high score name entry (new in version II) | 1 |

The fix of the tune 1 order list moved the data after it by 2 bytes. Thus the entry of the game moved from `$1158` to `$115A`. Each order list pointer after the fixed list is 2 more than in version I. Each instrument pointer is also 2 more. The code of the driver did not change. (**Observed**, byte compare of the R2010 and SCC images)

### The fixed tune 1

In version I, the order list of voice 0 of tune 1 has a bug. Its repeat command jumps to position 19, but the list has only 17 bytes before the jump. Thus voice 0 continues into the order list of voice 1 and plays out of step with the other voices. Pattern 2 of the tune never plays. (**Code**)

Version II puts 2 more bytes, `01 00` (play pattern 0), into the list at [`music_t1_order_v0` `$0FCE`](../src/music_tables.asm#L51). Now the repeat target 19 is the jump to position 0 at `$0FD5`. Voice 0 plays its section of 960 ticks two times, then pattern 2 (210 ticks). The loop has 2130 ticks, the same length as the loops of voices 1 and 2. At tempo 2, one loop takes about 85 seconds. (**Code**)

The runs of version II read pattern 2, instrument 2 and the last bytes of the list `$0FD3-$0FD6`. No run of version I read them. (**Observed**, coverage)

### The name entry jingle

Version I has tune 4 in memory, but no code selects it. In version II, [`hs_name_entry` `$1762`](../src/high_score_table.asm#L400) writes 4 to `game_mode`. Thus the player hears tune 4 while he types his name into the high score table. The tune data is the same as in version I. (**Code**)

Tune 4 is a jingle that plays one time. After 384 ticks, about 7.7 seconds, each voice reads the stop command [`music_cmd_stop` `$0C58`](../src/music_driver.asm#L342). Then the name entry continues without music. The next value of `game_mode`, 1 for the demo, starts tune 1. The name entry run read all the data of tune 4 and executed the stop command. (**Observed**, coverage)

The high score table is on [high_scores.md](high_scores.md).

## The sample player

The sample player makes a sound with only the master volume of the SID. It changes the volume between 0 and 15 again and again. Each change makes a click in the output. The time between two changes comes from the sample byte. Thus a sample is a square wave with a different length for each half-wave. (**Code**)

The player uses no SID voice. It uses the two timers of CIA1. The same method is in the sample player of the loading stage, which plays the speech of the title picture. See [loading_stage.md](../../docs/loading_stage.md). (**Code**)

~~~mermaid
flowchart TB
  A["A game event calls a sample entry (sfx_play_sample_0..3)"] --> B{"samples_off = 0?"}
  B -- "no" --> X["Start no sample"]
  B -- "yes" --> C["Stop the CIA1 timers, set the read and end pointers"]
  C --> D["Clear the SID, volume 15, start timers A and B"]
  D --> E["Timer B underflows: CIA1 IRQ"]
  E --> F["Raster handler prologue: BIT $DC0D, CLI, JMP"]
  F --> G["Toggle the volume, read the next sample byte"]
  G --> H{"Pointer past the end?"}
  H -- "no" --> I["Load timer B from the period tables, start it"]
  I --> E
  H -- "yes" --> J["sfx_done = $FF, timer B stays stopped"]
~~~

### The start of a sample

The game has eight entries, [`sfx_play_sample_0` `$3158`](../src/sfx_sample_player.asm#L44) to `sfx_play_sample_7` at `$3182`. Each entry saves X in `sfx_saved_x` and loads X with 4 times the sample number. Only the entries 0 to 3 have callers. The common part [`sfx_sample_start` `$3186`](../src/sfx_sample_player.asm#L84) then does these steps (**Code**):

1. It reads `samples_off`. When the value is not 0, it restores X and returns. No sample starts.
2. It writes `$7F` to `$DC0D` and switches off all CIA1 interrupts. It writes `$28` to `$DC0E` and `$DC0F` and stops the two timers. Thus a sample that plays stops now.
3. It adds `$F540` to the start offset and the end offset of the table entry. The results go to `sfx_sample_ptr` and `sfx_sample_end`.
4. It sets the latch of timer A to 8. Timer A then underflows each 9 cycles.
5. It writes 0 to `$D400-$D41C`. This clears all SID registers, also the registers of the three music voices.
6. It sets `sfx_volume` to 15. It switches on the timer B interrupt (`$82` to `$DC0D`).
7. It starts timer A in continuous mode (`$51`). It loads timer B with `$0040` and starts it (`$59`). In this mode, timer B counts the underflows of timer A.
8. It writes 0 to `sfx_done`, restores X and returns.

A new sample always stops the sample that plays. The game does not compare the two sounds. (**Code**)

### The sample IRQ

The CIA1 and the VIC share the IRQ vector at `$FFFE`, and the vector always points to a raster handler. Each raster handler starts with `BIT $DC0D / BPL / CLI / JMP sfx_sample_irq`. The `BIT` reads the CIA1 interrupt flags and clears them. When bit 7 is 1, the IRQ comes from timer B. The handler then clears the I flag and jumps to the sample IRQ. A raster IRQ can thus interrupt the sample IRQ. The raster handlers are on [interrupts.md](interrupts.md). (**Code**)

[`sfx_sample_irq` `$311A`](../src/sfx_sample_player.asm#L6) does these steps (**Code**):

1. It changes `sfx_volume` with `EOR #$0F` and writes it to `$D418`. The volume is now 0 or 15. The filter mode bits of `$D418` are 0.
2. It reads the sample byte at `sfx_sample_ptr`. The byte is an index into the two period tables.
3. It writes the high byte from `sfx_period_hi` and the low byte from `sfx_period_lo` into the latch of timer B.
4. It adds 1 to `sfx_sample_ptr`.
5. While `sfx_sample_ptr` is not more than `sfx_sample_end`, it starts timer B again in one-shot mode (`$59`).
6. After it reads the end byte, it writes `$FF` to `sfx_done`. Timer B stays stopped, and no more sample IRQs come. Thus the player reads the end byte, but it does not wait for the count of that byte.

Timer B counts the underflows of timer A. A count `c` gives `c + 1` underflows, that is `(c + 1) x 9` cycles. The time between two timer B IRQs is the length of one half-wave. (**Code**)

### The period tables

The two tables [`sfx_period_lo` `$0200`](../src/constants.asm#L125) and `sfx_period_hi` at `$0300` give the count of timer B for each value of a sample byte. The file holds them at [`sfx_period_lo_init` `$C700`](../src/sfx_period_tables.asm#L103) and `sfx_period_hi_init` at `$C800`. The shape buffer 3 of the sprite builder uses `$C700-$C93F`. Thus [`init_copy_periods` `$18FA`](../src/init_machine.asm#L16) copies the two tables to pages 2 and 3 at the start, before the shape builder writes over them. (**Code**)

The counts go up from 1 for value `$00` to 60000 for value `$FF`. Up to value `$30`, the count is the value + 1. From `$31`, the count is the value + 2, so the count 50 is not in the table. Above about `$BC` the steps are larger. The values `$EE-$FF` give long pauses from 500 to 60000. The samples use only the values `$04-$F1`. (**Code**)

The tables are byte for byte the same as M.SPCHTBL of the loading stage at `$9800/$9900`. (**Observed**, byte compare of the SCC image with the 2010 loading image). In version I, the dead player reads its tables at `$0E00/$0F00`, but the music driver uses these addresses. Version II moved the tables out of the music area. (**Code**)

### The state of a sample

`sfx_done` tells if a sample plays. Only the bull round reads it. It starts sample 3 only when no sample plays. The bull round itself writes `$7F` to `sfx_done`, the end value of the version I player. Each value that is not 0 works for the test. (**Code**)

~~~mermaid
stateDiagram-v2
  state "No sample (sfx_done not 0)" as Idle
  state "Plays (sfx_done = 0)" as Play
  [*] --> Idle
  Idle --> Play: a sample entry, samples_off = 0
  Play --> Play: a sample entry, samples_off = 0
  Play --> Idle: the end byte is played
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| No sample | A sample entry with `samples_off` = 0 | Plays | `sfx_sample_start` |
| Plays | A sample entry with `samples_off` = 0 | Plays (the new sample) | `sfx_sample_start` |
| Plays | `sfx_sample_ptr` > `sfx_sample_end` | No sample | `sfx_sample_irq` |

## The sample format

### Where the data is

The sample table [`sfx_sample_table` `$F540`](../src/sfx_samples_f540.asm#L6) holds one entry for each sample. `sfx_sample_start` reads the entry at offset X. The samples follow the table, from `$F580` to `$FFDD`. The file of the samples ends at `$FFEF`. (**Code**)

### The byte layout

An entry has 4 bytes. The offsets are from `$F540`, the start of the table. (**Code**)

| Byte | Meaning |
|---|---|
| 0-1 | The start offset, low byte first. The address of the first sample byte is `$F540` + offset. |
| 2-3 | The end offset, low byte first. The address of the last sample byte is `$F540` + offset. The player plays this byte. |

| Entry | Bytes in the file | Start offset | End offset | Range |
|---|---|---|---|---|
| 0 | `40 00 23 01` | `$0040` | `$0123` | `$F580-$F663` |
| 1 | `23 01 39 04` | `$0123` | `$0439` | `$F663-$F979` |
| 2 | `39 04 93 07` | `$0439` | `$0793` | `$F979-$FCD3` |
| 3 | `93 09 9D 0A` | `$0993` | `$0A9D` | `$FED3-$FFDD` |

A sample byte is an index into the period tables. The player toggles the volume, then waits for the count of the byte. Two bytes give one full wave. A sample has no header and no end mark. The table entry gives its length. (**Code**)

Sample 0 ends at `$F663`, and sample 1 starts at `$F663`. Sample 1 ends at `$F979`, and sample 2 starts at `$F979`. Thus the samples 0 and 1 share one byte, and the samples 1 and 2 share one byte. Only between entry 2 and entry 3 is there a gap (see [the cut tail](#the-cut-tail-of-sample-2)). (**Code**). The authors cut the samples from one long block of data. (**Conclusion**)

The entries 4 to 7 of the code read `$F550-$F55F`. These 16 bytes and the 32 bytes after them hold values like sample bytes, not offsets. Entry 4 gives the range `$01FD-$4279`, which is no sample. Nothing calls the entries 4 to 7, and no run read `$F550-$F57F`. The code has room for 8 samples, but the game has only 4. (**Observed**, coverage, **Conclusion**)

### The decoder

```
X = 4 * sample number
ptr = $F540 + word(table + X)
end = $F540 + word(table + X + 2)
volume = 15
wait 65 underflows of timer A               ; first count $0040
repeat
    volume = volume XOR 15 ; $D418 = volume
    c = period_lo[mem[ptr]] + 256 * period_hi[mem[ptr]]
    ptr = ptr + 1
    if ptr > end: sfx_done = $FF ; stop
    wait c + 1 underflows of timer A        ; 9 cycles each
```

### A worked example

Entry 0 has the bytes `40 00 23 01`. The start is `$F540 + $0040 = $F580`. The end is `$F540 + $0123 = $F663`. Thus sample 0 has `$F663 - $F580 + 1` = 228 bytes. (**Code**)

The first sample bytes at `$F580` are `0A 35 08 2F`. (**Code**)

| Sample byte | `sfx_period_hi` / `sfx_period_lo` | Count | Cycles `(c + 1) x 9` | Time |
|---|---|---|---|---|
| `$0A` | `$00` / `$0B` | 11 | 108 | 0.11 ms |
| `$35` | `$00` / `$37` | 55 | 504 | 0.51 ms |
| `$08` | `$00` / `$09` | 9 | 90 | 0.09 ms |
| `$2F` | `$00` / `$30` | 48 | 441 | 0.45 ms |

The first full wave takes 612 cycles. This is a frequency of about 1600 Hz. The sum over all 228 bytes is about 0.076 seconds. (**Code**)

## The four samples

The table gives each sample and the event that starts it. The names of the samples come from the events. The time is the sum of the half-waves at the PAL clock of 985248 Hz. (**Code**, the times **Observed** in the render)

| Sample | Entry | Range | Bytes | Time | Event |
|---|---|---|---|---|---|
| 0 | `sfx_play_sample_0` | `$F580-$F663` | 228 | 0.08 s | The opponent gets hit reaction `$16`, the knockdown |
| 1 | `sfx_play_sample_1` | `$F663-$F979` | 791 | 0.46 s | The opponent gets hit reaction `$1A` or `$1B`, or the bull hits the fighter |
| 2 | `sfx_play_sample_2` | `$F979-$FCD3` | 859 | 0.36 s | A fighter starts an attack move |
| 3 | `sfx_play_sample_3` | `$FED3-$FFDD` | 267 | 0.18 s | A fighter reaches frame `$28` or `$2C`, the pose on the floor, or the bull starts a run |

Listen to the samples in these WAV files:

- Sample 0, the knockdown: [sample0_knockdown.wav](assets/sample0_knockdown.wav)
- Sample 1, the hit: [sample1_hit.wav](assets/sample1_hit.wav)
- Sample 2, the attack: [sample2_attack.wav](assets/sample2_attack.wav)
- Sample 3, the floor: [sample3_floor.wav](assets/sample3_floor.wav)

The callers are in the hit test and in the move code. [`hit_record` `$2CA8`](../src/hit_test.asm#L175) sets the hit reaction of the opponent and then starts sample 0 or sample 1. [`move_start_anim` `$2B46`](../src/fighter_moves.asm#L263) starts sample 2 when the new move has `move_attack_flags` not 0. [`move_hit_fall_sample` `$29E9`](../src/fighter_moves.asm#L36) starts sample 3. The bull round starts sample 1 at `$13B7` and sample 3 at `$141F`. The bull round is on [bull_round.md](bull_round.md), and the hit reactions are on [combat.md](combat.md). (**Code**)

The runs executed the entries 0 to 3 and read each byte of the four samples. They did not execute the entries 4 to 7. (**Observed**, coverage)

[`../../tools/sample_to_wav.py`](../../tools/sample_to_wav.py) made the WAV files from the image of the SCC release. It uses the same count tables and the same `(c + 1) x 9` cycles as the player. It also adds the half-wave of the end byte, and it leaves out the first wait of `$0040`. Each of the two differences is less than 1 ms. The script does not include the END address. Thus END is the last byte + 1. This command makes sample 0, from the group folder:

```
python3 tools/sample_to_wav.py v2/original/releases/scc/image.bin 0xf580 0xf664 0xc700 0xc800 v2/docs/assets/sample0_knockdown.wav
```

A second run of the script with the ranges of the table gave the same bytes as each of the five WAV files. (**Observed**)

### The cut tail of sample 2

The data has a gap of 511 bytes between sample 2 and sample 3. [`sfx_sample_attack_cut` `$FCD4`](../src/sfx_samples_f979.asm#L116) holds the bytes `$FCD4-$FED2`, and no table entry covers them. No run read them. (**Observed**, coverage)

The bytes continue sample 2. They have the same range of values (`$1A-$35`) as the end of sample 2. Sample 3 starts with other values at `$FED3`. The end offset of entry 2 is `$0793`, and the start offset of entry 3 is `$0993`. The two offsets have the same low byte, and the high bytes differ by 2. (**Code**)

Thus sample 2 first went to `$FED2`, 1370 bytes and about 0.54 seconds. Then a person changed the high byte of its end offset from 9 to 7. This cut 512 bytes from the end of the sound, but nothing removed the bytes from memory. (**Conclusion**)

[sample2_attack_uncut.wav](assets/sample2_attack_uncut.wav) plays sample 2 with the 511 cut bytes, `$F979-$FED2`. It takes 0.54 seconds. (**Observed**, render)

## Samples in the floor bitmap

The samples are in the screen bitmap. The bitmap is at `$E000-$FF3F` in VIC bank 3. Bitmap row 17 starts at `$E000 + 17 x 320 = $F540`. Thus the table and the samples up to `$FF3F` fill the floor, the rows 17 to 24 of the bitmap. The last bytes, `$FF40-$FFDD`, are after the end of the bitmap. (**Code**)

The player sees no pattern on the floor. [`floor_colour_fill` `$192F`](../src/init_machine.asm#L50) writes `$77` into the screen RAM and the colour RAM of rows 17 to 24. [`nmi_floor_colour` `$2FF2`](../src/irq_screen_split.asm#L44) sets the background colour to 7 at the floor. Thus all four multicolour values of a floor cell are 7, yellow. Each bit pattern shows as the same yellow area. (**Code**)

The scene unpacker writes only the scene bitmap at `$E640-$F53F`. Thus no scene writes over the samples. In version I, the bull sprites had this place in the floor bitmap. Version II moved the bull to other memory and put the samples there. (**Code**, **Conclusion**)

## The DEL key

DEL switches the samples off and on. [`title_key_del` `$1ED4`](../src/title_and_scene.asm#L72) changes `samples_off` with `EOR #$01`. It does this only when `in_game` is 0. The title loop and the demo have `in_game` = 0, and a game sets it to 1. Thus DEL works on the title and in the demo. During a game, the code ignores DEL. The start-up code sets `samples_off` to 0, so the samples are on after a load. (**Code**)

`samples_off` stops only new samples. `sfx_sample_start` is the only code that reads it. A sample that plays when the player presses DEL continues to its end byte, at most 0.46 seconds. When the samples are off, the bull round also calls a sample entry that does nothing. The round continues normally, because `sfx_done` keeps the value `$7F`. (**Code**)

The music does not read `samples_off`. DEL has no effect on the music. (**Code**)

## Samples and music together

Each sample start clears all SID registers in the loop `sfx_clear_sid_loop` at `$31C5`. This also clears the frequency, the waveform and the gate bit of the three music voices. The driver writes the waveform and the gate only at the start of a note. Thus each music voice is silent from the sample start to its next note. The player hears a short break in the music at each hit and each attack. (**Code**, **Conclusion**)

The two players also share `$D418`. The sample IRQ writes only 0 or 15, with the filter mode bits 0. The music driver writes `music_volume` to `$D418` in each frame. Thus the music changes the level of the sample one time in each frame. The sample removes the filter mode of the music until the next frame. (**Code**, **Conclusion**)

The frame-end raster IRQ [`irq_frame_end` `$30E5`](../src/irq_screen_split.asm#L177) calls the music driver with the I flag set. A timer B IRQ must wait until the driver ends. The half-wave at that time becomes longer, one time in each frame. (**Code**, **Conclusion**)

## Still open

- **The sound of each sample.** The names of the samples come from their events. No person listened to the WAV files and the game together to tell a shout, a hit or a fall. A run with a breakpoint at `$3186` in a one-player game, and a listening test, can tell.
- **The cut tail.** Does the sound of sample 2 continue without a break into `$FCD4-$FED2`? Write `$09` to `$F54B`, play sample 2 in the emulator, and compare with sample2_attack_uncut.wav.
- **The break in the music.** How long is the break after a sample start, and does the filter mode loss give a sound that a player hears? Log the writes to `$D418` at `$09B7` and at `$3121`, and record the SID output during a bout.
- **The delay in the frame-end IRQ.** How many cycles does the music driver add to one half-wave? Measure the cycles from the timer B underflow to the write at `$3121` during `irq_frame_end`.
- **The end of tune 4.** Confirm in a run that tune 4 stops after 384 frames and that the name entry continues without music.
