// src/components/ConfigPanels/TvScreenerConfigPanel.jsx
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

export default function TvScreenerConfigPanel() {
  const [config, setConfig] = useState(null);
  const [original, setOriginal] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get("/config/tv_screener").then((res) => {
      const cfg = res.data.tv_screener || {};
      const safe = {
        enabled: cfg.enabled ?? false,
        disable_if_btc_unhealthy: cfg.disable_if_btc_unhealthy ?? false,
        weights: cfg.weights ?? {},
        score_threshold: cfg.score_threshold ?? 0.7,
      };
      setConfig(safe);
      setOriginal(JSON.stringify(safe));
    }).catch(() => setError("Failed to load config"));
  }, []);

  const handleSave = () => {
    setSaving(true);
    axios.post("/config/tv_screener", { tv_screener: config })
      .then(() => {
        setOriginal(JSON.stringify(config));
        setSaving(false);
      })
      .catch(() => setError("Failed to save config"));
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

  if (!config) return <p className="p-4 text-sm">Loading config…</p>;

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl">📺 TV Screener Config
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        <Section title="⚙️ Screener Settings">
          <FieldGrid>
            <SwitchField
              label="Enable TV Screener"
              checked={config.enabled}
              onChange={(v) => updateField("enabled", v)}
            />
            <SwitchField
              label="Disable if BTC is Unhealthy"
              checked={config.disable_if_btc_unhealthy}
              onChange={(v) => updateField("disable_if_btc_unhealthy", v)}
            />
            <NumericField
              label="Score Threshold"
              value={config.score_threshold}
              onChange={(val) => updateField("score_threshold", val)}
            />
          </FieldGrid>
        </Section>

        <Section title="📊 Signal Weights">
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
        onChange={(e) => onChange(parseFloat(e.target.value))}
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
