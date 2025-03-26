import { Button } from "@mantine/core";

const Login = () => {
  const handleLogin = () => {
    window.location.href = "http://localhost:5000/get_playlists"; 
  };

  return <Button onClick={handleLogin}>Bandify your Playlists</Button>;
};

export default Login;