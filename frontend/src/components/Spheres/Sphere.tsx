/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
import { motion } from "framer-motion";
import { useEffect, useState } from "react";


//background-image: linear-gradient(319deg,  0%, #aa00ff 37%, #cc4499 100%);
// #313dff // #313dff #aa00ff 0%, #cc4499 37%, #71116a 100% #663dff

const sphereStyle = css({
  position: 'absolute',
  borderRadius: '50%',
  background: `radial-gradient(circle, rgba(220,53,227,1) 0%, rgba(191,36,190,1) 35%, rgba(41,2,22,0.7979924391631652) 100%)`,
  boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.3)',
  transform: 'translate(-50%, -50%)',
  filter: 'blur(10px)'
});

const Sphere = ({ size }: { size: number }) => {
  const [position, setPosition] = useState({
    x: Math.random() * window.innerWidth * 0.8, // Initial random X
    y: Math.random() * window.innerHeight * 0.8, // Initial random Y
  });

  useEffect(() => {
    const updatePosition = () => {
      setPosition({
        x: Math.random() * window.innerWidth * 0.8, // Avoid edges
        y: Math.random() * window.innerHeight * 0.8,
      });
    };

    const interval = setInterval(updatePosition, 10000); // Update every 5s
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      css={sphereStyle}
      style={{
        width: size,
        height: size,
      }}
      initial={{ x: position.x, y: position.y }} // Set initial position
      animate={{ x: position.x, y: position.y }}
      transition={{ duration: 8, ease: "easeInOut" }}
    />
  );
};

export default Sphere;
