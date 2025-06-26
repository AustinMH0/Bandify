import { motion } from "framer-motion";

export default function LoadingRipple() {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "200px", 
      }}
    >
      <div
        style={{
          position: "relative",
          width: 120,
          height: 120,
        }}
      >
        <motion.span
          style={circleStyle}
          animate={{
            scale: [0, 1],
            opacity: [1, 0],
          }}
          transition={{
            duration: 1.5,
            ease: "easeInOut",
            repeat: Infinity,
            repeatDelay: 0.2,
          }}
        />
        <motion.span
          style={circleStyle}
          animate={{
            scale: [0, 1],
            opacity: [1, 0],
          }}
          transition={{
            duration: 1.5,
            ease: "easeInOut",
            repeat: Infinity,
            repeatDelay: 0.8, 
          }}
        />
      </div>
    </div>
  );
}

const circleStyle: React.CSSProperties = {
  position: "absolute",
  width: "100%",
  height: "100%",
  borderRadius: "50%",
  border: "4px solid #e599f7", 
  top: 0,
  left: 0,
};