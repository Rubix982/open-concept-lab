# Your first story in five minutes

1. **Start one.**
   ```sh
   cd projects/brick-stage
   node new.mjs first-light "First Light"
   node dev.mjs first-light
   ```
   Open http://localhost:5173. You'll see a robot, a speech bubble and a tower
   assembling itself.

2. **Change a line and save.** Open `stories/first-light.mjs`, change the text
   in `s.say(...)`, and save. The page rebuilds and reopens at the same moment.

3. **Direct it.** Each line of the script is one action, and they run in order:
   ```js
   s.caption("Build a tower.", "STEP 01");   // text on screen
   s.build(tower, { from: "everywhere" });   // pieces fly in
   s.move("hero", [4, 0, 0]);                // walk somewhere
   s.pose("hero", "right-arm", 120);         // raise an arm
   s.say("hero", "Done!");                   // a speech bubble
   s.emit("hearts", { on: "hero" });         // particles
   s.mood("sunset");                         // change the light
   ```
   Put actions inside `s.together((g) => { … })` to make them happen at once.

4. **Build your own model.** List its parts in the order you'd build it:
   `P(part, colour, x, y, z, rotation)`, where x and z count studs and y counts
   plates (a brick is 3). The parts you can use are in
   `../brick-check/lib/parts.mjs`.

5. **Trust the checks.** If a model can't really be built (a floating brick, a
   part that can't be pressed in, something that would tip over), the terminal
   says which part and why, and that part glows red on stage. If two actors walk
   into each other, the corner badge links to the moment it happens.

6. **Record it.** Press **H** to hide the controls and **M** for sound, then
   screen-record.

Every action is listed in the [README](README.md). The three stories in
`stories/` are worked examples. `rated-for-two.mjs` uses nearly everything.
