import type { LabelInfo, EntryData, StatsData } from '../api';
import { LabelButton } from './LabelButton';
import { JumpToInput } from './JumpToInput';

interface ControlPanelProps {
    entry: EntryData | null;
    labels: LabelInfo[];
    stats: StatsData | null;
    scoreMin: number;
    scoreMax: number;
    onLabel: (label: LabelInfo) => void;
    onPrevious: () => void;
    onJumpTo: (queueOrder: number) => void;
    canGoBack: boolean;
}

export function ControlPanel({
    entry,
    labels,
    stats,
    scoreMin,
    scoreMax,
    onLabel,
    onPrevious,
    onJumpTo,
    canGoBack,
}: ControlPanelProps) {
    return (
        <div className='flex flex-col h-full'>
            <div className='px-5 py-4 border-stone-300 border-b'>
                <h1
                    className='font-serif font-semibold text-stone-900 text-xl break-all break-words tracking-tight'
                    title={entry?.display_id || ''}
                >
                    {entry?.display_id || '—'}
                </h1>
                {entry && (
                    <p className='mt-0.5 font-mono text-stone-500 text-xs'>
                        #{entry.queue_order}
                    </p>
                )}
            </div>

            <div className='flex flex-col flex-1 gap-2 space-y-2 px-5 py-4 overflow-y-auto'>
                {entry &&
                    labels.map((label) => (
                        <LabelButton
                            key={label.shortcut}
                            label={label}
                            score={entry.scores[label.label] ?? null}
                            scoreMin={scoreMin}
                            scoreMax={scoreMax}
                            isActive={entry.final_label === label.title}
                            onClick={() => onLabel(label)}
                        />
                    ))}

                {!entry && (
                    <div className='flex flex-col justify-center items-center py-12'>
                        <div className='p-4 border border-stone-300 rounded-full'>
                            <svg
                                className='w-6 h-6 text-stone-700'
                                fill='none'
                                viewBox='0 0 24 24'
                                stroke='currentColor'
                            >
                                <path
                                    strokeLinecap='round'
                                    strokeLinejoin='round'
                                    strokeWidth={2}
                                    d='M5 13l4 4L19 7'
                                />
                            </svg>
                        </div>
                        <p className='mt-3 font-sans text-stone-700 text-sm'>
                            All entries reviewed
                        </p>
                    </div>
                )}
            </div>

            <div className='space-y-4 px-5 py-4 border-stone-300 border-t'>
                {stats && (
                    <div className='space-y-1.5'>
                        <div className='flex justify-between text-xs'>
                            <span className='font-medium text-stone-600'>Progress</span>
                            <span className='font-mono text-stone-700'>
                                {stats.labeled}/{stats.total} ({stats.progress_pct}%)
                            </span>
                        </div>
                        <div className='rounded-full h-1.5 overflow-hidden'>
                            <div
                                className='rounded-full h-full'
                                style={{ width: `${stats.progress_pct}%` }}
                            />
                        </div>
                    </div>
                )}

                <div className='flex gap-2'>
                    <button
                        id='btn-previous'
                        onClick={onPrevious}
                        disabled={!canGoBack}
                        className='flex-1 bg-white hover:bg-stone-100 disabled:opacity-40 px-3 py-2 border border-stone-400 hover:border-stone-800 rounded font-medium text-stone-800 text-xs cursor-pointer disabled:cursor-not-allowed'
                    >
                        ← Previous
                    </button>
                </div>

                <JumpToInput onSelect={onJumpTo} />
            </div>
        </div>
    );
}
