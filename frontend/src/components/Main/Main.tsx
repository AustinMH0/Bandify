import { useState, useEffect } from "react";

import { Container } from "@mantine/core";

import { SpheresBackground } from "../Spheres/SpheresBackground";
import classes from "./Main.module.css";
import PlaylistTable from "../PlaylistTable/PlaylistTable";
import HeroBox from "../HeroBox/HeroBox";
import Header from "../Header/Header";

import type { Playlist } from "../../types/types";

export function Main() {
  const [showLoginCard, setShowLoginCard] = useState(false);
  const [user, setUser] = useState<{ display_name: string; profile_picture: string | null } | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [hideHero,] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch("https://b1eq0t3rh0.execute-api.us-west-1.amazonaws.com/Prod/get_playlists", {
          credentials: "include",
        });

        if (!response.ok) throw new Error(`HTTP Error ${response.status}`);

        const data = await response.json();
        setUser({
          display_name: data.display_name,
          profile_picture: data.profile_picture,
        });
        setPlaylists(data.playlists);
      } catch (error) {
        console.error("Error fetching user:", error);
      }
    };

    fetchUser();
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
          <PlaylistTable playlists={playlists} setPlaylists={setPlaylists} />
        </Container>
      </div>
    </div>
  );
}
