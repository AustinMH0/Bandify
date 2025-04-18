import { useState, useEffect } from "react";
import axios from "axios";
import { Modal, Card, Container, Title, Grid, Text, Button, Image, Table, useMantineTheme } from "@mantine/core";
import { IconBrandSpotify } from "@tabler/icons-react";
import { motion } from "framer-motion"; 

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
  const [loggedIn, setLoggedIn] = useState(false);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [tracks, setTracks] = useState<Record<string, Track[]>>({});
  const [selectedPlaylist, setSelectedPlaylist] = useState<string | null>(null);
  const [modalOpened, setModalOpened] = useState(false);
  const [, setUser] = useState<{ display_name: string; profile_picture: string | null } | null>(null);
  const [showPriceTable, setPriceTable] = useState(false);
  const [showTrackTable, setTrackTable] = useState(false);
  const [tableButton, setTableButton] = useState("View Prices");
  const [itunesPrices, setItunesPrices] = useState<Record<string, { price: number; url: string } | null>>({});
  const [bandCampPrices, setBandCampPrices] = useState<Record<string, { price: number; url: string; } | null>>({});
  const [beatportPrices, setBeatportPrices] = useState<Record<string, { price: number; url: string; } | null>>({});

  const theme = useMantineTheme();

  useEffect(() => {
    const fetchPlaylists = async () => {
      try {
        const response = await axios.get("http://localhost:5000/get_playlists", {
          withCredentials: true,
        });
        const data = response.data;
        setLoggedIn(true);
        setUser({
          display_name: data.display_name,
          profile_picture: data.profile_picture,
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
      const response = await axios.get(`http://localhost:5000/get_tracks/${playlistId}`, {
        withCredentials: true,
      });
      const data: Track[] = response.data;
      setTracks((prev) => ({ ...prev, [playlistId]: data }));
      setSelectedPlaylist(playlistId);
      setModalOpened(true);
      setTrackTable(true);
    } catch (error) {
      console.error("Error fetching tracks:", error);
    }
  };

  const fetchItunesPrices = async () => {
    if (!selectedPlaylist || !tracks[selectedPlaylist]) return;

    try {
      const response = await axios.post("http://localhost:5000/itunes_result", {
        tracks: tracks[selectedPlaylist],
      }, {
        withCredentials: true,
      });
      const data = response.data;
      console.log("Raw iTunes price response:", data);

      const priceMap: Record<string, { price: number; url: string } | null> = {};
      data.forEach((item: any) => {
        if (item.price !== undefined && item.url) {
          priceMap[item.name] = { price: item.price, url: item.url };
        } else {
          priceMap[item.name] = null;
        }
      });

      setItunesPrices(priceMap);
    } catch (error) {
      console.error("Error fetching iTunes prices:", error);
    }
  };

  const fetchBandcampPrices = async () => {
    if (!selectedPlaylist || !tracks[selectedPlaylist]) return;

    try {
      const response = await axios.post("http://localhost:5000/bandcamp_results", {
        tracks: tracks[selectedPlaylist],
      }, {
        withCredentials: true,
      });
      const data = response.data;
      console.log("Full bandcamp prices data:", data);

      const pricesMap: Record<string, { price: number; url: string } | null> = {};
      data.forEach((item: any) => {
        if (item.price !== undefined && item.url) {
          pricesMap[item.name] = { price: item.price, url: item.url };
        } else {
          pricesMap[item.name] = null;
        }
      });

      setBandCampPrices(pricesMap);
    } catch (error) {
      console.error("Error fetching prices", error);
    }
  };

  const fetchBeatportPrices = async () => {
    if (!selectedPlaylist || !tracks[selectedPlaylist]) return;

    try {
      const response = await axios.post("http://localhost:5000/beatport_results", {
        tracks: tracks[selectedPlaylist],
      }, {
        withCredentials: true,
      });
      const data = response.data;
      console.log("Full Beatport prices data:", data);

      const pricesMap: Record<string, { price: number; url: string } | null> = {};
      data.forEach((item: any) => {
        if (item.price !== undefined && item.url) {
          pricesMap[item.name] = { price: item.price, url: item.url };
        } else {
          pricesMap[item.name] = null;
        }
      });

      setBeatportPrices(pricesMap);
    } catch (error) {
      console.error("Error fetching prices", error);
    }
  };

  return (
    <div>
      {loggedIn ? (
        <div>
          <Title>Your Playlists</Title>
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
              title={
                selectedPlaylist ? playlists.find((p) => p.id === selectedPlaylist)?.name || "Tracklist" : "Tracklist"
              }
              centered
              styles={{
                header: {
                  textAlign: "center",
                  // backgroundColor: theme.colors.grape[7], 
                  padding: "10px",
                  borderRadius: "8px 8px 0 0",
                },
                body: {
                  display: "flex",
                  flexDirection: "column",
                  maxHeight: "70vh"
                },
                title: {
                  width: "100%",
                  textAlign: "center",
                  fontWeight: "bold",
                  color: theme.colors.grape[3]
                }
              }}
            >

            <div style={{ flex: 1, overflowY: "auto", paddingBottom: "60px" }}>
              {showTrackTable && selectedPlaylist && tracks[selectedPlaylist] ? (
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>#</Table.Th>
                      <Table.Th>Track</Table.Th>
                      <Table.Th>Artist</Table.Th>
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

                        {/* Bandcamp Prices */}
                        <Table.Td>
                          {bandCampPrices[track.name] && bandCampPrices[track.name]?.url ? (
                            <a
                              href={bandCampPrices[track.name]?.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: "#007aff", textDecoration: "none" }}
                            >
                              {typeof bandCampPrices[track.name]?.price === 'number'
                                ? `$${bandCampPrices[track.name]?.price.toFixed(2)}`
                                : bandCampPrices[track.name]?.price}
                            </a>
                          ) : (
                            ""
                          )}
                        </Table.Td>



                        {/* Beatport Prices */}
                        <Table.Td>
                        {beatportPrices[track.name] ? (
                            <a
                              href={beatportPrices[track.name]?.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: "#007aff", textDecoration: "none" }}
                            >
                              ${beatportPrices[track.name]?.price.toFixed(2)}
                            </a>
                          ) : (
                            ""
                          )}                    
                        </Table.Td>

                        {/* Itunes Prices */}
                        <Table.Td>
                          {itunesPrices[track.name] ? (
                            <a
                              href={itunesPrices[track.name]?.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: "#007aff", textDecoration: "none" }}
                            >
                              ${itunesPrices[track.name]?.price.toFixed(2)}
                            </a>
                          ) : (
                            ""
                          )}
                        </Table.Td>
                        
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
                onClick={async () => {
                  if (showTrackTable) {
                    await fetchBandcampPrices();
                    await fetchItunesPrices();
                    await fetchBeatportPrices();
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
      ) : (
        <Container size="sm" mt={100}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            <Card
              shadow="xl"
              padding="xl"
              radius="md"
              withBorder
              style={{ textAlign: "center" }}
            >
              <Card.Section inheritPadding py="md">
                <Title order={2} c="grape">Welcome to Bandify</Title>
                <Text c="dimmed" mt="sm">
                  Log in with Spotify to view your playlists and compare track prices across platforms.
                </Text>
              </Card.Section>
      
              <Card.Section mt="lg">
                <Button
                  fullWidth
                  color="grape"
                  size="md"
                  leftSection={<IconBrandSpotify size={20} />}
                  onClick={() => {
                    window.location.href = "http://localhost:5000/get_playlists";
                  }}
                >
                  Login with Spotify
                </Button>
              </Card.Section>
            </Card>
          </motion.div>
        </Container>
      )
    }
    
    </div>
  );
};

export default PlaylistTable;
