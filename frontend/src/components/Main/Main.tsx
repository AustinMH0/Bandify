import { Container } from '@mantine/core';
import { SpheresBackground } from '../Spheres/SpheresBackground';
import classes from './Main.module.css';
import PlaylistTable from '../PlaylistTable/PlaylistTable';

export function Main() {  
  return (
    <div className={classes.wrapper}>
      <SpheresBackground />
      <SpheresBackground />
      <div className={classes.inner}>
        <Container>
          <PlaylistTable />
        </Container>
      </div>
    </div>
  );
}
