// Capability 8: every sound effect, in turn, with the room ambience under it.
import { story, SFX } from "../../lib/director.mjs";
import { floor } from "./_floor.mjs";

export default story({ title: "Capability: sound cues", poster: 2000 }, (s) => {
  s.shot({ at: [12, 4, 6], az: 15, el: 20, dist: 30 }, 0);
  s.build(floor(), { at: [0, 0, 0], from: "below", stagger: 8, dur: 300 });
  s.ambience("room");
  for (const name of SFX) { s.caption(name, "SOUND"); s.sfx(name); s.wait(1300); }
  s.ambience(null);
  s.wait(500);
});
