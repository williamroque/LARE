import type { LabelInfo, EntryData, StatsData } from "../api";
import { LabelButton } from "./LabelButton";
import { JumpToInput } from "./JumpToInput";

interface ControlPanelProps {
    entry: EntryData | null;
    labels: LabelInfo[];
    stats: StatsData | null;
    onLabel: (label: LabelInfo) => void;
    onPrevious: () => void;
    onJumpTo: (queueOrder: number) => void;
    canGoBack: boolean;
}

export function ControlPanel({
    entry,
    labels,
    stats,
    onLabel,
    onPrevious,
    onJumpTo,
    canGoBack,
}: ControlPanelProps) {
    return (
        <div className="flex h-full flex-col">
            <div className="border-b border-white/8 px-5 py-4">
                <h1
                    className="truncate font-mono text-lg font-bold tracking-tight text-white"
                    title={entry?.display_id || ""}
                >
                    {entry?.display_id || "—"}
                </h1>
                {entry && (
                    <p className="mt-1 font-mono text-xs text-white/30">
                        #{entry.queue_order}
                    </p>
                )}
            </div>

            <div className="flex-1 space-y-2.5 overflow-y-auto px-5 py-4">
                {entry &&
                    labels.map((label) => (
                        <LabelButton
                            key={label.shortcut}
                            label={label}
                            score={entry.scores[label.label] ?? null}
                            isActive={entry.final_label === label.title}
                            onClick={() => onLabel(label)}
                        />
                    ))}

                {!entry && (
                    <div className="flex flex-col items-center justify-center py-12">
                        <div className="rounded-full bg-green-500/10 p-4">
                            <svg
                                className="h-8 w-8 text-green-400"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M5 13l4 4L19 7"
                                />
                            </svg>
                        </div>
                        <p className="mt-3 text-sm font-medium text-green-400/80">
                            All entries reviewed
                        </p>
                    </div>
                )}
            </div>

            <div className="border-t border-white/8 px-5 py-4 space-y-3">
                {stats && (
                    <div className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                            <span className="text-white/40">Progress</span>
                            <span className="font-mono text-white/60">
                                {stats.labeled}/{stats.total} (
                                {stats.progress_pct}%)
                            </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                            <div
                                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700"
                                style={{ width: `${stats.progress_pct}%` }}
                            />
                        </div>
                    </div>
                )}

                <div className="flex gap-2">
                    <button
                        id="btn-previous"
                        onClick={onPrevious}
                        disabled={!canGoBack}
                        className="
              flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2
              text-xs font-medium text-white/60 transition-all cursor-pointer
              hover:border-white/20 hover:bg-white/10 hover:text-white/80
              disabled:cursor-not-allowed disabled:opacity-30
            "
                    >
                        ← Previous
                    </button>
                </div>

                <JumpToInput onSelect={onJumpTo} />
            </div>
        </div>
    );
}
