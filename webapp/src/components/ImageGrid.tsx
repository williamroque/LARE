import type { ImageResult } from '../api';

interface ImageGridProps {
    images: ImageResult[];
}

export function ImageGrid({ images }: ImageGridProps) {
    const validImages = images.filter((img) => img.url !== null);

    if (validImages.length === 0) {
        return (
            <div className='flex flex-1 justify-center items-center h-full'>
                <p className='font-sans text-stone-500 text-sm'>No images available</p>
            </div>
        );
    }

    return (
        <div
            className='gap-3 grid p-3 w-full h-full select-none'
            style={{
                gridTemplateColumns: `repeat(${validImages.length}, 1fr)`,
                gridTemplateRows: '1fr',
            }}
        >
            {images.map((img, i) => (
                <div
                    key={i}
                    className='relative flex flex-col bg-white border border-stone-300 rounded overflow-hidden'
                >
                    <div className='flex-shrink-0 px-3 py-2 border-stone-200 border-b text-center'>
                        <span className='font-mono font-medium text-stone-700 text-xs uppercase tracking-wide'>
                            {img.title}
                        </span>
                    </div>
                    <div className='relative flex flex-1 justify-center items-center p-2 overflow-hidden'>
                        {img.url ? (
                            <img
                                src={img.url}
                                alt={img.title}
                                className='max-w-full max-h-full object-contain'
                                draggable={false}
                            />
                        ) : (
                            <div className='flex flex-col items-center gap-2 p-4'>
                                <svg
                                    className='w-7 h-7 text-stone-400'
                                    fill='none'
                                    viewBox='0 0 24 24'
                                    stroke='currentColor'
                                >
                                    <path
                                        strokeLinecap='round'
                                        strokeLinejoin='round'
                                        strokeWidth={1.5}
                                        d='M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z'
                                    />
                                </svg>
                                <span className='font-serif text-stone-600 text-xs text-center'>
                                    {img.error || 'Image unavailable'}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}
