import { authHeaders, clearSession } from "./session";
import type { Playlist } from "../types/types";

export interface Discovery {
  id: string;
  display_name: string;
  profile_picture: string | null;
  playlists: Playlist[];
}

// Share discovery across components and StrictMode's repeated mount effects.
// A different sign-in must never reuse the previous account's result.
let discovery: { session: string; promise: Promise<Discovery> } | undefined;

export function discoverPlaylists(): Promise<Discovery> {
  const headers = authHeaders();
  const session = headers.Authorization;
  if (!session) return Promise.reject(new Error("Not signed in"));
  if (discovery?.session === session) return discovery.promise;

  const promise = fetch(`${import.meta.env.VITE_SEARCHRESULTS_API}/get_playlists`, { headers })
    .then(async response => {
      if (response.status === 401 && authHeaders().Authorization === session) clearSession();
      if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
      return response.json() as Promise<Discovery>;
    }).catch(error => {
      if (discovery?.promise === promise) discovery = undefined;
      throw error;
    });
  discovery = { session, promise };
  return promise;
}
