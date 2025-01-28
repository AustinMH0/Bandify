import Sphere from './Sphere'

export function SpheresBackground() {
  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden' }}>
      {[...Array(1)].map((_, index) => (
        <Sphere key={index} size={Math.random() * 100 + 50} />
      ))}
    </div>
  );
}
