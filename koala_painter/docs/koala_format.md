# The Koala picture file

Koala Painter keeps each picture in one file of 10003 bytes. The file is a copy of the picture memory: the bitmap, the two colour tables and the background colour. Both versions of Koala Painter use the same layout. This page gives the layout, the names of the files on the disk, and one cell of a real picture decoded by hand.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge of each version, with the label of the version, for example `v2:save_picture`.
- A *cell* is one 4x8 block of multicolour pixels, the size of one character of the screen.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## Where the data is

The program keeps the picture in two parts of memory. The bitmap is at `$6000-$7F3F`, where the VIC-II shows it. While the menu shows, the program keeps the other 2001 bytes of the picture at `$C000-$C7D0`, in the same order as the file. Thus a save is two blocks of memory, and a load fills the same two blocks (**Code**).

[`v2:save_picture` `$3351`](../v2/src/storage/picture_file.asm#L28) opens the file with secondary address 1. It sends the load address `$6000`, then the bytes of `$6000-$7F3F` and `$C000-$C7D0`. [`v2:load_picture` `$33A6`](../v2/src/storage/picture_file.asm#L73) opens the file with secondary address 0. It reads the 2 bytes of the load address and does not use them. Then it fills the same two blocks. Both routines call the KERNAL byte routines directly (**Code**).

## The byte layout

| File offset | Bytes | Memory | Content |
|---|---|---|---|
| 0-1 | 2 | | Load address `$6000` (bytes `$00`, `$60`) |
| 2-8001 | 8000 | `$6000-$7F3F` | Bitmap: 1000 cells of 8 bytes, row by row, 40 cells in a row |
| 8002-9001 | 1000 | `$C000-$C3E7` | Screen colours: high nybble = colour of pixel value 1, low nybble = colour of pixel value 2 |
| 9002-10001 | 1000 | `$C3E8-$C7CF` | Colour RAM: low nybble = colour of pixel value 3 |
| 10002 | 1 | `$C7D0` | Background colour: the colour of pixel value 0 |

Each bitmap byte holds 4 pixels of 2 bits, the left pixel in bits 7-6. A pixel value selects one of 4 colours. Value 0 is the background. Values 1 and 2 are the two nybbles of the screen byte of the cell. Value 3 is the colour RAM byte of the cell. Thus each cell can have 3 colours of its own and the background colour (**Code**).

The colour RAM of the C64 keeps only 4 bits. A save writes the colour RAM bytes from `$C3E8`, and their upper nybbles are not defined. A round trip run saved the sample picture PIC D FARM as a new file and loaded it again. All 8000 bitmap bytes, all 1000 screen bytes and the background byte came back the same. The 1000 colour RAM bytes came back with the same low nybbles, and many upper nybbles changed (**Observed**).

## The file names

Storage shows 16 slots, PIC A to PIC P. A file name has 15 characters. They are the byte `$81`, the text `PIC `, the letter of the slot, a space and up to 8 characters of the name. The Storage screen lists only the files whose names start with `$81` and `PIC ` (**Code**).

The release disks have sample pictures in this form:

- The MAM disk has 13 pictures, PIC A to PIC M. Their names are ABC'S, VAN, VANPROPS, FARM, FARMANIM, JUNGLE, MONKEY, CASTLE, DRAGON, TREE, VAN2, IC and ZAXXON.
- The Mayday! disk has 8 pictures, PIC A to PIC H: ABC'S, VAN, PROPVAN, FARM, FARMANIM, JUNGLE, MONKEY and TREE.

Each file has 40 blocks of the disk (**Observed**).

## A worked example

The first cell with three different pixel values in PIC D FARM is cell 33, in the top row of cells at column 33. Line 5 of that cell is bitmap byte 269, at file offset 271 and address `$610D`.

![The FARM sample picture after Get](../v2/docs/images/farm_picture.png)

The FARM picture after Get: the sun in the upper right corner is in cell 33.

| Item | File offset | Value | Meaning |
|---|---|---|---|
| Bitmap byte | 271 | `$E0` = `11 10 00 00` | Pixel values 3, 2, 0, 0 |
| Screen byte | 8035 | `$E7` | Value 1 = light blue, value 2 = yellow |
| Colour RAM byte | 9035 | `$FA` | Value 3 = light red |
| Background | 10002 | `$01` | Value 0 = white |

Thus the 4 pixels of this line are light red, yellow, white and white. This agrees with the picture: the sun has light red and yellow lines (**Observed**).

## The decoder

```text
load the file at $6000 (or read its 2 address bytes and ignore them)
for cell = 0 to 999:
    for line = 0 to 7:
        byte = bitmap[cell * 8 + line]
        for p = 0 to 3:
            value = (byte >> (6 - 2 * p)) & 3
            colour = background         if value = 0
                     screen[cell] >> 4  if value = 1
                     screen[cell] & 15  if value = 2
                     colour[cell] & 15  if value = 3
            plot 2 screen pixels at x = (cell mod 40) * 8 + p * 2, y = (cell div 40) * 8 + line
```

## Still open

- The project does not show where the sample pictures come from. The MAM disk has 5 pictures more than the Mayday! disk, and "PIC C" has a different name on each disk. A comparison with a disk image of an original release can tell which pictures came with the program.
