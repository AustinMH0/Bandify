// Import styles of packages that you've installed.
// All packages except `@mantine/hooks` require styles imports
import '@mantine/core/styles.css';
import { MantineProvider } from '@mantine/core';

import { Header as Header } from './components/Header/Header';
import { Main as Main } from './components/Main/Main'
import { SpheresBackground } from './components/Spheres/SpheresBackground';

export default function App() {
  return (
    <MantineProvider>
      <Header />
      <SpheresBackground />
      <Main />
    </MantineProvider>
  );
}
