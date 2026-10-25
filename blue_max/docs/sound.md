# The music and the sound

Blue Max plays one tune with three SID voices. The tune plays on the title screen, and again on the rank screen after a complete mission. The title gives the credit "MUSIC PROGRAMMED BY STEPHEN C BIGGS". In play, the SID makes the engine sound and the sound effects of the guns, the bombs, the explosions and the service. This page tells how the music player reads the tune. It also tells why the note table fits an NTSC C64, and when each sound effect plays.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one raster interrupt: 50.1 each second on a PAL C64, 59.8 on an NTSC C64.
- A *tick* is one step of the music player. It comes every 3 frames.
- An *entry* is 2 bytes of a voice: the note byte and the duration in ticks.
- An *even frame* is a frame on which the frame interrupt runs the game routines (`frame_odd` = 1). It comes every second frame.
- The *effect lock* is the timer `sfx_timer`. While it is not 0, the gun, the bomb whistle and the bomb burst do not start on voice 2.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

Two interrupts own the SID. On the title screen, [`title_irq` `$758D`](../src/irq/title_irq.asm#L6) calls the music player one time in each frame. In play, [`irq_frame` `$456D`](../src/irq/frame_irq.asm#L6) writes the engine sound on even frames, and the game routines start the sound effects. After a complete mission, the frame interrupt also calls the music player (**Code**).

~~~mermaid
flowchart TB
  A["Title screen: start the tune (sound_init)"] --> B["Title interrupt: one call of the player each frame"]
  B --> C{"Tune at its end?"}
  C -->|no| B
  C -->|yes| D["Demo mode starts"]
  E["Game start: engine on (engine_sound_start)"] --> F["Frame interrupt: engine pitch on even frames"]
  F --> G["Game routines: effects on voices 2 and 3"]
  G --> F
  F --> H["Mission complete: start the tune again"]
  H --> I["Rank screen: the frame interrupt calls the player"]
~~~

The three voices have these jobs (**Code**):

| Voice | Title and rank screen | Play |
|---|---|---|
| 1 | Melody, pulse wave | Engine, pulse wave, filtered |
| 2 | Middle part, pulse wave | Gun, bomb whistle, bomb burst, beeps, the hit tone |
| 3 | Bass, pulse wave | Explosions and hits, noise, filtered |

The music and the play never use the SID at the same time. Thus the player has no code to share a voice with an effect (**Conclusion**).

## The music player

[`sound_init` `$759C`](../src/music/music_player.asm#L6) prepares the SID and the tune. The title screen calls it, and `rank_after_mission` calls it before the rank screen (**Code**):

1. It writes 0 to all SID registers `$D400-$D418`. This also turns the filter off.
2. It sets `music_ended` to 0.
3. It gives each voice attack 3, decay 5, sustain 10 and release 9, and a pulse width of `$0200` (12.5%).
4. It sets the volume to 6 AND `sound_volume`. The section about the volume tells why this is important.
5. It sets the three voice pointers to `tune_voice1`, `tune_voice2` and `tune_voice3`, and the three durations to 0.
6. It loads the tick counter from `music_tempo`.
7. It calls `copy_d100_table`, which copies the identity table of the loader to `$1000`. The page [protection.md](protection.md) tells about this table.

The last step hides a copy protection step in the sound code. A cracker who removes the music start also removes the table copy (**Conclusion**).

[`music_play` `$7620`](../src/music/music_player.asm#L51) runs one time in each frame. It counts `music_tempo_count` down, and makes one tick when the counter goes below 0 (**Code**):

~~~mermaid
flowchart TB
  A["Count the tempo counter down"] --> B{"Below 0?"}
  B -->|no| Z["Return"]
  B -->|yes| C["Load the counter: tempo - 1"]
  C --> D["Voice 1: duration 0? Read the next entry"]
  D --> E{"Duration byte 0?"}
  E -->|yes| F["End of the tune (music_end)"]
  E -->|no| G["Voices 2 and 3: the same"]
  G --> H["Write the three frequencies"]
  H --> I["New entry: write gate off, then the wave"]
  I --> J["Count the three durations down"]
~~~

1. The counter starts at 3 and returns to 2 after each tick. The first tick thus comes after 4 frames, and the next ticks every 3 frames.
2. For each voice with a duration of 0, it reads the next entry. A duration byte of 0 ends the tune at once.
3. A note byte with bit 7 set is a rest. The wave value is then `$40`, pulse with the gate off.
4. Other note bytes give a note. The player reads the frequency of the note from the note table and shifts it right for the octave. The wave value is `$41`, pulse with the gate on.
5. It adds 2 to the pointer of the voice.
6. It writes the frequencies of all three voices to the SID.
7. For each voice with a new entry, it writes `$40` and then the wave value. Each note thus starts a new attack.
8. It counts the three durations down by 1.

`music_end` sets `music_ended` to `$FF` and returns. It does not write the SID and does not count the durations down. Thus each later tick reads the same end entry again, and the voices stay silent (**Code**).

Only voice 1 can end the tune in practice. All three voices have 912 ticks, and the player reads voice 1 first. The end code of voices 2 and 3 never ran in a run (**Observed**: coverage).

## The tune data

The tune is at `$77FE-$7B61`, directly after the note table. Each voice has its own list of entries (**Code**):

| Byte | Value | Meaning |
|---|---|---|
| 0 | `$00-$7F` | A note. Bits 4-6 are the octave 0-7. Bits 0-3 are the note 0-11, C to B. |
| 0 | `$80` | A rest. The gate closes. |
| 1 | 1-255 | The duration in ticks. |
| 1 | 0 | The end of the tune. Byte 0 is then also 0. |

| Voice | Start | Range | Entries | Rests | Ticks | Notes |
|---|---|---|---|---|---|---|
| 1 | `tune_voice1` | `$77FE-$7927` | 148 | 57 | 912 | D4 to E5 |
| 2 | `tune_voice2` | `$7928-$7A2D` | 130 | 55 | 912 | G#3 to B4 |
| 3 | `tune_voice3` | `$7A2E-$7B61` | 153 | 66 | 912 | A1 to A3 |

Voice 1 plays the melody, voice 2 a middle part and voice 3 the bass (**Conclusion**). The notes are C#, D, D#, E, F#, G#, A and B. The durations are 1, 2, 3, 4, 6, 8, 9, 10, 12, 14, 16, 18, 24 and 28 ticks. In each voice, all notes but one start on a multiple of 4 ticks (**Code**).

Many notes have a short rest after them, for example 6 ticks of note and 2 ticks of rest. The pair then fills a time of 4, 8, 16 or 24 ticks. Thus the composer gave each note a short gap, and the rests do not show pauses in the music (**Conclusion**).

## When the tune plays

On the title screen, `title_screen` calls `sound_init` and then sets the title interrupt at line `$FA`. The title waits in `title_screen_wait` until bit 7 of `music_ended` is 1. Then it sets `demo_mode` to 1 and starts the demo (**Code**). The demo recording left the title alone, and the demo started and flew the plane (**Observed**).

The tune takes 4 + 912 × 3 = 2740 frames from `sound_init` to its end. This is 54.7 seconds on PAL and 45.8 seconds on NTSC (**Code**). The tempo is a count of frames. Thus a PAL C64 plays the tune 16% slower than an NTSC C64 (**Conclusion**).

On the title screen, F1 shows the options, and the music credit text replaces the copyright line. The tune continues, because the title interrupt calls the player in each frame (**Code**).

After a complete mission, `rank_after_mission` calls `sound_init` and sets `music_on` to 1. The frame interrupt then calls `music_play` at its end, also while the game is frozen on the rank screen. After a crash, `rank_after_crash` does not start the tune, so the rank screen of a crash is silent (**Code**). Fire on the rank screen starts a new game, and `game_start` sets `music_on` to 0 again (**Code**).

## The note table and its NTSC values

[`note_freq_lo` `$77E5`](../src/music/music_player.asm#L265) holds the low bytes and [`note_freq_hi` `$77F1`](../src/music/music_player.asm#L267) the high bytes of 12 SID frequencies. They are the notes C7 to B7, the highest octave of the player. For a lower octave, the player shifts the value right 7 − octave times (**Code**).

| Note | Value | NTSC Hz | PAL Hz | Equal temperament Hz |
|---|---|---|---|---|
| C7 | `$861E` | 2093.0 | 2016.3 | 2093.0 |
| E7 | `$A8FA` | 2637.0 | 2540.3 | 2637.0 |
| A7 | `$E18F` | 3520.0 | 3391.0 | 3520.0 |
| B7 | `$FD2E` | 3951.0 | 3806.2 | 3951.1 |

The SID gives the frequency value × clock / 16777216. With the NTSC clock of 1022727 Hz, all 12 values are within 0.1 cent of equal temperament with A4 = 440 Hz. Thus the table is an NTSC table (**Code**).

A PAL C64 has a clock of 985248 Hz, 3.7% slower. On PAL each note thus sounds 65 cents flat, about two thirds of a semitone (**Conclusion**). The right shift drops the low bits, so the lower octaves are a little lower again. A1 gives `$0386`, 54.99 Hz on NTSC in place of 55 Hz (**Code**).

Together with the tempo, a PAL C64 plays the tune lower and slower than an NTSC C64. The author thus tuned the music on an NTSC machine (**Conclusion**).

## The volume and the silent title after the demo

The SID volume of the tune is 6 AND `sound_volume`. The variable has three values, and each one comes from a different place (**Code**):

~~~mermaid
stateDiagram-v2
  state "$FF: tune at volume 6" as Cold
  state "$1F: tune at volume 6" as Game
  state "$00: tune silent" as Demo
  [*] --> Cold: cold start
  Cold --> Game: key on the title, or a game starts
  Cold --> Demo: the demo starts
  Game --> Demo: the demo starts
  Demo --> Game: key on the title, or a game starts
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| none | The program starts | `$FF` | `cold_start` |
| `$FF` or `$00` | A function key on the title | `$1F` | `title_screen` |
| any | A game starts, `demo_mode` = 0 | `$1F` | `engine_sound_start` |
| any | A game starts, `demo_mode` = 1 | `$00` | `engine_sound_start` |

`engine_sound_start` writes `$1F` to the SID volume register and to `sound_volume`: volume 15 and the low-pass filter. In demo mode it then writes 0 to both. Thus the demo is silent (**Code**).

The demo ends at the rank screen of its crash, or with F7, and the program returns to the title. `restart_title` does not set `sound_volume` again. Thus `sound_init` sets the volume to 6 AND 0 = 0, and the second title tune is silent. The next demo is silent too (**Code**). A key on the title sets `sound_volume` to `$1F`, but the title does not write the SID volume again. The sound returns only when a game starts (**Conclusion**).

The pause writes 0 to the SID volume and shows GAME IN PAUSE. Fire continues the game and writes `sound_volume` back to the SID (**Code**).

## The engine sound

[`engine_sound_start` `$7B94`](../src/sound/sound_effects.asm#L35) starts the engine on voice 1 when a game starts and at each take-off after a service. It sets a pulse width of `$0100` (6.25%), attack 0, decay 0, sustain 3 and release 0, and opens the gate with the pulse wave. It also sets resonance 15 and the filter on voices 1 and 3, with the cutoff high byte `$3C` (**Code**).

[`engine_sound` `$7B62`](../src/sound/sound_effects.asm#L6) runs on each even frame. It sets the frequency of voice 1 to `$0232` + speed + 2 × altitude. On the runway at speed 0 and altitude 1 this gives `$0234`, 33 Hz on PAL. At speed 200 and altitude 80 it gives `$039A`, 54 Hz. Thus the engine hums higher when the plane flies faster or higher (**Code**).

The engine stops in two cases (**Code**):

- The fuel is empty. The frame interrupt writes 0 to the control register of voice 1.
- The plane crashes. `update_crash` writes 0 to the control register of voice 1 in each frame.

## The sound effects

The effects use voices 2 and 3. Voice 3 plays the explosions, always with the noise wave and the low-pass filter. Voice 2 plays the short effects without the filter. Most routines write only the high byte of the frequency (**Code**).

| Effect | Routine | Voice and wave | Pitch (high byte) | Attack, decay | Effect lock |
|---|---|---|---|---|---|
| Small explosion | `sound_explosion_small` | 3, noise | `$10` | 6, 12 | — |
| Large explosion | `sound_explosion_large` | 3, noise | `$10` | 6, 13 | — |
| Hit | `sound_noise_hit` | 3, noise | `$64` | 6, 10 | — |
| Plane hit | `sound_plane_hit` | 3 large explosion, and 2 sawtooth | `$0F` | 8, 8 | 10 |
| Double explosion | `sound_explosion_double` | 3 small explosion, and 2 noise | `$28` | 4, 12 | 10 |
| High beep | `sound_beep_high` | 2, triangle | `$64` | 6, 10 | 17 |
| Low beep | `sound_beep_low` | 2, triangle | `$32` | 6, 10 | 17 |
| Gun | `sound_gun` | 2, noise | `$28` | 0, 0 | waits for 0 |
| Bomb whistle | `sound_bomb_drop` | 2, sawtooth, sustain 3 | `$A4` + bomb height | 0, 0 | 48, waits for 0 |
| Bomb burst | `sound_bomb_impact` | 2, noise | `$28` | 1, 1 | waits for 0 |

The game starts the effects at these events (**Code**):

| Event | Effect |
|---|---|
| A bullet flies | Gun |
| The plane drops a bomb | Bomb whistle |
| A bomb makes a crater, or a bullet hits a ground object | Hit |
| A flak shell explodes | Hit |
| A bomb destroys a building, a bridge, an airfield part or another object | Large or small explosion, by the object |
| A road vehicle crashes | Small explosion |
| Three bullets destroy a 2×2 ground object | Double explosion |
| A bomb of the runway attacker explodes | Large explosion |
| A bullet shoots down the enemy plane | Large explosion |
| A shell hits the plane, or the enemy plane touches it | Plane hit |
| The plane crashes, at crash timer `$B3` | Large explosion |
| The first row of an airfield comes | High beep |
| A bomb hits a special target | Large explosion and high beep |
| The service fills the fuel, fills the bombs, or repairs one damage | Low beep |
| A bomb ends on the ground | The whistle stops |

### The effect lock

`engine_sound` counts `sfx_timer` down by 1 on each even frame. A lock of 17 thus lasts 34 frames, and the bomb whistle lock of 48 lasts 96 frames. The beeps and the plane hit write the lock without a test. The gun, the whistle and the burst start only when the lock is 0 (**Code**). Thus a beep or a hit is more important than the gun on voice 2 (**Conclusion**).

### The gun

[`sound_gun` `$7CE2`](../src/sound/sound_effects.asm#L200) runs in each frame while a bullet flies. It starts a short noise click on the frames with bit 1 of `frame_count` clear. With attack, decay, sustain and release all 0, each click is very short. The gun thus makes a fast rattle while the player holds fire (**Code**). While a bomb falls, the lock of the whistle stops the gun sound (**Conclusion**).

### The bomb whistle

[`sound_bomb_drop` `$7D06`](../src/sound/sound_effects.asm#L218) opens voice 2 with the sawtooth wave and sets `bomb_whistle_on` to 1. Then `engine_sound` writes `$A4` + `bomb_height` to the high byte of the frequency on each even frame. The bomb falls 1 unit in each frame, so the whistle falls in pitch until the bomb lands. `end_bomb` calls `sound_bomb_stop`, which writes 0 to the control register of voice 2 (**Code**).

The highest altitude is about 89, because the plane cannot go above sprite line `$5B` and its shadow stays at line `$B4` or below. The fall height is the altitude − 6, so a bomb falls for at most about 84 frames (**Code**). The lock of the whistle lasts 96 frames. Thus the lock is still not 0 when a bomb hits tile `$01`, and the noise of `sound_bomb_impact` does not play. No run executed this noise code (**Observed**: coverage). The burst can play only when the whistle did not start, for example after a beep shortly before the drop (**Conclusion**).

### The wind and the old beep

`update_wind` calls `sound_nothing` when the wind starts. This routine is only an RTS (**Code**). The wind perhaps had a sound in an earlier build (**Conclusion**). The development leftover `debug_beep` plays a short triangle tone on voice 1, but nothing calls it. The page [development.md](development.md) tells about it.

## A worked example

These are the first entries of the three voices. The note byte `$44` gives octave 4 and note 4, E. The player reads `$A8FA` from the note table and shifts it right 3 times: `$547D`, `$2A3E`, `$151F` (**Code**).

| Address | Bytes | Note | Value | NTSC Hz | PAL Hz | Ticks |
|---|---|---|---|---|---|---|
| `$77FE` | `44 06` | E4 | `$151F` | 329.6 | 317.5 | 1-6 |
| `$7800` | `80 02` | rest | — | — | — | 7-8 |
| `$7802` | `49 0C` | A4 | `$1C31` | 439.9 | 423.8 | 9-20 |
| `$7928` | `80 08` | rest | — | — | — | 1-8 |
| `$792A` | `44 18` | E4 | `$151F` | 329.6 | 317.5 | 9-32 |
| `$7A2E` | `80 08` | rest | — | — | — | 1-8 |
| `$7A30` | `39 08` | A3 | `$0E18` | 219.9 | 211.9 | 9-16 |
| `$7A32` | `38 08` | G#3 | `$0D4E` | 207.6 | 200.0 | 17-24 |

Thus the tune starts with one E4 in voice 1. At tick 9 the three voices play A4, E4 and A3 together. Tick 9 comes 28 frames after `sound_init`, 0.56 seconds on PAL (**Conclusion**).

## Still open

- No run measured the length of the tune. A run that counts the frames from `sound_init` until `music_ended` is `$FF` can confirm the 2740 frames of the code.
- The silent title after the demo is from the code only. A run that leaves the title alone until the demo ends, and then reads `sound_volume`, can show it.
- No run reached the special target hit, the shot at the enemy plane, the runway attacker bomb or the double explosion. A run that writes the game variables can reach them and show the effect lock.
- No run made a bomb burst after a beep. A run that drops a bomb on tile `$01` soon after the airfield beep can show the burst noise.
- The Atari 8-bit version of Blue Max can show if the tune came from that version. A comparison of its tune data can show it.

The reference has each routine: [music player](reference/modules/music/music_player.md), [sound effects](reference/modules/sound/sound_effects.md).
