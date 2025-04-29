import { Container, Text, Button, Group } from "@mantine/core";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
// import ParticlesBackground from "../ParticlesBackground/ParticlesBackground";
import classes from "../Welcome/Welcome.module.css";

const MotionDiv = motion.div;

const Welcome = () => {
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX - window.innerWidth / 2) / 40;
      const y = (e.clientY - window.innerHeight / 2) / 40;
      setOffset({ x, y });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <div className={classes.heroBox}>

      {/* <div className={classes.particlesWrapper}>
        <ParticlesBackground />
      </div> */}

      <Container size={700} className={classes.inner}>
        <MotionDiv
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px)`,
          }}
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
              gradient={{ from:"#ff91d1", to: "#ff6ec4" }}
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
                onClick={() => {
                  console.log("Navigate to app or start login flow");
                }}
              >
                Get Started
              </button>
            </Group>
          </MotionDiv>
        </MotionDiv>
      </Container>
    </div>
  );
};

export default Welcome;
