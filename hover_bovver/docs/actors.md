# The actors

Three actors share the lawn with Gordon. Rover, the dog, walks at random and attacks the neighbour when the player holds the fire button. The neighbour wants his mower back and chases Gordon. The gardener comes when Gordon mows the flowers, and he also chases Gordon. When the neighbour or the gardener touches Gordon, the player loses the mower. The actor code moves all of them with one set of tables and four modes. The main loop, the scales and the score are on [game.md](game.md). The reference lists each routine and variable: [reference/index.md](reference/index.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of the main loop. A *frame* is one raster interrupt.
- An *actor* is one of the moving figures of the actor tables, number 1-4. Gordon is not an actor.
- An *actor tick* is one call of `move_actors`. It comes each `actor_speed` passes.
- A *move* is one change of the position of one actor: 2 raster lines up or down, and 2 pixels to the side.
- A *mode* is the behaviour of an actor: 0 chase Gordon, 1 flee from Rover, 2 attack the neighbour, 3 wander.
- A *scale step* is one of the 8 parts of a cell of a status scale.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How the actors move

The actors move on their own clock. `tick_actors` counts passes, and each `actor_speed` passes it calls [`move_actors` `$9374`](../src/actors/actor_move.asm#L6). This routine handles the actors from `actor_count` down to 1. `actor_count` is 2 at the start of a lawn: Rover and the neighbour. The gardener makes it 3 (**Code**).

1. **Each actor has its own delay.** `move_actors` counts `actor_delay` of the actor down. At 0, the actor moves. An actor in mode 2 moves at each actor tick (**Code**).
2. **The move loads the delay again.** `move_actor` copies the delay of the actor from `actor_step_delay`. Each 3 moves, the animation frame changes. After 4 frames, it calls `dog_tolerance_tick`, which removes a scale step of DOG TOLERANCE (**Code**).
3. **The mode gives the direction.** [`actor_direction` `$9434`](../src/actors/actor_direction.asm#L6) selects the target of the mode. It divides both positions by 4, compares them and sets the bits of `actor_dir` (**Code**).
4. **The collision test runs before the move.** `actor_collisions` compares the actor with its target and with Gordon. The section about a catch tells the details (**Code**).
5. **The actor moves on both axes.** The routine adds or subtracts 2 from the Y position and tests the new place. Then it adds or subtracts 1 from the X position and tests again. A blocked axis keeps its old value (**Code**).
6. **The sprite follows.** `actor_set_frame` selects the frame, and `set_sprite_position` puts sprite X + 1 at the new position (**Code**).

[`actor_test_place` `$94C2`](../src/actors/actor_place_test.asm#L6) turns the position into a square: column = (X - 8) / 4 and row = (Y - 40) / 8. Grass `$73`, mown grass `$7B` and mown flowers `$77` are free for all actors. Flowers `$76` are free for the neighbour and for actor 4, but they block Rover and the gardener. The hedges and the edges block all actors (**Code**).

- **An actor always moves on a diagonal.** The direction has a bit for each axis and no value for "no move". Thus each move changes X and Y, unless a hedge or an edge blocks one axis (**Code**).
- **An actor on the line of its target walks in a zigzag.** With equal positions divided by 4, the compare sets the bit for up or for left. The next move then goes back (**Code**).
- **DOG TOLERANCE drains with each actor.** `dog_tolerance_tick` runs after each 12 moves of each actor, not only of Rover. Thus the gardener and the attacks of Rover make the scale go down faster (**Code**). On lawn 1 without fire, Rover and the neighbour remove one scale step each 288 passes, so the full scale lasts 34,560 passes (**Conclusion**).

## The actor tables

The actor tables are at `$1F00-$1F6F`. Each table has 16 bytes, and the code reads it with X = 1-4. The entry of Rover is at offset 1, the entry of the neighbour at offset 2 (**Code**).

| Table | Offset | Content |
|---|---|---|
| `actor_x` | `+$00` | X position, half of the sprite X |
| `actor_y` | `+$10` | Y position, the sprite Y |
| `actor_delay` | `+$20` | actor ticks to the next move |
| `actor_mode` | `+$30` | mode 0-3 |
| `actor_wander_time` | `+$40` | moves to the next random direction, mode 3 only |
| `actor_frame` | `+$50` | animation frame 0-3. Frame 3 shows frame 1 again |
| `actor_frame_delay` | `+$60` | moves to the next animation frame |

[`init_actors` `$8FF6`](../src/actors/init_actors.asm#L18) fills the tables at the start of each lawn and after each lost mower. It copies the position and the mode from three start tables, sets the delays and the frames to 1, and sets the sprite colours (**Code**).

| Actor | Who | Sprite | Colour | Start X | Start Y | Start mode | Moves each |
|---|---|---|---|---|---|---|---|
| 1 | Rover | 2, hires | black | `$64` | `$2E` | 3, wander | 3 actor ticks |
| 2 | the neighbour | 3, multicolour | yellow | `$1E` | `$2E` | 0, chase | 6 actor ticks |
| 3 | the gardener | 4, multicolour | dark grey | `$46` | `$2E` | 0, chase | 4 actor ticks |
| 4 | none | 5 | light red | `$00` | `$2E` | 0, chase | 3 actor ticks |

All actors start on row 0, at the top of the lawn. Rover starts in column 23, the neighbour in column 5 and the gardener in column 15 (**Code**). On lawn 1, Rover and the gardener thus start just above the two hedges (**Conclusion**).

Actor 4 never moves. `actor_count` is at most 3, and no code turns on sprite 5 (**Code**). The tables still hold a full entry for it, so the author probably planned a fourth actor (**Conclusion**).

## The modes

Each actor has a mode in `actor_mode`. [`dog_command` `$95C0`](../src/dog/dog_command.asm#L6) sets the modes of all three actors each time that the timer of Gordon gets to 0. Thus the fire button acts at the speed of Gordon (**Code**).

| Mode | Target | Direction |
|---|---|---|
| 0, chase | Gordon: `gordon_x` and the Y of sprite 1 | to the target |
| 1, flee | Rover | away from the target: both bits inverted |
| 2, attack | the neighbour | to the target |
| 3, wander | none | a random direction for a random number of moves |

In mode 3, [`actor_random_direction` `$957B`](../src/actors/actor_random.asm#L6) counts `actor_wander_time` down. At 0, it reads the raster line `$D012`. The value AND 3 gives the direction, and the value AND `$3F` gives the number of moves (**Code**). Only Rover uses mode 3.

The modes of Rover change with the fire button and the dog scales:

~~~mermaid
stateDiagram-v2
  state "Wander (3)" as Wander
  state "Attack the neighbour (2)" as Attack
  state "Chase Gordon (0)" as Chase
  [*] --> Wander
  Wander --> Attack: fire, DOG LOYALTY not empty
  Attack --> Wander: no fire
  Wander --> Chase: DOG TOLERANCE empty, no bite
  Attack --> Chase: DOG TOLERANCE gets empty
  Chase --> Wander: bite of Gordon
  Chase --> Attack: fire, DOG LOYALTY not empty
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Rover, wander | fire down, DOG LOYALTY not empty | Rover, attack | `dog_attack` |
| Rover, attack | fire up, or DOG LOYALTY empty | Rover, wander, or chase as in the next row | `dog_no_attack` |
| Rover, wander | fire up, DOG TOLERANCE empty, `dog_bit_gordon` = 0 | Rover, chase | `dog_no_attack` |
| Rover, any | the last cell of DOG TOLERANCE gets empty | Rover, chase | `dog_tolerance_step_down` |
| Rover, chase | Rover touches Gordon | Rover, wander at the next fire read | `gordon_hits_dog` |
| Neighbour, gardener | fire down, DOG LOYALTY not empty | flee | `dog_attack` |
| Neighbour, gardener | fire up | chase | `dog_others_chase` |
| Neighbour, chase | Rover near, fire up | flee | `neighbour_near_dog` |

## Rover

Rover is the friend of Gordon. He wanders on the lawn until the player sends him after the neighbour. He bites Gordon when DOG TOLERANCE is empty, and when Gordon touches him (**Code**).

- **The attack.** With the fire button down and DOG LOYALTY not empty, [`dog_attack` `$95E9`](../src/dog/dog_command.asm#L30) shows message 4, "ROVER.. KILL!! GO ON, BOY! SIEZE! KILL!". Rover takes mode 2, and the neighbour and the gardener take mode 1. Each `loyalty_rate` reads of the button remove one scale step of DOG LOYALTY (**Code**).
- **The attack is fast.** In mode 2, Rover moves at each actor tick, 3 times as often as in mode 3 (**Code**).
- **The attack gives points.** When Rover in mode 2 reaches the neighbour, the score gets 1 point, and message 5 shows "AAARGH! LAY OFF, YOU BEASTLY HOUND!". Each move of Rover near the neighbour gives 1 point more. The neighbour does not stop, and he does not lose anything (**Code**). The overheat recording holds the fire button, and Rover reaches the neighbour (**Observed**).
- **The bark.** During an attack, `sound_key_tick` calls `dog_attack_sound` each 16 passes. The sound rises in 8 steps on voice 3, then it waits for a random pause from the raster line (**Code**).
- **The anger.** When the last cell of DOG TOLERANCE gets empty, [`dog_tolerance_step_down` `$9624`](../src/dog/dog_tolerance.asm#L6) sets Rover to mode 0 and shows message 8, "OH DEAR... THE DOG LOOKS ANNOYED...!". From then on, `dog_command` keeps Rover in mode 0 while the fire button is up and no bite blocks it (**Code**).

### The bite

When Rover touches Gordon, [`gordon_hits_dog` `$9751`](../src/actors/actor_collision.asm#L100) runs. It sets `dog_bit_gordon` to 3, fills MOWER OVERLOAD with full cells and empties DOG TOLERANCE. Then it stops the mower with `mower_overheated` = 1 (**Code**).

1. While `dog_bit_gordon` is 3, a second touch does nothing, and `dog_command` keeps Rover in mode 3 (**Code**).
2. The cooling of the mower clears `dog_bit_gordon` when the scale gets back to column `$19` (**Code**).
3. DOG TOLERANCE is still empty, so Rover takes mode 0 again and chases Gordon. Only the fire button stops him while DOG LOYALTY lasts (**Code**).

Thus after the first bite, Rover bites Gordon again after each restart of the mower. This continues until the lawn ends or the player loses the mower (**Conclusion**).

The bite has a message that never shows. The fill loop of MOWER OVERLOAD exits to `hit_dog_clear_tolerance` at `$9783`. The code at `$977A-$9782` shows message 10, "DAMNATION!! I'VE HIT THE DOG!", but no jump goes there (**Code**). No run executed it (**Observed**).

The trainer TRAINER_DOG_TOLERANCE of the Hokuto Force release puts an RTS at the start of `dog_tolerance_step_down`. Then DOG TOLERANCE never goes down slowly, but a bite still empties it (**Code**).

## The neighbour

The neighbour owns the mower. At the start of each lawn, `lawn_play_start` prints message 3 with his words, "COME BACK HERE WITH MY LAWNMOWER!!". `print_message` shows a message only when the message timer is 0 (**Code**). He chases Gordon in mode 0 and moves each 6 actor ticks, half as often as Rover (**Code**).

[`neighbour_near_dog` `$9665`](../src/neighbour/neighbour_flee.asm#L6) makes him afraid of Rover. When Rover is near him, the neighbour takes mode 1 and walks away from Rover. "Near" is an X difference of -16 to 15 and a Y difference of -24 to 23. That is about 32 pixels to each side and 24 raster lines up and down (**Code**). The routine runs only when Rover does not attack (**Code**).

Thus Rover protects Gordon also without the fire button. A player can keep Rover between Gordon and the neighbour. But Rover wanders at random, so this protection does not last (**Conclusion**).

The neighbour walks across the flower beds, which block Rover and the gardener (**Code**).

## The gardener

The gardener protects the flowers. When Gordon mows a flower square, `mow_square` calls [`gardener_start` `$960C`](../src/gardener/gardener_start.asm#L6). This routine sets `actor_count` to 3, shows message 7, "OI! OFF MY FLOWERS, YOU LUNATIC!", and turns on sprite 4 (**Code**).

The gardener starts at the place that `init_actors` gave him, at the top of the lawn. He chases Gordon in mode 0, and he flees from Rover during an attack. He moves each 4 actor ticks, more often than the neighbour (**Code**).

The flower beds block the gardener, so he must walk around them (**Code**). He catches Gordon in the same way as the neighbour. He stays on the lawn until the lawn ends or the player loses the mower (**Code**).

## How a catch works

[`actor_collisions` `$96C7`](../src/actors/actor_collision.asm#L6) runs before each move of an actor. It has two tests with different sizes. The X differences are in units of 2 pixels, as the positions (**Code**).

| Test | X difference | Y difference | Result |
|---|---|---|---|
| The actor at its target | -7 to 5 | -8 to 7 | mode 0: a catch or a bite. Mode 2: a point for Rover. Modes 1 and 3: the second test |
| The actor at Gordon | -5 to 4 | -7 to 6 | Rover: a bite. The other actors: a catch |

The second test also runs when the actor is not at its target. Thus the neighbour and the gardener catch Gordon in any mode, also while they flee from Rover (**Code**).

[`actor_catches_gordon` `$97AE`](../src/neighbour/neighbour_catch.asm#L6) takes the mower:

1. It clears the message timer and shows message 6, "GIMME THAT MOWER!!". The clear makes sure that this message always shows (**Code**).
2. The actor walks to the right with the mower. Sprite 1 shows the mower frame `$D6` 16 pixels to the right of the actor. Gordon stays where he is (**Code**).
3. Each loop moves the actor by 1 and waits 3 x 256 calls of `restart_tune_if_ended`. The walk ends at X = `$C0`, past the right edge of the lawn (**Code**).
4. `save_lawn_scroll_out` scrolls out the lawn and saves it for the player. Then `next_mower_or_player` gives the next mower or the turn of the other player (**Code**).

The walk runs inside the actor code, so the main loop and the other actors stop until the walk ends (**Code**). The catch never returns to the main loop. `next_mower` starts the lawn again, and `switch_player` resets the stack (**Code**).

The trainer TRAINER_INVINCIBLE puts an RTS at the start of `actor_caught_gordon`. Both tests reach the catch through this routine, so no actor catches Gordon. Rover in mode 0 also reaches it, so he does not bite. In the other modes, the second test jumps to `gordon_hits_dog` first, so Rover still bites (**Code**).

## The speed of each lawn

The second part of `init_actors` sets the period `actor_speed` of the actor ticks and the reload `loyalty_rate` of the loyalty timer from the lawn number (**Code**).

1. After lawn 16, the lawn number minus 1 AND `$F0` is not 0. Then `loyalty_rate` is 2 and `actor_speed` is 4, the maximum speed (**Code**).
2. On lawns 1-16, `loyalty_rate` = 6 - A / 4. A is 0 here, so the rate is always 6. The next section tells why (**Code**).
3. On lawns 1-16, `actor_speed` = 12 - (lawn number AND 15) / 2 (**Code**).

| Lawn | Actor tick, passes | Rover wanders, passes | Neighbour, passes | Gardener, passes | Loyalty rate |
|---|---|---|---|---|---|
| 1 | 12 | 36 | 72 | 48 | 6 |
| 2-3 | 11 | 33 | 66 | 44 | 6 |
| 4-5 | 10 | 30 | 60 | 40 | 6 |
| 6-7 | 9 | 27 | 54 | 36 | 6 |
| 8-9 | 8 | 24 | 48 | 32 | 6 |
| 10-11 | 7 | 21 | 42 | 28 | 6 |
| 12-13 | 6 | 18 | 36 | 24 | 6 |
| 14-15 | 5 | 15 | 30 | 20 | 6 |
| 16 | 12 | 36 | 72 | 48 | 6 |
| 17 and more | 4 | 12 | 24 | 16 | 2 |

The columns of Rover, the neighbour and the gardener give the passes between two moves. In an attack, Rover moves at each actor tick (**Code**).

- **Lawn 16 is as slow as lawn 1.** The formula uses the lawn number AND 15, and 16 AND 15 is 0 (**Code**). `draw_lawn_layout` subtracts 1 before the AND, so the author probably forgot the 1 here (**Conclusion**).
- **The step from lawn 16 to lawn 17 is large.** The actors become 3 times faster, and DOG LOYALTY drains 3 times faster during an attack (**Code**). The run of all 16 lawns reaches lawn 17 (**Observed**).

### The bug at `$9042`

[`speed_by_lawn_number` `$9042`](../src/actors/actor_speed_setup.asm#L23) starts with LDX `lawn_number`. The next instruction calls `divide_by_4`, which divides A, not X. At this point A holds the result of the AND `$F0`, which is 0 (**Code**).

~~~
speed_by_lawn_number
        ldx lawn_number     ; the lawn number goes to X
        jsr divide_by_4     ; but this divides A = 0
        sta work_ptr        ; 0
        lda #$06
        sec
        sbc work_ptr        ; 6 - 0 = 6
        sta loyalty_rate
~~~

Thus `loyalty_rate` is 6 on each lawn from 1 to 16 (**Code**). With LDA in place of LDX, the rate goes from 6 on lawn 1 to 2 on lawn 16. The value 2 after lawn 16 continues this row, so LDA was the plan (**Conclusion**). In practice, an attack of Rover costs the same loyalty on the first 16 lawns. From lawn 17, it costs 3 times as much (**Conclusion**).

## The sprites of the actors

Actor X uses sprite X + 1. `init_actors` sets sprites 0, 1, 3 and 4 to multicolour, so Rover on sprite 2 is the only hires sprite. The shared sprite colours are light red and light blue (**Code**).

[`actor_set_frame` `$9525`](../src/actors/actor_frame.asm#L6) selects one of two kinds of frames. The animation frame plays in the order 0, 1, 2, 1 (**Code**).

| Frames | Use |
|---|---|
| `$E4-$E6` | moving up |
| `$E7-$E9` | moving down |
| `$EA-$EC` | moving to the right, side view |
| `$ED-$EF` | moving to the left, side view |
| `$F0-$FB` | the same four sets for Rover, `$0C` higher |

The side frames show when the place test blocks the vertical move. They also show when the actor is less than 8 lines above or below its target. Else a wandering actor shows the frames for up and down (**Code**).

During a catch, the actor shows the side frames to the right, and sprite 1 shows the mower frame `$D6`. Gordon keeps his last frame on sprite 0 (**Code**).

## Worked example: the start of lawn 1

The start tables are 18 bytes at `$8FE4-$8FF5`. The code reads each table with X = 1-4. Thus entry 4 of the X table and of the Y table is entry 0 of the next table (**Code**).

| Address | Bytes | Table | Values for actors 1-4 |
|---|---|---|---|
| `$8FE4` | `00 64 1E 46` | start X | `$64`, `$1E`, `$46`, and `$00` from `$8FE8` |
| `$8FE8` | `00 2E 2E 2E` | start Y | `$2E`, `$2E`, `$2E`, and `$2E` from `$8FEC` |
| `$8FEC` | `2E 03 00 00 00` | start mode | 3, 0, 0, 0 |
| `$8FF1` | `00 03 06 04 03` | move delay | 3, 6, 4, 3 |

The first byte `$00` at `$8FE4` is also entry 8 of `gordon_dy_by_dir`, the Y offset of Gordon for the direction right (**Code**).

On lawn 1, the neighbour starts at X `$1E`, Y `$2E`. Gordon starts at X `$51`, Y `$CD`. `actor_direction` divides the four values by 4 (**Code**):

1. The neighbour gives X 7 and Y 11. Gordon gives X 20 and Y 51.
2. Y 11 is less than 51, so bit 0 of `actor_dir` stays 0, and the neighbour moves down.
3. X 7 is less than 20, so bit 1 stays 0, and the neighbour moves to the right.
4. `actor_dir` is 0 and `actor_facing` is 1. The frame is `$E7` plus the animation frame, a frame for the move down.

The neighbour thus walks down and to the right on a diagonal. He moves each 72 passes on lawn 1. His square is column (`$1E` - 8) / 4 = 5, which is in the flower bed of columns 1-6. The flowers do not block him (**Code**). When nothing blocks his vertical moves, he needs 80 moves to reach the row of Gordon. That is 5,760 passes (**Conclusion**).

## Still open

- How long does DOG TOLERANCE last in play? A run that holds no fire on lawn 1 and records the time of message 8 can measure it.
- Why does `dog_command` also test bit 6 of the joystick port for the attack? On port 1, bits 4 and 6 of `$DC01` are also the keys SPACE and Q of keyboard column 7 (**Conclusion**). A run that presses Q or SPACE in play can show if the keys send Rover.
