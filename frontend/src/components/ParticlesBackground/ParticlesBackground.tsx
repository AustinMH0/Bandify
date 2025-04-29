import { useEffect, useState } from "react";
import Particles from "@tsparticles/react";
import { loadFireflyPreset } from "@tsparticles/preset-firefly";
import { initParticlesEngine } from "@tsparticles/react";

const ParticlesBackground = () => {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadFireflyPreset(engine);
    }).then(() => {
      setLoaded(true);
    });
  }, []);

  if (!loaded) return null;

  return (
    <Particles
      id="tsparticles"
      options={{
        preset: "firefly",
        background: {
          color: {
            value: "transparent",
          },
        },
        interactivity: {
          events: {
            onHover: { enable: false },
            onClick: { enable: false },
            resize: { enable: true },
          },
        },
        particles: {
          shape: { type: "circle" },
        },
      }}
    />
  );
};

export default ParticlesBackground;
