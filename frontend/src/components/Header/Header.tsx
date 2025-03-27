import { Burger, Button, Container, Group, Avatar, Modal, ActionIcon } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import classes from './Header.module.css';
import { ReactComponent as BandifyLogo } from '../../assets/bandify.svg';

interface HeaderProps {
  user: { display_name: string; profile_picture: string | null } | null;
}

const Header: React.FC<HeaderProps> = ({ user }) => {
  const [opened, { toggle, open, close }] = useDisclosure(false);

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
          // <Modal opened={opened} onClose={close} title={user.display_name} >
            
          // </Modal>
          <div>
            <ActionIcon onClick={open} variant="transparent" size="xl" radius="xl" style={{ padding: 0 }} >
              <Avatar src={user.profile_picture} />
            </ActionIcon>
            <Modal
              opened={opened}
              onClose={close}
              title={user.display_name}
              overlayProps={{
                backgroundOpacity: 0.55,
                blur: 3,
              }}
              size="sm"
              radius="md"
            >

            </Modal>            
          </div>


        ) : (
          <Button>Login</Button>
        )}

        <Burger opened={opened} onClick={toggle} hiddenFrom="xs" size="sm" />
      </Container>
    </header>
  );
};

export default Header; 
