# The script interpreter

Koala Painter draws most of its screens with small byte-code programs, the *scripts*. A script sets the colour registers, writes the frame and the texts of the menu, builds the menu charset and draws the cursor marks. Scripts also copy the picture to the undo buffer, the zoom buffer and the swap picture. The interpreter reads a script one opcode at a time and runs a short 6502 routine for each opcode. A script is much shorter than the 6502 code that does the same work. For example, 11 bytes fill the 1000 bytes of the colour RAM. This page gives the format of the byte code, its three stacks, and two scripts decoded by hand.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *script* is a sequence of opcodes and operands that ends with `$FF`. An *op* is one opcode with its operands.
- The *source* is `script_src_ptr` (`$64/$65`). The *destination* is `script_dest_ptr` (`$66/$67`). The *script pointer* is `script_ptr` (`$62/$63`).
- *Stack mode* is an op with bit 7 set. Its operands come from the argument stack.
- A count *n* of 0 means 256 for the ops that copy, fill or add to a pointer.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## Where the scripts are

The scripts have no table of pointers. Each caller puts the address of a script in A (low byte) and Y (high byte) and calls [`run_script` `$4361`](../src/script/interpreter.asm#L6). The code calls run_script from 53 places. The tool start code [`start_tool` `$0DD0`](../src/tools/tool_start.asm#L6) also runs the label script of each tool (**Code**).

| Range | Scripts |
|---|---|
| `$1B23-$1BCD` | Cursor sprites, and the 8 brush marks in sprite 1 |
| `$1DD3-$1EF7` | Start-up, picture colours, undo, clear, zoom buffer, self-wipe |
| `$1EF8-$236C` | The menu charset, with the glyph data inline |
| `$236D-$23AB` | The colour bar and the screen clear |
| `$23AC-$2479`, `$247A-$25E7` | The storage screen and its texts |
| `$2E4D-$2F7A` | The tool labels of the cursor ("draw", "line", "fill" ...) |
| `$3153-$32E9` | The zoom view |
| `$36D2` | The swap of the two pictures |
| `$3EE7-$431C` | The menu screen |

The interpreter is at `$4361-$4643`. The opcode table [`script_ops` `$4684`](../src/script/opcode_table.asm#L6) has 38 words, at `$4684-$46CF`. The reference pages of [the interpreter](reference/modules/script/interpreter.md), [the opcodes](reference/modules/script/opcodes.md) and [the table](reference/modules/script/opcode_table.md) give each routine and each caller.

## The interpreter loop

`run_script` saves A/Y in the script pointer and sets the three stack indexes to 0. Then it reads one byte at a time (**Code**):

1. Read the opcode at the script pointer, and add 1 to the pointer.
2. If the opcode is `$FF`, end the script or return from a call (see below).
3. Else, [`script_dispatch` `$43B1`](../src/script/interpreter.asm#L65) shifts the opcode left by one bit. Bit 7 goes into `script_stack_mode`. Bits 0-6 select one word of `script_ops`.
4. The interpreter jumps through `temp_word` to the routine of the op. The routine reads its operands and does its work.
5. The RTS of the routine goes back to step 1.

Only the opcodes 0-37 have a routine. When bits 0-6 of an opcode are above 37, the dispatch reads an address from the bytes after the table. These bytes are the leftover at `$46D0` (**Code**). No script uses such an opcode (**Code**).

## The operand rule of bit 7

Each op gets its operands through [`script_get_operand` `$4399`](../src/script/interpreter.asm#L45). When `script_stack_mode` is 0, this routine reads the next script byte. When it is 1, it pops the top byte of the argument stack. Thus each op has a script form and a stack form, with the same operands in the same order (**Code**).

Four ops do not obey this rule:

- Op 14 always reads its count and its bytes from the script.
- Ops 15 and 17 always read their count from the script.
- Op 5 reads its loop address from the script in the two forms. Only its count comes from the stack in the stack form.

The stack form lets one script do the work of several. [`copy_1000_ram_script` `$1DEC`](../src/script/picture_buffers.asm#L12) starts with `$81 $80`: op 1 and op 0 in the stack form. The caller pushes the two pointers with op 14, and calls the script with op 8. `save_colours_script` uses it to copy the screen RAM `$5C00` to `$C000` (**Code**).

## The three stacks

The interpreter keeps three stacks in RAM from `$4F00`. Each stack has an index in zero page that points at its last used byte. `run_script` sets each index to 0, so each new script starts with empty stacks (**Code**).

| Stack | Address | Index | Entry | Limit |
|---|---|---|---|---|
| Loop stack | `$4F00` | `script_loop_index` | 5 bytes: loop address lo, hi, count, and the address of the op 5 operands lo, hi | 10 loops. Op 5 makes no new loop when the stack is full. |
| Return stack | `$4F32` | `script_return_index` | 2 bytes: the script pointer lo, hi after the op 8 | No check of the depth |
| Argument stack | `$4F46` | `script_arg_index` | 1 byte | No check of the depth |

**The loop stack.** Op 5 (count, lo, hi) is a loop that jumps back to an address. [`script_op_loop` `$4455`](../src/script/opcodes.asm#L108) identifies a loop by the address of its own operands. When the top entry has the same address, the op decrements the count. When the count becomes 0, it removes the entry and continues after the operands. Else it jumps to the loop address again. When the top entry has a different address, the op pushes a new entry and jumps. Thus the code between the loop address and the op runs count + 1 times. Loops can nest, and two different ops 5 can jump to the same address (**Code**).

**The return stack.** Op 8 (lo, hi) pushes the script pointer and continues at the new address. The opcode `$FF` pops the return address when the stack has an entry. When the return stack is empty, `$FF` ends `run_script` with an RTS (**Code**).

**The argument stack.** Op 14 (n, n bytes) pushes the bytes in reverse order, so the first byte is on top. The next pops thus give the bytes in script order. Ops 27 and 28 push the source or the destination with the low byte on top. Ops 0 and 1 in the stack form pop such a pointer in the right order. Ops 15, 16 and 17 move the index or clear it (**Code**).

## The opcodes

The table gives each op with its script-form operands. "n" is a count, "lo, hi" an address. Each routine is in `script_ops`, in the order of the opcodes.

| Op | Byte | Operands | Action |
|---|---|---|---|
| 0 | `$00` | lo, hi | Set the source. |
| 1 | `$01` | lo, hi | Set the destination. |
| 2 | `$02` | n, n bytes | Write the n bytes to the destination. Destination += n. The source becomes the end of the bytes. Stack form: pop n, then n bytes. |
| 3 | `$03` | n | Copy n bytes from the source to the destination. Both += n. |
| 4 | `$04` | n | Swap n bytes between the source and the destination, with all RAM. Both += n. |
| 5 | `$05` | n, lo, hi | Loop: jump back to lo/hi n times. See the loop stack. |
| 6 | `$06` | - | SEI. |
| 7 | `$07` | - | CLI. |
| 8 | `$08` | lo, hi | Call the script at lo/hi. |
| 9 | `$09` | lo, hi | Jump to the machine code at lo/hi. Its RTS returns to the interpreter loop. |
| 10 | `$0A` | n | Source += n. |
| 11 | `$0B` | n | Destination += n. |
| 12 | `$0C` | n | Write `script_fill_byte` to n bytes at the destination. Destination += n. |
| 13 | `$0D` | byte | Set `script_fill_byte`. |
| 14 | `$0E` | n, n bytes | Push the n bytes on the argument stack, the first byte on top. |
| 15 | `$0F` | n | Argument index += n. The n bytes above the top are on the stack again. |
| 16 | `$10` | - | Clear the argument stack. |
| 17 | `$11` | n | Argument index -= n. |
| 18 | `$12` | - | Nothing. |
| 19 | `$13` | a, b, c | a to `current_colour` and `count_pixels_1`, b to `count_pixels_2`, c to `count_pixels_3`. |
| 20 | `$14` | - | Call `$0915` with X/Y = `shape_x0`/`shape_y0`, then `$0918`. Add the steps to `shape_x0` and `shape_y0`. |
| 21 | `$15` | x | Set `shape_x0`. |
| 22 | `$16` | y | Set `shape_y0`. |
| 23 | `$17` | dx | Set `script_step_x`. |
| 24 | `$18` | dy | Set `script_step_y`. |
| 25 | `$19` | x, y | Set `shape_x1` and `shape_y1`, then JMP `$091B`. |
| 26 | `$1A` | a | Call `$0918` with A = a and X/Y = `shape_x0`/`shape_y0`. Add the steps. |
| 27 | `$1B` | - | Push the source. |
| 28 | `$1C` | - | Push the destination. |
| 29 | `$1D` | - | Push `shape_x0`. |
| 30 | `$1E` | - | Push `shape_y0`. |
| 31 | `$1F` | - | Read the byte at the source into `pixel_value`. Source += 1. |
| 32 | `$20` | n | `shape_y0` += n. |
| 33 | `$21` | - | SEI, then all RAM: `$01` bits 0-1 = 0. |
| 34 | `$22` | - | BASIC, KERNAL and I/O on: `$01` bits 0-1 = 1, then CLI. |
| 35 | `$23` | lo, hi | Continue at the script lo/hi when `script_condition` is not 0. |
| 36 | `$24` | n | Destination -= n. |
| 37 | `$25` | n | Copy n bytes with all RAM. Both += n. |
| - | `$FF` | - | End of the script, or return from op 8. |

Ops 4 and 37 select all RAM for the copy, and then select the ROMs and the I/O again. Thus a script can read and write the RAM under the I/O at `$D000-$DFFF`. The undo buffer and the swap picture use this RAM (**Code**).

## The decoder

```text
run_script(A, Y):
    ptr = Y:A
    loop_index = return_index = arg_index = 0
    forever:
        op = mem[ptr++]
        if op == $FF:
            if return_index == 0: return
            ptr = pop(return_stack)              ; 2 bytes
            continue
        stack_mode = op >> 7
        routine = script_ops[op & $7F]
        call routine                             ; its RTS ends the op

operand():
    if stack_mode: return arg_stack[arg_index--]
    return mem[ptr++]
```

A tool that decodes a script must know the length of each op. The `$FF` in the bytes of op 2 or op 14 is data and does not end the script. For example, the mark of brush 7 writes the bytes `$FF $FC` with op 2 (**Code**).

## Worked example: the start-up script

[`startup_script` `$1E1A`](../src/script/picture_buffers.asm#L28) is the first script that runs. `cold_start` calls it through `start_script` (**Code**).

| Address | Bytes | Op | What it does |
|---|---|---|---|
| `$1E1A` | `01 D0 C7` | 1 | Destination = `$C7D0`, the background colour of the picture. |
| `$1E1D` | `02 01 01` | 2 | Write 1 byte: `$01` (white). |
| `$1E20` | `01 E8 D7` | 1 | Destination = `$D7E8`, the background of the undo buffer. |
| `$1E23` | `00 D0 C7` | 0 | Source = `$C7D0`. |
| `$1E26` | `25 01` | 37 | Copy 1 byte with all RAM. |
| `$1E28` | `01 E8 DF` | 1 | Destination = `$DFE8`, the background of the swap picture. |
| `$1E2B` | `00 D0 C7` | 0 | Source = `$C7D0`. |
| `$1E2E` | `25 01` | 37 | Copy 1 byte with all RAM. |
| `$1E30` | `09 43 3A` | 9 | Jump to `disk_protection` at `$3A43`. |
| `$1E33` | `FF` | - | End. |

The script uses op 37, not op 3. With the I/O on, a write to `$D7E8` goes to the SID, not to the RAM. In the default build, the switch PROTECTION puts `$FF` at `$1E30`. The script then ends before the disk protection (**Code**).

## Worked example: the frame of the menu

![The menu screen after menu_screen_script](images/menu.png)

The menu screen with its frame of 5 columns, from a run (**Observed**).

[`menu_screen_script` `$3EE7`](../src/menu/menu_screen_script.asm#L6) draws this screen. `draw_menu` calls it. The first 73 bytes set the colours, clear the screen and draw the top row and the three divider rows (**Code**).

| Address | Bytes | Op | What it does |
|---|---|---|---|
| `$3EE7` | `01 20 D0` | 1 | Destination = `$D020`. |
| `$3EEA` | `02 04 0F 01 00 04` | 2 | `$D020-$D023` = `$0F`, `$01`, `$00`, `$04`. |
| `$3EF0` | `08 A0 23` | 8 | Call `clear_menu_screen_script`: 1000 spaces at `$5C00`. |
| `$3EF3` | `01 00 D8` | 1 | Destination = `$D800`, the colour RAM. |
| `$3EF6` | `0D 06` | 13 | Fill byte = 6 (blue). |
| `$3EF8` | `0C FA` | 12 | Fill 250 bytes. |
| `$3EFA` | `05 03 F8 3E` | 5 | Jump back to `$3EF8` 3 times: 4 x 250 = 1000 bytes. |
| `$3EFE` | `01 00 5C` | 1 | Destination = `$5C00`, row 0 of the screen. |
| `$3F01` | `02 01 5E` | 2 | Column 0 = `$5E`. |
| `$3F04` | `0D 5F` | 13 | Fill byte = `$5F`. |
| `$3F06` | `0C 06` | 12 | Columns 1-6 = `$5F`. |
| `$3F08` | `02 01 60` | 2 | One `$60`. |
| `$3F0B` | `0C 07` | 12 | Seven `$5F`. |
| `$3F0D` | `05 03 08 3F` | 5 | Jump back to `$3F08` 3 times: `$60` at columns 7, 15, 23 and 31. |
| `$3F11` | `02 01 61` | 2 | Column 39 = `$61`. |
| `$3F14` | `01 A0 5C` | 1 | Destination = `$5CA0`, row 4. |
| `$3F17` | `0D 40` | 13 | Fill byte = `$40`. |
| `$3F19` | `02 01 76` | 2 | Column 0 = `$76`. |
| `$3F1C` | `0C 06` | 12 | Columns 1-6 = `$40`. |
| `$3F1E` | `02 01 5B` | 2 | One `$5B`. |
| `$3F21` | `0C 07` | 12 | Seven `$40`. |
| `$3F23` | `05 03 1E 3F` | 5 | Inner loop to `$3F1E`: `$5B` at columns 7, 15, 23 and 31. |
| `$3F27` | `02 01 78` | 2 | Column 39 = `$78`. |
| `$3F2A` | `0B 78` | 11 | Destination += 120: three rows lower. |
| `$3F2C` | `05 02 19 3F` | 5 | Outer loop: jump back to `$3F19` 2 times. This gives rows 4, 8 and 12. |

The two loops at `$3F23` and `$3F2C` nest. When the outer loop jumps back to `$3F19`, the top entry of the loop stack belongs to `$3F2C`. Thus the op at `$3F23` pushes a new entry and starts again with its count of 3 (**Code**). The characters `$5E`, `$60`, `$61`, `$76`, `$5B` and `$78` are the corners and junctions of the frame. `$5F` and `$40` are its horizontal lines. Their positions in the menu screen show this (**Conclusion**).

The next bytes draw the vertical lines of rows 1-3 with a loop at `$3F45`. Op 11 at `$3F49` then skips row 4. A second op 5 at `$3F4B` jumps to the same address `$3F35`, and gives rows 5-7 and 9-11. This works because the loop stack identifies each loop by the address of the op, not by the target (**Code**).

## The opcodes that no script uses

A scan follows each script from the callers of `run_script` and `start_tool`, the 8 brush scripts and the targets of ops 5, 8 and 35. It finds no use of 18 opcodes: 7, 10, 17-26 and 29-34 (**Code**). Ops 33 and 34 still run as subroutines of ops 4 and 37. A script that the code reaches only through an op in the stack form can be outside the scan (**Conclusion**).

The coverage of the runs agrees. The code of ops 6, 7, 10, 17-27, 29-32 and 36 never ran, and the stack form of op 2 never ran (**Observed**). Op 6 is only in [`wipe_program_script` `$1E71`](../src/script/picture_buffers.asm#L59), which runs when a protection check fails. Ops 27 and 36 are only in storage scripts that the runs did not reach (**Code**).

The unused ops 20-26, 29, 30 and 32 form one group. They set and move a point (`shape_x0`, `shape_y0`) by a step, plot through the JMP table at `$0900`, and push the point. **Conclusion**: the authors made the interpreter to draw shapes too, but the program draws its shapes in 6502 code.

## The odd op 25

[`script_op_set_end_jump` `$4596`](../src/script/opcodes.asm#L333) reads two operands into `shape_x1` and `shape_y1`, and then executes `JMP $091B`. The code is `20 99 43 85 DB 20 99 43 85 DC 4C 1B 09` (**Code**).

The JMP table [`entry_jump_table` `$0900`](../src/init/entry.asm#L6) has 9 entries of 3 bytes, at `$0900-$091A`. Thus `$091B` is the first byte after the table, and in this build it is `cold_start`. If a script used op 25, the program would start again from the cold start. It would set the interrupt again and run the start-up script again (**Code**).

Ops 20 and 26 call the entries `$0915` and `$0918` of the same table. These entries jump to `plot_pixel_bits` and `draw_line`. Version 1 has the same op 25 code, at [`v1:script_op_set_end_jump` `$4437`](../../v1/src/script/opcodes.asm#L333) (**Code**).

**Conclusion**: `$091B` was a tenth entry of the table in an earlier layout, for example a line to the second point (`shape_x1`, `shape_y1`). The interpreter used the table as a stable interface to the program. The authors later removed the entry, but op 25 kept its jump, because no script used it.

## The assets

The [menu screen capture](images/menu.png) shows the result of `menu_screen_script`. The [charset images](reference/images/charset_1f27-hires.png) of the reference show the glyph data inside `menu_charset_script`.
