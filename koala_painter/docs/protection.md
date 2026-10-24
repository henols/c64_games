# The disk protection of Koala Painter

Koala Painter checks its disk once, at the start of the program. A short routine tests one byte of RAM, then sends two block reads to the 1541 and reads the drive status after each read. The two builds have the same scheme but read different sectors: v1 reads track 33, v2 reads track 1. When a check fails, a script of the program writes zero bytes over the program code. All releases of this project are cracks, so no release has the protection in its original form.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge. The label `v1:` or `v2:` gives the project of a name.
- A *script* is a byte-code program of the script interpreter. An *op* is one opcode with its operands. The v2 page [scripts.md](../v2/docs/scripts.md) gives the format.
- The *start-up script* is the first script that the program runs.
- The *drive status* is the text that the 1541 sends on channel 15, for example `00, OK,00,00`.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## The scheme

Both builds keep the protection in one routine of 83 bytes. The routine runs three checks in a fixed sequence:

1. It writes `$01` and then `$00` to `$8413`, and reads each value back.
2. It reads a first sector and gets the drive status.
3. It reads a second sector and gets the drive status.

In v1, the first sector must give a read error, and the second sector must read without an error. In v2, the crackers put NOPs over the compares, so the conditions are not known (**Code**).

The routine opens channel 5 with the name `#`. This name gives a buffer in the drive. Each block read copies one sector into that buffer. The C64 never reads the 256 bytes of the buffer. Only the drive status counts. Thus the protection tests the format of the disk, not its data (**Code**).

### How the start-up script hides the call

No 6502 instruction calls the protection. The call is an op of the start-up script: op 9 jumps to the machine code at the address of its two operands. The start-up script is data, so a disassembler finds no JSR and no JMP to the routine. The knowledge has no reference from the code to `$3A43` or to `$393D` (**Code**).

[`v2:startup_script` `$1E1A`](../v2/src/script/picture_buffers.asm#L28) first copies the background colour to the undo buffer and the swap picture. Then the bytes `09 43 3A` at `$1E30` jump to `$3A43`. In v1, [`v1:startup_script` `$1DEF`](../v1/src/script/picture_buffers.asm#L28) has the same ops, and the bytes `09 3D 39` at `$1E05` jump to `$393D` (**Code**).

The two builds leave the routine in different ways. In v1, the routine ends with an RTS, and the script ends at the next `$FF`. In v2, the routine sets the stack pointer to `$FF` and jumps to `v2:start_main`. Thus the op 9 of v2 never returns, and the `$FF` at `$1E33` never runs (**Code**).

## The checks

The v2 routine is [`v2:disk_protection` `$3A43`](../v2/src/protection/disk_protection.asm#L6). The v1 routine is [`v1:disk_protection` `$393D`](../v1/src/leftovers/leftover_393d.asm#L6). Both run once, from the start-up script, before the main menu shows (**Code**).

### The RAM test at `$8413`

The first check writes `$01` to `$8413` and compares the read value with `$01`. Then it writes `$00` and compares the read value with 0. A different value goes to the failure code. Both builds have the same 22 bytes (**Code**).

`$8413` is in the undo bitmap at `$8000-$9F3F`. A cartridge can show its ROM at `$8000-$9FFF`. A write then goes to the RAM, but a read gives the ROM byte. **Conclusion:** the test finds a cartridge in that area, for example a copy or freeze cartridge. The program also needs this RAM for its undo buffer.

### The block reads of v1

v1 sends two `B-R` commands, one for each sector. For each read, `v1:protection_open_buffer` opens file 5 with the name `#`. [`v1:send_command_close` `$2C83`](../v1/src/storage/storage_screen.asm#L400) sends the command on channel 15. [`v1:drive_status` `$39C4`](../v1/src/storage/drive_status.asm#L6) reads the status, and the carry flag is clear for status `00`. Before the reads, `v1:set_kernal_vectors` puts the KERNAL IRQ and NMI vectors back. At the end, `v1:set_program_irq` sets the IRQ of the program again (**Code**).

- Track 33 sector 5 must give an error. A clear carry after the status is a failure.
- Track 33 sector 6 must read without an error. A set carry after the status is a failure.
- After each command, a set carry is also a failure.

**Conclusion:** the second read makes sure that the drive and the disk work. A disk with no track 33, or a drive that cannot read, fails there. Only a disk with a read error in sector 5 and a good sector 6 passes.

The commands are at [`v1:protection_commands` `$3990`](../v1/src/protection/disk_protection_3990.asm#L6). The byte `$23` (`#`) at `$3990` is the name of the buffer. Each command has 15 bytes and no CR. The DOS takes a space as a separator, and the command uses one or two spaces for each field (**Code**).

| Bytes | Text | Meaning |
|---|---|---|
| `42 2D 52` | `B-R` | Block read |
| `3A` | `:` | End of the command word |
| `20 35` | ` 5` | Channel 5, the buffer of `#` |
| `20 20 30` | `  0` | Drive 0 |
| `20 33 33` | ` 33` | Track 33 |
| `20 20 35` | `  5` | Sector 5. The second command at `$39A0` has `36`: sector 6 |

### The block reads of v2

v2 sends two `U1` commands. `U1` is the block read of the 1541 that reads the full sector. For each read, `v2:protection_open_buffer` opens file 5 with the name `#` on drive 8. `v2:open_command_channel` opens channel 15 with the command as the file name. Then [`v2:protection_read_status` `$3AC2`](../v2/src/protection/disk_protection.asm#L110) reads the drive status up to the CR. It keeps only the first digit of the error number, in A and in `v2:protection_result` at `$0850`. Nothing else in the program reads that byte (**Code**).

The commands are at [`v2:protection_commands` `$3A96`](../v2/src/protection/disk_protection.asm#L60). The byte `$23` (`#`) at `$3A96` is the name of the buffer. Each command has 11 bytes with the CR (**Code**).

| Bytes | Text | Meaning |
|---|---|---|
| `55 31` | `U1` | Block read of a full sector |
| `3A` | `:` | End of the command word |
| `35` | `5` | Channel 5, the buffer of `#` |
| `2C 30` | `,0` | Drive 0 |
| `2C 31` | `,1` | Track 1 |
| `2C 31` | `,1` | Sector 1. The second command at `$3AA2` has `32`: sector 2 |
| `0D` | CR | End of the command |

The routine runs this sequence for the first sector. The second read is the same, with the command at `$3AA2` (**Code**):

```text
$3A59  JSR protection_open_buffer   ; OPEN 5,8,5,"#"
$3A5C  LDA #$0B                     ; 11 bytes
$3A5E  LDX #$97                     ; the command at $3A97
$3A60  LDY #$3A
$3A62  JSR open_command_channel     ; OPEN 15,8,15,"U1:5,0,1,1"
$3A65  NOP                          ; TBC: 2 bytes of the original
$3A66  NOP
$3A67  JSR protection_read_status   ; A = first digit of the status
$3A6A  NOP                          ; TBC: 2 bytes of the original
$3A6B  NOP
$3A6C  JSR CLALL
```

After each read, two bytes follow the command and two bytes follow the status. In every v2 release these four places hold NOPs. The original bytes are in no release, so the condition of each read is not known. **Conclusion:** the gaps fit a branch to `v2:protection_failed`. A `BCS` after the OPEN and a `BEQ` or `BNE` on the status digit are each 2 bytes. After both reads, the routine closes all files with CLALL and sends `I` (initialize) to the drive.

### All checks

| Check | Build | Where | Compares | Passes when |
|---|---|---|---|---|
| RAM test | v1 and v2 | `$393D` / `$3A43` | `$8413` after a write of `$01` and of `$00` | Both values read back |
| First read | v1 | `$3956` | Carry after `B-R` 33/5 and its status | The status is an error |
| Second read | v1 | `$396E` | Carry after `B-R` 33/6 and its status | The status is `00` |
| First read | v2 | `$3A59` | First status digit after `U1` 1/1 | Not known: NOPs in all releases |
| Second read | v2 | `$3A6F` | First status digit after `U1` 1/2 | Not known: NOPs in all releases |

## The effect of a failed check

A failed check runs a script that writes zero bytes over the program. The program erases its own code, and no message shows (**Code**).

- v2: [`v2:protection_failed` `$3A8F`](../v2/src/protection/disk_protection.asm#L54) runs [`v2:wipe_program_script` `$1E71`](../v2/src/script/picture_buffers.asm#L59). Op 6 stops the interrupts (SEI). Then the script calls the 8000-byte clear two times from `$0900`. The target is `$0900-$477F`, 16000 bytes.
- v1: [`v1:protection_failed` `$3989`](../v1/src/leftovers/leftover_393d.asm#L40) runs [`v1:wipe_program_script` `$1E30`](../v1/src/script/picture_buffers.asm#L44). It has no SEI op. It fills `$1000-$4E7F` with the same two calls.

The planned targets hold the code of the tools, the menu, the scripts and the interpreter. The v2 target also holds the IRQ handler at `$0943`. Thus v2 must stop the interrupts first. The v1 target starts above the IRQ handler at `$0969`. After a failed read, the IRQ vector of v1 also points to the KERNAL (**Code** / **Conclusion**).

The wipe does not reach its end. The 8000-byte clear writes 250 bytes with op 12 and repeats 32 times with op 5. The scripts themselves are in the target. In v2, the 23rd write fills `$1E7C-$1F75` and erases the op 5 of the loop at `$1E86`. The interpreter then reads zero bytes, and each zero byte is op 0. In v1, the 15th write fills `$1DAC-$1EA5` and erases the loop at `$1E44` (**Code**).

**Conclusion:** the wipe writes zero to the first 5750 bytes in v2 and to the first 3750 bytes in v1. After that, the interpreter runs the bytes after the filled area as ops. The fill loop takes 13 cycles for each byte. Thus the program loses this code in less than 0.1 seconds. No run showed the state of the machine after the wipe.

## The releases

Every release is a crack, and each crack stops the protection in a different way.

### TBC (v2)

The RAM test and both reads still run. TBC put NOPs at `$3A65`, `$3A6A`, `$3A7B` and `$3A80`, two bytes each. These are the four places after the command and after the status: [`v2:disk_protection` `$3A65`](../v2/src/protection/disk_protection.asm#L29) is the first. Thus the reads have no effect on the program (**Code**). **Conclusion:** a cartridge at `$8000` can still fail the RAM test.

### MAM (v2)

Only the RAM test runs. MAM put 47 NOPs at `$3A59-$3A87` over both reads, the CLALL calls and the initialize: [`v2:disk_protection` `$3A59`](../v2/src/protection/disk_protection.asm#L24). MAM also changed three other places that no code reaches after the NOPs (**Code**):

- `$57` (`W`) in place of `U` at `$3A97` and `$3AA2`. The 1541 DOS has no `W1` command.
- `$3AAD-$3AB5` in `v2:protection_open_buffer`: `LDA #$02`, `STA $0850`, `RTS`.
- `$3ACA-$3ACC` in `v2:protection_read_status`: `NOP`, `LDA #$02` in place of the CHRIN of the first digit.

The value 2 is the first digit of the read errors 20-29. **Conclusion:** MAM changed the protection in steps, and the NOPs made the earlier changes useless. In the MAM file, `$0850` is a byte of the MAM key code in its BASIC part. A call of the changed routine would damage that code.

### Mayday! (v1)

No check runs. Mayday! put three NOPs at [`v1:cold_start_irq_setup` `$0955`](../v1/src/init/entry.asm#L52), so nothing calls `v1:start_script`. The original bytes are in no release. **Conclusion:** they were most likely `JSR $0A81`, as v2 calls its start-up script in the same place of the cold start. The NOPs also skip the colour copies of the start-up script. Mayday! changed the device of `v1:protection_open_buffer` at `$39BA` to `LDX $BA`, with the other disk code. That change has no effect, because no code reaches it (**Code**).

## The rebuild

The two builds handle the protection in different ways, because the releases keep different parts of it.

### v2: the switch PROTECTION

The switch PROTECTION has the default 0. Its one patch is at [`v2:startup_script` `$1E30`](../v2/src/script/picture_buffers.asm#L40). With the switch off, the byte `$09` (op 9) becomes `$FF`, and the start-up script ends there. The routine, the commands and the wipe script stay in the build, but nothing reaches them. Thus the default build runs no RAM test and no drive command at the start (**Code**).

With the switch on, the byte is `$09`, as in TBC and MAM. The build of the TBC release has the bytes of the file `KMAIN` of the TBC disk. It has the NOPs of TBC (**Observed**: a byte compare of the two files). The bytes before TBC cannot come back, because no release has them. The switch CRACK_MAM adds the changes of MAM (**Code**).

### v1: no switch

v1 has no switch for the protection. The bytes at `$0955` are NOPs in the only release, and no release has the bytes of the call. A switch would have to use bytes that are not known. Thus `v1:disk_protection` and `v1:start_script` are leftovers in `v1/src/leftovers/`. Only LEFTOVERS = 1 builds them, and the default build has zero bytes at `$393D-$398F`. The commands and `v1:protection_open_buffer` at `$3990-$39C3` stay in the default build, but no code reaches them (**Code**).

### What the runs showed

- 16 recordings of each version replay on the original and on the default build. Each checkpoint is equal. In v2, each record file writes `$FF` to `$1E30` of the TBC capture, as the switch does. Thus both sides skip the protection, and the program works without it (**Observed**).
- The v2 Storage tests start from a snapshot of the main menu. The TBC start-up of that snapshot ran the RAM test and both `U1` reads with a copy of the Mayday! disk. The program reached the menu, because TBC ignores the result of the reads (**Observed**).
- In v1 no run executed the protection, because the Mayday! release never calls it (**Observed**: the coverage has no byte of `$393D-$398F`).

## Still open

- **No run had a protected disk.** The images of this project are D64 files of 174848 bytes, without the error bytes of a D64. Thus they keep no read error. Mayday! made v1 from a G64 of an original disk, but that G64 is not in the project. — A run of the v1 protection with that G64 can show the error number of track 33 sector 5. It needs a build with LEFTOVERS = 1 and `JSR $0A81` at `$0955`.
- **The v2 conditions.** The four NOP places hide the original branches. — A G64 of an original v2 disk can show the status of track 1 sectors 1 and 2. That status tells which branch fits each place.
- **The state after the wipe.** — A run can fail the RAM test on purpose, for example with `$00` in place of the compare value at `$3A4C`. That run can show what the interpreter does after the wipe erases its own script.
- **The RAM test and a cartridge.** — A run with an 8K cartridge image at `$8000` can show if the test finds it.
