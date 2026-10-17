# Bruce Lee: the interrupts and the per-frame work

This page covers the raster interrupt chains of the three screen modes and the per-frame routine of the game screen.

**Scope.**

- The IRQ entry [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry) and the handler vector [`irq_vector`](../src/cold_start.asm#L31) [`$0408`](reference/modules/cold_start.md#irq_vector).
- The raster handlers of the title and game over screen, of the PLAYER n screen and of the game screen.
- The colour splits of the game screen: the split lists and the band palettes of each room.
- [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update): everything that runs once per frame in the game and in the attract demo.
- The timing: frame rate, the pace of the main loop and the length of each countdown.
- Sources: [interrupt_entry.asm](../src/interrupt_entry.asm), [screen_raster_irqs.asm](../src/screen_raster_irqs.asm), [game_irq.asm](../src/game_irq.asm), [frame_update.asm](../src/frame_update.asm), [room_palettes.asm](../src/room_palettes.asm), [game_main_loop.asm](../src/game_main_loop.asm).

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one PAL video frame: 312 raster lines, 19656 CPU cycles, 50 frames per second.
- A *pass* is one run of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop). It lasts at least 3 frames.
- A *line* is a raster line. Text row r of the screen starts at line 51 + 8r.
- A *handler* is a routine that [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry) reaches through [`irq_vector`](../src/cold_start.asm#L31) [`$0408`](reference/modules/cold_start.md#irq_vector).
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.
- The runs of this page: the emulator from the snapshot `entry.vsf` (the cold start) through the title, the attract demo, F7 (the key written into [`key_code`](../src/constants.asm#L137) [`$0109`](reference/variables.md#key_code) with [`key_ready`](../src/constants.asm#L140) [`$010C`](reference/variables.md#key_ready) = 1), the PLAYER 1 screen and room 0; and the snapshot `rooms/room07.vsf`, 300 frames of room 7. Traces of exec points and of writes to the VIC registers gave the raster lines.

## 1. The overview

All interrupts are VIC-II raster interrupts. [`init_game_irq`](../src/play_init.asm#L114) [`$082D`](reference/modules/play_init.md#init_game_irq) turns the CIA 1 and CIA 2 interrupts off. Each handler sets the next raster line, and often the next handler.

~~~mermaid
flowchart TB
  HW["hw_irq_vector $FFFE"] --> E["irq_entry $1103<br/>push A, X, Y"]
  E --> D["irq_dispatch $1113<br/>JMP (irq_vector $0408)"]
  D --> T["title / game over<br/>irq_title_frame $152C<br/>irq_title_split $1574"]
  D --> P["PLAYER n<br/>irq_player_screen $14A4"]
  D --> G["game and demo<br/>irq_game_bottom $48C1<br/>irq_game_playfield $491E<br/>irq_game_colour_split $4982"]
  G --> F["frame_update $15A8"]
  T --> M["music_api_play $E006"]
  N["hw_nmi_vector $FFFA<br/>hw_reset_vector $FFFC"] --> R["nmi_entry $1116<br/>RTI"]
~~~

| Screen mode | Installed by | Handlers in a frame | Music | Per-frame work |
|---|---|---|---|---|
| Title | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) (line 253), [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) (line 130) | [`music_api_play`](../src/music_player_state.asm#L13) [`$E006`](reference/modules/music_player_state.md#music_api_play) | [`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown), [`title_countdown`](../src/constants.asm#L39) [`$0049`](reference/variables.md#title_countdown) |
| Game over | [`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over) | the same as the title (the first IRQ at line 251) | [`music_api_play`](../src/music_player_state.asm#L13) [`$E006`](reference/modules/music_player_state.md#music_api_play) is called; [`lose_fall`](../src/lose_fall_game_over.asm#L14) [`$1818`](reference/modules/lose_fall_game_over.md#lose_fall) has stopped the sound before | the same as the title |
| PLAYER n | [`show_player_screen`](../src/title_player_screens.asm#L71) [`$0EA7`](reference/modules/title_player_screens.md#show_player_screen) | [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) (line 99) | none | [`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown) |
| Game and demo | [`init_game_irq`](../src/play_init.asm#L114) [`$082D`](reference/modules/play_init.md#init_game_irq) | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) (line 253), [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) (line 64), [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) (0-2 times) | none (sound effects only) | [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) |

## 2. The IRQ entry and the vector

[`hw_irq_vector`](../src/hardware_vectors.asm#L77) [`$FFFE`](reference/modules/hardware_vectors.md#hw_irq_vector) points to [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry). The KERNAL ROM is switched out ([`R6510`](../src/constants.asm#L12) [`$0001`](reference/variables.md#R6510) = `$35`), so the CPU reads the vector from RAM. [`hw_nmi_vector`](../src/hardware_vectors.asm#L73) [`$FFFA`](reference/modules/hardware_vectors.md#hw_nmi_vector) and [`hw_reset_vector`](../src/hardware_vectors.asm#L75) [`$FFFC`](reference/modules/hardware_vectors.md#hw_reset_vector) point to [`nmi_entry`](../src/interrupt_entry.asm#L25) [`$1116`](reference/modules/interrupt_entry.md#nmi_entry), an RTI. RESTORE does nothing. **Code**

[`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry):

1. Pushes A, X and Y.
2. Reads the stacked status register (LDA `$0104`,X after TSX) and does `AND #$00` at [`irq_entry`](../src/interrupt_entry.asm#L10) [`$110C`](../src/interrupt_entry.asm#L18). The result is always zero, so the BRK branch (`JMP (io1_dummy)` at [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1110`](../src/interrupt_entry.asm#L21)) never runs. **Code**
3. [`irq_dispatch`](../src/interrupt_entry.asm#L22) [`$1113`](reference/modules/interrupt_entry.md#irq_dispatch) does `JMP (irq_vector)`.

[`irq_vector`](../src/cold_start.asm#L31) [`$0408`](reference/modules/cold_start.md#irq_vector) / [`irq_vector_hi`](../src/cold_start.asm#L32) [`$0409`](reference/modules/cold_start.md#irq_vector_hi) are the two bytes of the `AND #$EF` instruction in [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start). After the cold start the code stores the address of the next handler there. **Code**

| Writer | Value | When |
|---|---|---|
| [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | title setup |
| [`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | game over screen |
| [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) | every title frame |
| [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | every title frame |
| [`show_player_screen`](../src/title_player_screens.asm#L71) [`$0EA7`](reference/modules/title_player_screens.md#show_player_screen) | [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) | PLAYER n screen (the handler keeps itself) |
| [`init_game_irq`](../src/play_init.asm#L114) [`$082D`](reference/modules/play_init.md#init_game_irq) | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) |
| [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) | every game frame |
| [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) | [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) | every game frame |
| [`irq_chain_to_bottom`](../src/game_irq.asm#L108) [`$4975`](reference/modules/game_irq.md#irq_chain_to_bottom) | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | after the last split of the frame |

Each handler ends the same way: it writes 1 to [`IRQMSK`](../src/constants.asm#L182) [`$D01A`](reference/variables.md#IRQMSK) and [`VICIRQ`](../src/constants.asm#L181) [`$D019`](reference/variables.md#VICIRQ) (raster IRQ on, acknowledged), clears bit 8 of the compare line in [`SCROLY`](../src/constants.asm#L175) [`$D011`](reference/variables.md#SCROLY), writes the next line to [`RASTER`](../src/constants.asm#L176) [`$D012`](reference/variables.md#RASTER), and returns with PLA/TAY/PLA/TAX/PLA/RTI. **Code**

## 3. The title and game over screen

| Handler | Line | Sets | Calls | Next |
|---|---|---|---|---|
| [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | 253 (`$FD`) | [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = `$30` (screen [`game_screen`](../src/game_screen.asm#L9) [`$8C00`](reference/modules/game_screen.md#game_screen), charset `$8000` of the logo), [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) = `$18` (multicolour, 40 columns) for the top of the next frame | [`music_api_play`](../src/music_player_state.asm#L13) [`$E006`](reference/modules/music_player_state.md#music_api_play) | [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) at line 130 |
| [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) | 130 (`$82`) | after a short delay: [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = `$32` (charset [`text_font`](../src/text_font.asm#L9) [`$8800`](reference/modules/text_font.md#text_font)), [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) = `$16` (multicolour, 38 columns, x-scroll 6) | none | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) at line 253 |

[`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) also decrements [`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown) and the 16-bit [`title_countdown`](../src/constants.asm#L39) [`$0049`](reference/variables.md#title_countdown). Both stop at 0. **Code**

**Observed.** The first title IRQs came 2 frames after [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen). [`irq_title_split`](../src/screen_raster_irqs.asm#L121) ran at line 130. It wrote [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) at line 130, cycle 62 and [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) at line 131. [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) ran at line 253. It wrote [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) at line 253 and [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) at line 254, then called [`music_api_play`](../src/music_player_state.asm#L13) [`$E006`](reference/modules/music_player_state.md#music_api_play) at line 254.

**Conclusion.** Text row 10 starts at line 131. The logo rows 0-9 (DATASOFT PRESENTS, BRUCE LEE, BY RON J FORTIER) show in the logo charset. The menu rows 10-24 show in the text font. The colour RAM of the menu rows is `$F1` (bit 3 clear: hires), so the menu text is hires although [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) selects multicolour.

[`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over) installs the same pair with a first compare line of 251 (`$FB`). After the first [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) the line is 253 again. **Code**

~~~mermaid
flowchart LR
  A["line 0-130<br/>logo charset $8000<br/>40 columns"] --> B["line 130<br/>irq_title_split $1574<br/>text_font $8800<br/>38 columns, x-scroll 6"]
  B --> C["line 253<br/>irq_title_frame $152C<br/>logo charset for the next frame<br/>music, countdowns"]
  C --> A
~~~

![The title screen](images/screens/title.png)

The title screen: the logo rows above line 130, the menu in the text font below it.

## 4. The PLAYER n screen

[`show_player_screen`](../src/title_player_screens.asm#L71) [`$0EA7`](reference/modules/title_player_screens.md#show_player_screen) fills the screen with the blank logo character `$DC`, copies the big PLAYER 1 or PLAYER 2 banner ([`player_banner_top`](../src/banners.asm#L36) [`$4A5D`](reference/modules/banners.md#player_banner_top)) to rows 7 and 8, and installs [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) at line 99 (`$63`). It waits until [`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown) reaches 0: 64 frames, or 128 frames in a two-player game. The 24-bit counter [`player_screen_wait`](../src/constants.asm#L25) [`$0018`](reference/variables.md#player_screen_wait) ends the wait if the interrupt stops. **Code**

| Handler | Line | Sets | Next |
|---|---|---|---|
| [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) | 99 (`$63`) | waits for line 110 ([`irq_player_screen_sync`](../src/screen_raster_irqs.asm#L13) [`$14A8`](reference/modules/screen_raster_irqs.md#irq_player_screen_sync)); then [`BGCOL1`](../src/constants.asm#L189) [`$D022`](reference/variables.md#BGCOL1) = `$B`, `$C`, `$F`, `$1`, `$F`, `$C`, `$B` (dark grey, grey, light grey, white and back) about every 2 lines with [`delay_raster_line`](../src/screen_raster_irqs.asm#L71) [`$1526`](reference/modules/screen_raster_irqs.md#delay_raster_line); then [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = `$30`, [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) = `$18`; decrements [`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown) | itself at line 99 |

**Observed.** [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) ran at line 99-100 in 64 frames after F7. The writes to [`BGCOL1`](../src/constants.asm#L189) [`$D022`](reference/variables.md#BGCOL1) came at lines 109, 112, 114, 116, 117, 119 and 121. [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) and [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) followed at line 121.

**Conclusion.** Rows 7 and 8 cover lines 107-122. [`BGCOL1`](../src/constants.asm#L189) [`$D022`](reference/variables.md#BGCOL1) is multicolour 1 of the logo charset, so the big letters get a shading from grey to white and back.

~~~mermaid
flowchart LR
  A["line 99<br/>irq_player_screen $14A4<br/>wait for line 110"] --> B["lines 110-121<br/>BGCOL1: B, C, F, 1, F, C, B"]
  B --> C["line 121<br/>VMCSB $30, SCROLX $18<br/>frame_countdown - 1"]
  C --> A
~~~

![The PLAYER 1 screen](images/screens/player_screen.png)

The PLAYER 1 screen with the shaded big text.

## 5. The game screen

The game screen and the attract demo use the same chain. [`reset_play_state`](../src/play_init.asm#L19) [`$0763`](reference/modules/play_init.md#reset_play_state) sets [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = `$38` and [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX) = `$18` one time. No game handler writes [`SCROLX`](../src/constants.asm#L178) [`$D016`](reference/variables.md#SCROLX). **Observed** (no write in a traced game frame).

| Handler | Line | Sets | Next |
|---|---|---|---|
| [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | 253 (`$FD`) | [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = `$32` (screen [`game_screen`](../src/game_screen.asm#L9) [`$8C00`](reference/modules/game_screen.md#game_screen), charset [`text_font`](../src/text_font.asm#L9) [`$8800`](reference/modules/text_font.md#text_font)) and [`BGCOL0`](../src/constants.asm#L188) [`$D021`](reference/variables.md#BGCOL0) = `$FC` (grey) for the status line at the top of the next frame. Copies 12 bytes of the band palette of the room ([`room_palette_ptr`](../src/room_palettes.asm#L75) [`$480B`](reference/modules/room_palettes.md#room_palette_ptr)) to [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours) and the first 4 bytes of the split list of the room ([`room_split_list_ptr`](../src/room_palettes.asm#L82) [`$4833`](reference/modules/room_palettes.md#room_split_list_ptr)) to [`raster_split_lines`](../src/room_palettes.asm#L56) [`$47F5`](reference/modules/room_palettes.md#raster_split_lines). Calls [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update). | [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) at line 64 |
| [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) | 64 (`$40`) | waits until the line is past 65 ([`irq_playfield_wait`](../src/game_irq.asm#L64) [`$4920`](reference/modules/game_irq.md#irq_playfield_wait)) plus a delay; [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = [`room_vmcsb`](../src/constants.asm#L121) [`$00F2`](reference/variables.md#room_vmcsb) (the room charset); [`BGCOL0`](../src/constants.asm#L188) [`$D021`](reference/variables.md#BGCOL0) to [`BGCOL2`](../src/constants.asm#L190) [`$D023`](reference/variables.md#BGCOL2) = band 0 ([`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours)); [`raster_split_index`](../src/constants.asm#L36) [`$0044`](reference/variables.md#raster_split_index) = 0, [`band_palette_offset`](../src/constants.asm#L123) [`$00F4`](reference/variables.md#band_palette_offset) = 3 | [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) at [`raster_split_lines`](../src/room_palettes.asm#L56) [`$47F5`](reference/modules/room_palettes.md#raster_split_lines)[0], or [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) when that is `$FD` |
| [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) | split line r | waits for line r+3 ([`irq_split_wait`](../src/game_irq.asm#L127) [`$4991`](reference/modules/game_irq.md#irq_split_wait)), writes [`BGCOL0`](../src/constants.asm#L188) [`$D021`](reference/variables.md#BGCOL0) to [`BGCOL2`](../src/constants.asm#L190) [`$D023`](reference/variables.md#BGCOL2) from the next 3 bytes of [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours) ([`irq_split_set_colours`](../src/game_irq.asm#L136) [`$49A0`](reference/modules/game_irq.md#irq_split_set_colours)), [`band_palette_offset`](../src/constants.asm#L123) [`$00F4`](reference/variables.md#band_palette_offset) += 3, [`raster_split_index`](../src/constants.asm#L36) [`$0044`](reference/variables.md#raster_split_index) += 1 | the next split line, or [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) when the next entry is `$FD` ([`irq_chain_to_bottom`](../src/game_irq.asm#L108) [`$4975`](reference/modules/game_irq.md#irq_chain_to_bottom)) |

**Observed** (room 0, demo and game, one frame):

| Line | Write |
|---|---|
| 253 | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom): [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = `$32`, [`BGCOL0`](../src/constants.asm#L188) [`$D021`](reference/variables.md#BGCOL0) = `$FC` |
| 254 | [`RASTER`](../src/constants.asm#L176) [`$D012`](reference/variables.md#RASTER) = `$40` |
| 259 | [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) starts |
| 64 | [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) starts |
| 66-68 | [`VMCSB`](../src/constants.asm#L180) [`$D018`](reference/variables.md#VMCSB) = `$38`, then [`BGCOL0`](../src/constants.asm#L188) = `$FB`, [`BGCOL1`](../src/constants.asm#L189) = `$F1`, [`BGCOL2`](../src/constants.asm#L190) = `$FE` |
| 120 | [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) starts (split line `$78`) |
| 123-124 | [`BGCOL0`](../src/constants.asm#L188) = `$FB`, [`BGCOL1`](../src/constants.asm#L189) = `$F2`, [`BGCOL2`](../src/constants.asm#L190) = `$F1` |
| 151 | [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) starts (split line `$97`) |
| 154 | [`BGCOL0`](../src/constants.asm#L188) = `$FC`, [`BGCOL1`](../src/constants.asm#L189) = `$F2`, [`BGCOL2`](../src/constants.asm#L190) = `$F1`; [`RASTER`](../src/constants.asm#L176) [`$D012`](reference/variables.md#RASTER) = `$FD` |

**Conclusion.** Text rows 0-1 (lines 51-66) are the status line in the hires text font on grey. The room starts at text row 2 (line 67), the separator row. The room uses the multicolour room charset. The colour splits change the background and the two multicolours at fixed lines, 3 lines after the split line.

~~~mermaid
flowchart LR
  A["lines 51-66<br/>status line<br/>text_font, BGCOL0 grey"] --> B["line 64<br/>irq_game_playfield $491E<br/>room charset, band 0"]
  B --> C["split lines<br/>irq_game_colour_split $4982<br/>band 1, band 2"]
  C --> D["line 253<br/>irq_game_bottom $48C1<br/>status setup, palette copy"]
  D --> E["line 259<br/>frame_update $15A8"]
  E --> A
~~~

### 5.1 The charset of the play area

[`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) sets [`room_vmcsb`](../src/constants.asm#L121) [`$00F2`](reference/variables.md#room_vmcsb). Room 18 changes it during the wizard defeat ([`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated)). [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) derives [`room_charset_hi`](../src/constants.asm#L77) [`$007C`](reference/variables.md#room_charset_hi) from it every frame. **Code**

| [`room_vmcsb`](../src/constants.asm#L121) | Charset | [`room_charset_hi`](../src/constants.asm#L77) | Rooms |
|---|---|---|---|
| `$38` | [`charset_rooms_0_9`](../src/constants.asm#L157) [`$A000`](reference/variables.md#charset_rooms_0_9) | `$A0` | 0-9 |
| `$3A` | [`charset_rooms_10_19`](../src/constants.asm#L158) [`$A800`](reference/variables.md#charset_rooms_10_19) | `$A8` | 10-17, 19 |
| `$3C` | [`charset_wizard`](../src/constants.asm#L159) [`$B000`](reference/variables.md#charset_wizard) | `$B0` | 18 |
| `$3E` | [`charset_wizard_flash`](../src/constants.asm#L160) [`$B800`](reference/variables.md#charset_wizard_flash) | `$B8` | 18, while the wizard flashes |

### 5.2 The split lists and the band palettes

[`raster_split_lines`](../src/room_palettes.asm#L56) [`$47F5`](reference/modules/room_palettes.md#raster_split_lines) holds the split lines of the current frame. A list ends with `$FD`, the line of [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom). A room with n split lines uses n + 1 records of 3 bytes ([`BGCOL0`](../src/constants.asm#L188), [`BGCOL1`](../src/constants.asm#L189), [`BGCOL2`](../src/constants.asm#L190)) from its band palette. **Code**

| Rooms | Split list | Split lines | Band palette | Bands ([`BGCOL0`](../src/constants.asm#L188)/[`BGCOL1`](../src/constants.asm#L189)/[`BGCOL2`](../src/constants.asm#L190), low nibble) |
|---|---|---|---|---|
| 0, 1, 2 | [`split_list_r0`](../src/room_palettes.asm#L60) [`$47F9`](reference/modules/room_palettes.md#split_list_r0), [`split_list_r1`](../src/room_palettes.asm#L62) [`$47FC`](reference/modules/room_palettes.md#split_list_r1), [`split_list_r2`](../src/room_palettes.asm#L64) [`$47FF`](reference/modules/room_palettes.md#split_list_r2) | `$78`, `$97` (120, 151) | [`room_palette_r0_3`](../src/room_palettes.asm#L29) [`$47C8`](reference/modules/room_palettes.md#room_palette_r0_3) | B/1/E, B/2/1, C/2/1 |
| 3 | [`split_list_r3`](../src/room_palettes.asm#L66) [`$4802`](reference/modules/room_palettes.md#split_list_r3) | `$62`, `$97` (98, 151) | [`room_palette_r0_3`](../src/room_palettes.asm#L29) [`$47C8`](reference/modules/room_palettes.md#room_palette_r0_3) | B/1/E, B/2/1, C/2/1 |
| 4, 5, 6 | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | none | [`room_palette_r4_6`](../src/room_palettes.asm#L33) [`$47D1`](reference/modules/room_palettes.md#room_palette_r4_6) | 6/E/1 |
| 7, 8, 9 | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | none | [`room_palette_r7_9`](../src/room_palettes.asm#L35) [`$47D4`](reference/modules/room_palettes.md#room_palette_r7_9) | 8/9/1 |
| 10, 12, 14, 16 | [`split_list_r10_12_14_16`](../src/room_palettes.asm#L70) [`$4806`](reference/modules/room_palettes.md#split_list_r10_12_14_16) | `$56` (86) | [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37) [`$47D7`](reference/modules/room_palettes.md#room_palette_r10_12_14_16) | 6/E/B, C/E/B |
| 11 | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | none | [`room_palette_r11`](../src/room_palettes.asm#L40) [`$47DD`](reference/modules/room_palettes.md#room_palette_r11) | 4/E/B |
| 13 | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | none | [`room_palette_r13`](../src/room_palettes.asm#L42) [`$47E0`](reference/modules/room_palettes.md#room_palette_r13) | E/6/1 |
| 15 | [`split_list_r15`](../src/room_palettes.asm#L72) [`$4808`](reference/modules/room_palettes.md#split_list_r15) | `$B6`, `$C7` (182, 199) | [`room_palette_r15`](../src/room_palettes.asm#L44) [`$47E3`](reference/modules/room_palettes.md#room_palette_r15) | E/6/B, C/E/1, F/8/C |
| 17 | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | none | [`room_palette_r17`](../src/room_palettes.asm#L48) [`$47EC`](reference/modules/room_palettes.md#room_palette_r17) | C/8/B |
| 18 | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | none | [`room_palette_r18`](../src/room_palettes.asm#L50) [`$47EF`](reference/modules/room_palettes.md#room_palette_r18) | 0/E/4 |
| 19 | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | none | [`room_palette_r19`](../src/room_palettes.asm#L52) [`$47F2`](reference/modules/room_palettes.md#room_palette_r19) | 6/2/1 |

Colours: 0 black, 1 white, 2 red, 4 purple, 6 blue, 8 orange, 9 brown, B dark grey, C grey, E light blue, F light grey.

[`irq_bottom_copy`](../src/game_irq.asm#L42) [`$4904`](reference/modules/game_irq.md#irq_bottom_copy) copies the palette every frame. So the screen saver of [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update), which writes [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours) after the copy, changes the colours of the next frame only. **Code**

## 6. frame_update: the work of each frame

[`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) calls [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) in each frame of the game screen, in the game and in the attract demo. **Observed** at line 259. It runs inside the interrupt, with interrupts disabled. The steps in the order of the code:

1. **Split index.** [`raster_split_index`](../src/constants.asm#L36) [`$0044`](reference/variables.md#raster_split_index) = 0.
2. **Sound effects.** [`sfx_voice1_update`](../src/sfx_voice1.asm#L19) [`$EB03`](reference/modules/sfx_voice1.md#sfx_voice1_update), [`sfx_voice2_update`](../src/sfx_voice2.asm#L19) [`$EF73`](reference/modules/sfx_voice2.md#sfx_voice2_update) and [`sfx_voice3_update`](../src/sfx_voice3.asm#L19) [`$F073`](reference/modules/sfx_voice3.md#sfx_voice3_update), with X = [`room`](../src/constants.asm#L32) [`$0029`](reference/variables.md#room). There is no music in the game screen: only [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) calls [`music_api_play`](../src/music_player_state.asm#L13) [`$E006`](reference/modules/music_player_state.md#music_api_play).
3. **Random pointer.** [`frame_update`](../src/frame_update.asm#L20) [`$15B8`](../src/frame_update.asm#L28) increments [`random_ptr`](../src/constants.asm#L24) [`$0016`](reference/variables.md#random_ptr) (also [`random_byte`](../src/interrupt_entry.asm#L89) [`$1159`](reference/modules/interrupt_entry.md#random_byte) increments it).
4. **Sprites.** [`show_actor_sprites`](../src/actor_sprites.asm#L75) [`$25E2`](reference/modules/actor_sprites.md#show_actor_sprites) writes the positions and colours of the actor sprites.
5. **Fall attack budget.** When [`fall_attack_refill_timer`](../src/actor_workspace.asm#L8) [`$4EEC`](reference/modules/actor_workspace.md#fall_attack_refill_timer) is 0, the three bytes of [`fall_attack_budget`](../src/actor_workspace.asm#L72) [`$4F45`](reference/modules/actor_workspace.md#fall_attack_budget) are set to 2. Then the timer is decremented ([`frame_update_dec_fall_attack_timer`](../src/frame_update.asm#L37) [`$15CD`](reference/modules/frame_update.md#frame_update_dec_fall_attack_timer)): one refill every 256 frames.
6. **Room charset.** [`room_charset_hi`](../src/constants.asm#L77) [`$007C`](reference/variables.md#room_charset_hi) from [`room_vmcsb`](../src/constants.asm#L121) [`$00F2`](reference/variables.md#room_vmcsb) (section 5.1).
7. **Handedness marks.** Status row 1, column 2: `L` (character `$2C`) when joystick 1 is left-handed ([`joystick_right_handed`](../src/room_enemy_tables.asm#L114) [`$1383`](reference/modules/room_enemy_tables.md#joystick_right_handed) = 0), else blank. Column 37: the same for joystick 2 ([`joystick_right_handed+1`](../src/room_enemy_tables.asm#L114) [`$1384`](reference/modules/room_enemy_tables.md#joystick_right_handed)), but only when port 2 is in use ([`option_two_players`](../src/options_and_patterns.asm#L14) [`$42C9`](reference/modules/options_and_patterns.md#option_two_players) or [`option_yamo_player2`](../src/options_and_patterns.asm#L18) [`$42CA`](reference/modules/options_and_patterns.md#option_yamo_player2) set).
8. **Room time.** In a game ([`game_mode`](../src/constants.asm#L134) [`$0104`](reference/variables.md#game_mode) = 1) and not paused ([`pause_state`](../src/constants.asm#L135) [`$0105`](reference/variables.md#pause_state) bit 7 clear): [`room_time`](../src/constants.asm#L86) [`$0087`](reference/variables.md#room_time) + 1. Its high byte stops at `$80`. [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) sets it to 0.
9. **Frame counters and the idle timer.** [`frame_counter`](../src/constants.asm#L79) [`$007F`](reference/variables.md#frame_counter) + 1 ([`frame_update_count_frames`](../src/frame_update.asm#L95) [`$1628`](reference/modules/frame_update.md#frame_update_count_frames)). When it wraps (every 256 frames): [`idle_timer`](../src/constants.asm#L81) [`$0082`](reference/variables.md#idle_timer) + 1 while it is positive, and [`frame_count_256`](../src/constants.asm#L80) [`$0080`](reference/variables.md#frame_count_256) + 1 (16 bit). When [`idle_timer`](../src/constants.asm#L81) [`$0082`](reference/variables.md#idle_timer) reaches `$80`: [`pause_state`](../src/constants.asm#L135) [`$0105`](reference/variables.md#pause_state) = `$86` (paused, debounce 6), [`show_paused`](../src/pause_status_line.asm#L88) [`$1A42`](reference/modules/pause_status_line.md#show_paused) and [`start_screen_saver`](../src/game_setup.asm#L139) [`$102B`](reference/modules/game_setup.md#start_screen_saver).
10. **Screen saver masks.** [`frame_update_saver_masks`](../src/frame_update.asm#L117) [`$1645`](reference/modules/frame_update.md#frame_update_saver_masks): with [`idle_timer`](../src/constants.asm#L81) [`$0082`](reference/variables.md#idle_timer) positive, [`saver_and_mask`](../src/constants.asm#L83) [`$0084`](reference/variables.md#saver_and_mask) = `$FE` and [`saver_eor_mask`](../src/constants.asm#L82) [`$0083`](reference/variables.md#saver_eor_mask) = 0. With [`idle_timer`](../src/constants.asm#L81) negative (saver on): [`idle_timer`](../src/constants.asm#L81) = `$FE`, [`saver_eor_mask`](../src/constants.asm#L82) = [`frame_count_256`](../src/constants.asm#L80), [`saver_and_mask`](../src/constants.asm#L83) = `$F7`, and the 20 bytes of [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours) = ([`palette_backup`](../src/room_palettes.asm#L21) [`$47B4`](reference/modules/room_palettes.md#palette_backup) EOR [`saver_eor_mask`](../src/constants.asm#L82)) AND [`saver_and_mask`](../src/constants.asm#L83).
11. **Protection check 1.** [`frame_update_check_ddr`](../src/frame_update.asm#L140) [`$166A`](reference/modules/frame_update.md#frame_update_check_ddr): [`D6510`](../src/constants.asm#L11) [`$0000`](reference/variables.md#D6510) must hold `$EF`. Else the code branches back to step 9 for ever, inside the interrupt, and the game hangs. The original loader leaves `$EF` there.
12. **Countdowns.** [`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown) - 1 and the 16-bit [`title_countdown`](../src/constants.asm#L39) [`$0049`](reference/variables.md#title_countdown) - 1, both stop at 0 ([`frame_update_dec_countdowns`](../src/frame_update.asm#L156) [`$1672`](reference/modules/frame_update.md#frame_update_dec_countdowns)). In the game screen [`title_countdown`](../src/constants.asm#L39) times the congratulations room ([`room19_init`](../src/ending_room.asm#L7) [`$425F`](reference/modules/ending_room.md#room19_init) sets `$0458`).
13. **Joysticks.** [`frame_update_read_input`](../src/frame_update.asm#L171) [`$1689`](reference/modules/frame_update.md#frame_update_read_input) saves [`CIADDRA`](../src/constants.asm#L230) `$DC02`/[`CIADDRB`](../src/constants.asm#L231) `$DC03` in [`cia1_ddra_save`](../src/actor_step.asm#L617) `$2005`/[`cia1_ddrb_save`](../src/actor_step.asm#L619) `$2006` and makes both CIA 1 ports inputs. In the demo ([`game_mode`](../src/constants.asm#L134) [`$0104`](reference/variables.md#game_mode) = 0) it reads nothing: [`update_actors`](../src/actor_driver_text.asm#L10) [`$179E`](reference/modules/actor_driver_text.md#update_actors) takes Bruce's input from the demo stream. In a game:
    - Bruce: port 1 ([`CIAPRB`](../src/constants.asm#L229) [`$DC01`](reference/variables.md#CIAPRB)) when [`current_player`](../src/constants.asm#L14) [`$0003`](reference/variables.md#current_player) = 0, port 2 ([`CIAPRA`](../src/constants.asm#L228) [`$DC00`](reference/variables.md#CIAPRA)) when it is 1. Bits 0-3 go to [`actor_joy_dir`](../src/constants.asm#L92) [`$0098`](reference/variables.md#actor_joy_dir), fire (bit 4) to [`actor_fire`](../src/constants.asm#L93) [`$009B`](reference/variables.md#actor_fire).
    - A Yamo played by a person ([`option_yamo_player2`](../src/options_and_patterns.asm#L18) [`$42CA`](reference/modules/options_and_patterns.md#option_yamo_player2) = 1): the other port, to [`actor_joy_dir+1`](../src/constants.asm#L92) [`$0099`](reference/variables.md#actor_joy_dir) and [`actor_fire+1`](../src/constants.asm#L93) [`$009C`](reference/variables.md#actor_fire).
    - A left-handed joystick ([`joystick_right_handed`](../src/room_enemy_tables.asm#L114) [`$1383`](reference/modules/room_enemy_tables.md#joystick_right_handed),X = 0) is turned by 90 degrees: new = (old >> 2) OR [`joy_rotate_bits`](../src/room_tables.asm#L8) [`$4A85`](reference/modules/room_tables.md#joy_rotate_bits)[old AND 3]. Up becomes right, down becomes left, left becomes up, right becomes down.
14. **Protection check 2.** [`frame_update_check_loader_mark`](../src/frame_update.asm#L245) [`$1703`](reference/modules/frame_update.md#frame_update_check_loader_mark): [`prot_loader_mark`](../src/constants.asm#L13) [`$0002`](reference/variables.md#prot_loader_mark) must hold `$32`. Else [`frame_update_wipe_loop`](../src/frame_update.asm#L265) [`$170B`](reference/modules/frame_update.md#frame_update_wipe_loop) writes over memory page by page downward. Its page counter is [`frame_update_wipe_counter`](../src/title_demo_start.asm#L37) [`$0539`](reference/modules/title_demo_start.md#frame_update_wipe_counter), a byte of an instruction of [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$0531`](reference/modules/title_demo_start.md#start_attract_demo). The original loader leaves `$32` there.
15. [`frame_update_restore_ddr`](../src/frame_update.asm#L272) [`$1717`](reference/modules/frame_update.md#frame_update_restore_ddr) restores the CIA 1 port directions.
16. **Idle reset.** [`frame_update_reset_idle`](../src/frame_update.asm#L289) [`$173B`](reference/modules/frame_update.md#frame_update_reset_idle) sets [`idle_timer`](../src/constants.asm#L81) [`$0082`](reference/variables.md#idle_timer) = 0 in the demo (always), and in a game when not paused and Bruce's or Yamo's joystick has a direction or fire.
17. **Yamo player idle.** Only in a game, not paused, in a room with enemies ([`room_no_enemy_flag`](../src/constants.asm#L75) [`$007A`](reference/variables.md#room_no_enemy_flag) = 0) and with [`option_yamo_player2`](../src/options_and_patterns.asm#L18) [`$42CA`](reference/modules/options_and_patterns.md#option_yamo_player2) = 1: without input on Yamo's joystick, [`yamo_idle_time`](../src/constants.asm#L87) [`$0089`](reference/variables.md#yamo_idle_time) + 1 per frame; input sets it to 0. At 7 * 256 = 1792 frames Yamo goes back to the computer: [`option_yamo_player2`](../src/options_and_patterns.asm#L18) = 0, [`room_time+1`](../src/constants.asm#L86) [`$0088`](reference/variables.md#room_time) = `$20` (the top time level), [`play_open_sound`](../src/wizard_fireballs.asm#L183) [`$424F`](reference/modules/wizard_fireballs.md#play_open_sound), 5 falls are taken from [`falls_left`](../src/constants.asm#L31) [`$0028`](reference/variables.md#falls_left) and from the parked player ([`inactive_player_state`](../src/fireball_text_score_vars.asm#L96) [`$439F`](reference/modules/fireball_text_score_vars.md#inactive_player_state)), not below 0, and [`show_falls_count`](../src/status_and_keys.asm#L10) [`$1AED`](reference/modules/status_and_keys.md#show_falls_count) redraws the count.

The copy-protection checks are listed with the others on the protection page of this documentation. Both checks of [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) never fail in the clean program with the entry state of the loader. **Observed** (all runs pass them).

### 6.1 The idle timer and the screen saver

~~~mermaid
stateDiagram-v2
  state "Playing: idle_timer $0082 = $00-$7F" as Play
  state "Paused by the player: idle_timer = $51" as Pause
  state "Paused with screen saver: idle_timer = $FE" as Saver
  [*] --> Play
  Play --> Play: input, idle_timer = 0
  Play --> Saver: idle_timer reaches $80
  Play --> Pause: SPACE or fire
  Pause --> Saver: idle_timer reaches $80
  Pause --> Play: SPACE or fire
  Saver --> Play: SPACE or fire
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Playing | joystick input (Bruce or player Yamo), or the demo | Playing, [`idle_timer`](../src/constants.asm#L81) = 0 | [`frame_update_reset_idle`](../src/frame_update.asm#L289) [`$173B`](reference/modules/frame_update.md#frame_update_reset_idle) |
| Playing | 128 * 256 = 32768 frames without input (about 11 minutes) | Paused with screen saver | [`frame_update`](../src/frame_update.asm#L20) [`$1634`](../src/frame_update.asm#L105): [`pause_state`](../src/constants.asm#L135) [`$0105`](reference/variables.md#pause_state) = `$86`, [`show_paused`](../src/pause_status_line.asm#L88) [`$1A42`](reference/modules/pause_status_line.md#show_paused), [`start_screen_saver`](../src/game_setup.asm#L139) [`$102B`](reference/modules/game_setup.md#start_screen_saver) |
| Playing | SPACE ([`handle_game_keys`](../src/status_and_keys.asm#L57) [`$1B29`](reference/modules/status_and_keys.md#handle_game_keys)) or fire of the current player ([`check_pause_fire`](../src/pause_status_line.asm#L53) [`$1A08`](reference/modules/pause_status_line.md#check_pause_fire)) | Paused, [`idle_timer`](../src/constants.asm#L81) = `$51` | [`toggle_pause`](../src/pause_status_line.asm#L69) [`$1A22`](reference/modules/pause_status_line.md#toggle_pause), [`show_paused`](../src/pause_status_line.asm#L88) [`$1A42`](reference/modules/pause_status_line.md#show_paused) |
| Paused | [`idle_timer`](../src/constants.asm#L81) counts on from `$51`: 47 * 256 = 12032 frames (about 4 minutes) | Paused with screen saver | [`frame_update`](../src/frame_update.asm#L20) [`$1630`](../src/frame_update.asm#L102) |
| Paused, or with saver | SPACE or fire | Playing; the saver stops ([`stop_screen_saver`](../src/game_setup.asm#L151) [`$103B`](reference/modules/game_setup.md#stop_screen_saver)) | [`toggle_pause`](../src/pause_status_line.asm#L69) [`$1A22`](reference/modules/pause_status_line.md#toggle_pause) |

While [`pause_state`](../src/constants.asm#L135) [`$0105`](reference/variables.md#pause_state) bit 7 is set, [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) skips the game work, but the interrupt and [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) go on. **Code**

## 7. The timing

| Fact | Value | Evidence |
|---|---|---|
| Video standard | PAL, 50 frames per second, 312 lines, 19656 cycles per frame | **Observed** (the emulator runs PAL; the stopwatch gives 19656 cycles per frame) |
| Frames per handler | one [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) + one [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) per frame; one [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) per frame; one [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) + one [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) + 0-2 [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) per frame | **Observed** |
| A pass of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) | at least 3 frames: it sets [`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown) = 3 and waits at [`main_loop_wait_frame`](../src/game_main_loop.asm#L83) [`$1C32`](reference/modules/game_main_loop.md#main_loop_wait_frame) until the interrupt has counted it to 0 | **Code** |
| Pace in room 0 (demo) and room 7 | a pass starts every 3 frames, at line 264-277, just after [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) of the third frame. In 300 frames of room 7 one pass took 4 frames; the next pass started at once. | **Observed** |
| Passes per second | 50 / 3 = 16.7 when no pass is late | **Conclusion** |
| Cold start to title | [`restart_to_title`](../src/title_demo_start.asm#L9) [`$050F`](reference/modules/title_demo_start.md#restart_to_title) 79 frames after [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start); the first title IRQ 4 frames later | **Observed** |
| Title countdown | [`title_countdown`](../src/constants.asm#L39) [`$0049`](reference/variables.md#title_countdown) = `$0960` = 2400 frames = 48 s, then [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$0531`](reference/modules/title_demo_start.md#start_attract_demo). Each option key restarts it. | **Code**; **Observed**: 2394 frames from a countdown of `$095C` |
| Option message on the title | cleared about 350 frames after the last option key ([`title_menu_check_message_timeout`](../src/title_menu.asm#L37) [`$08E0`](reference/modules/title_menu.md#title_menu_check_message_timeout), countdown `$0801`) | **Code** |
| Start of a game | F7 or fire: wait for the fire release, then 16 frames ([`title_menu_start_game`](../src/title_menu.asm#L52) [`$08FC`](reference/modules/title_menu.md#title_menu_start_game)) | **Code**; **Observed**: [`start_new_game`](../src/title_demo_start.asm#L283) [`$070E`](reference/modules/title_demo_start.md#start_new_game) 15 frames after the key |
| PLAYER n screen | 64 frames (128 in a two-player game) | **Observed**: 64 frames of [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) |
| Attract demo | ends when Bruce is knocked out, about 1714 frames (34 s) after [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$0531`](reference/modules/title_demo_start.md#start_attract_demo), or on fire of port 1 or F1 | **Observed** |
| Game over screen | 254 frames, then 64 more frames before the title ([`game_over_wait`](../src/lose_fall_game_over.asm#L195) [`$1968`](reference/modules/lose_fall_game_over.md#game_over_wait), [`game_over_wait_title`](../src/lose_fall_game_over.asm#L207) [`$197D`](reference/modules/lose_fall_game_over.md#game_over_wait_title)) | **Code** |
| Congratulations room | [`title_countdown`](../src/constants.asm#L39) [`$0049`](reference/variables.md#title_countdown) = `$0458` = 1112 frames (22 s); Bruce's joystick is forced up while [`room_time+1`](../src/constants.asm#L86) [`$0088`](reference/variables.md#room_time) < 2 (512 frames) | **Code** |
| Room time levels | [`room_time+1`](../src/constants.asm#L86) [`$0088`](reference/variables.md#room_time) >= `$19` (6400 frames, 128 s) and >= `$20` (8192 frames, 164 s) make the enemies faster | **Code** |
| Fall attack refill | every 256 frames | **Code** |
| Idle pause | 32768 frames (about 11 minutes) | **Code** |
| Player Yamo time-out | 1792 frames (36 s) | **Code** |

## 8. Still open

- How long [`frame_update`](../src/frame_update.asm#L20) [`$15A8`](reference/modules/frame_update.md#frame_update) takes in the worst case, and which work made the 4-frame pass in room 7. A trace of the raster line at the RTS of [`frame_update`](../src/frame_update.asm#L20) and at [`main_loop_wait_frame`](../src/game_main_loop.asm#L83) [`$1C32`](reference/modules/game_main_loop.md#main_loop_wait_frame) over a long run with all actors can answer it.
- Whether the colour split of room 15 at line 199 shows a visible seam with sprites over it. A screenshot of room 15 with Bruce on the split can answer it.
