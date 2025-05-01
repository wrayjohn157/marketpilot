import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { Menu, X } from "lucide-react";

const links = [
  { label: "Dashboard", icon: "📊", path: "/dashboard" },
  { label: "Active Trades", icon: "📈", path: "/active-trades" },
  { label: "Scan Review", icon: "🔍", path: "/scan-review" },
  { label: "DCA Tracker", icon: "📊", path: "/dca-tracker" },
  { label: "Backtest", icon: "📚", path: "/backtest-summary" },
  { label: "ML Monitor", icon: "🤖", path: "/ml-monitor" },
  { label: "BTC Panel", icon: "⚠️", path: "/btc-panel" },
  { label: "Fork Config", icon: "🛠️", path: "/fork-score" },  // ✅ NEW
];

export default function Sidebar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="md:hidden flex items-center justify-between p-4 bg-gray-900 border-b border-gray-800">
        <span className="text-lg font-bold text-white">🧠 MarketPilot v2 🚧</span>
        <button
          onClick={() => setOpen(!open)}
          className="text-white focus:outline-none"
        >
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 z-40 h-full w-64 bg-gray-900 p-4 space-y-4 border-r border-gray-800 transform transition-transform duration-300
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:static md:translate-x-0 md:w-56 md:min-h-screen`}
      >
        <div className="text-xl font-bold text-white mb-6 hidden md:block">
          🧠 MarketPilot v2 🚧
        </div>
        {links.map((link) => (
          <NavLink
            key={link.path}
            to={link.path}
            className={({ isActive }) =>
              `block py-2 px-3 rounded hover:bg-gray-800 transition-all ${
                isActive ? "bg-gray-800 text-green-400 font-semibold" : "text-gray-300"
              }`
            }
            onClick={() => setOpen(false)}
          >
            <span className="mr-2">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </div>
    </>
  );
}
