import { useState, useEffect } from "react";
import { IconPlus } from '@tabler/icons-react';
import { Accordion } from '@mantine/core';
import classes from './PlaylistTable.module.css';

interface Playlist {
  id: string;
  name: string;
  total_tracks: number;
}

interface Track {
  name: string;
  artist: string;
}

const PlaylistTable = () => {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [selectedPlaylist, setSelectedPlaylist] = useState<string | null>(null);

  const items = playlists.map((playlist) => (
    <Accordion.Item key={playlist.name} value={playlist.id}>
        <Accordion.Control onClick={() => fetchTracks(playlist.id)}>{playlist.name}</Accordion.Control>
        <Accordion.Panel>
        {tracks.map((track, index) => (
          <li key={index}>
            {track.artist} - {track.name}
          </li>
        ))}                
        </Accordion.Panel>
    </Accordion.Item>
))

  useEffect(() => {
    const fetchPlaylists = async () => {
        try {
          const response = await fetch("http://localhost:5000/get_playlists", {
            credentials: "include", 
          });
      
          if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
      
          const data: Playlist[] = await response.json();
          setPlaylists(data);
        } catch (error) {
          console.error("Error fetching playlists:", error);
        }
      };

    fetchPlaylists();
  }, []);

  const fetchTracks = async (playlistId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/get_tracks/${playlistId}`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch tracks");

      const data: Track[] = await response.json();
      setTracks(data);
      setSelectedPlaylist(playlistId);
    } catch (error) {
      console.error("Error fetching tracks:", error);
    }
  };

  return (
    <div>
        <h2>Your Playlists</h2>
        <Accordion
            transitionDuration={1000}
            classNames={classes}
        >
            {items}
        </Accordion>
    </div>

  );

};
export default PlaylistTable;
