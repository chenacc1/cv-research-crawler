interface FilterChipProps {
  label: string;
  value: string;
  onRemove: () => void;
}

export default function FilterChip({ label, value, onRemove }: FilterChipProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-0.5 text-sm text-blue-700">
      <span className="font-medium">{label}:</span>
      <span>{value}</span>
      <button
        type="button"
        onClick={onRemove}
        className="ml-0.5 inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-blue-200"
        aria-label={`Remove filter ${label}`}
      >
        &times;
      </button>
    </span>
  );
}
