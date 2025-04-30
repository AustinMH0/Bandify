import { useEffect, useState } from "react";

import { Container, Text, Group } from "@mantine/core";
import { IconBrandSpotify, IconChevronLeft } from "@tabler/icons-react";
import { motion, AnimatePresence } from "framer-motion";

// import ParticlesBackground from "../ParticlesBackground/ParticlesBackground";
import classes from "../Welcome/Welcome.module.css";

interface WelcomeProps {
  showLoginCard: boolean;
  setShowLoginCard: (value: boolean) => void;
}


const MotionDiv = motion.div;

const Welcome: React.FC<WelcomeProps> = ({ showLoginCard, setShowLoginCard }) => {

  const [offset, setOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX - window.innerWidth / 4) / 60;
      const y = (e.clientY - window.innerHeight / 4) / 60;
      setOffset({ x, y });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <div className={`${classes.heroBox} ${showLoginCard ? classes.greenMode : ""}`}>
      {/* <div className={classes.particlesWrapper}>
        <ParticlesBackground />
      </div> */}

      <AnimatePresence mode="wait">
        {!showLoginCard ? (
          <Container 
            size={700} 
            className={classes.inner} 
            key="welcome"
          >
            <MotionDiv
              style={{
                transform: `translate(${offset.x}px, ${offset.y}px)`,
              }}
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
                <Text
                  component="span"
                  variant="gradient"
                  gradient={{ from: "#fdb6e0", to: "#ff6ec4" }}
                  inherit
                >
                  simple tool
                </Text>{" "}
                to compare prices of your favorite tracks
              </motion.h1>

              <MotionDiv
                className={classes.description}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
              >
                <Text className={classes.description} c="#ff91d1">
                  Login with Spotify and connect your playlists. Discover the best prices and
                  support artists you love.
                </Text>
              </MotionDiv>

              <MotionDiv
                className={classes.controls}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6, duration: 0.4 }}
              >
                <Group>
                  <button
                    className={classes.animatedButton}
                    onClick={() => setShowLoginCard(true)}
                  >
                    Get Started
                  </button>
                </Group>
              </MotionDiv>
            </MotionDiv>
          </Container>
        ) : (
          <div >
            <button
              className={classes.backArrow}
              onClick={() => setShowLoginCard(false)}
              aria-label="Go back"
            >
              <IconChevronLeft size={24} />
            </button>

            <Container
              size={700}
              className={classes.inner} 
              key="login"
            >
              <MotionDiv
                style={{
                  transform: `translate(${offset.x}px, ${offset.y}px)`,
                }}
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
                  Let's{" "}
                  <Text
                    component="span"
                    variant="gradient"
                    gradient={{ from: "#a6f4c5", to: "#00e676" }}
                    inherit
                  >
                    get started
                  </Text>{" "}
                </motion.h1>

                <MotionDiv
                  className={classes.description}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
                >
                  <Text className={classes.description} c="#a6f4c5">
                    We’ll fetch your Spotify playlists so you can start comparing track prices across Bandcamp, iTunes, and Beatport.
                  </Text>
                </MotionDiv>

                <MotionDiv
                  className={classes.controls}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.6, duration: 0.4 }}
                >
                    <button
                      className={`${classes.animatedButton} ${showLoginCard ? classes.greenMode : ""}`}
                      onClick={() => {
                        window.location.href = "http://localhost:5000/get_playlists";
                      }}
                    >
                      <IconBrandSpotify size={22} style={{ position: "relative", top: "1px" }} />
                       Log in 
                    </button>
                </MotionDiv>
              </MotionDiv>
            </Container>
          </div>

        )}
      </AnimatePresence>
    </div>
  );
};

export default Welcome;