import { useState, useEffect } from "react";

import axios from "axios";
import {
  Button,
  Card,
  Grid,
  Image,
  Modal,
  Pagination,
  Table,
  Text,
  useMantineTheme
} from "@mantine/core";
import { motion, AnimatePresence } from "framer-motion";

import classes from '../PlaylistTable/PlaylistTable.module.css'

import type { Playlist } from "../../types/types";

interface Track {
  name: string;
  artist: string;
}

const PlaylistTable = ({
  playlists,
  setPlaylists
}: {
  playlists: Playlist[];
  setPlaylists: React.Dispatch<React.SetStateAction<Playlist[]>>;
}) => {
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
  const [currentPage, setCurrentPage] = useState(1);

  const theme = useMantineTheme();

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1,
      },
    },
    exit: { opacity: 0 },
  };
  
  const cardVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 150,
        damping: 20,
      },
    },
    exit: {
      opacity: 0,
      y: -20,
      scale: 0.95,
      transition: {
        duration: 0.2,
        ease: "easeInOut",
      },
    },
  };
  
  useEffect(() => {
    const fetchPlaylists = async () => {
      try {
        const response = await axios.get("http://localhost:5000/get_playlists", {
          withCredentials: true,
        });
        const data = response.data;
        // setLoggedIn(true);
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
      {playlists.length > 0 ? (
        <div>

            <div id="playlist-cards" style={{ paddingTop: "4rem" }}>
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentPage}
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                >
                  {/* Playlist Grid */}
                  <Grid mt="md">
                    {playlists
                      .slice((currentPage - 1) * 9, currentPage * 9)
                      .map((playlist) => (
                        <Grid.Col 
                          key={playlist.id} 
                          span={4} 
                          className={classes.playlistCard}>
                          <motion.div variants={cardVariants}>
                            <Card
                              className={classes.cardContent}
                              shadow="sm"
                              padding="lg"
                              onClick={() => fetchTracks(playlist.id)}
                            
                            >
                              <Card.Section>
                                <Image
                                  src={playlist.image}
                                  height={160}
                                  alt={playlist.name}
                                  fit="cover"
                                />
                              </Card.Section>

                              <Text className={classes.playlistTitle} size="lg" mt="md" fw={500}>
                                {playlist.name}
                              </Text>
                              <Text className={classes.trackInfo} size="sm" c="dimmed">
                                {playlist.total_tracks} tracks
                              </Text>
                            </Card>
                          </motion.div>
                        </Grid.Col>
                      ))}
                  </Grid>

                  {/* Sticky Pagination */}
                  {playlists.length > 9 && (
                    <div style={{ marginTop: "2rem", display: "flex", justifyContent: "center" }}>
                      <Pagination
                        total={Math.ceil(playlists.length / 9)}
                        value={currentPage}
                        onChange={setCurrentPage}
                        color="grape"
                        radius="xl"
                      />
                    </div>
                  )}
                
                </motion.div>
              </AnimatePresence>
            </div>

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
        null
      )
    }
    
    </div>
  );
};

export default PlaylistTable;

// "#fdb6e0" "#ff6ec4"
