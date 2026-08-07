import { useState, useEffect, useRef, useCallback } from "react";
import type { SearchResult } from "../api";
import { searchDisplayId } from "../api";

interface JumpToInputProps {
    onSelect: (queueOrder: number) => void;
}

export function JumpToInput({ onSelect }: JumpToInputProps) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResult[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const doSearch = useCallback(async (q: string) => {
        if (q.trim().length === 0) {
            setResults([]);
            setIsOpen(false);
            return;
        }
        const data = await searchDisplayId(q);
        setResults(data);
        setSelectedIndex(0);
        setIsOpen(data.length > 0);
    }, []);

    useEffect(() => {
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => doSearch(query), 200);
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [query, doSearch]);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (
                containerRef.current &&
                !containerRef.current.contains(e.target as Node)
            ) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () =>
            document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleSelect = (result: SearchResult) => {
        onSelect(result.queue_order);
        setQuery("");
        setResults([]);
        setIsOpen(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen || results.length === 0) {
            if (e.key === "Enter" && results.length === 0 && query.trim()) {
                doSearch(query);
            }
            return;
        }

        if (e.key === "ArrowDown") {
            e.preventDefault();
            setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setSelectedIndex((prev) => Math.max(prev - 1, 0));
        } else if (e.key === "Enter") {
            e.preventDefault();
            handleSelect(results[selectedIndex]);
        } else if (e.key === "Escape") {
            setIsOpen(false);
        }
    };

    return (
        <div ref={containerRef} className="relative">
            <div className="flex items-center gap-2">
                <label
                    htmlFor="jump-to-input"
                    className="text-xs font-medium text-white/40"
                >
                    Jump To
                </label>
                <input
                    id="jump-to-input"
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => results.length > 0 && setIsOpen(true)}
                    placeholder="Search by ID..."
                    className="
            w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2
            text-sm text-white/80 placeholder:text-white/25
            outline-none transition-colors
            focus:border-indigo-400/50 focus:bg-white/8
          "
                />
            </div>

            {isOpen && results.length > 0 && (
                <div
                    className="
          absolute left-0 right-0 top-full z-50 mt-1
          max-h-48 overflow-y-auto
          rounded-lg border border-white/15 bg-slate-900/95 shadow-xl backdrop-blur-sm
        "
                >
                    {results.map((r, i) => (
                        <button
                            key={r.queue_order}
                            onClick={() => handleSelect(r)}
                            className={`
                flex w-full items-center justify-between px-3 py-2 text-left text-sm
                transition-colors cursor-pointer
                ${
                    i === selectedIndex
                        ? "bg-indigo-500/20 text-white"
                        : "text-white/60 hover:bg-white/5 hover:text-white/80"
                }
              `}
                        >
                            <span className="font-mono">{r.display_id}</span>
                            <span className="text-xs text-white/30">
                                #{r.queue_order}
                            </span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
