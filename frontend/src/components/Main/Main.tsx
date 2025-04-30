import { useState, useEffect } from "react";
import { Container } from '@mantine/core';

import { SpheresBackground } from '../Spheres/SpheresBackground';
import classes from './Main.module.css';
import PlaylistTable from '../PlaylistTable/PlaylistTable';
import Welcome from '../Welcome/Welcome'
import Header from '../Header/Header';

export function Main() {  
  const [showLoginCard, setShowLoginCard] = useState(false);

  const [user, setUser] = useState<{ display_name: string; profile_picture: string | null } | null>(null);
  
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
      } catch (error) {
        console.error("Error fetching user:", error);
      }
    };

    fetchUser();
  }, []);


  return (
    <div>
      <Header user={user} onGetStartedClick={() => setShowLoginCard(true)} />
      <div className={classes.wrapper}>
        <div className={`${classes.blob} ${classes.blob1}`} />
          <div style={{ position: 'relative', zIndex: 0 }}>
            <SpheresBackground />
            <SpheresBackground />
          </div>
        <div className={classes.inner}>
        <Welcome showLoginCard={showLoginCard} setShowLoginCard={setShowLoginCard} />
          <Container>
            <PlaylistTable />
          </Container>
        </div>
      </div>
    </div>
  );
}
