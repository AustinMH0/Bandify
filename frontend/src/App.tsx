// Import styles of packages that you've installed.
// All packages except `@mantine/hooks` require styles imports
import '@mantine/core/styles.css';
import { MantineProvider } from '@mantine/core';

import { Header as Header } from './components/Header/Header';
import { Main as Main } from './components/Main/Main'

export default function App() {
  return (
    <MantineProvider>
      <Header />
      <Main />
    </MantineProvider>
  );
}
