

  import { useState } from 'react';
  import { Burger, Button, Container, Group } from '@mantine/core';
  import { useDisclosure } from '@mantine/hooks';

  import classes from './Header.module.css';
  import { ReactComponent as BandifyLogo } from '../../assets/bandify.svg';

  const links = [
    { link: '/about', label: 'Features' },
    { link: '/start', label: 'Get Started' },
  ];
  
  export function Header() {
    const [opened, { toggle }] = useDisclosure(false);
    const [active, setActive] = useState(links[0].link);
  
    const items = links.map((link) => (
      <a
        key={link.label}
        href={link.link}
        className={classes.link}
        data-active={active === link.link || undefined}
        onClick={(event) => {
          event.preventDefault();
          setActive(link.link);
        }}
      >
        {link.label}
      </a>
    ));
    

    return (
      <header className={classes.header}>
        <Container fluid size="lg" className={classes.inner}>
          <BandifyLogo />
          <Group visibleFrom="sm">
              <Button 
                size="md" 
                variant="subtle" 
                color="grape"
                onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth"})}
              >
                  Features
                </Button>
              <Button 
                variant="outline" 
                color="grape"
                onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth"})}
              >
                  Get Started
              </Button>
            </Group>
  
          <Burger opened={opened} onClick={toggle} hiddenFrom="xs" size="sm" />
        </Container>
      </header>
    );
  }
