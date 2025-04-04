import { useState, useEffect } from "react";
import { Modal, Card, Grid, Text, Button, Image, Table, useMantineTheme } from "@mantine/core";

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
  const [, setUser] = useState<{ display_name: string; profile_picture: string | null } | null>(null);
  const [showPriceTable, setPriceTable] = useState(false);
  const [showTrackTable, setTrackTable] = useState(false);
  const [tableButton, setTableButton] = useState("View Prices");  

  const theme = useMantineTheme();

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
      setTrackTable(true);
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
        onClose={() => {
          setModalOpened(false);
          setPriceTable(false);
          setTrackTable(true);
        }}
        overlayProps={{
          backgroundOpacity: 0.55,
          blur: 3,
        }}
        size="lg" 
        radius="md"
        title="Tracklist"
        centered
        styles={{
          body: { 
            display: "flex", 
            flexDirection: "column",
            maxHeight: "70vh" 
          },
          title: {
            color: theme.colors.grape[3],
            textAlign: "center"
          }
        }}
      >

      <div style={{ flex: 1, overflowY: "auto", paddingBottom: "60px" }}> 
        {showTrackTable && selectedPlaylist && tracks[selectedPlaylist] ? (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>#</Table.Th>
                <Table.Th>Artist</Table.Th>
                <Table.Th>Track</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {tracks[selectedPlaylist].map((track, index) => (
                <Table.Tr key={index}>
                  <Table.Td>{index + 1}</Table.Td>
                  <Table.Td>{track.name}</Table.Td>
                  <Table.Td>{track.artist}</Table.Td> 
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        ) : (
          <Text>No tracks available</Text>
        )}

        {showPriceTable && selectedPlaylist && tracks[selectedPlaylist] ? (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Track</Table.Th>
                <Table.Th>Bandcamp</Table.Th>
                <Table.Th>Beatport</Table.Th>
                <Table.Th>iTunes</Table.Th>
                <Table.Th>Amazon Music</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {tracks[selectedPlaylist].map((track, index) => (
                <Table.Tr key={index}>
                  <Table.Td>{track.name}</Table.Td>
                  <Table.Td>$--</Table.Td> 
                  <Table.Td>$--</Table.Td>
                  <Table.Td>$--</Table.Td>
                  <Table.Td>$--</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        ) : (
          <Text>No tracks available</Text>
        )}
      </div>

      <div style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          backgroundColor: theme.colors.dark[7],
          padding: "10px",
          boxShadow: "0 -2px 5px rgba(0, 0, 0, 0.1)"
        }}
      >
        <Button 
          fullWidth 
          variant="outline"
          color="grape"
          onClick={() => {
            if (showTrackTable) {
              setTrackTable(false);
              setPriceTable(true);
              setTableButton("View Playlist");
            } else {
              setTrackTable(true);
              setPriceTable(false);
              setTableButton("View Prices");
            }
          }}
        >
          {tableButton}
        </Button>
      </div>
      </Modal>
    </div>
  );
};

export default PlaylistTable;
