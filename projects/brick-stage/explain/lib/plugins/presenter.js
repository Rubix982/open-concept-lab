// The presenter stage: one LEGO minifigure (lib/minifig.js) on a 4×4 plate,
// lit like the brick stages, framed in its own rect. Gesture strengths (0..1,
// tweened by actions/presenter.mjs) become joint angles here, as a pure
// function of time. Pointing reads another stage's anchor, so create the
// presenter after the stage it points at (it then sees that frame's camera).
(function () {
  const { clamp, EASE, TL } = BP;
  const D2R = Math.PI / 180;
  let MFK = null;

  // smooth 0→1→0 envelope for a caption line, so talking eases in and out
  function talking(t) {
    let k = 0;
    for (const n of TL.narration) if (t > n.t && t < n.t + n.dur) k = Math.max(k, clamp((t - n.t) / 300) * clamp((n.t + n.dur - t) / 300));
    return k;
  }

  function Presenter(o) {
    const THREE = BP.THREE;
    MFK ||= minifigKit(THREE, TL.colors);
    const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(26, o.w / o.h, 0.1, 200);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(1); renderer.setSize(o.w, o.h, false); renderer.setClearColor(0x000000, 0);
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    // the brick stages' light: a cool sky, a warm key with shadows, a blue rim
    scene.add(new THREE.HemisphereLight(0xe8eeff, 0x1a2550, 1.6));
    const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(-10, 20, 14); key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024); const sc = key.shadow.camera; sc.left = sc.bottom = -12; sc.right = sc.top = 12; sc.near = 1; sc.far = 60;
    scene.add(key);
    const rim = new THREE.DirectionalLight(0x9fb8ff, 1.1); rim.position.set(8, 8, -14); scene.add(rim);
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ opacity: 0.35 }));
    shadow.rotation.x = -Math.PI / 2; shadow.position.y = -0.001; shadow.receiveShadow = true; scene.add(shadow);
    // a 4×4 plate to stand on (a real part, from the shared brick kit)
    const plate = BP.kit().brick({ part: "3031", x: -2, y: 0, z: -2, w: 4, d: 4, h: 1, kind: "plate", rot: 0 }, BP.plastic(o.plate ?? 72));
    plate.position.copy(plate.userData.home); scene.add(plate);
    const rig = MFK.build(o.look || {});
    rig.root.position.y = BP.PLATE; scene.add(rig.root);
    rig.root.scale.setScalar(0.9);
    // the camera: a little above chest height, looking slightly down
    const lookY = 2.1, dist = 15.5;
    cam.position.set(0, lookY + 2.6, dist); cam.lookAt(0, lookY, 0); cam.updateProjectionMatrix();
    // how far to walk so the figure starts just outside the rect
    const halfW = Math.tan((cam.fov * D2R) / 2) * dist * cam.aspect;
    const offstage = halfW + 2.5;

    const api = {
      canvas: renderer.domElement,
      update(p, t) {
        const sideSign = p.side === "right" ? 1 : -1;
        const walk = clamp(p.walk ?? 1), moving = walk > 0 && walk < 1;
        rig.root.position.x = (1 - walk) * offstage * sideSign;
        rig.root.visible = walk > 0.001;
        plate.visible = true;

        // pointing: turn the body toward the target's screen side, raise the arm toward it
        // pointing uses the arm on the target's side, swung out sideways at the
        // target's angle from the shoulder, with the body and head turned toward it
        let yaw = p.facing * D2R, pointElev = 0, pointRight = false;
        const pt = p.point > 0 && p.pointAt ? target(p.pointAt) : null;
        if (pt) {
          const cx = p.x + p.w / 2, cy = p.y + p.h * 0.36;
          const dx = pt[0] - cx, dy = pt[1] - cy;
          pointRight = dx > 0; // the figure faces the camera: its left arm is on screen right
          yaw += clamp(dx / 900, -1, 1) * 28 * D2R * EASE.inout(clamp(p.point));
          pointElev = clamp(90 + (Math.atan2(-dy, Math.abs(dx)) * 180) / Math.PI, 25, 165); // from hanging
        }
        rig.root.rotation.y = yaw;

        // walking: legs swing, arms counter-swing; whole steps so it settles at rest
        const steps = 6, swing = moving ? Math.sin(walk * steps * Math.PI * 2) * 32 * D2R : 0;
        rig.legs[0].rotation.x = -swing; rig.legs[1].rotation.x = swing;
        const bobWalk = moving ? Math.abs(Math.sin(walk * steps * Math.PI * 2)) * 0.08 : 0;

        // gestures → shoulder angles: x = raise forward (deg), z = raise out to the side (deg)
        const talk = Math.max(clamp(p.talk), p.talkOnNarration ? talking(t) : 0);
        const w = clamp(p.wave), pt0 = clamp(p.point), sh = clamp(p.shrug), nd = clamp(p.nod), th = clamp(p.think);
        let rX = 0, rZ = 0, lX = 0, lZ = 0, wristR = 0;
        // walking counter-swing
        rX += -swing * 0.7 / D2R; lX += swing * 0.7 / D2R;
        // wave: right arm up and out, rocking at the shoulder
        rZ += w * (125 + 18 * Math.sin(t / 115)); rX += w * 20; wristR += w * 60;
        // point: out to the side toward the target, a little forward so it reads
        if (pointRight) { lZ += pt0 * pointElev; lX += pt0 * 18; }
        else { rZ += pt0 * pointElev; rX += pt0 * 18; }
        // shrug: both arms out a little, palms up
        rZ += sh * 32; lZ += sh * 32; rX += sh * 28; lX += sh * 28;
        // think: right hand to the chin
        rX += th * 118; rZ += th * -22; wristR += th * 90;
        // talk: the free hand gestures a little
        lX += talk * (18 + 14 * Math.sin(t / 290));
        rX += talk * (1 - Math.max(w, pointRight ? 0 : pt0, th)) * (10 + 8 * Math.sin(t / 340 + 1));
        if (pointRight) lX -= talk * pt0 * (18 + 14 * Math.sin(t / 290)); // the pointing hand holds still
        for (const arm of rig.arms) {
          const right = arm.side === "r";
          arm.sh.rotation.x = -(right ? rX : lX) * D2R;
          arm.sh.rotation.z = (right ? -rZ : lZ) * D2R;
          arm.wrist.rotation.y = (right ? wristR : 0) * D2R;
        }
        // head and upper body
        rig.head.rotation.x = (nd * Math.sin(t / 150) * 16 + talk * Math.sin(t / 135) * 4 - th * 6) * D2R;
        rig.head.rotation.z = (sh * 9 + th * 8) * D2R;
        rig.head.rotation.y = pt ? (pointRight ? 0.45 : -0.45) * EASE.inout(pt0) : 0;
        rig.upper.rotation.x = (-sh * 5 + talk * Math.sin(t / 420) * 1.5) * D2R;
        rig.upper.rotation.z = (talk * Math.sin(t / 380) * 2 + Math.sin(t / 1300) * 0.8) * D2R;
        rig.root.position.y = BP.PLATE + bobWalk + sh * 0.06 * Math.abs(Math.sin(t / 200));
        rig.setFace(p.face || "smile");
        renderer.render(scene, cam);
      },
    };
    return api;
  }

  // a target in frame pixels: { obj, at } on a stage, { obj, col, row } on a stack, or { x, y }
  function target(a) {
    if (a.x != null && a.y != null && !a.obj) return [a.x, a.y];
    const st = BP.STAGES[a.obj];
    if (!st) return null;
    if (a.at != null && st.anchor && st.anchors) return st.anchor(st.anchors[a.at], st.x, st.y);
    if (st.project) return st.project(a.col, a.row, st.x, st.y);
    return null;
  }

  BP.stage("presenter", Presenter, { overlays: false, after: true });
})();
