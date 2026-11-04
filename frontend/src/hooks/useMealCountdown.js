import { useEffect, useState } from "react";

export function useMealCountdown(serverRemainingMs) {
    const [remainingMs, setRemainingMs] = useState(serverRemainingMs);

    useEffect(() => {
        const endsAt = Date.now() + serverRemainingMs;
        const updateRemaining = () => {
            const remaining = Math.max(0, endsAt - Date.now());
            setRemainingMs(remaining);
            return remaining;
        };

        const intervalId = setInterval(() => {
            if (updateRemaining() === 0) {
                clearInterval(intervalId);
            }
        }, 1000);
        if (updateRemaining() === 0) {
            clearInterval(intervalId);
        }

        return () => clearInterval(intervalId);
    }, [serverRemainingMs]);

    return remainingMs;
}

export function formatDuration(ms) {
    const total = Math.ceil(ms / 1000);
    const hours = Math.floor(total / 3600);
    const minutes = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
    const seconds = String(total % 60).padStart(2, "0");
    return hours > 0 ? `${hours}:${minutes}:${seconds}` : `${minutes}:${seconds}`;
}