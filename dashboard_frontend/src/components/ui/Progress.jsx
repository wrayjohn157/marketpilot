export function Progress({ value }) {
  return (
    <div className="w-full bg-gray-700 h-2 rounded">
      <div
        className="bg-green-500 h-2 rounded"
        style={{ width: `${value}%` }}
      ></div>
    </div>
  );
}
