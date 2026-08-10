export interface LabelInfo {
    label: string;
    title: string;
    shortcut: string;
    is_emergent: boolean;
}

export interface ImageInfo {
    column: string;
    title: string;
    format: string;
}

export interface AppConfig {
    labels: LabelInfo[];
    images: ImageInfo[];
    id_display_method: string;
}

export interface ImageResult {
    title: string;
    url: string | null;
    error: string | null;
}

export interface EntryData {
    queue_order: number;
    entry_id: string;
    display_id: string;
    final_label: string | null;
    images: ImageResult[];
    scores: Record<string, number>;
}

export interface NextResponse {
    entry: EntryData | null;
    complete: boolean;
}

export interface StatsData {
    labeled: number;
    total: number;
    progress_pct: number;
}

export interface SearchResult {
    queue_order: number;
    entry_id: string;
    display_id: string;
    final_label: string | null;
}

export async function fetchConfig(): Promise<AppConfig> {
    const res = await fetch("/api/config");
    return res.json();
}

export async function fetchStats(): Promise<StatsData> {
    const res = await fetch("/api/stats");
    return res.json();
}

export async function fetchEntry(queueOrder: number): Promise<EntryData> {
    const res = await fetch(`/api/entry/${queueOrder}`);
    if (!res.ok) throw new Error(`Entry not found: ${queueOrder}`);
    return res.json();
}

export async function fetchNext(after: number = -1): Promise<NextResponse> {
    const res = await fetch(`/api/next?after=${after}`);
    return res.json();
}

export async function submitLabel(
    entryId: string,
    label: string,
): Promise<void> {
    await fetch("/api/label", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_id: entryId, label }),
    });
}

export async function clearLabel(entryId: string): Promise<void> {
    await fetch("/api/clear-label", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_id: entryId }),
    });
}

export async function searchDisplayId(query: string): Promise<SearchResult[]> {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    return data.results;
}
