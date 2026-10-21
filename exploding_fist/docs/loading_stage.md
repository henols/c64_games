# The loading stage

The original disk of Melbourne House did not start the game at once. While the game files loaded, the loader showed the title picture and played a short speech sample. The four files of this stage are M.PICTURE, M.MYTINY, M.SPCHTBL and M.TSOUND. A fifth file, M.PRERUN, runs just before the game starts. None of these files is part of the game image. The two cracks of the 2010 disk and of SCC kept them. The rebuild of each version plays the same stage from a new boot before it unpacks the game.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- The files of the stage are in the knowledge space bank1 of v1. Their source is [v1/src/loading_stage/](../v1/src/loading_stage/main.asm). A name of bank1 has no link. The text gives its space and its address, for example `tsound_irq` in bank1 at `$90CD`.
- A *half-wave* is the time between two flips of the SID volume. A *tick* is one underflow of CIA1 timer A, 9 cycles.
- *Stage 2* is the packed loader of the game build. *The boot* is the hand-written code that shows the picture and plays the sample in the rebuild.
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
3. **The game.** The loader loads the game files over the sample and part of the picture area. Then it calls `$C400` and jumps to [`v1:program_entry` `$1158`](../v1/src/entry_and_tables.asm#L6) (**Observed**).

The sample does not play during the load. It plays one time between the picture and the game files (**Observed**). The original protected loader possibly did the same, because the crackers kept the order of the files (**Conclusion**).

## The title picture: M.PICTURE

M.PICTURE loads at `$6000-$870F`, 10000 bytes. It has the layout of a Koala Painter file without the last byte, the background colour (**Code**). The picture is `picture_bitmap` in bank1 at `$6000`, in [segment_6000.asm](../v1/src/loading_stage/segment_6000.asm#L6).

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

M.MYTINY loads at `$9000-$910F`. It plays a 1-bit sample through the volume register of the SID. Each byte of the sample gives the length of one half-wave. A CIA timer measures the length, and the IRQ of the timer flips the volume between 0 and 15 (**Code**). The source is [segment_9000.asm](../v1/src/loading_stage/segment_9000.asm#L6).

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

[`tsound_start_irq`](../v1/src/loading_stage/segment_9000.asm#L33) prepares the CIA, the SID and the vector with interrupts off (**Code**):

1. It copies the end address into `tsound_end_copy` and the start address into the pointer `$FB/$FC`.
2. It writes `$7F` to `$DC0D`, then `$82`. Only timer B of CIA1 can now give an IRQ. The KERNAL interrupt of timer A stops.
3. It writes 8 into the latch of timer A, `$DC04/$DC05`. A continuous timer with the latch 8 underflows each 9 cycles, so one tick is 9 cycles.
4. It writes 0 to the 29 SID registers `$D400-$D41C` and clears `tsound_done`. It writes 15 into the volume byte `$02`.
5. It writes `$51` to `$DC0E`: timer A starts, loads its latch and runs continuously.
6. It writes `$0101` into the latch of timer B and `$51` to `$DC0F`. Timer B starts and counts the underflows of timer A.
7. It keeps the KERNAL vector `$0314/$0315` in `tsound_saved_irq` and points the vector to `tsound_irq` at `$90CD`.
8. It enables interrupts and clears bit 0 of `$01`. That bit selects the BASIC ROM, so the BASIC ROM is now off.

### The IRQ

The KERNAL sends each timer B IRQ through `$0314` to [`tsound_irq`](../v1/src/loading_stage/segment_9000.asm#L98). The KERNAL entry pushes A, X and Y before the jump. The handler does these steps (**Code**):

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

`tsound_stop_irq` puts back the KERNAL vector and sets bit 0 of `$01`, so the BASIC ROM is on again. It does not stop timer B, and the IRQ of timer B stays enabled (**Code**). Thus the KERNAL IRQ routine runs at each underflow of timer B after the sample, not each 1/60 second (**Conclusion**). The boot of the rebuild stops timer B itself, as [The boot](#the-boot) tells.

The game has the same player inside. In version I, [`v1:sfx_sample_irq` `$29C8`](../v1/src/sfx_sample_player.asm#L6) is a copy that never runs, because the game never starts its timer IRQ. In version II, [`v2:sfx_sample_irq` `$311A`](../v2/src/sfx_sample_player.asm#L6) plays 4 short samples during the fights (**Code**). The details are on [v1/docs/sound_music.md](../v1/docs/sound_music.md) and [v2/docs/sound_music.md](../v2/docs/sound_music.md).

## The count table: M.SPCHTBL

M.SPCHTBL loads at `$9800-$9AFF`, 3 pages. The first two pages are the table of the timer B counts. The name of the file means "speech table" (**Conclusion**). The source is [segment_9800.asm](../v1/src/loading_stage/segment_9800.asm#L6).

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

M.TSOUND loads at `$2000-$35FF`. The sample is `tsound_sample` in bank1 at `$2000`, in [segment_2000.asm](../v1/src/loading_stage/segment_2000.asm#L6). It has 5590 bytes, `$2000-$35D5`. The rest of the file, `$35D6-$35FF`, is not part of the sample. The player reads the byte at `$35D6` also, as [The end of the sample](#the-end-of-the-sample) tells (**Code**). Each byte is the length of one half-wave, as an index into M.SPCHTBL (**Code**).

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

M.PRERUN loads at `$C400-$C435`. Its first byte, `prerun_entry` in bank1 at `$C400`, is an RTS. The 2010 loader calls `$C400` just before it jumps to the game. Thus the call returns at once (**Code**). The source is [segment_c400.asm](../v1/src/loading_stage/segment_c400.asm#L6).

A `JMP $C404` follows the RTS at `$C401`. It goes to `prerun_fill_bar` in bank1 at `$C404`, and no code calls this routine (**Code**). The routine writes `$FF` into the top 4 bytes of each of the 40 cells of bitmap row 5, from `$E640`. It changes the operand of its STA for each cell (**Code**). The bar is 40 cells wide and 4 pixel lines high. The game draws its first scene over this area (**Code**).

The routine possibly drew a bar in an earlier form of the loading stage (**Conclusion**). No fact shows its purpose. The RTS at `$C400` turns it off.

## The files in the SCC release

The SCC disk of version II has the same three sample files under other names. The files E and F are byte-identical to M.SPCHTBL and M.TSOUND. The last 272 bytes of the file D are byte-identical to M.MYTINY at `$9000-$910F` (**Observed** in a byte compare). The disk layout of SCC is on [releases.md](releases.md#the-scc-disk-scc).

The second stage of the SCC loader, file A, shows the picture with the same register values as the 2010 loader. Then it calls `$9000` at `$C07F` (**Code**, from the bytes of the file A). Thus SCC plays the same sample at the same point of the load (**Conclusion**). The file C holds the picture with the text "CRACKED BY S.C.C." in the top right cells (**Observed**). The rebuild of version II thus uses the clean M.PICTURE of the 2010 disk.

## The rebuild of the loading stage

The game image of each version holds no file of the loading stage. The rebuild adds them in a boot that the user starts with RUN. The boot shows the picture and plays the sample as the 2010 loader does. Then it starts the game build (**Code**). The boot is hand-written. The source generator keeps the files [boot.asm](../v1/src/boot.asm), [boot_bitmap.asm](../v1/src/boot_bitmap.asm) and [boot_stash.asm](../v1/src/boot_stash.asm).

### The two-stage packed file

The release file of each version is one PRG with two packed stages (**Code**):

1. **The outer stage.** The c64-packer joins seven parts into one Exomizer file. It unpacks them to their addresses and jumps to the boot at `$C600`.
2. **Stage 2.** This part is the loader of the game build at `$0801`. It is an Exomizer file itself, and its unpacker starts at `$080D`, `SYS 2061`. It unpacks the game and a copier, and the copier sets the entry state.

The parts of the outer stage are in this load order (**Code**):

| Part | Load address | Content |
|---|---|---|
| `build/fist_vN_loader.prg` | `$0801` | Stage 2 |
| `segment-2000-35ff.prg` | `$2000` | M.TSOUND |
| `segment-9000-910f.prg` | `$9000` | M.MYTINY |
| `segment-9800-9aff.prg` | `$9800` | M.SPCHTBL |
| `build/boot_stash.prg` | `$9B00` | The stash: the bytes of stage 2 under the loading files |
| `build/boot.prg` | `$C000` | The colour data, M.PRERUN, the boot code and the screen data |
| `build/boot_bitmap.prg` | `$E000` | The bitmap of the picture |

The sample and the player must be at their original addresses, because M.MYTINY holds the addresses `$2000`, `$35D6` and `$9800` in its code (**Code**). Stage 2 also uses `$2000-$35FF`. Thus a later part writes over stage 2 there, and the stash keeps the original bytes of stage 2 (**Code**). The files of the loading stage come from `original/releases/2010_loading/` of each project. In v2 these are the 2010 files also, because the SCC picture has the crack text (**Code**).

Each version gives one file. `build/exploding_fist_v1.prg` has 44508 bytes, and `build/exploding_fist_v2.prg` has 45983 bytes. Each file loads with `LOAD"...",8` and starts with RUN (**Observed**).

### The memory plan

This table gives the memory during the boot, after the outer stage unpacks all parts (**Code**). Stage 2 of version I ends at `$8B44`, and stage 2 of version II ends at `$93C1`.

| Range | Version I | Version II |
|---|---|---|
| `$0801-$1FFF` | Stage 2 | Stage 2 |
| `$2000-$35FF` | M.TSOUND. The stage 2 bytes are in the stash. | The same |
| `$3600-$8FFF` | Stage 2 to `$8B44` | Stage 2 |
| `$9000-$910F` | M.MYTINY | M.MYTINY. The stage 2 bytes are in the stash. |
| `$9110-$93C1` | Free | Stage 2 |
| `$9800-$9AFF` | M.SPCHTBL | M.SPCHTBL |
| `$9B00-$B0FF` | The stash of `$2000-$35FF` | The stash of `$2000-$35FF` |
| `$B100-$B4C1` | Free | The stash of `$9000-$93C1` |
| `$C000-$C3E7` | The colour data of the picture | The same |
| `$C400-$C435` | M.PRERUN | The same |
| `$C600-$C6C2` / `$C6DA` | The boot code (v1 / v2) | The same |
| `$CC00-$CFE7` | The screen data of the picture | The same |
| `$D800-$DBE7` | The colour RAM, a copy from `$C000` | The same |
| `$E000-$FF3F` | The bitmap of the picture | The same |

The bitmap and the screen data are already at the addresses of VIC bank 3, and only the colour data needs a copy (**Code**). The colour RAM is in the I/O area, so the boot writes it with the I/O on (**Conclusion**). When the boot ends, stage 2 unpacks the game over all these areas (**Conclusion**).

### The boot

[`boot_start`](../v1/src/boot.asm#L51) at `$C600` does these steps. Version II does the same, in [boot.asm](../v2/src/boot.asm#L58), and adds a second piece of the stash (**Code**).

1. It sets the border colour 3, the background colour 1 and VIC bank 3 with the screen at `$CC00` and the bitmap at `$E000`. These are the values of the 2010 loader.
2. It copies the 1000 bytes of colour data from `$C000` to `$D800` and switches the bitmap mode on with `$D011` = `$3B`.
3. It calls `$9000`. M.MYTINY plays the sample and returns at its end.
4. It stops CIA1 timer B and its IRQ, because M.MYTINY leaves them on.
5. It waits up to 400 frames, 8 seconds on a PAL C64. It waits for raster line `$F8` one time in each frame.
6. In each frame it reads the keyboard with all columns selected, and the fire button of port 2. A key or a fire button ends the wait at once.
7. It calls M.PRERUN at `$C400`, as the 2010 loader does.
8. It writes `$36` to `$01` and copies the stash from `$9B00` back to `$2000-$35FF`. Version II then copies the second piece from `$B100` to `$9000-$93FF`.
9. It writes `$37` to `$01` and jumps to the unpacker of stage 2 at `$080D`.

The keyboard test uses only bits 0-4 of `$DC01`. A key with its row in bits 5-7 thus does not end the wait. The fire button of port 1 is bit 4 and ends the wait (**Code**). In this VICE setup, bits 5-7 of `$DC01` always read 0. A test of the full byte would thus end the wait at once (**Conclusion** from the emulator flaw).

### Two findings

Runs of the boot showed two values of `$01` that the boot needs (**Observed**):

- **`$01` = `$36` for the stash copy.** The stash is at `$9B00-$B0FF`, and the BASIC ROM covers `$A000-$BFFF`. `tsound_stop_irq` sets bit 0 of `$01` at its end, so the BASIC ROM is on after the sample. With the ROM on, the copy reads ROM bytes in place of the stash above `$A000` (**Code**). The store of `$36` before the copy at [line 116](../v1/src/boot.asm#L116) switches the BASIC ROM off (**Observed** in runs).
- **`$01` = `$37` for the Exomizer unpacker.** The unpacker of stage 2 expects the machine state after RUN, with BASIC, KERNAL and I/O on. With `$36` the unpack gives wrong bytes (**Observed**). The store of `$37` at [line 136](../v1/src/boot.asm#L136) corrects it.

The two stores are at [line 123](../v2/src/boot.asm#L123) and [line 156](../v2/src/boot.asm#L156) in version II (**Code**).

### The tests

Each project has the run [boot_title_picture.json](../v1/tests/boot_title_picture.json) of version I and [boot_title_picture.json](../v2/tests/boot_title_picture.json) of version II. Both runs PASS (**Observed**). Each run does these steps on the release file:

1. It runs until the CPU reaches `$9000`, the call of the sample, and then runs 20 more frames.
2. It compares the bitmap at `$E000-$FF3F`, the screen data at `$CC00` and the low nybbles of the colour RAM with M.PICTURE. It also compares `$D011`, `$D018` and `$DD00`. Then it keeps the screen as `title_picture`.
3. It runs until the game entry, `$1158` or `$115A`. It gives no key, so the boot waits the full 8 seconds.
4. It compares the game bytes `$0400-$13FF`, a 4 KB block and `$F540-$FFEF` with the original. The block is `$2000-$2FFF` in version I and `$3000-$3FFF` in version II.
5. It runs 300 frames and keeps the screen as `game_demo`.

Both 4 KB blocks include bytes of the stash range `$2000-$35FF`. Thus each run also shows that the stash copy puts back the correct bytes of stage 2 (**Conclusion**).

## Still open

- Why does the Exomizer unpacker of stage 2 give wrong bytes with `$01` = `$36`? A trace of the unpack with each value of `$01` can show the first different byte.
- What did `prerun_fill_bar` in bank1 at `$C404` do in an earlier loading stage? No file or run shows a caller.
- How long does the sample last on a real machine? A run can count the frames between the call of `$9000` and its return. The IRQ itself takes cycles, so short half-waves are possibly longer than the render model gives.
- No test checks `$9000-$93C1` of version II at the game entry. A memory compare of that range at `$115A` can show that the second piece of the stash is correct.
