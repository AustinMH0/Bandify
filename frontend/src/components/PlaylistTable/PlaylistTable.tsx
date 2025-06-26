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
  useMantineTheme,
} from "@mantine/core";
import { motion, AnimatePresence } from "framer-motion";

import classes from "../PlaylistTable/PlaylistTable.module.css";
import LoadingRipple from "../LoadingAnimation/LoadingRipple";
import PlaylistSort from "../PlaylistSort/PlaylistSort";

import type { Playlist } from "../../types/types";

interface Track {
  name: string;
  artist: string;
}

const PlaylistTable = ({
  playlists,
  setPlaylists,
}: {
  playlists: Playlist[];
  setPlaylists: React.Dispatch<React.SetStateAction<Playlist[]>>;
}) => {
  const [originalPlaylists, setOriginalPlaylists] = useState<Playlist[]>([]);
  const [tracks, setTracks] = useState<Record<string, Track[]>>({});
  const [selectedPlaylist, setSelectedPlaylist] = useState<string | null>(null);
  const [modalOpened, setModalOpened] = useState(false);
  const [user, setUser] = useState<{ id: string; display_name: string; profile_picture: string | null; } | null>(null);
  const [, setPriceTable] = useState(false);
  const [showTrackTable, setTrackTable] = useState(false);
  const [tableButton, setTableButton] = useState("View Prices");
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [songPrices, setSongPrices] = useState<
    Record<
      string,
      {
        itunesPrice: number;
        itunesUrl: string;
        beatPortPrice: number;
        beatPortUrl: string;
        bandCampPrice: number;
        bandCampUrl: string;
      } | null
    >
  >({});
  

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
        setUser({
          id: data.id,
          display_name: data.display_name,
          profile_picture: data.profile_picture,
        });
        setPlaylists(data.playlists);
        setOriginalPlaylists(data.playlists);
      } catch (error) {
        console.error("Error fetching playlists:", error);
      }
    };

    fetchPlaylists();
  }, []);

  const fetchTracks = async (playlistId: string) => {
    if (tracks[playlistId]) {
      setTrackTable(true);
      return;
    }
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:5000/get_tracks/${playlistId}`, {
        withCredentials: true,
      });
      const data: Track[] = response.data;
      setTracks((prev) => ({ ...prev, [playlistId]: data }));
      setTrackTable(true);
    } catch (error) {
      console.error("Error fetching tracks:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSongPrices = async () => {
    if (!selectedPlaylist || !tracks[selectedPlaylist]) return;
    setLoading(true);
    try {
      const response = await axios.post(
        "http://localhost:5000/db_results",
        {
          tracks: tracks[selectedPlaylist],
        },
        { withCredentials: true }
      );

      const data = response.data;
      const priceMap: Record<
        string,
        {
          itunesPrice: number;
          itunesUrl: string;
          beatPortPrice: number;
          beatPortUrl: string;
          bandCampPrice: number;
          bandCampUrl: string;
        } | null
      > = {};

      data.forEach((item: any) => {
        if (item.track_name && item.artist) {
          priceMap[item.track_name] = {
            itunesPrice: item.itunes_price,
            itunesUrl: item.itunes_url,
            bandCampPrice: item.bandcamp_price,
            bandCampUrl: item.bandcamp_url,
            beatPortPrice: item.beatport_price,
            beatPortUrl: item.beatport_url,
          };
        }
      });

      setSongPrices(priceMap);
    } catch (error) {
      console.error("Error fetching song prices: ", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {playlists.length > 0 && (
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
                <PlaylistSort
                  playlists={playlists}
                  setPlaylists={setPlaylists}
                  originalPlaylists={originalPlaylists}
                  userId={user?.id}
                />
                <Grid mt="md">
                  {playlists
                    .slice((currentPage - 1) * 9, currentPage * 9)
                    .map((playlist) => (
                      <Grid.Col key={playlist.id} span={4} className={classes.playlistCard}>
                        <motion.div variants={cardVariants}>
                          <Card
                            className={classes.cardContent}
                            shadow="sm"
                            padding="lg"
                            onClick={() => {
                              setSelectedPlaylist(playlist.id);
                              setModalOpened(true);
                              fetchTracks(playlist.id);
                            }}
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
              selectedPlaylist
                ? playlists.find((p) => p.id === selectedPlaylist)?.name || "Tracklist"
                : "Tracklist"
            }
            centered
            styles={{
              header: {
                textAlign: "center",
                padding: "10px",
                borderRadius: "8px 8px 0 0",
              },
              body: {
                display: "flex",
                flexDirection: "column",
                maxHeight: "70vh",
              },
              title: {
                width: "100%",
                textAlign: "center",
                fontWeight: "bold",
                color: theme.colors.grape[3],
              },
            }}
          >
            <div style={{ flex: 1, overflowY: "auto", paddingBottom: "60px" }}>
              {loading ? (
                <LoadingRipple />
              ) : selectedPlaylist && tracks[selectedPlaylist]?.length > 0 ? (
                showTrackTable ? (
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
                          <Table.Td>
                            {songPrices[track.name] ? (
                              <a href={songPrices[track.name]?.bandCampUrl ?? "#"}>
                                {songPrices[track.name]?.bandCampPrice ?? "$--"}
                              </a>
                            ) : (
                              ""
                            )}
                          </Table.Td>
                          <Table.Td>
                            {songPrices[track.name] ? (
                              <a href={songPrices[track.name]?.beatPortUrl ?? "#"}>
                                {songPrices[track.name]?.beatPortPrice ?? "$--"}
                              </a>
                            ) : (
                              ""
                            )}
                          </Table.Td>
                          <Table.Td>
                            {songPrices[track.name] ? (
                              <a href={songPrices[track.name]?.itunesUrl ?? "#"}>
                                {songPrices[track.name]?.itunesPrice ?? "$--"}
                              </a>
                            ) : (
                              ""
                            )}
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                )
              ) : (
                <Text>No tracks available</Text>
              )}
            </div>

            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                width: "100%",
                backgroundColor: theme.colors.dark[7],
                padding: "10px",
                boxShadow: "0 -2px 5px rgba(0, 0, 0, 0.1)",
              }}
            >
              <Button
                fullWidth
                variant="outline"
                color="grape"
                onClick={async () => {
                  if (showTrackTable) {
                    await fetchSongPrices();
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
      )}
    </div>
  );
};

export default PlaylistTable;