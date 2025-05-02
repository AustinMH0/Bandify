import { motion } from "framer-motion";
import { Container, Text, Group } from "@mantine/core";

export default function HeroLoggedIn({ user, playlists, classes }: any) {
  return (
    <Container size={700} className={`${classes.inner} ${classes.loggedIn}`} key="logged-in">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -30 }}
        transition={{ type: "spring", stiffness: 40 }}
      >
        <motion.h1 className={classes.title} initial={{ opacity: 0, y: -30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          Welcome back, {user?.display_name}
        </motion.h1>

        <Text className={classes.description} mt="sm" c="#ff91d1">
          You have{" "}
          <Text component="span" c="#00e676"  inherit>
            {playlists.length}
          </Text>
          {" "}playlists synced 
        </Text>

        <motion.div className={classes.controls} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.4 }}>
          <Group>
            <button
              className={classes.animatedButton}
              onClick={() => {
                const cardSection = document.getElementById("playlist-cards");
                if (cardSection) cardSection.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
            >
              View Playlists
            </button>
          </Group>
        </motion.div>
      </motion.div>
    </Container>
  );
}
