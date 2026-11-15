import { useMemo } from "react";
import PostCheckoutAmbience from "./pages/PostCheckoutAmbience";

export default function App() {
  const orderId = useMemo(
    () => new URLSearchParams(window.location.search).get("order"),
    []
  );
  const token = localStorage.getItem("authToken");

  const getSpotifyToken = () => localStorage.getItem("spotifyAccessToken") ?? "";

  if (!orderId || !token) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 text-center text-sm text-slate-400">
        We could not find an active order for this session.
      </div>
    );
  }

  return (
    <PostCheckoutAmbience
      orderId={orderId}
      token={token}
      getSpotifyToken={getSpotifyToken}
    />
  );
}