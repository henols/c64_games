# Playtest checklist

The replays in [README.md](README.md) compare the game state of the default build with the SAEGER file `releases/bruce_lee.prg`. Only a person can judge the items below.

## Application

- [ ] Start `build/clean_loader.prg` (the default build, protection off) in an emulator. The Datasoft title picture shows without the TBC text. A key or fire on joystick port 1 or 2 starts the game. The title screen comes with no cracktro before it.
- [ ] Play into rooms 2, 5 and 10 with the default build. The game does not hang, and rooms 0, 1 and 5 keep their maps.
- [ ] On the title, press F3 and F5. The highlight moves between 1 PLAYER / 2 PLAYERS and COMPUTER / OPPONENT.
- [ ] Press L, R, shift-L and shift-R on the title. The line "JOYSTICK # n IS IN LEFT/RIGHT HANDED MODE" appears.
- [ ] Wait about 48 seconds on the title. The attract demo starts, and F1 or fire returns to the title.
- [ ] Press F7 or fire on joystick port 1. A game starts in room 0, and joystick port 1 moves Bruce.
- [ ] In a game, press SPACE: the pause message shows, and SPACE again resumes. V shows the credit text in the status line. F1 goes back to the title.
- [ ] Take the lanterns of room 0 and leave the room. The next room shows, and the score counts.
- [ ] With 2 PLAYERS and OPPONENT, joystick port 2 moves the Yamo. When Bruce loses a fall, the PLAYER 2 screen appears.
- [ ] Lose all falls. GAME OVER appears, and the game returns to the title.
- [ ] The title tune plays on the title screen (every few titles), and the sound effects play in the game.
- [ ] The controls respond as fast as in the SAEGER file.
- [ ] The animation is smooth and has no glitches.
- [ ] The music and the sound effects sound the same as in the SAEGER file.
- [ ] The game flow and the room changes work from start to end. A room change can stop the game in rare cases. The three releases have the same fault (see [docs/interrupts.md](../docs/interrupts.md)).
- [ ] Nothing unexpected happens outside the tested parts.
