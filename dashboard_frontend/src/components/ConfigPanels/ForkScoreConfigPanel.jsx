// src/components/ConfigPanels/ForkScoreConfigPanel.jsx
import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/Card";
import { FormField } from "../ui/FormField";
import { Switch } from "../ui/Switch";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import axios from "axios";

// baked-in defaults
const defaultConfig = {
  min_score: 0.73,
  weights: {
    macd_histogram:             0.2,
    macd_bearish_cross:        -0.25,
    rsi_recovery:               0.2,
    stoch_rsi_cross:            0.2,
    stoch_overbought_penalty:  -0.15,
    adx_rising:                 0.15,
    ema_price_reclaim:          0.15,
    mean_reversion_score:       0.2,
    volume_penalty:            -0.25,
    stoch_rsi_slope:            0.2,
  },
  options: {
    use_stoch_ob_penalty:  true,
    use_volume_penalty:    true,
    use_macd_bearish_check:false,
  },
};

export default function ForkScoreConfigPanel() {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // load on mount
  useEffect(() => {
    axios.get("/config/fork_score/")
      .then(r => setConfig(r.data))
      .catch(() => setError("Failed to load"));
  }, []);

  const updateSection = (section, key, value) =>
    setConfig(c => ({ ...c, [section]: { ...c[section], [key]: value } }));

  const handleSave = () => {
    setSaving(true);
    axios.post("/config/fork_score/", config)
      .finally(() => setSaving(false))
      .catch(() => setError("Saving failed"));
  };

  const handleReset = () => {
    if (window.confirm("Reset all values to defaults?")) {
      setConfig(defaultConfig);
    }
  };

  // pretty label for toggles
  const prettyToggleLabel = k =>
    k.replace(/^use_/, "")
     .replace(/_/g, " ")
     .replace(/\b\w/g, c => c.toUpperCase());

  if (!config) return <p className="p-4 text-sm">Loading…</p>;

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl">⚙️ Fork Score Config</CardTitle>
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
              onChange={e =>
                updateSection("min_score", "", parseFloat(e.target.value))
              }
              className="w-24 sm:w-32 bg-gray-800 border-gray-600 text-white"
            />
          </FormField>

          {/* All other weight fields */}
          {Object.entries(config.weights).map(([key, val]) => (
            <FormField
              key={key}
              label={key
                .replace(/_/g, " ")
                .replace(/\b\w/g, c => c.toUpperCase())}
            >
              <Input
                type="number"
                step="0.01"
                value={val}
                onChange={e =>
                  updateSection("weights", key, parseFloat(e.target.value))
                }
                className="w-24 sm:w-32 bg-gray-800 border-gray-600 text-white"
              />
            </FormField>
          ))}
        </div>

        <hr className="my-6 border-gray-700" />

        {/* --- TOGGLES GRID --- */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(config.options).map(([key, val]) => (
            <FormField key={key} label={prettyToggleLabel(key)}>
              <Switch
                checked={val}
                onCheckedChange={() =>
                  updateSection("options", key, !val)
                }
              />
            </FormField>
          ))}
        </div>

        <hr className="my-6 border-gray-700" />

        {/* --- ACTION BUTTONS --- */}
        <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-4 sm:space-y-0">
          <Button size="lg" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save Config"}
          </Button>
          <Button size="lg" variant="danger" onClick={handleReset}>
            Reset to Default
          </Button>
        </div>

        {error && <p className="mt-4 text-red-400">{error}</p>}
      </CardContent>
    </Card>
  );
}
