interface DateRangePickerProps {
  dateFrom: string; dateTo: string;
  onDateFromChange: (v: string) => void; onDateToChange: (v: string) => void;
  onClear: () => void;
}

export default function DateRangePicker({ dateFrom, dateTo, onDateFromChange, onDateToChange, onClear }: DateRangePickerProps) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Date:</label>
      <input type="date" value={dateFrom} onChange={(e) => onDateFromChange(e.target.value)}
        className="glass-input h-[34px] px-2 text-sm" aria-label="Date from" />
      <span style={{ color: 'var(--text-tertiary)' }}>to</span>
      <input type="date" value={dateTo} onChange={(e) => onDateToChange(e.target.value)}
        className="glass-input h-[34px] px-2 text-sm" aria-label="Date to" />
      {(dateFrom || dateTo) && (
        <button type="button" onClick={onClear} className="text-sm hover:underline" style={{ color: 'var(--text-tertiary)' }}>Clear</button>
      )}
    </div>
  );
}
