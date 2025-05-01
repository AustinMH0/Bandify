import { useState, useEffect } from "react";

import { Container } from '@mantine/core';

import { SpheresBackground } from '../Spheres/SpheresBackground';
import classes from './Main.module.css';
import PlaylistTable from '../PlaylistTable/PlaylistTable';
import Welcome from '../Welcome/Welcome'
import Header from '../Header/Header';

import type { Playlist } from "../../types/types";

export function Main() {

  const [showLoginCard, setShowLoginCard] = useState(false);
  const [user, setUser] = useState<{ display_name: string; profile_picture: string | null } | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);

  useEffect(() => {
    const fetchUser = async () => {
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
        console.error("Error fetching user:", error);
      }
    };

    fetchUser();
  }, []);

  const loggedIn = user !== null;

  return (
    <div>
      <Header 
        user={user}
        showLoginCard={showLoginCard}
        setShowLoginCard={setShowLoginCard}
      />
      <div className={classes.wrapper}>
        <div className={`${classes.blob} ${classes.blob1}`} />
        <div style={{ position: 'relative', zIndex: 0 }}>
          <SpheresBackground />
          <SpheresBackground />
        </div>
        <div className={classes.inner}>
          <Welcome 
            user={user}
            playlists={playlists}
            showLoginCard={showLoginCard} 
            setShowLoginCard={setShowLoginCard} 
            loggedIn={loggedIn}
          />
        </div>
        <Container>
          <PlaylistTable 
            playlists={playlists}
            setPlaylists={setPlaylists}
          />
        </Container>
      </div>
    </div>
  );
}