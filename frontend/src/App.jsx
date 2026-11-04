import { useEffect, useMemo, useState } from "react";
import {
  Activity, Users, Target, Wallet, RefreshCw, TrendingUp,
  AlertCircle, CheckCircle2, BarChart3, BrainCircuit, Search,
  LayoutDashboard, SlidersHorizontal, ArrowUpRight, IndianRupee,
  CircleHelp, Menu, X
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, PieChart, Pie, Cell, Legend, LineChart, Line
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";
const COLORS = ["#4776e6", "#13a889", "#f0a34a"];

const formatNumber = (value, digits = 2) => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return Number(value).toLocaleString("en-IN", { maximumFractionDigits: digits });
};

const formatCurrency = (value) =>
  value === null || value === undefined ? "—" : `₹${formatNumber(value, 2)}`;

const formatPercent = (value) => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const number = Number(value);
  return `${formatNumber(number <= 1 && number >= -1 ? number * 100 : number, 1)}%`;
};

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (!data || typeof data !== "object") return [];
  for (const key of ["customers", "results", "data", "items", "records"]) {
    if (Array.isArray(data[key])) return data[key];
  }
  return [];
}

function getRecommendation(customer) {
  return customer.recommended_discount ??
    customer.recommended_discount_amount ??
    customer.recommended_discount_by_uplift ??
    customer.discount_amount ?? 0;
}

function App() {
  const [metrics, setMetrics] = useState({});
  const [customers, setCustomers] = useState([]);
  const [distribution, setDistribution] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [discountFilter, setDiscountFilter] = useState("all");
  const [refreshCount, setRefreshCount] = useState(0);
  const [activeNav, setActiveNav] = useState("overview");
  const [mobileMenu, setMobileMenu] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadDashboard() {
      setLoading(true);
      setError("");
      const getJSON = async (path) => {
        const response = await fetch(`${API}${path}`);
        if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}`);
        return response.json();
      };
      const results = await Promise.allSettled([
        getJSON("/api/metrics"),
        getJSON("/api/customers?limit=100&offset=0"),
        getJSON("/api/discount-distribution")
      ]);
      if (cancelled) return;

      const [metricResult, customerResult, distributionResult] = results;
      if (metricResult.status === "fulfilled") {
        const response = metricResult.value || {};
        setMetrics({
          ...(response.causal_metrics || {}),
          ...(response.optimization_summary || {})
        });
      } else {
        setMetrics({});
        setError("Could not load model metrics. Check the /api/metrics endpoint.");
      }

      if (customerResult.status === "fulfilled") {
        setCustomers(normalizeList(customerResult.value));
      } else {
        setCustomers([]);
        setError("Customer data could not be loaded. Check the /api/customers endpoint.");
      }

      if (distributionResult.status === "fulfilled") {
        setDistribution(normalizeList(distributionResult.value?.distribution ?? distributionResult.value));
      } else {
        setDistribution([]);
      }
      setLoading(false);
    }
    loadDashboard().catch((err) => {
      if (!cancelled) {
        setError(err.message || "Unable to load dashboard.");
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, [refreshCount]);

  const filteredCustomers = useMemo(() => customers.filter((customer) => {
    const id = String(customer.customer_id ?? "").toLowerCase();
    const recommendation = String(getRecommendation(customer));
    return id.includes(search.toLowerCase()) &&
      (discountFilter === "all" || recommendation === discountFilter);
  }), [customers, search, discountFilter]);

  const totalCustomers = metrics.customers_evaluated ?? metrics.total_customers ?? customers.length;
  const recommendedCounts = metrics.recommended_discount_counts || {};
  const pieData = distribution.map((item) => ({
    name: `₹${item.discount ?? item.discount_amount ?? 0}`,
    value: Number(item.customers ?? item.customer_count ?? item.count ?? 0)
  }));

  const probabilityData = useMemo(() => {
    const fields = [
      ["purchase_probability_0", "No discount"],
      ["purchase_probability_10", "₹10 discount"],
      ["purchase_probability_20", "₹20 discount"]
    ];
    return fields.map(([key, name]) => {
      const values = customers.map((c) => Number(c[key])).filter(Number.isFinite);
      const average = values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
      return { option: name, probability: average === null ? null : average * 100 };
    }).filter((item) => item.probability !== null);
  }, [customers]);

  const profitData = [
    { strategy: "No discount", profit: Number(metrics.total_expected_profit_if_no_discount || 0) },
    { strategy: "Recommended", profit: Number(metrics.total_expected_profit_under_recommendations || 0) }
  ];

  const navItems = [
    { id: "overview", label: "Overview", icon: LayoutDashboard, target: "overview" },
    { id: "customers", label: "Customers", icon: Users, target: "customers" },
    { id: "optimization", label: "Optimization", icon: SlidersHorizontal, target: "optimization" }
  ];

  const goTo = (id) => {
    setActiveNav(id);
    setMobileMenu(false);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const metricRows = [
    ["Training rows", formatNumber(metrics.training_rows, 0)],
    ["Test rows", formatNumber(metrics.test_rows, 0)],
    ["MAE · ₹10", formatNumber(metrics.true_effect_mae_10, 4)],
    ["MAE · ₹20", formatNumber(metrics.true_effect_mae_20, 4)],
    ["RMSE · ₹10", formatNumber(metrics.true_effect_rmse_10, 4)],
    ["RMSE · ₹20", formatNumber(metrics.true_effect_rmse_20, 4)],
    ["Treatment propensity AUC", formatNumber(metrics.treatment_propensity_macro_ovr_auc, 4)]
  ];

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">EC</div>
          <div><strong>EconoCausal</strong><span>Causal intelligence platform</span></div>
          <button className="mobile-close" onClick={() => setMobileMenu(false)} aria-label="Close menu"><X size={18} /></button>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="nav-list">
          {navItems.map(({ id, label, icon: Icon, target }) => (
            <button key={id} className={`nav-item ${activeNav === id ? "active" : ""}`} onClick={() => goTo(target)}>
              <Icon size={18} /> {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <div className="sidebar-note-icon"><BrainCircuit size={17} /></div>
          <strong>Causal AI engine</strong>
          <span>CausalForestDML · EconML</span>
        </div>
        <div className="sidebar-bottom">
          <span className="status-dot" />
          <div><strong>API connection</strong><span>localhost:8000</span></div>
          <CheckCircle2 size={16} className="connection-check" />
        </div>
      </aside>

      {mobileMenu && <button className="mobile-backdrop" onClick={() => setMobileMenu(false)} aria-label="Close navigation" />}

      <main className="main-content">
        <header className="topbar">
          <div className="heading-group">
            <button className="mobile-menu-button" onClick={() => setMobileMenu(true)} aria-label="Open menu"><Menu size={20} /></button>
            <div>
              <div className="eyebrow">ECONOMICS & CAUSAL AI <span className="live-indicator">LIVE DATA</span></div>
              <h1>Dynamic Pricing Intelligence</h1>
              <p>Understand customer response. Optimize every discount decision.</p>
            </div>
          </div>
          <button className="refresh-button" onClick={() => setRefreshCount((n) => n + 1)} disabled={loading}>
            <RefreshCw size={16} className={loading ? "spin" : ""} /> {loading ? "Refreshing…" : "Refresh data"}
          </button>
        </header>

        {error && <div className="alert"><AlertCircle size={18} /><span>{error}</span></div>}

        <section id="overview" className="section-anchor">
          <div className="section-title"><div><span className="section-kicker">OVERVIEW</span><h2>Business snapshot</h2></div><span className="subtle-label">Model: CausalForestDML</span></div>
          <div className="kpi-grid">
            <article className="kpi-card">
              <div className="kpi-top"><span>Customers evaluated</span><div className="kpi-icon blue"><Users size={19} /></div></div>
              <strong className="kpi-value">{loading ? "…" : formatNumber(totalCustomers, 0)}</strong>
              <p>Customers included in optimization</p>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span>Expected profit</span><div className="kpi-icon green"><Wallet size={19} /></div></div>
              <strong className="kpi-value">{loading ? "…" : formatCurrency(metrics.total_expected_profit_under_recommendations)}</strong>
              <p>Under current recommendations</p>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span>Incremental expected profit</span><div className="kpi-icon violet"><TrendingUp size={19} /></div></div>
              <strong className="kpi-value">{loading ? "…" : formatCurrency(metrics.estimated_incremental_expected_profit)}</strong>
              <p>Compared with no-discount strategy</p>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span>Discount budget remaining</span><div className="kpi-icon amber"><IndianRupee size={19} /></div></div>
              <strong className="kpi-value">{loading ? "…" : formatCurrency(metrics.remaining_budget)}</strong>
              <p>{formatCurrency(metrics.total_discount_spend)} spent of {formatCurrency(metrics.campaign_budget)}</p>
            </article>
          </div>
        </section>

        <section className="chart-grid">
          <article className="panel">
            <div className="panel-heading"><div><h3>Discount allocation</h3><p>Number of customers assigned to each discount</p></div><span className="tag">Optimization output</span></div>
            {pieData.length ? <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={94} paddingAngle={3}>
                    {pieData.map((entry, index) => <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(value) => [formatNumber(value, 0), "Customers"]} />
                  <Legend verticalAlign="bottom" height={28} />
                </PieChart>
              </ResponsiveContainer>
            </div> : <div className="empty-state">Discount allocation data is not available.</div>}
            <div className="allocation-strip">
              {[0, 10, 20].map((amount, index) => <div key={amount}><span className="allocation-dot" style={{ background: COLORS[index] }} /><span>₹{amount}</span><strong>{formatNumber(recommendedCounts[String(amount)] ?? pieData[index]?.value ?? 0, 0)}</strong></div>)}
            </div>
          </article>

          <article className="panel">
            <div className="panel-heading"><div><h3>Purchase probability by offer</h3><p>Average across currently loaded customer records</p></div><span className="tag tag-blue">Prediction</span></div>
            {probabilityData.length ? <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={probabilityData} margin={{ top: 12, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid stroke="#edf1f7" strokeDasharray="4 4" vertical={false} />
                  <XAxis dataKey="option" axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 10 }} />
                  <Tooltip formatter={(v) => [`${formatNumber(v, 1)}%`, "Avg. purchase probability"]} />
                  <Bar dataKey="probability" fill="#4776e6" radius={[7, 7, 0, 0]} barSize={42} />
                </BarChart>
              </ResponsiveContainer>
            </div> : <div className="empty-state">Purchase probability fields are not present in the customer API response.</div>}
          </article>
        </section>

        <section id="optimization" className="section-anchor">
          <div className="section-title"><div><span className="section-kicker">DECISION SUPPORT</span><h2>Profit & campaign optimization</h2></div></div>
          <div className="optimization-grid">
            <article className="panel profit-panel">
              <div className="panel-heading"><div><h3>Expected profit comparison</h3><p>Current recommendation strategy versus no discount</p></div><BarChart3 size={19} className="panel-icon" /></div>
              <div className="chart-area compact-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={profitData} margin={{ top: 15, right: 12, left: 12, bottom: 5 }}>
                    <CartesianGrid stroke="#edf1f7" strokeDasharray="4 4" vertical={false} />
                    <XAxis dataKey="strategy" axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
                    <YAxis tickFormatter={(v) => `₹${formatNumber(v, 0)}`} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 10 }} />
                    <Tooltip formatter={(v) => [formatCurrency(v), "Expected profit"]} />
                    <Bar dataKey="profit" fill="#13a889" radius={[7, 7, 0, 0]} barSize={56} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
            <article className="panel optimization-summary">
              <div className="panel-heading"><div><h3>Optimization summary</h3><p>Based on current margin and budget assumptions</p></div><Target size={19} className="panel-icon" /></div>
              <div className="summary-list">
                <div><span>Customers evaluated</span><strong>{formatNumber(metrics.customers_evaluated, 0)}</strong></div>
                <div><span>Profit margin assumption</span><strong>{formatPercent(metrics.profit_margin_assumption)}</strong></div>
                <div><span>Discount spend</span><strong>{formatCurrency(metrics.total_discount_spend)}</strong></div>
                <div><span>Budget status</span><strong className={metrics.budget_respected ? "positive-text" : "warning-text"}>{metrics.budget_respected ? "Within budget" : "Over budget"}</strong></div>
              </div>
              <div className="insight-box"><CircleHelp size={17} /><p>{metrics.estimated_incremental_expected_profit === 0 ? "The current optimizer selected ₹0 for all customers because discounts do not improve expected profit under the configured assumptions." : "Recommendations are model-based estimates. Validate them with a randomized campaign and actual margin data."}</p></div>
            </article>
          </div>
        </section>

        <section className="panel model-panel">
          <div className="panel-heading"><div><span className="section-kicker">MODEL QUALITY</span><h3>Causal model evaluation</h3><p>Evaluation against the known synthetic treatment-effect mechanism</p></div><span className="model-badge"><CheckCircle2 size={14} /> Evaluation loaded</span></div>
          <div className="model-metrics-grid">
            {metricRows.map(([label, value]) => <div className="model-metric" key={label}><span>{label}</span><strong>{value}</strong></div>)}
          </div>
          <p className="model-note">Propensity metrics describe treatment-assignment prediction, not causal-effect accuracy. Synthetic-data metrics do not guarantee real-world campaign performance.</p>
        </section>

        <section id="customers" className="panel table-panel section-anchor">
          <div className="panel-heading table-heading"><div><span className="section-kicker">CUSTOMER INTELLIGENCE</span><h3>Individual discount predictions</h3><p>Compare predicted outcomes and treatment effects for each customer</p></div><span className="result-count">{filteredCustomers.length} of {customers.length} loaded</span></div>
          <div className="table-controls">
            <div className="search-box"><Search size={16} /><input type="search" placeholder="Search customer ID…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
            <select value={discountFilter} onChange={(e) => setDiscountFilter(e.target.value)} aria-label="Filter by recommended discount">
              <option value="all">All recommendations</option><option value="0">₹0 recommendation</option><option value="10">₹10 recommendation</option><option value="20">₹20 recommendation</option>
            </select>
          </div>
          <div className="table-scroll">
            <table>
              <thead><tr><th>Customer</th><th>Purchase · ₹0</th><th>Purchase · ₹10</th><th>Purchase · ₹20</th><th>Uplift · ₹10</th><th>Uplift · ₹20</th><th>Suggested offer*</th></tr></thead>
              <tbody>
                {filteredCustomers.map((c, index) => <tr key={c.customer_id ?? index}>
                  <td className="customer-id">{c.customer_id ?? `Customer ${index + 1}`}</td>
                  <td>{formatPercent(c.purchase_probability_0)}</td>
                  <td>{formatPercent(c.purchase_probability_10)}</td>
                  <td>{formatPercent(c.purchase_probability_20)}</td>
                  <td>{c.predicted_uplift_10_pp === undefined ? "—" : `${formatNumber(c.predicted_uplift_10_pp, 2)} pp`}</td>
                  <td>{c.predicted_uplift_20_pp === undefined ? "—" : `${formatNumber(c.predicted_uplift_20_pp, 2)} pp`}</td>
                  <td><span className="discount-pill">₹{formatNumber(getRecommendation(c), 0)}</span></td>
                </tr>)}
              </tbody>
            </table>
            {!filteredCustomers.length && <div className="empty-state">{loading ? "Loading customer predictions…" : "No customers match this search or filter."}</div>}
          </div>
          <p className="table-footnote">*Suggested offer uses the customer API's recommendation field. Confirm whether it is uplift-based or profit-optimized before treating it as the final business recommendation. Showing up to 100 records returned by the current API request.</p>
        </section>

        <footer>EconoCausal <span>·</span> Causal machine learning for smarter discount decisions</footer>
      </main>
    </div>
  );
}

export default App;
