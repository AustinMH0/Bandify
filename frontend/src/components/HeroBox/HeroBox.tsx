import { useRef, useEffect } from "react";
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

  useEffect(() => {
    if (isInView) {
      bounceControls.start({
        scale: [0.95, 1.05, 1],
        transition: { type: "spring", stiffness: 900, damping: 10 },
      });
    }
  }, [isInView, bounceControls]);

  return (
    <AnimatePresence mode="wait">
      {!hideHero && (
        <motion.div
          ref={ref}
          style={{
            opacity,
            scale, // Scroll-driven scale
            transformStyle: "preserve-3d",
          }}
          className={`${classes.heroBox} ${showLoginCard ? classes.greenMode : ""} ${loggedIn ? classes.loggedIn : ""}`}
        >
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