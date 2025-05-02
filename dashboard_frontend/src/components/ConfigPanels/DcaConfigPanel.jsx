// src/components/ConfigPanels/DcaConfigPanel.jsx
import React, { useEffect, useState } from "react";
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
import axios from "axios";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "../ui/Collapsible";

const prettyLabel = (key) =>
  key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

export default function DcaConfigPanel() {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    axios
      .get("/config/dca")
      .then((res) => setConfig(res.data))
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

  const updateRoot = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    setSaving(true);
    axios
      .post("/config/dca", config)
      .then(() => setSaving(false))
      .catch(() => setError("Failed to save config"));
  };

  const handleReset = () => {
    if (window.confirm("Reset all values to default?")) {
      window.location.reload();
    }
  };

  if (!config) return <p className="p-4 text-sm">Loading config…</p>;

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl">🎛️ DCA Config</CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        <Section title="🛠️ DCA Config">
          <FieldGrid>
            <NumericField label="Max Trade USDT" value={config.max_trade_usdt} onChange={(v) => updateRoot("max_trade_usdt", v)} />
            <NumericField label="Base Order USDT" value={config.base_order_usdt} onChange={(v) => updateRoot("base_order_usdt", v)} />
            <NumericField label="Drawdown Trigger %" value={config.drawdown_trigger_pct} onChange={(v) => updateRoot("drawdown_trigger_pct", v)} />
            <NumericField label="SAFU Score Threshold" value={config.safu_score_threshold} onChange={(v) => updateRoot("safu_score_threshold", v)} />
            <NumericField label="Score Decay Min" value={config.score_decay_min} onChange={(v) => updateRoot("score_decay_min", v)} />
            <NumericField label="Buffer Zone %" value={config.buffer_zone_pct} onChange={(v) => updateRoot("buffer_zone_pct", v)} />
            <SwitchField label="Require Indicator Health" checked={config.require_indicator_health} onChange={(v) => updateRoot("require_indicator_health", v)} />
          </FieldGrid>
        </Section>

        <Section title="🔪 Indicator Thresholds">
          <FieldGrid>
            {Object.entries(config.indicator_thresholds).map(([k, v]) => (
              <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("indicator_thresholds", k, val)} />
            ))}
          </FieldGrid>
        </Section>

        <Section title="📉 BTC Market Filter">
          <FieldGrid>
            <SwitchField label="Use BTC Filter" checked={config.use_btc_filter} onChange={(v) => updateRoot("use_btc_filter", v)} />
            {Object.entries(config.btc_indicators).map(([k, v]) => (
              <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("btc_indicators", k, val)} />
            ))}
          </FieldGrid>
        </Section>

        <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
          <CollapsibleTrigger>
            <p className="text-blue-400 cursor-pointer text-sm hover:underline">▶ Advanced Settings</p>
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-6 mt-4">
            <Section title="🔀 Trajectory Check">
              <FieldGrid>
                <SwitchField label="Use Trajectory Check" checked={config.use_trajectory_check} onChange={(v) => updateRoot("use_trajectory_check", v)} />
                {Object.entries(config.trajectory_thresholds).map(([k, v]) => (
                  <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("trajectory_thresholds", k, val)} />
                ))}
              </FieldGrid>
            </Section>

            <Section title="🎯 TP1 Feasibility">
              <FieldGrid>
                <SwitchField label="Require TP1 Feasibility" checked={config.require_tp1_feasibility} onChange={(v) => updateRoot("require_tp1_feasibility", v)} />
                <NumericField label="Max TP1 Shift %" value={config.max_tp1_shift_pct} onChange={(v) => updateRoot("max_tp1_shift_pct", v)} />
              </FieldGrid>
            </Section>

            <Section title="🚪 Recovery Odds Gate">
              <FieldGrid>
                <SwitchField label="Require Recovery Odds" checked={config.require_recovery_odds} onChange={(v) => updateRoot("require_recovery_odds", v)} />
                <NumericField label="Min Recovery Probability" value={config.min_recovery_probability} onChange={(v) => updateRoot("min_recovery_probability", v)} />
                <NumericField label="Min Confidence Odds" value={config.min_confidence_odds} onChange={(v) => updateRoot("min_confidence_odds", v)} />
              </FieldGrid>
            </Section>

            <Section title="💡 Confidence DCA Guard">
              <FieldGrid>
                <SwitchField label="Use Confidence Override" checked={config.use_confidence_override} onChange={(v) => updateRoot("use_confidence_override", v)} />
                {Object.entries(config.confidence_dca_guard).map(([k, v]) => (
                  <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("confidence_dca_guard", k, val)} />
                ))}
              </FieldGrid>
            </Section>

            <Section title="🧪 Soft Confidence Rescue">
              <FieldGrid>
                {Object.entries(config.soft_confidence_override).map(([k, v]) => (
                  <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("soft_confidence_override", k, val)} />
                ))}
              </FieldGrid>
            </Section>

            <Section title="💀 Zombie Detection">
              <FieldGrid>
                <SwitchField label="Enabled" checked={config.zombie_tag.enabled} onChange={(v) => updateField("zombie_tag", "enabled", v)} />
                {Object.entries(config.zombie_tag).filter(([k]) => k !== "enabled").map(([k, v]) => (
                  <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("zombie_tag", k, val)} />
                ))}
              </FieldGrid>
            </Section>

            <Section title="🤖 ML Spend Model">
              <FieldGrid>
                <SwitchField label="Use ML Spend Model" checked={config.use_ml_spend_model} onChange={(v) => updateRoot("use_ml_spend_model", v)} />
                {Object.entries(config.spend_adjustment_rules).map(([k, v]) => (
                  <NumericField key={k} label={prettyLabel(k)} value={v} onChange={(val) => updateField("spend_adjustment_rules", k, val)} />
                ))}
              </FieldGrid>
            </Section>

            <Section title="🔊 Logging">
              <FieldGrid>
                <SwitchField label="Verbose Logging" checked={config.log_verbose} onChange={(v) => updateRoot("log_verbose", v)} />
              </FieldGrid>
            </Section>
          </CollapsibleContent>
        </Collapsible>

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
