import { useCallback, useRef } from "react";

export function useNavigationStack() {
    const stackRef = useRef<number[]>([]);

    const push = useCallback((queueOrder: number) => {
        stackRef.current.push(queueOrder);
    }, []);

    const pop = useCallback((): number | undefined => {
        return stackRef.current.pop();
    }, []);

    const canGoBack = useCallback((): boolean => {
        return stackRef.current.length > 0;
    }, []);

    const clear = useCallback(() => {
        stackRef.current = [];
    }, []);

    return { push, pop, canGoBack, clear };
}
