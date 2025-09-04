// src/components/ConfigPanels/SafuConfigPanel.jsx
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

const prettyLabel = (key) =>
  key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

const btcStatusOptions = [
  "any",
  "not_bearish",
  "safe",
  "bullish_only"
];

// Default configuration
const DEFAULT_CONFIG = {
  min_score: 0.4,
  telegram_alerts: true,
  auto_close: false,
  weights: {
    macd_histogram: 0.2,
    rsi_recovery: 0.2,
    stoch_rsi_cross: 0.2,
    adx_rising: 0.15,
    ema_price_reclaim: 0.15,
    mean_reversion_score: 0.2,
  },
  safu_reentry: {
    enabled: true,
    require_btc_status: "not_bearish",
    cooldown_minutes: 30,
    min_macd_lift: 0.00005,
    min_rsi_slope: 1.0,
    min_safu_score: 0.4,
    allow_if_tp1_shift_under_pct: 12.5,
  }
};

export default function SafuConfigPanel() {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    fetch("/config/safu")
      .then(res => res.json())
      .then((data) => {
        const cfg = data || {};
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
      .catch(() => setError("Failed to load config"));
  }, []);

  const updateField = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const updateNestedField = (section, key, value) => {
    setConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch("/config/safu", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
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

  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to reset to default configuration? This will overwrite all current settings.")) {
      return;
    }
    
    setSaving(true);
    setError(null);
    setSuccess(null);
    
    try {
      // Load defaults from server
      const response = await fetch("/config/safu/default");
      if (response.ok) {
        const defaultConfig = await response.json();
        setConfig(defaultConfig);
        setSuccess("Configuration reset to defaults!");
        setTimeout(() => setSuccess(null), 3000);
      } else {
        // Fallback to local defaults
        setConfig({ ...DEFAULT_CONFIG });
        setSuccess("Configuration reset to defaults!");
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      // Fallback to local defaults
      setConfig({ ...DEFAULT_CONFIG });
      setSuccess("Configuration reset to defaults!");
      setTimeout(() => setSuccess(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  if (!config) return <p className="p-4 text-sm">Loading…</p>;

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl">⚙️ SAFU Config</CardTitle>
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
        {/* Basic Settings */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <FormField label="Minimum Score">
            <Input
              type="number"
              step="0.01"
              value={config.min_score}
              onChange={(e) => updateField("min_score", parseFloat(e.target.value))}
              className="bg-gray-800 border-gray-600 text-white"
            />
          </FormField>
          
          <div className="flex items-center space-x-2">
            <Switch
              checked={config.telegram_alerts}
              onCheckedChange={(checked) => updateField("telegram_alerts", checked)}
            />
            <label className="text-sm">Telegram Alerts</label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Switch
              checked={config.auto_close}
              onCheckedChange={(checked) => updateField("auto_close", checked)}
            />
            <label className="text-sm">Auto Close</label>
          </div>
        </div>

        {/* Weights */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Weights</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(config.weights || {}).map(([key, value]) => (
              <FormField key={key} label={prettyLabel(key)}>
                <Input
                  type="number"
                  step="0.01"
                  value={value}
                  onChange={(e) => updateNestedField("weights", key, parseFloat(e.target.value))}
                  className="bg-gray-800 border-gray-600 text-white"
                />
              </FormField>
            ))}
          </div>
        </div>

        {/* SAFU Reentry */}
        <div>
          <h3 className="text-lg font-semibold mb-4">SAFU Reentry</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <Switch
                checked={config.safu_reentry?.enabled}
                onCheckedChange={(checked) => updateNestedField("safu_reentry", "enabled", checked)}
              />
              <label className="text-sm">Enabled</label>
            </div>
            
            <FormField label="Require BTC Status">
              <select
                value={config.safu_reentry?.require_btc_status}
                onChange={(e) => updateNestedField("safu_reentry", "require_btc_status", e.target.value)}
                className="bg-gray-800 border-gray-600 text-white px-3 py-2 rounded"
              >
                {btcStatusOptions.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </FormField>
            
            <FormField label="Cooldown Minutes">
              <Input
                type="number"
                value={config.safu_reentry?.cooldown_minutes}
                onChange={(e) => updateNestedField("safu_reentry", "cooldown_minutes", parseInt(e.target.value))}
                className="bg-gray-800 border-gray-600 text-white"
              />
            </FormField>
            
            <FormField label="Min MACD Lift">
              <Input
                type="number"
                step="0.00001"
                value={config.safu_reentry?.min_macd_lift}
                onChange={(e) => updateNestedField("safu_reentry", "min_macd_lift", parseFloat(e.target.value))}
                className="bg-gray-800 border-gray-600 text-white"
              />
            </FormField>
            
            <FormField label="Min RSI Slope">
              <Input
                type="number"
                step="0.1"
                value={config.safu_reentry?.min_rsi_slope}
                onChange={(e) => updateNestedField("safu_reentry", "min_rsi_slope", parseFloat(e.target.value))}
                className="bg-gray-800 border-gray-600 text-white"
              />
            </FormField>
            
            <FormField label="Min SAFU Score">
              <Input
                type="number"
                step="0.01"
                value={config.safu_reentry?.min_safu_score}
                onChange={(e) => updateNestedField("safu_reentry", "min_safu_score", parseFloat(e.target.value))}
                className="bg-gray-800 border-gray-600 text-white"
              />
            </FormField>
            
            <FormField label="Allow if TP1 Shift Under %">
              <Input
                type="number"
                step="0.1"
                value={config.safu_reentry?.allow_if_tp1_shift_under_pct}
                onChange={(e) => updateNestedField("safu_reentry", "allow_if_tp1_shift_under_pct", parseFloat(e.target.value))}
                className="bg-gray-800 border-gray-600 text-white"
              />
            </FormField>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-4 sm:space-y-0 mt-8">
          <Button size="lg" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save Config"}
          </Button>
          <Button size="lg" variant="danger" onClick={handleReset} disabled={saving}>
            {saving ? "Resetting…" : "Reset to Default"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}