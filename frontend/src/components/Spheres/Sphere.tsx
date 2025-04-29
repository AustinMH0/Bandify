/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
import { motion } from "framer-motion";
import { useEffect, useState } from "react";


const Sphere = ({ size, color }: { size: number; color: string }) => {
  const [position, setPosition] = useState({
    x: Math.random() * window.innerWidth * 0.8,
    y: Math.random() * window.innerHeight * 0.8,
  });

  useEffect(() => {
    const updatePosition = () => {
      setPosition({
        x: Math.random() * window.innerWidth * 0.8,
        y: Math.random() * window.innerHeight * 0.8,
      });
    };

    const interval = setInterval(updatePosition, 10000);
    return () => clearInterval(interval);
  }, []);


  const sphereStyle = css({
    position: 'absolute',
    borderRadius: '50%',
    background: `radial-gradient(circle, ${color} 0%, ${color}80 35%, transparent 100%)`,
    // background: `radial-gradient(circle, ${color} 0%, rgba(0,0,0,0) 100%)`,
    boxShadow: '0px 10px 40px rgba(0, 0, 0, 0.4)',
    transform: 'translate(-50%, -50%)',
    filter: 'blur(10px)',
    opacity: 0.7,
    zIndex: -1
  });

  return (
    <motion.div
      css={sphereStyle}
      style={{
        width: size,
        height: size,
      }}
      initial={{ x: position.x, y: position.y }}
      animate={{ x: position.x, y: position.y }}
      transition={{ duration: 8, ease: "easeInOut" }}
    />
  );
};

export default Sphere;
