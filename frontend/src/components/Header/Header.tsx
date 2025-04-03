import { Burger, Button, Container, Group, Avatar, ActionIcon, Divider, Menu } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
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

        {user?.profile_picture ? (
      <div>
        <Menu shadow="md" width={200} position="bottom-end">
          <Menu.Target>
            <ActionIcon variant="transparent" size="xl" radius="xl" style={{ padding: 0 }}>
              <Avatar src={user.profile_picture} />
            </ActionIcon>
          </Menu.Target>

          <Menu.Dropdown>
            <Menu.Label style={{ textAlign: "center" }}>{user.display_name}</Menu.Label>
            <Divider />

            <Menu.Item leftSection={<IconTool size={16} />}>Explore Stuff</Menu.Item>
            <Menu.Item leftSection={<IconUser size={16} />}>Customize Stuff</Menu.Item>
            <Menu.Item leftSection={<IconSettings size={16} />}>Settings</Menu.Item>
            <Menu.Item leftSection={<IconStar size={16} />}>Upgrade Stuff</Menu.Item>

            <Divider />
            <Menu.Item onClick={handleLogout} leftSection={<IconLogout size={16} />} color="red">
              Logout
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </div>
        ) : (
          <Button onClick={handleLogin} >Login</Button>
        )}

        <Burger opened={opened} onClick={toggle} hiddenFrom="xs" size="sm" />
      </Container>
    </header>
  );
};

export default Header; 
