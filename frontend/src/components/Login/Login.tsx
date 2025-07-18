import { Button } from "@mantine/core";

const Login = () => {
  const baseURL= import.meta.env.VITE_API_BASE_URL;

  const handleLogin = () => {
    window.location.href = `${baseURL}`;
  };

  return <Button onClick={handleLogin}>Login with Spotify</Button>;
};

export default Login;