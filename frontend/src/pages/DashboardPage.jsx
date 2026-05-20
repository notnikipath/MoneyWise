import React, { useEffect, useMemo, useState } from "react";

import { CashflowBars } from "../components/CashflowBars";
import { KpiCard } from "../components/KpiCard";

const envGatewayUrl = import.meta.env.VITE_API_GATEWAY_URL?.trim();
const gatewayUrl =
  envGatewayUrl ||
  (typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:32092`
    : "http://localhost:32092");

const initialData = {
  accounts: { items: [] },
  transactions: { items: [] },
  recurring: { items: [] },
  budgets: { items: [] },
  budget_alerts: { items: [] },
  goals: { items: [] },
  portfolio: { items: [], average_return_pct: 0, total_market_value: 0 },
  portfolio_risk: { risk_level: "low", volatility: 0 },
  reports: { cashflow: {}, categories: {}, forecast: {} },
  analytics_kpi: {
    report_latency_estimate_seconds: 0,
    report_latency_target_seconds: 3,
    throughput_estimate_tx_per_day: 0,
    throughput_target_tx_per_day: 1000000,
    cache_hit_ratio: 0,
  },
  categorization: { accuracy_pct: 0, target_pct: 90, meets_target: false },
  notifications: { items: [] },
};

async function loadDashboard(userId) {
  const response = await fetch(`${gatewayUrl}/dashboard/${userId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard: ${response.status}`);
  }
  return response.json();
}

export function DashboardPage() {
  const [userId, setUserId] = useState("USR-DEMO");
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);
  const [data, setData] = useState(initialData);

  useEffect(() => {
    let active = true;
    setStatus("loading");

    loadDashboard(userId)
      .then((payload) => {
        if (!active) {
          return;
        }
        setData({ ...initialData, ...payload });
        setStatus("ready");
        setError(null);
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setStatus("failed");
        setError(err.message);
      });

    return () => {
      active = false;
    };
  }, [userId]);

  const categories = useMemo(() => Object.entries(data.reports?.categories || {}), [data]);

  return (
    <div className="app-shell">
      <div className="background-layer layer-a" />
      <div className="background-layer layer-b" />

      <header className="hero">
        <div>
          <p className="eyebrow">MoneyWise Personal Finance Assistant</p>
          <h1>Track spending, protect budget limits, and grow goals with one dashboard.</h1>
          <p className="hero-copy">
            The platform combines transactions, budgets, goals, and investments, then builds forecast and alerts.
          </p>
          <div className="badge-row">
            <span>Auto categorization</span>
            <span>Budget threshold alerts</span>
            <span>Cashflow forecast</span>
            <span>Portfolio risk view</span>
          </div>
        </div>

        <aside className="control-card">
          <label>
            User ID
            <input value={userId} onChange={(event) => setUserId(event.target.value)} />
          </label>
          <button onClick={() => setUserId((prev) => prev.trim() || "USR-DEMO")}>Refresh</button>
          <p className="status">Status: {status}</p>
          {error ? <p className="error-text">{error}</p> : null}
        </aside>
      </header>

      <section className="kpi-grid">
        <KpiCard
          title="Categorization"
          value={`${Number(data.categorization?.accuracy_pct || 0).toFixed(1)}%`}
          note={`Target ${data.categorization?.target_pct || 90}%`}
          ok={Boolean(data.categorization?.meets_target)}
        />
        <KpiCard
          title="Report Latency"
          value={`${Number(data.analytics_kpi?.report_latency_estimate_seconds || 0).toFixed(2)} sec`}
          note={`Target < ${data.analytics_kpi?.report_latency_target_seconds || 3} sec`}
          ok={
            Number(data.analytics_kpi?.report_latency_estimate_seconds || 99) <=
            Number(data.analytics_kpi?.report_latency_target_seconds || 3)
          }
        />
        <KpiCard
          title="Throughput"
          value={`${Math.round(data.analytics_kpi?.throughput_estimate_tx_per_day || 0).toLocaleString()} tx/day`}
          note={`Target ${(data.analytics_kpi?.throughput_target_tx_per_day || 1000000).toLocaleString()} tx/day`}
          ok={
            Number(data.analytics_kpi?.throughput_estimate_tx_per_day || 0) >=
            Number(data.analytics_kpi?.throughput_target_tx_per_day || 1000000)
          }
        />
        <KpiCard
          title="Portfolio Return"
          value={`${Number(data.portfolio?.average_return_pct || 0).toFixed(2)}%`}
          note={`Risk: ${data.portfolio_risk?.risk_level || "low"}`}
          ok={(data.portfolio_risk?.risk_level || "low") !== "high"}
        />
      </section>

      <section className="grid-layout">
        <article className="panel panel-wide">
          <div className="panel-head">
            <h2>Cashflow by Month</h2>
            <span className="pill">Cache: {data.reports?.cache || "n/a"}</span>
          </div>
          <CashflowBars cashflow={data.reports?.cashflow} />
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>Category Spend</h2>
            <span className="pill">Expense only</span>
          </div>
          <div className="stack-list">
            {categories.length ? (
              categories.map(([category, amount]) => (
                <div className="stack-item" key={category}>
                  <span>{category}</span>
                  <strong>{Math.round(amount).toLocaleString()}</strong>
                </div>
              ))
            ) : (
              <div className="empty-block">No category breakdown yet.</div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>Goals</h2>
            <span className="pill">{data.goals?.count || 0}</span>
          </div>
          <div className="stack-list">
            {(data.goals?.items || []).map((goal) => (
              <div className="stack-item" key={goal.goal_id}>
                <div>
                  <p>{goal.name}</p>
                  <small>
                    {Math.round(goal.current_amount).toLocaleString()} / {Math.round(goal.target_amount).toLocaleString()}
                  </small>
                </div>
                <strong>{Number(goal.progress_pct).toFixed(1)}%</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>Budget Alerts</h2>
            <span className="pill warning">{data.budget_alerts?.count || 0}</span>
          </div>
          <div className="stack-list">
            {(data.budget_alerts?.items || []).slice(-4).reverse().map((alert) => (
              <div className="stack-item" key={alert.alert_id}>
                <div>
                  <p>{alert.category}</p>
                  <small>{alert.month}</small>
                </div>
                <strong>+{Math.round(alert.over_by).toLocaleString()}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-wide">
          <div className="panel-head">
            <h2>Forecast</h2>
            <span className="pill">Savings rate {Number(data.reports?.forecast?.savings_rate_pct || 0).toFixed(1)}%</span>
          </div>
          <div className="forecast-grid">
            <div>
              <p>Predicted Next Month Expense</p>
              <strong>{Math.round(data.reports?.forecast?.next_month_expense || 0).toLocaleString()}</strong>
            </div>
            <div>
              <p>Average Income</p>
              <strong>{Math.round(data.reports?.forecast?.avg_income || 0).toLocaleString()}</strong>
            </div>
            <div>
              <p>Average Expense</p>
              <strong>{Math.round(data.reports?.forecast?.avg_expense || 0).toLocaleString()}</strong>
            </div>
            <div>
              <p>Portfolio Value</p>
              <strong>{Math.round(data.portfolio?.total_market_value || 0).toLocaleString()}</strong>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
