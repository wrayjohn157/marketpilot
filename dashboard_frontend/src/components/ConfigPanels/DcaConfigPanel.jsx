// src/components/ConfigPanels/DcaConfigPanel.jsx

import { useEffect, useState } from "react";
import { Button } from "../ui/Button";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "../ui/Card";
import { FormField } from "../ui/FormField";
import { Input } from "../ui/Input";
import { Switch } from "../ui/Switch";

const prettyLabel = (key) =>
  key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

// Default config object matching the latest dca_config.yaml
const defaultConfig = {
  max_trade_usdt: 2000,
  base_order_usdt: 200,
  drawdown_trigger_pct: 1.2, // updated from 0.9
  safu_score_threshold: 0.5,
  score_decay_min: 0.2,
  buffer_zone_pct: 0.0,
  require_indicator_health: true,
  indicator_thresholds: {
    rsi: 42,
    macd_histogram: 0.0002,
    adx: 12,
  },
  use_btc_filter: true,
  btc_indicators: {
    rsi_max: 35,
    macd_histogram_max: 0.0,
    adx_max: 15,
  },
  use_trajectory_check: true,
  trajectory_thresholds: {
    macd_lift_min: 0.0001, // updated from 0.00005
    rsi_slope_min: 1.0,    // updated from 0.75
  },
  require_tp1_feasibility: true,
  max_tp1_shift_pct: 30.0,
  require_recovery_odds: true,
  min_recovery_probability: 0.5,
  min_confidence_odds: 0.65,
  use_confidence_override: true,
  confidence_dca_guard: {
    safu_score_min: 0.5,
    macd_lift_min: 0.00005,
    rsi_slope_min: 1.0,
    confidence_score_min: 0.75,      // updated from 0.7
    min_confidence_delta: 0.1,       // updated from 0.05
    min_tp1_shift_gain_pct: 1.5,     // updated from 1.10
  },
  soft_confidence_override: {
    enabled: false,
  },
  min_be_improvement_pct: 2.0,
  step_repeat_guard: {
    enabled: true,
    min_conf_delta: 0.10,
    min_tp1_delta: 1.5,
  },
  so_volume_table: [20, 10, 19, 36.1, 68.59, 130.32, 247.61, 470.46, 893.87],
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
    min_pct_gap_from_last_dca: 2.0, // updated from 1.0
  },
  adaptive_step_spacing: {
    enabled: false,
  },
  require_macd_cross: false,
  macd_cross_lookback: 1,
  bottom_reversal_filter: {
    enabled: true,
    macd_lift_min: 0.0003,         // updated from 0.00001
    rsi_slope_min: 0.6,            // updated from 0.45
    local_price_reversal_window: 3,
    lookback_bars: 1,
    rsi_floor: 35,
    candles_required: 5,           // added if missing
  },
};

function CollapsibleSection({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-700 rounded mb-2">
      <button
        className="flex items-center w-full px-2 py-2 text-left bg-gray-900 hover:bg-gray-800 focus:outline-none"
        onClick={() => setOpen((v) => !v)}
        type="button"
      >
        <span className="mr-2">{open ? "▼" : "▶"}</span>
        <span className="font-semibold">{title}</span>
      </button>
      {open && <div className="px-4 pb-4 pt-2">{children}</div>}
    </div>
  );
}

export default function DcaConfigPanel() {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

useEffect(() => {
  fetch("/config/dca")
    .then(res => res.json())
    .then((data) => {
      console.log("Loaded config", data);
      // Handle wrapped config response
      const configData = data.config || data;
      setConfig(configData);
    })
    .catch(() => setError("Failed to load config"));
}, []);

  const updateField = (section, key, value) => {
    setConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  const updateNestedField = (section, nestedKey, key, value) => {
    setConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [nestedKey]: {
          ...prev[section][nestedKey],
          [key]: value,
        },
      },
    }));
  };

  const updateRoot = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const updateListField = (section, key, list) => {
    setConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: list,
      },
    }));
  };

  const handleSave = () => {
    setSaving(true);
    fetch("/config/dca", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config)
    })
      .then(() => setSaving(false))
      .catch(() => {
        setError("Failed to save config");
        setSaving(false);
      });
  };

  const handleReset = () => {
    if (window.confirm("Reset all values to default?")) {
      setConfig({ ...defaultConfig });
    }
  };

  if (!config) return <div>Loading...</div>;

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl">🎛️ DCA Config</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <CollapsibleSection title="🛠️ DCA Config" defaultOpen>
          <FieldGrid>
            <NumericField label="Max Trade USDT" value={config.max_trade_usdt} onChange={(v) => updateRoot("max_trade_usdt", v)} />
            <NumericField label="Base Order USDT" value={config.base_order_usdt} onChange={(v) => updateRoot("base_order_usdt", v)} />
            <NumericField label="Drawdown Trigger %" value={config.drawdown_trigger_pct} onChange={(v) => updateRoot("drawdown_trigger_pct", v)} />
            <NumericField label="SAFU Score Threshold" value={config.safu_score_threshold} onChange={(v) => updateRoot("safu_score_threshold", v)} />
            <NumericField label="Score Decay Min" value={config.score_decay_min} onChange={(v) => updateRoot("score_decay_min", v)} />
            <NumericField label="Buffer Zone %" value={config.buffer_zone_pct} onChange={(v) => updateRoot("buffer_zone_pct", v)} />
            <SwitchField label="Require Indicator Health" checked={config.require_indicator_health} onChange={(v) => updateRoot("require_indicator_health", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🔪 Indicator Thresholds">
          <FieldGrid>
            <NumericField label="RSI" value={config.indicator_thresholds.rsi} onChange={(v) => updateField("indicator_thresholds", "rsi", v)} />
            <NumericField label="MACD Histogram" value={config.indicator_thresholds.macd_histogram} onChange={(v) => updateField("indicator_thresholds", "macd_histogram", v)} />
            <NumericField label="ADX" value={config.indicator_thresholds.adx} onChange={(v) => updateField("indicator_thresholds", "adx", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="📉 BTC Market Guard">
          <FieldGrid>
            <SwitchField label="Use BTC Filter" checked={config.use_btc_filter} onChange={(v) => updateRoot("use_btc_filter", v)} />
            <NumericField label="RSI Max" value={config.btc_indicators.rsi_max} onChange={(v) => updateField("btc_indicators", "rsi_max", v)} />
            <NumericField label="MACD Histogram Max" value={config.btc_indicators.macd_histogram_max} onChange={(v) => updateField("btc_indicators", "macd_histogram_max", v)} />
            <NumericField label="ADX Max" value={config.btc_indicators.adx_max} onChange={(v) => updateField("btc_indicators", "adx_max", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🔀 Recovery Trajectory">
          <FieldGrid>
            <SwitchField label="Use Trajectory Check" checked={config.use_trajectory_check} onChange={(v) => updateRoot("use_trajectory_check", v)} />
            <NumericField label="MACD Lift Min" value={config.trajectory_thresholds.macd_lift_min} onChange={(v) => updateField("trajectory_thresholds", "macd_lift_min", v)} />
            <NumericField label="RSI Slope Min" value={config.trajectory_thresholds.rsi_slope_min} onChange={(v) => updateField("trajectory_thresholds", "rsi_slope_min", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🎯 TP1 Feasibility Guard">
          <FieldGrid>
            <SwitchField label="Require TP1 Feasibility" checked={config.require_tp1_feasibility} onChange={(v) => updateRoot("require_tp1_feasibility", v)} />
            <NumericField label="Max TP1 Shift %" value={config.max_tp1_shift_pct} onChange={(v) => updateRoot("max_tp1_shift_pct", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🚪 Recovery Odds Guard">
          <FieldGrid>
            <SwitchField label="Require Recovery Odds" checked={config.require_recovery_odds} onChange={(v) => updateRoot("require_recovery_odds", v)} />
            <NumericField label="Min Recovery Probability" value={config.min_recovery_probability} onChange={(v) => updateRoot("min_recovery_probability", v)} />
            <NumericField label="Min Confidence Odds" value={config.min_confidence_odds} onChange={(v) => updateRoot("min_confidence_odds", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="💡 Confidence-Based DCA Override">
          <FieldGrid>
            <SwitchField label="Use Confidence Override" checked={config.use_confidence_override} onChange={(v) => updateRoot("use_confidence_override", v)} />
            {Object.entries(config.confidence_dca_guard).map(([k, v]) => (
              <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("confidence_dca_guard", k, val)} />
            ))}
            <SwitchField label="Use Soft Confidence Override" checked={config.soft_confidence_override?.enabled} onChange={(v) => updateField("soft_confidence_override", "enabled", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="⚖️ Minimum Impact Guard">
          <FieldGrid>
            <NumericField label="Min BE Improvement %" value={config.min_be_improvement_pct} onChange={(v) => updateRoot("min_be_improvement_pct", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🔁 Step Repeat Guard">
          <FieldGrid>
            <SwitchField
              label="Enabled"
              checked={config.step_repeat_guard?.enabled}
              onChange={(v) => updateField("step_repeat_guard", "enabled", v)}
            />
            <NumericField
              label="Min Confidence Delta"
              value={config.step_repeat_guard?.min_conf_delta}
              onChange={(val) => updateField("step_repeat_guard", "min_conf_delta", val)}
            />
            <NumericField
              label="Min TP1 Delta"
              value={config.step_repeat_guard?.min_tp1_delta}
              onChange={(val) => updateField("step_repeat_guard", "min_tp1_delta", val)}
            />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="📊 Smart SO Volume Logic">
          <ListNumericField
            label="SO Volume Table"
            values={config.so_volume_table}
            onChange={(list) => updateRoot("so_volume_table", list)}
          />
        </CollapsibleSection>

        <CollapsibleSection title="🎯 TP1 Reference Distances">
          <ListNumericField
            label="TP1 Targets"
            values={config.tp1_targets}
            onChange={(list) => updateRoot("tp1_targets", list)}
          />
        </CollapsibleSection>

        <CollapsibleSection title="💀 Zombie Tag Detection">
          <FieldGrid>
            <SwitchField label="Enabled" checked={config.zombie_tag.enabled} onChange={(v) => updateField("zombie_tag", "enabled", v)} />
            <NumericField label="Min Drawdown %" value={config.zombie_tag.min_drawdown_pct} onChange={(v) => updateField("zombie_tag", "min_drawdown_pct", v)} />
            <NumericField label="Max Drawdown %" value={config.zombie_tag.max_drawdown_pct} onChange={(v) => updateField("zombie_tag", "max_drawdown_pct", v)} />
            <NumericField label="Max Score" value={config.zombie_tag.max_score} onChange={(v) => updateField("zombie_tag", "max_score", v)} />
            <SwitchField label="Require Zero Recovery Odds" checked={config.zombie_tag.require_zero_recovery_odds} onChange={(v) => updateField("zombie_tag", "require_zero_recovery_odds", v)} />
            <NumericField label="Max MACD Lift" value={config.zombie_tag.max_macd_lift} onChange={(v) => updateField("zombie_tag", "max_macd_lift", v)} />
            <NumericField label="Max RSI Slope" value={config.zombie_tag.max_rsi_slope} onChange={(v) => updateField("zombie_tag", "max_rsi_slope", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🤖 ML Spend Model">
          <FieldGrid>
            <SwitchField label="Use ML Spend Model" checked={config.use_ml_spend_model} onChange={(v) => updateRoot("use_ml_spend_model", v)} />
            <NumericField label="Min Volume" value={config.spend_adjustment_rules.min_volume} onChange={(v) => updateField("spend_adjustment_rules", "min_volume", v)} />
            <NumericField label="Max Multiplier" value={config.spend_adjustment_rules.max_multiplier} onChange={(v) => updateField("spend_adjustment_rules", "max_multiplier", v)} />
            <NumericField label="TP1 Shift Soft Cap" value={config.spend_adjustment_rules.tp1_shift_soft_cap} onChange={(v) => updateField("spend_adjustment_rules", "tp1_shift_soft_cap", v)} />
            <NumericField label="Low DD % Limit" value={config.spend_adjustment_rules.low_dd_pct_limit} onChange={(v) => updateField("spend_adjustment_rules", "low_dd_pct_limit", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🔊 Logging Options">
          <FieldGrid>
            <SwitchField label="Verbose Logging" checked={config.log_verbose} onChange={(v) => updateRoot("log_verbose", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🚦 Step Price Enforcement">
          <FieldGrid>
            <SwitchField label="Enforce Price Below Last Step" checked={config.enforce_price_below_last_step} onChange={(v) => updateRoot("enforce_price_below_last_step", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🚥 Trailing Step Guard">
          <FieldGrid>
            <SwitchField label="Enabled" checked={config.trailing_step_guard?.enabled} onChange={(v) => updateField("trailing_step_guard", "enabled", v)} />
            <NumericField label="Min % Gap From Last DCA" value={config.trailing_step_guard?.min_pct_gap_from_last_dca} onChange={(v) => updateField("trailing_step_guard", "min_pct_gap_from_last_dca", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="📏 Adaptive Step Spacing">
          <FieldGrid>
            <SwitchField label="Enabled" checked={config.adaptive_step_spacing?.enabled} onChange={(v) => updateField("adaptive_step_spacing", "enabled", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🔄 MACD Cross Filter">
          <FieldGrid>
            <SwitchField label="Require MACD Cross" checked={config.require_macd_cross} onChange={(v) => updateRoot("require_macd_cross", v)} />
            <NumericField label="MACD Cross Lookback" value={config.macd_cross_lookback} onChange={(v) => updateRoot("macd_cross_lookback", v)} />
          </FieldGrid>
        </CollapsibleSection>

        <CollapsibleSection title="🟢 Bottom Reversal Filter">
          <FieldGrid>
            <SwitchField
              label="Enable Bottom Reversal Filter"
              checked={config.bottom_reversal_filter?.enabled ?? false}
              onChange={v => updateField("bottom_reversal_filter", "enabled", v)}
            />
            <NumericField
              label="Min RSI Slope"
              value={
                config.bottom_reversal_filter?.rsi_slope_min !== undefined
                  ? config.bottom_reversal_filter.rsi_slope_min
                  : 0.1
              }
              onChange={v => updateField("bottom_reversal_filter", "rsi_slope_min", v)}
            />
            <NumericField
              label="Min MACD Lift"
              value={
                config.bottom_reversal_filter?.macd_lift_min !== undefined
                  ? config.bottom_reversal_filter.macd_lift_min
                  : 0.0
              }
              onChange={v => updateField("bottom_reversal_filter", "macd_lift_min", v)}
              step={0.00001}
            />
            <NumericField
              label="Lookback Bars"
              value={
                config.bottom_reversal_filter?.lookback_bars !== undefined
                  ? config.bottom_reversal_filter.lookback_bars
                  : 3
              }
              onChange={v => updateField("bottom_reversal_filter", "lookback_bars", v)}
            />
            <NumericField
              label="Local Price Reversal Window"
              value={
                config.bottom_reversal_filter?.local_price_reversal_window !== undefined
                  ? config.bottom_reversal_filter.local_price_reversal_window
                  : 3
              }
              onChange={v => updateField("bottom_reversal_filter", "local_price_reversal_window", v)}
            />
            <NumericField
              label="RSI Floor"
              value={
                config.bottom_reversal_filter?.rsi_floor !== undefined
                  ? config.bottom_reversal_filter.rsi_floor
                  : ""
              }
              onChange={v => updateField("bottom_reversal_filter", "rsi_floor", v)}
            />
            <NumericField
              label="Candles Required"
              value={
                config.bottom_reversal_filter?.candles_required !== undefined
                  ? config.bottom_reversal_filter.candles_required
                  : 5
              }
              onChange={v => updateField("bottom_reversal_filter", "candles_required", v)}
            />
          </FieldGrid>
        </CollapsibleSection>

        <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-4 sm:space-y-0 mt-8">
          <Button size="lg" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save Config"}
          </Button>
          <Button size="lg" variant="danger" onClick={handleReset}>
            Reset to Default
          </Button>
        </div>
        {error && <p className="mt-4 text-red-400 text-sm">{error}</p>}
      </CardContent>
    </Card>
  );
}

function Section({ title, children }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {children}
    </div>
  );
}

function FieldGrid({ children }) {
  return <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-6 items-end">{children}</div>;
}

function NumericField({ label, value, onChange }) {
  return (
    <FormField label={label}>
      <Input
        type="number"
        value={value}
        className="w-full max-w-[9rem] bg-gray-800 border-gray-600 text-white"
        onChange={(e) => {
          const val = e.target.value;
          if (val === "") {
            onChange(undefined);
          } else {
            onChange(parseFloat(val));
          }
        }}
      />
    </FormField>
  );
}

function SwitchField({ label, checked, onChange }) {
  return (
    <FormField label={label}>
      <Switch checked={checked} onCheckedChange={onChange} />
    </FormField>
  );
}

function ListNumericField({ label, values, onChange }) {
  const handleChange = (index, newValue) => {
    const newList = [...values];
    newList[index] = newValue;
    onChange(newList);
  };

  const handleAdd = () => {
    onChange([...values, 0]);
  };

  const handleRemove = (index) => {
    const newList = values.filter((_, i) => i !== index);
    onChange(newList);
  };

  return (
    <FormField label={label}>
      <div className="space-y-2">
        {values.map((val, idx) => (
          <div key={idx} className="flex items-center space-x-2">
            <Input
              type="number"
              value={val}
              className="w-24 bg-gray-800 border-gray-600 text-white"
              onChange={(e) => {
                const v = e.target.value;
                if (v === "") {
                  handleChange(idx, undefined);
                } else {
                  handleChange(idx, parseFloat(v));
                }
              }}
            />
            <Button size="sm" variant="danger" onClick={() => handleRemove(idx)}>
              Remove
            </Button>
          </div>
        ))}
        <Button size="sm" onClick={handleAdd}>
          Add
        </Button>
      </div>
    </FormField>
  );
}
