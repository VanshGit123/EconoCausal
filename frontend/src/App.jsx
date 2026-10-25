
import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from "recharts";
import {
  Activity, Users, Target, Wallet, RefreshCw,
  TrendingUp, AlertCircle, CheckCircle2
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function formatValue(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    return Number.isInteger(value)
      ? value.toLocaleString("en-IN")
      : value.toLocaleString("en-IN", { maximumFractionDigits: 3 });
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function findNumber(obj, candidates) {
  if (!obj || typeof obj !== "object") return null;
  for (const key of candidates) {
    const value = obj[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
  }
  return null;
}

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (!data || typeof data !== "object") return [];
  for (const key of ["customers", "results", "data", "items", "records"]) {
    if (Array.isArray(data[key])) return data[key];
  }
  return [];
}

function App() {
  const [metrics, setMetrics] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [distribution, setDistribution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [discount, setDiscount] = useState("all");
  const [search, setSearch] = useState("");
  const [refreshCount, setRefreshCount] = useState(0);

  async function getJSON(path) {
    const response = await fetch(`${API}${path}`);
    if (!response.ok) {
      throw new Error(`${path} returned HTTP ${response.status}`);
    }
    return response.json();
  }

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled([
          getJSON("/api/metrics"),
          getJSON("/api/customers?limit=100&offset=0"),
          getJSON("/api/discount-distribution")
        ]);

        if (cancelled) return;

        const [metricsResult, customersResult, distributionResult] = results;

        if (metricsResult.status === "fulfilled") {
          setMetrics(metricsResult.value);
        } else {
          setMetrics(null);
        }

        if (customersResult.status === "fulfilled") {
          setCustomers(normalizeList(customersResult.value));
        } else {
          setCustomers([]);
        }

        if (distributionResult.status === "fulfilled") {
          setDistribution(distributionResult.value);
        } else {
          setDistribution(null);
        }

        if (results.every((r) => r.status === "rejected")) {
          setError("Could not load dashboard data. Check that FastAPI is running.");
        } else if (customersResult.status === "rejected") {
          setError("Customer data could not be loaded. Check the /api/customers endpoint.");
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDashboard();
    return () => { cancelled = true; };
  }, [refreshCount]);

  const filteredCustomers = useMemo(() => {
    return customers.filter((customer) => {
      const discountValue =
        customer.recommended_discount ??
        customer.recommended_discount_amount ??
        customer.discount_amount ??
        customer.recommended_discount_by_uplift;

      const matchesDiscount =
        discount === "all" || String(discountValue) === discount;

      const searchable = [
        customer.customer_id,
        customer.recommended_discount,
        customer.discount_amount
      ].map((v) => String(v ?? "")).join(" ").toLowerCase();

      return matchesDiscount && searchable.includes(search.toLowerCase());
    });
  }, [customers, discount, search]);

  const metricEntries = metrics && typeof metrics === "object"
    ? Object.entries(metrics).filter(([, value]) =>
        ["string", "number", "boolean"].includes(typeof value)
      )
    : [];

  const chartData = useMemo(() => {
    const raw = distribution;
    const list = normalizeList(raw);

    if (list.length) {
      return list.map((item) => ({
        name: String(
          item.discount ?? item.discount_amount ?? item.name ?? item.label ?? "Unknown"
        ),
        customers: Number(
          item.count ?? item.customer_count ?? item.customers ?? item.total ?? item.value ?? 0
        )
      }));
    }

    if (raw && typeof raw === "object") {
      const source = raw.distribution ?? raw.counts ?? raw;
      if (source && !Array.isArray(source) && typeof source === "object") {
        return Object.entries(source)
          .filter(([, value]) => typeof value === "number")
          .map(([name, customers]) => ({ name, customers }));
      }
    }
    return [];
  }, [distribution]);

  const totalCustomers =
    findNumber(metrics, ["total_customers", "n_customers", "customers_analyzed"]) ??
    customers.length;

  const cards = [
    {
      label: "Customers analyzed",
      value: formatValue(totalCustomers),
      icon: Users,
      note: "Customers in available API data"
    },
    {
      label: "Model",
      value: "CausalForestDML",
      icon: Activity,
      note: "Individual treatment effect estimation"
    },
    {
      label: "Discount options",
      value: "₹0 · ₹10 · ₹20",
      icon: Target,
      note: "Candidate discount amounts"
    },
    {
      label: "Optimization",
      value: "Profit-aware",
      icon: Wallet,
      note: "Review estimated profit metrics below"
    }
  ];

  const customerColumns = [
    ["customer_id", "Customer ID"],
    ["ite_discount_10", "ITE ₹10"],
    ["ite_discount_20", "ITE ₹20"],
    ["predicted_uplift_10_pp", "Uplift ₹10"],
    ["predicted_uplift_20_pp", "Uplift ₹20"],
    ["recommended_discount_by_uplift", "Recommended discount"]
  ];

  const visibleColumns = customerColumns.filter(([key]) =>
    customers.some((customer) => customer[key] !== undefined)
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">EC</div>
          <div>
            <strong>EconoCausal</strong>
            <span>Causal AI platform</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active"><Activity size={18} /> Overview</div>
        <div className="nav-item"><Users size={18} /> Customers</div>
        <div className="nav-item"><TrendingUp size={18} /> Optimization</div>

        <div className="sidebar-bottom">
          <span className="status-dot" />
          <div>
            <strong>API connection</strong>
            <span>localhost:8000</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">ECONOMICS & CAUSAL AI</div>
            <h1>Dynamic Pricing Dashboard</h1>
            <p>Estimate customer response and evaluate discount decisions.</p>
          </div>
          <button
            className="refresh-button"
            onClick={() => setRefreshCount((count) => count + 1)}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? "spin" : ""} />
            Refresh data
          </button>
        </header>

        {error && (
          <div className="alert">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <section className="kpi-grid">
          {cards.map(({ label, value, icon: Icon, note }) => (
            <article className="kpi-card" key={label}>
              <div className="kpi-top">
                <span>{label}</span>
                <div className="kpi-icon"><Icon size={19} /></div>
              </div>
              <strong className="kpi-value">{loading ? "…" : value}</strong>
              <p>{note}</p>
            </article>
          ))}
        </section>

        <section className="content-grid">
          <article className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>Discount distribution</h2>
                <p>Customer counts returned by the API</p>
              </div>
              <span className="tag">Live API</span>
            </div>

            {chartData.length ? (
              <div className="chart-area">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="customers" fill="#3578e5" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state">
                {loading ? "Loading chart data…" : "No recognized distribution data returned."}
              </div>
            )}
          </article>

          <article className="panel metrics-panel">
            <div className="panel-heading">
              <div>
                <h2>Model metrics</h2>
                <p>Values from causal_metrics.json via API</p>
              </div>
              <CheckCircle2 size={20} className="success-icon" />
            </div>
            {metricEntries.length ? (
              <div className="metrics-list">
                {metricEntries.map(([key, value]) => (
                  <div className="metric-row" key={key}>
                    <span>{key.replaceAll("_", " ")}</span>
                    <strong>{formatValue(value)}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                {loading ? "Loading metrics…" : "No scalar metrics found in the API response."}
              </div>
            )}
          </article>
        </section>

        <section className="panel table-panel">
          <div className="panel-heading table-heading">
            <div>
              <h2>Customer recommendations</h2>
              <p>Inspect estimated treatment effects and discount recommendations.</p>
            </div>
            <span className="result-count">{filteredCustomers.length} shown</span>
          </div>

          <div className="table-controls">
            <input
              type="search"
              placeholder="Search customer ID…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <select value={discount} onChange={(event) => setDiscount(event.target.value)}>
              <option value="all">All discounts</option>
              <option value="0">₹0</option>
              <option value="10">₹10</option>
              <option value="20">₹20</option>
            </select>
          </div>

          {visibleColumns.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>{visibleColumns.map(([key, label]) => <th key={key}>{label}</th>)}</tr>
                </thead>
                <tbody>
                  {filteredCustomers.map((customer, index) => (
                    <tr key={customer.customer_id ?? index}>
                      {visibleColumns.map(([key]) => (
                        <td key={key}>
                          {key === "recommended_discount_by_uplift"
                            ? `₹${formatValue(customer[key])}`
                            : formatValue(customer[key])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              {loading
                ? "Loading customer data…"
                : "No expected treatment-effect columns were found. Check the API response field names."}
            </div>
          )}
          <p className="table-footnote">
            ITE values are estimated treatment effects. Confirm the units and definitions in your model output before interpreting them as percentage-point changes.
          </p>
        </section>

        <footer>
          EconoCausal · Causal machine learning for discount decisions
        </footer>
      </main>
    </div>
  );
}

export default App;

