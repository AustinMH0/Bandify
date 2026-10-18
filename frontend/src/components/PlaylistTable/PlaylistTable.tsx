import { useState, useEffect } from "react";
import axios from "axios";
import {
  Alert,
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

import { authHeaders, hasSession } from "../../api/session";
import type { Playlist } from "../../types/types";

interface Track {
  name: string;
  artist: string;
}

interface SongPrice {
  track_name: string;
  artist: string;
  itunes_price: number | null;
  itunes_url: string;
  itunes_validated_at?: string | null;
  bandcamp_price: number | null;
  bandcamp_url: string;
  bandcamp_validated_at?: string | null;
  beatport_price: number | null;
  beatport_url: string;
  beatport_validated_at?: string | null;
  errors?: string[];
}

const trackKey = (track: Track) => JSON.stringify([track.name, track.artist]);

const PriceCell = ({ price, url, validatedAt }: {
  price?: number | null;
  url?: string;
  validatedAt?: string | null;
}) => {
  const label = price == null || !Number.isFinite(price) || price < 0
    ? "N/A" : `$${price.toFixed(2)}`;
  const checked = validatedAt ? new Date(validatedAt) : null;
  return <>
    {url && label !== "N/A" ? <a href={url}>{label}</a> : label}
    {checked && Number.isFinite(checked.getTime()) && (
      <Text component="time" dateTime={validatedAt ?? undefined} size="xs" c="dimmed" span>
        {" "}checked {checked.toLocaleDateString(undefined, { month: "short", day: "numeric" })}
      </Text>
    )}
  </>;
};

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
  const [showTrackTable, setTrackTable] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [fetchingPrices, setFetchingPrices] = useState(false);
  const [priceProgress, setPriceProgress] = useState(0);
  const [priceError, setPriceError] = useState("");
  const [songPrices, setSongPrices] = useState<Record<string, SongPrice>>({});

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

      const baseURL = import.meta.env.VITE_SEARCHRESULTS_API;

      if (!hasSession()) return;

      try {
        const response = await axios.get(`${baseURL}/get_playlists`, {
          headers: authHeaders(),
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

    const baseURL = import.meta.env.VITE_SEARCHRESULTS_API;

    if (tracks[playlistId]) {
      setTrackTable(true);
      return;
    }
    setLoading(true);
    try {
      const response = await axios.get(`${baseURL}/get_tracks/${playlistId}`, {
        headers: authHeaders(),
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
    setFetchingPrices(true);
    setTrackTable(false);
    setPriceProgress(0);
    setPriceError("");
    const baseURL = import.meta.env.VITE_SEARCHRESULTS_API;

    try {
      // A cache miss can take several seconds. Never put a whole playlist
      // behind one API Gateway/Lambda deadline or discard completed tracks.
      for (const [index, track] of tracks[selectedPlaylist].entries()) {
        try {
          const response = await axios.post<SongPrice[]>(`${baseURL}/db_results`, {
            tracks: [track],
          }, { timeout: 35000 });
          const item = response.data.find(
            (item) => item.track_name === track.name && item.artist === track.artist
          );
          if (!item) throw new Error("Missing track in price response");
          setSongPrices((prev) => ({ ...prev, [trackKey(track)]: item }));
          if (item.errors?.length) {
            setPriceError("Some stores could not be reached. Retry to look up missing prices.");
          }
        } catch (error) {
          console.error("Error fetching song prices:", error);
          setPriceError("Some prices could not be fetched. Retry to look up missing prices.");
        }
        setPriceProgress(index + 1);
      }
    } finally {
      setFetchingPrices(false);
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
                              setPriceError("");
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
            closeOnClickOutside={!fetchingPrices}
            closeOnEscape={!fetchingPrices}
            withCloseButton={!fetchingPrices}
            onClose={() => {
              setModalOpened(false);
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
              {fetchingPrices && (
                <div role="status" aria-live="polite">
                  <div aria-hidden="true"><LoadingRipple /></div>
                  <Text ta="center">Looking up prices: {priceProgress}/{selectedPlaylist ? tracks[selectedPlaylist]?.length : 0}</Text>
                </div>
              )}
              {priceError && <Alert color="red" role="alert">{priceError}</Alert>}
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
                            <PriceCell price={songPrices[trackKey(track)]?.bandcamp_price} url={songPrices[trackKey(track)]?.bandcamp_url} validatedAt={songPrices[trackKey(track)]?.bandcamp_validated_at} />
                          </Table.Td>
                          <Table.Td>
                            <PriceCell price={songPrices[trackKey(track)]?.beatport_price} url={songPrices[trackKey(track)]?.beatport_url} validatedAt={songPrices[trackKey(track)]?.beatport_validated_at} />
                          </Table.Td>
                          <Table.Td>
                            <PriceCell price={songPrices[trackKey(track)]?.itunes_price} url={songPrices[trackKey(track)]?.itunes_url} validatedAt={songPrices[trackKey(track)]?.itunes_validated_at} />
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
                disabled={loading || fetchingPrices}
                onClick={() => {
                  if (showTrackTable || priceError) {
                    void fetchSongPrices();
                  } else {
                    setTrackTable(true);
                  }
                }}
              >
                {fetchingPrices ? "Looking Up Prices…" : showTrackTable ? "View Prices" : priceError ? "Retry Prices" : "View Playlist"}
              </Button>
            </div>
          </Modal>
        </div>
      )}
    </div>
  );
};

export default PlaylistTable;
