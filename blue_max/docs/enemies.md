# The enemies

The enemies of Blue Max attack the plane of the player, and some of them are targets. An enemy plane flies at the plane from the front or from behind. A second enemy plane attacks the plane on the runway during the service. Flak guns on the ground fire shells that burst at the altitude of the plane. Boats sail on the river, and cars and trucks drive on the roads. Some of these objects are *special targets*, which the player must destroy to finish the mission. This page also tells how the game finds a collision and how the status line shows the altitude of an enemy plane. The map and its ground targets are on [map.md](map.md). The plane, the weapons and the damage are on [game.md](game.md). The reference lists each routine and variable: [reference/index.md](reference/index.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one run of the frame interrupt. A *step* is one run of the game routines. The frame interrupt runs them on each second frame.
- *X* is the sprite X position divided by 2, as the game keeps it. *Y* is the sprite Y position.
- The *shadow* of a plane is its sprite on the ground. The sprite of the enemy plane is at the Y of its shadow minus `enemy_altitude`.
- The *diagonal line* of a position is X + Y / 2, from `map_diagonal`. Two objects on the same diagonal line are at the same place across the diagonal scroll.
- A *special target* is an enemy object that counts for the mission. `special_target` holds its kind: 1 a ground target, 2 a boat or a vehicle, 3 an enemy plane.
- The *points* are the points of the score. `add_score` adds A x 10 points, because the lowest digit `score_1` stays 0.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How the enemy code runs

The game has eight sprites, and the enemies share them. Sprite 1 shows the enemy plane, the boat or the road vehicle. Thus only one of the three is on the screen at a time. Sprite 7 shows the shadow of the enemy plane, the marker of a ground target, or a special target of the city. Sprites 4 and 5 show the two flak shells. The bomb of the runway attacker uses sprite 2, the sprite of the bomb of the player (**Code**).

At each step, the frame interrupt calls [`enemy_plane_update` `$6037`](../src/enemy/enemy_plane.asm#L6). Then it moves the flak guns with the ground, sets the altitude alert and moves the shells. The runway attacker is different: the plane state 5 calls it at each frame (**Code**).

~~~mermaid
flowchart TB
  A["Step: enemy_plane_update"] --> B["Decrement the quiet timer"]
  B --> C["Move the road vehicle and the boat"]
  C --> D["Flash the special target"]
  D --> E{"Enemy plane explodes?"}
  E -- yes --> F["Next explosion image"]
  E -- no --> G{"enemy_timer = 0?"}
  G -- yes --> H["Move the enemy plane"]
  G -- no --> I["Decrement enemy_timer"]
  I --> J["At 0: start a plane or wait again"]
~~~

1. **The quiet timer keeps the enemies away from the airfields.** Each airfield row sets `quiet_timer` to 10 or 20. The service on the runway sets it to 10 at each frame. While it is not 0, no enemy plane starts, no flak gun fires and no boat sails (**Code**).
2. **One timer controls sprite 1.** `enemy_timer` is 0 while an enemy plane flies. The boat and the road vehicle write `$1E` into it at each step, so no enemy plane starts while they move (**Code**).
3. **The difficulty grows with the airfields.** The main loop sets `difficulty` to the airfields passed plus the skill level 0-2. It sets `flak_chance` to skill x 16 + airfields x 8 (**Code**).

## The enemy plane

The enemy plane is a yellow multicolour plane on sprite 1 with a black shadow on sprite 7. It uses the same images as the plane of the player. The letter P shows in the status line while it flies (**Code**).

![The plane sprite $E0 in multicolour. The enemy plane uses the same images.](reference/images/plane_level_spr_0-multicolour.png)

### The start

When `enemy_timer` gets to 0, [`enemy_plane_spawn` `$606B`](../src/enemy/enemy_plane.asm#L34) starts a plane. It does not start a plane while the quiet timer runs or a special target is active. In these cases it loads a new delay (**Code**).

1. It asks `pick_special_target` if this plane is a special target. A special plane sets `special_target` to 3 (**Code**).
2. It gives the plane an altitude near the altitude of the player: random 0-31, plus the altitude, minus 15, AND `$3F`. It adds 6 until the value is at least 25 (**Code**).
3. Bits 0-1 of `random_seed` select the direction. Bits 4-7 add 0-15 to the start X (**Code**).

| Seed bits 0-1 | `enemy_dy` | Start | Move of the shadow at each step |
|---|---|---|---|
| 0 | 0 | no plane: a new delay | none |
| 1 | `$02` | top, Y `$14`, X `$78` + 0-15 | Y + 4, X - 2: head-on |
| 2 | `$FF` | bottom, Y `$FF`, X `$20` + 0-15 | Y - 1, X + 1: from behind, slow |
| 3 | `$FE` | bottom, Y `$FF`, X `$20` + 0-15 | Y - 2, X + 2: from behind, fast |

Thus one start in four gives no plane (**Code**). The ground moves down and to the left on the screen. A head-on plane moves down faster than the ground, and a plane from behind climbs up the screen and passes the player (**Conclusion**).

### The flight

[`enemy_plane_move` `$611E`](../src/enemy/enemy_plane.asm#L126) moves the shadow by `enemy_dy`. Then it puts the plane sprite at the shadow Y minus `enemy_altitude` (**Code**).

- **The plane changes its side step at random.** A plane from behind has a side step in `enemy_dx`. On 1 of 32 random values, the step changes. Of 8 seed values, 2 give right, 2 give left and 4 give straight (**Code**).
- **A turn to the left is faster than a turn to the right.** The code for the left turn decrements X and then adds `enemy_dx` = -1. The plane thus moves 2 to the left, but only 1 to the right (**Code**).
- **The wind also pushes the enemy plane.** `update_wind` adds the wind to the X of the shadow and to `enemy_altitude` (**Code**).
- **The plane leaves at the edges.** A shadow Y below 3, an X below 5 or an X of `$B4` or more removes the plane. A head-on plane leaves at Y `$FA` (**Code**).

[`enemy_plane_remove` `$60EC`](../src/enemy/enemy_plane.asm#L101) hides sprites 1 and 7 and clears `special_target`. A special plane that leaves the screen thus does not count. The new delay is `$1E-$5D` steps, from `enemy_plane_delay_set` (**Code**).

### The explosion

A bullet sets `enemy_explode_timer` to 16, and a collision with the player sets it to 20. [`enemy_plane_explode` `$62D8`](../src/enemy/road_vehicle.asm#L103) then shows the falling image `$FA` on sprite 1. Sprite 7 shows explosion images `$F5-$F8` in random colours near the plane (**Code**).

The colour of sprite 1 comes from `enemy_explosion_colours`, by the timer. The table has 16 entries, from black to white. A collision starts at 20, so the timer values 19-16 read the first bytes of `check_enemy_collision` (**Code**). The worked example decodes them.

At 0, a special plane counts as a destroyed target, and `enemy_plane_remove` ends the plane (**Code**). The coverage runs executed the explosion, but not the count of a special plane (**Observed**).

### The state machine of the enemy plane

~~~mermaid
stateDiagram-v2
  state "Waiting (enemy_timer > 0)" as Wait
  state "Flying (enemy_timer = 0)" as Fly
  state "Exploding (enemy_explode_timer > 0)" as Boom
  [*] --> Wait
  Wait --> Fly: timer 0, seed bits 1-3
  Wait --> Wait: seed bits 0, quiet timer, special target
  Fly --> Wait: off the screen
  Fly --> Boom: bullet or collision
  Boom --> Wait: explosion timer 0
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Waiting | `enemy_timer` gets to 0, seed bits 0-1 not 0 | Flying | `enemy_plane_spawn` |
| Waiting | seed bits 0-1 = 0 | Waiting, new delay | `enemy_plane_remove` |
| Waiting | `quiet_timer` or `special_target` not 0 | Waiting, new delay | `enemy_plane_delay_set` |
| Waiting | boat or vehicle moves | Waiting, timer `$1E` | `update_boat`, `road_vehicle_update` |
| Flying | shadow outside the edges | Waiting | `enemy_plane_remove` |
| Flying | bullet hit | Exploding, 16 steps | `update_weapons` |
| Flying | collision with the player | Exploding, 20 steps | `check_enemy_collision` |
| Exploding | `enemy_explode_timer` = 0 | Waiting | `enemy_plane_explode` |

## The runway attacker

The runway attacker is a white enemy plane that attacks the plane during the service on the runway. [`runway_attacker` `$5EF9`](../src/enemy/runway_attacker.asm#L6) runs at each frame of plane state 5. It writes `$1E` into `enemy_timer`, so no normal enemy plane starts (**Code**).

1. **The start.** When a random byte is less than `airfields_passed`, the attacker starts at Y `$F0`, at the bottom of the screen. Its X is random 0-31, and its altitude is 26-42 (**Code**).
2. **The flight.** At each frame it moves 2 lines up and 1 to the right. It does not change its side step. At Y below `$1E` it leaves the screen (**Code**).
3. **The bomb.** [`enemy_bomb_drop` `$5FA4`](../src/enemy/runway_attacker.asm#L87) drops a bomb when the shadow of the attacker is less than 20 lines from the shadow of the plane. A random byte must also be less than `difficulty` (**Code**).
4. **The fall.** The bomb falls 2 units of height and moves 1 to the right at each frame. Below height 4 it explodes with a flash and a large explosion sound (**Code**).
5. **The explosion.** The burst shows images `$F5-$F8` in yellow for 11 frames. When the plane is in the box of the burst, the crash flag goes to 1 (**Code**).

Thus the chance of an attack grows with each airfield. While `airfields_passed` is 0, no attacker comes (**Code**). When the player takes off with an attacker in the air, `plane_start_takeoff` sets `enemy_timer` to 0 and `enemy_dy` to `$FF`. The attacker then continues as a normal enemy plane from behind (**Code**).

The game start sets `enemy_dy` to 1. The plane starts on the runway in state 5, so the first call of `runway_attacker` moves this plane. The shadow Y is 1, so the code removes the plane at once (**Code**). No run executed the start, the bomb or the explosion of the attacker (**Observed**).

## The flak guns and the shells

The flak guns are positions in a table of 8 slots, `gun_x` and `gun_y`. A gun slot with X = 0 is free. [`add_flak_gun` `$6DB1`](../src/ground/flak_guns.asm#L6) fills the first free slot from 7 down to 1, else slot 0. It puts the gun at X = map column x 4 + 15 and Y `$2B` (**Code**).

Three kinds of map objects add a gun:

- the gun tile `$A1` that `place_ground_targets_any` puts beside the river,
- each ship on the river, from `place_ship`,
- each water object of the city, from `draw_water_objects`.

Thus a ship and a city water object also fire flak (**Code**). `scroll_flak_guns` moves each gun 1 to the left and 2 lines down at each step. It frees the slot at Y `$C8` (**Code**).

### Firing

[`update_shells` `$6BF7`](../src/enemy/flak_shells.asm#L6) handles two shells, on sprites 5 and 4. For a free shell, it does these steps (**Code**):

1. It stops when the quiet timer runs, or when a random byte is not less than `flak_chance`.
2. It calculates the line of the plane: the shadow Y minus the altitude / 2.
3. It finds the gun whose Y is nearest to this line. The gun must be less than 15 lines from the line.
4. The shell starts at the gun at height 0. The code clears the X of the gun, so each gun fires only one shell.
5. It compares the diagonal line of the gun with the diagonal line of the shadow. A gun on a lower line gets base direction 2, else base direction 0. The code adds a random 0-2.

| Direction | X step | Y step | Height step | Flight |
|---|---|---|---|---|
| 0 | -4 | -2 | +2 | up and to the left |
| 1 | -2 | -4 | +4 | up, a little to the left |
| 2 | 0 | -6 | +6 | straight up |
| 3 | +2 | -4 | +4 | up, a little to the right |
| 4 | +4 | -2 | +2 | up and to the right |

With skill 0 and no airfield passed, `flak_chance` is 0, and no gun fires (**Code**). The city rows write `$C8` into `flak_chance`. But the main loop writes the normal value again at each pass. Thus the high chance probably lasts only a short time (**Conclusion**).

### The burst

The shell is a small black square, image `$FB`. It moves by the steps of the table, and its height grows by the height step. When the height reaches the altitude of the plane, the shell bursts with a noise sound (**Code**). A shell outside X `$14-$9F` or above Y `$14` disappears (**Code**).

The burst lasts 11 steps and shows images `$F5-$F8` in red. When the plane is in the box of the burst, [`plane_hit_by_shell` `$6974`](../src/plane/shell_damage.asm#L6) runs. Bit 4 of the shell state then blocks a second hit by the same burst. The `invincible` flag blocks all hits (**Code**).

`plane_hit_by_shell` shows the plane and the border in red and plays the hit sound. It sets one of the four damage flags, from a random start. With all four flags set, the plane falls (**Code**). The coverage runs executed a shell hit that set the first flag (**Observed**). [game.md](game.md) tells what each damage does.

### Destroyed guns

A bullet on the gun tile `$A1` draws a crater and gives 10 points. Then [`clear_flak_gun` `$67BA`](../src/ground/ground_hits.asm#L192) must free the slot of this gun (**Code**). But the routine writes 0 into `gun_x_2` for each slot whose Y is at least the bullet Y minus 5. Thus it frees only slot 2, and not the slot of the gun (**Code**).

A bomb on the gun tile draws rubble and gives 30 points. This path does not call `clear_flak_gun` (**Code**). Thus a destroyed gun can still fire its one shell (**Conclusion**).

## The boats

The boat is a brown multicolour sprite, image `$F2`, that sails on the river. [`update_boat` `$6A1F`](../src/enemy/boat.asm#L6) starts it and moves it (**Code**).

1. **The wait.** `boat_wait` decrements when bit 4 of `scroll_frames` is 0. A new wait is 63-127 (**Code**).
2. **The start.** At 0, a boat starts only in map section 0, without quiet timer, enemy plane or vehicle. The road and airfield delays must be at least 10, and the river column below `$3D`. Else a new wait starts (**Code**).
3. **The place.** The boat starts at Y `$14` on the river: X = (river column - 2) x 4 - 10. Its drift is -1 or +1 (**Code**).
4. **The sail.** At each step the boat moves with the ground: X - 1, Y + 2. When bits 1-2 of the frame counter are both set, it also drifts across the river. Then X gets - drift and Y gets + 2 x drift (**Code**).
5. **The end.** At Y `$FC` the boat leaves the screen (**Code**).

Two hits sink the boat. A bomb on the water shows the burst tiles `$74` and `$75` for 8 frames. When one of them is under the boat, the boat sinks. In low flight, a bullet sinks it when the boat is 2-5 diagonal lines from the bullet (**Code**). A sunk boat puts wreck tiles on the map and gives 100 points (**Code**). No run sank a boat (**Observed**).

### The special boat that escapes

[`update_boat_end` `$6B51`](../src/enemy/boat.asm#L157) ends each boat. For a special boat it counts a destroyed target, removes the marker and adds 200 points (**Code**). But the boat also reaches this code when it leaves the screen at Y `$FC`. Thus a special boat that sails away counts as a destroyed target and gives 250 points (**Code**). The coverage runs executed this count, and no run sank a boat (**Observed**). A special enemy plane or vehicle that leaves the screen does not count (**Code**). Thus the code for the boat is probably a bug (**Conclusion**).

## The road vehicles

A car or a truck drives down the road after the road appears on the map. The first road row calls [`road_vehicle_start` `$620F`](../src/enemy/road_vehicle.asm#L6). It starts a vehicle only while no enemy plane flies and no boat sails (**Code**).

- **The image.** A random bit selects the car `$F0` or the truck `$F1` (**Code**).
- **The colour.** A random byte AND 4 selects entry 0 or entry 4 of `vehicle_colours`. The table has only 4 entries, so entry 4 reads `$AD` from the next routine. The vehicles are thus black or light green, and entries 1-3 are never used (**Code**).
- **The move.** `road_vehicle_update` moves the vehicle 1 to the right and 2 lines down at each step. It removes the vehicle when Y passes `$FF` (**Code**).

From Y `$32`, the code reads the map tile under the vehicle. A road tile is a tile with bit 7 set. On any other tile, the vehicle crashes: the code draws wreck tiles and gives 100 points. A special vehicle gives 150 points more (**Code**). A crater or a broken bridge on the road is not a road tile. Thus a bomb on the road in front of a vehicle destroys it (**Conclusion**). No run executed a crash of a vehicle (**Observed**).

## The special targets

The mission needs special targets. `targets_left` holds the number that remains, and [map.md](map.md) tells how the map sets it. [`pick_special_target` `$6B72`](../src/enemy/special_targets.asm#L6) decides if the next enemy object is a special target (**Code**).

1. It returns "no" while a special target is active, or when `targets_left` is 0.
2. It decrements `special_wait`. It returns "no" until the counter gets to 0.
3. At 0, it loads the counter again with (7 - map section) AND 7. In the country, section 0, that is 7.
4. It returns "yes" only when no enemy plane flies.

Five objects ask the routine: a building, a road with its bridge, a boat, a vehicle and an enemy plane (**Code**). A ground target gets `special_target` 1. `special_kind` then holds the kind of the building 0-3, or `$80` for the bridge (**Code**).

[`update_special_marker` `$6B98`](../src/enemy/special_targets.asm#L27) flashes the special target in the colours of `special_marker_colours`: cyan, light blue, blue, blue. For a ground target, it shows the box with a cross, image `$F3`, on sprite 7. It moves the box with the ground. For a boat, a vehicle or a plane, it flashes the colour of sprite 1 (**Code**). The coverage runs executed both kinds of marker (**Observed**).

- **The end of a target loads the counter with 2.** `remove_special_target` ends the target after a hit, or when its marker leaves the screen. It calculates a random value, but then loads 2 in its place. Thus the second object after it is a special target again (**Code**).
- **A bomb on any building of the kind counts.** The bomb code compares the kind of the hit building with `special_kind`. It does not compare the place (**Code**).
- **A marker that leaves the screen ends the target.** At Y `$FC`, the box disappears and the target does not count (**Code**).

The three special targets of the city water use sprite 7 in their own way. [map.md](map.md) tells about them.

## The collisions

The game does not use the collision registers of the VIC-II. Each test compares positions in code (**Code**). Two tests need the same altitude, which the status line shows in light blue. Two tests use the diagonal lines.

[`check_enemy_collision` `$6342`](../src/enemy/enemy_collision.asm#L10) runs at each step of a flying enemy plane. [`check_bullet_enemy` `$657A`](../src/plane/weapons.asm#L268) runs at each step of a bullet (**Code**).

| Test | Condition | Result |
|---|---|---|
| enemy plane and plane | same altitude, plane X from enemy X - 7 to + 6, plane Y from enemy Y - 14 to + 12 | enemy explodes, 20 steps. `engine_damage` and `plane_failing` = 1 |
| bullet and enemy plane | same altitude, enemy line - plane line from -2 to +1, enemy shadow not below the plane shadow | enemy explodes, 16 steps. 100 points |
| shell burst and plane | not `invincible`, plane X from shell X - 5 to + 3, plane Y from shell Y - 9 to + 8 | `plane_hit_by_shell`, one time for each burst |
| attacker bomb and plane | plane X from bomb X - 9 to - 1, plane Y from bomb Y - 9 to + 8 | `crash_flag` = 1 |
| bullet and boat | low flight, boat line - bullet line from 2 to 5 | boat sinks, 100 points |
| bomb burst and boat | burst tile `$74` or `$75` under the boat | boat sinks, 100 points |
| vehicle and map | tile under the vehicle without bit 7 | vehicle crashes, 100 points |

- **A collision brings the plane down slowly.** `engine_damage` makes `plane_control` use a random value in place of the joystick. It also decrements the altitude at each step. At altitude 0 the plane crashes (**Code**). The coverage runs executed a collision with an enemy plane (**Observed**).
- **The bullet must hit at the same altitude.** The bullet test does not compare the positions of the sprites. It compares the diagonal lines of the two shadows. The bullet must fly while the status line is light blue (**Code**). No run destroyed an enemy plane (**Observed**).

## The altitude alert

The status line shows where the enemy plane is in height, and how near the plane is to the ground. [`update_altitude_alert` `$6862`](../src/screen/altitude_alert.asm#L6) sets `status_bg_colour` at each step. The status interrupt writes it into the background colour of the status rows (**Code**).

1. It clears two marks at column 38 of the two status rows.
2. While an enemy plane flies, it compares `enemy_altitude` with the altitude. Above altitude + 4, it shows an up arrow, character `$2D`, in the upper row. At altitude - 4 or below, it shows a down arrow, character `$2E`, in the lower row.
3. Between these limits, the enemy plane is at the same altitude. The status line becomes light blue, and the routine ends.
4. Else, an altitude below 0 sets the crash flag. An altitude of 26 or more gives black.
5. Below 26, the status line is brown, and `low_flight` lets the bullets hit ground objects.
6. At `obstacle_altitude` or below, the status line flashes yellow and black, 16 frames each. On the runway, in plane states 1, 4 and 5, it stays black.

| Colour | Value | Condition |
|---|---|---|
| light blue | `$0E` | enemy plane at altitude - 3 to altitude + 4 |
| black | `$00` | altitude 26 or more, or on the runway |
| brown | `$09` | altitude below 26 |
| yellow, flashing | `$07` | altitude at `obstacle_altitude` or below |

The help page of the anonymous release calls the colour for low flight "red" and gives 15 for yellow (**Observed**: the BASIC text). The code uses colour 9, brown on the C64 (**Code**). The main loop sets `obstacle_altitude` to 16-19 on a random value 0. Below this altitude, trees and buildings hit the plane (**Code**). Thus the yellow flash warns of the trees (**Conclusion**).

## Worked example: a flak shell and an explosion

The tables `shell_step_x` at `$6DA7` and `shell_step_y` at `$6DAC` hold these bytes (**Code**):

| Address | Bytes | Values for directions 0-4 |
|---|---|---|
| `$6DA7` | `FC FE 00 02 04` | X steps -4, -2, 0, +2, +4 |
| `$6DAC` | `FE FC FA FC FE` | Y steps -2, -4, -6, -4, -2 |

The plane flies at altitude 40. A gun on a lower diagonal line fires, and the random value is 0. The direction is thus 2 (**Code**):

1. At each step, the shell X stays the same, and the Y gets `$FA` = -6. The code then adds 1 to the Y, so the shell climbs 5 lines.
2. The height is the height minus the Y step: 0 + 6 = 6, then 12, 18, 24, 30, 36, 42.
3. At step 7 the height 42 is 40 or more, so the shell bursts. It is then 35 lines above the gun.
4. The burst moves the shell 6 to the left and 10 lines up, to the centre of the explosion image.

Thus a shell needs 7 steps, or 14 frames, to reach altitude 40 (**Conclusion**).

The explosion colours of a collision start at timer 20. The first step decrements the timer to 19. Entries 19-16 are the bytes `C9 40 52 AD` at `$6345-$6342`, the code of `check_enemy_collision` (**Code**). The VIC-II uses the low 4 bits, so the colours are brown, black, red and light green. Then the table gives white, light grey, grey, dark grey and black (**Code**). Thus the first 4 images of a collision explosion have colours that the author did not plan (**Conclusion**).

## Still open

- How often does a runway attacker come in play? A run that lands at each airfield and waits for the full service can show the first attack.
- Is `airfields_passed` 0 or 1 during the first service on the start runway? A watchpoint on `airfields_passed` from the game start can tell.
- Does the value `$C8` of the city rows ever reach `update_shells`? A watchpoint on `flak_chance` in map sections 3 and 5 can tell.
- What do the writes of 0 to `$0C27` and `$0C4F` in `update_altitude_alert` do? These cells are on the status screen, but not in the two status rows that the interrupt shows. A run that shows screen `$0C00` with all rows can tell.
- Does the faster turn to the left show in play? A run that records the shadow X of an enemy plane from behind can measure it.
