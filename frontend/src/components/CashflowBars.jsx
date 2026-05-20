import React from "react";

export function CashflowBars({ cashflow }) {
  const entries = Object.entries(cashflow || {});
  const maxValue = entries.reduce((acc, [, value]) => Math.max(acc, value.income, value.expense), 1);

  if (!entries.length) {
    return <div className="empty-block">No cashflow history yet.</div>;
  }

  return (
    <div className="bar-grid">
      {entries.map(([month, value]) => (
        <div className="bar-item" key={month}>
          <p>{month}</p>
          <div className="bar-group">
            <span className="bar income" style={{ height: `${Math.max((value.income / maxValue) * 120, 4)}px` }} />
            <span className="bar expense" style={{ height: `${Math.max((value.expense / maxValue) * 120, 4)}px` }} />
          </div>
          <small>{Math.round(value.net).toLocaleString()} net</small>
        </div>
      ))}
    </div>
  );
}
