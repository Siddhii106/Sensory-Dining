import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const SDK_URL = "https://sdk.scdn.co/spotify-player.js";
const PLAYER_API = "https://api.spotify.com/v1/me/player";

function loadSpotifySdk() {
    if (window.Spotify) return Promise.resolve();
    if (!window.__spotifySdkReady) {
        window.__spotifySdkReady = new Promise((resolve) => {
            window.onSpotifyWebPlaybackSDKReady = resolve;
            const script = document.createElement("script");
            script.src = SDK_URL;
            script.async = true;
            document.body.appendChild(script);
        });
    }
    return window.__spotifySdkReady;
}

@param {object}  
@param {boolean} 
@param {Function}
@param {Function} 

export function useSpotifyPlayer({ enabled, getAccessToken, onTrackEnded }) {
      const [deviceId, setDeviceId] = useState(null);
  const [error, setError] = useState(null);

  const playerRef = useRef(null);
  const deviceIdRef = useRef(null);
  const tokenRef = useRef(getAccessToken);
  const endedRef = useRef(onTrackEnded);
  const endTimerRef = useRef(null);
  const loadedUriRef = useRef(null);
  const pausedRef = useRef(false);
  const remainingMsRef = useRef(0);

  // Keep the latest callbacks without re-creating the player.
  useEffect(() => {
    tokenRef.current = getAccessToken;
    endedRef.current = onTrackEnded;
  });

  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;

    loadSpotifySdk().then(() => {
        if (cancelled) return;

        const player = new window.Spotify.Player({
            name: "Sensory Dining",
            volume: 0.8,
            get0AuthToken: (callback) => callback(tokenRef.current()),
        });

        player.addListener("ready", ({ device_id }) => {
            deviceIdRef.current = device_id;
            setDeviceId(device_id);
        });
        player.addListener("not_ready", () => {
            deviceIdRef.current = null;
            setDeviceId(null);
        });
        ["initialization_error", "authentication_error", "account_error", "playback_error"].forEach(
            (event) => player.addListener(event, ({ message }) => setError(message))
        );
        player.connect();
        playerRef.current = player;
    });

    return () => {
        cancelled = true;
        clearTimeout(endTimerRef.current);
        playerRef.current?.disconnect();
        playerRef.current = null;
        deviceIdRef.current = null;
        loadedUriRef.current = null;
        pausedRef.current = false;
        setDeviceId(null);
    };
  }, [enabled]);

  const callPlayer = useCallback(async (endpoint, body) => {
    const id = deviceIdRef.current;
    if (!id) throw new Error("Spotify player is not ready yet.");

    const response = await fetch(
        `${PLAYER_API}/${endpoint}?device_id=${encodeURIComponent(id)}`,
        {
            method: "PUT",
            headers: {
                Authorization: `Bearer ${tokenRef.current()}`,
                "Content-Type": "application/json",
            },
            body: body ? JSON.stringify(body) : undefined,
        }
    )
  })
}
