import type { ImageResult } from "../api";

interface ImageGridProps {
    images: ImageResult[];
}

export function ImageGrid({ images }: ImageGridProps) {
    const validImages = images.filter((img) => img.url !== null);

    if (validImages.length === 0) {
        return (
            <div className="flex h-full items-center justify-center">
                <p className="text-sm text-white/30">No images available</p>
            </div>
        );
    }

    return (
        <div
            className="grid h-full w-full gap-3 p-3"
            style={{
                gridTemplateColumns: `repeat(${validImages.length}, 1fr)`,
                gridTemplateRows: "1fr",
            }}
        >
            {images.map((img, i) => (
                <div
                    key={i}
                    className="relative flex flex-col overflow-hidden rounded-xl border border-white/10 bg-black/40"
                >
                    <div className="flex-shrink-0 border-b border-white/8 bg-white/5 px-3 py-2">
                        <span className="text-xs font-medium tracking-wide text-white/60 uppercase">
                            {img.title}
                        </span>
                    </div>
                    <div className="relative flex flex-1 items-center justify-center overflow-hidden">
                        {img.url ? (
                            <img
                                src={img.url}
                                alt={img.title}
                                className="max-h-full max-w-full object-contain"
                                draggable={false}
                            />
                        ) : (
                            <div className="flex flex-col items-center gap-2 p-4">
                                <svg
                                    className="h-8 w-8 text-red-400/50"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={1.5}
                                        d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                                    />
                                </svg>
                                <span className="text-center text-xs text-red-400/60">
                                    {img.error || "Image unavailable"}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}
