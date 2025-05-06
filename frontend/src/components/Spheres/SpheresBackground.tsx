import Sphere from './Sphere';
const colors = ['#AE3CC9', '#F565EB', '#9C64F5'];
export function SpheresBackground() {
  return (
    <div
      style={{
        position: 'fixed', 
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        zIndex: -1, 
        pointerEvents: 'none', 
      }}
    >
      {[...Array(1)].map((_, index) => (
        <Sphere
          key={index}
          size={Math.max(100, Math.random() * 100 + 50)}
          color={colors[Math.floor(Math.random() * colors.length)]}
        />
      ))}
    </div>
  );
}