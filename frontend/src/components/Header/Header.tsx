import { Burger, Button, Container, Group, Avatar, ActionIcon, Divider, Menu, Popover, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useState } from "react";
import { IconUser, IconSettings, IconStar, IconLogout, IconTool } from "@tabler/icons-react";
import classes from './Header.module.css';
import { ReactComponent as BandifyLogo } from '../../assets/bandify.svg';

interface HeaderProps {
  user: { display_name: string; profile_picture: string | null } | null;
}

const Header: React.FC<HeaderProps> = ({ user }) => {
  const [opened, { toggle }] = useDisclosure(false);


  const handleLogin = () => {
    window.location.href = "http://localhost:5000/";
  };

  const handleLogout = () => {
    window.location.href = "http://localhost:5000/logout";
  };

  const [hovered, setHovered] = useState(false);

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
          
        ) : null}

        <Burger opened={opened} onClick={toggle} hiddenFrom="xs" size="sm" />
      </Container>
    </header>
  );
};

export default Header; 
