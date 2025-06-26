import '@mantine/core/styles.css';
import { MantineProvider } from '@mantine/core';
import { Main as Main } from './components/Main/Main';

export default function App() {

  return (
    <MantineProvider defaultColorScheme="dark">
      <Main />
    </MantineProvider>
  );
}
