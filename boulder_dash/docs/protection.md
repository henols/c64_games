# The copy protection of Boulder Dash

The Micro Fun build has one disk check. It reads one sector of the disk and expects a read error. A copy of the disk reads the sector without an error, and the check then damages one page of the game code. No release in the project runs the check, because every crack starts the game after it. The Statesoft build came on tape with a turbo loader, and we found no check in its game code.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge, with the label `v1:` or `v2:` of their project.
- The *drive status* is the text that the 1541 sends on channel 15, for example `00, OK,00,00`. Its first two characters are the error number.
- The *game file* is the file that holds the game at `$5000`. A *boot* is the small program of a crack that loads the game file and starts it.
- **Observed** marks a fact that a run or a byte compare showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The scheme

The protection of the Micro Fun disk is a bad sector. The check asks the drive to read track 18, sector 18, and it accepts only the drive error 23. The 1541 gives error 23 when the checksum of the data block of a sector is wrong. The check compares no other key, and it reads no byte of the sector (**Code**).

**Conclusion:** the original disk had a sector with a wrong checksum at track 18, sector 18. Track 18 is the directory track, and sector 18 is its last sector. A copy program that copies good sectors writes a correct checksum. Thus a copy reads the sector without an error, and the check fails.

The Statesoft build has no disk check. The tape has a turbo loader, which a normal tape copy cannot copy. Neither build has a check in the code that runs during the game (**Code**).

## The check

The check is [`v1:disk_protection` `$8CFF`](../v1/src/leftovers/leftover_8b86.asm#L61). It is at the end of the game file, after the code of the game. Its two data items come first:

- `v1:disk_check_channel_name` at `$8CF2`: the byte `$23`, the name `#` of the drive buffer.
- `v1:disk_check_command` at `$8CF3`: the 12 characters of the block read command.

No instruction, table or vector of the game refers to `$8CFF`. The knowledge has no reference to it (**Code**).

### What the check does

The routine runs these steps once (**Code**):

1. It closes all files with CLALL.
2. It opens file 15 on drive 8 with the secondary address 15 and no name. This is the command channel.
3. It opens file 5 on drive 8 with the secondary address 5 and the name `#`. The drive gives a buffer to this channel.
4. It sends the 12 characters of the command on channel 15, without a CR. Then CLRCHN ends the output to the drive.
5. It reads the first character of the drive status and compares it with `2`. Then it reads the second character and compares it with `3`.
6. For the status 23, it reads 20 more characters of the status. It closes files 5 and 15 and jumps to [`v1:cold_start` `$8AB3`](../v1/src/init/cold_start.asm#L9).
7. For any other status, it goes to [`v1:disk_check_wipe` `$8D6A`](../v1/src/leftovers/leftover_8b86.asm#L110). The wipe then jumps to `v1:cold_start` too. On this path, files 5 and 15 stay open.

The command uses the `U1` form of the block read. `U1` reads the full sector into the buffer of the channel:

| Bytes | Text | Meaning |
|---|---|---|
| `55 31` | `U1` | Block read of a full sector |
| `3A` | `:` | End of the command word |
| `35` | `5` | Channel 5, the buffer of `#` |
| `2C 30` | `,0` | Drive 0 |
| `2C 31 38` | `,18` | Track 18 |
| `2C 31 38` | `,18` | Sector 18 |

The C64 never reads the 256 bytes of the buffer. Only the error number of the drive status counts (**Code**).

### Summary

| Check | Where | When | Compares | Passes when |
|---|---|---|---|---|
| Disk check | `$8CFF-$8D80` | Once, before the cold start | The first two characters of the drive status after `U1` 18/18 | The status is 23 |

## The effect of a failed check

A failed check writes zero bytes into the game code. Then it starts the game as usual. No message shows (**Code**).

The wipe puts `$7000` into the pointer at `$FA`/`$FB`. The inner loop writes 256 zero bytes with `STA ($FA),Y`. X counts the inner loop 32 times. The loop never changes the high byte at `$FB`. Thus the wipe writes `$7000-$70FF` 32 times, and only that page changes. It takes about 90000 cycles, less than 0.1 seconds (**Code**).

The page `$7000-$70FF` holds parts of these routines (**Code**):

- The end of `v1:handle_amoeba`, which grows the amoeba.
- `v1:add_bonus_life`, `v1:check_bonus_life` and `v1:add_points`, which count the score and the lives.
- `v1:start_crack_sound`, `v1:check_time` and `v1:decrement_time`.
- `v1:tick_cave_time` and `v1:tick_inbox_delay`, which count the seconds of a cave.

A zero byte is the opcode BRK. No code of the title screen calls this page, so the title shows as usual. In a cave, [`v1:update_clock` `$7111`](../v1/src/status/score_time.asm#L143) runs in each frame of the play interrupt. After 60 frames it calls `v1:tick_inbox_delay` at `$70F1`, and the CPU executes a BRK (**Code**).

**Conclusion:** the game breaks about one second after the first cave starts, in a game or in the demo. The player sees a title screen that works, and the failure comes later. That makes the check harder to find. No run showed what the BRK does in this state.

**Conclusion:** the loop counts 32 pages but writes only one. A wipe of 32 pages from `$7000` would also erase `$8AB3` and the loop itself at `$8D74`. Then the check could not start the game at all. We cannot tell if the author wanted one page or 32 pages.

## Why the check was most likely the entry of the original

No release has the original boot of Micro Fun. These facts point to a start at `$8CFF`:

1. Nothing in the game calls the check. The only way to run it is a jump from outside the game file, for example `SYS 36095` (**Code**).
2. Both paths of the check end with a jump to `v1:cold_start`. The check never returns. It is a front end that runs before the game (**Code**).
3. The check starts with CLALL and uses the KERNAL file routines. It needs the state of the C64 after a LOAD from BASIC. The cold start then sets `$01` to `$36` and its own NMI vector (**Code**).
4. The check lies after the end of the game code at `$8B85`. Before it, `$8B86-$8CF1` holds a part of the developer's symbol table. The last record of the table breaks off after the name ":LOOP", and the check starts at the next byte. Thus the check covers the end of the table (**Code**).
5. Every Micro Fun crack that we examined has the check, byte for byte, but starts at `$8AB3` (**Observed**: a byte compare of the game files).

**Conclusion:** Micro Fun added the check to the finished game. The free space after the game held old bytes of the developer's assembler, and the check went over the end of them. The original boot most likely ended with `SYS 36095`, to `$8CFF`. The crackers replaced it with `SYS 35507`, to `$8AB3`.

The forum post of LogicDeLuxe gives `$5000-$8B86` and the entry `$8AB3` for Micro Fun. The forum post states these values. They agree with the game code without the leftovers, and with the entry of the cracks (**Conclusion**).

## The releases

No release calls the check. The boots of Charsoft, Killer Kamakazi, Jeff the Ripper and Lord Markus end with `SYS 35507` (**Code**: the BASIC lines). No crack changed a byte of the game file. Thus the check is still in each Micro Fun release, but nothing reaches it. The page [releases.md](releases.md) gives the files of the releases.

The Statesoft releases have no check. The tape loader jumps to `$8E6A`. The boots of DDC and Roan jump to `$8E69`, a CLI before the cold start (**Observed** for the tape, **Code** for the boots).

## The Statesoft tape

The tape loads with a turbo loader. The border shows flashing stripes, and the loader shows the Statesoft picture while the game loads (**Observed**: a run of the TAP file). We did not examine the code of the turbo loader.

The game code of v2 is the code of v1, moved up by `$398` bytes. The v2 game file ends with the symbol table leftover at `$8F3D-$8FFF`. It has nothing like the disk check (**Code**). No routine of the v2 source calls a KERNAL file routine, for example OPEN, SETLFS or CHKIN. In v1, only the disk check calls them (**Code**: a search of both sources).

**Conclusion:** the protection of the Statesoft release was the turbo format of the tape. A normal tape copy with the KERNAL cannot copy that format.

## The rebuild

The rebuild of v1 has no switch for the protection. The original call of the check is in no release, so a switch would need bytes that are not known. The check is part of the leftover file `v1/src/leftovers/leftover_8b86.asm`, with the symbol table (**Code**).

- LEFTOVERS = 1 builds the leftover file. The build of the release CHARSOFT sets it, and that build is identical to BD.OBJ (**Observed**: the release build gave PASS).
- The default build has LEFTOVERS = 0. It has 521 zero bytes at `$8B86-$8D8E`, and its loader does not load them. The loader jumps to `v1:cold_start` (**Observed**: a build of the default program, and the loader source).

The seven recordings of v1 start the game at `$8AB3`, as the cracks do. Their coverage has no executed byte at `$8CFF-$8D80`. Thus the game works without the check, and no run reached it (**Observed**).

The rebuild of v2 has nothing to turn off. Its switch START_SCREEN only shows the Statesoft picture before the game starts (**Code**).

## Still open

- **The bad sector of the original disk.** The D64 images of the project have 174848 bytes, without the error bytes of a D64. Thus they keep no read error. — A G64 or a D64 with error bytes of an original Micro Fun disk can show the status of track 18 sector 18.
- **The effect of the BRK.** — A run of a build with LEFTOVERS = 1 that jumps to `$8CFF` with a D64 of a copy. It can show the wipe and what happens at the first BRK.
- **The original boot.** — An original Micro Fun disk can show the boot and its SYS address.
- **A check in the turbo loader.** — A trace of the turbo loader of the TAP file can show if the loader tests the machine or the tape.
