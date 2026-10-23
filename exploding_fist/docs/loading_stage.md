# The loading stage

The original disk of Melbourne House did not start the game at once. While the game files loaded, the loader showed the title picture and played a short speech sample. The four files of this stage are M.PICTURE, M.MYTINY, M.SPCHTBL and M.TSOUND. A fifth file, M.PRERUN, runs just before the game starts. None of these files is part of the game image. The two cracks of the 2010 disk and of SCC kept them. The rebuild of each version does not load these files. Its `build/clean_loader.prg` shows the picture and plays the sample from a capture of this stage, as its start screen. See [The start screen of the rebuild](#the-start-screen-of-the-rebuild).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- The files of the stage are in the knowledge space bank1 of v1. Their source is [v1/src/loading_stage/](../v1/src/loading_stage/main.asm). A name of bank1 has no link. The text gives its space and its address, for example `tsound_irq` in bank1 at `$90CD`.
- A *half-wave* is the time between two flips of the SID volume. A *tick* is one underflow of CIA1 timer A, 9 cycles.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How the original loading stage works

The 2010 crack replaced the protected loader of Melbourne House with a KERNAL loader at `$C000`. That loader uses the original files in this order. The disk layout and the full load list are on [releases.md](releases.md#the-2010-disk-r2010).

~~~mermaid
flowchart TB
  A["Load M.PRERUN and M.PICTURE"] --> B["Copy the picture to VIC bank 3 and show it"]
  B --> C["Load M.MYTINY, M.SPCHTBL and M.TSOUND"]
  C --> D["Call $9000: play the speech sample one time"]
  D --> E["Load M.SHAPES, M.PROG, M.CHSET and M.XSPRITES"]
  E --> F["Call M.PRERUN at $C400"]
  F --> G["Jump to the game entry"]
~~~

1. **The picture.** The loader copies the bitmap from `$6000` to `$E000`, the screen data from `$7F40` to `$CC00` and the colour data from `$8328` to `$D800`. It sets `$DD00` = 0, `$D018` = `$38`, `$D011` = `$3B`, `$D016` = `$18`, `$D021` = 1 and the border colour 3 (**Observed** in the disassembly and a run).
2. **The sample.** The call to `$9000` returns at the end of the sample. The loader loads nothing while the sample plays (**Observed**).
3. **The game.** The loader loads the game files over the sample and part of the picture area. Then it calls `$C400` and jumps to [`v1:program_entry` `$1158`](../v1/src/game/entry_and_tables.asm#L6) (**Observed**).

The sample does not play during the load. It plays one time between the picture and the game files (**Observed**). The original protected loader possibly did the same, because the crackers kept the order of the files (**Conclusion**).

## The title picture: M.PICTURE

M.PICTURE loads at `$6000-$870F`, 10000 bytes. It has the layout of a Koala Painter file without the last byte, the background colour (**Code**). The picture is `picture_bitmap` in bank1 at `$6000`, in [segment_6000.asm](../v1/src/loading_stage/segments/segment_6000.asm#L6).

| Range | Bytes | Meaning | Copy of the loader |
|---|---|---|---|
| `$6000-$7F3F` | 8000 | The multicolour bitmap, 25 rows of 40 cells of 8 bytes | `$E000` |
| `$7F40-$8327` | 1000 | The screen data: colours 1 and 2 of each cell, high nybble and low nybble | `$CC00` |
| `$8328-$870F` | 1000 | The colour data: colour 3 of each cell in the low nybble | `$D800` |

The file has no background byte. Thus the loader writes the background colour itself: `$D021` = 1, white (**Code**).

The high nybbles of the colour data have all 16 values (**Observed** in the bytes of the file). Colour RAM has only 4 bits for each cell, and a read gives random bits in the high nybble. Thus the authors saved the colour data from the colour RAM of a running C64 (**Conclusion**). The VIC-II uses only the low nybble, so the random bits have no effect on the screen (**Code**).

The first 128 bytes of the bitmap are `$55`. In multicolour mode, `%01` in each pixel pair gives colour 1 of the screen data. The first screen byte is `$30`, so the top left cells show colour 3, cyan (**Code**).

This image shows the picture, rendered from M.PICTURE of the 2010 disk.

![The Melbourne House title picture of M.PICTURE](../v1/docs/images/title_picture.png)

## The sample player: M.MYTINY

M.MYTINY loads at `$9000-$910F`. It plays a 1-bit sample through the volume register of the SID. Each byte of the sample gives the length of one half-wave. A CIA timer measures the length, and the IRQ of the timer flips the volume between 0 and 15 (**Code**). The source is [segment_9000.asm](../v1/src/loading_stage/segments/segment_9000.asm#L6) and [segment_9020.asm](../v1/src/loading_stage/segments/segment_9020.asm#L6).

~~~mermaid
flowchart TB
  A["Set the range $2000-$35D6 (tsound_play)"] --> B["Start timer A, timer B and the IRQ (tsound_start_irq)"]
  B --> C["Wait for the end flag (tsound_wait)"]
  C --> D["Put back the IRQ vector (tsound_stop_irq)"]
  E["Timer B IRQ (tsound_irq)"] --> F["Flip the volume, load the next length"]
  F --> G["Set the end flag after the last byte"]
  G -.-> C
~~~

### The call

The entry `tsound_entry` in bank1 at `$9000` is a JMP to `tsound_play` in bank1 at `$9028`. 29 zero bytes follow the JMP, and no code reads them (**Code**). The routine does these steps:

1. It writes the start address `$2000` and the end address `$35D6` into `tsound_start` and `tsound_end` in bank1 at `$9020` and `$9022`. The file holds zero in these bytes (**Code**).
2. It calls `tsound_start_irq` in bank1 at `$9046`. This routine sets up the timers and the IRQ, as the next section tells.
3. It calls `tsound_wait` in bank1 at `$90B2`. That loop reads `tsound_done` until the IRQ writes 1 into it (**Code**).
4. It calls `tsound_stop_irq` in bank1 at `$90B8` and returns to the loader (**Code**).

### The start of the IRQ

[`tsound_start_irq`](../v1/src/loading_stage/segments/segment_9020.asm#L28) prepares the CIA, the SID and the vector with interrupts off (**Code**):

1. It copies the end address into `tsound_end_copy` and the start address into the pointer `$FB/$FC`.
2. It writes `$7F` to `$DC0D`, then `$82`. Only timer B of CIA1 can now give an IRQ. The KERNAL interrupt of timer A stops.
3. It writes 8 into the latch of timer A, `$DC04/$DC05`. A continuous timer with the latch 8 underflows each 9 cycles, so one tick is 9 cycles.
4. It writes 0 to the 29 SID registers `$D400-$D41C` and clears `tsound_done`. It writes 15 into the volume byte `$02`.
5. It writes `$51` to `$DC0E`: timer A starts, loads its latch and runs continuously.
6. It writes `$0101` into the latch of timer B and `$51` to `$DC0F`. Timer B starts and counts the underflows of timer A.
7. It keeps the KERNAL vector `$0314/$0315` in `tsound_saved_irq` and points the vector to `tsound_irq` at `$90CD`.
8. It enables interrupts and clears bit 0 of `$01`. That bit selects the BASIC ROM, so the BASIC ROM is now off.

### The IRQ

The KERNAL sends each timer B IRQ through `$0314` to [`tsound_irq`](../v1/src/loading_stage/segments/segment_9020.asm#L93). The KERNAL entry pushes A, X and Y before the jump. The handler does these steps (**Code**):

1. `BIT $DC0D` reads the interrupt register of CIA1. The read acknowledges the IRQ.
2. It flips the volume byte `$02` with `EOR #$0F` and writes it to `$D418`. The volume changes from 15 to 0, or from 0 to 15.
3. It reads the next sample byte through the pointer `$FB/$FC`.
4. It uses the byte as an index into M.SPCHTBL. It writes `tsound_period_lo` (bank1 `$9800`) to `$DC06` and `tsound_period_hi` (bank1 `$9900`) to `$DC07`.
5. It increments the pointer.
6. It subtracts the pointer from `tsound_end_copy`. When the pointer is higher than the end, it writes 1 into `tsound_done`.
7. It pulls Y, X and A and ends with RTI, as the KERNAL routine at `$EA81` does. The KERNAL clock and the keyboard scan do not run during the sample.

The same steps as pseudo-code:

```text
irq:
    acknowledge CIA1
    volume = volume XOR 15 ; SID volume register = volume
    b = sample[pointer]
    timer B latch = lo[b] + 256 * hi[b]
    pointer = pointer + 1
    if pointer > end: done = 1
    return from interrupt
```

Timer B runs continuously. At its underflow it loads the old latch at once, and then the IRQ writes the new latch. Thus a sample byte sets the length of the half-wave after the next flip, not the half-wave that starts now (**Conclusion** from the CIA behaviour). The delay moves all half-waves by one and does not change the sound (**Conclusion**).

The volume register of the SID changes the DC level of the SID output. The flips of the level give the sound, a square wave with the half-wave lengths of the sample (**Conclusion**).

### The end of the sample

The end compare stops after the byte at `$35D6`, not before it. At the read of `$35D5` the pointer becomes `$35D6`, which is not higher than the end. Thus the player plays 5591 bytes, one more than the 5590 bytes of the sample (**Code**). The IRQ continues until `tsound_stop_irq` puts back the vector. Each IRQ in that time reads one more byte after the end and writes 1 into `tsound_done` again (**Code**).

`tsound_stop_irq` puts back the KERNAL vector and sets bit 0 of `$01`, so the BASIC ROM is on again. It does not stop timer B, and the IRQ of timer B stays enabled (**Code**). Thus the KERNAL IRQ routine runs at each underflow of timer B after the sample, not each 1/60 second (**Conclusion**).

The game has the same player inside. In version I, [`v1:sfx_sample_irq` `$29C8`](../v1/src/sfx/sfx_sample_player.asm#L6) is a copy that never runs, because the game never starts its timer IRQ. In version II, [`v2:sfx_sample_irq` `$311A`](../v2/src/sfx/sfx_sample_player.asm#L6) plays 4 short samples during the fights (**Code**). The details are on [v1/docs/sound_music.md](../v1/docs/sound_music.md) and [v2/docs/sound_music.md](../v2/docs/sound_music.md).

## The count table: M.SPCHTBL

M.SPCHTBL loads at `$9800-$9AFF`, 3 pages. The first two pages are the table of the timer B counts. The name of the file means "speech table" (**Conclusion**). The source is [segment_9800.asm](../v1/src/loading_stage/segments/segment_9800.asm#L6).

| Range | Name | Meaning |
|---|---|---|
| `$9800-$98FF` | `tsound_period_lo` | The low byte of the count for each sample value 0-255 |
| `$9900-$99FF` | `tsound_period_hi` | The high byte of the count for each sample value 0-255 |
| `$9A00-$9AFF` | – | RAM content that no code reads |

The count of entry n follows these rules (**Code**, from the bytes of the table):

| Entry n | Count |
|---|---|
| `$00-$30` | n + 1 |
| `$31-$98` | n + 2. The count `$32` is missing. |
| `$99-$FF` | Larger steps: 156 at `$99`, 400 at `$EA`, 1097 at `$F9`, then 2000, 4000, 8000, 20000, 40000 and 60000 at `$FA-$FF` |

M.TSOUND uses only the values `$04-$EA` (**Observed** in the bytes of the sample). The entries `$EB-$FF` give pauses of up to 0.55 seconds, and this sample does not use them. Thus the table possibly served more samples than this one (**Conclusion**).

The step from n + 1 to n + 2 at `$31` has no effect that a listener can hear. A half-wave of the count `$32` is only one tick of 9 cycles shorter than the count `$33` (**Conclusion**).

The third page holds bytes such as `$80,$FF` and `$00,$3F` in pairs. The table needs only two pages, but the save of the file took three (**Code**). The bytes are RAM content of the computer of the authors (**Conclusion**).

## The sample: M.TSOUND

M.TSOUND loads at `$2000-$35FF`. The sample is `tsound_sample` in bank1 at `$2000`, in [segment_2000.asm](../v1/src/loading_stage/segments/segment_2000.asm#L6). It has 5590 bytes, `$2000-$35D5`. The rest of the file, `$35D6-$35FF`, is not part of the sample. The player reads the byte at `$35D6` also, as [The end of the sample](#the-end-of-the-sample) tells (**Code**). Each byte is the length of one half-wave, as an index into M.SPCHTBL (**Code**).

| Byte | Meaning |
|---|---|
| `$00-$FF` | The index of the count in M.SPCHTBL. The half-wave lasts (count + 1) ticks. |

The first four bytes give this start of the sound. The cycle values use the model of the render tool, (count + 1) × 9 cycles (**Code**):

| Address | Byte | Count | Half-wave |
|---|---|---|---|
| `$2000` | `$D6` | 297 | 2682 cycles |
| `$2001` | `$15` | 22 | 207 cycles |
| `$2002` | `$07` | 8 | 81 cycles |
| `$2003` | `$23` | 36 | 333 cycles |

The counts of the whole sample are 5 to 400, and the mean count is 43 (**Observed** in the bytes). The script [sample_to_wav.py](../tools/sample_to_wav.py) renders the sample as a WAV file with the same model. The render of `$2000-$35D5` lasts 2.23 seconds (**Observed**). The comment of the knowledge on `tsound_sample` gives about 1.8 seconds. The render counts each half-wave, so it is the better value (**Conclusion**).

[loading_sample.wav](../v1/docs/assets/loading_sample.wav) is the render, a 16-bit mono WAV at 44100 Hz. This command makes it from the group folder:

```text
python3 tools/sample_to_wav.py v1/original/releases/2010_loading/image.bin \
    0x2000 0x35d6 0x9800 0x9900 v1/docs/assets/loading_sample.wav
```

## M.PRERUN

M.PRERUN loads at `$C400-$C435`. Its first byte, `prerun_entry` in bank1 at `$C400`, is an RTS. The 2010 loader calls `$C400` just before it jumps to the game. Thus the call returns at once (**Code**). The source is [leftover_c400.asm](../v1/src/loading_stage/leftovers/leftover_c400.asm#L6).

A `JMP $C404` follows the RTS at `$C401`. It goes to `prerun_fill_bar` in bank1 at `$C404`, and no code calls this routine (**Code**). The routine writes `$FF` into the top 4 bytes of each of the 40 cells of bitmap row 5, from `$E640`. It changes the operand of its STA for each cell (**Code**). The bar is 40 cells wide and 4 pixel lines high. The game draws its first scene over this area (**Code**).

The routine possibly drew a bar in an earlier form of the loading stage (**Conclusion**). No fact shows its purpose. The RTS at `$C400` turns it off.

## The start screen of the rebuild

The `build/clean_loader.prg` of each version shows the title picture and plays the speech sample before the game starts. Then it waits for a key, or for the fire button of joystick port 1 or 2. The loader check of c64-source and the run `tests/start_screen.json` show this (**Observed**).

The knowledge of each version holds a capture of the 2010 loading stage in the space `loading`. The capture stops at the call of the sample player at `$9000`, while the picture shows. A coverage run of the call gives the bytes that the sample player needs: the sample, the count table and the player. The show code of the loader calls `$9000`. The call returns at the end of the sample. The game stays packed during the wait, and then it unpacks over the picture (**Code**: `src/start_screen_stage.asm` of each version).

Both versions take the picture from the 2010 release. The SCC picture has the text "CRACKED BY S.C.C.", and M.PICTURE of the 2010 disk has no crack text (**Observed**: byte compare).

The captures of both versions keep all memory of the stage, and their segments are byte-identical. Both versions have the same coverage run of the call, `runs/loading_stage_rc3/` (**Observed**: the capture and the run of 2026-10-21). An earlier capture of version II left out the text screen of the 2010 crack at `$0400-$07E7`. Then the show stage did not fit below `$FFFF`. With c64-re-tools 2.6.0-rc.3, the show stage of each version fits with the full capture (**Observed**: the generate check).

The space `loading` also names the parts of the 2010 crack in the capture. These parts are its text screen, its BASIC start at `$0801`, its loader at `$C000-$C394` and the nine file names in the loader. The text screen reads "SUPPLIED BY 2010 AND CHR.." and "WAIT FOR VERSION II". The start screen does not show it (**Observed**: the capture).

Older captures of the stage stay in space bank1 of each version as history. The loader does not use them.

## The files in the SCC release

The SCC disk of version II has the same three sample files under other names. The files E and F are byte-identical to M.SPCHTBL and M.TSOUND. The last 272 bytes of the file D are byte-identical to M.MYTINY at `$9000-$910F` (**Observed** in a byte compare). The disk layout of SCC is on [releases.md](releases.md#the-scc-disk-scc).

The second stage of the SCC loader, file A, shows the picture with the same register values as the 2010 loader. Then it calls `$9000` at `$C07F` (**Code**, from the bytes of the file A). Thus SCC plays the same sample at the same point of the load (**Conclusion**). The file C holds the picture with the text "CRACKED BY S.C.C." in the top right cells (**Observed**).

## Still open

- What did `prerun_fill_bar` in bank1 at `$C404` do in an earlier loading stage? No file or run shows a caller.
- How long does the sample last on a real machine? A run can count the frames between the call of `$9000` and its return. The IRQ itself takes cycles, so short half-waves are possibly longer than the render model gives.
