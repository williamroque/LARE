import { useState, useEffect, useCallback } from "react";
import type { AppConfig, EntryData, LabelInfo, StatsData } from "./api";
import {
    fetchConfig,
    fetchEntry,
    fetchNext,
    fetchStats,
    submitLabel,
} from "./api";
import { ImageGrid } from "./components/ImageGrid";
import { ControlPanel } from "./components/ControlPanel";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { useNavigationStack } from "./hooks/useNavigationStack";

export default function App() {
    const [config, setConfig] = useState<AppConfig | null>(null);
    const [entry, setEntry] = useState<EntryData | null>(null);
    const [stats, setStats] = useState<StatsData | null>(null);
    const [loading, setLoading] = useState(true);
    const { push, pop, canGoBack } = useNavigationStack();

    useEffect(() => {
        async function init() {
            const [cfg, nextRes, statsRes] = await Promise.all([
                fetchConfig(),
                fetchNext(-1),
                fetchStats(),
            ]);
            setConfig(cfg);
            setStats(statsRes);
            if (nextRes.entry) {
                setEntry(nextRes.entry);
            }
            setLoading(false);
        }
        init();
    }, []);

    const refreshStats = useCallback(async () => {
        const s = await fetchStats();
        setStats(s);
    }, []);

    const handleLabel = useCallback(
        async (label: LabelInfo) => {
            if (!entry) return;
            push(entry.queue_order);
            await submitLabel(entry.entry_id, label.title);
            const nextRes = await fetchNext(entry.queue_order);
            setEntry(nextRes.entry);
            refreshStats();
        },
        [entry, push, refreshStats],
    );

    const handlePrevious = useCallback(async () => {
        const prevOrder = pop();
        if (prevOrder === undefined) return;
        const prevEntry = await fetchEntry(prevOrder);
        setEntry(prevEntry);
    }, [pop]);

    const handleJumpTo = useCallback(
        async (queueOrder: number) => {
            if (entry) {
                push(entry.queue_order);
            }
            const target = await fetchEntry(queueOrder);
            setEntry(target);
        },
        [entry, push],
    );

    useKeyboardShortcuts({
        labels: config?.labels ?? [],
        onLabel: handleLabel,
        onPrevious: handlePrevious,
        enabled: !loading && !!config,
    });

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-slate-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/20 border-t-indigo-400" />
                    <p className="text-sm text-white/40">Loading project...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-slate-950 text-white">
            <div className="flex flex-1 min-w-0">
                <ImageGrid images={entry?.images ?? []} />
            </div>

            <div className="w-80 flex-shrink-0 border-l border-white/8 bg-slate-900/50">
                <ControlPanel
                    entry={entry}
                    labels={config?.labels ?? []}
                    stats={stats}
                    onLabel={handleLabel}
                    onPrevious={handlePrevious}
                    onJumpTo={handleJumpTo}
                    canGoBack={canGoBack()}
                />
            </div>
        </div>
    );
}
