import { useState, useEffect, useRef, createContext, useContext } from "react";

const ThemeContext = createContext();
const useTheme = () => useContext(ThemeContext);

const ABB = {
  red: "#FF000F",
  redDark: "#CC000C",
  redLight: "#FF334040",
  black: "#000000",
  white: "#FFFFFF",
};

const themes = {
  light: {
    bg: "#FAFAFA",
    surface: "#FFFFFF",
    surfaceAlt: "#F5F5F5",
    border: "#E0E0E0",
    borderSubtle: "#EEEEEE",
    text: "#1A1A1A",
    textSecondary: "#6B6B6B",
    textTertiary: "#999999",
    codeBg: "#F0F0F0",
    codeText: "#1A1A1A",
    cardShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
    accent: ABB.red,
    accentBg: "#FF000F08",
    accentBorder: "#FF000F20",
    navBg: "#FFFFFF",
    headerBg: "#FFFFFF",
    matrixHigh: "rgba(255,0,15,",
    barColors: ["#FF000F", "#1A1A1A", "#6B6B6B", "#999999", "#CCCCCC"],
    tagBg: ["#FF000F12", "#E8E8E8", "#F0E6FF", "#E6F7ED", "#FFF3E6"],
    tagColor: ["#FF000F", "#1A1A1A", "#7C3AED", "#059669", "#D97706"],
    successColor: "#059669",
    successBg: "#ECFDF5",
    warningColor: "#D97706",
    warningBg: "#FFFBEB",
    errorColor: "#FF000F",
    errorBg: "#FFF5F5",
    infoColor: "#2563EB",
    infoBg: "#EFF6FF",
  },
  dark: {
    bg: "#0A0A0A",
    surface: "#141414",
    surfaceAlt: "#1C1C1C",
    border: "#2A2A2A",
    borderSubtle: "#222222",
    text: "#F0F0F0",
    textSecondary: "#A0A0A0",
    textTertiary: "#666666",
    codeBg: "#1A1A1A",
    codeText: "#E0E0E0",
    cardShadow: "0 1px 3px rgba(0,0,0,0.3)",
    accent: ABB.red,
    accentBg: "#FF000F10",
    accentBorder: "#FF000F30",
    navBg: "#0F0F0F",
    headerBg: "#0F0F0F",
    matrixHigh: "rgba(255,0,15,",
    barColors: ["#FF000F", "#E0E0E0", "#A78BFA", "#34D399", "#FBBF24"],
    tagBg: ["#FF000F18", "#2A2A2A", "#2D1B69", "#064E3B", "#5C3D1A"],
    tagColor: ["#FF000F", "#E0E0E0", "#C4B5FD", "#6EE7B7", "#FCD34D"],
    successColor: "#34D399",
    successBg: "#064E3B22",
    warningColor: "#FBBF24",
    warningBg: "#5C3D1A22",
    errorColor: "#FF000F",
    errorBg: "#FF000F15",
    infoColor: "#60A5FA",
    infoBg: "#1E3A5F22",
  },
};

const SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "tokenization", label: "Tokenizzazione" },
  { id: "embedding", label: "Embedding" },
  { id: "attention", label: "Self-Attention" },
  { id: "ffn", label: "Feed-Forward" },
  { id: "layers", label: "Layer & Scala" },
  { id: "generation", label: "Generazione" },
  { id: "sampling", label: "Sampling" },
  { id: "training", label: "Training" },
  { id: "limits", label: "Limiti & Forze" },
];

function AnimNum({ target, duration = 1200 }) {
  const [val, setVal] = useState(0);
  const ref = useRef();
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      setVal(Math.floor(p * target));
      if (p < 1) ref.current = requestAnimationFrame(step);
    };
    ref.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(ref.current);
  }, [target, duration]);
  return <span>{val.toLocaleString()}</span>;
}

function Card({ children, style }) {
  const t = useTheme();
  return (
    <div style={{
      background: t.surface, border: `1px solid ${t.border}`, borderRadius: 8,
      padding: 20, boxShadow: t.cardShadow, ...style,
    }}>{children}</div>
  );
}

function CodeBlock({ children, style }) {
  const t = useTheme();
  return (
    <div style={{
      background: t.codeBg, borderRadius: 8, padding: "16px 20px", marginTop: 16,
      border: `1px solid ${t.borderSubtle}`, fontFamily: "'ABB Mono', 'JetBrains Mono', monospace",
      fontSize: 16, color: t.codeText, ...style,
    }}>{children}</div>
  );
}

function Pill({ children, index = 0 }) {
  const t = useTheme();
  return (
    <span style={{
      display: "inline-block", background: t.tagBg[index % 5],
      color: t.tagColor[index % 5], padding: "3px 10px", borderRadius: 4,
      fontSize: 14, fontWeight: 600, letterSpacing: "0.02em",
    }}>{children}</span>
  );
}

function InfoPopup({ title = "Info", children, width = 340 }) {
  const t = useTheme();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onMouseDown = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const onKeyDown = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onMouseDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onMouseDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <span ref={ref} style={{ position: "relative", display: "inline-flex", alignItems: "center", marginLeft: 6, verticalAlign: "middle" }}>
      <button
        type="button"
        aria-label={`Apri spiegazione: ${title}`}
        onClick={() => setOpen((v) => !v)}
        style={{
          width: 18, height: 18, borderRadius: "50%",
          border: `1px solid ${open ? t.accent : t.border}`, background: open ? t.accentBg : t.surfaceAlt,
          color: open ? t.accent : t.textSecondary, cursor: "pointer", fontSize: 11, fontWeight: 700,
          display: "inline-flex", alignItems: "center", justifyContent: "center", lineHeight: 1,
        }}
      >
        i
      </button>
      {open && (
        <div style={{
          position: "absolute", top: 24, right: 0, width,
          maxWidth: "calc(100vw - 32px)",
          background: t.surface, border: `1px solid ${t.border}`, borderRadius: 8,
          boxShadow: t.cardShadow, padding: 12, zIndex: 200,
        }}>
          <div style={{ color: t.text, fontWeight: 700, fontSize: 14, marginBottom: 6 }}>{title}</div>
          <div style={{ color: t.textSecondary, fontSize: 14, lineHeight: 1.6 }}>{children}</div>
        </div>
      )}
    </span>
  );
}

// ─── INTERACTIVE DEMOS ───

function TokenDemo() {
  const t = useTheme();
  const [step, setStep] = useState(0);
  const tokens = ["Come", " funzion", "a", " l'", "ener", "gia", " sol", "are", "?"];
  useEffect(() => {
    const i = setInterval(() => setStep((s) => (s + 1) % (tokens.length + 2)), 550);
    return () => clearInterval(i);
  }, []);

  return (
    <CodeBlock>
      <div style={{ color: t.textSecondary, marginBottom: 10, fontSize: 15 }}>
        Input: <span style={{ color: t.text }}>"Come funziona l'energia solare?"</span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {tokens.map((tk, i) => (
          <span key={i} style={{
            border: `1.5px solid ${i < step ? t.accent : t.border}`,
            background: i < step ? t.accentBg : "transparent",
            color: i < step ? t.accent : t.textTertiary,
            padding: "5px 11px", borderRadius: 6, fontSize: 15,
            fontFamily: "'JetBrains Mono', monospace",
            transition: "all 0.25s ease", fontWeight: i < step ? 600 : 400,
          }}>{tk}</span>
        ))}
      </div>
      <div style={{ color: t.textTertiary, fontSize: 14, marginTop: 10 }}>
        {step > 0 ? `${Math.min(step, tokens.length)} di ${tokens.length} token identificati` : "Analisi in corso..."}
      </div>
    </CodeBlock>
  );
}

function EmbeddingViz() {
  const t = useTheme();
  const dims = [
    { label: "Semantica", vals: [0.82, -0.14, 0.67, 0.91, 0.23] },
    { label: "Sintassi", vals: [-0.33, 0.78, 0.12, -0.56, 0.44] },
    { label: "Contesto", vals: [0.15, 0.55, -0.88, 0.34, -0.71] },
    { label: "Dominio", vals: [0.91, 0.02, 0.45, -0.22, 0.68] },
  ];
  const tokens = ["Come", "funzion", "ener", "gia", "sol"];

  return (
    <CodeBlock>
      <div style={{ display: "flex", gap: 4, marginBottom: 10, paddingLeft: 80 }}>
        {tokens.map((tk, i) => (
          <div key={i} style={{
            width: 64, textAlign: "center", fontSize: 13, fontWeight: 600,
            color: i === 0 ? t.accent : t.textSecondary, letterSpacing: "0.03em",
          }}>{tk}</div>
        ))}
      </div>
      {dims.map((d, di) => (
        <div key={di} style={{ display: "flex", alignItems: "center", marginBottom: 5 }}>
          <div style={{ width: 76, fontSize: 13, color: t.textTertiary, textAlign: "right", paddingRight: 8 }}>
            {d.label}
          </div>
          {d.vals.map((v, vi) => (
            <div key={vi} style={{
              width: 64, height: 30, display: "flex", alignItems: "center", justifyContent: "center",
              background: v > 0 ? `rgba(5,150,105,${Math.abs(v) * 0.35})` : `rgba(255,0,15,${Math.abs(v) * 0.3})`,
              borderRadius: 4, margin: "0 2px", fontSize: 13, color: t.text,
            }}>{v > 0 ? "+" : ""}{v.toFixed(2)}</div>
          ))}
        </div>
      ))}
      <div style={{ color: t.textTertiary, fontSize: 13, marginTop: 10, fontStyle: "italic" }}>
        Realtà: ~4.096 dimensioni per token. Qui ne mostriamo solo 4 per chiarezza.
      </div>
    </CodeBlock>
  );
}

function AttentionMatrix() {
  const t = useTheme();
  const words = ["Come", "funziona", "energia", "solare", "?"];
  const matrix = [
    [0.15, 0.35, 0.20, 0.20, 0.10],
    [0.10, 0.10, 0.40, 0.30, 0.10],
    [0.05, 0.15, 0.15, 0.55, 0.10],
    [0.05, 0.10, 0.60, 0.15, 0.10],
    [0.20, 0.30, 0.20, 0.20, 0.10],
  ];
  const [hovR, setHovR] = useState(null);
  const [hovC, setHovC] = useState(null);

  return (
    <CodeBlock>
      <div style={{ display: "inline-block" }}>
        <div style={{ display: "flex", gap: 2, marginBottom: 4, paddingLeft: 82 }}>
          {words.map((w, i) => (
            <div key={i} style={{
              width: 66, textAlign: "center", fontSize: 13, fontWeight: hovC === i ? 700 : 500,
              color: hovC === i ? t.accent : t.textTertiary, transition: "all 0.15s",
            }}>{w}</div>
          ))}
        </div>
        {matrix.map((row, ri) => (
          <div key={ri} style={{ display: "flex", alignItems: "center", gap: 2, marginBottom: 2 }}>
            <div style={{
              width: 78, textAlign: "right", paddingRight: 6, fontSize: 14,
              color: hovR === ri ? t.accent : t.textSecondary,
              fontWeight: hovR === ri ? 700 : 500, transition: "all 0.15s",
            }}>{words[ri]}</div>
            {row.map((v, ci) => (
              <div key={ci}
                onMouseEnter={() => { setHovR(ri); setHovC(ci); }}
                onMouseLeave={() => { setHovR(null); setHovC(null); }}
                style={{
                  width: 66, height: 34, display: "flex", alignItems: "center", justifyContent: "center",
                  background: `${t.matrixHigh}${v * 0.9})`,
                  borderRadius: 4, cursor: "pointer", fontSize: 14,
                  color: v > 0.3 ? "#fff" : t.textSecondary, fontWeight: v > 0.3 ? 700 : 400,
                  border: (hovR === ri && hovC === ci) ? `2px solid ${t.accent}` : "2px solid transparent",
                  transition: "all 0.12s",
                }}>{(v * 100).toFixed(0)}%</div>
            ))}
          </div>
        ))}
      </div>
      <div style={{ marginTop: 12, fontSize: 15, color: t.textSecondary, minHeight: 20 }}>
        {hovR !== null && hovC !== null ? (
          <>
            <strong style={{ color: t.accent }}>"{words[hovR]}"</strong> presta il{" "}
            <strong style={{ color: t.text }}>{(matrix[hovR][hovC] * 100).toFixed(0)}%</strong>{" "}
            della sua attenzione a <strong style={{ color: t.accent }}>"{words[hovC]}"</strong>
          </>
        ) : (
          <span style={{ color: t.textTertiary }}>Hover sulle celle per esplorare i pesi di attenzione</span>
        )}
      </div>
    </CodeBlock>
  );
}

function GenerationDemo() {
  const t = useTheme();
  const fullTokens = [
    { t: "L'", p: 0.88 }, { t: "energia", p: 0.92 }, { t: " solare", p: 0.85 },
    { t: " funziona", p: 0.78 }, { t: " convertendo", p: 0.72 },
    { t: " la", p: 0.90 }, { t: " luce", p: 0.83 }, { t: " del", p: 0.91 },
    { t: " sole", p: 0.87 }, { t: " in", p: 0.93 }, { t: " elettricità", p: 0.81 },
    { t: ".", p: 0.95 },
  ];
  const [count, setCount] = useState(0);
  useEffect(() => {
    const i = setInterval(() => setCount((c) => (c >= fullTokens.length ? 0 : c + 1)), 480);
    return () => clearInterval(i);
  }, []);

  return (
    <CodeBlock>
      <div style={{ minHeight: 44, fontSize: 17, lineHeight: 1.6 }}>
        {fullTokens.slice(0, count).map((tk, i) => (
          <span key={i} style={{
            color: i === count - 1 ? t.accent : t.text,
            background: i === count - 1 ? t.accentBg : "transparent",
            borderRadius: 3, padding: "1px 0", transition: "all 0.2s",
          }}>{tk.t}</span>
        ))}
        {count < fullTokens.length && (
          <span style={{
            display: "inline-block", width: 2, height: 16, background: t.accent,
            marginLeft: 1, verticalAlign: "text-bottom", animation: "blink 1s infinite",
          }} />
        )}
      </div>
      {count > 0 && count <= fullTokens.length && (
        <div style={{
          marginTop: 12, padding: "8px 12px", background: t.surfaceAlt, borderRadius: 6,
          display: "flex", alignItems: "center", gap: 12, border: `1px solid ${t.borderSubtle}`,
        }}>
          <span style={{ fontSize: 13, color: t.textTertiary, whiteSpace: "nowrap" }}>
            Token #{Math.min(count, fullTokens.length)}
          </span>
          <div style={{ flex: 1, height: 6, background: t.border, borderRadius: 3, overflow: "hidden" }}>
            <div style={{
              width: `${fullTokens[Math.min(count, fullTokens.length) - 1].p * 100}%`,
              height: "100%", background: t.accent, borderRadius: 3, transition: "width 0.25s ease",
            }} />
          </div>
          <span style={{ fontSize: 14, color: t.accent, fontWeight: 600, whiteSpace: "nowrap" }}>
            {(fullTokens[Math.min(count, fullTokens.length) - 1].p * 100).toFixed(0)}%
          </span>
        </div>
      )}
    </CodeBlock>
  );
}

function SamplingDemo() {
  const t = useTheme();
  const [temp, setTemp] = useState(0.7);
  const candidates = [
    { t: "convertendo", base: 0.72 },
    { t: "trasformando", base: 0.18 },
    { t: "catturando", base: 0.06 },
    { t: "usando", base: 0.03 },
    { t: "assorbendo", base: 0.01 },
  ];
  const adjusted = candidates.map((c) => ({ ...c, adj: Math.exp(Math.log(c.base + 0.001) / (temp + 0.01)) }));
  const sum = adjusted.reduce((s, c) => s + c.adj, 0);
  const probs = adjusted.map((c) => ({ ...c, prob: c.adj / sum }));
  const maxP = Math.max(...probs.map((p) => p.prob));

  return (
    <CodeBlock>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
        <label style={{ color: t.textSecondary, fontSize: 15, whiteSpace: "nowrap" }}>Temperatura</label>
        <input type="range" min="0.05" max="2" step="0.05" value={temp}
          onChange={(e) => setTemp(parseFloat(e.target.value))}
          style={{ flex: 1, accentColor: t.accent }} />
        <span style={{
          fontWeight: 700, fontSize: 20, color: t.accent, minWidth: 44, textAlign: "right",
        }}>{temp.toFixed(2)}</span>
      </div>
      {probs.map((c, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 7 }}>
          <div style={{ width: 110, textAlign: "right", fontSize: 14, color: i === 0 ? t.text : t.textSecondary }}>
            {c.t}
          </div>
          <div style={{ flex: 1, height: 20, background: t.surfaceAlt, borderRadius: 4, overflow: "hidden", border: `1px solid ${t.borderSubtle}` }}>
            <div style={{
              width: `${(c.prob / maxP) * 100}%`, height: "100%",
              background: i === 0 ? t.accent : t.barColors[i],
              borderRadius: 4, transition: "width 0.3s ease",
              opacity: i === 0 ? 1 : 0.5,
            }} />
          </div>
          <div style={{
            width: 48, fontSize: 14, fontWeight: 600, textAlign: "right",
            color: i === 0 ? t.accent : t.textSecondary,
          }}>{(c.prob * 100).toFixed(1)}%</div>
        </div>
      ))}
      <div style={{
        marginTop: 14, padding: "10px 14px", borderRadius: 6,
        background: t.surfaceAlt, border: `1px solid ${t.borderSubtle}`,
        fontSize: 14, color: t.textSecondary, lineHeight: 1.5,
      }}>
        {temp < 0.3
          ? "Molto fredda — quasi deterministico. Ideale per task precisi e ripetibili."
          : temp < 0.8
          ? "Bilanciata — coerente con variabilità controllata. Il range standard per assistenti AI."
          : temp < 1.2
          ? "Calda — esplora scelte meno probabili. Buona per brainstorming e creatività."
          : "Molto calda — risposte imprevedibili. Le parole rare competono con quelle comuni."}
      </div>
    </CodeBlock>
  );
}

// ─── SECTION CONTENT ───

function SectionContent({ id }) {
  const t = useTheme();
  const P = ({ children }) => <p style={{ color: t.textSecondary, lineHeight: 1.8, fontSize: 16, marginBottom: 16 }}>{children}</p>;
  const Strong = ({ children, accent }) => <strong style={{ color: accent ? t.accent : t.text }}>{children}</strong>;
  const InfoBox = ({ title, children, variant = "default" }) => {
    const colors = {
      default: { bg: t.surfaceAlt, border: t.border, title: t.text },
      accent: { bg: t.accentBg, border: t.accentBorder, title: t.accent },
      success: { bg: t.successBg, border: t.successColor + "33", title: t.successColor },
      warning: { bg: t.warningBg, border: t.warningColor + "33", title: t.warningColor },
    };
    const c = colors[variant];
    return (
      <div style={{ padding: 16, background: c.bg, border: `1px solid ${c.border}`, borderRadius: 8, marginTop: 16 }}>
        {title && <div style={{ color: c.title, fontWeight: 700, fontSize: 15, marginBottom: 6, letterSpacing: "0.02em" }}>{title}</div>}
        <div style={{ color: t.textSecondary, fontSize: 15, lineHeight: 1.7 }}>{children}</div>
      </div>
    );
  };
  const Grid = ({ children, cols = 2 }) => (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 12, marginTop: 16 }}>
      {children}
    </div>
  );
  const GridCard = ({ title, children, index = 0 }) => (
    <div style={{ background: t.surfaceAlt, borderRadius: 8, padding: 14, border: `1px solid ${t.borderSubtle}` }}>
      <div style={{ color: t.tagColor[index % 5], fontWeight: 700, fontSize: 15, marginBottom: 6 }}>{title}</div>
      <div style={{ color: t.textSecondary, fontSize: 14, lineHeight: 1.6 }}>{children}</div>
    </div>
  );

  switch (id) {
    case "overview":
      return (
        <>
          <P>
            Un <Strong>Large Language Model (LLM)</Strong> è una rete neurale basata sull'architettura Transformer, addestrata su enormi quantità di testo per{" "}
            <Strong accent>predire il prossimo token</Strong> dato un contesto. Questa operazione apparentemente semplice,
            ripetuta miliardi di volte durante il training, produce rappresentazioni sofisticate del linguaggio.
          </P>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, marginBottom: 20 }}>
            {[
              { label: "Parametri (GPT-4, MoE)", value: 1800, unit: "miliardi totali*" },
              { label: "Token di training", value: 13000, unit: "miliardi (con epoche)" },
              { label: "Dimensioni embedding", value: 4096, display: "4.096", unit: "range tipico: 4.096-12.288" },
              { label: "Vocabolario", value: 100000, unit: "token (BPE)" },
            ].map((s, i) => (
              <div key={i} style={{
                background: t.surfaceAlt, borderRadius: 8, padding: 14,
                borderLeft: `3px solid ${i === 0 ? t.accent : t.border}`,
                border: `1px solid ${t.borderSubtle}`,
              }}>
                <div style={{ fontSize: 26, fontWeight: 800, color: i === 0 ? t.accent : t.text, fontFamily: "'JetBrains Mono', monospace" }}>
                  {s.display ?? <AnimNum target={s.value} />}
                </div>
                <div style={{ fontSize: 13, color: t.textTertiary }}>{s.unit}</div>
                <div style={{ fontSize: 14, color: t.textSecondary, marginTop: 3 }}>{s.label}</div>
              </div>
            ))}
          </div>
          <InfoBox title="LA PIPELINE COMPLETA" variant="accent">
            <div style={{ fontSize: 13, color: t.textTertiary, marginBottom: 8 }}>
              *GPT-4 usa un'architettura Mixture of Experts (MoE) con ~1.8T parametri totali distribuiti su 16 esperti, ma solo ~280B sono attivi per ogni singola predizione. I 13T token di training includono ripetizioni (2 epoche per testo, 4 per codice).
              <InfoPopup title="Come leggere questi numeri">
                Mixture of Experts vuol dire che il modello ha molti sottoblocchi specializzati ("esperti"), ma a ogni token ne attiva solo alcuni.
                Quindi 1.8T sono i parametri totali disponibili, mentre ~280B sono quelli davvero usati in quella singola predizione.
                Le epoche indicano quante volte lo stesso dato viene rivisto: se il dataset viene ripassato più volte, i token "contati" aumentano.
              </InfoPopup>
            </div>
            Testo → <Pill index={0}>Tokenizzazione</Pill> → <Pill index={1}>Embedding</Pill> → <Pill index={0}>Self-Attention</Pill>{" "}
            (×N layer) → <Pill index={2}>Feed-Forward</Pill> (×N layer) → <Pill index={3}>Predizione probabilità</Pill> → <Pill index={4}>Sampling</Pill>{" "}
            → Token output → <span style={{ color: t.textTertiary }}>ripeti</span>
          </InfoBox>
        </>
      );

    case "tokenization":
      return (
        <>
          <P>
            Il primo passo è la <Strong accent>tokenizzazione</Strong>: il testo viene spezzato in sotto-unità chiamate{" "}
            <Strong>token</Strong> usando algoritmi come <Strong>BPE</Strong> (Byte-Pair Encoding). Non parole intere, non singoli caratteri.
            <InfoPopup title="BPE in parole semplici">
              BPE parte dai caratteri e costruisce pezzi ricorrenti. Se una sequenza compare spesso (es. "zione"), la unisce in un token unico.
              Così il vocabolario resta gestibile e il modello capisce anche parole nuove combinando pezzi noti.
            </InfoPopup>
          </P>
          <TokenDemo />
          <Grid>
            <GridCard title="PERCHÉ NON PAROLE INTERE?" index={0}>
              Un vocabolario di parole intere sarebbe enorme e non gestirebbe parole mai viste. I sub-word token bilanciano vocabolario compatto (~100K) e flessibilità.
            </GridCard>
            <GridCard title="IMPATTO PRATICO" index={3}>
              L'italiano usa ~1.3× più token dell'inglese per lo stesso testo. Questo impatta costi API (si paga per token) e lunghezza del contesto elaborabile.
            </GridCard>
          </Grid>
        </>
      );

    case "embedding":
      return (
        <>
          <P>
            Ogni token diventa un <Strong accent>vettore numerico</Strong> in uno spazio ad alta dimensionalità (es. 4.096 dimensioni, con range tipico 4.096-12.288).
            Questo è il <Strong>linguaggio interno</Strong> del modello: numeri che codificano relazioni semantiche, sintattiche e contestuali.
            <InfoPopup title="Cosa vuol dire 4.096 dimensioni">
              Ogni token viene rappresentato da 4.096 numeri. Non sono 4.096 significati separati, ma coordinate che insieme descrivono
              il contesto del token. Più dimensioni danno più sfumature, ma aumentano costo e memoria.
            </InfoPopup>
          </P>
          <EmbeddingViz />
          <InfoBox title="PERCHÉ 4.096 DIMENSIONI?" variant="accent">
            È un <Strong>iperparametro architetturale</Strong> — scelto dai progettisti, non appreso dal modello.
            Più dimensioni = più sfumature, ma costo computazionale quadratico nell'Attention. La scelta segue{" "}
            <Strong accent>scaling laws</Strong> empiriche. GPT-3: 12.288 dim. LLaMA-7B: 4.096. LLaMA-70B: 8.192. Modelli piccoli: 768.
            <InfoPopup title="Cosa sono le scaling laws">
              Sono regole empiriche: aumentando parametri, dati e calcolo, la qualità cresce in modo prevedibile.
              Servono ai team per decidere quanto conviene scalare un modello prima che i costi superino i benefici.
            </InfoPopup>
            <div style={{ marginTop: 8, color: t.textTertiary, fontSize: 14, fontStyle: "italic" }}>
              Analogia ABB: come la risoluzione di un sensore industriale — più dettaglio catturato, più banda e calcolo richiesto.
            </div>
          </InfoBox>
        </>
      );

    case "attention":
      return (
        <>
          <P>
            Il <Strong accent>Self-Attention</Strong> è il cuore dell'architettura Transformer. Ogni token "guarda" tutti gli altri
            nella sequenza e assegna un peso di attenzione per costruire una rappresentazione contestualizzata.
            <InfoPopup title="Self-Attention spiegata semplice">
              Ogni parola decide quanto contano le altre parole della frase in quel momento.
              Il risultato è che lo stesso termine può cambiare significato in base al contesto.
            </InfoPopup>
          </P>
          <AttentionMatrix />
          <Grid>
            <GridCard title="QUERY, KEY, VALUE" index={0}>
              Ogni token genera 3 vettori: <strong>Query</strong> (cosa cerco?), <strong>Key</strong> (cosa offro?),{" "}
              <strong>Value</strong> (il mio contenuto). L'attenzione = prodotto scalare Query × Key, normalizzato con softmax.
              <InfoPopup title="Query, Key, Value in pratica">
                Pensa a una ricerca interna: Query è la domanda, Key è l'etichetta, Value è l'informazione.
                Se domanda ed etichetta combaciano, quel token pesa di più nella risposta finale.
              </InfoPopup>
            </GridCard>
            <GridCard title="MULTI-HEAD ATTENTION" index={2}>
              Non una sola testa, ma <strong>32–128 teste parallele</strong> (es. 32 per LLaMA-7B, 96 per GPT-3): ognuna specializzata su relazioni diverse
              (sintattiche, semantiche, co-riferimento). I risultati vengono concatenati.
              <InfoPopup title="Perché tante teste">
                Ogni testa osserva la frase da un angolo diverso: grammatica, significato, riferimenti tra parole.
                Unendo tutto, il modello ottiene una lettura più robusta del testo.
              </InfoPopup>
            </GridCard>
          </Grid>
        </>
      );

    case "ffn":
      return (
        <>
          <P>
            Dopo l'Attention, ogni token attraversa una <Strong accent>rete Feed-Forward</Strong> — due layer lineari con
            attivazione non-lineare (GeLU/SwiGLU). Questa è la "memoria fattuale" del modello.
            <InfoPopup title="FFN, GeLU e SwiGLU">
              La FFN trasforma il segnale in modo non lineare: non fa solo somme, ma accentua pattern utili e attenua rumore.
              GeLU e SwiGLU sono funzioni diverse per fare questa selezione.
            </InfoPopup>
          </P>
          <CodeBlock>
            <div style={{ display: "flex", alignItems: "stretch", justifyContent: "center", gap: 12, flexWrap: "wrap", padding: "8px 0" }}>
              <div style={{
                width: 150, minHeight: 94, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                background: t.accentBg, border: `1.5px solid ${t.accent}40`, borderRadius: 8, padding: "8px 10px",
              }}>
                <div style={{ fontSize: 15, color: t.text, fontWeight: 700 }}>Input</div>
                <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 3 }}>d_model</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", color: t.textTertiary, fontSize: 18, fontWeight: 700 }}>→</div>
              <div style={{
                width: 190, minHeight: 120, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                background: t.accentBg, border: `1.5px solid ${t.accent}40`, borderRadius: 8, padding: "10px 12px",
              }}>
                <div style={{ fontSize: 15, color: t.text, fontWeight: 700 }}>Espansione</div>
                <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 3 }}>~4× d_model</div>
                <div style={{ fontSize: 12, color: t.textTertiary, marginTop: 7 }}>più capacità di rappresentazione</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", color: t.textTertiary, fontSize: 16, fontWeight: 700 }}>→ GeLU →</div>
              <div style={{
                width: 170, minHeight: 94, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                background: t.accentBg, border: `1.5px solid ${t.accent}40`, borderRadius: 8, padding: "8px 10px",
              }}>
                <div style={{ fontSize: 15, color: t.text, fontWeight: 700 }}>Compressione</div>
                <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 3 }}>d_model</div>
              </div>
            </div>
            <div style={{ marginTop: 8, color: t.textTertiary, fontSize: 13, textAlign: "center" }}>
              In breve: espande lo spazio per calcolare relazioni non lineari, poi comprime di nuovo nella dimensione originale.
            </div>
          </CodeBlock>
          <InfoBox title="DOVE RISIEDE LA CONOSCENZA?" variant="default">
            I pesi della FFN sono una <Strong>memoria associativa compressa</Strong>. Studi recenti mostrano che singoli neuroni
            si attivano per concetti specifici: "la Torre Eiffel è a Parigi", "l'acqua bolle a 100°C".
            L'Attention decide <em>cosa guardare</em>, la FFN <em>applica la conoscenza</em>.
          </InfoBox>
        </>
      );

    case "layers":
      return (
        <>
          <P>
            Un Transformer ha <Strong accent>decine di layer impilati</Strong> (32 per LLaMA-7B, 96 per GPT-3, 120 per GPT-4). Ogni layer raffina progressivamente
            la rappresentazione, da feature superficiali a concetti astratti.
          </P>
          <CodeBlock>
            {[
              { layer: "Layer iniziali", desc: "Sintassi, struttura grammaticale, pattern locali", pct: 20 },
              { layer: "Layer intermedi", desc: "Semantica, relazioni tra entità, ragionamento base", pct: 45 },
              { layer: "Layer profondi", desc: "Ragionamento complesso, analogie, conoscenza mondo", pct: 75 },
              { layer: "Layer finali", desc: "Pianificazione risposta, stile, coerenza globale", pct: 100 },
            ].map((l, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 12, padding: "10px 14px",
                marginBottom: 4, borderRadius: 6,
                background: `linear-gradient(90deg, ${t.accent}${(8 + i * 6).toString(16)} ${l.pct}%, transparent ${l.pct}%)`,
                borderLeft: `3px solid ${t.accent}`,
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: t.accent, minWidth: 90, fontFamily: "'JetBrains Mono', monospace" }}>
                  {l.layer}
                </div>
                <div style={{ fontSize: 14, color: t.textSecondary }}>{l.desc}</div>
              </div>
            ))}
          </CodeBlock>
          <Grid>
            <GridCard title="RESIDUAL CONNECTIONS" index={1}>
              Ogni layer somma il suo output all'input originale (skip connection), impedendo che il segnale si degradi attraverso 80+ layer.
              <InfoPopup title="Perché serve la residual">
                La scorciatoia mantiene vivo il segnale originale mentre il layer aggiunge una correzione.
                Senza residual, i modelli profondi perderebbero informazione strada facendo.
              </InfoPopup>
            </GridCard>
            <GridCard title="LAYER NORMALIZATION" index={3}>
              I valori vengono normalizzati ad ogni layer per stabilità numerica — senza questo, il training divergerebbe.
              <InfoPopup title="Layer norm in pratica">
                Riporta attivazioni su una scala controllata, evitando numeri troppo grandi o troppo piccoli.
                In questo modo l'addestramento resta stabile e più veloce da convergere.
              </InfoPopup>
            </GridCard>
          </Grid>
        </>
      );

    case "generation":
      return (
        <>
          <P>
            La generazione è <Strong accent>autoregressiva</Strong>: il modello genera <Strong>un token alla volta</Strong>.
            Ad ogni passo, tutto il contesto (input + token già generati) viene riprocessato.
            <InfoPopup title="Autoregressivo significa">
              Il modello decide ogni token usando i token precedenti. È come scrivere una frase una parola per volta,
              controllando ogni volta il contesto già scritto.
            </InfoPopup>
          </P>
          <GenerationDemo />
          <InfoBox title="PERCHÉ È LENTA LA GENERAZIONE?" variant="default">
            Ad ogni token, il modello ricalcola l'intera sequenza attraverso tutti i layer.
            Per 500 token con un modello a 96 layer = <Strong>48.000 passaggi Attention+FFN</Strong>.
            Tecniche di ottimizzazione: <Strong accent>KV-cache</Strong> (memorizzare calcoli già fatti per non riprocessare token precedenti) e{" "}
            <Strong accent>speculative decoding</Strong> (predire più token in parallelo con un modello più piccolo).
            <InfoPopup title="KV-cache e speculative decoding">
              KV-cache evita di rifare calcoli già fatti sui token vecchi. Speculative decoding usa un modello veloce per proporre token
              e uno grande per validarli, riducendo la latenza percepita.
            </InfoPopup>
          </InfoBox>
        </>
      );

    case "sampling":
      return (
        <>
          <P>
            Il modello non "sceglie" una parola: produce una <Strong accent>distribuzione di probabilità</Strong>{" "}
            su ~100K token. La <Strong>temperatura</Strong> controlla la concentrazione della scelta. Prova a muovere lo slider.
            <InfoPopup title="Temperatura in parole umane">
              Temperatura bassa: risposta più prevedibile e stabile. Temperatura alta: più variabilità e creatività,
              ma aumenta il rischio di frasi meno precise.
            </InfoPopup>
          </P>
          <SamplingDemo />
          <Grid>
            <GridCard title="TOP-K SAMPLING" index={1}>
              Si considerano solo i K token più probabili. Top-K=50 significa scegliere tra i 50 migliori candidati, scartando gli altri.
              <InfoPopup title="Quando usare Top-K">
                È utile quando vuoi limitare uscite strane: restringe il campo a un numero fisso di candidati forti.
              </InfoPopup>
            </GridCard>
            <GridCard title="TOP-P (NUCLEUS)" index={2}>
              Si prendono token fino a raggiungere probabilità cumulativa P. Top-P=0.9 include i token che coprono il 90% della massa probabilistica.
              <InfoPopup title="Quando usare Top-P">
                Invece di un numero fisso, prende i token necessari per coprire una quota di probabilità.
                Si adatta meglio a frasi semplici o complesse.
              </InfoPopup>
            </GridCard>
          </Grid>
        </>
      );

    case "training":
      return (
        <>
          <P>
            Il training di un LLM avviene in <Strong accent>tre fasi distinte</Strong>, ciascuna con obiettivi, dati e costi diversi.
            <InfoPopup title="RLHF e DPO, differenza rapida">
              RLHF usa un modello di reward per stimare quali risposte piacciono di più agli umani. DPO ottimizza direttamente
              su coppie di preferenze, con pipeline spesso più semplice da gestire.
            </InfoPopup>
          </P>
          {[
            { phase: "1. PRE-TRAINING", desc: "Il modello legge trilioni di token dal web, libri, codice, paper scientifici. Obiettivo: predire il prossimo token. Costo: milioni di $ in GPU per settimane.", variant: 0 },
            { phase: "2. FINE-TUNING (SFT)", desc: "Addestramento su conversazioni curate da umani — il modello impara a seguire istruzioni, rispondere utilmente, mantenere formato coerente.", variant: 2 },
            { phase: "3. RLHF / DPO", desc: "Allineamento tramite feedback umano: con RLHF, un reward model valuta le risposte; con DPO (alternativa più recente) si ottimizza direttamente sulle preferenze umane senza reward model separato.", variant: 3 },
          ].map((p, i) => (
            <div key={i} style={{
              display: "flex", gap: 14, padding: 16, marginBottom: 8,
              background: t.surfaceAlt, borderRadius: 8, borderLeft: `3px solid ${t.tagColor[p.variant]}`,
              border: `1px solid ${t.borderSubtle}`,
            }}>
              <div>
                <div style={{ color: t.tagColor[p.variant], fontWeight: 700, fontSize: 15, letterSpacing: "0.04em" }}>{p.phase}</div>
                <div style={{ color: t.textSecondary, fontSize: 14, marginTop: 4, lineHeight: 1.6 }}>{p.desc}</div>
              </div>
            </div>
          ))}
        </>
      );

    case "limits":
      return (
        <>
          <P>Capire limiti e punti di forza è fondamentale per un'adozione consapevole in azienda.</P>
          <Grid>
            <div>
              <div style={{ color: t.errorColor, fontWeight: 700, fontSize: 16, marginBottom: 10, letterSpacing: "0.04em" }}>LIMITI</div>
              {[
                { t: "Allucinazioni", d: "Genera testo plausibile ma falso — non ha un \"database di fatti\"" },
                { t: "No ragionamento causale", d: "Trova correlazioni statistiche, non comprende causa-effetto" },
                { t: "Context window finita", d: "Elabora solo un numero limitato di token alla volta (128K–1M a seconda del modello)" },
                { t: "Nessuna memoria persistente", d: "Ogni conversazione parte da zero (senza tool esterni)" },
                { t: "Bias dai dati", d: "Riflette pregiudizi presenti nei testi di training" },
              ].map((l, i) => (
                <div key={i} style={{
                  background: t.surfaceAlt, borderRadius: 6, padding: 10, marginBottom: 6,
                  borderLeft: `3px solid ${t.errorColor}`, border: `1px solid ${t.borderSubtle}`,
                }}>
                  <div style={{ color: t.errorColor, fontWeight: 600, fontSize: 14 }}>{l.t}</div>
                  <div style={{ color: t.textTertiary, fontSize: 13, marginTop: 3 }}>{l.d}</div>
                </div>
              ))}
            </div>
            <div>
              <div style={{ color: t.successColor, fontWeight: 700, fontSize: 16, marginBottom: 10, letterSpacing: "0.04em" }}>PUNTI DI FORZA</div>
              {[
                { t: "Versatilità estrema", d: "Un solo modello per traduzione, analisi, coding, riassunti, brainstorming" },
                { t: "Comprensione contesto", d: "Eccellente nel capire sfumature, tono, intent dell'utente" },
                { t: "Velocità", d: "Sintetizza in secondi ciò che richiederebbe ore" },
                { t: "Scalabilità", d: "Serve migliaia di utenti simultaneamente via API" },
                { t: "Miglioramento continuo", d: "Nuovi modelli ogni ~6 mesi con salti qualitativi" },
              ].map((l, i) => (
                <div key={i} style={{
                  background: t.surfaceAlt, borderRadius: 6, padding: 10, marginBottom: 6,
                  borderLeft: `3px solid ${t.successColor}`, border: `1px solid ${t.borderSubtle}`,
                }}>
                  <div style={{ color: t.successColor, fontWeight: 600, fontSize: 14 }}>{l.t}</div>
                  <div style={{ color: t.textTertiary, fontSize: 13, marginTop: 3 }}>{l.d}</div>
                </div>
              ))}
            </div>
          </Grid>
          <InfoBox title="NOTE SUI LIMITI" variant="warning">
            Allucinazioni e context window finita sono due limiti spesso sottovalutati.
            <InfoPopup title="Allucinazioni: cosa sono davvero">
              Non sono bug casuali: il modello completa la frase in modo plausibile anche quando non ha evidenza sufficiente.
              Per ridurle servono fonti esterne verificate, controlli e validazione umana.
            </InfoPopup>
            <InfoPopup title="Context window: perché conta">
              È la memoria a breve termine del modello: oltre quel limite, parti del testo vengono tagliate o compresse.
              Questo può ridurre coerenza e precisione su documenti molto lunghi.
            </InfoPopup>
          </InfoBox>
          <InfoBox title="TAKEAWAY PER ABB" variant="accent">
            Gli LLM non sono intelligenze artificiali generali — sono <Strong>motori statistici di linguaggio estremamente potenti</Strong>.
            Il valore emerge quando li si integra con guardrail, retrieval da fonti verificate (RAG), validazione umana e processi strutturati.
            La domanda giusta non è "è intelligente?" ma <Strong accent>"dove crea valore nel nostro contesto?"</Strong>
          </InfoBox>
        </>
      );

    default: return null;
  }
}

// ─── MAIN APP ───

export default function App() {
  const [mode, setMode] = useState("light");
  const [active, setActive] = useState("overview");
  const t = themes[mode];

  return (
    <ThemeContext.Provider value={t}>
      <div style={{ minHeight: "100vh", background: t.bg, fontFamily: "'ABBvoice', 'Segoe UI', -apple-system, sans-serif", transition: "background 0.3s" }}>
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
          @keyframes blink { 0%,50% { opacity: 1 } 51%,100% { opacity: 0 } }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          ::-webkit-scrollbar { width: 5px; height: 5px; }
          ::-webkit-scrollbar-track { background: ${t.bg}; }
          ::-webkit-scrollbar-thumb { background: ${t.border}; border-radius: 3px; }
          input[type=range] { height: 4px; }
        `}</style>

        {/* Header */}
        <div style={{
          background: t.headerBg, borderBottom: `1px solid ${t.border}`,
          padding: "16px 24px", position: "sticky", top: 0, zIndex: 100,
        }}>
          <div style={{ maxWidth: 1120, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              {/* Datapizza Logo */}
              <img
                src={`${import.meta.env.BASE_URL}datapizza_icon.png`}
                alt="Datapizza logo"
                style={{ height: 28, width: "auto", display: "block" }}
              />
              <div>
                <div style={{ color: t.text, fontSize: 18, fontWeight: 700, letterSpacing: "-0.01em" }}>
                  Come funzionano gli LLM
                </div>
                <div style={{ color: t.textTertiary, fontSize: 13, letterSpacing: "0.04em" }}>
                  GUIDA INTERATTIVA — DATAPIZZA × ABB
                </div>
              </div>
            </div>
            {/* Theme toggle */}
            <button onClick={() => setMode(mode === "light" ? "dark" : "light")} style={{
              background: t.surfaceAlt, border: `1px solid ${t.border}`, borderRadius: 6,
              padding: "6px 12px", cursor: "pointer", color: t.textSecondary, fontSize: 14,
              display: "flex", alignItems: "center", gap: 6, transition: "all 0.2s",
            }}>
              {mode === "light" ? "◐" : "◑"}
              <span>{mode === "light" ? "Dark" : "Light"}</span>
            </button>
          </div>
        </div>

        {/* Nav */}
        <div style={{
          background: t.navBg, borderBottom: `1px solid ${t.border}`,
          overflowX: "auto", position: "sticky", top: 64, zIndex: 99,
        }}>
          <div style={{ maxWidth: 1120, margin: "0 auto", display: "flex", padding: "0 24px" }}>
            {SECTIONS.map((s, i) => (
              <button key={s.id} onClick={() => setActive(s.id)} style={{
                background: "transparent", border: "none",
                borderBottom: active === s.id ? `2px solid ${t.accent}` : "2px solid transparent",
                color: active === s.id ? t.accent : t.textTertiary,
                padding: "10px 14px", cursor: "pointer", fontSize: 14, fontWeight: active === s.id ? 700 : 500,
                whiteSpace: "nowrap", transition: "all 0.2s", letterSpacing: "0.02em",
              }}>
                <span style={{ color: t.textTertiary, marginRight: 4, fontSize: 12 }}>{String(i + 1).padStart(2, "0")}</span>
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div style={{ maxWidth: 1120, margin: "0 auto", padding: "32px 28px 44px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 4 }}>
            <span style={{ color: t.accent, fontSize: 13, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.06em" }}>
              {String(SECTIONS.findIndex((s) => s.id === active) + 1).padStart(2, "0")}
            </span>
            <h2 style={{ color: t.text, fontSize: 22, fontWeight: 700, letterSpacing: "-0.01em" }}>
              {SECTIONS.find((s) => s.id === active)?.label}
            </h2>
          </div>
          <div style={{ height: 2, width: 40, background: t.accent, borderRadius: 1, marginBottom: 24 }} />
          <SectionContent id={active} />

          {/* Footer nav */}
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 36, paddingTop: 20, borderTop: `1px solid ${t.border}` }}>
            {(() => {
              const idx = SECTIONS.findIndex((s) => s.id === active);
              return (
                <>
                  {idx > 0 ? (
                    <button onClick={() => setActive(SECTIONS[idx - 1].id)} style={{
                      background: t.surfaceAlt, border: `1px solid ${t.border}`, borderRadius: 6,
                      color: t.textSecondary, padding: "8px 16px", cursor: "pointer", fontSize: 15, transition: "all 0.2s",
                    }}>← {SECTIONS[idx - 1].label}</button>
                  ) : <div />}
                  {idx < SECTIONS.length - 1 ? (
                    <button onClick={() => setActive(SECTIONS[idx + 1].id)} style={{
                      background: t.accent, border: "none", borderRadius: 6,
                      color: "#fff", padding: "8px 20px", cursor: "pointer",
                      fontSize: 15, fontWeight: 700, letterSpacing: "0.02em", transition: "all 0.2s",
                    }}>{SECTIONS[idx + 1].label} →</button>
                  ) : <div />}
                </>
              );
            })()}
          </div>
        </div>
      </div>
    </ThemeContext.Provider>
  );
}
