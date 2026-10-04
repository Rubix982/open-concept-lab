// Build hook for the presenter: when a script uses one, inline the rigged
// minifig kit (lib/minifig.js) and make sure the LEGO colour table is there.
import fs from "node:fs/promises";
import path from "node:path";

export async function build(tl, { here, log }) {
  const hosts = tl.objects.filter((o) => o.type === "stage3d" && o.props.kind === "presenter");
  if (!hosts.length) return "";
  if (!tl.colors) tl.colors = (await import("../../../../brick-check/lib/parts.mjs")).COLORS;
  const kit = await fs.readFile(path.join(here, "..", "lib", "minifig.js"), "utf8");
  log(`presenter · ${hosts.map((o) => o.id).join(", ")}`);
  return `<script>\n${kit}\n</script>`;
}
