import { useState, useRef, useEffect } from 'react';

interface GlassDropdownProps {
  value: string;
  options: { value: string; label: string }[];
  onChange?: (value: string) => void;
  className?: string;
  placeholder?: string;
  multiple?: boolean;
  selectedValues?: string[];
  onMultiChange?: (values: string[]) => void;
}

export default function GlassDropdown({ value, options, onChange, className = '', placeholder, multiple, selectedValues = [], onMultiChange }: GlassDropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const currentLabel = multiple
    ? (selectedValues.length ? `${selectedValues.length} selected` : (placeholder || 'Select...'))
    : (options.find((o) => o.value === value)?.label || placeholder || value);

  function toggleOption(optValue: string) {
    if (!onMultiChange) return;
    if (selectedValues.includes(optValue)) {
      onMultiChange(selectedValues.filter((v) => v !== optValue));
    } else {
      onMultiChange([...selectedValues, optValue]);
    }
  }

  const isActive = (v: string) => multiple && selectedValues.includes(v);

  return (
    <div ref={ref} className={`relative ${className}`}>
      <div className="glass-select flex items-center justify-between gap-2 whitespace-nowrap"
        onClick={() => setOpen(!open)} style={{ minWidth: 120 }}>
        <span className="truncate text-sm" style={{ color: value || (multiple && selectedValues.length) ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>
          {currentLabel}
        </span>
      </div>
      {open && (
        <div className="absolute z-30 mt-1 glass-panel bg-white/80 min-w-full w-max"
          style={{ maxHeight: 260, overflowY: 'auto', padding: 4, borderRadius: 'var(--r-md)' }}>
          {options.map((opt) => (
            <div
              key={opt.value}
              className={`flex items-center gap-2 rounded px-3 py-2 text-sm cursor-pointer transition-colors ${
                (multiple ? isActive(opt.value) : opt.value === value)
                  ? ''
                  : ''
              }`}
              style={multiple
                ? {}
                : (opt.value === value ? { background: 'rgba(116,95,242,0.12)', color: 'var(--purple)', fontWeight: 500 } : {})
              }
              onClick={() => {
                if (multiple) { toggleOption(opt.value); }
                else { onChange?.(opt.value); setOpen(false); }
              }}
              onMouseEnter={(e) => {
                if (!(multiple ? isActive(opt.value) : opt.value === value)) {
                  (e.target as HTMLElement).style.background = 'var(--glass-hover)';
                }
              }}
              onMouseLeave={(e) => {
                if (!(multiple ? isActive(opt.value) : opt.value === value)) {
                  (e.target as HTMLElement).style.background = '';
                }
              }}
            >
              {multiple && (
                <span className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
                  isActive(opt.value) ? 'border-purple-400' : 'border-white/30'
                }`} style={{
                  background: isActive(opt.value) ? 'var(--purple)' : 'transparent',
                }}>
                  {isActive(opt.value) && (
                    <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 5l2 2 4-4" fill="none" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  )}
                </span>
              )}
              {opt.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
