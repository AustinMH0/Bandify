import { useState } from "react";

import { motion, AnimatePresence } from 'framer-motion';
import { Button, Container, Group, Avatar, ActionIcon, Popover, Text } from '@mantine/core';
import { IconBrandSpotify } from "@tabler/icons-react";

import classes from './Header.module.css';
import { ReactComponent as GroovonomyLogo } from '../../assets/groovonomy.svg';

interface HeaderProps {
  user: { display_name: string; profile_picture: string | null } | null;

  onGetStartedClick?: () => void;
  
  showLoginCard: boolean;
  setShowLoginCard: (value: boolean) => void;
}

const MotionDiv = motion.div;

const Header: React.FC<HeaderProps> = ({ user, showLoginCard, setShowLoginCard }) => {
  const [hovered, setHovered] = useState(false);

  return (
    <header className={classes.header}>
      <div className={`${classes.blob} ${classes.blob1}`} />
      <div className={`${classes.blob} ${classes.blob2} ${showLoginCard ? classes.greenMode : ""}`} />
      <Container fluid size="lg" className={classes.inner}>

        <GroovonomyLogo className={classes.logo}/>

        <Group visibleFrom="sm">

          <Button 
            size="md" 
            variant="subtle" 
            color="grape"
            onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth"})}
          >
            Features
          </Button>

          <AnimatePresence mode="wait">
            {!user && ( 
              showLoginCard ? (
                <MotionDiv className={classes.getStarted}
                  key="login-button"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ duration: 0.3 }}
                >
                  <Button
                    variant="outline"
                    color="green"
                    onClick={() => setShowLoginCard(true)}
                  >
                    <IconBrandSpotify size={20} />
                  </Button>
                </MotionDiv>
              ) : (
                <MotionDiv
                  key="get-started-button"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ duration: 0.3 }}
                >
                  <Button
                    className={classes.getStarted}
                    variant="outline"
                    color="grape"
                    onClick={() => setShowLoginCard(true)}
                  >
                    Get Started
                  </Button>
                </MotionDiv>
              )
            )}
          </AnimatePresence>

        {user ? (
        <Popover
          width={200}
          position="bottom-end"
          withArrow
          shadow="md"
          opened={hovered}
        >
          <Popover.Target>
            <ActionIcon
              variant="transparent"
              size="xl"
              radius="xl"
              style={{ padding: 0 }}
              onMouseEnter={() => setHovered(true)}
              onMouseLeave={() => setHovered(false)}
            >
              <Avatar
                src={user.profile_picture || undefined}
                radius="xl"
                color="grape"
              >
                {!user.profile_picture && user.display_name
                  ? user.display_name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .toUpperCase()
                  : null}
              </Avatar>
            </ActionIcon>
          </Popover.Target>

          <Popover.Dropdown
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
          >
            <Text style={{zIndex: 10}} size="sm" ta="center">
              Welcome, {user.display_name}!
            </Text>
          </Popover.Dropdown>
        </Popover>
          
        ) : null}

        </Group>
      </Container>
    </header>
  );
};

export default Header; 

          // <Menu shadow="md" width={200} position="bottom-end">
          //   <Menu.Target>
          //     <ActionIcon variant="transparent" size="xl" radius="xl" style={{ padding: 0 }}>
          //       <Avatar src={user.profile_picture || undefined} radius="xl" color="grape">
          //         {!user.profile_picture && user.display_name
          //           ? user.display_name
          //               .split(" ")
          //               .map((n) => n[0])
          //               .join("")
          //               .toUpperCase()
          //           : null}
          //       </Avatar>
          //     </ActionIcon>
          //   </Menu.Target>
          //   <Menu.Dropdown>
          //     <Menu.Label style={{ textAlign: "center" }}>{user.display_name}</Menu.Label>
          //     <Divider />
          //     <Menu.Item leftSection={<IconTool size={16} />}>Explore Stuff</Menu.Item>
          //     <Menu.Item leftSection={<IconUser size={16} />}>Customize Stuff</Menu.Item>
          //     <Menu.Item leftSection={<IconSettings size={16} />}>Settings</Menu.Item>
          //     <Menu.Item leftSection={<IconStar size={16} />}>Upgrade Stuff</Menu.Item>
          //     <Divider />
          //     <Menu.Item onClick={handleLogout} leftSection={<IconLogout size={16} />} color="red">
          //       Logout
          //     </Menu.Item>
          //   </Menu.Dropdown>
          // </Menu>