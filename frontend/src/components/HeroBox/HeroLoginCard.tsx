import { motion } from "framer-motion";
import { Container, Text } from "@mantine/core";
import { IconChevronLeft, IconBrandSpotify } from "@tabler/icons-react";

export default function HeroLoginCard({ onBack, classes }: any) {
  return (
    <div>
      <button className={classes.backArrow} onClick={onBack} aria-label="Go back">
        <IconChevronLeft size={24} />
      </button>

      <Container size={700} className={classes.inner} key="login">
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
            transition={{ duration: 0.6 }}
          >
            Let's{" "}
            <Text component="span" variant="gradient" gradient={{ from: "#a6f4c5", to: "#00e676" }} inherit>
              get started
            </Text>
          </motion.h1>

          <motion.div
            className={classes.description}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <Text className={classes.description} c="#a6f4c5">
              We’ll fetch your Spotify playlists so you can start comparing track prices across Bandcamp, iTunes, and Beatport.
            </Text>
          </motion.div>

          <motion.div
            className={classes.controls}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            <button
              className={`${classes.animatedButton} ${classes.greenMode}`}
              onClick={() => (window.location.href = "https://b1eq0t3rh0.execute-api.us-west-1.amazonaws.com/Prod/get_playlists")}
            >
              <IconBrandSpotify size={22} style={{ position: "relative", top: "1px" }} />
              Log in
            </button>
          </motion.div>
        </motion.div>
      </Container>
    </div>
  );
}