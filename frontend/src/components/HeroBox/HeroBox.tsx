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

  const [fastGradient, setFastGradient] = useState(false);
  const [, setFadeOut] = useState(false);

  // Use refs for timeout cleanup
  const fadeTimeoutRef = useRef<number | null>(null);
  const clearTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (isInView) {
      bounceControls.start({
        scale: [0.95, 1.05],
        transition: { type: "spring", stiffness: 900, damping: 10 },
      });
      // No longer triggers fastGradient on scroll
    }
  }, [isInView, bounceControls]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;

    const deltaX = (offsetX - centerX) / centerX;
    const deltaY = (offsetY - centerY) / centerY;

    const deadZone = 0.2;
    const tiltStrength = 2;

    const isOutsideDeadZone = Math.abs(deltaX) > deadZone || Math.abs(deltaY) > deadZone;

    if (isOutsideDeadZone) {
      const rotateX = -deltaY * tiltStrength;
      const rotateY = deltaX * tiltStrength;

      e.currentTarget.style.transition = "transform 0.2s ease-out";
      e.currentTarget.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;

      if (!fastGradient) {
        setFastGradient(true);
        setFadeOut(false);

        fadeTimeoutRef.current = window.setTimeout(() => setFadeOut(true), 500);
        clearTimeoutRef.current = window.setTimeout(() => setFastGradient(false), 1000);
      }
    } else {
      // Inside dead zone — no rotation
      e.currentTarget.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg)";
    }
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.currentTarget.style.transition = "transform 0.2s ease";
    e.currentTarget.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg)";
  };

  useEffect(() => {
    return () => {
      if (fadeTimeoutRef.current !== null) clearTimeout(fadeTimeoutRef.current);
      if (clearTimeoutRef.current !== null) clearTimeout(clearTimeoutRef.current);
    };
  }, []);

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
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Fast Gradient Layer */}
          <AnimatePresence>
            {fastGradient && (
              <motion.div
                className={classes.fastGradient}
                initial={{ opacity: 0.5 }}
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
