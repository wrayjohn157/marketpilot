// src/components/ConfigPanels/TvScreenerConfigPanel.jsx
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

// Default configuration
const DEFAULT_CONFIG = {
  enabled: false,
  disable_if_btc_unhealthy: false,
  weights: {
    macd_histogram: 0.2,
    rsi_recovery: 0.2,
    stoch_rsi_cross: 0.2,
    adx_rising: 0.15,
    ema_price_reclaim: 0.15,
    mean_reversion_score: 0.2,
  },
  score_threshold: 0.7,
};

export default function TvScreenerConfigPanel() {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    fetch("/config/tv_screener")
      .then((res) => res.json())
      .then((data) => {
        const cfg = data || {};
        const safe = {
          enabled: cfg.enabled ?? false,
          disable_if_btc_unhealthy: cfg.disable_if_btc_unhealthy ?? false,
          weights: cfg.weights ?? {},
          score_threshold: cfg.score_threshold ?? 0.7,
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
      const response = await fetch("/config/tv_screener", {
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
      const response = await fetch("/config/tv_screener/default");
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
        <CardTitle className="text-2xl">⚙️ TV Screener Config</CardTitle>
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
          <div className="flex items-center space-x-2">
            <Switch
              checked={config.enabled}
              onCheckedChange={(checked) => updateField("enabled", checked)}
            />
            <label className="text-sm">Enabled</label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              checked={config.disable_if_btc_unhealthy}
              onCheckedChange={(checked) => updateField("disable_if_btc_unhealthy", checked)}
            />
            <label className="text-sm">Disable if BTC Unhealthy</label>
          </div>

          <FormField label="Score Threshold">
            <Input
              type="number"
              step="0.01"
              value={config.score_threshold}
              onChange={(e) => updateField("score_threshold", parseFloat(e.target.value))}
              className="bg-gray-800 border-gray-600 text-white"
            />
          </FormField>
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
