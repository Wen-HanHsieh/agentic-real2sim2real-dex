// viewer3d.js — 3D hand–object viewer for the reconstruction comparison (Agentic Reconstruction vs Do as I Do).
// ES module, no globals, no storage, no network beyond `base`. Usage:
//   import { mount, unmount } from './viewer3d.js';
//   await mount(document.getElementById('viewer'), { task: 'tennis', base: 'website3d', defaultMethod: 'agentic' });
//   unmount();
// Everything shown is loaded from the delivered reconstructions (see data/manifest.json); nothing is synthesised.
import * as THREE from './vendor/three.module.min.js';
import { OrbitControls } from './vendor/OrbitControls.js';

const METHODS = ['agentic', 'doasido'];
const FPS = 30;
const SIDES = ['left', 'right'];
const FINGERS = ['thumb', 'index', 'middle', 'ring', 'little'];
const COL = { left: 0x7fb3e6, right: 0xe9a23b, obj: [0xd34fd3, 0x2cb5b5], bone: 0x30343a };
const LBL_C = 'computed from the delivered reconstruction (not ground truth)';
const CSS = `
.rv3d{--rv-text:var(--text,#1b2330);--rv-muted:var(--muted,#5d6878);--rv-surface:var(--surface,#ffffff);--rv-surface2:var(--surface-2,#eef1f5);
 --rv-border:var(--border,#d6dbe3);--rv-accent:var(--accent,#2f6fd6);--rv-accent-text:var(--accent-text,#fff);--rv-vp:var(--viewport,#e9edf2);
 --rv-ok:var(--ok,#1f7a46);--rv-bad:var(--bad,#b4372f);color:var(--rv-text);font:13px/1.45 inherit;font-family:inherit}
.rv3d *{box-sizing:border-box}
.rv3d .bar{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;background:var(--rv-surface);border:1px solid var(--rv-border);border-radius:10px;padding:7px 9px;margin-bottom:8px}
.rv3d label{display:inline-flex;align-items:center;gap:4px;color:var(--rv-muted);white-space:nowrap}
.rv3d select,.rv3d button{font:inherit;color:var(--rv-text);background:var(--rv-surface2);border:1px solid var(--rv-border);border-radius:7px;padding:3px 8px;cursor:pointer}
.rv3d button.pri{background:var(--rv-accent);color:var(--rv-accent-text);border-color:var(--rv-accent);min-width:58px}
.rv3d .sl{display:flex;align-items:center;gap:8px;flex:1 1 240px;min-width:0}.rv3d .sl input{flex:1;min-width:0;accent-color:var(--rv-accent)}
.rv3d .fl{font-variant-numeric:tabular-nums;color:var(--rv-muted);min-width:118px;text-align:right}
.rv3d .views{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
@media (max-width:820px){.rv3d .views{grid-template-columns:1fr}}
.rv3d .pane{position:relative;background:var(--rv-vp);border:1px solid var(--rv-border);border-radius:10px;overflow:hidden;aspect-ratio:3/4;min-height:220px}
.rv3d .pane.land{aspect-ratio:4/3}
.rv3d .pane video{width:100%;height:100%;object-fit:contain;display:block;background:#000}
.rv3d .pane canvas{display:block;width:100%;height:100%;touch-action:none}
.rv3d .tag{position:absolute;left:6px;top:6px;right:6px;pointer-events:none;font-size:12px}
.rv3d .tag b.t{font-size:12.5px}.rv3d .chip{display:inline-block;background:var(--rv-surface);border:1px solid var(--rv-border);border-radius:6px;padding:0 5px;margin:2px 3px 0 0}
.rv3d .na{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;color:var(--rv-muted);padding:16px;font-weight:600}
.rv3d .ok{color:var(--rv-ok)}.rv3d .bad{color:var(--rv-bad)}.rv3d .mut{color:var(--rv-muted)}
.rv3d .diag{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:8px}
@media (max-width:820px){.rv3d .diag{grid-template-columns:1fr}}
.rv3d .card{background:var(--rv-surface);border:1px solid var(--rv-border);border-radius:10px;padding:8px 10px;min-width:0;overflow-x:auto}
.rv3d .card h4{margin:0 0 4px;font-size:13px}
.rv3d table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}
.rv3d td,.rv3d th{border-top:1px solid var(--rv-border);padding:2px 5px;text-align:right;white-space:nowrap}.rv3d td:first-child,.rv3d th:first-child{text-align:left}
.rv3d .strip{width:100%;height:22px;display:block;cursor:pointer;border-radius:4px;margin-top:6px}
.rv3d .note{color:var(--rv-muted);font-size:11.5px;margin:3px 0}
.rv3d .leg{display:inline-flex;flex-wrap:wrap;gap:8px;color:var(--rv-muted);font-size:11.5px}.rv3d .sw{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:3px;vertical-align:-1px}
.rv3d details{margin-top:8px;background:var(--rv-surface);border:1px solid var(--rv-border);border-radius:10px;padding:6px 10px}.rv3d details summary{cursor:pointer;font-weight:600}
.rv3d details li,.rv3d details p{color:var(--rv-muted)}
`;

// ------------------------------------------------------------------ known-geometry signed distance (SPECS frame, metres)
function sdfKnown(name) {
  const box = (x, y, z, hx, hy, hz, cx = 0, cy = 0, cz = 0) => {
    const qx = Math.abs(x - cx) - hx, qy = Math.abs(y - cy) - hy, qz = Math.abs(z - cz) - hz;
    const ox = Math.max(qx, 0), oy = Math.max(qy, 0), oz = Math.max(qz, 0);
    return Math.hypot(ox, oy, oz) + Math.min(Math.max(qx, qy, qz), 0);
  };
  if (name === 'tennis_ball') return (x, y, z) => Math.hypot(x, y, z) - 0.0325;
  if (name === 'cube') return (x, y, z) => box(x, y, z, 0.025, 0.025, 0.025);
  if (name === 'plug_white' || name === 'plug_black') {
    const hb = name === 'plug_white' ? [0.0145, 0.02155, 0.02925] : [0.0159, 0.0179, 0.03225];
    const bl = name === 'plug_white' ? 0.016 : 0.018;
    return (x, y, z) => Math.min(box(x, y, z, ...hb), box(x, y, z, 0.003175, 0.00075, bl / 2, 0, 0.00635, hb[2] + bl / 2),
      box(x, y, z, 0.003175, 0.00075, bl / 2, 0, -0.00635, hb[2] + bl / 2));
  }
  if (name === 'pen') {
    const xs = [0, 0.8, 2.3, 13.7, 14.8, 16, 171.6, 172.6, 187.2, 188.8, 194, 195].map((v) => v / 1000 - 0.0975);
    const ds = [0, 7.6, 9.5, 9.5, 8.5, 9.0, 9.0, 11.2, 11.2, 8.5, 2.6, 0].map((v) => v / 2000);
    const rad = (x) => { if (x <= xs[0] || x >= xs[11]) return 0; let i = 0; while (xs[i + 1] < x) i++; const u = (x - xs[i]) / (xs[i + 1] - xs[i]); return ds[i] + u * (ds[i + 1] - ds[i]); };
    return (x, y, z) => { const radial = Math.hypot(y, z) - rad(Math.max(xs[0], Math.min(xs[11], x))); const beyond = Math.max(Math.abs(x) - 0.0975, 0);
      return beyond > 0 ? Math.hypot(beyond, Math.max(radial, 0)) : radial; };
  }
  return null;
}
const LEG = { pen: '#d93a2e', contact: '#29b85c', gap: '#3b78eb', none: '#9aa0a8' };  // the legend's colours (sRGB)
function tipColor(d, out) {  // fingertip status, same colours as the legend: penetration > 5 mm, |d| <= 5 mm band, gap > 5 mm
  if (d === null || !Number.isFinite(d)) return out.set(LEG.none);
  return out.set(d < -0.005 ? LEG.pen : d <= 0.005 ? LEG.contact : LEG.gap);
}
function distColor(d, out) {  // per-vertex colouring: legend colours, gap fading to grey with distance
  if (d === null || !Number.isFinite(d)) return out.set(LEG.none);
  if (d < -0.005) return out.set(LEG.pen);
  if (d <= 0.005) return out.set(LEG.contact);
  const a = Math.min(1, (d - 0.005) / 0.03); return out.set(LEG.gap).lerp(_grey.set(LEG.none), a);
}

// ------------------------------------------------------------------ module state
let S = null;

export async function mount(el, opts = {}) {
  if (S) unmount();
  const base = (opts.base || '.').replace(/\/$/, '');
  S = { el, base, task: null, frame: 0, T: 0, data: {}, diag: {}, raf: 0, vfc: 0, alive: true,
    show: { mesh: true, skeleton: true, tips: true, vcolor: false, objects: true, camaxes: true, objaxes: true },
    tipSrc: 'known', view: 'fit', views: [], primary: METHODS.includes(opts.defaultMethod) ? opts.defaultMethod : 'agentic' };
  const root = document.createElement('div'); root.className = 'rv3d'; S.root = root;
  const style = document.createElement('style'); style.textContent = CSS; root.append(style);
  root.insertAdjacentHTML('beforeend', `
  <div class="bar">
    <label>Task <select data-k="task"></select></label>
    <button class="pri" data-k="play">Play</button><button data-k="prev" title="previous frame">−1</button><button data-k="next" title="next frame">+1</button>
    <label>Speed <select data-k="rate"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option></select></label>
    <div class="sl"><input data-k="slider" type="range" min="0" max="0" value="0" aria-label="frame"><span class="fl" data-k="flab"></span></div>
  </div>
  <div class="bar">
    <label><input type="checkbox" data-t="mesh" checked> hand mesh</label><label><input type="checkbox" data-t="skeleton" checked> skeleton</label>
    <label><input type="checkbox" data-t="tips" checked> fingertips</label><label><input type="checkbox" data-t="vcolor"> colour hand by distance</label>
    <label><input type="checkbox" data-t="objects" checked> objects</label><label><input type="checkbox" data-t="camaxes" checked> camera axes</label>
    <label><input type="checkbox" data-t="objaxes" checked> object axes</label>
    <label>Distances to <select data-k="tipsrc"><option value="known">known object geometry</option><option value="own">method's own mesh</option></select></label>
    <span style="flex:1"></span><label>View</label><button data-v="fit" title="true camera position and orientation; zoomed so the hands and objects (10th-90th percentile box over the task) fill about 70 % of the view">Front · fit</button><button data-v="camera" title="true camera position, orientation and field of view">Front · true camera FOV</button><button data-v="side">Side</button><button data-v="top">Top</button>
  </div>
  <div class="leg"><span><i class="sw" style="background:#d93a2e"></i>penetration</span><span><i class="sw" style="background:#29b85c"></i>|d| ≤ 5 mm (heuristic contact band)</span>
   <span><i class="sw" style="background:#3b78eb"></i>gap</span><span><i class="sw" style="background:#e9a23b"></i>right hand</span><span><i class="sw" style="background:#7fb3e6"></i>left hand</span>
   <span><i class="sw" style="background:#d34fd3"></i>object 1</span><span><i class="sw" style="background:#2cb5b5"></i>object 2</span><span>axes: x red, y green, z blue</span></div>
  <div class="views">
    <div class="pane" data-p="video"><video data-k="video" muted playsinline preload="auto"></video><div class="tag"><span class="chip"><b>Input video</b></span><span class="chip mut" data-k="vlab"></span></div></div>
    <div class="pane" data-p="agentic"><div class="tag" data-k="tag-agentic"></div></div>
    <div class="pane" data-p="doasido"><div class="tag" data-k="tag-doasido"></div></div>
  </div>
  <div class="diag"><div class="card" data-k="diag-agentic"></div><div class="card" data-k="diag-doasido"></div></div>
  <details><summary>About these views</summary><div data-k="about"></div></details>`);
  el.append(root);
  const q = (k) => root.querySelector(`[data-k="${k}"]`);
  S.q = q;
  const r = await fetch(`${base}/data/manifest.json`); if (!r.ok) throw new Error('manifest ' + r.status);
  S.manifest = await r.json();
  for (const t of Object.keys(S.manifest.tasks)) { const o = document.createElement('option'); o.value = t; o.textContent = t[0].toUpperCase() + t.slice(1); q('task').append(o); }
  bindUI();
  S.views = METHODS.map((m) => makeView(m, root.querySelector(`[data-p="${m}"]`)));
  S.ro = new ResizeObserver(resize); S.ro.observe(root);
  startVideoClock();
  await loadTask(S.manifest.tasks[opts.task] ? opts.task : Object.keys(S.manifest.tasks)[0]);
  S.raf = requestAnimationFrame(loop);
}

export function unmount() {
  if (!S) return;
  S.alive = false; cancelAnimationFrame(S.raf);
  const v = S.q && S.q('video'); if (v) { try { v.pause(); if (S.vfc && v.cancelVideoFrameCallback) v.cancelVideoFrameCallback(S.vfc); } catch (e) { /* ignore */ } v.removeAttribute('src'); v.load(); }
  if (S.ro) S.ro.disconnect();
  for (const w of S.views) { w.controls.dispose(); disposeGroup(w.scene); w.renderer.dispose(); }
  if (S.root) S.root.remove();
  S = null;
}

// ------------------------------------------------------------------ views
function makeView(m, pane) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1)); pane.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x445566, 1.1));
  const dl = new THREE.DirectionalLight(0xffffff, 1.1); dl.position.set(0.4, 1, 0.8); scene.add(dl);
  const camera = new THREE.PerspectiveCamera(45, 1, 0.003, 20);
  const controls = new OrbitControls(camera, renderer.domElement);
  const root = new THREE.Group(); root.matrixAutoUpdate = false; root.matrix.makeScale(1, -1, -1); scene.add(root);  // OpenCV -> three.js
  const w = { m, pane, renderer, scene, camera, controls, root, lastTarget: new THREE.Vector3(), tag: pane.querySelector('.tag') };
  controls.addEventListener('change', () => syncFrom(w));
  return w;
}
let syncing = false;
function syncFrom(w) {  // same orbit offset/orientation/pan relative to each scene's own centre (frames are not registered)
  if (syncing || !S) return; syncing = true;
  const pan = w.controls.target.clone().sub(w.lastTarget); w.lastTarget.copy(w.controls.target);
  for (const o of S.views) if (o !== w) {
    o.controls.target.add(pan); o.lastTarget.copy(o.controls.target);
    o.camera.position.copy(o.controls.target).add(w.camera.position.clone().sub(w.controls.target));
    o.camera.quaternion.copy(w.camera.quaternion); o.camera.up.copy(w.camera.up); o.camera.zoom = w.camera.zoom; o.camera.updateProjectionMatrix(); o.controls.update();
  }
  syncing = false;
}
function resize() {
  if (!S) return;
  for (const w of S.views) { const r = w.pane.getBoundingClientRect(); const a = Math.max(10, r.width), b = Math.max(10, r.height);
    w.renderer.setSize(a, b, false); w.camera.aspect = a / b; if (S.view === 'fit') applyFit(w); w.camera.updateProjectionMatrix(); }
}
function disposeGroup(g) { g.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((x) => x.dispose()); }); }

// ------------------------------------------------------------------ data
function view(buf, a) {
  const C = { int16: Int16Array, int8: Int8Array, uint8: Uint8Array, uint16: Uint16Array, uint32: Uint32Array, float32: Float32Array }[a.dtype];
  return new C(buf, a.offset, a.shape.reduce((x, y) => x * y, 1));
}
async function loadTask(task) {
  const tm = S.manifest.tasks[task]; S.q('task').value = task;
  if (!S.data[task]) {
    const parts = {};
    await Promise.all(METHODS.map(async (m) => {
      const mm = tm.methods[m];
      if (!mm || !mm.available || !mm.available.overall) { parts[m] = null; return; }
      const r = await fetch(`${S.base}/${mm.file}`); if (!r.ok) throw new Error('fetch ' + mm.file);
      const buf = await r.arrayBuffer(); const A = {}; for (const [k, a] of Object.entries(mm.arrays)) A[k] = view(buf, a); parts[m] = { mm, A };
    }));
    const dr = await fetch(`${S.base}/diag/${task}.json`); S.diag[task] = dr.ok ? await dr.json() : null;
    S.data[task] = parts;
  }
  if (!S) return;
  S.task = task; S.T = tm.frames; S.frame = 0;
  const vid = S.q('video'); vid.pause(); vid.src = `${S.base}/${tm.video.file}`; vid.playbackRate = parseFloat(S.q('rate').value);
  const land = tm.video.width > tm.video.height;
  S.root.querySelectorAll('.pane').forEach((p) => p.classList.toggle('land', land));
  S.q('slider').max = S.T - 1;
  for (const w of S.views) build(w, task);
  resize(); setView(S.view); setFrame(0, true); about(task);
  vid.addEventListener('loadeddata', () => seek(S.frame), { once: true });
}
function build(w, task) {
  while (w.root.children.length) { const c = w.root.children[0]; w.root.remove(c); disposeGroup(c); }
  const P = S.data[task][w.m]; w.P = P; w.na && w.na.remove(); w.na = null;
  const tm = S.manifest.tasks[task];
  const av = tm.methods[w.m] && tm.methods[w.m].available;
  if (!P || !av || !av.overall) {
    const why = av && av.reasons && av.reasons.overall ? av.reasons.overall : 'no valid 3D hands or objects';
    w.na = document.createElement('div'); w.na.className = 'na'; w.na.textContent = `${S.manifest.methods[w.m]}: Not available (${why})`; w.pane.append(w.na); return;
  }
  const { mm, A } = P;
  w.root.add(new THREE.AxesHelper(0.05)); w.camAxes = w.root.children[w.root.children.length - 1];
  w.hands = SIDES.map((side, s) => {
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(778 * 3), 3));
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(778 * 3), 3)); g.setIndex(new THREE.BufferAttribute(A.hand_faces, 1));
    const mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: COL[side], roughness: 0.7, side: THREE.DoubleSide, transparent: true, opacity: 0.85 }));
    mesh.frustumCulled = false; w.root.add(mesh);
    const bg = new THREE.BufferGeometry(); bg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(S.manifest.bones.length * 6), 3));
    // overlays drawn on top of the (transparent) hand mesh: unlit, no depth test, transparent queue with high renderOrder
    const bonesObj = new THREE.LineSegments(bg, new THREE.LineBasicMaterial({ color: COL.bone, transparent: true, opacity: 0.85, depthTest: false, depthWrite: false }));
    bonesObj.renderOrder = 8; bonesObj.frustumCulled = false; w.root.add(bonesObj);
    const jm = new THREE.InstancedMesh(new THREE.SphereGeometry(0.0016, 8, 6), new THREE.MeshBasicMaterial({ color: COL.bone, transparent: true, depthTest: false, depthWrite: false }), 21);
    jm.renderOrder = 9; jm.frustumCulled = false; w.root.add(jm);
    const ring = new THREE.InstancedMesh(new THREE.SphereGeometry(0.0082, 16, 12), new THREE.MeshBasicMaterial({ color: 0x1b1f24, transparent: true, depthTest: false, depthWrite: false }), 5);
    ring.renderOrder = 10; ring.frustumCulled = false; w.root.add(ring);  // dark outline behind each fingertip marker
    const tipm = new THREE.InstancedMesh(new THREE.SphereGeometry(0.0068, 16, 12), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, depthTest: false, depthWrite: false }), 5);
    tipm.renderOrder = 11; tipm.frustumCulled = false; w.root.add(tipm);
    return { mesh, bones: bonesObj, jm, tipm, ring };
  });
  w.objs = mm.objects.map((o, j) => {
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(A[`obj${j}_verts`], 3)); g.setIndex(new THREE.BufferAttribute(A[`obj${j}_faces`], 1)); g.computeVertexNormals();
    const mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: COL.obj[j % 2], roughness: 0.55, side: THREE.DoubleSide, transparent: true, opacity: 0.8 }));
    mesh.matrixAutoUpdate = false; mesh.frustumCulled = false;
    g.computeBoundingSphere(); const ax = new THREE.AxesHelper(Math.max(0.03, g.boundingSphere.radius * 1.4)); mesh.add(ax);
    w.root.add(mesh);
    const al = o.known_alignment; const R = new THREE.Matrix3().set(...al.R.flat());
    return { mesh, ax, name: o.name, sdf: sdfKnown(o.name), Rinv: R.clone().transpose(), t: new THREE.Vector3(...al.t) };
  });
  // scene centre and gravity for presets
  const K = mm.K; w.K = K; w.size = mm.image_size; w.grav = new THREE.Vector3(...mm.gravity_cam).normalize();
  const cs = [];
  for (let j = 0; j < w.objs.length; j++) { const Pj = A[`obj${j}_pose`], va = A[`obj${j}_valid`]; for (let k = 0; k < S.T; k++) if (va[k]) cs.push([Pj[k * 16 + 3], Pj[k * 16 + 7], Pj[k * 16 + 11]]); }
  if (!cs.length) for (let k = 0; k < S.T; k++) for (let s = 0; s < 2; s++) if (A.hand_valid[k * 2 + s]) { const b = (k * 2 + s) * 21 * 3; cs.push([A.joints[b], A.joints[b + 1], A.joints[b + 2]]); }
  const med = (i) => { const a = cs.map((c) => c[i]).sort((x, y) => x - y); return a.length ? a[a.length >> 1] : (i === 2 ? 0.5 : 0); };
  w.center = new THREE.Vector3(med(0), med(1), med(2));
  // "fit" framing: per frame, the box (normalised image coordinates x/z, y/z, OpenCV) of the valid hand joints and the valid
  // objects' bounding spheres; the task box is the 10th-90th percentile of those boxes, so brief excursions (a ball
  // tossed out of frame) do not shrink the hands and objects
  const bx = [[], [], [], []];
  for (let k = 0; k < S.T; k++) {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const addPt = (x, y, z) => { if (z <= 1e-3) return; x0 = Math.min(x0, x / z); x1 = Math.max(x1, x / z); y0 = Math.min(y0, y / z); y1 = Math.max(y1, y / z); };
    for (let s = 0; s < 2; s++) if (mm.available[`hands_${SIDES[s]}`] && A.hand_valid[k * 2 + s]) { const b = (k * 2 + s) * 63; for (let j = 0; j < 21; j++) addPt(A.joints[b + j * 3], A.joints[b + j * 3 + 1], A.joints[b + j * 3 + 2]); }
    w.objs.forEach((o, j) => {
      if (!mm.available.objects[o.name] || !A[`obj${j}_valid`][k]) return; const Pj = A[`obj${j}_pose`]; const r = o.mesh.geometry.boundingSphere.radius;
      const x = Pj[k * 16 + 3], y = Pj[k * 16 + 7], z = Pj[k * 16 + 11]; addPt(x - r, y - r, z); addPt(x + r, y + r, z);
    });
    if (Number.isFinite(x0)) { bx[0].push(x0); bx[1].push(x1); bx[2].push(y0); bx[3].push(y1); }
  }
  const pct = (a, q) => { const s2 = [...a].sort((u, v) => u - v); return s2[Math.min(s2.length - 1, Math.max(0, Math.round(q * (s2.length - 1))))]; };
  w.fitBox = bx[0].length ? [pct(bx[0], 0.1), pct(bx[1], 0.9), pct(bx[2], 0.1), pct(bx[3], 0.9)] : null;
}
function applyFit(w) {  // keep the true camera position and orientation; crop the view (lens shift + zoom) so the box fills ~70 %
  const cam = w.camera; if (!w.fitBox) { cam.clearViewOffset(); return; }
  const [x0, x1, y0, y1] = w.fitBox; const r = w.pane.getBoundingClientRect(); const Hf = Math.max(10, r.height), Wf = Math.max(10, r.width), aspect = Wf / Hf;
  const Tv = Math.tan(cam.fov * Math.PI / 360); const pxPerTan = Hf / (2 * Tv);
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2; const h = Math.max((y1 - y0) / 2, (x1 - x0) / 2 / aspect) / 0.7, hw = h * aspect;
  cam.setViewOffset(Wf, Hf, (cx - hw) * pxPerTan + Wf / 2, (cy - h) * pxPerTan + Hf / 2, 2 * hw * pxPerTan, 2 * h * pxPerTan);
}

// ------------------------------------------------------------------ per frame
const _c = new THREE.Color(), _grey = new THREE.Color(), _m = new THREE.Matrix4(), _v = new THREE.Vector3();
function setFrame(k, fromVideo) {
  if (!S || !S.task) return;
  k = Math.max(0, Math.min(S.T - 1, k | 0)); S.frame = k;
  S.q('slider').value = k; S.q('flab').textContent = `frame ${k} / ${S.T - 1} · ${(k / FPS).toFixed(2)} s`;
  const dg = S.diag[S.task];
  for (const w of S.views) {
    const chips = [];
    if (!w.P || w.na) { w.tag.innerHTML = `<b class="t">${S.manifest.methods[w.m]}</b>`; renderDiag(w, null, k); continue; }
    const { mm, A } = w.P; const sc = mm.hand_scale, of = mm.hand_offset; const fd = dg && dg.methods[w.m] ? dg.methods[w.m].frames[k] : null;
    SIDES.forEach((side, s) => {
      const av = mm.available; const has = av[`hands_${side}`];
      const h = w.hands[s]; const valid = has && A.hand_valid[k * 2 + s] === 1;
      h.mesh.visible = valid && S.show.mesh; h.bones.visible = valid && S.show.skeleton; h.jm.visible = valid && S.show.skeleton;
      h.tipm.visible = valid && S.show.tips; h.ring.visible = h.tipm.visible;
      if (has) chips.push(`<span class="chip">${side} hand: ${valid ? '<b class="ok">valid</b>' : '<b class="bad">invalid</b>'}</span>`);
      if (!valid) return;
      const pos = h.mesh.geometry.attributes.position.array, b = (k * 2 + s) * 778 * 3;
      for (let n = 0; n < 778 * 3; n++) pos[n] = A.hand_q[b + n] * sc[n % 3] + of[n % 3];
      h.mesh.geometry.attributes.position.needsUpdate = true; h.mesh.geometry.computeVertexNormals();
      const jb = (k * 2 + s) * 63; const bp = h.bones.geometry.attributes.position.array;
      S.manifest.bones.forEach(([i0, i1], bi) => { for (let c = 0; c < 3; c++) { bp[bi * 6 + c] = A.joints[jb + i0 * 3 + c]; bp[bi * 6 + 3 + c] = A.joints[jb + i1 * 3 + c]; } });
      h.bones.geometry.attributes.position.needsUpdate = true;
      for (let j = 0; j < 21; j++) { _m.makeTranslation(A.joints[jb + j * 3], A.joints[jb + j * 3 + 1], A.joints[jb + j * 3 + 2]); h.jm.setMatrixAt(j, _m); }
      h.jm.instanceMatrix.needsUpdate = true;
      const tb = (k * 2 + s) * 15; const hd = fd && fd.hands[side];
      for (let f = 0; f < 5; f++) {
        _m.makeTranslation(A.tips[tb + f * 3], A.tips[tb + f * 3 + 1], A.tips[tb + f * 3 + 2]); h.tipm.setMatrixAt(f, _m); h.ring.setMatrixAt(f, _m);
        h.tipm.setColorAt(f, tipColor(nearestTip(hd, f, mm.available), _c));
      }
      h.tipm.instanceMatrix.needsUpdate = true; h.ring.instanceMatrix.needsUpdate = true; if (h.tipm.instanceColor) h.tipm.instanceColor.needsUpdate = true;
      vertexColour(w, h, pos, k);
    });
    w.objs.forEach((o, j) => {
      const oav = mm.available.objects[o.name]; const valid = oav && A[`obj${j}_valid`][k] === 1; o.mesh.visible = valid && S.show.objects; o.ax.visible = S.show.objaxes;
      chips.push(oav ? `<span class="chip">${o.name.replace('_', ' ')}: ${valid ? '<b class="ok">valid</b>' : '<b class="bad">invalid</b>'}</span>`
        : `<span class="chip mut" title="${mm.available.reasons[o.name] || ''}">${o.name.replace('_', ' ')}: Not available</span>`);
      if (valid) { const Pj = A[`obj${j}_pose`]; o.mesh.matrix.fromArray(Array.from(Pj.subarray(k * 16, k * 16 + 16))).transpose(); o.mesh.matrixWorldNeedsUpdate = true; }
    });
    if (w.camAxes) w.camAxes.visible = S.show.camaxes;
    if (!mm.available.hands_right && !mm.available.hands_left) chips.push('<span class="chip mut">3D hands: Not available</span>');
    if (!mm.available.interaction) chips.push(`<span class="chip mut">hand–object interaction: Not available</span>`);
    w.tag.innerHTML = `<b class="t">${S.manifest.methods[w.m]}</b><br>${chips.join('')}`;
    renderDiag(w, fd, k);
  }
  if (!fromVideo) seek(k);
}
function nearestTip(hd, f, av) {  // signed distance (m) of fingertip f to the nearest valid, available object, selected geometry
  if (!hd) return null; let best = null;
  for (const [on, rec] of Object.entries(hd.objects)) {
    if (av && !av.objects[on]) continue;
    const arr = S.tipSrc === 'own' ? rec.tips_own_mm : rec.tips_known_mm; const v = arr[f];
    if (v === null || v === undefined) continue; if (best === null || Math.abs(v) < Math.abs(best)) best = v;
  }
  return best === null ? null : best / 1000;
}
function vertexColour(w, h, pos, k) {
  const mat = h.mesh.material; const on = S.show.vcolor;
  if (mat.vertexColors !== on) { mat.vertexColors = on; mat.color.set(on ? 0xffffff : (h === w.hands[0] ? COL.left : COL.right)); mat.needsUpdate = true; }
  if (!on) return;
  const col = h.mesh.geometry.attributes.color.array; const A = w.P.A; const live = [];
  w.objs.forEach((o, j) => { if (w.P.mm.available.objects[o.name] && A[`obj${j}_valid`][k] && o.sdf) { const Pj = A[`obj${j}_pose`]; const M = new THREE.Matrix4().fromArray(Array.from(Pj.subarray(k * 16, k * 16 + 16))).transpose(); live.push({ o, inv: M.clone().invert() }); } });
  for (let n = 0; n < 778; n++) {
    let d = null;
    for (const { o, inv } of live) {
      _v.set(pos[n * 3], pos[n * 3 + 1], pos[n * 3 + 2]).applyMatrix4(inv).sub(o.t).applyMatrix3(o.Rinv);  // delivered object frame -> known frame
      const s = o.sdf(_v.x, _v.y, _v.z); if (d === null || s < d) d = s;
    }
    distColor(d, _c); col[n * 3] = _c.r; col[n * 3 + 1] = _c.g; col[n * 3 + 2] = _c.b;
  }
  h.mesh.geometry.attributes.color.needsUpdate = true;
}

// ------------------------------------------------------------------ diagnostics panel + timeline strip
function fmt(v) { return v === null || v === undefined ? '–' : v.toFixed(1); }
function renderDiag(w, fd, k) {
  const card = S.q(`diag-${w.m}`); const name = S.manifest.methods[w.m];
  const dm = S.diag[S.task] && S.diag[S.task].methods[w.m];
  const av = S.manifest.tasks[S.task].methods[w.m].available;
  if (!w.P || w.na || !dm) { card.innerHTML = `<h4>${name}</h4><p class="mut">Not available: ${(av && av.reasons && av.reasons.overall) || 'no valid 3D hands or objects'}.</p>`; return; }
  if (!av.interaction) { card.innerHTML = `<h4>${name} · frame ${k}</h4><p class="mut">Hand–object diagnostics not available: ${Object.entries(av.reasons).filter(([key]) => key !== 'interaction').map(([key, v]) => `${key.replace('_', ' ')}: ${v}`).join('; ') || av.reasons.interaction}.</p>`; return; }
  let html = `<h4>${name} · frame ${k}</h4><p class="note">Distances in mm, ${LBL_C}. Positive = gap, negative = penetration.</p>`;
  const hands = fd ? Object.entries(fd.hands) : [];
  if (!hands.length) html += '<p class="mut">No valid hand on this frame.</p>';
  for (const [side, hd] of hands) {
    const objs = Object.entries(hd.objects);
    if (!objs.length) { html += `<p class="mut">${side} hand: no valid object on this frame.</p>`; continue; }
    for (const [on, rec] of objs.filter(([on2]) => av.objects[on2])) {
      html += `<table><tr><th>${side} hand → ${on.replace('_', ' ')}</th>${FINGERS.map((f) => `<th>${f}</th>`).join('')}</tr>`;
      html += `<tr><td>known geometry (signed)</td>${rec.tips_known_mm.map((v, i) => `<td class="${rec.contact_known[i] ? 'ok' : ''}">${fmt(v)}</td>`).join('')}</tr>`;
      html += `<tr><td>own mesh (${rec.own_signed ? 'signed' : 'unsigned: mesh not watertight'})</td>${rec.tips_own_mm.map((v) => `<td>${fmt(v)}</td>`).join('')}</tr></table>`;
      html += `<p class="note">Penetration into known geometry: max ${fmt(rec.pen_known.max_mm)} mm, ${rec.pen_known.n_inside} of 778 hand vertices inside. Own mesh: ${rec.pen_own ? `max ${fmt(rec.pen_own.max_mm)} mm, ${rec.pen_own.n_inside} vertices` : 'not computable (no inside/outside without a watertight mesh)'}. Gap (min distance): known ${fmt(rec.gap_known_mm)} mm, own ${fmt(rec.gap_own_mm)} mm. Apparent contact (heuristic flag, |d| ≤ ${S.manifest.thresholds.contact_band_mm} mm, known geometry): ${rec.contact_known.map((c, i) => c ? FINGERS[i] : null).filter(Boolean).join(', ') || 'none'}.</p>`;
    }
  }
  html += `<p class="note"><b>Continuity flags</b> (heuristic flags, thresholds in the text): ${fd && fd.flags.length ? fd.flags.map((x) => `<span class="bad">${x}</span>`).join('; ') : 'none on this frame'}.</p>`;
  html += `<canvas class="strip" data-strip="${w.m}" height="22" title="click to seek: red = continuity flag, green = heuristic fingertip contact, grey = no valid hand"></canvas>`;
  card.innerHTML = html;
  const cv = card.querySelector('canvas'); drawStrip(cv, dm, k, av);
  cv.addEventListener('click', (e) => { const r = cv.getBoundingClientRect(); setFrame(Math.round((e.clientX - r.left) / r.width * (S.T - 1))); });
}
function drawStrip(cv, dm, k, av) {
  const wpx = Math.max(100, Math.round(cv.getBoundingClientRect().width || 400)); cv.width = wpx; const ctx = cv.getContext('2d'); const T = S.T;
  ctx.clearRect(0, 0, wpx, 22);
  for (let i = 0; i < T; i++) {
    const f = dm.frames[i]; const x0 = Math.floor(i / T * wpx), x1 = Math.max(x0 + 1, Math.floor((i + 1) / T * wpx));
    const hands = Object.values(f.hands); let contact = false;
    for (const hd of hands) for (const [on, rec] of Object.entries(hd.objects)) if (av.objects[on] && rec.contact_known.some(Boolean)) contact = true;
    ctx.fillStyle = !hands.length ? '#b9bfc8' : contact ? '#29b85c' : '#9ec1f5'; ctx.fillRect(x0, 8, x1 - x0, 14);
    if (f.flags.length) { ctx.fillStyle = '#d93a2e'; ctx.fillRect(x0, 0, x1 - x0, 7); }
  }
  ctx.fillStyle = '#111'; ctx.fillRect(Math.floor(k / T * wpx), 0, 2, 22);
}

// ------------------------------------------------------------------ video clock
function frameOfTime(t) { return Math.max(0, Math.min(S.T - 1, Math.floor(t * FPS + 0.02))); }
function seek(k) { const v = S && S.q('video'); if (!v || !v.src) return; const t = (k + 0.5) / FPS; if (Math.abs(v.currentTime - t) > 0.5 / FPS) v.currentTime = t; }
function startVideoClock() {
  const v = S.q('video');
  if (v.requestVideoFrameCallback) {
    // while playing, the video drives the frame index; while paused, the frame is chosen by the user and the video is seeked to it
    const cb = (now, meta) => { if (!S || !S.alive) return; const k = frameOfTime(meta.mediaTime); S.q('vlab').textContent = `video frame ${k}`;
      if (!v.paused && k !== S.frame) setFrame(k, true); S.vfc = v.requestVideoFrameCallback(cb); };
    S.vfc = v.requestVideoFrameCallback(cb);
  }
  v.onseeked = () => { if (!S) return; const k = frameOfTime(v.currentTime); S.q('vlab').textContent = `video frame ${k}`; if (!v.paused && k !== S.frame) setFrame(k, true); };
  v.onplay = () => { S.q('play').textContent = 'Pause'; }; v.onpause = () => { S.q('play').textContent = 'Play'; };
}
function loop() {
  if (!S || !S.alive) return;
  const v = S.q('video');
  if (!v.requestVideoFrameCallback && !v.paused) { const k = frameOfTime(v.currentTime); if (k !== S.frame) setFrame(k, true); }
  for (const w of S.views) w.renderer.render(w.scene, w.camera);
  S.raf = requestAnimationFrame(loop);
}

// ------------------------------------------------------------------ presets + UI
const toThree = (p) => new THREE.Vector3(p.x, -p.y, -p.z);
function setView(name) {
  S.view = name; syncing = true;
  for (const w of S.views) {
    if (!w.center) continue;
    const cam = w.camera; const c = toThree(w.center); const up = toThree(w.grav.clone().negate()).normalize();
    cam.clearViewOffset();
    if (name === 'camera' || name === 'fit') {  // the true camera pose: optical centre, looking along the optical axis
      cam.fov = 2 * Math.atan(w.size[1] / 2 / w.K[1][1]) * 180 / Math.PI; cam.up.set(0, 1, 0); cam.position.set(0, 0, 0); w.controls.target.set(0, 0, -Math.max(0.05, w.center.z));
    } else {
      cam.fov = 40; const r = Math.max(0.35, 0.8 * w.center.z);
      if (name === 'side') { const sd = new THREE.Vector3(1, 0, 0); sd.addScaledVector(up, -sd.dot(up)).normalize(); cam.up.copy(up); cam.position.copy(c).addScaledVector(sd, r); }
      else { const fw = new THREE.Vector3(0, 0, -1); fw.addScaledVector(up, -fw.dot(up)).normalize(); cam.up.copy(fw); cam.position.copy(c).addScaledVector(up, r); }
      w.controls.target.copy(c);
    }
    cam.zoom = 1; cam.updateProjectionMatrix(); cam.lookAt(w.controls.target); w.controls.update(); w.lastTarget.copy(w.controls.target);
    if (name === 'fit') { applyFit(w); cam.updateProjectionMatrix(); }
  }
  syncing = false;
}
function bindUI() {
  const q = S.q, root = S.root;
  q('task').addEventListener('change', (e) => loadTask(e.target.value));
  q('play').addEventListener('click', () => { const v = q('video'); if (v.paused) v.play().catch(() => {}); else v.pause(); });
  q('prev').addEventListener('click', () => { q('video').pause(); setFrame(S.frame - 1); });
  q('next').addEventListener('click', () => { q('video').pause(); setFrame(S.frame + 1); });
  q('rate').addEventListener('change', (e) => { q('video').playbackRate = parseFloat(e.target.value); });
  q('slider').addEventListener('input', (e) => { q('video').pause(); setFrame(parseInt(e.target.value, 10)); });
  q('tipsrc').addEventListener('change', (e) => { S.tipSrc = e.target.value; setFrame(S.frame, true); });
  root.querySelectorAll('[data-t]').forEach((c) => c.addEventListener('change', () => { S.show[c.dataset.t] = c.checked; setFrame(S.frame, true); }));
  root.querySelectorAll('[data-v]').forEach((b) => b.addEventListener('click', () => setView(b.dataset.v)));
  root.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') { q('video').pause(); setFrame(S.frame - 1); e.preventDefault(); }
    else if (e.key === 'ArrowRight') { q('video').pause(); setFrame(S.frame + 1); e.preventDefault(); }
  });
  root.tabIndex = 0;
}
function about(task) {
  const tm = S.manifest.tasks[task]; const rows = [];
  for (const m of METHODS) {
    const mm = tm.methods[m]; if (!mm || !mm.available || !mm.available.overall) { rows.push(`<li>${S.manifest.methods[m]}: not available.</li>`); continue; }
    rows.push(`<li>${S.manifest.methods[m]}: hands valid on ${mm.hand_valid_frames.right} (right) / ${mm.hand_valid_frames.left} (left) of ${tm.frames} frames; ` +
      mm.objects.map((o) => `${o.name.replace('_', ' ')} valid on ${o.valid_frames}, own mesh ${o.mesh_watertight ? 'watertight (signed distances)' : 'not watertight (unsigned distances only)'}, known-geometry alignment residual ${o.known_alignment.rms_mm} mm`).join('; ') + '.</li>');
  }
  S.q('about').innerHTML = `<ul>
  <li>Each panel shows one method's delivered reconstruction ${S.manifest.checkpoint === 'T+0120m' ? '2 hours after start' : ''} in that method's own camera frame (OpenCV axes, metres). The two methods' cameras are not registered to each other; views are synchronised relative to each scene's centre.</li>
  <li>Fingertips are MANO fingertip vertices (ids ${Object.values(S.manifest.fingertips.vertex_ids).join(', ')}); the skeleton is the delivered 21-joint set.</li>
  <li>Known object geometry: the object's published dimensions, placed at the delivered pose through a rigid alignment of the known shape to the method's own mesh (ICP, no scaling). It is common to both methods; it is not a measurement of the real object's position.</li>
  <li>Distances to a method's own mesh are unsigned unless that mesh is watertight. All numbers are ${LBL_C}. Contact and continuity flags are heuristics with the thresholds stated next to them.</li>
  <li>Not verifiable without 3D ground truth: absolute depth, true contact, true penetration.</li>${rows.join('')}</ul>
  <p class="note">Source files and SHA-256: data/manifest.json.</p>`;
}
