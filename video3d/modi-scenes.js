// ===== Scenes + timeline for modi.html (appended after the shared engine from long.html) =====
// A neutral, documentary-style biography told with symbolic 3D scenes (no likeness of any person).

const SAFFRON = 0xff9933, GREEN = 0x138808, WHITE = 0xffffff;
function skyDome(group, top, bot, r = 900) {
  const u = { uTop: { value: new THREE.Color(top) }, uBot: { value: new THREE.Color(bot) } };
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 16), new THREE.ShaderMaterial({
    uniforms: u, side: THREE.BackSide, depthWrite: false,
    vertexShader: `varying vec3 vP; void main(){vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader: `uniform vec3 uTop,uBot; varying vec3 vP; void main(){float h=normalize(vP).y; gl_FragColor=vec4(mix(uBot,uTop,smoothstep(-0.05,0.45,h)),1.0);}`
  }));
  m.renderOrder = -1; group.add(m); return u;
}
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
const lam = (color, extra = {}) => new THREE.MeshLambertMaterial({ color, ...extra });

// =====================================================================
// VILLAGE RAILWAY STATION (z = -3000)
// =====================================================================
const VIL = V(0, 0, -3000);
const village = new THREE.Group(); village.position.copy(VIL); scene.add(village);
const vilSky = skyDome(village, 0x5b8fd6, 0xffb36b);
{
  village.add(new THREE.Mesh(new THREE.PlaneGeometry(1600, 1600).rotateX(-Math.PI / 2), lam(0xa88a5c)));
  const ballast = new THREE.Mesh(new THREE.BoxGeometry(1000, 0.3, 4), lam(0x6f6457)); ballast.position.y = 0.15; village.add(ballast);
  [-0.75, 0.75].forEach(z => { const r = new THREE.Mesh(new THREE.BoxGeometry(1000, 0.18, 0.14), new THREE.MeshStandardMaterial({ color: 0x9aa0a8, metalness: 0.8, roughness: 0.35 })); r.position.set(0, 0.42, z); village.add(r); });
  const sl = new THREE.InstancedMesh(new THREE.BoxGeometry(0.35, 0.12, 2.5), lam(0x4a3b2c), 1250);
  const m4 = new THREE.Matrix4(); for (let i = 0; i < 1250; i++) { m4.makeTranslation(-500 + i * 0.8, 0.32, 0); sl.setMatrixAt(i, m4); } village.add(sl);
  // platform + roof
  const plat = new THREE.Mesh(new THREE.BoxGeometry(70, 1.0, 6), lam(0xb9b2a5)); plat.position.set(0, 0.5, 5.2); village.add(plat);
  const edge = new THREE.Mesh(new THREE.BoxGeometry(70, 0.05, 0.4), lam(0xf2d14b)); edge.position.set(0, 1.03, 2.5); village.add(edge);
  const roof = new THREE.Mesh(new THREE.BoxGeometry(44, 0.25, 5.2), lam(0x7a3b2a)); roof.position.set(0, 4.8, 5.6); roof.rotation.x = -0.06; village.add(roof);
  const pil = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.12, 0.12, 3.8, 8), lam(0x3d4d5c), 12);
  for (let i = 0; i < 12; i++) { m4.makeTranslation(-20 + i * (40 / 11), 2.9, 6.8); pil.setMatrixAt(i, m4); } village.add(pil);
  // station building
  const bld = new THREE.Mesh(new THREE.BoxGeometry(22, 5.5, 7), lam(0xe8d9b5)); bld.position.set(4, 2.75, 12); village.add(bld);
  const broof = new THREE.Mesh(new THREE.BoxGeometry(24, 0.7, 8.6), lam(0x8a3a24)); broof.position.set(4, 5.8, 12); village.add(broof);
  const doorTex = canvasTex(512, 128, (x, w, h) => { x.fillStyle = '#e8d9b5'; x.fillRect(0, 0, w, h); for (let i = 0; i < 6; i++) { x.fillStyle = i % 2 ? '#3a2a1c' : '#4c6a8a'; x.fillRect(20 + i * 82, 30, 50, 98); } });
  const front = new THREE.Mesh(new THREE.PlaneGeometry(22, 5.5), lam(0xffffff, { map: doorTex })); front.position.set(4, 2.75, 8.49); front.rotation.y = Math.PI; village.add(front);
  // signboard (yellow board, black text)
  const signTex = canvasTex(1024, 256, (x, w, h) => { x.fillStyle = '#f5c518'; x.fillRect(0, 0, w, h); x.strokeStyle = '#111'; x.lineWidth = 14; x.strokeRect(7, 7, w - 14, h - 14); x.fillStyle = '#111'; x.font = '900 120px "DejaVu Sans", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('VADNAGAR', w / 2, h / 2 + 6); });
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(6, 1.5), lam(0xffffff, { map: signTex, side: THREE.DoubleSide })); sign.position.set(9, 3.4, 3.4); village.add(sign);
  [6.4, 11.6].forEach(x => { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 2.6, 6), lam(0x222222)); p.position.set(x, 2.3, 3.4); village.add(p); });
  // tea stall
  const counter = new THREE.Mesh(new THREE.BoxGeometry(3.2, 1.1, 1.4), lam(0x7b4a26)); counter.position.set(-8, 1.55, 5.4); village.add(counter);
  const awnTex = canvasTex(256, 64, (x, w, h) => { for (let i = 0; i < 8; i++) { x.fillStyle = i % 2 ? '#ffffff' : '#ff9933'; x.fillRect(i * 32, 0, 32, h); } });
  const awn = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.08, 2.2), lam(0xffffff, { map: awnTex })); awn.position.set(-8, 3.3, 5.2); awn.rotation.x = 0.18; village.add(awn);
  [[-9.7, 4.5], [-6.3, 4.5], [-9.7, 6.1], [-6.3, 6.1]].forEach(([x, z]) => { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 2.3, 6), lam(0x5a3a1e)); p.position.set(x, 2.15, z); village.add(p); });
  const kettle = new THREE.Mesh(new THREE.SphereGeometry(0.28, 20, 14), new THREE.MeshPhongMaterial({ color: 0xc9ccd2, specular: 0xffffff, shininess: 80 })); kettle.position.set(-8.6, 2.38, 5.2); village.add(kettle);
  const spout = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.06, 0.4, 8), kettle.material); spout.position.set(-8.3, 2.48, 5.2); spout.rotation.z = -0.9; village.add(spout);
  const stove = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.36, 0.25, 16), lam(0x333333)); stove.position.set(-8.6, 2.2, 5.2); village.add(stove);
  const glow = new THREE.PointLight(0xff7a2a, 4, 5, 2); glow.position.set(-8.6, 2.25, 5.0); village.add(glow);
  for (let i = 0; i < 5; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.055, 0.14, 10), lam(0xf4efe6)); c.position.set(-7.6 + i * 0.22, 2.17, 4.9); village.add(c); }
  // houses + trees
  const HN = 150, hs = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), lam(0xffffff), HN);
  const rf = new THREE.InstancedMesh(new THREE.ConeGeometry(0.75, 0.6, 4).rotateY(Math.PI / 4), lam(0x9b4a2c), HN);
  const pal = [0xf2e3c6, 0xe9c9a0, 0xd8e2e8, 0xf0d5d5, 0xe3d2a8, 0xcfe0c9], q = new THREE.Quaternion(), sc = new THREE.Vector3(), ps = new THREE.Vector3();
  for (let i = 0; i < HN; i++) {
    let x, z; do { x = (rand() - 0.5) * 320; z = 22 + rand() * 160; } while (Math.abs(x) < 16 && z < 30);
    const w = 4 + rand() * 4, h = 3 + rand() * 4, d = 4 + rand() * 4;
    m4.compose(ps.set(x, h / 2, z), q, sc.set(w, h, d)); hs.setMatrixAt(i, m4); hs.setColorAt(i, new THREE.Color(pal[i % pal.length]));
    m4.compose(ps.set(x, h + 0.9, z), q, sc.set(w * 0.95, 3, d * 0.95)); rf.setMatrixAt(i, m4);
  }
  village.add(hs, rf);
  const TN = 120, tr = new THREE.InstancedMesh(new THREE.ConeGeometry(1.6, 4.5, 7), lam(0x3f6b2e), TN), tk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.2, 0.25, 2, 6), lam(0x5a4028), TN);
  for (let i = 0; i < TN; i++) {
    const x = (rand() - 0.5) * 400, z = rand() < 0.5 ? -15 - rand() * 120 : 20 + rand() * 180, s = 0.8 + rand() * 0.8;
    m4.compose(ps.set(x, 2 * s + 2.2 * s, z), q, sc.set(s, s, s)); tr.setMatrixAt(i, m4);
    m4.compose(ps.set(x, s, z), q, sc.set(s, s, s)); tk.setMatrixAt(i, m4);
  }
  village.add(tr, tk);
  village.add(new THREE.HemisphereLight(0xffe2b8, 0x6b5a40, 1.0));
  const sunL = new THREE.DirectionalLight(0xffc887, 1.7); sunL.position.set(-200, 90, 160); village.add(sunL, sunL.target);
}
// steam
const STN = 260, stPos = new Float32Array(STN * 3), stInfo = [];
for (let i = 0; i < STN; i++) stInfo.push([rand(), rand() * 6.28, 0.5 + rand()]);
const stGeo = new THREE.BufferGeometry(); stGeo.setAttribute('position', new THREE.BufferAttribute(stPos, 3));
const steam = new THREE.Points(stGeo, new THREE.PointsMaterial({ map: SOFT, size: 0.35, transparent: true, opacity: 0.35, depthWrite: false, color: 0xffffff }));
steam.frustumCulled = false; village.add(steam);
// train
const train = new THREE.Group(); village.add(train);
{
  const winTex = canvasTex(512, 64, (x, w, h) => { x.fillStyle = '#7a1f1f'; x.fillRect(0, 0, w, h); for (let i = 0; i < 10; i++) { x.fillStyle = '#ffd98a'; x.fillRect(14 + i * 50, 16, 30, 26); } x.fillStyle = '#e7c35a'; x.fillRect(0, 50, w, 5); });
  const coachMat = lam(0xffffff, { map: winTex });
  const eng = new THREE.Mesh(new THREE.BoxGeometry(15, 3.8, 3.1), lam(0x1f3b63)); eng.position.set(0, 2.6, 0); train.add(eng);
  const stripe = new THREE.Mesh(new THREE.BoxGeometry(15.05, 0.4, 3.15), lam(0xf2c14e)); stripe.position.set(0, 2.2, 0); train.add(stripe);
  for (let i = 1; i <= 7; i++) { const c = new THREE.Mesh(new THREE.BoxGeometry(18, 3.5, 3.0), coachMat); c.position.set(i * 18.6 + 1.5, 2.45, 0); train.add(c); }
  const head = new THREE.Sprite(new THREE.SpriteMaterial({ map: SOFT, color: 0xfff2c0, blending: THREE.AdditiveBlending, depthWrite: false })); head.scale.set(4, 4, 1); head.position.set(-7.6, 3.2, 0); train.add(head);
}
function S_village(lt) {
  village.visible = true; scene.fog = new THREE.FogExp2(0xf0c08a, 0.0045);
  const k = seg(lt, 0, 40);
  vilSky.uTop.value.setRGB(lerp(0.2, 0.42, k), lerp(0.35, 0.62, k), lerp(0.65, 0.9, k));
  vilSky.uBot.value.setRGB(1.0, lerp(0.6, 0.82, k), lerp(0.35, 0.62, k));
  camPath([
    [0, [70, 42, 90], [0, 2, 5]], [8, [26, 11, 30], [-2, 2, 5]], [16, [6, 3.6, 13], [-8, 2, 5.4]], [22, [-6.4, 2.9, 8.2], [-8.4, 2.3, 5.2]],
    [28, [-5.5, 3.2, 9.5], [-8, 2.3, 5]], [36, [20, 14, 26], [-30, 2, 0]], [44, [60, 30, 50], [-60, 0, 0]]
  ], lt);
  camera.position.add(VIL); const look = new THREE.Vector3(); camera.getWorldDirection(look);
  train.position.set(260 - (lt - 14) * 22, 0, 0);
  stInfo.forEach(([ph, a, s], i) => {
    const age = (ph + lt * 0.35 * s) % 1;
    stPos.set([-8.25 + Math.sin(a + lt) * 0.15 * age + age * 0.4, 2.62 + age * 1.6, 5.2 + Math.cos(a) * 0.15 * age], i * 3);
  });
  stGeo.attributes.position.needsUpdate = true;
}

// =====================================================================
// HIMALAYAS (reuse terrain from shared engine, clear sunrise)
// =====================================================================
const himSky = skyDome(mountains, 0x4f86c9, 0xffcf9a, 1200);
function S_himalaya(lt) {
  mountains.visible = true; scene.fog = new THREE.FogExp2(0xe3d6c8, 0.0011);
  let x, y, z, lx, ly, lz;
  if (lt < 12) { z = 380 - lt * 14; x = pathX(z); y = terrainH(x, z) + 18; const z2 = z - 50; lx = pathX(z2); lz = z2; ly = terrainH(lx, z2) + 16; }
  else { const k = ease(seg(lt, 12, 25)), z0 = 380 - 12 * 14; z = z0 - k * 80; x = pathX(z) + k * 30; y = terrainH(pathX(z0), z0) + 18 + k * 230; lx = pathX(z - 220); lz = z - 280; ly = lerp(terrainH(lx, lz) + 10, 60, k); }
  camera.position.set(x, y, z).add(MTN); camera.lookAt(V(lx, ly, lz).add(MTN));
}

// =====================================================================
// THE ORGANISER: network of lights, then the Ekta Yatra convoy (x = +3000)
// =====================================================================
const YAT = V(3000, 0, 0);
const yatra = new THREE.Group(); yatra.position.copy(YAT); scene.add(yatra);
const roadCurve = new THREE.CatmullRomCurve3([V(40, 0, 420), V(-30, 0, 300), V(20, 0, 180), V(-40, 0, 60), V(30, 0, -60), V(-20, 0, -180), V(40, 0, -300), V(0, 0, -430)]);
const NODES = [], EDGES = [];
{
  yatra.add(new THREE.Mesh(new THREE.PlaneGeometry(1400, 1400).rotateX(-Math.PI / 2), lam(0x0b0f18)));
  // stars
  const n = 2500, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const th = rand() * 6.28, ph = rand() * 1.4; pos.set([Math.cos(th) * Math.sin(ph) * 800, Math.cos(ph) * 800, Math.sin(th) * Math.sin(ph) * 800], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  yatra.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, sizeAttenuation: false, fog: false })));
  // road ribbon
  const P = 600, verts = [], uvs = [], idx = [];
  for (let i = 0; i <= P; i++) {
    const u = i / P, p = roadCurve.getPointAt(u), tg = roadCurve.getTangentAt(u), side = V(-tg.z, 0, tg.x).normalize().multiplyScalar(4);
    verts.push(p.x - side.x, 0.05, p.z - side.z, p.x + side.x, 0.05, p.z + side.z); uvs.push(0, u * 120, 1, u * 120);
    if (i < P) idx.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
  }
  const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3)); rg.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2)); rg.setIndex(idx);
  yatra.add(new THREE.Mesh(rg, new THREE.ShaderMaterial({ side: THREE.DoubleSide, vertexShader: `varying vec2 vUv; void main(){vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader: `varying vec2 vUv; void main(){vec3 c=vec3(0.08,0.085,0.1); float dash=step(0.5,fract(vUv.y))*step(abs(vUv.x-0.5),0.02); float e=smoothstep(0.06,0.0,vUv.x)+smoothstep(0.94,1.0,vUv.x); c+=dash*vec3(0.9,0.8,0.4)+e*vec3(1.0,0.6,0.2)*0.8; gl_FragColor=vec4(c,1.0);}` })));
  // village nodes for the network
  for (let i = 0; i < 70; i++) NODES.push(V((rand() - 0.5) * 500, 0.5, (rand() - 0.5) * 800));
  NODES.forEach((a, i) => { const near = NODES.map((b, j) => [a.distanceTo(b), j]).filter(([, j]) => j !== i).sort((p, q) => p[0] - q[0]).slice(0, 2); near.forEach(([d, j]) => { if (i < j || d > 160) EDGES.push([i, j, a.distanceTo(V(0, 0, 0))]); }); });
  EDGES.sort((p, q) => p[2] - q[2]);
}
const netPos = new Float32Array(EDGES.length * 6);
EDGES.forEach(([i, j], k) => netPos.set([NODES[i].x, 0.6, NODES[i].z, NODES[j].x, 0.6, NODES[j].z], k * 6));
const netGeo = new THREE.BufferGeometry(); netGeo.setAttribute('position', new THREE.BufferAttribute(netPos, 3));
const netLines = new THREE.LineSegments(netGeo, new THREE.LineBasicMaterial({ color: SAFFRON, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending })); yatra.add(netLines);
const nodePts = new THREE.Points(new THREE.BufferGeometry().setFromPoints(NODES), new THREE.PointsMaterial({ map: SOFT, size: 9, color: 0xffd28a, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); yatra.add(nodePts);
// crowd lamps along the road
const CN = 3000, crowdPos = new Float32Array(CN * 3), crowdU = [];
for (let i = 0; i < CN; i++) { const u = rand(), p = roadCurve.getPointAt(u), tg = roadCurve.getTangentAt(u), sd = (rand() < 0.5 ? -1 : 1) * (6 + rand() * 14); crowdU.push(u); crowdPos.set([p.x - tg.z * sd, 0.8 + rand() * 0.6, p.z + tg.x * sd], i * 3); }
const crowdGeo = new THREE.BufferGeometry(); crowdGeo.setAttribute('position', new THREE.BufferAttribute(crowdPos, 3));
const crowdCol = new Float32Array(CN * 3); crowdGeo.setAttribute('color', new THREE.BufferAttribute(crowdCol, 3));
const crowd = new THREE.Points(crowdGeo, new THREE.PointsMaterial({ map: SOFT, size: 1.6, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); yatra.add(crowd);
// convoy
const VN = 30, convoy = new THREE.InstancedMesh(new THREE.BoxGeometry(2.2, 1.8, 4.4), lam(0xd9d9d9), VN); yatra.add(convoy);
const lightsGeo = new THREE.BufferGeometry(), lightsPos = new Float32Array(VN * 2 * 3), lightsCol = new Float32Array(VN * 2 * 3);
lightsGeo.setAttribute('position', new THREE.BufferAttribute(lightsPos, 3)); lightsGeo.setAttribute('color', new THREE.BufferAttribute(lightsCol, 3));
const vLights = new THREE.Points(lightsGeo, new THREE.PointsMaterial({ map: SOFT, size: 5, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); vLights.frustumCulled = false; yatra.add(vLights);
const rath = new THREE.Sprite(new THREE.SpriteMaterial({ map: SOFT, color: SAFFRON, blending: THREE.AdditiveBlending, depthWrite: false })); rath.scale.set(16, 16, 1); yatra.add(rath);
const placeLabel = (txt, pos) => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(512, 128, (x, w, h) => { x.fillStyle = 'rgba(5,10,25,0.8)'; x.beginPath(); x.roundRect(4, 4, w - 8, h - 8, 20); x.fill(); x.strokeStyle = '#ff9933'; x.lineWidth = 6; x.stroke(); x.fillStyle = '#fff'; x.font = '900 58px "DejaVu Sans", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(txt, w / 2, h / 2 + 3); }), depthTest: false, transparent: true })); s.scale.set(48, 12, 1); s.position.copy(pos); s.renderOrder = 5; yatra.add(s); return s; };
const lblS = placeLabel('KANYAKUMARI', roadCurve.getPointAt(0).add(V(0, 14, 0))), lblN = placeLabel('SRINAGAR', roadCurve.getPointAt(1).add(V(0, 14, 0)));
function S_yatra(lt) {
  yatra.visible = true; scene.background = new THREE.Color(0x05070d);
  // phase 1 (0-16): network of lights grows
  const netK = seg(lt, 1, 14);
  netGeo.setDrawRange(0, Math.floor(EDGES.length * netK) * 2);
  netLines.material.opacity = 0.85 * (1 - seg(lt, 16, 20) * 0.7);
  nodePts.material.opacity = seg(lt, 0, 2);
  // phase 2 (16-40): the convoy travels south -> north, crowds light up as it passes
  const head = clamp((lt - 16) / 22, 0, 1) * 0.97 + 0.015;
  const q = new THREE.Quaternion(), s = V(1, 1, 1), m = new THREE.Matrix4();
  for (let i = 0; i < VN; i++) {
    const u = clamp(head - i * 0.0035, 0.0005, 0.9995), p = roadCurve.getPointAt(u), tg = roadCurve.getTangentAt(u);
    q.setFromUnitVectors(V(0, 0, -1), V(tg.x, 0, tg.z).normalize());
    m.compose(V(p.x, lt < 16 ? -10 : 1.1, p.z), q, s); convoy.setMatrixAt(i, m);
    lightsPos.set([p.x - tg.x * 2.4, 1.2, p.z - tg.z * 2.4, p.x + tg.x * 2.4, 1.2, p.z + tg.z * 2.4], i * 6);
    lightsCol.set(lt < 16 ? [0, 0, 0, 0, 0, 0] : [1, 0.95, 0.8, 0.9, 0.1, 0.05], i * 6);
  }
  convoy.instanceMatrix.needsUpdate = true; lightsGeo.attributes.position.needsUpdate = true; lightsGeo.attributes.color.needsUpdate = true;
  rath.position.copy(roadCurve.getPointAt(head)).add(V(0, 3, 0)); rath.visible = lt >= 16;
  crowdU.forEach((u, i) => { const on = lt >= 16 && u < head + 0.02 ? 1 : 0.08; const tri = i % 3 === 0 ? [1, 0.6, 0.2] : i % 3 === 1 ? [1, 1, 1] : [0.1, 0.7, 0.2]; crowdCol.set(tri.map(c => c * on), i * 3); });
  crowdGeo.attributes.color.needsUpdate = true;
  lblS.material.opacity = lblN.material.opacity = seg(lt, 16, 18);
  if (lt < 16) camPath([[0, [0, 700, 300], [0, 0, 0]], [16, [0, 420, 380], [0, 0, -40]]], lt);
  else if (lt < 32) {
    const p = roadCurve.getPointAt(head), tg = roadCurve.getTangentAt(head);
    camera.position.set(p.x - tg.x * 40 + 16, 18, p.z - tg.z * 40); camera.lookAt(p.x + tg.x * 30, 2, p.z + tg.z * 30);
  } else camPath([[32, [60, 60, -260], [0, 0, -380]], [40, [140, 520, 120], [0, 0, -20]]], lt);
  camera.position.add(YAT); const d = new THREE.Vector3(); camera.getWorldDirection(d); camera.lookAt(camera.position.clone().add(d));
}

// =====================================================================
// CITY: earthquake -> rebuild (x = -3000)
// =====================================================================
const CTY = V(-3000, 0, 0);
const city = new THREE.Group(); city.position.copy(CTY); scene.add(city);
const citySky = skyDome(city, 0x0a1430, 0x2a2440);
const BLD = [];
const bldMesh = (() => {
  const tex = canvasTex(256, 512, (x, w, h) => { x.fillStyle = '#20242c'; x.fillRect(0, 0, w, h); for (let r = 0; r < 32; r++) for (let c = 0; c < 8; c++) { const on = Math.random() < 0.55; x.fillStyle = on ? `hsl(${38 + Math.random() * 12},90%,${60 + Math.random() * 25}%)` : '#2c323d'; x.fillRect(8 + c * 31, 8 + r * 15.7, 20, 9); } });
  const mat = new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: 0.9, roughness: 0.7 });
  const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0), mat, 1100);
  let n = 0;
  for (let gx = -16; gx <= 16; gx++) for (let gz = -16; gz <= 16; gz++) {
    if (gx % 4 === 0 || gz % 4 === 0 || Math.abs(gx + 3) < 1.5 || n >= 1100) continue; // roads + river corridor
    const d = Math.hypot(gx, gz), h = 4 + Math.pow(rand(), 2.2) * 55 * Math.exp(-d / 10) + rand() * 6;
    BLD.push({ x: gx * 9, z: gz * 9, w: 5 + rand() * 2.5, d: 5 + rand() * 2.5, h, delay: d * 0.35 + rand() * 2 });
    n++;
  }
  mesh.count = BLD.length; city.add(mesh); return mesh;
})();
{
  city.add(new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200).rotateX(-Math.PI / 2), lam(0x1a1d22)));
  const river = new THREE.Mesh(new THREE.PlaneGeometry(14, 1200).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x1b3a5a, metalness: 0.9, roughness: 0.15, emissive: 0x0a1a2a })); river.position.set(-27, 0.05, 0); city.add(river);
  const streetTex = canvasTex(64, 64, (x) => { x.fillStyle = '#000'; x.fillRect(0, 0, 64, 64); x.fillStyle = '#ffb347'; x.fillRect(30, 0, 4, 64); });
  void streetTex;
}
const cityHemi = new THREE.HemisphereLight(0x8fa8d8, 0x202030, 0.6); city.add(cityHemi);
const citySun = new THREE.DirectionalLight(0xffd2a0, 0); citySun.position.set(-200, 120, 150); city.add(citySun, citySun.target);
function S_city(lt) {
  city.visible = true; scene.background = new THREE.Color(0x0a1430);
  const dawn = seg(lt, 32, 45), dim = seg(lt, 17, 19) * (1 - seg(lt, 32, 35));
  citySky.uTop.value.setRGB(lerp(0.04, 0.3, dawn), lerp(0.08, 0.5, dawn), lerp(0.19, 0.85, dawn));
  citySky.uBot.value.setRGB(lerp(0.16, 1.0, dawn), lerp(0.14, 0.7, dawn), lerp(0.25, 0.45, dawn));
  citySun.intensity = dawn * 1.8; cityHemi.intensity = 0.6 + dawn * 0.6;
  bldMesh.material.emissiveIntensity = 0.9 * (1 - dim * 0.75) * (1 - dawn * 0.5);
  renderer.toneMappingExposure = 1 - dim * 0.35;
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), pp = new THREE.Vector3(), ss = new THREE.Vector3();
  BLD.forEach((b, i) => {
    const quake = lt < 6 ? (1 - seg(lt, 0.5, 5)) : 0; // standing -> collapse
    const rebuild = ease(seg(lt, 9 + b.delay, 15 + b.delay));
    const h = lt < 6 ? b.h * (0.35 + 0.65 * quake) : Math.max(0.6, b.h * rebuild);
    const tilt = lt < 6 ? Math.sin(i * 1.7) * 0.12 * (1 - quake) : 0;
    q.setFromEuler(new THREE.Euler(tilt, 0, tilt * 0.6));
    m.compose(pp.set(b.x, 0, b.z), q, ss.set(b.w, h, b.d)); bldMesh.setMatrixAt(i, m);
  });
  bldMesh.instanceMatrix.needsUpdate = true;
  const a = lt * 0.06 + 0.6, r = 170 - seg(lt, 0, 45) * 50;
  camera.position.set(Math.cos(a) * r, 70 - seg(lt, 20, 45) * 35, Math.sin(a) * r); camera.lookAt(0, 12, 0);
  const shake = lt < 6 ? (1 - seg(lt, 3, 6)) * 1.6 : 0;
  camera.position.add(V(Math.sin(lt * 53) * shake, Math.sin(lt * 61) * shake, Math.cos(lt * 47) * shake)).add(CTY);
  const d = new THREE.Vector3(); camera.getWorldDirection(d);
  camera.lookAt(CTY.clone().add(V(0, 12, 0)));
}

// =====================================================================
// PARLIAMENT-STYLE CIRCULAR BUILDING + FIREWORKS (x = +6000)
// =====================================================================
const DEL = V(6000, 0, 0);
const delhi = new THREE.Group(); delhi.position.copy(DEL); scene.add(delhi);
const delSky = skyDome(delhi, 0x070b1c, 0x1c1830);
{
  delhi.add(new THREE.Mesh(new THREE.PlaneGeometry(1600, 1600).rotateX(-Math.PI / 2), lam(0x1f3a1f)));
  const stone = new THREE.MeshStandardMaterial({ color: 0xe9d8b8, roughness: 0.8 });
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(38, 38, 9, 96, 1, true), stone); wall.position.y = 5.5; delhi.add(wall);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(46, 47, 1.2, 96), stone); base.position.y = 0.6; delhi.add(base);
  const cols = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.45, 0.5, 8.4, 10), stone, 144), m = new THREE.Matrix4();
  for (let i = 0; i < 144; i++) { const a = i / 144 * Math.PI * 2; m.makeTranslation(Math.cos(a) * 43, 5.4, Math.sin(a) * 43); cols.setMatrixAt(i, m); } delhi.add(cols);
  const ent = new THREE.Mesh(new THREE.TorusGeometry(43, 0.8, 6, 96), stone); ent.rotation.x = Math.PI / 2; ent.position.y = 9.9; delhi.add(ent);
  const roof = new THREE.Mesh(new THREE.CylinderGeometry(44, 44, 0.6, 96), stone); roof.position.y = 10.2; delhi.add(roof);
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(16, 16, 6, 64), stone); drum.position.y = 13.4; delhi.add(drum);
  const dome = new THREE.Mesh(new THREE.SphereGeometry(16, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), stone); dome.scale.y = 0.45; dome.position.y = 16.4; delhi.add(dome);
  const path = new THREE.Mesh(new THREE.PlaneGeometry(10, 400).rotateX(-Math.PI / 2), lam(0xc9b48a)); path.position.set(0, 0.03, 240); delhi.add(path);
  delhi.add(new THREE.HemisphereLight(0x8090c0, 0x203020, 0.45));
  [[SAFFRON, -70, 40], [WHITE, 0, 80], [GREEN, 70, 40]].forEach(([c, x, z]) => { const l = new THREE.PointLight(c, c === GREEN ? 3500 : 6000, 260, 2); l.position.set(x, 18, z); delhi.add(l); });
  [[SAFFRON, -70, -40], [WHITE, 0, -80], [GREEN, 70, -40]].forEach(([c, x, z]) => { const l = new THREE.PointLight(c, c === GREEN ? 2500 : 4000, 260, 2); l.position.set(x, 18, z); delhi.add(l); });
}
const FW = [], FWN = 260;
const FWT = [1, 2.2, 3.1, 4.4, 5.2, 6.8, 7.5, 8.9, 10.2, 11, 12.6, 13.4, 15, 16.2, 17.7, 19, 20.4, 22, 23.1, 24.8, 26, 27.5, 29, 30.6, 32, 33.3, 35, 36.4, 38, 39.5, 41, 42.5, 44, 46, 48, 50, 52, 54];
FWT.forEach((t, i) => { const r = mkRng(i + 900); FW.push({ t, o: V((r() - 0.5) * 160, 70 + r() * 50, -40 + (r() - 0.5) * 120), col: new THREE.Color([SAFFRON, WHITE, GREEN][i % 3]), sp: 14 + r() * 10, dirs: [...Array(FWN)].map(() => V(r() - 0.5, r() - 0.5, r() - 0.5).normalize().multiplyScalar(0.6 + r() * 0.4)) }); });
const fwPos = new Float32Array(FWT.length * FWN * 3), fwCol = new Float32Array(FWT.length * FWN * 3);
const fwGeo = new THREE.BufferGeometry(); fwGeo.setAttribute('position', new THREE.BufferAttribute(fwPos, 3)); fwGeo.setAttribute('color', new THREE.BufferAttribute(fwCol, 3));
const fireworks = new THREE.Points(fwGeo, new THREE.PointsMaterial({ map: SOFT, size: 5, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); fireworks.frustumCulled = false; delhi.add(fireworks);
function S_delhi(lt, { fw = 1, night = 1 } = {}) {
  delhi.visible = true; scene.background = new THREE.Color(0x070b1c);
  let k = 0;
  FW.forEach((f) => {
    const dt = lt - f.t, alive = fw && dt > 0 && dt < 3.2;
    f.dirs.forEach((d) => {
      if (alive) { const g = 0.5 * 9 * dt * dt * 0.35; fwPos.set([f.o.x + d.x * f.sp * dt, f.o.y + d.y * f.sp * dt - g, f.o.z + d.z * f.sp * dt], k * 3); const a = Math.pow(1 - dt / 3.2, 1.5) * (dt < 0.1 ? dt * 10 : 1); fwCol.set([f.col.r * a, f.col.g * a, f.col.b * a], k * 3); }
      else { fwCol.set([0, 0, 0], k * 3); }
      k++;
    });
  });
  fwGeo.attributes.position.needsUpdate = true; fwGeo.attributes.color.needsUpdate = true;
  const a = 1.2 + lt * 0.05, r = 150 - seg(lt, 0, 40) * 40;
  camera.position.set(Math.sin(a) * r, 32 + Math.sin(lt * 0.15) * 10, Math.cos(a) * r).add(DEL);
  camera.lookAt(DEL.clone().add(V(0, 34, 0)));
  void night;
}

// =====================================================================
// MOON LANDING (x = -6000)
// =====================================================================
const MOON = V(-6000, 0, 0);
const moon = new THREE.Group(); moon.position.copy(MOON); scene.add(moon);
const CRATERS = [...Array(70)].map(() => [(rand() - 0.5) * 700, (rand() - 0.5) * 700, 4 + Math.pow(rand(), 3) * 60]);
function moonH(x, z) {
  let h = fbm2(x * 0.02 + 50, z * 0.02) * 6 - 3;
  CRATERS.forEach(([cx, cz, r]) => { if (Math.hypot(cx, cz) < 25) return; const d = Math.hypot(x - cx, z - cz) / r; if (d < 1.4) h += d < 1 ? (d * d - 1) * r * 0.25 : Math.exp(-((d - 1.05) ** 2) * 40) * r * 0.08; });
  return h;
}
{
  const g = new THREE.PlaneGeometry(800, 800, 260, 260).rotateX(-Math.PI / 2), p = g.attributes.position;
  for (let i = 0; i < p.count; i++) p.setY(i, moonH(p.getX(i), p.getZ(i)));
  g.computeVertexNormals();
  moon.add(new THREE.Mesh(g, lam(0x9b9b9b)));
  const sunM = new THREE.DirectionalLight(0xffffff, 2.6); sunM.position.set(300, 60, 100); moon.add(sunM, sunM.target);
  moon.add(new THREE.AmbientLight(0x404858, 0.25));
  const n = 3000, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const th = rand() * 6.28, ph = rand() * 1.45; pos.set([Math.cos(th) * Math.sin(ph) * 900, Math.cos(ph) * 900, Math.sin(th) * Math.sin(ph) * 900], i * 3); }
  const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  moon.add(new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xffffff, size: 1.1, sizeAttenuation: false })));
  const earth = new THREE.Mesh(planet.geometry, planet.material); earth.scale.setScalar(3.2); earth.position.set(-260, 150, -520); moon.add(earth);
  const eatmo = new THREE.Mesh(atmo.geometry, atmo.material); eatmo.scale.setScalar(3.2); eatmo.position.copy(earth.position); moon.add(eatmo);
}
const lander = new THREE.Group(); moon.add(lander);
{
  const gold = new THREE.MeshStandardMaterial({ color: 0xd4a017, metalness: 0.85, roughness: 0.35 }), silver = new THREE.MeshStandardMaterial({ color: 0xcfd3d8, metalness: 0.9, roughness: 0.25 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(2.6, 1.6, 2.6), gold); body.position.y = 1.9; lander.add(body);
  const top = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.6, 1.6), silver); top.position.y = 3.0; lander.add(top);
  const panel = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.05, 1.2), new THREE.MeshStandardMaterial({ color: 0x1a2a6a, metalness: 0.6, roughness: 0.3 })); panel.position.set(0, 2.4, 1.9); panel.rotation.x = -0.5; lander.add(panel);
  [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([sx, sz]) => {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.8, 6), silver); leg.position.set(sx * 1.55, 0.95, sz * 1.55); leg.rotation.set(sz * 0.4, 0, -sx * 0.4); lander.add(leg);
    const pad = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.32, 0.08, 12), silver); pad.position.set(sx * 1.9, 0.05, sz * 1.9); lander.add(pad);
  });
}
const thrust = new THREE.Sprite(new THREE.SpriteMaterial({ map: SOFT, color: 0xffd0a0, blending: THREE.AdditiveBlending, depthWrite: false })); thrust.scale.set(3, 5, 1); moon.add(thrust);
const rover = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.4, 0.7), new THREE.MeshStandardMaterial({ color: 0xd8d8d8, metalness: 0.7, roughness: 0.3 })); moon.add(rover);
const DN = 900, dustPos = new Float32Array(DN * 3), dustInfo = [];
for (let i = 0; i < DN; i++) dustInfo.push([rand() * 6.28, 2 + rand() * 9, 0.5 + rand() * 2.5]);
const dustGeo = new THREE.BufferGeometry(); dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
const dustMat = new THREE.PointsMaterial({ map: SOFT, size: 0.7, color: 0xb5b0a5, transparent: true, opacity: 0, depthWrite: false }); const dust = new THREE.Points(dustGeo, dustMat); dust.frustumCulled = false; moon.add(dust);
function S_moon(lt) {
  moon.visible = true; scene.background = new THREE.Color(0x000000);
  PU.uTime.value = lt; sunDir.set(0.6, 0.2, 0.8).normalize();
  const TD = 9; // touchdown time
  const k = seg(lt, 0, TD), y = lt < TD ? lerp(55, 0, 1 - Math.pow(1 - k, 2.2)) : 0;
  lander.position.set(Math.sin(lt * 0.3) * (1 - k) * 4, y, 0);
  thrust.position.set(lander.position.x, y - 0.4, 0); thrust.material.opacity = lt < TD + 0.4 ? 0.9 : 0; thrust.scale.set(3, 4 + Math.sin(lt * 40) * 0.8, 1);
  const dd = lt - (TD - 1.2);
  dustMat.opacity = dd > 0 ? Math.max(0, 0.7 * (1 - dd / 6)) : 0;
  dustInfo.forEach(([a, sp, h], i) => { const r = dd > 0 ? Math.min(40, sp * dd) : 0; dustPos.set([Math.cos(a) * r, Math.min(h, r * 0.15) * (dd > 0 ? 1 : 0), Math.sin(a) * r], i * 3); });
  dustGeo.attributes.position.needsUpdate = true;
  const rk = ease(seg(lt, TD + 3, TD + 8)); rover.position.set(1.4 + rk * 6, 0.25 + (1 - rk) * 1.4 * (rk < 0.25 ? 1 : 0), 1.5 + rk * 2); rover.visible = lt > TD + 2.5;
  camPath([[0, [22, 50, 30], [0, 40, 0]], [TD, [14, 6, 16], [0, 2, 0]], [TD + 4, [10, 3, 12], [2, 1, 1]], [14, [-24, 10, 34], [0, 6, -40]]], lt);
  camera.position.add(MOON); const d = new THREE.Vector3(); camera.getWorldDirection(d); camera.lookAt(camera.position.clone().add(d));
}

// =====================================================================
// GLOBE: arcs to New Delhi + tricolor rings
// =====================================================================
const DELHI_LL = [28.6, 77.2];
const CAPS = [[38.9, -77], [45.4, -75.7], [19.4, -99.1], [-15.8, -47.9], [-34.6, -58.4], [51.5, -0.1], [48.9, 2.35], [52.5, 13.4], [41.9, 12.5], [55.7, 37.6], [39.9, 32.9], [24.7, 46.7], [-25.7, 28.2], [39.9, 116.4], [35.7, 139.7], [37.6, 127], [-6.2, 106.8], [-35.3, 149.1], [50.8, 4.4], [9.0, 38.7]];
const arcs = new THREE.Group(); planet.add(arcs);
const ARC = CAPS.map(([la, lo], i) => {
  const a = latLon(la, lo, 10.05), b = latLon(...DELHI_LL, 10.05), mid = a.clone().add(b).multiplyScalar(0.5), h = 10.05 + a.distanceTo(b) * 0.35;
  const curve = new THREE.QuadraticBezierCurve3(a, mid.normalize().multiplyScalar(h), b);
  const g = new THREE.BufferGeometry().setFromPoints(curve.getPoints(80));
  const l = new THREE.Line(g, new THREE.LineBasicMaterial({ color: [SAFFRON, WHITE, GREEN][i % 3], transparent: true, blending: THREE.AdditiveBlending })); arcs.add(l); return l;
});
const beacon = new THREE.Sprite(new THREE.SpriteMaterial({ map: SOFT, color: SAFFRON, blending: THREE.AdditiveBlending, depthWrite: false })); beacon.position.copy(latLon(...DELHI_LL, 10.2)); beacon.scale.set(1.6, 1.6, 1); planet.add(beacon);
const indiaRot = (() => { const d = latLon(...DELHI_LL, 1); return Math.atan2(-d.x, d.z); })();
const RINGN = 1800, ringPos = new Float32Array(RINGN * 3), ringCol = new Float32Array(RINGN * 3);
const ringGeo = new THREE.BufferGeometry(); ringGeo.setAttribute('position', new THREE.BufferAttribute(ringPos, 3)); ringGeo.setAttribute('color', new THREE.BufferAttribute(ringCol, 3));
const rings = new THREE.Points(ringGeo, new THREE.PointsMaterial({ map: SOFT, size: 0.32, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); space.add(rings);
function S_globe(lt, { arcsK = 0, ringK = 0, beaconK = 1 } = {}) {
  setSpace(lt, { rot: indiaRot + Math.sin(lt * 0.08) * 0.25, clouds: 0.25 });
  arcs.visible = arcsK > 0; ARC.forEach((l, i) => { const k = clamp(arcsK * 1.6 - i * 0.03, 0, 1); l.geometry.setDrawRange(0, Math.floor(81 * k)); l.material.opacity = k; });
  beacon.visible = beaconK > 0; beacon.scale.setScalar(1.4 + Math.sin(lt * 4) * 0.3);
  rings.visible = ringK > 0;
  if (ringK > 0) {
    const cols = [[1, 0.6, 0.2], [1, 1, 1], [0.07, 0.6, 0.1]];
    for (let i = 0; i < RINGN; i++) {
      const band = i % 3, a = i / RINGN * Math.PI * 2 * 3 + lt * (0.25 + band * 0.04), r = 13 + band * 0.9;
      const tilt = 0.35 + band * 0.12;
      ringPos.set([Math.cos(a) * r, Math.sin(a) * r * Math.sin(tilt) + (band - 1) * 0.5, Math.sin(a) * r * Math.cos(tilt)], i * 3);
      const c = cols[band]; ringCol.set(c.map(x => x * ringK), i * 3);
    }
    ringGeo.attributes.position.needsUpdate = true; ringGeo.attributes.color.needsUpdate = true;
  }
}

// =====================================================================
// TIMELINE (310 s) + overlays
// =====================================================================
const DURATION = 310;
const groupsAll = [space, mountains, village, yatra, city, delhi, moon];
function resetAll() {
  reset(); groupsAll.forEach(g => g.visible = false);
  arcs.visible = false; beacon.visible = false; rings.visible = false;
}
let YEAR = '';
const FNM = {
  village: S_village, himalaya: S_himalaya, yatra: S_yatra, city: S_city, delhi: S_delhi, moon: S_moon,
  globe: (lt) => { S_globe(lt, { arcsK: seg(lt, 2, 12), ringK: 0 }); camPath([[0, [0, 6, 40], [0, 2, 0]], [25, [6, 9, 30], [0, 3, 0]]], lt); },
};
const CHM = [
  { id: 'hook', a: 0, b: 15 },
  { id: 'intro', a: 15, b: 32, next: 'A boy from Vadnagar' },
  { id: 'ch1', a: 32, b: 75, n: 1, title: 'A BOY FROM VADNAGAR', next: 'The wandering years' },
  { id: 'ch2', a: 75, b: 100, n: 2, title: 'THE WANDERING YEARS', next: 'The organiser' },
  { id: 'ch3', a: 100, b: 140, n: 3, title: 'THE ORGANISER', next: '' },
  { id: 'mid', a: 140, b: 150 },
  { id: 'ch4', a: 150, b: 195, n: 4, title: 'CHIEF MINISTER OF GUJARAT', next: 'Prime Minister' },
  { id: 'ch5', a: 195, b: 235, n: 5, title: 'PRIME MINISTER', next: 'The world stage' },
  { id: 'ch6', a: 235, b: 285, n: 6, title: 'THE WORLD STAGE', next: '' },
  { id: 'outro', a: 285, b: 310 },
];
const CHAP = {
  hook(lt) {
    if (lt < 4) FNM.village(22 + lt); else if (lt < 7) FNM.city(12 + lt); else if (lt < 10) FNM.delhi(6 + lt); else if (lt < 12.5) FNM.moon(6 + lt); else { S_globe(lt, { arcsK: 1, ringK: seg(lt, 12.5, 14) }); camPath([[12.5, [0, 8, 46], [0, 0, 0]], [15, [0, 4, 34], [0, 1, 0]]], lt); }
    [4, 7, 10, 12.5].forEach(c => { const d = lt - c; if (d >= 0 && d < 0.25) FLASH2D = Math.max(FLASH2D, 0.8 * (1 - d / 0.25)); });
    say(() => {
      popTxt('A TEA STALL. A RAILWAY STATION.', lt, 0.3, 4, 120, 50, '#fff');
      popTxt('THE WORLD\'S LARGEST DEMOCRACY', lt, 5.2, 10, 120, 54, '#ffb366');
      popTxt('THE MODI STORY', lt, 10.2, 15, 300, 96, '#fff');
      popTxt('Watch till the end', lt, 12.2, 15, 400, 40, '#fde68a');
    });
  },
  intro(lt) {
    S_globe(lt, { arcsK: 0, ringK: seg(lt, 0, 3) }); camPath([[0, [0, 4, 34], [0, 1, 0]], [17, [8, 6, 30], [0, 2, 0]]], lt);
    say(() => {
      popTxt('THE MODI STORY', lt, 0.3, 8, 250, 100, '#fff');
      popTxt('From Vadnagar to New Delhi', lt, 1, 8, 350, 40, '#ffb366');
      const list = ['1  A boy from Vadnagar', '2  The wandering years', '3  The organiser', '4  Chief Minister', '5  Prime Minister', '6  The world stage'];
      const k = win(lt, 8.5, 16.5, 0.4);
      if (k > 0) { box(410, 160, 460, 330, 0.65 * k); txt('THE JOURNEY', 640, 200, 30, '#ffb366', k, 'center', '800'); }
      list.forEach((s, i) => txt(s, 460, 255 + i * 46, 29, i === 5 ? '#86efac' : '#fff', win(lt, 9 + i * 0.35, 16.5, 0.3), 'left', '800'));
    });
  },
  ch1(lt) { FNM.village(lt); YEAR = lt < 25 ? '1950' : '1958'; },
  ch2(lt) { FNM.himalaya(lt); YEAR = lt < 17 ? '1968' : '1971'; },
  ch3(lt) { FNM.yatra(lt); YEAR = lt < 10 ? '1972' : lt < 16 ? '1987' : lt < 33 ? '1991' : '1998'; },
  mid(lt) {
    if (lt < 5) FNM.delhi(10 + lt); else FNM.moon(lt - 5);
    const d = lt - 5; if (d >= 0 && d < 0.25) FLASH2D = Math.max(FLASH2D, 0.8 * (1 - d / 0.25));
    say(() => { popTxt('HALFWAY THERE', lt, 0.2, 5, 300, 92, '#fff'); popTxt('Coming up: power, controversy and the Moon', lt, 5.2, 10, 330, 42, '#ffb366'); });
  },
  ch4(lt) { FNM.city(lt); YEAR = lt < 10 ? '2001' : lt < 33 ? '2002' : '2001–2014'; },
  ch5(lt) {
    S_delhi(lt); YEAR = lt < 18 ? '2014' : lt < 30 ? '2014–2016' : '2017';
    say(() => {
      const k = win(lt, 4, 15, 0.4); if (k > 0) {
        const n = Math.round(282 * ease(seg(lt, 4.3, 7.5)));
        box(860, 40, 380, 140, 0.65 * k);
        txt(`${n}`, 1050, 110, 76, '#ffb366', k); txt('BJP SEATS IN 2014 (272 = MAJORITY)', 1050, 175, 17, '#e2e8f0', k, 'center', '700');
      }
      ['CLEAN INDIA', 'JAN DHAN', 'MAKE IN INDIA', 'DIGITAL INDIA'].forEach((s, i) => { const kk = win(lt, 18 + i * 0.7, 25, 0.3); if (kk > 0) { box(80 + i * 290, 60, 260, 40, 0.6 * kk); txt(s, 210 + i * 290, 100, 26, ['#ffb366', '#fff', '#86efac', '#7dd3fc'][i], kk, 'center', '800'); } });
      popTxt('2016: Rs 500 and Rs 1000 notes withdrawn', lt, 25.5, 32.5, 175, 38, '#fde68a');
      popTxt('2017: Goods and Services Tax', lt, 33, 39, 175, 40, '#86efac');
    });
  },
  ch6(lt) {
    if (lt < 15) { S_delhi(lt + 20); YEAR = lt < 9 ? '2019' : '2021'; }
    else if (lt < 29) { FNM.moon(lt - 15); YEAR = '2023'; }
    else { S_globe(lt, { arcsK: seg(lt, 29, 34), ringK: seg(lt, 35, 40) }); camPath([[29, [0, 6, 44], [0, 2, 0]], [50, [0, 4, 30], [0, 1, 0]]], lt); YEAR = lt < 35 ? '2023' : '2024'; }
    [15, 29].forEach(c => { const d = lt - c; if (d >= 0 && d < 0.25) FLASH2D = Math.max(FLASH2D, 0.6 * (1 - d / 0.25)); });
    say(() => {
      const k = win(lt, 4, 9, 0.3); if (k > 0) { box(860, 40, 380, 140, 0.65 * k); txt(`${Math.round(303 * ease(seg(lt, 4.2, 6.5)))}`, 1050, 110, 76, '#ffb366', k); txt('BJP SEATS IN 2019', 1050, 175, 17, '#e2e8f0', k, 'center', '700'); }
      popTxt('2+ BILLION VACCINE DOSES', lt, 14 - 5, 15, 175, 44, '#86efac');
      popTxt('23 AUGUST 2023 · 18:04 IST', lt, 24, 28.8, 175, 40, '#fff');
      popTxt('G20 SUMMIT · NEW DELHI', lt, 29.5, 34.5, 175, 44, '#ffb366');
      const k2 = win(lt, 36, 49, 0.4); if (k2 > 0) { box(820, 40, 420, 150, 0.65 * k2); txt('THIRD TERM · 2024', 1030, 85, 28, '#fff', k2, 'center', '800'); txt('BJP 240  ·  NDA 293', 1030, 140, 40, '#ffb366', k2, 'center', '900'); txt('272 needed for majority', 1030, 185, 17, '#e2e8f0', k2, 'center', '600'); }
    });
  },
  outro(lt) {
    S_globe(lt + 50, { arcsK: 1, ringK: 1 }); camPath([[0, [0, 4, 30], [0, 1, 0]], [25, [0, 22, 92], [0, 0, 0]]], lt);
    say(() => {
      popTxt('From a tea stall to the world stage', lt, 0.4, 9, 250, 52, '#fff');
      popTxt('Whose story should we tell next?', lt, 9.5, 24, 230, 52, '#fff');
      popTxt('Tell us in the comments', lt, 10.5, 24, 310, 38, '#ffb366');
      popTxt('SUBSCRIBE for the next story', lt, 14, 24, 400, 42, '#86efac');
    });
  },
};
// narration captions (loaded from modi-narration.json: [{t, text, d}])
let CAPS_LINES = [];
function captions(t) {
  const l = CAPS_LINES.find(l => t >= l.t && t < l.t + (l.d || 3) + 0.2); if (!l) return;
  const k = Math.min(1, (t - l.t) / 0.15, (l.t + (l.d || 3) + 0.2 - t) / 0.15);
  ctx.save(); ctx.font = '700 30px "DejaVu Sans", sans-serif';
  const words = l.text.split(' '), linesOut = []; let cur = '';
  words.forEach(w => { const tryS = cur ? cur + ' ' + w : w; if (ctx.measureText(tryS).width > 1000) { linesOut.push(cur); cur = w; } else cur = tryS; }); linesOut.push(cur);
  const h = linesOut.length * 40 + 20, y0 = 690 - h;
  ctx.globalAlpha = 0.6 * k; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.roundRect(1280 / 2 - 530, y0, 1060, h, 12); ctx.fill(); ctx.restore();
  linesOut.forEach((s, i) => txt(s, 640, y0 + 30 + i * 40, 30, '#fff', k, 'center', '700'));
}
function chapterOverlayM(c, lt) {
  if (c.title) say(() => {
    const k = win(lt, 0.3, 3.8, 0.4); if (k <= 0) return;
    txt(`CHAPTER ${c.n}`, 640, 280, 30, '#ffb366', k, 'center', '800');
    ctx.save(); ctx.globalAlpha = k; const w = 300 * ease(seg(lt, 0.3, 1.1));
    ctx.fillStyle = '#ff9933'; ctx.fillRect(640 - w / 2, 308, w / 3, 4); ctx.fillStyle = '#fff'; ctx.fillRect(640 - w / 6, 308, w / 3, 4); ctx.fillStyle = '#138808'; ctx.fillRect(640 + w / 6, 308, w / 3, 4); ctx.restore();
    txt(c.title, 640, 360, 60, '#fff', k);
  });
  if (c.next) say(() => {
    const L = c.b - c.a, k = win(lt, L - 6, L - 0.8, 0.5); if (k <= 0) return;
    const x = lerp(1300, 880, ease(seg(lt, L - 6, L - 5.4)));
    ctx.save(); ctx.globalAlpha = 0.7 * k; ctx.fillStyle = '#050a19'; ctx.beginPath(); ctx.roundRect(x, 40, 360, 86, 14); ctx.fill(); ctx.restore();
    txt('NEXT UP', x + 22, 66, 19, '#ffb366', k, 'left', '800'); txt(c.next, x + 22, 100, 25, '#fff', k, 'left', '800', 320);
  });
  if (YEAR && c.n) say(() => { const k = seg(lt, 3.6, 4.2); box(36, 36, 210, 52, 0.6 * k); txt(YEAR, 141, 82, YEAR.length > 6 ? 30 : 44, '#fff', k, 'center', '900'); });
}
function progressBarM(t) {
  const y = 708; ctx.save(); ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.fillRect(0, y, 1280, 6);
  const g = ctx.createLinearGradient(0, 0, 1280, 0); g.addColorStop(0, '#ff9933'); g.addColorStop(0.5, '#ffffff'); g.addColorStop(1, '#138808');
  ctx.fillStyle = g; ctx.fillRect(0, y, 1280 * t / DURATION, 6); ctx.fillStyle = 'rgba(255,255,255,0.85)';
  CHM.forEach(c => { if (c.a > 0) ctx.fillRect(1280 * c.a / DURATION - 1, y, 2, 6); }); ctx.restore();
}
window.renderFrame = (t) => {
  t = clamp(t, 0, DURATION - 1e-3);
  const c = CHM.find(c => t >= c.a && t < c.b), lt = t - c.a;
  OV = []; FLASH2D = 0; YEAR = '';
  resetAll();
  CHAP[c.id](lt);
  chapterOverlayM(c, lt);
  renderer.render(scene, camera);
  ctx.globalAlpha = 1; ctx.drawImage(renderer.domElement, 0, 0, W, H);
  const vg = ctx.createRadialGradient(640, 360, 300, 640, 360, 800); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.45)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  if (FLASH2D > 0) { ctx.fillStyle = `rgba(255,244,230,${FLASH2D})`; ctx.fillRect(0, 0, W, H); }
  const fade = Math.min(seg(t, c.a, c.a + 0.5), 1 - seg(t, c.b - 0.5, c.b));
  const fadeA = (c.a === 0 ? 1 : fade) * (c.b === DURATION ? Math.min(1, (DURATION - t) / 1.5) : 1);
  if (fadeA < 1) { ctx.fillStyle = `rgba(0,0,0,${1 - fadeA})`; ctx.fillRect(0, 0, W, H); }
  OV.forEach(f => f());
  captions(t);
  if (t > 15) progressBarM(t);
};
window.DURATION = DURATION;
fetch('modi-narration.json').then(r => r.ok ? r.json() : []).catch(() => []).then(j => { CAPS_LINES = j; window.ready = true; });
const qm = new URLSearchParams(location.search);
if (!qm.has('capture')) {
  const start = performance.now(), off = Number(qm.get('t') || 0);
  (function loop() { if (window.ready) renderFrame((off + (performance.now() - start) / 1000) % DURATION); requestAnimationFrame(loop); })();
}
