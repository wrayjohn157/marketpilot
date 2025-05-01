// src/components/ui/Button.jsx
export function Button({
  children,
  onClick,
  disabled,
  size = "md",
  variant = "default",
}) {
  const base =
    "rounded px-3 py-1.5 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50";

  const sizes = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1.5",
    lg: "text-base px-4 py-2",
  };

  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
    secondary: "bg-gray-200 text-black hover:bg-gray-300 focus:ring-gray-400",
    success: "bg-green-600 text-white hover:bg-green-700 focus:ring-green-500",
    ghost: "bg-transparent text-white hover:bg-white/10 focus:ring-white",
  };

  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
