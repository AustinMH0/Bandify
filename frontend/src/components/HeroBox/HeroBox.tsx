import { useState, useRef, useEffect } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useInView,
  useAnimation,
  AnimatePresence,
} from "framer-motion";

import HeroWelcome from "./HeroWelcome";
import HeroLoginCard from "./HeroLoginCard";
import HeroLoggedIn from "./HeroLoggedIn";

import classes from "./HeroBox.module.css";

interface HeroBoxProps {
  loggedIn: boolean;
  showLoginCard: boolean;
  setShowLoginCard: (value: boolean) => void;
  user: any;
  hideHero: boolean;
  playlists: any[];
}

const HeroBox = ({
  loggedIn,
  showLoginCard,
  setShowLoginCard,
  hideHero,
  user,
  playlists,
}: HeroBoxProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll();
  const isInView = useInView(ref, { margin: "-40% 0px -40% 0px" });
  const bounceControls = useAnimation();

  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.5]);
  const background = useTransform(
    scrollYProgress,
    [0.2, 0], // Makes the change happen faster as it starts at a higher scroll progress
    [
      "conic-gradient(from 0deg, var(--mantine-color-dark-6), #ff6ec4, #ff91d1)", 
      "linear-gradient(#e100ff, #ff8800, #76ff64)"
    ]
  );
  
  const [fastGradient, setFastGradient] = useState(false);
  const [fadeOut, setFadeOut] = useState(false);
  
  useEffect(() => {
    if (isInView) {
      bounceControls.start({
        scale: [0.95, 1.05, 1],
        transition: { type: "spring", stiffness: 900, damping: 10 },
      });
  
      setFastGradient(true);
      setFadeOut(false);
  
      const fadeTimeout = setTimeout(() => {
        setFadeOut(true); // start fading out
      }, 2500); // fade after 2.5s
  
      const clearTimeoutId = setTimeout(() => {
        setFastGradient(false); // remove overlay completely
      }, 4000); // fully remove after 4s
  
      return () => {
        clearTimeout(fadeTimeout);
        clearTimeout(clearTimeoutId);
      };
    }
  }, [isInView, bounceControls]);
  

  return (
    <AnimatePresence mode="wait">
      {!hideHero && (
        <motion.div
          ref={ref}
          style={{
            opacity,
            scale,
            transformStyle: "preserve-3d",
            position: "relative",
          }}
          className={`
            ${classes.heroBox}
            ${showLoginCard ? classes.greenMode : ""}
            ${loggedIn ? classes.loggedIn : ""}
          `}
        >
          {/* Fast Gradient Layer */}
          <AnimatePresence>
            {fastGradient && (
              <motion.div
                className={classes.fastGradient}
                initial={{ opacity: 1 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 1.2, ease: "easeOut" }}
              />
            )}
          </AnimatePresence>
  
          <motion.div animate={bounceControls}>
            {!loggedIn ? (
              showLoginCard ? (
                <HeroLoginCard onBack={() => setShowLoginCard(false)} classes={classes} />
              ) : (
                <HeroWelcome onGetStarted={() => setShowLoginCard(true)} classes={classes} />
              )
            ) : (
              <HeroLoggedIn user={user} playlists={playlists} classes={classes} />
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
  
  
};

export default HeroBox;