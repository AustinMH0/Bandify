import { useState, useEffect } from "react";
import { Modal, Card, Grid, Text, List, Button, Image } from "@mantine/core";

interface Playlist {
  id: string;
  name: string;
  total_tracks: number;
  image: string | null;
}

interface Track {
  name: string;
  artist: string;
}

const PlaylistTable = () => {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [tracks, setTracks] = useState<Record<string, Track[]>>({});
  const [selectedPlaylist, setSelectedPlaylist] = useState<string | null>(null);
  const [modalOpened, setModalOpened] = useState(false);
  const [user, setUser] = useState<{ display_name: string; profile_picture: string | null } | null>(null);

  useEffect(() => {
    const fetchPlaylists = async () => {
      try {
        const response = await fetch("http://localhost:5000/get_playlists", {
          credentials: "include",
        });
  
        if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
  
        const data = await response.json();
        setUser({
          display_name: data.display_name,
          profile_picture: data.profile_picture
        });
        setPlaylists(data.playlists);
      } catch (error) {
        console.error("Error fetching playlists:", error);
      }
    };
  
    fetchPlaylists();
  }, []);

  const fetchTracks = async (playlistId: string) => {
    if (tracks[playlistId]) {
      setSelectedPlaylist(playlistId);
      setModalOpened(true);
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/get_tracks/${playlistId}`, {
        credentials: "include",
      });

      if (!response.ok) throw new Error("Failed to fetch tracks");

      const data: Track[] = await response.json();
      setTracks((prev) => ({ ...prev, [playlistId]: data }));
      setSelectedPlaylist(playlistId);
      setModalOpened(true);
    } catch (error) {
      console.error("Error fetching tracks:", error);
    }
  };

  return (
    <div>
      <h2>Your Playlists</h2>
      <Grid>
        {playlists.map((playlist) => (
          <Grid.Col key={playlist.id} span={4}>
            <Card shadow="sm" padding="lg" onClick={() => fetchTracks(playlist.id)} style={{ cursor: "pointer" }}>
            <Card.Section>
              <Image
                src={playlist.image}
                height={160}
                alt={playlist.name}
                fit="cover"
              />
            </Card.Section>
              <Text size="lg" mt="md">
                {playlist.name}
              </Text>
              <Text size="sm" c="dimmed">
                {playlist.total_tracks} tracks
              </Text>
            </Card>
          </Grid.Col>
        ))}
      </Grid>

      <Modal 
          opened={modalOpened} 
          onClose={() => setModalOpened(false)}
          overlayProps={{
            backgroundOpacity: 0.55,
            blur: 3,
          }}
          size="auto" 
          radius="md"
          title ="Tracklist"
          centered>
        {selectedPlaylist && tracks[selectedPlaylist] ? (
          <List>
            {tracks[selectedPlaylist].map((track, index) => (
              <List.Item key={index}>
                <Text>
                  <strong>{track.artist}</strong> - {track.name}
                </Text>
              </List.Item>
            ))}
          </List>
        ) : (
          <Text>Loading tracks...</Text>
        )}
        <Button fullWidth variant="light" mt="md" onClick={() => setModalOpened(false)}>Bandify Playlist</Button>
      </Modal>
    </div>
  );
};

export default PlaylistTable;
