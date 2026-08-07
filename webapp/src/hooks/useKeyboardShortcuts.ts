import { useEffect } from "react";
import type { LabelInfo } from "../api";

interface UseKeyboardShortcutsOptions {
    labels: LabelInfo[];
    onLabel: (label: LabelInfo) => void;
    onPrevious: () => void;
    enabled: boolean;
}

export function useKeyboardShortcuts({
    labels,
    onLabel,
    onPrevious,
    enabled,
}: UseKeyboardShortcutsOptions) {
    useEffect(() => {
        if (!enabled) return;

        const handler = (e: KeyboardEvent) => {
            const active = document.activeElement;
            if (
                active?.tagName === "INPUT" ||
                active?.tagName === "TEXTAREA" ||
                active?.tagName === "SELECT"
            ) {
                return;
            }

            if (e.key === "Backspace" || e.key === "ArrowLeft") {
                e.preventDefault();
                onPrevious();
                return;
            }

            const match = labels.find(
                (l) => l.shortcut === e.key.toLowerCase(),
            );
            if (match) {
                e.preventDefault();
                onLabel(match);
            }
        };

        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [labels, onLabel, onPrevious, enabled]);
}
