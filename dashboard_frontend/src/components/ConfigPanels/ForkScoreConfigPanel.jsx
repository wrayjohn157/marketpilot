// src/components/ConfigPanels/ForkScoreConfigPanel.jsx
import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/Card";
import { FormField } from "../ui/FormField";
import { Switch } from "../ui/Switch";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

// Default configuration
const DEFAULT_CONFIG = {
  min_score: 0.73,
  weights: {
    macd_histogram: 0.2,
    macd_bearish_cross: -0.25,
    rsi_recovery: 0.2,
    stoch_rsi_cross: 0.2,
    stoch_overbought_penalty: -0.15,
    adx_rising: 0.15,
    ema_price_reclaim: 0.15,
    mean_reversion_score: 0.2,
    volume_penalty: -0.25,
    stoch_rsi_slope: 0.2,
  },
  options: {
    use_stoch_ob_penalty: true,
    use_volume_penalty: true,
    use_macd_bearish_check: false,
  },
};

export default function ForkScoreConfigPanel() {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Load config on mount
  useEffect(() => {
    fetch("/config/fork_score")
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(() => setError("Failed to load config"));
  }, []);

  const updateSection = (section, key, value) =>
    setConfig(c => ({ ...c, [section]: { ...c[section], [key]: value } }));

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/config/fork_score", {
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
      const response = await fetch("/config/fork_score/default");
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

  // Pretty label for toggles
  const prettyToggleLabel = k =>
    k.replace(/^use_/, "")
     .replace(/_/g, " ")
     .replace(/\b\w/g, c => c.toUpperCase());

  // Pretty label for general use
  const prettyLabel = k =>
    k.replace(/_/g, " ")
     .replace(/\b\w/g, c => c.toUpperCase());

  if (!config) return <p className="p-4 text-sm">Loading…</p>;

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl">⚙️ Fork Score Config</CardTitle>
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
      <CardContent>
        {/* --- WEIGHTS GRID --- */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Minimum Score */}
          <FormField label="Minimum Score">
            <Input
              type="number"
              step="0.01"
              value={config.min_score}
              onChange={(e) => setConfig(c => ({ ...c, min_score: parseFloat(e.target.value) }))}
              className="bg-gray-800 border-gray-600 text-white"
            />
          </FormField>

          {/* Weight Controls */}
          {Object.entries(config.weights || {}).map(([key, value]) => (
            <FormField key={key} label={prettyLabel(key)}>
              <Input
                type="number"
                step="0.01"
                value={value}
                onChange={(e) => updateSection("weights", key, parseFloat(e.target.value))}
                className="bg-gray-800 border-gray-600 text-white"
              />
            </FormField>
          ))}
        </div>

        {/* --- OPTIONS TOGGLES --- */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">Options</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(config.options || {}).map(([key, value]) => (
              <div key={key} className="flex items-center space-x-2">
                <Switch
                  checked={value}
                  onCheckedChange={(checked) => updateSection("options", key, checked)}
                />
                <label className="text-sm">{prettyToggleLabel(key)}</label>
              </div>
            ))}
          </div>
        </div>

        {/* --- ACTION BUTTONS --- */}
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
