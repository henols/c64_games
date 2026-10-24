# The music and the sound

Hover Bovver plays two tunes on the SID voices 1 and 2. A short jingle plays before the title logo and before each turn. The main tune plays almost all the rest of the time, also during the play. The title credits the musical arrangements to James Lisney. The raster interrupt plays the tunes, so the music continues while the game code waits in its delay loops. Voice 3 makes all sound effects: the mower, the dog and the tones of the end screens.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one raster interrupt at line 0: 50 each second on a PAL C64, 60 on an NTSC C64.
- A *tune step* is one step of the tune player. It comes every 3 frames (`music_speed` = 3).
- An *entry* is 2 bytes of a voice: the duration in tune steps and the note number.
- A *note number* is an index into the note table, 0-60. Note 0 is C1, and each number is one semitone higher.
- A *pass* is one run of the main loop. A *tick* of the sound effects comes every 16 passes.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

[`install_interrupts` `$8076`](../src/irq/interrupts.asm#L6) points the IRQ vector to `irq_handler` and the NMI vector to `nmi_handler`. It starts the raster interrupt at line 0, sets the tempo to 3 and the volume to 15. The tune flag `music_playing` starts at 0, so no tune plays yet (**Code**).

~~~mermaid
flowchart TB
  A["Interrupt"] --> B{"Raster interrupt?"}
  B -->|no| K["KERNAL handler at $EA31"]
  B -->|yes| C["Line 0 again, acknowledge"]
  C --> D{"Tune flag set?"}
  D -->|no| K
  D -->|yes| E{"Tempo counter at 0?"}
  E -->|no| K
  E -->|yes| F["Message timer"]
  F --> G["Voice 1: next entry when its time ends"]
  G --> H["Voice 2: next entry, or the end of the tune"]
  H --> K
~~~

[`irq_handler` `$80C0`](../src/irq/interrupts.asm#L44) does these steps (**Code**):

1. An interrupt that is not the raster interrupt goes directly to the KERNAL handler at `$EA31`.
2. The raster interrupt sets line 0 again and acknowledges the interrupt.
3. When `music_playing` is 0, the handler ends. The message timer then stops too.
4. It decrements `music_tick`. When the counter is not 0, the handler ends. At 0, it loads `music_speed` again and makes one tune step.
5. It decrements `message_timer`. At 0, it clears the message row 21.
6. `tune_voice1` decrements `voice1_duration`. At 0, it adds 2 to `voice1_ptr`, closes the gate and reads the next entry. A note gets its frequency from the note table. Then the gate opens with a sawtooth wave, `$21`, unless the music is off.
7. `tune_voice2` does the same for voice 2. The note `$FF` sets `music_playing` to 0 and ends the tune.
8. All paths end in the KERNAL handler at `$EA31`.

The code does not stop the CIA timer interrupt. Thus the KERNAL handler still runs and scans the keyboard, and the game reads the keys from `LSTX` and `SHFLAG` (**Code**).

[`nmi_handler` `$80BF`](../src/irq/interrupts.asm#L41) is one RTI. RESTORE thus does nothing. The events run pressed RESTORE during the play and continued to the high-score entry (**Observed**).

The tempo is 3 frames for each tune step on both machines. A PAL C64 thus plays 16.7 tune steps each second, and an NTSC C64 plays 20. The music plays 17% slower on PAL (**Conclusion**).

## The tune data

The tunes are at `$6000-$63BF`. Voice 1 reads from `$6000-$61FF`, voice 2 from `$6200-$63BF`. Each entry has 2 bytes (**Code**):

| Byte | Value | Meaning |
|---|---|---|
| 0 | 1-255 | The duration of the entry in tune steps. 0 gives 256 steps. |
| 1 | 0-60 | A note number. The gate opens with the frequency of the note. |
| 1 | `$F0` | A rest. The gate stays closed. |
| 1 | `$FF` | Voice 2 only: the end of the tune. Voice 1 has no end mark. |

The player adds 2 to the pointer before it reads an entry. The code that starts a tune thus sets each pointer to the entry before the first note. The entries at `$6000` and `$6200` never play: `$03,$1B` and `$04,$1A` (**Code**).

| Tune | Voice | Start pointer | First entry | Last entry | End |
|---|---|---|---|---|---|
| Jingle | 1 | `$6000` | `$6002` | `$6032` | none |
| Jingle | 2 | `$6200` | `$6202` | `$622C` | `$622E` |
| Main tune | 1 | `$6032` | `$6034` | `$61EA` | none |
| Main tune | 2 | `$622E` | `$6230` | `$63BC` | `$63BE` |

The two tunes share two entries. `tune2_voice1` at `$6032` is the last note of the jingle in voice 1, C4 for 12 steps. It is also the start pointer of the main tune, so the main tune never plays it. `tune2_voice2` at `$622E` is the end mark of the jingle, `$01,$FF`, and the start pointer of voice 2 of the main tune (**Code**).

Voice 2 sets the length of a tune. In both tunes the two voices have the same length (**Code**):

- The jingle has 96 tune steps. At step 97, voice 2 reads its end mark. On the same step, voice 1 reads `$6034` and opens the gate for C5, the first note of the main tune. The main tune plays this note again at its start.
- The main tune has 1057 tune steps. At step 1058, voice 1 reads the rest `$F0,$F0` at `$61EC`, and voice 2 reads its end mark. 18 bytes of `$FF` fill the rest of the voice 1 block.

Thus the jingle takes 5.8 seconds on PAL and 4.8 seconds on NTSC. The main tune takes 63.4 seconds on PAL and 52.9 seconds on NTSC (**Conclusion**). The durations in the data are 1, 2, 3, 4, 6, 9, 10, 12, 14 and 16 steps. The notes go from 19 (G2) to 57 (A5) (**Code**).

## The two tunes

[`play_jingle_and_wait` `$8236`](../src/music/tune_start.asm#L6) starts the jingle from `$6000` and `$6200`. Then it waits until the interrupt clears `music_playing`. `title_screen` and `player_turn_intro` call it. The jingle starts with E4 F4 G4 E4 over D4 C4 and ends on C3 in voice 2 (**Code**).

[`restart_tune_if_ended` `$8259`](../src/music/tune_start.asm#L28) starts the main tune from `$6032` and `$622E`, but only when no tune plays. Most wait loops of the game call it (**Code**):

- `attract_check_fire` in the title, the walk and the high-score screen.
- The key delay of the setup screen.
- `main_loop_delay`, one time in each pass of the main loop.
- The walks of the borrow scene, the catch of Gordon and the scroll of the lawn.
- The joystick wait of `enter_initials`.

Thus the main tune starts again almost at once when it ends (**Conclusion**). The title is an exception. `title_walk_scene` waits until the main tune ends, and only then the high-score screen follows (**Code**).

## The note table and its NTSC values

[`note_freq_lo` `$8184`](../src/music/note_frequencies.asm#L6) holds the low bytes and [`note_freq_hi` `$81C2`](../src/music/note_frequencies_81c2.asm#L6) the high bytes of 61 SID frequencies. The byte `$81C1` between the tables is not used. The player reads both tables with the note number in X (**Code**).

| Note | Name | Value | NTSC Hz | PAL Hz | Equal temperament Hz |
|---|---|---|---|---|---|
| 0 | C1 | `$0218` | 32.67 | 31.48 | 32.70 |
| 19 | G2 | `$0647` | 97.96 | 94.37 | 98.00 |
| 36 | C4 | `$10C3` | 261.58 | 251.99 | 261.63 |
| 40 | E4 | `$151F` | 329.61 | 317.53 | 329.63 |
| 48 | C5 | `$2187` | 523.21 | 504.04 | 523.25 |
| 57 | A5 | `$3863` | 879.95 | 847.70 | 880.00 |
| 60 | C6 | `$430F` | 1046.49 | 1008.14 | 1046.50 |

The SID gives the frequency value x clock / 16777216. With the NTSC clock of 1022727 Hz, all 61 values are within 3 cents of equal temperament. Thus the table is an NTSC table (**Code**).

A PAL C64 has a clock of 985248 Hz, 3.7% slower. The same value thus gives a lower note. On PAL each note plays about 0.65 semitone flat, between the written note and the semitone below it (**Conclusion**). Together with the slower tempo, a PAL C64 plays the music lower and slower than an NTSC C64.

## The envelopes

`game_init` sets the envelopes one time at the start. Voices 1 and 2 have attack 0, decay 9, sustain 0 and release 0. Voice 3 has attack 3 and decay 9. The filter is off (**Code**).

Each note of a tune thus starts at full volume and decays toward silence. The gate closes at the next entry, and release 0 ends the rest of the sound at once (**Conclusion**).

`lawn_complete_sound` changes the envelope of voice 3 to attack 0 and decay 13 for its sweeps. At the end it writes attack 0 and decay 9, not the attack 3 of the start. After the first finished lawn, voice 3 thus has attack 0 until the next reset (**Code**).

`install_interrupts` also copies the value of `$D011` into the control register of voice 3. Each sound effect writes that register again before it plays (**Code**).

## The music on and off key

C= and M turn the music on and off during the play. [`check_keys` `$9D0B`](../src/input/keys.asm#L6) runs at each tick of `sound_key_tick`, every 16 passes of the main loop. It reads the C= bit of `SHFLAG` and the key code in `LSTX` (**Code**):

| Keys | Key code | Action |
|---|---|---|
| C= and M | `$24` | `music_off` = `music_off` EOR `$FF`. Then it waits until the key is up. |
| C= and P | `$29` | Pause. It waits until the key is up, then until any key is down. |

`music_off` does not stop the player. The player still reads the entries and writes the frequencies, but it does not open the gates. Thus the tune continues in silence, and the message timer still runs. When the music comes on again, the tune continues at its current place (**Code**).

The keys work only in the main loop, so the title and the setup screen do not read them. `start_game` sets the music on at the start of each game. The pause stops the main loop, but not the interrupt, so the tune plays on during the pause (**Code**).

The keys run pressed C= and M during the play. Later it pressed C= and P, then Q to end the pause, and then C= and M again (**Observed**).

## The sound effects on voice 3

The tunes use only voices 1 and 2. All effects use voice 3, so the music on and off key has no effect on them (**Code**). The effects of the play run at the ticks of [`sound_key_tick` `$9327`](../src/sound/sound_tick.asm#L6). The effects of the end screens run in their own delay loops (**Code**).

| Effect | Wave | Pitch (high byte of the frequency) | Code |
|---|---|---|---|
| The mower mows | noise `$81` | Starts at `$FF` on each mown square, then one lower at each tick until 0 | `overload_step_up`, `sound_key_tick` |
| The mower starts again after it cools | noise `$81` | As the mower noise | `mower_cooling` |
| The mower overheats, or Gordon touches Rover | triangle `$11` | Follows the colour of sprite 0, which changes at each tick | `gordon_hits_dog`, `sound_key_tick` |
| Rover attacks | sawtooth `$21` | Rising steps from `$08` to `$1C`, one at each tick, then a random pause | `dog_attack_sound` |
| The lawn is complete | sawtooth `$21` | 6 rising sweeps, while background colour 2 changes | `lawn_complete_sound` |
| WELL DONE! flashes | sawtooth `$21` | Follows the colour counter of the text, 32 falling sweeps | `lawn_complete` |
| Canine fidelity bonus | triangle `$11` | Rises from 1 to `$14` for each step of DOG LOYALTY | `fidelity_bonus` |
| GAME OVER | sawtooth `$21` | Falls from `$40` to 1 for each row | `game_over_tone` |
| The player stores an initial | triangle `$11` | 6 rising sweeps from 1 to `$40` | `enter_initials` |

The mower noise and the dog share the voice. While Rover attacks, `overload_step_up` does not start the mower noise, and `sound_key_tick` plays the dog (**Code**). [`dog_attack_sound` `$9698`](../src/sound/dog_sound.asm#L6) opens the gate again at each step, so the attack sounds like short barks. The pause after each bark comes from the raster register `$D012` AND `$1F` (**Code**).

## A worked example

These are the first entries of the jingle. The interrupt reads the note number as an index. For note `$28` it reads `$81AC` in the low table and `$81EA` in the high table (**Code**).

| Address | Bytes | Steps | Note | Value | NTSC Hz | Tune steps |
|---|---|---|---|---|---|---|
| `$6002` | `03 28` | 3 | 40, E4 | `$151F` | 329.6 | 1-3 |
| `$6004` | `03 29` | 3 | 41, F4 | `$1660` | 349.2 | 4-6 |
| `$6006` | `03 2B` | 3 | 43, G4 | `$191E` | 392.0 | 7-9 |
| `$6008` | `03 28` | 3 | 40, E4 | `$151F` | 329.6 | 10-12 |
| `$6202` | `06 26` | 6 | 38, D4 | `$12D1` | 293.6 | 1-6 |
| `$6204` | `06 24` | 6 | 36, C4 | `$10C3` | 261.6 | 7-12 |

Thus voice 1 plays four short notes over two long notes of voice 2. Each tune step is 3 frames, so each short note lasts 9 frames, 0.18 seconds on PAL (**Conclusion**).

## Still open

- The NTSC table suggests that the music came from an NTSC machine, for example the Atari 8-bit version. A comparison with the tune data of the Atari version can show it.
- The entries `$03,$1B` at `$6000` and `$04,$1A` at `$6200` never play. They can be a leftover of an older start of the jingle. The Atari version can show it.
- No checkpoint of the keys run compares the gate bits of the SID after C= and M. A checkpoint after the key can show that the gates stay closed.

The reference has each routine: [interrupts](reference/modules/irq/interrupts.md), [tune start](reference/modules/music/tune_start.md), [tune data](reference/modules/music/tune_data.md), [note table](reference/modules/music/note_frequencies.md), [keys](reference/modules/input/keys.md), [sound tick](reference/modules/sound/sound_tick.md), [dog sound](reference/modules/sound/dog_sound.md).
