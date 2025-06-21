// src/components/ConfigPanels/SafuConfigPanel.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../ui/Card";
import { FormField } from "../ui/FormField";
import { Input } from "../ui/Input";
import { Switch } from "../ui/Switch";
import { Button } from "../ui/Button";

const prettyLabel = (key) =>
  key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

const btcStatusOptions = [
  "any",
  "not_bearish",
  "safe",
  "bullish_only"
];

export default function SafuConfigPanel() {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get("/config/safu")
      .then((res) => {
        const cfg = res.data || {};
        const safe = {
          min_score: cfg.min_score ?? 0.4,
          telegram_alerts: cfg.telegram_alerts ?? true,
          auto_close: cfg.auto_close ?? false,
          weights: cfg.weights ?? {},
          safu_reentry: {
            enabled: cfg.safu_reentry?.enabled ?? true,
            require_btc_status: cfg.safu_reentry?.require_btc_status ?? "not_bearish",
            cooldown_minutes: cfg.safu_reentry?.cooldown_minutes ?? 30,
            min_macd_lift: cfg.safu_reentry?.min_macd_lift ?? 0.00005,
            min_rsi_slope: cfg.safu_reentry?.min_rsi_slope ?? 1.0,
            min_safu_score: cfg.safu_reentry?.min_safu_score ?? 0.4,
            allow_if_tp1_shift_under_pct: cfg.safu_reentry?.allow_if_tp1_shift_under_pct ?? 12.5,
          }
        };
        setConfig(safe);
      })
      .catch(() => setError("Failed to load SAFU config"));
  }, []);

  const handleSave = () => {
    setSaving(true);
    axios.post("/config/safu", config)
      .then(() => setSaving(false))
      .catch(() => setError("Failed to save SAFU config"));
  };

  const handleReset = () => {
    if (window.confirm("Reset all values to default?")) {
      window.location.reload();
    }
  };

  const updateField = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const updateWeight = (key, value) => {
    setConfig((prev) => ({
      ...prev,
      weights: { ...prev.weights, [key]: value }
    }));
  };

  const updateReentry = (key, value) => {
    setConfig((prev) => ({
      ...prev,
      safu_reentry: { ...prev.safu_reentry, [key]: value }
    }));
  };

  if (!config) return <p className="p-4 text-sm">Loading SAFU config…</p>;

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl">🛡️ SAFU Config</CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        <Section title="⚙️ General Settings">
          <FieldGrid>
            <NumericField label="Min Score" value={config.min_score} onChange={(v) => updateField("min_score", v)} />
            <SwitchField label="Telegram Alerts" checked={config.telegram_alerts} onChange={(v) => updateField("telegram_alerts", v)} />
            <SwitchField label="Auto Close" checked={config.auto_close} onChange={(v) => updateField("auto_close", v)} />
          </FieldGrid>
        </Section>

        <Section title="📊 SAFU Weights">
          <FieldGrid>
            {Object.entries(config.weights || {}).map(([key, val]) => (
              <NumericField
                key={key}
                label={prettyLabel(key)}
                value={val}
                onChange={(val) => updateWeight(key, val)}
              />
            ))}
          </FieldGrid>
        </Section>

        <Section title="🔁 SAFU Reentry Settings">
          <FieldGrid>
            <SwitchField
              label="Enable SAFU Reentry"
              checked={config.safu_reentry.enabled}
              onChange={(v) => updateReentry("enabled", v)}
            />
            <SelectField
              label="Require BTC Status"
              value={config.safu_reentry.require_btc_status}
              onChange={(val) => updateReentry("require_btc_status", val)}
              options={btcStatusOptions}
            />
            <NumericField
              label="Cooldown Minutes"
              value={config.safu_reentry.cooldown_minutes}
              onChange={(val) => updateReentry("cooldown_minutes", val)}
            />
            <NumericField
              label="Min MACD Lift"
              value={config.safu_reentry.min_macd_lift}
              onChange={(val) => updateReentry("min_macd_lift", val)}
            />
            <NumericField
              label="Min RSI Slope"
              value={config.safu_reentry.min_rsi_slope}
              onChange={(val) => updateReentry("min_rsi_slope", val)}
            />
            <NumericField
              label="Min SAFU Score"
              value={config.safu_reentry.min_safu_score}
              onChange={(val) => updateReentry("min_safu_score", val)}
            />
            <NumericField
              label="Allow TP1 Shift Under %"
              value={config.safu_reentry.allow_if_tp1_shift_under_pct}
              onChange={(val) => updateReentry("allow_if_tp1_shift_under_pct", val)}
            />
          </FieldGrid>
        </Section>

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
        step="any"
        value={value}
        className="w-full max-w-[9rem] bg-gray-800 border-gray-600 text-white"
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </FormField>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <FormField label={label}>
      <select
        className="w-full max-w-[12rem] bg-gray-800 border-gray-600 text-white p-2 rounded"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {prettyLabel(opt)}
          </option>
        ))}
      </select>
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
