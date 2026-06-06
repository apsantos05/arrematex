/**
 * IosDateTimePicker — date + time fields with iOS-inspired styling.
 * Props:
 *   date       string "YYYY-MM-DD"
 *   time       string "HH:MM"
 *   onDateChange / onTimeChange callbacks
 */

interface Props {
  date: string;
  time: string;
  onDateChange: (v: string) => void;
  onTimeChange: (v: string) => void;
  label?: string;
}

const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

function formatDateLabel(d: string) {
  if (!d) return "Selecionar data";
  const [y, m, day] = d.split("-");
  const dow = new Date(`${y}-${m}-${day}T12:00:00`).toLocaleDateString("pt-BR", { weekday: "short" });
  return `${dow.replace(".", "").charAt(0).toUpperCase() + dow.slice(1).replace(".", "")}, ${parseInt(day)} ${MONTHS[parseInt(m) - 1]} ${y}`;
}

function formatTimeLabel(t: string) {
  if (!t) return "Selecionar hora";
  return t.slice(0, 5);
}

export default function IosDateTimePicker({ date, time, onDateChange, onTimeChange, label }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {label && (
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", color: "#f5a623", textTransform: "uppercase" }}>
          {label}
        </span>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {/* ── Date ── */}
        <div style={{
          background: "rgba(255,255,255,0.06)",
          border: "1.5px solid rgba(245,166,35,0.25)",
          borderRadius: 14,
          padding: "10px 14px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
          transition: "border-color .2s",
        }}
          onMouseEnter={e => (e.currentTarget.style.borderColor = "rgba(245,166,35,0.6)")}
          onMouseLeave={e => (e.currentTarget.style.borderColor = "rgba(245,166,35,0.25)")}
        >
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", fontWeight: 600, letterSpacing: ".06em", textTransform: "uppercase" }}>
            Data
          </span>
          <input
            type="date"
            value={date}
            onChange={e => onDateChange(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: date ? "#fff" : "rgba(255,255,255,0.35)",
              fontSize: 14,
              fontWeight: 600,
              width: "100%",
              cursor: "pointer",
              colorScheme: "dark",
              padding: 0,
            }}
          />
        </div>

        {/* ── Time ── */}
        <div style={{
          background: "rgba(255,255,255,0.06)",
          border: "1.5px solid rgba(245,166,35,0.25)",
          borderRadius: 14,
          padding: "10px 14px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
          transition: "border-color .2s",
        }}
          onMouseEnter={e => (e.currentTarget.style.borderColor = "rgba(245,166,35,0.6)")}
          onMouseLeave={e => (e.currentTarget.style.borderColor = "rgba(245,166,35,0.25)")}
        >
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", fontWeight: 600, letterSpacing: ".06em", textTransform: "uppercase" }}>
            Hora
          </span>
          <input
            type="time"
            value={time}
            onChange={e => onTimeChange(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: time ? "#fff" : "rgba(255,255,255,0.35)",
              fontSize: 14,
              fontWeight: 600,
              width: "100%",
              cursor: "pointer",
              colorScheme: "dark",
              padding: 0,
            }}
          />
        </div>
      </div>
    </div>
  );
}
