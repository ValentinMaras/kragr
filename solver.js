// kragr·solver v0.11.31 — Rechenkern von „Schnittkräfte“ (calc.html)
// Reine Rechenfunktionen ohne Zugriff auf die Seite: Eingabe als Daten, Ergebnis als Daten.
// calc.html liest die Eingaben, ruft den Kern und zeichnet. Die Tests laden diese Datei direkt.
//
// Schnittstellen (alle auch als KragrSolver.<name>):
//   lineSolve(L, cfg, NP)        — Stabzug auf einer Achse (Einfeldträger, Kragarm, Durchlaufträger)
//   frameSolve(inp)              — Rahmen (gerader Riegel oder Satteldach) komplett: Modell, Lösung, Abtastung, Lagerkräfte
//   frameIndeterminacyOf(inp)    — Grad der statischen Unbestimmtheit des Rahmens
//   frameBuildModel / frameSolveDSM / frameSampleForces / frameSampleFine — die einzelnen Schritte
//   lcRules / lcCombine (mit lcOptions, lcFac, lcAt, lcSample) — Lastfälle und Kombinationen nach EN 1990 bzw. Land
// Einheiten: m, kN, kNm, EI in kNm². Vorzeichen siehe Kopf des Rahmenteils.
// Optionaler globaler Faktor LF_SETF (Lastfallüberlagerung: Setzungen gehören zu G) wird gelesen, wenn vorhanden.

// ── Satteldach: Geometrie des Riegels ──
function frameGableOf(b, hA, hB, on, f, xF){
  if(!on || !(f>0)) return null;
  if(!isFinite(xF)) xF = b/2;
  xF = Math.min(Math.max(xF, 0.05*b), 0.95*b);
  return { xF, f, yF: hA+(hB-hA)*xF/b+f, tF: xF/b };
}

// Höhe des Riegels über dem Fuß an der Stelle x (waagerecht)
function frameRafY(x, b, hA, hB, g){
  if(!g) return hA+(hB-hA)*x/b;
  return x<=g.xF ? hA+(g.yF-hA)*x/g.xF : g.yF+(hB-g.yF)*(x-g.xF)/(b-g.xF);
}

// Länge des Riegels (Polygonzug)
function frameRafLen(b, hA, hB, g){ return g ? Math.hypot(g.xF, g.yF-hA)+Math.hypot(b-g.xF, hB-g.yF) : Math.hypot(b, hB-hA); }

function supportDOF(s){ return s==='fixed'?3:s==='pin'?2:1; }

// Temperaturlasten → Anfangsdehnung ε₀ = α_T·ΔT, Anfangskrümmung κ₀ = α_T·ΔT_M/h (ΔT_M = T_u − T_o bzw. innen − außen), EA aus A (0 = dehnstarr)
function tempRows(list, Eof){
  return (list||[]).filter(l=>l && l.enabled!==false).map(l=>{ const v=l.values, a=(+v.alpha||1.2)*1e-5, h=Math.max(+v.h||30, 0.1)/100;
    return {eps0:a*(+v.dTN||0), kap0:a*(+v.dTM||0)/h, EA:(+v.A>0 ? Eof(v.member)*(+v.A)*100 : 0), member:v.member}; });
}


// ╔══════════════════════════════════════════════════════════════════╗
// ║  STATIQ · FRAME CALCULATOR (v0.7 – einheitlicher Solver)          ║
// ║                                                                   ║
// ║  Ein Rechenweg für alle Systeme: Weggrößenverfahren in            ║
// ║  Matrixform (direkte Steifigkeitsmethode).                        ║
// ║                                                                   ║
// ║  1. frameBuildModel()   — Knoten, Stabelemente, Lasten            ║
// ║  2. frameSolveDSM()     — K·u = F lösen, Auflagerreaktionen       ║
// ║  3. frameSampleForces() — M/Q/N je Stab an NP+1 Stellen           ║
// ║     frameSampleFine()   — dazu Lastpunkte, Q=0-Stellen, exakte    ║
// ║                           Verschiebungen (für Diagramme, max-Werte)║
// ║  4. calculateFrame()    — Orchestrator, Tabelle, Rendering        ║
// ║                                                                   ║
// ║  Deckt ab: jede Kombination aus fixed/pin/roller an A und B,      ║
// ║  Kopfhalterung, Gelenke in allen Stäben, Streckenlasten           ║
// ║  (Trapez, Teilbereich) und Einzellasten auf allen Stäben.         ║
// ║  Superposition ist automatisch erfüllt (lineares System).         ║
// ╚══════════════════════════════════════════════════════════════════╝
//
// ── Geometrie ──────────────────────────────────────────────────────
//   A = (0,0)   K2 = (0,hA)   K3 = (b,hB)   B = (b,0)
//   Stab 'left'  : A  → K2   (Fuß → Kopf, nach oben)
//   Stab 'rafter': K2 → K3   (links → rechts)
//   Stab 'right' : K3 → B    (Kopf → Fuß, nach unten)
//
// ── Vorzeichen (für alle Stäbe gleich) ─────────────────────────────
//   Gestrichelte Faser = Rahmeninnenseite.
//   M > 0 : Zug innen      (linke Stütze rechts, Riegel unten, rechte Stütze links)
//   Q     = dM/ds in Stabrichtung (s wie oben definiert)
//   N > 0 : Zug,  N < 0 : Druck
//   Die Arrays haben dieselbe Reihenfolge wie bisher:
//   Mleft[0]=Fuß A … Mleft[NP]=Kopf A,  Mraf[0]=links … Mraf[NP]=rechts,
//   Mright[0]=Kopf B … Mright[NP]=Fuß B.
//
// ── Lasten (Eingabe wie in der UI) ─────────────────────────────────
//   Streckenlast 'vert':  q_a → q_b von a bis b.
//     Riegel: a,b = horizontale Position x, q je m Grundriss, nach unten.
//     Stütze: a,b = Höhe z über Fuß, q je m Höhe. Richtung über dir:
//       dir='h'  → horizontal, q > 0 nach rechts → (z. B. Wind)
//       dir='ax' → axial, q > 0 nach unten (Standard für alte Dateien)
//   Einzellast 'horiz':   F ⊥ zum Stab, H ∥ zum Stab, Position z bzw. x.
//     Linke Stütze : F>0 nach links (außen),  H>0 nach unten
//     Rechte Stütze: F>0 nach rechts (außen), H>0 nach unten
//     Riegel       : F>0 senkrecht zum Riegel nach unten, H>0 in Riegelrichtung
//
// ── Auflagerreaktionen (Tabelle) ───────────────────────────────────
//   H > 0 → nach rechts,  V > 0 → nach oben,  M > 0 → gegen den Uhrzeigersinn
//
// Normalkraft-Verformungen werden (wie in der Handrechnung üblich)
// über eine sehr große Dehnsteifigkeit EA praktisch ausgeschaltet.

const FRAME_EA_FACTOR = 1e6;   // EA = 1e6 · EI  → dehnstarr

// ── 1. MODELL ──────────────────────────────────────────────────────
function frameBuildModel(b, hA, hB, cfg){
  const {supA, supB, head, headType, hinges, vLoads, hLoads, EI_S, EI_R} = cfg;
  const gable = cfg.gable || null;             // Satteldach (v0.11.3): {xF, yF, tF}
  const clamp01 = t => Math.min(Math.max(t,0),1);
  const tol = 1e-7;

  // Geometrie der drei Stäbe (Parameter t ∈ [0,1]); Satteldach: Riegel als Polygonzug über den First PF
  const members = {
    left:   {P0:[0,0],  P1:[0,hA], EI:EI_S, len:hA},
    rafter: {P0:[0,hA], P1:[b,hB], EI:EI_R, len:frameRafLen(b,hA,hB,gable), PF: gable ? [gable.xF, gable.yF] : null},
    right:  {P0:[b,hB], P1:[b,0],  EI:EI_S, len:hB}
  };
  // Umrechnung Benutzer-Position → Parameter t
  //   left : z über Fuß → t = z/hA
  //   right: z über Fuß → t = 1 − z/hB   (Stab läuft Kopf → Fuß)
  //   rafter: x horizontal → t = x/b
  const tOf = (mem, pos) => mem==='left' ? clamp01(pos/hA)
                          : mem==='right' ? clamp01(1-pos/hB)
                          : clamp01(pos/b);
  const ptOf = (mem, t) => {
    const m = members[mem];
    if(mem==='rafter' && gable) return [b*t, frameRafY(b*t, b, hA, hB, gable)];
    return [m.P0[0]+(m.P1[0]-m.P0[0])*t, m.P0[1]+(m.P1[1]-m.P0[1])*t];
  };
  // Richtung des Riegels am Parameter t (am First: Winkelhalbierende)
  const rafCS = t => { const m=members.rafter, u=(P,Q)=>{ const l=Math.hypot(Q[0]-P[0],Q[1]-P[1]); return [(Q[0]-P[0])/l,(Q[1]-P[1])/l]; };
    if(!gable) return u(m.P0, m.P1);
    const d1=u(m.P0, m.PF), d2=u(m.PF, m.P1);
    if(Math.abs(t-gable.tF)<1e-9) return u([0,0],[d1[0]+d2[0], d1[1]+d2[1]]);
    return t<gable.tF ? d1 : d2; };

  // Teilungspunkte je Stab: Enden, Gelenke, Einzellasten, Lastgrenzen
  const cuts = {left:[0,1], rafter: gable ? [0, gable.tF, 1] : [0,1], right:[0,1]};
  const hingeT = {left:[], rafter:[], right:[]};
  hinges.forEach(hg=>{
    const mem = hg.member, t = tOf(mem, parseFloat(hg.pos)||0);
    cuts[mem].push(t); hingeT[mem].push(t);
  });
  hLoads.forEach(hl=>{
    const mem = hl.values.member||'left';
    cuts[mem].push(tOf(mem, hl.values.z||0));
  });
  vLoads.forEach(dl=>{
    const mem = dl.values.member||'rafter';
    cuts[mem].push(tOf(mem, dl.values.a||0), tOf(mem, dl.values.b||0));
  });

  // Knoten (Verschiebungen gemeinsam, Verdrehung ggf. getrennt bei Gelenk)
  const nodes = [];         // {x,y,ux,uy,rot}
  let ndof = 0;
  const nodeAt = (P) => {
    let n = nodes.find(n=>Math.abs(n.x-P[0])<tol && Math.abs(n.y-P[1])<tol);
    if(!n){ n = {x:P[0], y:P[1], ux:ndof++, uy:ndof++, rot:ndof++, hinge:false}; nodes.push(n); }
    return n;
  };
  // Eckknoten zuerst, damit sie eindeutig sind
  const nA = nodeAt([0,0]), n2 = nodeAt([0,hA]), n3 = nodeAt([b,hB]), nB = nodeAt([b,0]);

  const elems = [];
  Object.keys(members).forEach(mem=>{
    const ts = [...new Set(cuts[mem].map(t=>+t.toFixed(9)))].sort((a,b)=>a-b);
    for(let i=0;i<ts.length-1;i++){
      const t0=ts[i], t1=ts[i+1];
      if(t1-t0 < 1e-9) continue;
      const Pi = ptOf(mem,t0), Pj = ptOf(mem,t1);
      const ni = nodeAt(Pi), nj = nodeAt(Pj);
      const isHinge = t => hingeT[mem].some(h=>Math.abs(h-t)<1e-9);
      // Gelenk: eigener Verdrehungsfreiheitsgrad für dieses Stabende
      const ri = isHinge(t0) ? (ni.hinge=true, ndof++) : ni.rot;
      const rj = isHinge(t1) ? (nj.hinge=true, ndof++) : nj.rot;
      const dx = Pj[0]-Pi[0], dy = Pj[1]-Pi[1], L = Math.hypot(dx,dy);
      const el={mem, t0, t1, L, c:dx/L, s:dy/L, EI:members[mem].EI, dofs:[ni.ux, ni.uy, ri, nj.ux, nj.uy, rj]};
      (cfg.temps||[]).forEach(T=>{ if((T.member||'rafter')===mem){ el.eps0=(el.eps0||0)+T.eps0; el.kap0=(el.kap0||0)+T.kap0; if(T.EA>0) el.EA=T.EA; } });   // Temperatur (v0.11.6)
      elems.push(el);
    }
  });

  // Streckenlast je Element als globale Kraft je m Stablänge: g(ξ) = [gx, gy]
  // (linear innerhalb eines Elements, weil an allen Lastgrenzen geteilt wurde)
  elems.forEach(e=>{
    e.gAt = (xi)=>{               // xi = Abstand vom Elementanfang [m]
      const t = e.t0 + (e.t1-e.t0)*xi/e.L;
      let gx=0, gy=0;
      vLoads.forEach(dl=>{
        const v = dl.values, mem = v.member||'rafter';
        if(mem!==e.mem) return;
        const ta = tOf(mem, v.a||0), tb = tOf(mem, v.b||0);
        const lo = Math.min(ta,tb), hi = Math.max(ta,tb);
        if(hi-lo < 1e-12 || t < lo-1e-12 || t > hi+1e-12) return;
        const frac = (t-ta)/(tb-ta);              // 0 bei a, 1 bei b
        const q = v.qa + (v.qb - v.qa)*frac;
        if(mem==='rafter'){
          const rd = v.rdir||'v';
          if(rd==='n'){
            // rechtwinklig zum Riegel, je m Stablänge, q > 0 auf den Riegel (Winddruck) = (sin α, −cos α)
            gx += q*e.s; gy -= q*e.c;
          } else if(rd==='h'){
            // waagerecht, je m Höhe → je m Stablänge: q·|sin α|, q > 0 nach rechts
            gx += q*Math.abs(e.s);
          } else {
            // Riegel: q je m Grundriss → je m Stablänge: q·|cos α|, nach unten
            gy -= q*Math.abs(e.c);
          }
        } else if(v.dir==='h'){
          // Stütze horizontal (z. B. Wind): q > 0 → nach rechts, je m Höhe
          gx += q;
        } else {
          // Stütze axial (Eigengewicht o. Ä.): q > 0 → nach unten
          gy -= q;
        }
      });
      return [gx, gy];
    };
    // lokal: px (Stabachse), py (senkrecht, links von Stabrichtung)
    e.pAt = (xi)=>{ const [gx,gy]=e.gAt(xi); return [gx*e.c+gy*e.s, -gx*e.s+gy*e.c]; };
  });

  // Einzellasten → Knotenlasten (global)
  const F = new Array(ndof).fill(0);
  hLoads.forEach(hl=>{
    const v = hl.values, mem = v.member||'left';
    const Fp = v.F||0, Hp = v.H||0;
    const n = nodeAt(ptOf(mem, tOf(mem, v.z||0)));
    if(mem==='left'){  F[n.ux] += -Fp; F[n.uy] += -Hp; }
    else if(mem==='right'){ F[n.ux] += Fp; F[n.uy] += -Hp; }
    else {
      const [c, s] = rafCS(tOf('rafter', v.z||0));
      // ⊥ nach unten = −(lokale y-Richtung) = (s, −c);  ∥ = (c, s)
      F[n.ux] += Fp*s + Hp*c;
      F[n.uy] += -Fp*c + Hp*s;
    }
  });

  // Lagerbedingungen
  const fixed = new Set(), springs = [], presc = {}, setf = (typeof LF_SETF==='number') ? LF_SETF : 1;
  const hold = (d, c, val) => { if(c>0) springs.push({d, k:c, s:val*setf}); else { fixed.add(d); if(val) presc[d]=val*setf; } };
  const support = (n, type, x={}) => {              // x: Federn und Setzungen (v0.11.6)
    hold(n.uy, +x.cv||0, -(+x.sv||0)/1000);
    if(type==='fixed' || type==='pin') hold(n.ux, +x.ch||0, (+x.sh||0)/1000);
    if(type==='fixed') hold(n.rot, +x.cr||0, (+x.sr||0)/1000);
  };
  support(nA, supA, (cfg.supx||{}).A); support(nB, supB, (cfg.supx||{}).B);
  if(head==='left' || head==='right'){
    const nh = head==='left' ? n2 : n3;
    fixed.add(nh.ux); if(headType==='pin') fixed.add(nh.uy);
  }

  const nF = gable ? nodeAt(ptOf('rafter', gable.tF)) : null;
  return {nodes, elems, F, fixed, ndof, nA, nB, n2, n3, nF, head, members, gable, springs, presc};
}

// Lokale Elementsteifigkeit (Euler-Bernoulli, 6×6) und Transformation
function frameElemK(e){
  const {L, EI} = e, EA = e.EA || FRAME_EA_FACTOR*EI;   // e.EA: echte Dehnsteifigkeit bei Temperatur mit Querschnittsfläche (v0.11.6)
  const a=EA/L, b1=12*EI/L**3, b2=6*EI/L**2, b3=4*EI/L, b4=2*EI/L;
  return [
    [ a,  0,   0,  -a,  0,   0 ],
    [ 0,  b1,  b2,  0, -b1,  b2],
    [ 0,  b2,  b3,  0, -b2,  b4],
    [-a,  0,   0,   a,  0,   0 ],
    [ 0, -b1, -b2,  0,  b1, -b2],
    [ 0,  b2,  b4,  0, -b2,  b3]
  ];
}
function frameElemT(e){
  const {c,s} = e;
  return [[c,s,0,0,0,0],[-s,c,0,0,0,0],[0,0,1,0,0,0],
          [0,0,0,c,s,0],[0,0,0,-s,c,0],[0,0,0,0,0,1]];
}
const GAUSS4 = [[-0.8611363115940526,0.3478548451374538],[-0.3399810435848563,0.6521451548625461],
                [ 0.3399810435848563,0.6521451548625461],[ 0.8611363115940526,0.3478548451374538]];

// Äquivalente Knotenlasten (lokal) aus Streckenlast, exakt per Gauss-Integration
function frameElemFeq(e){
  const L=e.L, f=[0,0,0,0,0,0];
  GAUSS4.forEach(([g,w])=>{
    const xi=(g+1)/2*L, t=xi/L, W=w*L/2;
    const [px,py]=e.pAt(xi);
    const N1=1-3*t*t+2*t**3, N2=L*(t-2*t*t+t**3), N3=3*t*t-2*t**3, N4=L*(-t*t+t**3);
    f[0]+=px*(1-t)*W; f[3]+=px*t*W;
    f[1]+=py*N1*W; f[2]+=py*N2*W; f[4]+=py*N3*W; f[5]+=py*N4*W;
  });
  // Temperatur (v0.11.6): Anfangsdehnung ε₀ und -krümmung κ₀ (κ₀ > 0: Faser innen/unten länger, wie M > 0)
  if(e.eps0 || e.kap0){ const EA=e.EA || FRAME_EA_FACTOR*e.EI;
    f[0]-=EA*(e.eps0||0); f[3]+=EA*(e.eps0||0); f[2]-=e.EI*(e.kap0||0); f[5]+=e.EI*(e.kap0||0); }
  return f;
}

// ── 2. LÖSEN ───────────────────────────────────────────────────────
function frameSolveDSM(model){
  const {elems, F, fixed, ndof} = model;
  const K = Array.from({length:ndof},()=>new Array(ndof).fill(0));
  const Fg = F.slice();
  elems.forEach(e=>{
    e.k = frameElemK(e); e.T = frameElemT(e); e.feq = frameElemFeq(e);
    const T=e.T, k=e.k, d=e.dofs;
    // kg = Tᵀ k T,  fg = Tᵀ feq
    for(let i=0;i<6;i++) for(let j=0;j<6;j++){
      let sum=0;
      for(let p=0;p<6;p++){ if(!T[p][i]) continue;
        for(let q=0;q<6;q++){ if(T[q][j]) sum+=T[p][i]*k[p][q]*T[q][j]; } }
      K[d[i]][d[j]]+=sum;
    }
    for(let i=0;i<6;i++){ let s=0; for(let p=0;p<6;p++) s+=T[p][i]*e.feq[p]; Fg[d[i]]+=s; }
  });

  // Federn: Steifigkeit auf die Hauptdiagonale, Setzung der Feder als Kraft k·s (v0.11.6)
  (model.springs||[]).forEach(sp=>{ K[sp.d][sp.d]+=sp.k; Fg[sp.d]+=sp.k*sp.s; });
  const presc = model.presc || {}, pK = Object.keys(presc).map(Number);
  // Freiheitsgrade ohne Steifigkeit (z. B. Knotenverdrehung an einem Gelenk) festhalten
  for(let i=0;i<ndof;i++) if(Math.abs(K[i][i])<1e-12 && !fixed.has(i)) fixed.add(i);
  const free = [];
  for(let i=0;i<ndof;i++) if(!fixed.has(i)) free.push(i);

  // Gauss mit Spaltenpivotisierung auf dem freien Teilsystem
  const n = free.length;
  const A = free.map(i=>[...free.map(j=>K[i][j]), Fg[i] - pK.reduce((t,d)=>t+K[i][d]*presc[d],0)]);   // vorgegebene Verschiebungen (Setzungen)
  const scale = Math.max(...free.map(i=>Math.abs(K[i][i])), 1);
  for(let p=0;p<n;p++){
    let mr=p;
    for(let r=p+1;r<n;r++) if(Math.abs(A[r][p])>Math.abs(A[mr][p])) mr=r;
    if(Math.abs(A[mr][p]) < 1e-10*scale) return {mechanism:true};
    [A[p],A[mr]]=[A[mr],A[p]];
    for(let r=p+1;r<n;r++){
      const f=A[r][p]/A[p][p]; if(!f) continue;
      for(let c=p;c<=n;c++) A[r][c]-=f*A[p][c];
    }
  }
  const x=new Array(n).fill(0);
  for(let i=n-1;i>=0;i--){
    let s=A[i][n]; for(let j=i+1;j<n;j++) s-=A[i][j]*x[j]; x[i]=s/A[i][i];
  }
  const u=new Array(ndof).fill(0);
  free.forEach((d,i)=>u[d]=x[i]); pK.forEach(d=>{ u[d]=presc[d]; });

  // Reaktionen R = K·u − F (nur an gefesselten Freiheitsgraden relevant)
  const R=new Array(ndof).fill(0);
  for(let i=0;i<ndof;i++){ let s=-Fg[i]; for(let j=0;j<ndof;j++) s+=K[i][j]*u[j]; R[i]=s; }
  (model.springs||[]).forEach(sp=>{ R[sp.d] = sp.k*(sp.s-u[sp.d]); });   // Federkraft = Auflagerkraft

  // Stabendkräfte lokal: f = k·(T·u_e) − feq
  elems.forEach(e=>{
    const ue=e.dofs.map(d=>u[d]);
    const ul=e.T.map(row=>row.reduce((s,v,j)=>s+v*ue[j],0));
    e.fEnd=e.k.map((row,i)=>row.reduce((s,v,j)=>s+v*ul[j],0)-e.feq[i]);
    e.uLoc=ul;
  });
  return {u, R, mechanism:false};
}

// Ungekapselter Löser für Hilfsrechnungen (Kraftgrößenverfahren im Rechenweg, calc v0.11.13): spätere Hüllen (Schnitt, Rechenweg)
// sollen davon nichts mitschneiden.
const FRAME_SOLVE_RAW = frameSolveDSM;
// ── 3. SCHNITTGRÖSSEN ──────────────────────────────────────────────
// Aus den Stabendkräften am Elementanfang + Gleichgewicht am Teilstück 0…ξ:
//   N(ξ) = −N_i − ∫px,   Q(ξ) = V_i + ∫py,   M(ξ) = −M_i + V_i·ξ + ∫py(τ)(ξ−τ)dτ
function frameForcesAt(e, xi){
  const [Ni,Vi,Mi] = e.fEnd;
  let Ipx=0, Ipy=0, Imy=0;
  if(xi>0) GAUSS4.forEach(([g,w])=>{
    const tau=(g+1)/2*xi, W=w*xi/2, [px,py]=e.pAt(tau);
    Ipx+=px*W; Ipy+=py*W; Imy+=py*(xi-tau)*W;
  });
  return {N:-Ni-Ipx, Q:Vi+Ipy, M:-Mi+Vi*xi+Imy};
}
function frameSampleForces(model, NP){
  const out={};
  ['left','rafter','right'].forEach(mem=>{
    out[mem]=sampleUniform(model.elems.filter(e=>e.mem===mem), NP);
  });
  return out;
}
// Gleichmäßig an t = k/NP (für SDF, Bericht, Tests)
function sampleUniform(es, NP){
  {
    const M=[],Q=[],N=[];
    for(let k=0;k<=NP;k++){
      const t=k/NP;
      // an einem Teilungspunkt: Wert des Elements davor (k=NP) bzw. danach nehmen
      let e=es.find(e=>t>=e.t0-1e-12 && t<e.t1-1e-12) || es[es.length-1];
      const xi=Math.min(Math.max((t-e.t0)/(e.t1-e.t0),0),1)*e.L;
      const f=frameForcesAt(e,xi);
      M.push(+f.M.toFixed(3)); Q.push(+f.Q.toFixed(3)); N.push(+f.N.toFixed(3));
    }
    return {M,Q,N};
  }
}

// ── 3b. FEINE ABTASTUNG FÜR DIE DARSTELLUNG ───────────────────────
// Wie frameSampleForces, aber die Stützstellen sind nicht gleichmäßig:
//   · gleichmäßiges Raster k/NP (Grundgerüst)
//   · jede Elementgrenze (Einzellast, Gelenk, Lastgrenze) ZWEIMAL:
//     Ende des Elements davor und Anfang des Elements danach → Sprünge
//     in Q/N und Knicke in M liegen exakt auf einer Stützstelle
//   · Nullstellen von Q im Element → dort liegt das Feldmoment max M
// Dazu die exakten Verschiebungen aus dem Weggrößenverfahren:
//   Knotenwerte u sind exakt. Dazwischen gilt EI·v'' = M (lokal), also
//     v(ξ) = v_i + θ_i·ξ + 1/EI · ∫₀^ξ (ξ−τ)·M(τ) dτ
//   M ist im Element höchstens kubisch → 4-Punkt-Gauss ist exakt.
//   Längsverschiebung linear zwischen den Knoten (dehnstarr).
// Ausgabe je Stab: t[], M[], Q[], N[], ux[], uy[] (global, in m)
function frameDispAt(e, xi){
  const [ui, vi, thi, uj] = e.uLoc;
  let I=0;
  if(xi>0) GAUSS4.forEach(([g,w])=>{
    const tau=(g+1)/2*xi, W=w*xi/2;
    I += (xi-tau)*frameForcesAt(e,tau).M*W;
  });
  const v = vi + thi*xi + I/e.EI + (e.kap0||0)*xi*xi/2;   // + Temperaturkrümmung (v0.11.6)
  const u = ui + (uj-ui)*xi/e.L;
  return [e.c*u - e.s*v, e.s*u + e.c*v];     // global ux, uy
}
function frameSampleFine(model, NP){
  const out={};
  ['left','rafter','right'].forEach(mem=>{
    out[mem]=sampleFine(model.elems.filter(e=>e.mem===mem), NP);
  });
  return out;
}
// Fein: Raster + Elementgrenzen doppelt + Q=0-Stellen, mit Verschiebungen
function sampleFine(elems, NP){
  {
    const es=elems.slice().sort((a,b)=>a.t0-b.t0);
    const r={t:[],M:[],Q:[],N:[],ux:[],uy:[]};
    es.forEach(e=>{
      // Stützstellen im Element (als ξ in m)
      const xs=new Set([0, e.L]);
      for(let k=0;k<=NP;k++){
        const t=k/NP;
        if(t>e.t0+1e-9 && t<e.t1-1e-9) xs.add((t-e.t0)/(e.t1-e.t0)*e.L);
      }
      // Q = 0 im Element suchen (Vorzeichenwechsel + Bisektion)
      const nS=24; let qPrev=frameForcesAt(e,0).Q;
      for(let k=1;k<=nS;k++){
        const x1=e.L*k/nS, q1=frameForcesAt(e,x1).Q;
        if(qPrev*q1<0){
          let lo=e.L*(k-1)/nS, hi=x1, qlo=qPrev;
          for(let it=0;it<50;it++){
            const mid=(lo+hi)/2, qm=frameForcesAt(e,mid).Q;
            if(qlo*qm<=0) hi=mid; else { lo=mid; qlo=qm; }
          }
          xs.add((lo+hi)/2);
        }
        qPrev=q1;
      }
      [...xs].sort((a,b)=>a-b).forEach(xi=>{
        const f=frameForcesAt(e,xi), d=frameDispAt(e,xi);
        const t=e.t0+(e.t1-e.t0)*xi/e.L;
        // doppelten Punkt an einer Elementgrenze nur behalten, wenn sich etwas ändert
        const n=r.t.length-1;
        if(n>=0 && Math.abs(r.t[n]-t)<1e-9 && Math.abs(r.M[n]-f.M)<1e-6 &&
           Math.abs(r.Q[n]-f.Q)<1e-6 && Math.abs(r.N[n]-f.N)<1e-6) return;
        r.t.push(t); r.M.push(f.M); r.Q.push(f.Q); r.N.push(f.N);
        r.ux.push(d[0]); r.uy.push(d[1]);
      });
    });
    return r;
  }
}

// ╔══════════════════════════════════════════════════════════════════╗
// ║  LINIENTRAGWERKE: Einfeldträger, Kragarm, Durchlaufträger         ║
// ║  Derselbe Rechenweg wie beim Rahmen (Weggrößenverfahren),         ║
// ║  nur mit einem geraden Stab auf der x-Achse.                      ║
// ╚══════════════════════════════════════════════════════════════════╝
//   x nach rechts, y nach oben. Eingabe:
//     supports: [{x, type:'pin'|'roller'|'fixed'}]
//     points:   [{x, Fx (→ +), Fy (↓ +), Me (im Uhrzeigersinn +)}]
//     dists:    [{a, b, qa, qb}]  (↓ +, linear von a nach b)
//     EI in kNm²
//   Ergebnis (lineSolve): fein abgetastete Arrays t (= x/L), M (Zug unten +),
//   Q (= dM/dx), N (Zug +), uy (m, nach oben +), gleichmäßige Arrays (uni)
//   und Auflagerkräfte je Lager {H (→ +), V (↑ +), M (↺ +)}.
function lineBuildModel(L, cfg){
  const {supports, points, dists, EI} = cfg;
  const hinges = cfg.hinges || [], EIfn = cfg.EIfn || null;   // Gelenke [x], EI je Stelle (optional)
  const cl = x => Math.min(Math.max(x,0),L);
  const cuts = [0, L];
  hinges.forEach(x=>cuts.push(cl(x)));
  supports.forEach(s=>cuts.push(cl(s.x)));
  points.forEach(p=>cuts.push(cl(p.x)));
  dists.forEach(d=>cuts.push(cl(d.a), cl(d.b)));
  const xs = [...new Set(cuts.map(x=>+x.toFixed(9)))].sort((a,b)=>a-b);
  let ndof = 0;
  const isH = x => hinges.some(h=>Math.abs(cl(h)-x)<1e-7);
  // Gelenk: zweiter Drehfreiheitsgrad rot2 für den Stab rechts vom Knoten
  const nodes = xs.map(x=>{ const n={x, ux:ndof++, uy:ndof++, rot:ndof++}; if(isH(x)) n.rot2=ndof++; return n; });
  const nodeAt = x => nodes.reduce((b,n)=>Math.abs(n.x-cl(x))<Math.abs(b.x-cl(x))?n:b, nodes[0]);
  const qAt = x => {                          // Streckenlast ↓ an der Stelle x
    let q = 0;
    dists.forEach(d=>{
      const a=cl(d.a), b=cl(d.b);
      if(b-a < 1e-12 || x < a-1e-12 || x > b+1e-12) return;
      q += d.qa + (d.qb-d.qa)*(x-a)/(b-a);
    });
    return q;
  };
  const elems = [];
  for(let i=0;i<nodes.length-1;i++){
    const ni=nodes[i], nj=nodes[i+1], len=nj.x-ni.x;
    if(len < 1e-9) continue;
    const e = {mem:'beam', x0:ni.x, t0:ni.x/L, t1:nj.x/L, L:len, c:1, s:0, EI: EIfn ? EIfn(ni.x+len/2) : EI,
               dofs:[ni.ux, ni.uy, ni.rot2??ni.rot, nj.ux, nj.uy, nj.rot]};
    // Mitte des Elements auswerten, damit Lastgrenzen am Rand eindeutig sind
    e.pAt = xi => [0, -qAt(e.x0 + Math.min(Math.max(xi, 1e-9), len-1e-9))];
    (cfg.temps||[]).forEach(T=>{ const xm=ni.x+len/2; if(xm>=T.x0-1e-9 && xm<=T.x1+1e-9){ e.eps0=(e.eps0||0)+T.eps0; e.kap0=(e.kap0||0)+T.kap0; if(T.EA>0) e.EA=T.EA; } });   // Temperatur (v0.11.6)
    elems.push(e);
  }
  const F = new Array(ndof).fill(0);
  points.forEach(p=>{
    const n = nodeAt(p.x);
    F[n.ux] += p.Fx||0;  F[n.uy] -= p.Fy||0;  F[n.rot] -= p.Me||0;
  });
  const fixed = new Set(), springs = [], presc = {}, setf = (typeof LF_SETF==='number') ? LF_SETF : 1;
  // gehaltene Richtung: starr (ggf. mit vorgegebener Verschiebung) oder Feder (v0.11.6)
  const hold = (d, c, val) => { if(c>0) springs.push({d, k:c, s:val*setf}); else { fixed.add(d); if(val) presc[d]=val*setf; } };
  supports.forEach(s=>{
    const n = nodeAt(s.x);
    hold(n.uy, +s.cv||0, -(+s.sv||0)/1000);
    if(s.type==='pin' || s.type==='fixed' || s.hfix) hold(n.ux, +s.ch||0, (+s.sh||0)/1000);
    if(s.type==='fixed') hold(n.rot, +s.cr||0, (+s.sr||0)/1000);
  });
  return {nodes, elems, F, fixed, ndof, nodeAt, springs, presc};
}
function lineSolve(L, cfg, NP=100){
  const model = lineBuildModel(L, cfg);
  const sol = frameSolveDSM(model);
  if(sol.mechanism) return null;
  const fine = sampleFine(model.elems, NP);
  const uni  = sampleUniform(model.elems, NP);
  const reac = cfg.supports.map(s=>{
    const n = model.nodeAt(s.x);
    return {H: sol.R[n.ux], V: sol.R[n.uy], M: sol.R[n.rot]};
  });
  // Schnittgrößen an einer Stelle x (rechts vom Knoten, falls dort ein Knoten liegt)
  const at = x => {
    const t = x/L, es = model.elems;
    const e = es.find(e=>t>=e.t0-1e-12 && t<e.t1-1e-12) || es[es.length-1];
    return frameForcesAt(e, Math.min(Math.max(x-e.x0,0),e.L));
  };
  return {fine, uni, reac, at, model};
}
// Ausgabe für die Diagramme: Vorzeichen je System wie bisher (sM, sQ)
function lineArrays(res, sM, sQ, closeQ){
  const f = res.fine;
  const o = {ts:f.t.slice(), M:f.M.map(v=>sM*v), Q:f.Q.map(v=>sQ*v), N:f.N.slice(), w:f.uy.map(v=>v*1000)};
  if(closeQ){
    // Querkraftlinie an den Endauflagern auf null schließen (senkrechter Strich)
    const n=o.ts.length-1;
    o.ts.unshift(0); o.M.unshift(o.M[0]); o.Q.unshift(0); o.N.unshift(o.N[0]); o.w.unshift(o.w[0]);
    o.ts.push(1); o.M.push(o.M[n+1]); o.Q.push(0); o.N.push(o.N[n+1]); o.w.push(o.w[n+1]);
  }
  o.uni = {M:res.uni.M.map(v=>sM*v), Q:res.uni.Q.map(v=>sQ*v), N:res.uni.N};
  return o;
}

// ══════════════════════════════════════════════════
// LASTFÄLLE UND KOMBINATIONEN (calc v0.11.31, vorher in calc.html)
// Je Teillastfall eine Einheitsrechnung mit charakteristischen Lasten, dann je Stelle die ungünstigste Kombination:
//   EN 1990 Gl. 6.10: Σ γ_G·G_k + γ_Q·Q_k,1 + Σ γ_Q·ψ_0,i·Q_k,i (γ_G = 1,35, günstig 1,0; γ_Q = 1,5, günstig 0)
//   UK: Gl. 6.10a/6.10b mit ξ = 0,925 · ES (CTE DB-SE) und CH (SIA 260): γ_G,günstig = 0,80 · CH: Begleiteinwirkung ψ0·Q_k ohne γ_Q
// Durchbiegung: charakteristische Kombination (γ = 1). W1 und W2 schließen sich aus.
// ══════════════════════════════════════════════════
const LF_TYPES = ['G','Q','S','W1','W2','T'];   // T: Temperatur (v0.11.6, ψ = 0,6 / 0,5 / 0)
const LF_PSI = { A:[0.7,0.5,0.3], B:[0.7,0.5,0.3], C:[0.7,0.7,0.6], D:[0.7,0.7,0.6], E:[1.0,0.9,0.8], F:[0.7,0.7,0.6], H:[0,0,0] };
const LF_PSI_S = [0.5,0.2,0], LF_PSI_W = [0.6,0.2,0], LF_PSI_T = [0.6,0.5,0];
const LF_GSUP = 1.35, LF_GINF = 1.0, LF_GQ = 1.5, LF_GINF_CH = 0.80, LF_XI = 0.925;
// Regeln je Bemessungsgrundlage. o: {na:'de'|'at'|'fr'|'uk'|'es'|'ch', cat:'A'…'H', psiCH:{Q,S,W,T} (leer = 1,0)}
//   Ergebnis: {na, mode:'en'|'uk'|'ch', cat, gSup, gInf, gQ, xi, psi:{G,Q,S,W1,W2,T: [ψ0, ψ1, ψ2]}}
function lcRules(o={}){
  const na=o.na||'de', uk=na==='uk', ch=na==='ch', es=na==='es';
  const cat = LF_PSI[o.cat] && !(es && o.cat==='E') ? o.cat : 'A';      // ES (CTE DB-SE): keine Lager-Kategorie
  const pc = k => { const v=o.psiCH ? +o.psiCH[k] : NaN; return isFinite(v) ? Math.min(1, Math.max(0, v)) : 1; };
  const tri = v => [v, v, v];
  const psi = ch ? { Q:tri(pc('Q')), S:tri(pc('S')), W1:tri(pc('W')), W2:tri(pc('W')), T:tri(pc('T')) }
                 : { Q: uk && cat==='H' ? [0.7,0,0] : LF_PSI[cat], S:LF_PSI_S, W1: uk ? [0.5,0.2,0] : LF_PSI_W, W2: uk ? [0.5,0.2,0] : LF_PSI_W, T:LF_PSI_T };
  psi.G = [1,1,1];
  return { na, mode: uk ? 'uk' : ch ? 'ch' : 'en', cat, gSup:LF_GSUP, gInf:(ch||es) ? LF_GINF_CH : LF_GINF, gQ:LF_GQ, xi:LF_XI, psi };
}
const lcExcl = (a, b) => (a==='W1'&&b==='W2') || (a==='W2'&&b==='W1');
// Kombinationen: GZT je γ_G und Leiteinwirkung, GZG (charakteristisch) je Leiteinwirkung. P: [{k, i, T, seg}]
function lcOptions(R, P){
  const hasG=P.some(p=>p.T==='G'), vars=[...new Set(P.filter(p=>p.T!=='G').map(p=>p.T))], leads=[null, ...vars], o=[];
  if(R.mode==='uk' && hasG){   // 6.10a: 1,35·G + Σ 1,5·ψ0·Q · 6.10b: ξ·1,35·G + 1,5·Q_1 + Σ 1,5·ψ0·Q_i · günstig 1,0·G
    o.push({uls:true, gam:R.gSup, lead:null, eq:'a'}); vars.forEach(lead=>o.push({uls:true, gam:R.xi*R.gSup, lead, eq:'b'}));
    leads.forEach(lead=>o.push({uls:true, gam:R.gInf, lead}));
  } else
  (hasG ? [R.gSup, R.gInf] : [R.gSup]).forEach(gam=>leads.forEach(lead=>o.push({uls:true, gam, lead})));
  leads.forEach(lead=>o.push({uls:false, gam:1, lead}));
  return o;
}
// Faktor eines Lastfalls T in der Kombination o
function lcFac(R, o, T){
  if(T==='G') return o.gam;
  const g = o.uls ? R.gQ : 1;
  if(T===o.lead) return g;
  if(lcExcl(T, o.lead)) return 0;
  if(R.mode==='ch') return R.psi[T][0];   // SIA 260: Begleiteinwirkung ψ0·Q_k ohne γ_Q
  return g*R.psi[T][0];
}
// Grenzwert an einer Stelle: val(p) = Ergebnis des Teillastfalls p; sense +1 (max) / −1 (min). Liefert Wert und Faktoren je Teillastfall.
function lcAt(R, o, P, val, sense){
  const fac={}; let v=0;
  P.forEach(p=>{ if(p.T==='G'){ fac[p.k]=o.gam; v+=o.gam*val(p); } });
  const plain=P.filter(p=>p.T!=='G' && p.T!=='W1' && p.T!=='W2');
  plain.forEach(p=>{ const f=lcFac(R,o,p.T), c=f*val(p); if(c*sense>1e-12){ fac[p.k]=f; v+=c; } else fac[p.k]=0; });
  // Wind: W1 und W2 schließen sich aus — die ungünstigere (oder keine)
  const W=['W1','W2'].map(T=>{ const ps=P.filter(p=>p.T===T); if(!ps.length) return null; const f=lcFac(R,o,T); return {ps, f, c:f*ps.reduce((s,p)=>s+val(p),0)}; }).filter(Boolean);
  W.forEach(w=>w.ps.forEach(p=>{ fac[p.k]=0; }));
  const best=W.filter(w=>w.f>0 && w.c*sense>1e-12).sort((a,b)=>sense*(b.c-a.c))[0];
  if(best){ v+=best.c; best.ps.forEach(p=>{ fac[p.k]=best.f; }); }
  return {v, fac};
}
// Einheitsrechnung auf einem gemeinsamen Raster abtasten. cap: {elems, reac:[[H,V,M]…]} (Modell der Rechnung)
function lcSample(cap, mems, NP){
  if(!cap) return null;
  const out={reac:cap.reac.map(r=>r.slice())};
  mems.forEach(m=>{ const es=cap.elems.filter(e=>e.mem===m).sort((a,b)=>a.t0-b.t0), r={t:[],M:[],Q:[],N:[],ux:[],uy:[]};
    es.forEach(e=>{ const n=Math.max(2, Math.ceil((e.t1-e.t0)*NP));
      for(let k=0;k<=n;k++){ const xi=e.L*k/n, f=frameForcesAt(e,xi), d=frameDispAt(e,xi);
        r.t.push(e.t0+(e.t1-e.t0)*k/n); r.M.push(f.M); r.Q.push(f.Q); r.N.push(f.N); r.ux.push(d[0]); r.uy.push(d[1]); } });
    out[m]=r; });
  return out;
}
// Überlagerung: Grenzlinien, maßgebende Kombinationen, Auflager-Grenzwerte, Biegelinie der maßgebenden GZG-Kombination.
//   runs[p.i] = lcSample(...) des Teillastfalls p
function lcCombine(R, mems, P, runs){
  const O=lcOptions(R,P), Ou=O.filter(o=>o.uls), Os=O.filter(o=>!o.uls);
  const env={}, gov={maxM:null, minM:null, absQ:null, absN:null, sls:null};
  const better=(g, v, cmp)=>!g || cmp(v, g.v);
  mems.forEach(m=>{
    const g0=runs[0][m], n=g0.t.length, e={t:g0.t.slice(), M:[],Q:[],N:[],M2:[],Q2:[],N2:[]};
    for(let i=0;i<n;i++){
      ['M','Q','N'].forEach(K=>{ let hi=-Infinity, lo=Infinity;
        Ou.forEach(o=>{ const val=p=>runs[p.i][m][K][i], a=lcAt(R,o,P,val,1), b=lcAt(R,o,P,val,-1);
          if(a.v>hi) hi=a.v; if(b.v<lo) lo=b.v;
          if(K==='M'){ if(better(gov.maxM,a.v,(x,y)=>x>y+1e-9)) gov.maxM={v:a.v, fac:a.fac, o, m, i}; if(better(gov.minM,b.v,(x,y)=>x<y-1e-9)) gov.minM={v:b.v, fac:b.fac, o, m, i}; }
          if(K==='Q'||K==='N'){ const key=K==='Q'?'absQ':'absN'; [a,b].forEach(r=>{ if(better(gov[key],Math.abs(r.v),(x,y)=>x>Math.abs(y)+1e-9)) gov[key]={v:r.v, fac:r.fac, o, m, i}; }); }
        });
        e[K].push(hi); e[K+'2'].push(lo); });
      // Gebrauchstauglichkeit: größte Verschiebung (Riegel/Träger lotrecht, Stiele waagerecht)
      const uK = (m==='left'||m==='right') ? 'ux' : 'uy';
      Os.forEach(o=>[1,-1].forEach(sn=>{ const r=lcAt(R,o,P,p=>runs[p.i][m][uK][i],sn); if(better(gov.sls,Math.abs(r.v),(x,y)=>x>Math.abs(y)+1e-12)) gov.sls={v:r.v, fac:r.fac, o, m, i, uK}; }));
    }
    env[m]=e;
  });
  // Auflagerkräfte: Grenzwerte je Komponente
  const reac = runs[0].reac.map((_,s)=>[0,1,2].map(c=>{ let hi=-Infinity, lo=Infinity;
    Ou.forEach(o=>{ const val=p=>runs[p.i].reac[s][c]; hi=Math.max(hi, lcAt(R,o,P,val,1).v); lo=Math.min(lo, lcAt(R,o,P,val,-1).v); }); return [hi, lo]; }));
  // Biegelinie der maßgebenden GZG-Kombination (echte Verformungsfigur)
  const shape={}; if(gov.sls) mems.forEach(m=>{ shape[m]={ux:[], uy:[]}; runs[0][m].t.forEach((_,i)=>['ux','uy'].forEach(k=>shape[m][k].push(P.reduce((s,p)=>s+(gov.sls.fac[p.k]||0)*runs[p.i][m][k][i],0)))); });
  ['absN','minM','maxM','absQ'].forEach(k=>{ if(gov[k] && Math.abs(gov[k].v)<1e-6) gov[k]=null; });
  return {env, gov, reac, shape, mems};
}

// ══════════════════════════════════════════════════
// ZUSAMMENGEFASSTE SCHNITTSTELLEN (calc v0.11.30)
// ══════════════════════════════════════════════════
// Unbestimmtheit n = r − 3 − g mit den wirksamen Gelenken (siehe calc.html, frameEffectiveHinges)
//   inp: {b, hA, hB, hinges:[{member, pos}], supA, supB, head:'none'|'left'|'right', headType:'roller'|'pin'}
function frameEffectiveHingesOf(inp){
  const {b, hA, hB} = inp, tol = 1e-6, keys = new Set();
  (inp.hinges||[]).forEach(hg=>{
    const Lm = hg.member==='rafter' ? b : hg.member==='left' ? hA : hB;
    const p  = Math.min(Math.max(parseFloat(hg.pos)||0, 0), Lm);
    let key;
    if(hg.member==='rafter') key = p<tol ? 'K2' : p>Lm-tol ? 'K3' : 'R:'+p.toFixed(6);
    else {
      const foot = hg.member==='left' ? 'A' : 'B', top = hg.member==='left' ? 'K2' : 'K3';
      const sup  = hg.member==='left' ? inp.supA : inp.supB;
      if(p<tol){ if(sup!=='fixed') return; key = 'foot'+foot; }
      else key = p>Lm-tol ? top : hg.member+':'+p.toFixed(6);
    }
    keys.add(key);
  });
  return keys.size;
}
function frameIndeterminacyOf(inp){
  const head = inp.head||'none', headDOF = head==='none' ? 0 : (inp.headType==='pin' ? 2 : 1);
  return supportDOF(inp.supA) + supportDOF(inp.supB) + headDOF - 3 - frameEffectiveHingesOf(inp);
}
// Rahmen komplett.
//   inp: {b, hA, hB, supA, supB, head, headType, hinges, vLoads, hLoads, EI_S, EI_R, gable, supx, temps, NP (50)}
//   vLoads/hLoads wie in der Oberfläche: [{enabled, values:{member, qa, qb, a, b, dir}}] bzw. [{enabled, values:{member, F, H, z}}]
//   Ergebnis: {mechanism} oder {model, sol, NP, forces (je Stab M/Q/N an NP+1 Stellen), fine (fein, mit Verschiebungen), reac}
function frameSolve(inp){
  const NP = inp.NP || 50;
  const model = frameBuildModel(inp.b, inp.hA, inp.hB, {
    supA:inp.supA, supB:inp.supB, head:inp.head||'none', headType:inp.headType||'roller',
    hinges:inp.hinges||[], vLoads:inp.vLoads||[], hLoads:inp.hLoads||[], EI_S:inp.EI_S, EI_R:inp.EI_R,
    gable:inp.gable||null, supx:inp.supx||{}, temps:inp.temps||[] });
  const sol = frameSolveDSM(model);
  if(sol.mechanism) return { mechanism:true, model };
  const R = sol.R, rx = n => ({ H:R[n.ux]||0, V:R[n.uy]||0, M:R[n.rot]||0 });
  const reac = { A:rx(model.nA), B:rx(model.nB) };
  if(inp.head==='left' || inp.head==='right') reac.head = rx(inp.head==='left' ? model.n2 : model.n3);
  return { model, sol, NP, forces:frameSampleForces(model, NP), fine:frameSampleFine(model, NP), reac };
}

const KragrSolver = { frameGableOf, frameRafY, frameRafLen, supportDOF, tempRows, frameBuildModel, frameElemK, frameElemT, frameElemFeq, frameSolveDSM,
  frameForcesAt, frameSampleForces, sampleUniform, frameDispAt, frameSampleFine, sampleFine, lineBuildModel, lineSolve, lineArrays,
  frameEffectiveHingesOf, frameIndeterminacyOf, frameSolve, FRAME_EA_FACTOR, GAUSS4,
  LF_TYPES, LF_PSI, LF_PSI_S, LF_PSI_W, LF_PSI_T, LF_GSUP, LF_GINF, LF_GQ, LF_GINF_CH, LF_XI, lcRules, lcExcl, lcOptions, lcFac, lcAt, lcSample, lcCombine };
if(typeof module!=='undefined' && module.exports) module.exports = KragrSolver;
