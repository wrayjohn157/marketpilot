export function Select({ children, ...props }) {
  return <select {...props} className="bg-gray-900 text-white rounded p-2">{children}</select>;
}
export const SelectTrigger = ({ children }) => <div>{children}</div>;
export const SelectValue = ({ children }) => <div>{children}</div>;
export const SelectContent = ({ children }) => <div>{children}</div>;
export const SelectItem = ({ children, ...props }) => <option {...props}>{children}</option>;
