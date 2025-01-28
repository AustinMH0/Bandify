/** @jsxImportSource @emotion/react */

import { css } from '@emotion/react';
import * as motion from "motion/react-client"


const sphereStyle = css({
  position: 'absolute',
  borderRadius: '50%',
  background: `radial-gradient(circle, rgba(255, 0, 150, 1), rgba(0, 204, 255, 1))`,
  boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.3)',
  transform: 'translate(-50%, -50%)',
  offsetPath: `path("M50,30 Q60,10 85,20 Q100,30 105,50 Q110,70 100,90 Q90,110 80,120 Q70,130 50,120 Q40,110 40,90 Q40,70 50,50 Q60,30 50,30 Z")`,
});

const transition = { duration: 10, repeat: Infinity, ease: 'easeInOut' , repeatType: 'reverse'}

const Sphere = ({ size }: { size: number }) => {

  return (
    <div style={{ position: "relative" }}>
    <motion.path
        d="M50,30 Q60,10 85,20 Q100,30 105,50 Q110,70 100,90 Q90,110 80,120 Q70,130 50,120 Q40,110 40,90 Q40,70 50,50 Q60,30 50,30 Z"
        fill="transparent"
        strokeWidth="12"
        stroke="var(--hue-6-transparent)"
        strokeLinecap="round"
        initial={{ pathLength: 0.001 }}
        animate={{ pathLength: 1 }}
    />
    <motion.div
      css={sphereStyle}
      style={{
        width: size,
        height: size,
        top: '0%',
        left: '20%',
      }}
      initial={{ offsetDistance: "0%", scale: 1 }}
      animate={{ offsetDistance: "100%", scale: 1 }}
      transition={transition}
    />
  </div>
  );
};

export default Sphere;


