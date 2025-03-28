import '@mantine/core/styles.css';
import { MantineProvider } from '@mantine/core';

import { useState, useEffect } from "react";

import Header from './components/Header/Header';
import { Main as Main } from './components/Main/Main';

export default function App() {
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
    <MantineProvider defaultColorScheme="dark">
      <Header user={user} />
      <Main />
    </MantineProvider>
  );
}
