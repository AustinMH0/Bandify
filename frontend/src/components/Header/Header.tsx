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
  
  
  export function Header() {
    const [drawerOpened, { toggle: toggleDrawer, close: closeDrawer }] = useDisclosure(false);
    const [linksOpened, { toggle: toggleLinks }] = useDisclosure(false);
    const theme = useMantineTheme();

    return (
      <Box pb={0} pos={'sticky'} top={0} style={{position: 'fixed', top: 0, left: 0, width: '100%', zIndex: 1}}>
        <header className={classes.header}>
          <Group justify="space-between" h="100%">
  
            <Group h="100%" gap={0} visibleFrom="sm">
              <a href="#" className={classes.link}>
                Home
              </a>
              <HoverCard width={600} position="bottom" radius="md" shadow="md" withinPortal>
  
              </HoverCard>
              <a href="#" className={classes.link}>
                Learn
              </a>
              {/* <a href="#" className={classes.link}>
                Academy
              </a> */}
            </Group>
  
            <Group visibleFrom="sm">
              <Button variant="default">Log in</Button>
              <Button>Sign up</Button>
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