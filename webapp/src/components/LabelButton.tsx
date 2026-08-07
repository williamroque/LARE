import type { LabelInfo } from '../api';

interface LabelButtonProps {
    label: LabelInfo;
    score: number | null;
    isActive: boolean;
    onClick: () => void;
}

export function LabelButton({
    label,
    score,
    isActive,
    onClick,
}: LabelButtonProps) {
    return (
        <button
            id={`label-btn-${label.shortcut}`}
            onClick={onClick}
            className={`
        group relative w-full rounded border px-4 py-3 text-left cursor-pointer
        ${
            isActive
                ? 'border-stone-900 text-white'
                : 'border-stone-300 text-stone-800 hover:border-stone-500 hover:bg-stone-50'
        }
      `}
        >
            <div className='flex items-center justify-between'>
                <span className={`text-sm font-medium ${isActive ? 'text-white' : 'text-stone-900'}`}>
                    {label.title}
                </span>
                <kbd
                    className={`
          inline-flex h-5 min-w-5 items-center justify-center rounded
          border px-1.5 font-mono text-xs font-semibold
          ${
              isActive
                  ? 'border-stone-700 bg-stone-800 text-stone-200'
                  : 'border-stone-300 bg-stone-100 text-stone-600'
          }
        `}
                >
                    {label.shortcut}
                </kbd>
            </div>
            {score !== null && score !== undefined && (
                <div className='mt-2 flex items-center gap-2'>
                    <div className={`h-1 flex-1 overflow-hidden rounded-full ${isActive ? 'bg-stone-700' : 'bg-stone-200'}`}>
                        <div
                            className={`h-full rounded-full ${
                                isActive ? 'bg-white' : 'bg-stone-700'
                            }`}
                            style={{
                                width: `${Math.min(Math.max(score * 100, 0), 100)}%`,
                            }}
                        />
                    </div>
                    <span className={`font-mono text-xs ${isActive ? 'text-stone-300' : 'text-stone-500'}`}>
                        {score.toFixed(3)}
                    </span>
                </div>
            )}
        </button>
    );
}
