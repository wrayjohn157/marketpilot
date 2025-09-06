// Using fetch API instead of axios
import { useEffect, useState } from "react";
import { Button } from "../components/ui/Button";
import CandleChart from "../components/ui/CandleChart";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "../components/ui/Collapsible";
import { FormField } from "../components/ui/FormField";
import { Input } from "../components/ui/Input";
import { Switch } from "../components/ui/Switch";

// --- Reusable UI helpers ---
const FieldGrid = ({ children }) => (
  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">{children}</div>
);

const NumericField = ({ label, value, onChange, ...props }) => (
  <FormField label={label}>
    <Input
      type="number"
      value={value}
      step="0.01"
      onChange={e => onChange(parseFloat(e.target.value))}
      {...props}
    />
  </FormField>
);

const SwitchField = ({ label, checked, onChange }) => (
  <FormField label={label} className="flex-row items-center gap-2">
    <Switch checked={checked} onCheckedChange={onChange} />
  </FormField>
);

const Section = ({ title, children }) => (
  <div>
    <div className="font-semibold text-lg mb-2">{title}</div>
    {children}
  </div>
);

const DcaStrategyBuilder = () => {
  const [symbol, setSymbol] = useState("BTC");
  const [interval, setInterval] = useState("1h");
  const [series, setSeries] = useState([]);
  const [entryTime, setEntryTime] = useState(null);
  const [dcaResults, setDcaResults] = useState([]);
  const [formData, setFormData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Default config matching actual backend structure
  const [params, setParams] = useState({
    max_trade_usdt: 2000,
    base_order_usdt: 200,
    drawdown_trigger_pct: 1.2,
    safu_score_threshold: 0.5,
    score_decay_min: 0.2,
    buffer_zone_pct: 0,
    require_indicator_health: true,
    indicator_thresholds: {
      rsi: 42,
      macd_histogram: 0.0001,
      adx: 12,
    },
    use_btc_filter: false,
    btc_indicators: {
      rsi_max: 35,
      macd_histogram_max: 0,
      adx_max: 15,
    },
    use_trajectory_check: true,
    trajectory_thresholds: {
      macd_lift_min: 0.0001,
      rsi_slope_min: 1.0,
    },
    require_tp1_feasibility: true,
    max_tp1_shift_pct: 25,
    require_recovery_odds: true,
    min_recovery_probability: 0.5,
    min_confidence_odds: 0.65,
    use_confidence_override: true,
    confidence_dca_guard: {
      safu_score_min: 0.5,
      macd_lift_min: 0.00005,
      rsi_slope_min: 1.0,
      confidence_score_min: 0.75,
      min_confidence_delta: 0.1,
      min_tp1_shift_gain_pct: 1.5,
    },
    soft_confidence_override: {
      enabled: false,
    },
    min_be_improvement_pct: 2.0,
    step_repeat_guard: {
      enabled: true,
      min_conf_delta: 0.1,
      min_tp1_delta: 1.5,
    },
    so_volume_table: [20, 15, 25, 40, 65, 90, 150, 250],
    tp1_targets: [0.4, 1.1, 1.7, 2.4, 3.0, 3.9, 5.2, 7.1, 10.0],
    zombie_tag: {
      enabled: true,
      min_drawdown_pct: 0.5,
      max_drawdown_pct: 5,
      max_score: 0.3,
      require_zero_recovery_odds: true,
      max_macd_lift: 0.0,
      max_rsi_slope: 0.0,
    },
    use_ml_spend_model: true,
    spend_adjustment_rules: {
      min_volume: 20,
      max_multiplier: 3.0,
      tp1_shift_soft_cap: 2.5,
      low_dd_pct_limit: 1.0,
    },
    log_verbose: true,
    enforce_price_below_last_step: true,
    trailing_step_guard: {
      enabled: true,
      min_pct_gap_from_last_dca: 2.0,
    },
    adaptive_step_spacing: {
      enabled: false,
    },
    require_macd_cross: false,
    macd_cross_lookback: 1,
    bottom_reversal_filter: {
      enabled: true,
      macd_lift_min: 0.0003,
      rsi_slope_min: 0.6,
      local_price_reversal_window: 3,
    },
  });

  // Load DCA config from API
  useEffect(() => {
    fetch("/config/dca")
      .then(res => res.json())
      .then(data => {
        console.log("Loaded config:", data.config);
        setFormData(data.config);
        setError(null);
      })
      .catch(err => {
        setError("Failed to load config");
        console.error("Config load error:", err);
      });
  }, []);

  useEffect(() => {
    fetch(`/price-series?symbol=${symbol}&interval=${interval}`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data.series)) {
          console.log("Fetched full series data length:", data.series.length);
          const mapped = data.series.map(d => ({
            timestamp: Number(d.timestamp),
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
          }));
          setSeries(mapped);
        }
      })
      .catch(err => console.error("Failed to load price series:", err));
  }, [symbol, interval]);

  // Merge fallback params with loaded config for any missing keys
  const configData = formData ? { ...params, ...formData } : params;

  const updateParam = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const updateNestedParam = (section, key, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  const updateArrayParam = (section, index, value) => {
    setFormData(prev => {
      const arr = Array.isArray(prev?.[section]) ? [...prev[section]] : [];
      arr[index] = value;
      return { ...prev, [section]: arr };
    });
  };

  // Save configuration
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // Ensure we save the complete configuration by merging with defaults
      const completeConfig = { ...params, ...formData };
      console.log("Saving complete config:", completeConfig);
      const response = await fetch("/config/dca", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(completeConfig)
      });

      if (response.ok) {
        setSuccess("Configuration saved successfully!");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error("Failed to save configuration");
      }
    } catch (err) {
      setError("Failed to save configuration: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Reset to default configuration
  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to reset to default configuration? This will overwrite all current settings.")) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // Reset to default values
      setFormData({ ...params });

      // Also save the reset to backend
      const response = await fetch("/config/dca", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params)
      });

      if (response.ok) {
        setSuccess("Configuration reset to defaults!");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error("Failed to save reset configuration");
      }
    } catch (err) {
      setError("Failed to reset configuration: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Load default configuration from server (view-only, doesn't save)
  const handleLoadDefaults = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/config/dca/default");
      if (response.ok) {
        const defaultConfig = await response.json();
        setFormData(defaultConfig.config);
        setSuccess("Default configuration loaded (view-only). Click 'Save Config' to apply changes.");
        setTimeout(() => setSuccess(null), 5000);
      } else {
        throw new Error("Failed to load default configuration");
      }
    } catch (err) {
      setError("Failed to load default configuration: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="p-6 bg-gray-900 text-white">
      <CardHeader>
        <CardTitle className="text-2xl">📌 DCA Strategy Builder</CardTitle>
        {error && (
          <div className="bg-red-600 text-white p-3 rounded mb-4">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-600 text-white p-3 rounded mb-4">
            {success}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Core DCA Config */}
        <Section title="🛠️ Core DCA Settings">
          <FieldGrid>
            <NumericField
              label="Max Trade USDT"
              value={configData.max_trade_usdt}
              onChange={(v) => updateParam("max_trade_usdt", v)}
            />
            <NumericField
              label="Base Order USDT"
              value={configData.base_order_usdt}
              onChange={(v) => updateParam("base_order_usdt", v)}
            />
            <NumericField
              label="Drawdown Trigger %"
              value={configData.drawdown_trigger_pct}
              onChange={(v) => updateParam("drawdown_trigger_pct", v)}
            />
            <NumericField
              label="SAFU Score Threshold"
              value={configData.safu_score_threshold}
              onChange={(v) => updateParam("safu_score_threshold", v)}
            />
            <NumericField
              label="Score Decay Min"
              value={configData.score_decay_min}
              onChange={(v) => updateParam("score_decay_min", v)}
            />
            <NumericField
              label="Buffer Zone %"
              value={configData.buffer_zone_pct}
              onChange={(v) => updateParam("buffer_zone_pct", v)}
            />
            <SwitchField
              label="Require Indicator Health"
              checked={configData.require_indicator_health}
              onChange={(v) => updateParam("require_indicator_health", v)}
            />
          </FieldGrid>
        </Section>

        {/* Indicator Thresholds */}
        <Collapsible>
          <CollapsibleTrigger className="flex items-center justify-between w-full p-3 bg-gray-800 rounded">
            <span className="font-semibold">🔪 Indicator Thresholds</span>
            <span className="text-gray-400">Click to expand</span>
          </CollapsibleTrigger>
          <CollapsibleContent className="p-4 bg-gray-800 rounded mt-2">
            <FieldGrid>
              <NumericField
                label="RSI"
                value={configData.indicator_thresholds?.rsi}
                onChange={(v) => updateNestedParam("indicator_thresholds", "rsi", v)}
              />
              <NumericField
                label="MACD Histogram"
                value={configData.indicator_thresholds?.macd_histogram}
                onChange={(v) => updateNestedParam("indicator_thresholds", "macd_histogram", v)}
              />
              <NumericField
                label="ADX"
                value={configData.indicator_thresholds?.adx}
                onChange={(v) => updateNestedParam("indicator_thresholds", "adx", v)}
              />
            </FieldGrid>
          </CollapsibleContent>
        </Collapsible>

        {/* BTC Filter */}
        <Collapsible>
          <CollapsibleTrigger className="flex items-center justify-between w-full p-3 bg-gray-800 rounded">
            <span className="font-semibold">₿ BTC Filter</span>
            <span className="text-gray-400">Click to expand</span>
          </CollapsibleTrigger>
          <CollapsibleContent className="p-4 bg-gray-800 rounded mt-2">
            <FieldGrid>
              <SwitchField
                label="Use BTC Filter"
                checked={configData.use_btc_filter}
                onChange={(v) => updateParam("use_btc_filter", v)}
              />
              <NumericField
                label="BTC RSI Max"
                value={configData.btc_indicators?.rsi_max}
                onChange={(v) => updateNestedParam("btc_indicators", "rsi_max", v)}
              />
              <NumericField
                label="BTC MACD Max"
                value={configData.btc_indicators?.macd_histogram_max}
                onChange={(v) => updateNestedParam("btc_indicators", "macd_histogram_max", v)}
              />
              <NumericField
                label="BTC ADX Max"
                value={configData.btc_indicators?.adx_max}
                onChange={(v) => updateNestedParam("btc_indicators", "adx_max", v)}
              />
            </FieldGrid>
          </CollapsibleContent>
        </Collapsible>

        {/* Safety Order Table */}
        <Collapsible>
          <CollapsibleTrigger className="flex items-center justify-between w-full p-3 bg-gray-800 rounded">
            <span className="font-semibold">📊 Safety Order Table</span>
            <span className="text-gray-400">Click to expand</span>
          </CollapsibleTrigger>
          <CollapsibleContent className="p-4 bg-gray-800 rounded mt-2">
            <div className="space-y-2">
              <label className="block text-sm font-medium">SO Volume Table</label>
              {configData.so_volume_table?.map((volume, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <span className="w-8 text-sm">Step {index + 1}:</span>
                  <Input
                    type="number"
                    value={volume}
                    className="w-24 bg-gray-700 border-gray-600 text-white"
                    onChange={(e) => updateArrayParam("so_volume_table", index, parseFloat(e.target.value))}
                  />
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Chart and Simulation */}
        <Section title="📈 Price Chart & Simulation">
          <div className="space-y-4">
            <div className="flex space-x-4">
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white"
              >
                <option value="BTC">BTC</option>
                <option value="ETH">ETH</option>
                <option value="ADA">ADA</option>
                <option value="SOL">SOL</option>
              </select>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white"
              >
                <option value="15m">15m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
                <option value="1d">1d</option>
              </select>
            </div>

            <CandleChart
              data={series}
              onCandleClick={(candle) => setEntryTime(candle.timestamp)}
              height={400}
            />

            <button
              onClick={async () => {
                if (!entryTime) {
                  alert("Please click on a candle to set entry time");
                  return;
                }

                try {
                  const response = await fetch("/dca/simulate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      symbol,
                      entry_time: entryTime,
                      tf: interval,
                      config: formData
                    })
                  });

                  const data = await response.json();
                  let resultArray = [];

                  if (data.result && Array.isArray(data.result)) {
                    resultArray = data.result;
                  } else if (data.series && Array.isArray(data.series)) {
                    resultArray = data.series;
                  } else {
                    console.error("Unexpected response format:", data);
                    return;
                  }

                  const mapped = resultArray.map(d => ({ ...d, time: d.timestamp }));
                  setDcaResults(mapped);
                } catch (err) {
                  console.error("Simulation failed:", err);
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded"
            >
              Run DCA Simulation
            </button>
          </div>
        </Section>

        {entryTime !== null && (
          <div className="mt-2 text-sm text-gray-300">
            Entry Time: {new Date(entryTime).toISOString().replace("T", " ").slice(0, 19)} UTC | DCA Steps:{" "}
            {dcaResults.filter(d => d.decision === "FIRE").length}
          </div>
        )}

        {dcaResults.length > 0 && (
          <div className="mt-6 p-4 bg-gray-800 rounded">
            <h3 className="text-lg font-semibold text-white mb-2">📊 DCA Simulation Results</h3>
            <div className="space-y-2 text-sm text-gray-300">
              {dcaResults.map((step, i) => (
                <div key={i} className="border-b border-gray-700 pb-1">
                  <strong>Step {i + 1}</strong> — {step.decision} at{" "}
                  <span className="text-green-300">{new Date(step.timestamp).toISOString().replace("T", " ").slice(0, 19)} UTC</span>{" "}
                  | Price: ${step.price?.toFixed(2)} | Volume: {step.volume}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 justify-end mt-6">
          <Button
            onClick={handleLoadDefaults}
            variant="outline"
            size="md"
            disabled={saving}
            title="Load safe default config (view-only, doesn't save)"
          >
            📖 View Defaults
          </Button>
          <Button
            onClick={handleReset}
            variant="danger"
            size="md"
            disabled={saving}
            title="Reset your config to match safe defaults"
          >
            🔄 Reset to Default
          </Button>
          <Button
            onClick={handleSave}
            variant="default"
            size="md"
            disabled={saving}
            title="Save your custom configuration"
          >
            {saving ? "Saving..." : "💾 Save My Config"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default DcaStrategyBuilder;
