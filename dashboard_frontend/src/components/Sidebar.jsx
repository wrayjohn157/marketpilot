// src/components/Sidebar.jsx
import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { Menu, X, HelpCircle, PlayCircle } from "lucide-react";

const links = [
  { label: "Dashboard", icon: "📊", path: "/dashboard" },
  { label: "Active Trades", icon: "📈", path: "/active-trades" },
  { label: "Scan Review", icon: "🔍", path: "/scan-review" },
  { label: "DCA Tracker", icon: "📊", path: "/dca-tracker" },
  { label: "DCA Strategy Builder", icon: "📐", path: "/dca-tuner" },
  { label: "ML Monitor", icon: "🤖", path: "/ml-monitor" },
  { label: "BTC Panel", icon: "⚠️", path: "/btc-panel" },
  { label: "Fork Config", icon: "🛠️", path: "/fork-score" },
  { label: "DCA Config", icon: "🛠️", path: "/dca-config" },
  { label: "TV Config", icon: "📺", path: "/tv-config" },
  { label: "SAFU Config", icon: "🧯", path: "/safu-config" },
];

export default function Sidebar({ onHelpClick, onTourClick }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Sticky Top Bar on Mobile */}
      <div className="md:hidden sticky top-0 z-50 flex items-center justify-between p-4 bg-gray-900 border-b border-gray-800">
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
        md:static md:translate-x-0 md:w-56 md:min-h-screen md:sticky md:top-0`}
      >
        {/* Show heading always on desktop, and on mobile only when open */}
        <div className={`text-xl font-bold text-white mb-6 ${open ? "block" : "hidden"} md:block`}>
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

        {/* Help System */}
        <div className="pt-4 border-t border-gray-800">
          <button
            onClick={() => {
              onTourClick && onTourClick();
              setOpen(false);
            }}
            className="w-full flex items-center py-2 px-3 rounded hover:bg-gray-800 transition-all text-gray-300 hover:text-white"
          >
            <PlayCircle size={16} className="mr-2" />
            Take Tour
          </button>
          
          <button
            onClick={() => {
              onHelpClick && onHelpClick();
              setOpen(false);
            }}
            className="w-full flex items-center py-2 px-3 rounded hover:bg-gray-800 transition-all text-gray-300 hover:text-white"
          >
            <HelpCircle size={16} className="mr-2" />
            Help & Docs
          </button>

          <NavLink
            to="/faq"
            className={({ isActive }) =>
              `block py-2 px-3 rounded hover:bg-gray-800 transition-all ${
                isActive ? "bg-gray-800 text-green-400 font-semibold" : "text-gray-300"
              }`
            }
            onClick={() => setOpen(false)}
          >
            <span className="mr-2">❓</span>
            FAQ
          </NavLink>
        </div>
      </div>
    </>
  );
}
