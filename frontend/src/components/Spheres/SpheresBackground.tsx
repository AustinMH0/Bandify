import Sphere from './Sphere';

export function SpheresBackground() {
  return (
    <div
      style={{
        position: 'absolute', // Overlay the spheres over the page
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        zIndex: 0, // Ensures it's behind other content
      }}
    >
      {[...Array(1)].map((_, index) => (
        <Sphere 
          key={index} 
          size={Math.max(100, Math.random() * 100 + 50)} 
        />
      ))}
    </div>
  );
}

export default SpheresBackground;
