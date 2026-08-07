import type { LabelInfo } from "../api";

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
        group relative w-full rounded-xl border px-5 py-4 text-left
        transition-all duration-200 ease-out cursor-pointer
        ${
            isActive
                ? "border-indigo-400 bg-indigo-500/20 shadow-lg shadow-indigo-500/10"
                : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
        }
      `}
        >
            <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-white/90">
                    {label.title}
                </span>
                <kbd
                    className={`
          inline-flex h-6 min-w-6 items-center justify-center rounded-md
          border px-1.5 font-mono text-xs font-medium
          ${
              isActive
                  ? "border-indigo-400/50 bg-indigo-500/30 text-indigo-200"
                  : "border-white/15 bg-white/8 text-white/50 group-hover:text-white/70"
          }
        `}
                >
                    {label.shortcut}
                </kbd>
            </div>
            {score !== null && score !== undefined && (
                <div className="mt-2 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
                        <div
                            className={`h-full rounded-full transition-all duration-500 ${
                                isActive ? "bg-indigo-400" : "bg-white/25"
                            }`}
                            style={{
                                width: `${Math.min(Math.max(score * 100, 0), 100)}%`,
                            }}
                        />
                    </div>
                    <span className="font-mono text-xs text-white/40">
                        {score.toFixed(3)}
                    </span>
                </div>
            )}
        </button>
    );
}
