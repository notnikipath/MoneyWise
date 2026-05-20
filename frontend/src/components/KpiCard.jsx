import React from "react";

export function KpiCard({ title, value, note, ok = true }) {
  return (
    <article className="kpi-card">
      <p className="kpi-title">{title}</p>
      <p className="kpi-value">{value}</p>
      <p className={`kpi-note ${ok ? "ok" : "warn"}`}>{note}</p>
    </article>
  );
}
