import { Button, Container, Group, Avatar, ActionIcon, Popover, Text } from '@mantine/core';
import { useState } from "react";
import classes from './Header.module.css';
import { ReactComponent as BandifyLogo } from '../../assets/bandify.svg';

interface HeaderProps {
  user: { display_name: string; profile_picture: string | null } | null;
  onGetStartedClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, onGetStartedClick }) => {
  const [hovered, setHovered] = useState(false);

  return (
    <header className={classes.header}>
      <div className={`${classes.blob} ${classes.blob1}`} />
      <div className={`${classes.blob} ${classes.blob2}`} />
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
            onClick={onGetStartedClick}
          >
            Get Started
          </Button>

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
              <Text size="sm" ta="center">
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