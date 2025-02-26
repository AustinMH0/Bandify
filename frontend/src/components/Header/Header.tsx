
  import {
    Box,
    Burger,
    Button,
    Divider,
    Drawer,
    Group,
    HoverCard,
    ScrollArea,
    useMantineTheme,
  } from '@mantine/core';
  import { useDisclosure } from '@mantine/hooks';
  import classes from './Header.module.css';
  import { ReactComponent as BandifyLogo } from '../../assets/bandify.svg';
  
  export function Header() {
    const [drawerOpened, { toggle: toggleDrawer, close: closeDrawer }] = useDisclosure(false);
    const [linksOpened, { toggle: toggleLinks }] = useDisclosure(false);
    const theme = useMantineTheme();

    return (
      <Box pb={0} pos={'fixed'} top={0} style={{position: 'fixed', top: 0, left: 0, width: '100%', zIndex: 1}}>
        <header className={classes.header}>
          <Group justify="space-between" align="center" >
          
            <BandifyLogo />

            <Group visibleFrom="sm">
              <Button size="md" variant="subtle" color="grape">Features</Button>
              <Button 
                variant="outline" color="grape">Get Started</Button>
            </Group>
  
            <Burger opened={drawerOpened} onClick={toggleDrawer} hiddenFrom="sm" />
          </Group>
        </header>
  
        <Drawer
          opened={drawerOpened}
          onClose={closeDrawer}
          size="100%"
          padding="md"
          title="Navigation"
          hiddenFrom="sm"
          zIndex={1000000}
        >
          <ScrollArea h="calc(100vh - 80px" mx="-md">
            <Divider my="sm" />
  
            <a href="#" className={classes.link}>
              Home
            </a>
            <a href="#" className={classes.link}>
              About
            </a>
            {/* <a href="#" className={classes.link}>
              Academy
            </a> */}
  
            <Divider my="sm" />
  
            <Group justify="center" grow pb="xl" px="md">
              <Button variant="default">Log in</Button>
              <Button>Sign up</Button>
            </Group>
          </ScrollArea>
        </Drawer>
      </Box>
    );
  }