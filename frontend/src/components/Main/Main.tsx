import { Container } from '@mantine/core';
import { SpheresBackground } from '../Spheres/SpheresBackground';
import classes from './Main.module.css';
import PlaylistTable from '../PlaylistTable/PlaylistTable';
import Welcome from '../Welcome/Welcome'

export function Main() {  
  return (
    <div className={classes.wrapper}>
      <div className={`${classes.blob} ${classes.blob1}`} />
      <div style={{ position: 'relative', zIndex: 0 }}>
        <SpheresBackground />
        <SpheresBackground />
      </div>

      <div className={classes.inner}>
        <Welcome />
        <Container>
          <PlaylistTable />
        </Container>
      </div>
    </div>
  );
}
