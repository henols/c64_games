# The releases

This page tells which releases the rebuild uses, how each release came to the game file, and what each crack changed in the game. The rebuild has three releases of the 13 cracks of Falcon Patrol on CSDb. A byte compare of the game image `$2000-$5FFF` of all 13 cracks shows that they come from one game file.

**Evidence.** **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The three releases of the rebuild

| Label | CSDb | File | SHA-256 |
|---|---|---|---|
| `BOMBARDIERI` | 147560 | `original/bombardieri/Falcon_Patrol-Bombardieri.d64` | `004f64bba659e0f2feb7baa5101e9e69f8ec6fa89143806a43290cfd49b8c670` |
| | | `original/bombardieri/falcon.prg` (`FALCON!` of the disk) | `eb95c68bf34f5501205ed71e59c99c3faa0d4f76f51aa75e40602196fc069bdf` |
| `DERBYSHIRE_RAM` | 161485 | `original/derbyshire_ram/Falcon Patrol + (Virgin)[cr dr].d64` | `84fab8c7e26428d4346a0f54bc5db6a0c0a8e5d655249385bc0e80874895bac7` |
| | | `original/derbyshire_ram/falcon_patrol_dr.prg` | `0cdae3461f7c2fc16bf99000794578c9a74eeac28e95c2147dc82be2f90e9bce` |
| `RGR` | 207856 | `original/rgr/FalconPatrol-RGR.d64` | `5192aa8f60f80584936c12717bd6d53b48bde632870159fcc6a5fe1575ef62d1` |
| | | `original/rgr/falcon_patrol_rgr.prg` | `c99b1f55a8a579f37160bb50b895f043cf04c158df8650543dd6fe5bd7164b1d` |

### T.Bombardieri: the base release

The disk holds two files. `FALCON PATROL` is a BASIC boot. It prints "FALCON PATROL NOW LOADING" and "Broken by T.BOMBARDIERI", loads `FALCON!` and starts it with SYS 16640. `FALCON!` is the game file `$2000-$6000`, 16385 bytes. Its bytes are the bytes of most other cracks, so it is the base release of the rebuild (**Observed**).

The boot also sets the IRQ vector `$0314` to `$EA34` (POKE 788,52). The game does not need this, because [`raster_irq_init` `$4B20`](../src/irq/raster_irq_4b20.asm#L6) sets its own vector (**Code**). The capture of the game at `$4100` leaves out the text screen of the boot at `$0400-$07E7` and the BASIC boot at `$0801-$08F8`. In 200 frames after the start, the game reads neither range before it writes it (**Observed**).

### Derbyshire Ram: the trainer

"FALCON PATROL+ CRACKED 1983 DERBY RAM." is a packed file of 53 blocks. A CSDb comment calls it a crack of 1983 that a cracker cracked again later. After it unpacks, it shows "* DERBYSHIRE RAM * INFINITE LIVES ? [Y/N]" and waits for a key with the KERNAL. The answer Y writes `$A5` to `$417C`. The `DEC lives` at `$417C` in [`game_life_begin` `$4173`](../src/game/main_loop.asm#L31) becomes `LDA lives`, so a lost jet costs no spare jet. Then the crack jumps to `$4100` (**Observed**). The switch `TRAINER` holds this patch. The trainer has a side effect. The spare-jet count stays 3, so the test for the first jet passes at each new jet, and the start prompt code clears the score. A run with the trainer byte and a score of 01750 shows 00000 at the next jet (**Observed**).

The game bytes of this release are the bytes of the base release, except the trainer byte and the run state below (**Observed**).

### RGR: a memory dump with a new credit line

The file is `$0801-$6009`, 22539 bytes. Its BASIC line is `POKE157,128:SYS16640: ***RGR***`. The bytes `$0900-$1FFF` hold the power-on RAM pattern of a real C64, so the file is a memory dump (**Observed**). The game image has the run state below, and RGR changed the credit line of the title screen. "©VIRGIN GAMES 1983" became "© MIKE GAMES 1983" (`$2F80-$2F86`, switch `CRACK_RGR`) (**Observed**).

## The run state of DR and RGR

The crackers of DR and RGR saved the memory of a game that ran before. Thus their game image holds bytes that the game wrote at run time, not the bytes of the game file. The coverage of the recordings shows that the game writes each of these bytes (**Observed**).

| Range | DR | RGR | What the game keeps there |
|---|---|---|---|
| `$35A0-$35A7` | yes | yes | Character `$B4`, the partial cell of the GAS gauge. |
| `$3710-$377B` | yes | yes | Radar characters `$E2-$EF`, which the game draws again in each pass. |
| `$6000` | yes | yes | The first byte of the gauge buffer. |
| `$3150-$315F` | no | yes | The crater characters `$2A`/`$2B`, which get random bits in each pass. |
| `$5FFE-$5FFF` | no | yes | Two bytes after the code that no run reads or writes. |

The switch `RUN_STATE` holds the first three ranges, and `RUN_STATE_RGR` the last two. Both are off in the default build (**Code**).

**Conclusion.** The two releases have the same gauge and radar bytes. In both, the jet had a full tank and the radar had the same picture when the cracker saved the memory. This is the state right after a refuel on the pad.

## The other cracks on CSDb

A compare of the game image `$2000-$5FFF` of the other 10 cracks gives these groups (**Observed**). These cracks are not releases of the rebuild.

| Crack (CSDb) | The game image |
|---|---|
| Unknown (93071), OTD (157448), The Cream Crackers (258654) | The bytes of the base release. Only `$5FFF` is different. The unknown crack also has the text "DER EIGENTUEMER DIESES SPIELS IST : MARTIN SORMAGEC" (the owner of this game is ...). |
| Mr. Copy (141462) | A memory dump `$0801-$5FFF`. Only `$5FFF` is different. The RAM below `$2000` holds the directory of a disk with "FALCON LOADER", "FALCON" and "CODE" among other games. |
| Supersoft (180933) | The credit line says "CRACKED BY SUPERSOFT". |
| Davy Kuratz (206804) | The credit line says "BROKEN BY DAVY KURATZ". |
| The Greek (198100) | The file loads at `$2001`, with a BASIC line inside the zero bytes at the start of the image. |
| ABC (135924), Special-Soft (166374) | Packed files. They were not unpacked. |
| Gabriel Software (258268) | About 10000 bytes are different. It was not examined. |

**Conclusion.** `$5FFF` is `$00` in the base release and `$FF` in most dumps. No code reads or writes it, so it is not a game byte. The disk directory in the Mr. Copy dump can show the file names of an early disk release ("FALCON LOADER", "FALCON", "CODE"). It is a disk of a collector with other games, so it does not prove the file names of the Virgin disk.

## No copy protection

The game file has no copy protection: no disk access, no check of the loader, no checksum (**Code**). The original Virgin tape and its loader are not in the releases. Thus the protection of the original loader, if there was one, is not known.
