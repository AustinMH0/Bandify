import { AnimatePresence, motion } from "framer-motion";

import HeroWelcome from "./HeroWelcome";
import HeroLoginCard from "./HeroLoginCard";
import HeroLoggedIn from "./HeroLoggedIn";

import classes from "./HeroBox.module.css";

interface HeroBoxProps {
  loggedIn: boolean;
  showLoginCard: boolean;
  setShowLoginCard: (value: boolean) => void;
  hideHero: boolean;
  classes: Record<string, string>;
  user: any;
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
  
  return (
    <AnimatePresence mode="wait">
      {!hideHero && (
        <motion.div
          key="heroBox"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -30 }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
          className={`${classes.heroBox} ${showLoginCard ? classes.greenMode : ""} ${loggedIn ? classes.loggedIn : ""}`}
        >
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
      )}
    </AnimatePresence>
  );
};

export default HeroBox;

