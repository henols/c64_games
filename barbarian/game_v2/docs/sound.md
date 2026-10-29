# Sound and music (Part 2, V 05 10 87)

Barbarian has music and sound effects, but it plays only one of the two. The key F3 selects the music or the effects. In music mode, a three-voice tune of about six minutes plays and loops through the demo and the game. In effects mode, the swings, the hits, the head, the goblin and Drax have sounds. In effects mode, the walk-in of each bout and the goblin also play parts of the music. Two CIA 1 timer interrupts run the sound driver, so the sound does not depend on the frames. The driver data has 114 tunes, 63 instruments and 16 filter settings. This page is about build V 05 10 87. The driver and its data are the same as in build V 05 05 87. Only the driver variables in the zero page are 1 byte higher. (**Code**)

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge of `game_v2`.
- A *frame* is one PAL screen, 1/50 of a second. A *pass* is one run of `main_loop`.
- A *music tick* is one interrupt of CIA 1 timer B. In a music tick, the driver reads the tune data. The *tempo* sets the count of music ticks in each second.
- An *effects tick* is one interrupt of CIA 1 timer A, about 98.5 each second on PAL. In an effects tick, the driver steps the effects and writes the SID.
- A *voice* is voice 0, 1 or 2 of the driver. Voice X of the driver is SID voice X+1.
- A *tune* is a byte stream with a number `$00-$71`. A *request* `$80`+n in `sound_request`,x starts tune n on voice X. A *pattern* is a tune that another tune calls with the command `$F7`.
- *Music mode* and *effects mode* are the two settings of F3. Bit 7 of `sound_off` is set in music mode and clear in effects mode.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The driver has two parts on two timers. [`irq_handler` `$94FE`](../src/irq/irq_handler.asm#L6) runs the raster routine first and then reads the CIA 1 flags. For timer B it calls [`music_tick` `$9941`](../src/music/tick.asm#L6), and for timer A it calls [`effects_tick` `$9EBC`](../src/sound/sid.asm#L38). (**Code**)

[`restart` `$800E`](../src/init/init.asm#L11) starts the two timers in effects mode. Timer A gets the latch `$2710`, 10000 cycles. Timer B gets `$5161`, 20833 cycles, until the first tempo command of a tune. In music mode, the restart does not touch the timers and the sound. Thus the music continues through a restart. (**Code**)

~~~mermaid
flowchart TB
  A["CIA 1 timer B: music tick (music_tick)"] --> B["Voices 2, 1, 0: start a waiting request"]
  B --> C{"Note time of the voice is 0?"}
  C -- "yes" --> D["Read commands up to a note or a rest"]
  C -- "no" --> E["Next voice"]
  D --> E
  E --> F["Count the note times, gate off at 0"]
  F --> G["Step the volume fade"]
  H["CIA 1 timer A: effects tick (effects_tick)"] --> I{"Music tick busy?"}
  I -- "no" --> J["Count the effect delays"]
  J --> K["Effects of each voice, filter sweep"]
  K --> L["Copy the SID shadow to $D400-$D418"]
~~~

`music_tick` does these steps in this order:

1. **It sets `music_tick_busy`.** The effects tick does nothing while this flag is set. (**Code**)
2. **It starts the requests.** For voice 2, 1 and 0, a request with bit 7 set goes to [`start_sound_request` `$9E27`](../src/music/requests.asm#L6). This routine stops the note and the effects of the voice, and the filter sweep. It sets the read offset to 0. (**Code**)
3. **It reads the tune data.** A voice reads when bit 7 of `voice_tune` is set and its note time is 0. A byte below `$C0` is a note for [`start_note` `$99B4`](../src/music/tick.asm#L68). A byte of `$C0` or more goes to [`music_command` `$9A37`](../src/music/commands.asm#L6). (**Code**)
4. **It counts the notes.** [`count_note_lengths` `$9C81`](../src/music/note_time.asm#L17) decrements the note time of each voice. At 0, it clears the gate bit in the SID shadow. It also decrements the fade delay. (**Code**)
5. **It steps the fade.** [`update_volume_fade` `$9E68`](../src/music/requests.asm#L40) changes `master_volume`. Then `music_tick` writes `master_volume` into the volume bits of the shadow of `$D418` and clears `music_tick_busy`. (**Code**)

The commands take no time. After a command, the voice reads the next byte in the same tick. Only a note, a rest and the end command stop the read of the voice until its next tick. (**Code**)

`effects_tick` does nothing while `music_tick_busy` is set. Else it decrements the effect delay of each voice and the filter delay. Then [`update_effects` `$9CB9`](../src/sound/effects.asm#L6) steps the effects of each voice, and [`update_filter_sweep` `$9DC2`](../src/sound/effects.asm#L148) steps the filter sweep. Last, [`copy_sid_shadow` `$9EB1`](../src/sound/sid.asm#L29) copies all 25 bytes of the shadow at `$31-$49` to `$D400-$D418`. (**Code**)

Except `init_sound`, only the effects tick writes the SID. The music tick writes only the shadow. Thus a note of the music tick reaches the SID at the next effects tick, about 10 ms later. (**Code**)

`irq_handler` executes `CLI` before it calls `music_tick`. Thus a timer A interrupt can come during the music tick. The inner handler finds `music_tick_busy` set and returns. It also writes its CIA flags into `cia1_icr_copy`. After `music_tick`, the outer handler reads that copy and calls `effects_tick`. Thus the late effects tick runs and is not lost. (**Code**)

### The note time and the gate

`start_note` sets the frequency, the pulse width and the gate. It also loads the note time from the note length of the voice. `count_note_lengths` runs in the same tick, so the gate is on for the note length minus 1 tick. In the last tick of the note, the gate is off and the release starts. The next note sets the gate again. (**Code**)

A rest (`$F0`) loads the note time but sets no gate. A note length of 1 tick would clear the gate before an effects tick copies it to the SID. The smallest entry of `note_lengths` is 3 ticks, so this does not occur. (**Code**)

`start_note` also starts the effect phases of the voice and the filter sweep from its start cutoff. The filter sweep is one sweep for all three voices. Thus a note on any voice starts the filter sweep again. (**Code**)

## Music or effects (F3)

`start` writes 0 to `sound_off`, so the game starts in effects mode. [`read_keys` `$93A7`](../src/input/keyboard.asm#L6) reads F3 in each pass. F3 calls `stop_sound`, changes bit 7 of `sound_off` and starts a fade-in. With bit 7 set after the change, F3 also requests `$80`, `$81` and `$82` on the three voices. These are tunes `$00-$02`, the start of the music. (**Code**)

`start_sound_request` drops each request of `$83` and higher while bit 7 of `sound_off` is set. Thus music mode has no effects. In effects mode, no code requests `$80-$82`, so the music plays only in the parts that the walk-in and the goblin request. (**Code**)

Thus bit 7 of `sound_off` set means "music on, effects off", in spite of the name (**Conclusion**).

~~~mermaid
stateDiagram-v2
  state "Effects mode (bit 7 clear)" as Fx
  state "Music mode (bit 7 set)" as Mu
  [*] --> Fx: start
  Fx --> Mu: F3, requests $80-$82
  Mu --> Fx: F3, stop_sound
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| (cold start) | - | Effects mode | `start` |
| Effects mode | F3 pressed | Music mode | `read_keys` |
| Music mode | F3 pressed | Effects mode | `read_keys` |

The two modes change these parts of the game (**Code**):

| Part | Effects mode | Music mode |
|---|---|---|
| Requests `$83` and higher | Start their tunes | Dropped |
| Start of a walk-in | Requests `$89-$8B` when voice 0 is free | No request, because the music keeps voice 0 busy |
| End of a walk-in | `stop_sound`, then a fade-in | Nothing |
| `restart` (quit to the demo) | New timers, `init_sound`, fade-in | Timers and music continue |

In the keys recording, F3 acts two times in the demo. In this recording, the driver reads tunes `$00-$02` and their first patterns. The recording has no goblin, so only the music mode of F3 can read these tunes (**Observed**, coverage). The recording then stops in the pause of F5, so the later keys have no effect (**Observed**, key reads).

No recording of this build executed the drop of a request in music mode. In the keys recording, no effect came in the music part of the demo (**Observed**, coverage).

## The tune requests

A routine requests a tune with a write of `$80`+n into `sound_request`,x. The next music tick starts tune n on voice X. A new request on a voice stops the tune that plays on that voice. (**Code**)

[`apply_hit_damage` `$8858`](../src/combat/hits.asm#L112) reads the high nibble of byte 2 of the hit record. It selects a sound triplet in [`hit_sounds` `$C889`](../src/combat/hit_tables.asm#L230). A 0 byte in the triplet does not change the request of that voice. (**Code**)

[`animate_fighter` `$897F`](../src/fighter/animate.asm#L32) compares the move and its step with seven pairs, and requests the sound of [`swing_sounds` `$C8D4`](../src/combat/hit_tables.asm#L259) on voices 0 and 1. (**Code**)

| Request | Tune | Voices | Code | When |
|---|---|---|---|---|
| `$80`, `$81`, `$82` | `$00-$02` | 0, 1, 2 | `read_keys` | F3 selects the music |
| `$89`, `$8A`, `$8B` | `$09-$0B` | 0, 1, 2 | `update_walk_in` | Walk-in, while voice 0 is free |
| `$89`, `$8A`, `$8B` | `$09-$0B` | 0, 1, 2 | `check_final_goal` | The barbarian walks back to the princess |
| `$D4`, `$D5`, `$D6` | `$54-$56` | 0, 1, 2 | `goblin_drag_body` | The goblin drags the body, while voice 0 is free |
| `$D7` | `$57` | 0, 1 | `animate_fighter` | Move `$99`, step 2 |
| `$DA`, `$DB`, `$DC` | `$5A-$5C` | 0, 1, 2 | `apply_hit_damage` | Hit sound entry 2: 4 hit records, no damage, no defender move |
| `$DD` | `$5D` | 0, 1 | `animate_fighter` | Moves `$89`, `$8B`, `$8E`, `$85` at step 0, move `$87` at step 2 |
| `$DD` | `$5D` | 0, 1, 2 | `final_stage_attack` | Drax throws a bolt |
| `$DE` | `$5E` | 0, 1 | `animate_fighter` | Move `$83`, step 0 |
| `$DF` | `$5F` | 0 | `run_sprite_script` | Motions 1, 2 and 6 of sprite 0, the head |
| `$E1` | `$61` | 0, 1 | `apply_hit_damage` | Hit sound entry 3: 2 records with defender move `$88`, the decapitation |
| `$E2` | `$62` | 0 | `goblin_grab_body` | The goblin takes the body |
| `$E9`, -, `$EA` | `$69`, `$6A` | 0, 2 | `apply_hit_damage` | Hit sound entry 1: 32 hit records, the hits with damage |
| `$EB` | `$6B` | 0, 1, 2 | `goblin_reach_sprite0` | The goblin reaches the head, while voice 0 is free |
| `$EE` | `$6E` | 0, 1 | `apply_hit_damage` | Hit sound entry 4: 1 record with defender move `$99` |

`apply_hit_damage` writes the three requests between `SEI` and `CLI`. Thus a music tick cannot start one voice of a triplet before the other voices. (**Code**) No recording executed the `$EB` request (**Observed**, coverage).

**Conclusion.** Entry 2 is probably the sound of a blocked blow, because its records give no damage and no new move to the defender.

### The fade

`fade_in_request` and `fade_out_request` hold a flag in bit 7 and a delay in bits 0-6. `update_volume_fade` changes `master_volume` by 1 after each delay, counted in music ticks. A fade-in stops at 15, and a fade-out stops at 0. Then the routine clears bit 7 of the request. A fade-in comes before a fade-out. (**Code**)

| Code | Fade | Delay | Steps |
|---|---|---|---|
| `restart`, `read_keys` (F3), end of a walk-in | In | `$81`: 1 tick | 15 ticks |
| `stop_sound` | Out | `$81`: 1 tick | 15 ticks |
| `change_scene` | Out, then in | `$84`: 4 ticks | about 60 ticks each |

[`stop_sound` `$94A0`](../src/sound/stop_sound.asm#L6) waits until a fade-in ends. Then it requests a fade-out, waits until the volume is 0 and calls `init_sound`. `init_sound` clears the SID, the shadow, the workspace `$0200-$0259` and 32 bytes of the zero page at `$CF-$EE`. The driver variables are at `$CF-$ED`. (**Code**)

These waits run in the main loop, not in an interrupt. Thus the main loop stops until the fade ends. At tempo 10, a fade of 15 ticks takes 0.42 s, about 21 frames. The fade counts music ticks, so its time depends on the last tempo command. (**Code**)

[`change_scene` `$8E8D`](../src/screen/scene.asm#L6) waits for volume 0 before it swaps the picture. The tunes continue at volume 0 during the swap, and the fade-in then continues them at their new position. (**Code**)

## The data format

### Where the data is

The driver code is at `$9941-$9EDC`, and its tables follow it up to `$A699`. The tunes `$00-$56` are at `$ED80-$FC03`, in the RAM under the KERNAL ROM. The game keeps `$01` at `$25`, so the driver reads this RAM in each interrupt. [`tune_ptrs` `$A193`](../src/music/tunes.asm#L6) holds the start address of each tune. (**Code**)

| Data | Address | Entries |
|---|---|---|
| `freq_table` | `$9EDD-$A05C` | 192 words, the frequency of each pitch |
| `note_lengths` | `$A05D-$A07C` | 16 words, note lengths in music ticks |
| `tempo_latches` | `$A07D-$A09E` | 17 words, timer B latches |
| `music_cmd_bytes`, `music_cmd_handlers` | `$A0A5-$A0C2` | 10 command bytes and 10 handler addresses |
| `filter_setting_ptrs` and the settings | `$A0C3-$A192` | 16 pointers, 16 settings of 11 bytes |
| `tune_ptrs` | `$A193-$A276` | 114 words, tunes `$00-$71` |
| Tunes `$57-$71` | `$A277-$A3A5` | 303 bytes |
| `instruments` | `$A3A6-$A699` | 63 records of 12 bytes |
| Tunes `$00-$56` | `$ED80-$FC03` | 3716 bytes |
| Driver variables | `$CF-$ED`, `$0200-$0259` | Zero page and workspace |

### The tune bytes

A tune is a stream of notes and commands. Each voice keeps a read offset into its tune, a note length and a note time. (**Code**)

| Byte | Arguments | Meaning |
|---|---|---|
| `$00-$5F` | - | Note n: C0 + n semitones. The pitch is 2n. The note uses the note length of the voice. |
| `$60-$BF` | - | Also a note in the code, but 2n does not fit the 192 table entries. No tune uses these bytes. |
| `$C0-$CF` | - | Note length = entry `b AND $0F` of `note_lengths`. |
| `$F0` | - | Rest for one note length. |
| `$F1` | - | Read offset 0, gate off. No tune uses it. |
| `$F2` | - | End: the voice stops. |
| `$F3` | n | Instrument n. |
| `$F4` | a b | Note length = entry a + entry b (low nibbles). |
| `$F5` | n | The voice continues with tune n from its start. |
| `$F6` | n | Tempo: timer B latch = entry n of `tempo_latches`. |
| `$F7` | n | Calls tune n. The voice returns after the `$F7 n`. |
| `$F8` | - | Returns to the calling tune. |
| `$F9` | n | Filter setting n, with this voice through the filter. |
| `$D0-$EF`, `$FA-$FF` | - | No handler. See "Findings in the code". |

The tunes use the notes `$01-$54`, C#0 to C7. [`cmd_call_tune` `$9BC9`](../src/music/commands.asm#L233) saves one return tune and one return offset for each voice. Thus a call has only one level. No pattern calls another tune. (**Code**)

### The note lengths

[`note_lengths` `$A05D`](../src/music/driver_tables.asm#L6) gives 16 lengths in music ticks: 3, 6, 9, 12, 18, 24, 36, 48, 72, 96, 144, 4, 8, 16, 576 and 768. The tunes use entries 0-11. No tune uses entries 12-15. (**Code**)

**Conclusion.** With 12 ticks for a quarter note, entries 0-10 are the note values from a 1/16 note to a dotted breve. The entries 4, 8 and 16 are the triplets of the 1/8, 1/4 and 1/2 notes.

### The tempo

[`tempo_latches` `$A07D`](../src/music/driver_tables.asm#L12) has 17 latch values for CIA 1 timer B. Each value is 1000000 divided by a round tick rate. The tunes use entries 10-16. (**Code**)

| Entry | Latch | Ticks each second at 1 MHz | Ticks each second on PAL | Used by |
|---|---|---|---|---|
| 0-9 | `$F424-$75A8` | 16.0-33.2 | 15.8-32.7 | No tune |
| 10 | `$6B50` | 36.4 | 35.9 | The music, `$61`, `$6B` |
| 11 | `$61A8` | 40.0 | 39.4 | `$5A`, `$6F` |
| 12 | `$57FA` | 44.4 | 43.7 | `$60` |
| 13 | `$4E20` | 50.0 | 49.3 | `$57`, `$5D`, `$5E`, `$6E` |
| 14 | `$444A` | 57.2 | 56.4 | `$5F` |
| 15 | `$3AD4` | 66.4 | 65.4 | `$69` |
| 16 | `$30D4` | 80.0 | 78.8 | `$62` |

The start value of timer B, `$5161` = 20833, also gives a round rate: 48 ticks each second at 1 MHz. The latch `$2710` of timer A gives 100 effects ticks at 1 MHz. (**Code**)

**Conclusion.** The authors calculated the latches with a clock of 1 MHz. On a PAL C64, all ticks are 1.5 % slower.

The tempo is one timer for the three voices. A tune with `$F6` thus changes the speed of each voice that plays. (**Code**)

### The frequency table

[`freq_table` `$9EDD`](../src/music/freq_table.asm#L6) has 192 words, 24 for each octave, for 8 octaves. The even entries are the semitones. Each odd entry is the mean of its two neighbours, about half a semitone. The last entry is `$FFFF`. (**Code**)

The even entries are the NTSC values of the Commodore 64 Programmer's Reference Guide. C0 is `$010C`, and A4, entry 114, is `$1C31`. This gives 439.9 Hz at the NTSC clock, but 423.8 Hz on a PAL C64. Thus each note on PAL is 3.7 % low, about 2/3 of a semitone. The music stays in tune with itself. (**Code**)

A note byte n uses entry 2n. The pitch effect of an instrument adds its step to the pitch, so it can also use the odd entries. (**Code**)

### The instruments

[`instruments` `$A3A6`](../src/music/instruments.asm#L6) holds 63 records of 12 bytes. The command `$F3 n` reads record n at `$A3A6` + 12n. [`cmd_instrument` `$9AB3`](../src/music/commands.asm#L78) writes the envelope and the waveform into the shadow, and keeps the pulse width and the effects for the voice. (**Code**)

| Byte | Meaning |
|---|---|
| 0 | Attack and decay |
| 1 | Sustain and release |
| 2 | Bits 4-7: waveform, `$10` triangle, `$20` sawtooth, `$40` pulse, `$80` noise. Bits 0-3: pulse width bits 8-11, inverted. |
| 3 | Pulse width bits 0-7, inverted |
| 4 | Effect speed: effects ticks from one step to the next |
| 5 | Effect flags |
| 6, 7 | Phase 0: step value and length |
| 8, 9 | Phase 1: step value and length |
| 10, 11 | Phase 2: step value and length |

The code inverts bytes 2 and 3 with `EOR` to get the pulse width. The waveform byte has no gate bit. `start_note` sets the gate. (**Code**)

| Flag bit | Effect | Instruments with the bit |
|---|---|---|
| 7 | The effects are on. | 56 |
| 6 | Pitch step: adds the step value to the pitch. | 17 |
| 5 | Pulse sweep: adds 16 × the step value to the pulse width. | 44 |
| 4 | Frequency slide: adds the step value to the frequency. Bit 7 of the length makes the step negative. | None |
| 3 | After phase 2, phase 0 starts again. Else the effects stop. | 53 |
| 2 | Control `$14`: triangle with ring modulation. | None |
| 1 | Sync bit. | None |

A phase with length L gives L + 1 steps. A phase with length 0 does nothing. The flag values in the records are `$00`, `$A0`, `$A8`, `$C0`, `$C8`, `$E0` and `$E8`. No record uses bits 4, 2 or 1, and no recording executed their code. (**Code**, **Observed** coverage)

Three records set bit 7 but not the loop bit: 24, 47 and 52. In the attract and fight recordings, the effects of a voice stopped after phase 2 (**Observed**, coverage). These recordings read the head tune `$5F`, and no tune of these recordings loads record 24 or 47. **Conclusion:** the pitch bend of the head ran to its end.

The tunes use 58 of the 63 records. No tune uses records 47, 48, 54, 56 and 57. (**Code**)

### The filter settings

[`cmd_filter` `$9C09`](../src/music/commands.asm#L262) reads a setting of 11 bytes through `filter_setting_ptrs`. The SID has one filter, so a setting changes the filter for all voices. (**Code**)

| Byte | Meaning |
|---|---|
| 0 | Sweep speed: effects ticks from one step to the next. 0: no sweep. |
| 1, 2 | Start cutoff, an 11-bit value: high byte, then low byte |
| 3 | `$D417`: resonance in bits 4-7, filter voices in bits 0-3. The driver adds the bit of its own voice. |
| 4 | Filter mode in bits 4-6: `$10` low-pass, `$20` band-pass, `$30` low-pass and band-pass, `$40` high-pass. The driver clears bit 7. |
| 5, 6 | Phase 0: step value (× 8 in the cutoff) and step count |
| 7, 8 | Phase 1 |
| 9, 10 | Phase 2 |

A step value of 1 adds 8 to the 11-bit cutoff, thus 1 to the high byte `$D416`. The cutoff wraps at 11 bits, so `$FF` subtracts 8. In all 16 settings, phases 1 and 2 are 0. After phase 0, the sweep stops, because the step of phase 1 is 0. (**Code**)

The tunes use 14 of the 16 settings. No tune uses settings 0 and 9. (**Code**)

### The decoder

```text
music tick (timer B):
  for voice X = 2 down to 0:
    if request[X] bit 7:
      if sound_off bit 7 and request[X] >= $83: drop it
      else: tune[X] = request[X], offset[X] = 0, stop note, effects and sweep
    if tune[X] bit 7 and note_time[X] = 0:
      loop:
        b = data(tune[X] AND $7F)[offset[X]]
        if b < $C0: pitch[X] = 2b, start_note, next voice
        if b = $C0-$CF: length[X] = note_lengths[b AND $0F], offset += 1, continue
        $F0: note_time[X] = length[X], offset += 1, next voice
        $F2: tune[X] = 0, next voice
        $F7 n: save tune and offset + 2, tune[X] = $80 + n, offset = 0, continue
        $F8: restore tune and offset, continue
        $F5 n: tune[X] = $80 + n, offset = 0, continue
        $F3, $F4, $F6, $F9: do the command, move the offset, continue
  count the note times: at 0, gate off
  count the fade delay, step the fade, volume = master_volume

effects tick (timer A):
  if music tick busy: return
  count the effect delays and the filter delay
  for each voice with effects on and delay 0: one step of the phase
  one step of the filter sweep
  copy the shadow $31-$49 to $D400-$D418
```

## The music

The music has five parts. Each part is a tune for each voice. The tune of a part calls patterns with `$F7` and then goes to the next part with `$F5`. Part 5 goes back to part 1. The tune of voice 0 sets tempo 10 at the start of each part. [`tune_00` `$ED80`](../src/music/tunes_high.asm#L6) is the start of part 1 for voice 0. (**Code**)

| Part | Voice 0 | Voice 1 | Voice 2 | Ticks | Time on PAL |
|---|---|---|---|---|---|
| 1 | `$00` | `$01` | `$02` | 3264 | 91.0 s |
| 2 | `$03` | `$04` | `$05` | 4740 | 132.2 s |
| 3 | `$06` | `$07` | `$08` | 456 | 12.7 s |
| 4 | `$09` | `$0A` | `$0B` | 4752 | 132.5 s |
| 5 | `$54` | `$55` | `$56` | 264 | 7.4 s |

In each part, the three voices have the same length in ticks. Thus the voices stay together through the loop. A full loop is 13476 ticks, 6 minutes and 16 seconds on PAL. (**Code**)

The parts also have other uses (**Code**):

- The walk-in of a bout plays part 4 from its start. In effects mode, the end of the walk-in stops it with `stop_sound`.
- The final stage plays part 4 when the barbarian walks back to the princess.
- [`tune_54` `$FBF0`](../src/music/tunes_high.asm#L591) is the goblin tune, part 5. It plays pattern `$0C` two times on voice 0, and then part 1 starts.

**Conclusion.** After a goblin in effects mode, the music thus continues with part 1. The next walk-in finds voice 0 busy and does not request part 4. At the end of that walk-in, `stop_sound` stops the music.

The recordings read the tunes of parts 1, 4 and 5, but no recording read a tune of parts 2 and 3 (**Observed**, coverage).

## The sound effects

The effect tunes are short. Most of them set their own tempo and filter, and end with `$F2`. (**Code**)

| Tune | Use | Tempo | Ticks | Time on PAL | Instrument |
|---|---|---|---|---|---|
| `$57` | Move `$99` | 13 | 6 | 0.12 s | 46, noise |
| `$5A`, `$5B`, `$5C` | Hit sound entry 2 | 11 | 36 | 0.91 s | 49 and 50, pulse |
| `$5D` | Swings, the bolt of Drax | 13 | 36 | 0.73 s | 51, noise |
| `$5E` | Move `$83` | 13 | 36 | 0.73 s | 51, noise |
| `$5F` | The head | 14 | 9 | 0.16 s | 52, pulse |
| `$61` | The decapitation | 10 | 3 | 0.08 s | 55, noise |
| `$62` | The goblin takes the body | 16 | 138 | 1.75 s | 62, pulse |
| `$69`, `$6A` | A hit with damage | 15 | 9 | 0.14 s | 59, noise |
| `$6B` | The goblin reaches the head | 10 | 9 | 0.25 s | 60, noise |
| `$6E` | Hit sound entry 4 | 13 | 9 | 0.18 s | 30, noise |

The tune `$5D` starts with a rest of 18 ticks, 0.37 s, before its note. The tune `$5E` has no rest. (**Code**)

**Conclusion.** The rest of `$5D` puts the swing sound at the cut of the sword, not at the start of the move.

The instrument 52 of the head has a pitch step of -1 for 8 steps and +1 for 10 steps, without a loop. Thus each bounce of the head sounds as a short bend of the pitch. (**Code**)

Some tunes have no use (**Code**):

- No code requests `$60` and `$6F-$71`. The tunes `$6F`, `$70` and `$71` are a set for three voices, as `$5A-$5C`. Only `$6F` sets the tempo.
- The tunes `$58`, `$59` and `$65-$68` are only the end byte `$F2`.
- No tune uses the command `$F1`. No recording executed its handler `cmd_restart` (**Observed**, coverage).

### Worked example: the sound of a hit

A hit with damage selects hit sound entry 1: `$E9`, `$00`, `$EA`. Voice 0 plays [`tune_69` `$A310`](../src/music/tunes.asm#L85), and voice 2 plays tune `$6A`. Voice 1 keeps its tune. (**Code**)

Tune `$69` has the bytes `F6 0F F3 3B F9 0D C0 F0 C1 21 F2`. (**Code**)

| Bytes | Decoded | Result |
|---|---|---|
| `F6 0F` | Tempo 15 | Timer B latch `$3AD4`, 65.4 ticks each second on PAL |
| `F3 3B` | Instrument 59 | Record at `$A66A`: `08 00 80 00 01 C8 01 01 FF 01 00 00` |
| `F9 0D` | Filter setting 13 | `00 00 80 F5 10 00 00 00 00 00 00` |
| `C0` | Note length entry 0 | 3 ticks |
| `F0` | Rest | 3 ticks, 46 ms |
| `C1` | Note length entry 1 | 6 ticks |
| `21` | Note 33, A2 | Pitch 66, entry 66 = `$070C`, 105.9 Hz on PAL |
| `F2` | End | Voice 0 stops |

The first music tick reads the six bytes up to `F0`, because the commands take no time. The rest ends the read. Three ticks later, the voice reads the note. The gate is on for 5 ticks, 76 ms. Six ticks later, the voice reads `F2`. (**Code**)

Instrument 59 is noise with attack 0 and decay 8, sustain 0 and release 0. Its effect speed is 1, and its flags `$C8` select the pitch step with a loop. Phase 0 adds 1 two times, and phase 1 subtracts 1 two times. Thus the noise pitch moves 66, 67, 68, 67, 66 and again, one step in each effects tick. (**Code**)

Filter setting 13 has no sweep and the cutoff `$080`, thus `$D416` = `$10` and `$D415` = 0. The byte `$F5` gives resonance 15 and the filter on SID voices 1 and 3. The mode `$10` is low-pass. (**Code**)

Tune `$6A` on voice 2 is `F3 3B F9 0D C0 15 C1 0E F2`. It uses the same instrument and filter. It plays note 21, A1, for 3 ticks and note 14, D1, for 6 ticks. It has no tempo command, so it uses the tempo 15 of voice 0. Both voices end after 9 ticks, 0.14 s. (**Code**)

**Conclusion.** A hit is thus a short, low noise through a closed low-pass filter: a thud with a small wobble of the pitch.

## Findings in the code

- **A byte without a handler stops the program.** `music_command` searches 10 command bytes. For a byte `$D0-$EF` or `$FA-$FF`, it finds no handler and returns without a move of the read offset. `music_tick` then reads the same byte again, without an end. The raster interrupt still runs, because the handler executed `CLI`. No tune has such a byte. (**Code**)
- **A test of the goblin tune never succeeds.** [`goblin_drag_body` `$96CD`](../src/story/goblin.asm#L70) loads `voice_tune` OR `sound_request` and skips when bit 7 is set. Then it compares the value with `$D4`. The value has bit 7 clear here, so it is never `$D4`. The bit 7 test does the work alone. (**Code**)
- **The pitch and the tempo are for 1 MHz and NTSC.** The notes are 3.7 % low and the ticks are 1.5 % slow on a PAL C64. (**Code**)
- **The effects share the tempo and the filter.** A new effect sets the timer B latch and the filter for all voices. A note on any voice starts the filter sweep again. (**Code**)
- **The fade stops the main loop.** In effects mode, the end of each walk-in waits for a fade-out of 15 music ticks in `stop_sound`. (**Code**)

The rebuild keeps all these parts, because it must give the bytes of the FLT capture. Build V 05 05 87 has the same parts. (**Code**)

## Changes from V 05 05 87

The sound of build V 05 10 87 is the same as the sound of build V 05 05 87. The page [../../game_v1/docs/sound.md](../../game_v1/docs/sound.md) describes the earlier build. [../../docs/versions.md](../../docs/versions.md) gives all differences between the builds.

- **The same driver and data.** The music and sound modules have the same instructions, tunes, instruments, filter settings and tables in both builds. Only the addresses in the instructions change. (**Code**)
- **The driver moved by +$22.** The driver code starts at `$9941`, not at `$991F`. The tunes `$00-$56` stay at `$ED80-$FC03`. (**Code**)
- **The zero page moved by +1.** The new flag `raster_irq_busy` takes `$CE`. Thus the driver variables move from `$CE-$EC` to `$CF-$ED`, and `init_sound` clears `$CF-$EE`. For example, `sound_request` moves from `$DC` to `$DD`. (**Code**)
- **The callers moved.** `irq_handler` moved by +$16, `read_keys` by +$0C and `apply_hit_damage` by +$13. `hit_sounds` and `swing_sounds` moved by +$41. Their sound code is the same. (**Code**)
- **Other hits.** The hit lists of V 05 10 87 change which poses a blow hits. Thus a hit sound plays for other poses, but the sounds are the same. (**Code**)
- **The pause.** In V 05 10 87, F5 stops the sprites. The CIA 1 timers continue in both builds, so the music continues during the pause. (**Code**)

The recordings of the two builds execute different parts of the driver (**Observed**, coverage):

| Code | V 05 05 87 | V 05 10 87 |
|---|---|---|
| The stop of the effects after phase 2 | not executed | attract, fight |
| The drop of a request in music mode | keys | not executed |

## Still open

- Does an effect during the goblin tune or the walk-in change the speed of the music? Record the SID writes of a decapitation in effects mode.
- Can a player see the stop of the main loop at the end of a walk-in? Compare the frames of the fighters around the end of the walk-in in the `win_bout` recording.
- Why does an instrument hold its pulse width inverted? Compare the driver with other Palace games of 1986 and 1987.
- What were the tunes `$60` and `$6F-$71` for? No code or text names them.
- Parts 2 and 3 of the music never ran in a recording. Record 6.5 minutes in music mode. This shows the full loop and the coverage of instrument 24. It is the only music instrument without the loop bit.
- Does a hit in music mode drop its sound in V 05 10 87? Record a bout in music mode. No recording of this build executed the drop.
