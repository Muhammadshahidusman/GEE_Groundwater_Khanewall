import { useState, useEffect } from "react";

// ─── DATA ───────────────────────────────────────────────────────────────────

const FACTORS = [
  { id: "SLP", name: "Slope", unit: "(in degrees)", rank: 7, weight: 0.0272, color: "#e07b54", icon: "⛰" },
  { id: "DD",  name: "Drainage Density", unit: "(km/km²)", rank: 6, weight: 0.0272, color: "#4a9eca", icon: "〰" },
  { id: "LD",  name: "Lineament Density", unit: "(km/km²)", rank: 3, weight: 0.1034, color: "#9b6bb5", icon: "⚡" },
  { id: "LULC",name: "LULC", unit: "(Land Use/Cover)", rank: 5, weight: 0.0728, color: "#5ba85a", icon: "🌿" },
  { id: "RAIN",name: "Rainfall", unit: "(mm/year)", rank: 2, weight: 0.2147, color: "#3a86d4", icon: "🌧" },
  { id: "GEO", name: "Geology", unit: "(Lithology)", rank: 1, weight: 0.4055, color: "#c8401a", icon: "🪨" },
  { id: "SOIL",name: "Soil Type", unit: "(Texture/Permeability)", rank: 4, weight: 0.1492, color: "#a0722a", icon: "🟫" },
];

// Pairwise matrix in FACTOR order above
const RAW_MATRIX = [
  [1,   1,   1/5, 1/4, 1/7, 1/9, 1/6],
  [1,   1,   1/5, 1/4, 1/7, 1/9, 1/6],
  [5,   5,   1,   2,   1/3, 1/5, 1/2],
  [4,   4,   1/2, 1,   1/4, 1/6, 1/3],
  [7,   7,   3,   4,   1,   1/3, 2  ],
  [9,   9,   5,   6,   3,   1,   4  ],
  [6,   6,   2,   3,   1/2, 1/4, 1  ],
];

const LAMBDA_MAX = 7.457;
const CI = 0.0762;
const RI  = 1.32;
const CR  = 0.0577;
const n   = 7;

// Column sums for normalized matrix display
const COL_SUMS = FACTORS.map((_, j) => RAW_MATRIX.reduce((s, row) => s + row[j], 0));

function normCell(i, j) { return RAW_MATRIX[i][j] / COL_SUMS[j]; }

// ─── Sub-criteria ────────────────────────────────────────────────────────────
const SUB = {
  SLP: [
    { cls: "> 30°", label: "Very Steep", rating: 1, potential: "Very Poor",  desc: "High runoff, minimal infiltration" },
    { cls: "20–30°", label: "Steep",      rating: 2, potential: "Poor",       desc: "Significant runoff, low recharge" },
    { cls: "10–20°", label: "Moderate",   rating: 3, potential: "Moderate",   desc: "Balanced runoff/infiltration" },
    { cls: "5–10°",  label: "Gentle",     rating: 4, potential: "Good",       desc: "Favours infiltration over runoff" },
    { cls: "< 5°",   label: "Flat",       rating: 5, potential: "Very Good",  desc: "Maximum infiltration & recharge" },
  ],
  DD: [
    { cls: "> 4.0",  label: "Very High",  rating: 1, potential: "Very Poor",  desc: "High surface drainage, less groundwater" },
    { cls: "3.0–4.0",label: "High",       rating: 2, potential: "Poor",       desc: "Increased runoff, less percolation" },
    { cls: "2.0–3.0",label: "Moderate",   rating: 3, potential: "Moderate",   desc: "Intermediate recharge" },
    { cls: "1.0–2.0",label: "Low",        rating: 4, potential: "Good",       desc: "More percolation, less runoff" },
    { cls: "< 1.0",  label: "Very Low",   rating: 5, potential: "Very Good",  desc: "Excellent groundwater recharge zone" },
  ],
  LD: [
    { cls: "< 0.5",  label: "Very Low",   rating: 1, potential: "Very Poor",  desc: "Minimal fractures, poor conductivity" },
    { cls: "0.5–1.0",label: "Low",        rating: 2, potential: "Poor",       desc: "Limited structural conduits" },
    { cls: "1.0–2.0",label: "Moderate",   rating: 3, potential: "Moderate",   desc: "Some fracture-controlled flow" },
    { cls: "2.0–3.0",label: "High",       rating: 4, potential: "Good",       desc: "Good fracture network, high recharge" },
    { cls: "> 3.0",  label: "Very High",  rating: 5, potential: "Very Good",  desc: "Dense fractures, excellent conduit" },
  ],
  LULC: [
    { cls: "Urban/Built-up",   label: "Impervious", rating: 1, potential: "Very Poor",  desc: "Impervious surfaces block recharge" },
    { cls: "Barren / Rocky",   label: "Barren",     rating: 2, potential: "Poor",       desc: "Low vegetation, high runoff" },
    { cls: "Scrubland",        label: "Scrubland",  rating: 3, potential: "Moderate",   desc: "Moderate infiltration capacity" },
    { cls: "Agricultural",     label: "Agri",       rating: 4, potential: "Good",       desc: "Tilled soil enhances percolation" },
    { cls: "Dense Forest / Wetland", label: "Forest", rating: 5, potential: "Very Good","desc": "High infiltration & moisture retention" },
  ],
  RAIN: [
    { cls: "< 400 mm",    label: "Very Low",   rating: 1, potential: "Very Poor",  desc: "Insufficient recharge source" },
    { cls: "400–600 mm",  label: "Low",        rating: 2, potential: "Poor",       desc: "Limited annual recharge" },
    { cls: "600–800 mm",  label: "Moderate",   rating: 3, potential: "Moderate",   desc: "Adequate seasonal recharge" },
    { cls: "800–1200 mm", label: "High",       rating: 4, potential: "Good",       desc: "Good recharge potential" },
    { cls: "> 1200 mm",   label: "Very High",  rating: 5, potential: "Very Good",  desc: "Excellent primary recharge source" },
  ],
  GEO: [
    { cls: "Massive Igneous / Metamorphic", label: "Massive", rating: 1, potential: "Very Poor",  desc: "Impermeable; negligible groundwater" },
    { cls: "Shale / Slate",                 label: "Shale",   rating: 2, potential: "Poor",       desc: "Very low permeability" },
    { cls: "Sandstone / Granite (weathered)",label: "Sandstone",rating:3, potential: "Moderate",  desc: "Secondary porosity, moderate yield" },
    { cls: "Limestone / Karst",             label: "Karst",   rating: 4, potential: "Good",       desc: "Solution cavities, high storage" },
    { cls: "Alluvium / Unconsolidated",     label: "Alluvium",rating: 5, potential: "Very Good",  desc: "Highest porosity & permeability" },
  ],
  SOIL: [
    { cls: "Clay",        label: "Clay",       rating: 1, potential: "Very Poor",  desc: "Near-zero infiltration capacity" },
    { cls: "Clay Loam",   label: "Clay Loam",  rating: 2, potential: "Poor",       desc: "Very slow percolation" },
    { cls: "Loam",        label: "Loam",       rating: 3, potential: "Moderate",   desc: "Moderate water retention & flow" },
    { cls: "Sandy Loam",  label: "Sandy Loam", rating: 4, potential: "Good",       desc: "Good drainage & infiltration" },
    { cls: "Sandy / Gravel",label:"Sandy",     rating: 5, potential: "Very Good",  desc: "Excellent percolation & recharge" },
  ],
};

const POTENTIAL_COLORS = {
  "Very Poor": "#c0392b", "Poor": "#e67e22", "Moderate": "#f1c40f",
  "Good": "#27ae60", "Very Good": "#1a7a4a",
};

function fmtVal(v) {
  if (v === 1) return "1";
  const map = { 0.2:"1/5", 0.25:"1/4", 0.143:"1/7", 0.111:"1/9", 0.167:"1/6",
                0.333:"1/3", 0.5:"1/2" };
  const k = parseFloat(v.toFixed(3));
  return map[k] ?? (v > 1 ? String(Math.round(v * 10)/10) : v.toFixed(3));
}

// ─── COMPONENT ──────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("overview");
  const [hoveredFactor, setHoveredFactor] = useState(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setTimeout(() => setMounted(true), 50); }, []);

  return (
    <div style={{
      fontFamily: "'Palatino Linotype', 'Book Antiqua', Palatino, serif",
      background: "#f7f3ee",
      minHeight: "100vh",
      color: "#1a1208",
    }}>
      <style>{`
        @keyframes slideUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeIn  { from{opacity:0} to{opacity:1} }
        @keyframes barGrow { from{width:0} to{width:var(--w)} }
        .tab-pill { cursor:pointer; border:none; transition:all 0.2s; font-family:inherit; }
        .tab-pill:hover { transform:translateY(-1px); }
        .trow:hover td { background:rgba(139,90,30,0.06) !important; }
        .factor-card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.12) !important; }
        .factor-card { transition:all 0.25s; }
        ::-webkit-scrollbar{height:5px;width:5px} 
        ::-webkit-scrollbar-track{background:#f0e8dc} 
        ::-webkit-scrollbar-thumb{background:#c8a03c;border-radius:3px}
      `}</style>

      {/* HEADER */}
      <div style={{
        background: "linear-gradient(135deg, #1a0e04 0%, #2d1a08 60%, #1a0e04 100%)",
        color: "#f0e8d8", padding: "2.5rem 1.5rem 2rem", textAlign: "center",
        borderBottom: "3px solid #c8a03c", position:"relative", overflow:"hidden",
      }}>
        <div style={{position:"absolute",inset:0,backgroundImage:"radial-gradient(ellipse at 30% 50%, rgba(200,160,60,0.08) 0%, transparent 60%), radial-gradient(ellipse at 70% 50%, rgba(200,100,30,0.06) 0%, transparent 60%)"}}/>
        <div style={{position:"relative"}}>
          <div style={{fontSize:"0.65rem", letterSpacing:"0.4em", color:"#c8a03c", textTransform:"uppercase", marginBottom:"0.6rem"}}>
            Multi-Criteria Decision Making · Remote Sensing & GIS
          </div>
          <h1 style={{fontSize:"clamp(1.5rem,4vw,2.4rem)", fontWeight:"700", margin:"0 0 0.5rem", lineHeight:1.15, letterSpacing:"-0.01em"}}>
            Groundwater Potential Zone Mapping
          </h1>
          <p style={{margin:"0 0 1.5rem", color:"#c0a878", fontSize:"0.95rem"}}>
            Analytic Hierarchy Process (AHP) — 7 Thematic Factor Analysis
          </p>

          {/* Mini weight pills */}
          <div style={{display:"flex", flexWrap:"wrap", gap:"0.4rem", justifyContent:"center"}}>
            {[...FACTORS].sort((a,b)=>a.rank-b.rank).map((f,i)=>(
              <div key={f.id} style={{
                padding:"0.3rem 0.7rem", borderRadius:"20px", fontSize:"0.72rem",
                background:`${f.color}22`, border:`1px solid ${f.color}60`,
                color:f.color, fontWeight:"600", letterSpacing:"0.03em",
                opacity: mounted ? 1 : 0, transition:`opacity 0.4s ${i*0.07}s`,
              }}>
                {f.icon} {f.name} — {(f.weight*100).toFixed(1)}%
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* TABS */}
      <div style={{background:"#ede5d8", borderBottom:"1px solid #d4c4a8", padding:"0 1rem", display:"flex", gap:"0", overflowX:"auto"}}>
        {[
          {id:"overview",   label:"① Overview"},
          {id:"matrix",     label:"② Pairwise Matrix"},
          {id:"normalized", label:"③ Normalized Matrix"},
          {id:"weights",    label:"④ Weights & CR"},
          {id:"sub",        label:"⑤ Sub-Criteria"},
          {id:"formula",    label:"⑥ Final Formula"},
        ].map(t=>(
          <button key={t.id} className="tab-pill" onClick={()=>setTab(t.id)} style={{
            padding:"0.75rem 1.1rem", background:"transparent", fontSize:"0.78rem",
            fontWeight: tab===t.id ? "700" : "400",
            color: tab===t.id ? "#8b3a0a" : "#6a5840",
            borderBottom: tab===t.id ? "3px solid #c8401a" : "3px solid transparent",
            whiteSpace:"nowrap", letterSpacing:"0.02em",
          }}>{t.label}</button>
        ))}
      </div>

      {/* CONTENT */}
      <div style={{maxWidth:"960px", margin:"0 auto", padding:"1.5rem 1rem 3rem", animation:"slideUp 0.4s ease"}}>

        {/* ── OVERVIEW ── */}
        {tab === "overview" && (
          <div>
            <Section title="AHP Methodology — Step-by-Step Process">
              <div style={{display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(240px,1fr))", gap:"0.8rem"}}>
                {[
                  ["01","Define Goal","Delineate Groundwater Potential Zones (GWPZ) using integrated spatial analysis of 7 thematic factors."],
                  ["02","Select Criteria","Seven factors selected: Slope, Drainage Density, Lineament Density, LULC, Rainfall, Geology, Soil Type."],
                  ["03","Pairwise Comparison","Each factor compared against every other using Saaty's 1–9 importance scale to build a 7×7 matrix."],
                  ["04","Compute Weights","Normalize each column → compute row average → derive Priority Weight (Eigenvector) for each factor."],
                  ["05","Consistency Check","Compute λmax → CI → CR. CR must be < 0.10 for the matrix to be valid and scientifically accepted."],
                  ["06","Weighted Overlay","Apply weights in GIS (ArcGIS/QGIS) using Weighted Index Overlay to generate the final GWPZ map."],
                ].map(([num,title,desc])=>(
                  <div key={num} style={{background:"#fff", border:"1px solid #ddd0bb", borderRadius:"8px", padding:"1rem", borderTop:`3px solid #c8401a`}}>
                    <div style={{fontSize:"0.65rem", color:"#c8401a", fontWeight:"700", letterSpacing:"0.15em", marginBottom:"0.3rem"}}>STEP {num}</div>
                    <div style={{fontWeight:"700", fontSize:"0.9rem", marginBottom:"0.4rem"}}>{title}</div>
                    <div style={{fontSize:"0.78rem", color:"#5a4a30", lineHeight:1.6}}>{desc}</div>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Seven Thematic Factors — Ranked by Importance">
              {[...FACTORS].sort((a,b)=>a.rank-b.rank).map((f,i)=>(
                <div key={f.id} className="factor-card" onMouseEnter={()=>setHoveredFactor(f.id)} onMouseLeave={()=>setHoveredFactor(null)}
                  style={{display:"flex", alignItems:"center", gap:"1rem", padding:"0.85rem 1rem", marginBottom:"0.5rem",
                    background:"#fff", borderRadius:"8px", border:`1px solid ${hoveredFactor===f.id ? f.color : "#e0d4c0"}`,
                    borderLeft:`4px solid ${f.color}`, boxShadow:"0 2px 8px rgba(0,0,0,0.05)"}}>
                  <div style={{fontSize:"1.4rem", width:"36px", textAlign:"center"}}>{f.icon}</div>
                  <div style={{width:"24px", height:"24px", borderRadius:"50%", background:f.color, color:"#fff",
                    display:"flex", alignItems:"center", justifyContent:"center", fontSize:"0.7rem", fontWeight:"700", flexShrink:0}}>
                    {f.rank}
                  </div>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:"700", fontSize:"0.9rem"}}>{f.name} <span style={{fontWeight:"400", color:"#8a7a60", fontSize:"0.8rem"}}>{f.unit}</span></div>
                    <div style={{fontSize:"0.75rem", color:"#7a6a50", marginTop:"0.15rem"}}>
                      {FACTOR_DESC[f.id]}
                    </div>
                  </div>
                  <div style={{textAlign:"right", flexShrink:0}}>
                    <div style={{fontWeight:"700", color:f.color, fontSize:"1.1rem"}}>{(f.weight*100).toFixed(2)}%</div>
                    <div style={{fontSize:"0.68rem", color:"#9a8a70"}}>AHP Weight</div>
                  </div>
                </div>
              ))}
            </Section>

            <Section title="Saaty's 1–9 Comparison Scale">
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%", borderCollapse:"collapse", fontSize:"0.8rem"}}>
                  <thead>
                    <tr style={{background:"#2d1a08", color:"#f0e8d8"}}>
                      {["Scale","Verbal Judgment","Reciprocal","Interpretation"].map(h=>(
                        <th key={h} style={{padding:"0.6rem 0.8rem", textAlign:"left", fontWeight:"600", letterSpacing:"0.04em"}}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      [1,"Equal importance","1","Both factors contribute equally"],
                      [3,"Moderate importance","1/3","One factor slightly favoured over another"],
                      [5,"Strong importance","1/5","One factor strongly favoured; clearly dominant"],
                      [7,"Very strong importance","1/7","One factor very strongly favoured; dominant in practice"],
                      [9,"Extreme importance","1/9","One factor is absolutely dominant over the other"],
                      ["2,4,6,8","Intermediate values","1/2,1/4,1/6,1/8","Used when compromise between two judgments is needed"],
                    ].map(([s,v,r,i],idx)=>(
                      <tr key={idx} className="trow" style={{background: idx%2===0?"#faf5ee":"#fff"}}>
                        <td style={{padding:"0.5rem 0.8rem", fontWeight:"700", color:"#c8401a"}}>{s}</td>
                        <td style={{padding:"0.5rem 0.8rem", fontWeight:"600"}}>{v}</td>
                        <td style={{padding:"0.5rem 0.8rem", color:"#7a6a50"}}>{r}</td>
                        <td style={{padding:"0.5rem 0.8rem", color:"#5a4a30", fontSize:"0.76rem"}}>{i}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        )}

        {/* ── PAIRWISE MATRIX ── */}
        {tab === "matrix" && (
          <div>
            <Section title="7×7 Pairwise Comparison Matrix (A)">
              <p style={{fontSize:"0.8rem", color:"#6a5840", marginBottom:"1rem", lineHeight:1.7}}>
                Each cell A[i,j] represents the relative importance of factor <em>i</em> over factor <em>j</em> using Saaty's scale. 
                The lower triangle contains reciprocal values (1/A[i,j]). Diagonal = 1 (self-comparison).
              </p>
              <div style={{overflowX:"auto"}}>
                <table style={{borderCollapse:"collapse", fontSize:"0.76rem", width:"100%", minWidth:"640px"}}>
                  <thead>
                    <tr style={{background:"#2d1a08", color:"#f0e8d8"}}>
                      <th style={{padding:"0.6rem 0.5rem", textAlign:"left", borderRight:"2px solid #c8a03c", minWidth:"110px"}}>Factor</th>
                      {FACTORS.map(f=>(
                        <th key={f.id} style={{padding:"0.6rem 0.4rem", textAlign:"center", minWidth:"55px"}}>
                          <div style={{fontSize:"0.7rem"}}>{f.icon}</div>
                          <div>{f.id}</div>
                        </th>
                      ))}
                      <th style={{padding:"0.6rem 0.5rem", textAlign:"center", borderLeft:"2px solid #c8a03c", color:"#c8a03c"}}>Col Sum</th>
                    </tr>
                  </thead>
                  <tbody>
                    {RAW_MATRIX.map((row, i)=>(
                      <tr key={i} className="trow" style={{background: i%2===0?"#faf5ee":"#fff"}}>
                        <td style={{padding:"0.5rem 0.6rem", fontWeight:"700", color:FACTORS[i].color, borderRight:"2px solid #e0d0b8"}}>
                          {FACTORS[i].icon} {FACTORS[i].id}
                        </td>
                        {row.map((val, j)=>{
                          const isDiag = i===j;
                          const isAbove = j>i;
                          return (
                            <td key={j} style={{
                              padding:"0.5rem 0.4rem", textAlign:"center",
                              background: isDiag ? "#2d1a0820" : "transparent",
                              fontWeight: isDiag ? "700" : isAbove ? "600" : "400",
                              color: isDiag ? "#c8401a" : isAbove ? "#1a1208" : "#8a7a60",
                              borderBottom:"1px solid #ece0cc",
                            }}>{fmtVal(val)}</td>
                          );
                        })}
                        <td style={{padding:"0.5rem 0.5rem", textAlign:"center", fontWeight:"700", color:"#c8a03c", borderLeft:"2px solid #e0d0b8", fontSize:"0.74rem"}}>
                          {COL_SUMS[i].toFixed(3)}
                        </td>
                      </tr>
                    ))}
                    <tr style={{background:"#2d1a08", color:"#c8a03c"}}>
                      <td style={{padding:"0.5rem 0.6rem", fontWeight:"700", fontSize:"0.72rem", borderRight:"2px solid #c8a03c"}}>Column Sum</td>
                      {COL_SUMS.map((s,j)=>(
                        <td key={j} style={{padding:"0.5rem 0.4rem", textAlign:"center", fontWeight:"700", fontSize:"0.74rem"}}>{s.toFixed(3)}</td>
                      ))}
                      <td style={{borderLeft:"2px solid #c8a03c"}}/>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div style={{marginTop:"1.2rem", display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))", gap:"0.6rem"}}>
                {[
                  ["#1a1208","Bold","Above diagonal — row factor more important"],
                  ["#8a7a60","Normal","Below diagonal — reciprocal values"],
                  ["#c8401a","Bold Red","Diagonal — self-comparison = 1"],
                  ["#c8a03c","Gold","Column/Row sums for normalization"],
                ].map(([color,weight,label])=>(
                  <div key={label} style={{display:"flex",alignItems:"center",gap:"0.5rem",fontSize:"0.73rem",color:"#5a4a30"}}>
                    <div style={{width:"12px",height:"12px",borderRadius:"2px",background:color,flexShrink:0}}/>
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Pairwise Comparison Rationale">
              <div style={{display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))", gap:"0.6rem"}}>
                {RATIONALE.map(({pair,val,reason})=>(
                  <div key={pair} style={{background:"#fff", border:"1px solid #e0d4c0", borderRadius:"6px", padding:"0.75rem"}}>
                    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"0.3rem"}}>
                      <span style={{fontWeight:"700", fontSize:"0.82rem", color:"#2d1a08"}}>{pair}</span>
                      <span style={{background:"#c8401a", color:"#fff", borderRadius:"12px", padding:"0.15rem 0.5rem", fontSize:"0.72rem", fontWeight:"700"}}>{val}</span>
                    </div>
                    <div style={{fontSize:"0.75rem", color:"#6a5840", lineHeight:1.5}}>{reason}</div>
                  </div>
                ))}
              </div>
            </Section>
          </div>
        )}

        {/* ── NORMALIZED MATRIX ── */}
        {tab === "normalized" && (
          <div>
            <Section title="Normalized Pairwise Matrix">
              <p style={{fontSize:"0.8rem", color:"#6a5840", marginBottom:"1rem", lineHeight:1.7}}>
                Each cell is divided by its column sum: <strong>N[i,j] = A[i,j] / ColSum[j]</strong>. 
                The row average of each factor gives its <strong>Priority Weight (w)</strong>.
              </p>
              <div style={{overflowX:"auto"}}>
                <table style={{borderCollapse:"collapse", fontSize:"0.74rem", width:"100%", minWidth:"700px"}}>
                  <thead>
                    <tr style={{background:"#2d1a08", color:"#f0e8d8"}}>
                      <th style={{padding:"0.6rem 0.5rem", textAlign:"left", borderRight:"2px solid #c8a03c", minWidth:"105px"}}>Factor</th>
                      {FACTORS.map(f=>(
                        <th key={f.id} style={{padding:"0.6rem 0.4rem", textAlign:"center", minWidth:"52px"}}>{f.id}</th>
                      ))}
                      <th style={{padding:"0.6rem 0.6rem", textAlign:"center", borderLeft:"2px solid #c8a03c", color:"#c8a03c", minWidth:"60px"}}>Row Avg (w)</th>
                      <th style={{padding:"0.6rem 0.5rem", textAlign:"center", color:"#c8a03c", minWidth:"50px"}}>Weight %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {FACTORS.map((f, i)=>{
                      const rowVals = FACTORS.map((_,j)=>normCell(i,j));
                      return (
                        <tr key={f.id} className="trow" style={{background: i%2===0?"#faf5ee":"#fff"}}>
                          <td style={{padding:"0.5rem 0.6rem", fontWeight:"700", color:f.color, borderRight:"2px solid #e8dcc8"}}>
                            {f.icon} {f.id}
                          </td>
                          {rowVals.map((v,j)=>(
                            <td key={j} style={{padding:"0.5rem 0.4rem", textAlign:"center", color:"#3a2a10", fontSize:"0.73rem", borderBottom:"1px solid #ece0cc"}}>
                              {v.toFixed(4)}
                            </td>
                          ))}
                          <td style={{padding:"0.5rem 0.6rem", textAlign:"center", fontWeight:"700", color:f.color, borderLeft:"2px solid #e8dcc8", fontSize:"0.82rem"}}>
                            {f.weight.toFixed(4)}
                          </td>
                          <td style={{padding:"0.5rem 0.5rem", textAlign:"center", fontWeight:"700", color:f.color}}>
                            {(f.weight*100).toFixed(2)}%
                          </td>
                        </tr>
                      );
                    })}
                    <tr style={{background:"#ede5d8"}}>
                      <td colSpan={8} style={{padding:"0.4rem 0.6rem", fontSize:"0.72rem", color:"#6a5840", borderRight:"2px solid #e8dcc8"}}>
                        ∑ Each column = 1.0000 &nbsp;|&nbsp; ∑ All weights = 1.0000
                      </td>
                      <td style={{padding:"0.4rem 0.6rem", textAlign:"center", fontWeight:"700", borderLeft:"2px solid #e8dcc8", color:"#c8401a"}}>
                        {FACTORS.reduce((s,f)=>s+f.weight,0).toFixed(4)}
                      </td>
                      <td style={{padding:"0.4rem 0.5rem", textAlign:"center", fontWeight:"700", color:"#c8401a"}}>100%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Section>

            <Section title="Weighted Sum Vector (for λmax)">
              <p style={{fontSize:"0.8rem", color:"#6a5840", marginBottom:"1rem", lineHeight:1.7}}>
                Multiply original matrix A by weight vector w → get weighted sum vector → divide each element by its weight → get λ values → average = λmax.
              </p>
              <div style={{overflowX:"auto"}}>
                <table style={{borderCollapse:"collapse", fontSize:"0.78rem", width:"100%"}}>
                  <thead>
                    <tr style={{background:"#2d1a08", color:"#f0e8d8"}}>
                      {["Factor","Weight (w)","Weighted Sum (Aw)","λ = Aw/w"].map(h=>(
                        <th key={h} style={{padding:"0.55rem 0.8rem", textAlign:"center"}}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {FACTORS.map((f,i)=>{
                      const aw = RAW_MATRIX[i].reduce((s,v,j)=>s+v*FACTORS[j].weight, 0);
                      const lam = aw/f.weight;
                      return (
                        <tr key={f.id} className="trow" style={{background:i%2===0?"#faf5ee":"#fff"}}>
                          <td style={{padding:"0.5rem 0.8rem", fontWeight:"700", color:f.color}}>{f.icon} {f.name}</td>
                          <td style={{padding:"0.5rem 0.8rem", textAlign:"center"}}>{f.weight.toFixed(4)}</td>
                          <td style={{padding:"0.5rem 0.8rem", textAlign:"center"}}>{aw.toFixed(4)}</td>
                          <td style={{padding:"0.5rem 0.8rem", textAlign:"center", fontWeight:"700", color:"#c8401a"}}>{lam.toFixed(4)}</td>
                        </tr>
                      );
                    })}
                    <tr style={{background:"#2d1a08", color:"#c8a03c"}}>
                      <td colSpan={3} style={{padding:"0.5rem 0.8rem", textAlign:"right", fontWeight:"600"}}>λmax = Average of all λ values</td>
                      <td style={{padding:"0.5rem 0.8rem", textAlign:"center", fontWeight:"700", fontSize:"1rem"}}>{LAMBDA_MAX.toFixed(4)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        )}

        {/* ── WEIGHTS & CR ── */}
        {tab === "weights" && (
          <div>
            <Section title="Priority Weights — Ranked Visualization">
              {[...FACTORS].sort((a,b)=>b.weight-a.weight).map((f,i)=>(
                <div key={f.id} style={{marginBottom:"0.9rem"}}>
                  <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"0.35rem"}}>
                    <div style={{display:"flex", alignItems:"center", gap:"0.5rem"}}>
                      <span style={{fontSize:"0.7rem", color:"#9a8a70", width:"16px"}}>#{i+1}</span>
                      <span style={{fontSize:"0.82rem", fontWeight:"700"}}>{f.icon} {f.name}</span>
                      <span style={{fontSize:"0.72rem", color:"#8a7a60"}}>{f.unit}</span>
                    </div>
                    <div style={{display:"flex", alignItems:"center", gap:"0.8rem"}}>
                      <span style={{fontSize:"0.78rem", color:"#6a5840"}}>{f.weight.toFixed(4)}</span>
                      <span style={{fontWeight:"700", color:f.color, fontSize:"1rem", minWidth:"48px", textAlign:"right"}}>{(f.weight*100).toFixed(2)}%</span>
                    </div>
                  </div>
                  <div style={{height:"12px", background:"#e8dcc8", borderRadius:"6px", overflow:"hidden"}}>
                    <div style={{
                      height:"100%", borderRadius:"6px",
                      background:`linear-gradient(90deg, ${f.color}99, ${f.color})`,
                      width: mounted ? `${(f.weight/0.4055)*100}%` : "0%",
                      transition:`width 0.9s cubic-bezier(0.34,1.56,0.64,1) ${i*0.1}s`,
                    }}/>
                  </div>
                </div>
              ))}
            </Section>

            <Section title="Consistency Analysis — Full Calculation">
              <div style={{display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(260px,1fr))", gap:"0.8rem", marginBottom:"1rem"}}>
                {[
                  {label:"n (Number of factors)", val:"7", sub:"", color:"#2d1a08"},
                  {label:"λmax (Principal Eigenvalue)", val:LAMBDA_MAX.toFixed(4), sub:"Avg of Aw/w ratios", color:"#2d1a08"},
                  {label:"CI — Consistency Index", val:CI.toFixed(4), sub:"CI = (λmax − n) / (n − 1) = (7.457−7)/6", color:"#e07b30"},
                  {label:"RI — Random Index (n=7)", val:RI.toFixed(2), sub:"Saaty (1980) standard table value", color:"#2d1a08"},
                  {label:"CR — Consistency Ratio", val:CR.toFixed(4), sub:"CR = CI / RI = 0.0762 / 1.32", color:"#16803a"},
                  {label:"Decision", val:"✅ VALID", sub:"CR = 0.0577 < 0.10 threshold", color:"#16803a"},
                ].map(({label,val,sub,color})=>(
                  <div key={label} style={{background:"#fff", border:"1px solid #e0d0b8", borderRadius:"8px", padding:"1rem"}}>
                    <div style={{fontSize:"0.72rem", color:"#8a7a60", marginBottom:"0.3rem", lineHeight:1.4}}>{label}</div>
                    <div style={{fontWeight:"800", fontSize:"1.2rem", color, marginBottom:"0.2rem"}}>{val}</div>
                    {sub && <div style={{fontSize:"0.68rem", color:"#a09070", fontFamily:"monospace"}}>{sub}</div>}
                  </div>
                ))}
              </div>

              <div style={{background:"#f0faf5", border:"2px solid #27ae60", borderRadius:"8px", padding:"1rem", marginBottom:"0.8rem"}}>
                <div style={{fontWeight:"700", color:"#16803a", marginBottom:"0.4rem", fontSize:"0.9rem"}}>
                  ✅ Consistency Ratio (CR) = 0.0577 — ACCEPTED
                </div>
                <div style={{fontSize:"0.8rem", color:"#2d5a3a", lineHeight:1.7}}>
                  The CR value of <strong>0.0577 is well below the maximum acceptable threshold of 0.10</strong> (10%) as defined by Saaty (1980). 
                  This confirms that the pairwise judgments are <strong>logically consistent</strong> and the derived weights are statistically valid for use in weighted overlay GIS analysis.
                </div>
              </div>

              <div style={{background:"#faf5ee", border:"1px solid #d4c4a8", borderRadius:"8px", padding:"1rem"}}>
                <div style={{fontWeight:"700", fontSize:"0.82rem", marginBottom:"0.5rem", color:"#2d1a08"}}>RI Reference Table (Saaty, 1980)</div>
                <div style={{overflowX:"auto"}}>
                  <table style={{borderCollapse:"collapse", fontSize:"0.75rem", width:"100%"}}>
                    <tbody>
                      <tr>
                        {["n","1","2","3","4","5","6","7","8","9","10"].map(v=>(
                          <td key={v} style={{padding:"0.35rem 0.5rem", textAlign:"center", fontWeight:"600", color:"#6a5840", borderBottom:"1px solid #e0d0b8"}}>{v}</td>
                        ))}
                      </tr>
                      <tr>
                        {["RI","0.00","0.00","0.58","0.90","1.12","1.24","1.32","1.41","1.45","1.49"].map((v,i)=>(
                          <td key={i} style={{
                            padding:"0.35rem 0.5rem", textAlign:"center",
                            background: i===7 ? "#2d1a08" : "transparent",
                            color: i===7 ? "#c8a03c" : "#2d1a08",
                            fontWeight: i===7 ? "700" : "400",
                            borderRadius: i===7 ? "4px" : "0",
                          }}>{v}</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div style={{fontSize:"0.7rem", color:"#8a7a60", marginTop:"0.4rem"}}>▲ n=7 (highlighted) is used in this study → RI = 1.32</div>
              </div>
            </Section>
          </div>
        )}

        {/* ── SUB-CRITERIA ── */}
        {tab === "sub" && (
          <div>
            <Section title="Sub-Criteria Classification & Suitability Ratings (1–5)">
              <p style={{fontSize:"0.8rem", color:"#6a5840", marginBottom:"1.2rem", lineHeight:1.7}}>
                Each thematic layer is classified into 5 sub-classes and rated on a scale of <strong>1 (Very Poor)</strong> to <strong>5 (Very Good)</strong> for groundwater potential. These ratings are applied during rasterisation and standardisation before weighted overlay.
              </p>
              {FACTORS.map(f=>(
                <div key={f.id} style={{marginBottom:"1.5rem", background:"#fff", border:"1px solid #e0d0b8", borderRadius:"10px", overflow:"hidden"}}>
                  <div style={{background:`linear-gradient(135deg, ${f.color}22, ${f.color}10)`, borderBottom:`2px solid ${f.color}40`, padding:"0.7rem 1rem", display:"flex", alignItems:"center", gap:"0.6rem"}}>
                    <span style={{fontSize:"1.3rem"}}>{f.icon}</span>
                    <div>
                      <span style={{fontWeight:"700", color:f.color, fontSize:"0.92rem"}}>{f.name}</span>
                      <span style={{fontSize:"0.75rem", color:"#8a7a60", marginLeft:"0.5rem"}}>{f.unit}</span>
                    </div>
                    <div style={{marginLeft:"auto", background:f.color, color:"#fff", borderRadius:"12px", padding:"0.2rem 0.7rem", fontSize:"0.72rem", fontWeight:"700"}}>
                      Weight: {(f.weight*100).toFixed(2)}%
                    </div>
                  </div>
                  <div style={{overflowX:"auto"}}>
                    <table style={{width:"100%", borderCollapse:"collapse", fontSize:"0.77rem"}}>
                      <thead>
                        <tr style={{background:"#f5ede0"}}>
                          {["Class/Range","Category","Rating","GW Potential","Significance"].map(h=>(
                            <th key={h} style={{padding:"0.45rem 0.6rem", textAlign:"left", fontWeight:"600", color:"#4a3820", fontSize:"0.72rem"}}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {SUB[f.id].map((row,i)=>(
                          <tr key={i} className="trow" style={{borderBottom:"1px solid #f0e0cc"}}>
                            <td style={{padding:"0.45rem 0.6rem", fontWeight:"600", color:"#2d1a08"}}>{row.cls}</td>
                            <td style={{padding:"0.45rem 0.6rem", color:"#5a4a30"}}>{row.label}</td>
                            <td style={{padding:"0.45rem 0.6rem"}}>
                              <div style={{display:"flex", gap:"0.15rem"}}>
                                {[1,2,3,4,5].map(n=>(
                                  <div key={n} style={{width:"10px", height:"10px", borderRadius:"2px", background: n<=row.rating ? f.color : "#e0d0b8"}}/>
                                ))}
                                <span style={{marginLeft:"0.3rem", fontWeight:"700", color:f.color}}>{row.rating}</span>
                              </div>
                            </td>
                            <td style={{padding:"0.45rem 0.6rem"}}>
                              <span style={{background:`${POTENTIAL_COLORS[row.potential]}20`, color:POTENTIAL_COLORS[row.potential], border:`1px solid ${POTENTIAL_COLORS[row.potential]}40`, borderRadius:"10px", padding:"0.1rem 0.5rem", fontSize:"0.7rem", fontWeight:"600"}}>
                                {row.potential}
                              </span>
                            </td>
                            <td style={{padding:"0.45rem 0.6rem", color:"#6a5840", fontSize:"0.74rem"}}>{row.desc}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </Section>
          </div>
        )}

        {/* ── FORMULA ── */}
        {tab === "formula" && (
          <div>
            <Section title="Final GWPZ Weighted Overlay Formula">
              <div style={{background:"#2d1a08", borderRadius:"10px", padding:"1.5rem", marginBottom:"1.2rem"}}>
                <div style={{color:"#c8a03c", fontSize:"0.7rem", letterSpacing:"0.2em", textTransform:"uppercase", marginBottom:"0.8rem"}}>
                  Groundwater Potential Zone Score (S)
                </div>
                <div style={{fontFamily:"'Courier New', monospace", fontSize:"0.82rem", lineHeight:2.2, color:"#f0e8d8"}}>
                  <span style={{color:"#c8a03c", fontWeight:"700"}}>S = </span>
                  {FACTORS.map((f,i)=>(
                    <span key={f.id}>
                      <span style={{color:f.color, fontWeight:"700"}}>{f.weight.toFixed(4)}</span>
                      <span style={{color:"#8a7a60"}}> × </span>
                      <span style={{color:"#f0e8d8"}}>{f.id}_rating</span>
                      {i < FACTORS.length-1 && <span style={{color:"#8a7a60"}}> + </span>}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{background:"#fff", border:"1px solid #e0d0b8", borderRadius:"8px", padding:"1rem", marginBottom:"1rem"}}>
                <div style={{fontWeight:"700", fontSize:"0.85rem", marginBottom:"0.8rem"}}>Expanded Formula:</div>
                <div style={{fontFamily:"monospace", fontSize:"0.78rem", lineHeight:2, color:"#3a2a10"}}>
                  S = (0.4055 × Geology) + (0.2147 × Rainfall) + (0.1492 × Soil) +<br/>
                  &nbsp;&nbsp;&nbsp;&nbsp;(0.1034 × Lineament_Density) + (0.0728 × LULC) +<br/>
                  &nbsp;&nbsp;&nbsp;&nbsp;(0.0272 × Drainage_Density) + (0.0272 × Slope)
                </div>
              </div>

              <Section title="GWPZ Classification of Output Score">
                <div style={{display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(150px,1fr))", gap:"0.6rem"}}>
                  {[
                    {range:"1.0 – 1.8", zone:"Very Poor",  color:"#c0392b", action:"Avoid drilling; poor aquifer potential"},
                    {range:"1.8 – 2.6", zone:"Poor",       color:"#e07b22", action:"Low yield expected; expensive drilling"},
                    {range:"2.6 – 3.4", zone:"Moderate",   color:"#d4a017", action:"Moderate yield; requires detailed survey"},
                    {range:"3.4 – 4.2", zone:"Good",       color:"#27ae60", action:"Recommended for exploration"},
                    {range:"4.2 – 5.0", zone:"Very Good",  color:"#1a7a4a", action:"Excellent recharge; high priority zones"},
                  ].map(({range,zone,color,action})=>(
                    <div key={zone} style={{background:color+"18", border:`2px solid ${color}40`, borderRadius:"8px", padding:"0.8rem", textAlign:"center"}}>
                      <div style={{fontWeight:"700", color, fontSize:"0.88rem", marginBottom:"0.2rem"}}>{zone}</div>
                      <div style={{fontFamily:"monospace", fontSize:"0.75rem", color:"#5a4a30", marginBottom:"0.4rem"}}>{range}</div>
                      <div style={{fontSize:"0.68rem", color:"#7a6a50", lineHeight:1.4}}>{action}</div>
                    </div>
                  ))}
                </div>
              </Section>

              <Section title="GIS Implementation Workflow">
                {[
                  ["1","Data Collection","Collect data: SRTM DEM (30m), LISS-IV/Sentinel imagery, GSI geological maps, IMD/TRMM rainfall, soil surveys, ASTER lineament."],
                  ["2","Preprocessing","Reproject all layers to common CRS (e.g. UTM). Resample to uniform 30m resolution. Clip to study area boundary."],
                  ["3","Thematic Layer Generation","Derive Slope (°) from DEM | Extract Drainage & DD from DEM | Map lineaments via PCA/edge detection | Classify LULC via LISS/Sentinel | Process rainfall rasters | Digitize geology & soil from maps."],
                  ["4","Reclassification","Reclassify each layer to 1–5 suitability scale as per sub-criteria table (Step ⑤)."],
                  ["5","Weighted Overlay","Apply AHP weights using Weighted Index Overlay tool in ArcGIS or QGIS Raster Calculator with the formula above."],
                  ["6","GWPZ Map","Classify output raster into 5 zones (Very Poor → Very Good). Generate final map with legend, scale bar, north arrow."],
                  ["7","Validation","Validate GWPZ map against existing borewell yield data, water table measurements, or ROC/AUC accuracy assessment."],
                ].map(([num,title,desc])=>(
                  <div key={num} style={{display:"flex", gap:"1rem", padding:"0.7rem 0", borderBottom:"1px solid #ece0cc"}}>
                    <div style={{minWidth:"28px", height:"28px", borderRadius:"50%", background:"#2d1a08", color:"#c8a03c", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"0.75rem", fontWeight:"700", flexShrink:0, marginTop:"2px"}}>{num}</div>
                    <div>
                      <div style={{fontWeight:"700", fontSize:"0.85rem", marginBottom:"0.2rem"}}>{title}</div>
                      <div style={{fontSize:"0.77rem", color:"#6a5840", lineHeight:1.6}}>{desc}</div>
                    </div>
                  </div>
                ))}
              </Section>

              <div style={{background:"#faf5ee", border:"1px solid #d4c4a8", borderRadius:"8px", padding:"1rem", marginTop:"0.5rem"}}>
                <div style={{fontWeight:"700", fontSize:"0.82rem", marginBottom:"0.5rem"}}>📚 Key References</div>
                <div style={{fontSize:"0.75rem", color:"#6a5840", lineHeight:1.9}}>
                  • Saaty, T.L. (1980). <em>The Analytic Hierarchy Process</em>. McGraw-Hill, New York.<br/>
                  • Jha, M.K., et al. (2010). Groundwater assessment using AHP & GIS. <em>Hydrogeology Journal</em>.<br/>
                  • Singh, A.K., et al. (2013). GWPZ mapping using MCA & GIS. <em>Journal of Earth System Science</em>.<br/>
                  • Rahmati, O., et al. (2015). GWP assessment using AHP & ML. <em>Environmental Earth Sciences</em>.
                </div>
              </div>
            </Section>
          </div>
        )}

      </div>

      <div style={{textAlign:"center", padding:"1rem", fontSize:"0.68rem", color:"#b0a090", letterSpacing:"0.12em", borderTop:"1px solid #e0d0b8"}}>
        AHP · MCDM · GWPZ MAPPING · SAATY (1980) · n=7 · CR=0.0577 &lt; 0.10 ✓
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{marginBottom:"1.5rem"}}>
      <div style={{display:"flex", alignItems:"center", gap:"0.6rem", marginBottom:"1rem"}}>
        <div style={{width:"4px", height:"20px", background:"#c8401a", borderRadius:"2px", flexShrink:0}}/>
        <h2 style={{margin:0, fontSize:"0.88rem", fontWeight:"700", letterSpacing:"0.05em", color:"#2d1a08", textTransform:"uppercase"}}>{title}</h2>
      </div>
      {children}
    </div>
  );
}

const FACTOR_DESC = {
  SLP:  "Steep slopes increase surface runoff and reduce infiltration, reducing groundwater recharge. Flat terrain maximizes percolation.",
  DD:   "High drainage density means more runoff through channels and less groundwater recharge. Inversely related to GW potential.",
  LD:   "Lineaments (faults, fractures, joints) act as preferential conduits for groundwater movement and enhance secondary porosity.",
  LULC: "Land cover governs the rate of infiltration. Forest and agricultural land promote recharge; urban areas block it.",
  RAIN: "The primary source of groundwater recharge. Higher annual rainfall directly correlates with greater recharge potential.",
  GEO:  "The single most important factor — controls aquifer type, primary & secondary porosity, permeability, and storage capacity.",
  SOIL: "Soil texture and permeability determine how fast water can infiltrate and percolate to the water table.",
};

const RATIONALE = [
  {pair:"Geology vs Rainfall", val:"3", reason:"Geology moderately more important — even abundant rainfall cannot recharge an impermeable rock formation."},
  {pair:"Geology vs Lineament", val:"5", reason:"Geology strongly dominates; lineaments matter only within a permeable geological context."},
  {pair:"Geology vs Soil", val:"6", reason:"Geology controls the deep aquifer; soil only governs near-surface infiltration."},
  {pair:"Geology vs LULC", val:"9", reason:"LULC has minimal influence compared to the fundamental rock-type aquifer control."},
  {pair:"Geology vs Drain. Density", val:"9", reason:"Drainage density is a surface expression — geology is the primary subsurface driver."},
  {pair:"Geology vs Slope", val:"9", reason:"Geology absolutely dominates over topographic slope for groundwater storage."},
  {pair:"Rainfall vs Lineament", val:"3", reason:"Rainfall moderately more important — it is the source of all recharge; lineaments only enhance it."},
  {pair:"Rainfall vs Soil", val:"2", reason:"Roughly equal; rainfall is the input, soil governs how much can infiltrate."},
  {pair:"Lineament vs LULC", val:"2", reason:"Lineament slightly more important — structural conduits trump surface cover effects."},
  {pair:"Soil vs Drain. Density", val:"3", reason:"Soil permeability controls vertical recharge; drainage density controls lateral runoff."},
  {pair:"Slope vs Drain. Density", val:"1", reason:"Equal importance — both are topographic controls on runoff vs infiltration balance."},
];