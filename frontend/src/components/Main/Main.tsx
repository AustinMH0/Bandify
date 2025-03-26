import { Button, Container, MantineProvider, Overlay, Text, Title } from '@mantine/core';
import { SpheresBackground } from '../Spheres/SpheresBackground';
import classes from './Main.module.css';
import PlaylistTable from '../PlaylistTable/PlaylistTable';
import Login from '../Login/Login';

export function Main() {
  return (
    <MantineProvider defaultColorScheme="dark">
    <div className={classes.wrapper}>
      <SpheresBackground />
      <SpheresBackground />

      {/* <Overlay color="#000" opacity={0.25} zIndex={1} /> */}

      <div className={classes.inner}>
        <Title className={classes.title}>Bandify</Title>

        <Container size={640}>
          <Text size="lg" className={classes.description}>
            Seamlessly add Spotify playlists to your Bandcamp wishlists.
          </Text>
        </Container>

        <div className={classes.controls}>
          <Login />
          {/* <Button className={classes.control} variant="white" size="lg">
            Get started
          </Button> */}
        </div>
        <Container>
          <PlaylistTable />
        </Container>
      </div>


    </div>
    </MantineProvider>
  );
}
