#!/usr/bin/env node
// A picture → a 3D model (GLB), using an open image-to-3D model running as a
// Hugging Face Space. Default: VAST-AI's TripoSG (MIT licence): remove the
// background, make the mesh, then (optionally) texture it.
//   node tools/image-to-3d.mjs picture.png [--no-texture] [--out model.glb]
// Free Spaces share GPU time; set HF_TOKEN (a free Hugging Face token) for a
// bigger quota. The picture is sent to Hugging Face — don't send anything private.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Two open providers; free Spaces come and go, so there's a fallback.
const PROVIDERS = {
  triposg: { space: "https://vast-ai-triposg.hf.space", licence: "MIT", session: true },
  instantmesh: { space: "https://tencentarc-instantmesh.hf.space", licence: "Apache-2.0", session: false },
};
let SPACE = PROVIDERS.triposg.space;
const headers = process.env.HF_TOKEN ? { Authorization: `Bearer ${process.env.HF_TOKEN}` } : {};
const session = Math.random().toString(36).slice(2);

async function upload(file) {
  const form = new FormData();
  form.append("files", new Blob([await fs.readFile(file)]), path.basename(file));
  const res = await fetch(`${SPACE}/gradio_api/upload`, { method: "POST", body: form, headers });
  if (!res.ok) throw new Error(`upload failed: ${res.status} ${await res.text()}`);
  const [p] = await res.json();
  return { path: p, orig_name: path.basename(file), meta: { _type: "gradio.FileData" } };
}

// Gradio's queue protocol, the one its own web page uses (the simpler REST
// call doesn't register the per-session state this Space keeps): join the
// queue with a session id, then read that session's event stream until the
// job completes.
let fnIndex = null;
async function call(endpoint, data) {
  if (!fnIndex) {
    const config = await (await fetch(`${SPACE}/config`, { headers })).json();
    fnIndex = Object.fromEntries((config.dependencies || []).map((d, i) => [d.api_name, d.id ?? i]));
  }
  if (!(endpoint in fnIndex)) throw new Error(`no endpoint "${endpoint}" on ${SPACE}`);
  const join = await fetch(`${SPACE}/gradio_api/queue/join`, {
    method: "POST", headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify({ data, fn_index: fnIndex[endpoint], session_hash: session, event_data: null, trigger_id: null }),
  });
  if (!join.ok) throw new Error(`${endpoint}: ${join.status} ${await join.text()}`);
  const { event_id } = await join.json();
  const res = await fetch(`${SPACE}/gradio_api/queue/data?session_hash=${session}`, { headers });
  const reader = res.body.getReader(), dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) throw new Error(`${endpoint}: stream ended before the job finished`);
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
      if (!chunk.startsWith("data:")) continue;
      const msg = JSON.parse(chunk.slice(5));
      if (msg.event_id && msg.event_id !== event_id) continue;
      if (msg.msg === "process_completed") {
        reader.cancel();
        if (!msg.success) throw new Error(`${endpoint} failed: ${JSON.stringify(msg.output).slice(0, 300)}`);
        return msg.output.data;
      }
    }
  }
}

async function download(fileData, to) {
  const url = fileData.url || `${SPACE}/gradio_api/file=${fileData.path}`;
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`download failed: ${res.status}`);
  await fs.writeFile(to, Buffer.from(await res.arrayBuffer()));
  return to;
}

export async function imageTo3D(picture, { texture = true, out, provider } = {}) {
  out ||= picture.replace(/\.[^.]+$/, "") + ".glb";
  const order = provider ? [provider] : ["triposg", "instantmesh"];
  let last;
  for (const name of order) {
    try { return { file: await run(name, picture, { texture, out }), provider: name, licence: PROVIDERS[name].licence }; }
    catch (e) { last = e; console.error(`  ${name}: ${e.message.slice(0, 200)}`); }
  }
  throw last;
}

async function run(name, picture, { texture, out }) {
  SPACE = PROVIDERS[name].space; fnIndex = null;
  if (name === "instantmesh") {
    const img = await upload(picture);
    const [cut] = await call("preprocess", [img, true]);               // background removed
    const [views] = await call("generate_mvs", [cut, 75, 42]);          // six views of the object (kept as session state)
    // make3d's one input is that hidden state: send a slot for it (the API
    // description hides state inputs, but the queue protocol counts them)
    const [, glb] = await call("make3d", [views ?? null]);              // reconstructed from those views
    return download(glb, out);
  }
  await call("start_session", []);                                      // TripoSG keeps per-session state
  const img = await upload(picture);
  const [cut] = await call("run_segmentation", [img]);                         // background removed
  const [glb] = await call("image_to_3d", [cut, 0, 50, 7.0, true, 100000]);     // seed, steps, guidance, simplify, faces
  if (!texture) return download(glb, out);
  const [textured] = await call("run_texture", [cut, glb, 0]);
  return download(textured, out);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), i = args.indexOf("--out");
  const out = i >= 0 ? args.splice(i, 2)[1] : undefined, texture = !args.includes("--no-texture");
  const picture = args.find((a) => !a.startsWith("--"));
  if (!picture) { console.log("usage: node tools/image-to-3d.mjs picture.png [--no-texture] [--out model.glb]"); process.exit(1); }
  const t0 = Date.now();
  const pi = args.indexOf("--provider"), provider = pi >= 0 ? args[pi + 1] : undefined;
  const r = await imageTo3D(picture, { texture, out, provider });
  console.log(`→ ${r.file}  (${Math.round((Date.now() - t0) / 1000)} s, ${r.provider} on Hugging Face, ${r.licence})`);
}
