import { useState, useEffect } from "react";

import { Container } from "@mantine/core";

import { SpheresBackground } from "../Spheres/SpheresBackground";
import classes from "./Main.module.css";
import PlaylistTable from "../PlaylistTable/PlaylistTable";
import HeroBox from "../HeroBox/HeroBox";
import Header from "../Header/Header";

import { authHeaders, hasSession } from "../../api/session";
import { discoverPlaylists, type Discovery } from "../../api/discovery";
import type { Playlist } from "../../types/types";

export function Main() {
  const [showLoginCard, setShowLoginCard] = useState(false);
  const [user, setUser] = useState<Discovery | null>(null);
  const [originalPlaylists, setOriginalPlaylists] = useState<Playlist[]>([]);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [hideHero,] = useState(false);

  useEffect(() => {
    let active = true;
    const session = authHeaders().Authorization;
    const fetchUser = async () => {
      if (!hasSession()) return;

      try {
        const data = await discoverPlaylists();
        if (!active || authHeaders().Authorization !== session) return;
        setUser(data);
        setPlaylists(data.playlists);
        setOriginalPlaylists(data.playlists);
      } catch (error) {
        console.error("Error fetching user:", error);
      }
    };

    fetchUser();
    return () => { active = false; };
  }, []);

  const loggedIn = user !== null;

  return (
    <div>
      <Header user={user} showLoginCard={showLoginCard} setShowLoginCard={setShowLoginCard} />
      <div className={classes.wrapper}>
        <div className={`${classes.blob} ${classes.blob1}`} />
        <div style={{ position: "relative", zIndex: 0 }}>
          <SpheresBackground />
          <SpheresBackground />
        </div>
        <div className={classes.inner}>
          <HeroBox
            user={user}
            playlists={playlists}
            loggedIn={loggedIn}
            showLoginCard={showLoginCard}
            setShowLoginCard={setShowLoginCard}
            hideHero={hideHero}
          />
        </div>
        <Container>
          <PlaylistTable playlists={playlists} setPlaylists={setPlaylists}
            originalPlaylists={originalPlaylists} userId={user?.id} />
        </Container>
      </div>
    </div>
  );
}
