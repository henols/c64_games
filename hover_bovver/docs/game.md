# The game

Gordon Bennet mows the lawn with a mower that he borrows from a neighbour. The game part of the program moves Gordon from square to square and mows each square that he enters. It counts the grass squares that remain, adds the points to the score and keeps three scales on the status rows. It ends a lawn when no grass remains, and it ends a game when the neighbours catch Gordon three times. The neighbour, Rover and the gardener have their own page: [actors.md](actors.md). The reference lists each routine and variable: [reference/index.md](reference/index.md).

![Lawn 1 in play, with the three scales, the score and the lender on the status rows](images/lawn_01.png)

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of the main loop. A *frame* is one raster interrupt, 1/50 second on a PAL C64.
- A *square* is one character cell of the lawn. The lawn has 40 columns and 21 rows, rows 0-20. Row 21 shows the messages, rows 22-24 are the status rows.
- A *step* is one move of Gordon: 2 pixels to the side, or 2 raster lines up or down. Four steps move Gordon by one square.
- A *scale* is one of the three bars on the status rows. A *cell* is one character of a scale. A cell has 8 *scale steps*.
- A *lender* is the neighbour who owns the mower: JIM, TOM or ALF. The number of the lender is also the number of the mower, 1-3.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## A pass of the main loop

The main loop has no wait for the raster. It runs a fixed delay, then four timers. Each timer counts passes, and a timer at 0 starts its task. Thus the pass is the clock of the game: Gordon, the actors and the cooling all count passes.

~~~mermaid
flowchart TB
  A["Delay: 128 loops, restart the tune (main_loop_delay)"] --> B["Gordon's timer (gordon_timer)"]
  B -->|"timer 0"| C["Fire button, then one step of Gordon (gordon_move)"]
  B --> D["Cooling of the mower: each 192 passes (mower_cooling)"]
  C --> D
  D --> E["Keys and voice 3: each 16 passes (sound_key_tick)"]
  E --> F["Actor timer (tick_actors)"]
  F -->|"timer 0"| G["Move the actors (move_actors)"]
  F --> A
  G --> A
~~~

[`main_loop` `$9082`](../src/game/main_loop.asm#L21) calls these parts in this order:

1. **The delay sets the pace.** [`main_loop_delay` `$9094`](../src/game/main_loop.asm#L39) counts 128 DEY loops. Then `restart_tune_if_ended` starts the main tune again when the interrupt stopped it at its end (**Code**).
2. **Gordon's timer.** [`gordon_timer` `$91F5`](../src/player/gordon_timer.asm#L6) counts `gordon_step_timer` down. At 0, it loads 69 - 8 x `gordon_speed` and moves Gordon one step. The section below tells the details (**Code**).
3. **The cooling.** `mower_cooling` removes one scale step from MOWER OVERLOAD each 192 passes (**Code**).
4. **The keys and voice 3.** `sound_key_tick` runs each 16 passes. It checks the C= keys, and it makes the mower noise, the overheat noise or the bark of Rover on SID voice 3 (**Code**).
5. **The actors.** `tick_actors` counts `actor_timer` down. At 0, it loads the period `actor_speed` of the lawn and moves the actors (**Code**).

A pass in which no timer gets to 0 takes about 750 cycles. The delay takes 671 cycles, and the four timer calls take about 80 cycles (**Code**). A PAL frame has 19,656 cycles, so not more than 26 passes fit into one frame. The bad lines and the KERNAL part of the interrupt use a part of each frame, so the true number is smaller (**Conclusion**).

The trainer TRAINER_HYPERSPEED of the Hokuto Force release writes LDA in place of the JSR to the delay. Then each timer gets to 0 after fewer cycles, and the full game runs faster (**Code**).

The interrupt `irq_handler` runs on raster line 0 of each frame. It plays the tune, and it counts the message timer `message_timer`. A message stays for 48 tune steps of 3 frames, about 3 seconds. Then the interrupt clears row 21 (**Code**).

## Gordon moves in squares and steps

Gordon is two sprites. Sprite 1 shows the mower, with one frame for each direction. Sprite 0 shows Gordon behind the mower, with 3 walk frames for each direction. [`place_mower_and_gordon` `$8F8E`](../src/player/place_mower.asm#L6) puts the mower at `gordon_x`, `gordon_y` and Gordon at an offset from a table of the direction (**Code**).

`gordon_x` is half of the sprite X position, because `set_sprite_position` doubles it. A step adds or subtracts 1 from `gordon_x`, or 2 from `gordon_y`. Thus a step is 2 pixels, and four steps make a square of 8 x 8 pixels. A move to a new square sets `gordon_steps` to 4 (**Code**).

Each time that Gordon's timer gets to 0, [`gordon_move` `$909D`](../src/player/gordon_move.asm#L6) does these things in this order:

1. **It reads the fire button.** `dog_command` sends Rover after the neighbour while the button is down. The game reads the fire button only here, at the timer of Gordon (**Code**).
2. **It stops while the mower is too hot.** With `mower_overheated` = 1, the routine returns. Gordon stands still, but the fire button still works (**Code**).
3. **It makes one step.** With steps left, Gordon moves one step in the direction `gordon_dir`, and the walk frame changes (**Code**).
4. **It tests the grass counter.** With no steps left, Gordon is on a square. When `grass_count` is 0, the lawn is complete (**Code**).
5. **It mows the next square.** The game mows the square ahead of Gordon at the start of the four steps. Then it tests the square after it. The hedge characters `$7C-$7F` and the edges of the lawn block the way (**Code**).
6. **It reads the joystick.** [`gordon_read_stick` `$917A`](../src/player/gordon_joystick.asm#L6) compares the stick with the direction. The same direction adds 1 to `gordon_speed`, up to 7, and starts four new steps. A new direction turns Gordon and sets the speed to 0. No direction stops Gordon (**Code**).

A block sets the speed to 0, stops Gordon and keeps the direction in `gordon_blocked_dir`. The stick in that direction then does nothing (**Code**).

The speed gives the time of a step: 69 passes at speed 0, 61 at speed 1, and 13 at speed 7. A square takes four steps, so Gordon at full speed needs 52 passes for a square (**Code**). The speed goes up by 1 on each square while the player holds the stick in one direction. Thus the seventh square in a straight line has the full speed (**Conclusion**).

The trainer TRAINER_SKIP_LEVEL replaces the call of `read_joystick` at the start of `gordon_read_stick` with a call of `$2A00`. This routine of the Hokuto Force release is not in the program, so the switch alone does not work in the rebuild (**Code**).

## Mowing and the grass counter

The lawn has four kinds of squares that Gordon can enter. [`mow_square` `$920A`](../src/lawn/mow_square.asm#L6) changes the character of the square and starts the effects (**Code**).

| Character | Square | Mowing gives | Effects |
|---|---|---|---|
| `$73` | grass | `$7B` | grass counter - 1, MOWER OVERLOAD + 1 scale step, score + lawn number |
| `$76` | flowers | `$77` | MOWER OVERLOAD + 2 scale steps, the gardener comes |
| `$7B` | mown grass | `$7B` | none |
| `$77` | mown flowers | `$77` | none |
| `$7C-$7F` | hedge | Gordon cannot enter | none |

[`setup_lawn` `$8AC2`](../src/lawn/setup_lawn.asm#L6) fills rows 0-20 with grass and sets the grass counter to 840, which is 40 x 21. Then `draw_lawn_layout` draws the flower beds and the hedges of the lawn from `lawn_layouts`. For each square that is not grass, it calls [`dec_grass_counter` `$8B10`](../src/lawn/lawn_shapes.asm#L6). Thus the counter holds the number of grass squares, and each mown square subtracts 1 (**Code**).

The flower beds do not count, so the player does not have to mow them. A mown flower only heats the mower and calls the gardener (**Code**).

When the grass counter is not 0 at the start of a lawn, `setup_lawn` restores the saved lawn of the player. The section about two players tells why (**Code**).

## The score

The score has no variable. It is 7 digits on the screen, at `$0790-$0796` on row 22. [`score_add` `$92FD`](../src/scores/score_add.asm#L6) adds 1 to digit X, Y times. A digit after 9 becomes 0 and adds 1 to the digit on its left. A carry out of the first digit is lost (**Code**).

| Event | Digit | Points |
|---|---|---|
| A mown grass square | 7, the units | the lawn number |
| Rover touches the neighbour in an attack | 7, the units | 1 at each move of Rover |
| A scale step of DOG LOYALTY at the end of a lawn | 6, the tens | 10 x the lawn number |

`score_add_lawn` adds the lawn number for each grass square. Thus a square of lawn 5 gives 5 points (**Code**). The status buffer of the player keeps the score with the status rows. The section about two players tells more (**Code**).

## The three scales

The status rows show three scales in columns 16-30. Each scale has 15 cells, and each cell has 8 scale steps, so a scale has 120 scale steps. The variable of a scale holds the column of its last cell that is not empty (**Code**).

| Scale | Row | Variable | Start | Goes down | Goes up |
|---|---|---|---|---|---|
| DOG LOYALTY | 22 | `loyalty_bar` | `$1E`, full | one scale step for each `loyalty_rate` reads of the fire button while it is down, and the bonus | never |
| DOG TOLERANCE | 23 | `tolerance_bar` | `$1E`, full | one scale step for each 12 moves of each actor, and empty when Gordon touches Rover | never |
| MOWER OVERLOAD | 24 | `overload_bar` | `$10`, empty | one scale step each 192 passes | 1 scale step for grass, 2 for flowers, full when Gordon touches Rover |

The value `$0F` marks an empty dog scale. A dog scale only goes down during a lawn. `lawn_play_start` fills both dog scales and empties MOWER OVERLOAD at the start of each lawn, and after each lost mower (**Code**).

[`scale_chars` `$922B`](../src/status/scale_chars.asm#L6) holds the 9 characters of a cell, from empty to full: `$20`, `$2A`, `$29`, `$28`, `$26`, `$25`, `$24`, `$23` and `$22`. A step routine reads the character of the cell and finds it in the table. A step up writes the next character, and a step down writes the character before it. When a cell is full or empty, the routine moves the column by one (**Code**).

The colours of the dog scales go from blue to white in pairs of cells. The colours of MOWER OVERLOAD are 5 green, 5 yellow and 5 red cells (**Code**).

- **The dog scales control Rover.** An empty DOG LOYALTY stops the attacks of Rover. An empty DOG TOLERANCE makes Rover chase Gordon. The details are on [actors.md](actors.md) (**Code**).
- **The fire button drains DOG LOYALTY with the speed of Gordon.** The game reads the button only when the timer of Gordon gets to 0. At speed 7 this happens each 13 passes, at speed 0 each 69 passes. Thus an attack of the same length costs more loyalty while Gordon moves fast (**Code**, **Conclusion**).
- **Kraksnax changed two cell characters.** The release KSX has `$2E,$0D` in place of `$2A,$29` at `$922C-$922D`. Its scales thus show other characters at 2 of the 8 scale steps (**Code**). The switch CRACK_KSX_RELOCATE puts these bytes in.

## Overheating and cooling

Each mown square heats the mower. When MOWER OVERLOAD is full, the mower stops until it cools again. [`overload_step_up` `$9283`](../src/status/mower_overload.asm#L6) adds one scale step. It also starts the mower noise on voice 3 when Rover does not attack (**Code**).

When the last cell is full, the column moves to `$1F`. Then the routine sets the column back to `$1E` and the mower overheats (**Code**):

1. Voice 3 plays a triangle tone.
2. `mower_overheated` becomes 1. `gordon_move` then reads the fire button and returns, so Gordon stands still.
3. Message 9 shows: "OH RATS!.. THE MOWER HAS OVERHEATED!".
4. Each 16 passes, `sound_key_tick` changes the colour of sprite 0, which is Gordon, and sets the pitch of voice 3 from that colour.

[`mower_cooling` `$9234`](../src/status/mower_cooling.asm#L6) removes one scale step each 192 passes, also while the mower runs. The column does not go below `$10`. When an empty cell moves the column to `$19`, the routine starts the mower again. It clears `mower_overheated` and `dog_bit_gordon`, starts the noise on voice 3 and makes sprite 0 yellow again (**Code**).

From the overheat to the restart, the mower loses the scale steps of 5 cells. That is 40 scale steps or 7,680 passes, about 6 seconds or more (**Conclusion**). At full speed Gordon mows a square each 52 passes, and the cooling removes a scale step each 192 passes. Thus about 165 grass squares in one run fill an empty scale (**Conclusion**).

The overheat recording fills the MOWER OVERLOAD row and its column with a test write. Then the mower overheats (**Observed**).

When Gordon touches Rover, `gordon_hits_dog` fills MOWER OVERLOAD at once and stops the mower in the same way. The code that shows message 10 "DAMNATION!! I'VE HIT THE DOG!" is at `$977A-$9782`, but the loop jumps over it. Thus this message never shows (**Code**). The details are on [actors.md](actors.md).

The trainer TRAINER_NO_OVERLOAD writes LDA #0 in place of the DEC of `cooldown_timer`. Then the cooling removes a scale step on each pass, and the scale stays almost empty (**Code**).

## The end of a lawn and the bonus

When Gordon is on a square and the grass counter is 0, `gordon_move` jumps to [`lawn_complete` `$99C5`](../src/lawn/lawn_complete.asm#L6). The routine does not return to the main loop (**Code**).

![The end of a lawn: WELL DONE! and the CANINE FIDELITY BONUS](images/lawn_complete.png)

1. Voice 3 plays 6 rising sweeps, and the background colour 2 changes at each step (**Code**).
2. `save_lawn_scroll_out` scrolls the lawn out to the left (**Code**).
3. Row 10 shows "WELL DONE!   PREPARE FOR MORE MOWING!". "WELL DONE!" flashes through all colours for 32 x 256 colour steps, with a sawtooth tone on voice 3 (**Code**).
4. When DOG LOYALTY is not empty, [`fidelity_bonus` `$9A34`](../src/lawn/lawn_complete.asm#L68) shows "CANINE FIDELITY BONUS" on row 13. For each scale step of DOG LOYALTY, it adds 10 x the lawn number to the score. Then it plays a rising tone and removes the scale step (**Code**).
5. [`next_lawn` `$9A26`](../src/lawn/lawn_complete.asm#L60) adds 1 to `lawn_number`, saves and loads the player state, and resets the stack. Then it jumps to `setup_lawn` (**Code**).

A full DOG LOYALTY scale gives 120 x 10 x the lawn number points, which is 1,200 points on lawn 1. Lawn 1 has 360 grass squares, so the bonus is more than three times the points of the grass. Thus each attack of Rover costs bonus points (**Conclusion**).

After lawn 16 the layouts repeat: lawn 17 has the layout of lawn 1. The actors move at the maximum speed from lawn 17 (**Code**). The run of all 16 lawns reaches this repeat (**Observed**).

## The lenders and the end of a game

A player has three mowers. `mower_lender` holds the number of the mower: 1 is the mower of JIM, 2 of TOM, and 3 of ALF. Before each mower, `borrow_mower_scene` shows Gordon at the house of the lender, and message 0, 1 or 2 shows the words of Gordon. The status rows show the name of the lender in "JIM'S MOWER", on two rows (**Code**).

When the neighbour or the gardener catches Gordon, `actor_catches_gordon` takes the mower and scrolls the lawn out. Then [`next_mower_or_player` `$98B0`](../src/neighbour/neighbour_catch.asm#L153) selects the next step (**Code**):

1. With one player, [`next_mower` `$98B9`](../src/neighbour/neighbour_catch.asm#L158) adds 1 to `mower_lender`. At 4, the game is over. Else the player borrows the next mower and mows the same lawn again (**Code**).
2. With two players, `switch_player` gives the turn to the other player. The game is over when the mower number of player 2 gets to 4 (**Code**).

[`game_over` `$9D37`](../src/game/game_over.asm#L6) writes "GAME OVER" on each row of the lawn with a falling tone. Then it clears the rows and goes to the high-score check `hiscore_check` (**Code**).

- **The fourth name never shows.** `lender_names` has a fourth name, JCM, for Jeff C. Minter. A mower number of 4 always ends the game or the turn of the player before the status rows show it (**Code**, **Conclusion**).
- **The infinite lives work only for one player.** The trainer TRAINER_LIVES changes the INC of `mower_lender` in `next_mower` to LDA. `switch_player` has its own INC of `mower_lender`, which the trainer does not change. Thus in a game of two players each player still has three mowers (**Code**).

## Two players and the saved lawns

Each player has a lawn, a score and a mower of his own. The game keeps them in three areas for each player and changes the areas at each change of the turn (**Code**).

| Data | Player 1 | Player 2 | Content |
|---|---|---|---|
| State | `$4F01-$4F08` | `$4F11-$4F18` | copies of `$20-$27`: mower number, lawn number, grass counter |
| Status rows | `$4000-$4077` | `$4080-$40F7` | rows 22-24: the scales, the score, the name of the lender |
| Lawn characters | `$5000-$536F` | `$5400-$576F` | rows 0-21 of the screen |
| Lawn colours | `$5800-$5B6F` | `$5C00-$5F6F` | rows 0-21 of the colour RAM |

A player keeps the turn until an actor catches Gordon. A complete lawn does not change the turn (**Code**).

1. [`save_lawn_scroll_out` `$9828`](../src/neighbour/neighbour_catch.asm#L71) copies and scrolls in one action. It stores the character and the colour of column 0, and moves the row one column to the left. It does this 40 times for each row (**Code**).
2. [`switch_player` `$998A`](../src/player/player_state.asm#L66) resets the stack and adds 1 to the mower number of the player. With two sticks, it changes `joy_port` between port 1 and port 2. Then `save_player_state` stores the state and the status rows (**Code**).
3. `save_player_state` first makes the dog scales full and MOWER OVERLOAD empty on the screen. Thus the status buffer always holds the scales of a new start (**Code**).
4. `player_turn_intro` shows "PLAYER ONE" or "PLAYER TWO" and plays the jingle. Then the borrow scene of the lender follows (**Code**).
5. `setup_lawn` finds a grass counter that is not 0, so [`restore_lawn` `$98D0`](../src/neighbour/neighbour_catch.asm#L180) copies the saved lawn back to the screen (**Code**).

The saved lawn keeps the mown squares and the mown flowers. Gordon, the actors and the scales start again from their start values (**Code**). The two-player recording plays a game of two players with two sticks (**Observed**).

## The keys C= + M and C= + P

The game reads two key commands. [`check_keys` `$9D0B`](../src/input/keys.asm#L6) runs each 16 passes from `sound_key_tick`. It reads the C= flag in `SHFLAG` and the key code in `LSTX`, which the KERNAL part of the interrupt updates (**Code**).

| Keys | Effect |
|---|---|
| C= + M | The music goes off or on. The routine waits until the player releases M. |
| C= + P | The game stops. The routine waits until the player releases P, then until the player presses any key. |

C= + M changes `music_off`. The tune player then keeps the gates of voices 1 and 2 closed, but the tune continues. The sound effects on voice 3 stay on (**Code**). During the pause the main loop stops, but the interrupt still plays the tune (**Code**). The keys recording presses C= + M, C= + P, Q and C= + M again, and the code of both commands ran (**Observed**).

## The random numbers

The game has two sources of random numbers. Both read the raster line `$D012` (**Code**):

- [`actor_new_random` `$9585`](../src/actors/actor_random.asm#L12) gives a new direction and a new time to an actor that wanders, in practice Rover.
- [`dog_sound_random_pause` `$96B6`](../src/sound/dog_sound.asm#L23) gives the pause between two barks of Rover.

The main loop does not wait for the raster. Thus the raster line depends on the time of each pass and on the input of the player (**Conclusion**). The lawns, the start positions and the speeds never change. The recordings store the values of the reads of `$D012`, and each replay of a recording gives the same game (**Observed**).

## Worked example: the grass of lawn 1

`draw_lawn_layout` finds lawn 1 after the first `$FF` of `lawn_layouts`, at `$8C6F`. The layout has 10 records. Each rectangle has the bytes character, column, row, width, height and colour. `$F6` is the flower character `$76` with bit 7, so the squares do not count as grass (**Code**).

| Bytes | Shape | Squares that are not grass |
|---|---|---|
| `F6 01 01 06 13 04` | flowers, columns 1-6, rows 1-19 | 114 |
| `F6 21 01 06 13 04` | flowers, columns 33-38, rows 1-19 | 114 |
| `F6 07 01 06 06 07` | flowers, columns 7-12, rows 1-6 | 36 |
| `F6 07 0E 06 06 07` | flowers, columns 7-12, rows 14-19 | 36 |
| `F6 1B 01 06 06 07` | flowers, columns 27-32, rows 1-6 | 36 |
| `F6 1B 0E 06 06 07` | flowers, columns 27-32, rows 14-19 | 36 |
| `7C 0F 01 13` | hedge, columns 15-16, rows 1-19 | 38 |
| `7C 17 01 13` | hedge, columns 23-24, rows 1-19 | 38 |
| `F6 12 01 04 04 03` | flowers, columns 18-21, rows 1-4 | 16 |
| `F6 12 10 04 04 03` | flowers, columns 18-21, rows 16-19 | 16 |

No two shapes cover the same square. The shapes cover 480 squares, so the grass counter starts at 840 - 480 = 360 (**Code**). Gordon starts on column 18, row 20, and he faces to the right (**Code**).

Lawn 1 thus gives 360 points for the grass. A full DOG LOYALTY at the end adds 1,200 points, for 1,560 points in total. Each catch of the neighbour by Rover adds 1 point more (**Conclusion**).

## Still open

- How many passes does a frame hold in play? A run that counts the calls of `main_loop` over 50 frames can measure it, also with TRAINER_HYPERSPEED on.
- Does the mown trail follow Gordon after a turn without a stop? A straight move sets `gordon_col` to the next square before the stick read. A turn then starts from that square, and not from the square of the sprite (**Code**). A run with a turn on fresh grass and a screen capture can show the trail.
- The grass counter of each of the 16 lawns. A run that reads `grass_count` after each `setup_lawn` gives the list.
