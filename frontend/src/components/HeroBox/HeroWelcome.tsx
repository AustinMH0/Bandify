import { motion } from "framer-motion";
import { Text, Group, Container } from "@mantine/core";

export default function HeroWelcome({ onGetStarted, classes }: any) {
  return (
    <Container size={700} className={classes.inner} key="welcome">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -30 }}
        transition={{ type: "spring", stiffness: 40 }}
      >
        <motion.h1
          className={classes.title}
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          A{" "}
          <Text component="span" variant="gradient" gradient={{ from: "#fdb6e0", to: "#ff6ec4" }} inherit>
            simple tool
          </Text>{" "}
          to compare prices of your favorite tracks
        </motion.h1>

        <motion.div
          className={classes.description}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
        >
          <Text className={classes.description} c="#ff91d1">
            Login with Spotify and connect your playlists. Discover the best prices and support artists you love.
          </Text>
        </motion.div>

        <motion.div
          className={classes.controls}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6, duration: 0.4 }}
        >
          <Group>
            <button className={classes.animatedButton} onClick={onGetStarted}>
              Get Started
            </button>
          </Group>
        </motion.div>
      </motion.div>
    </Container>
  );
}
