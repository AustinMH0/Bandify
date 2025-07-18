import { Button } from "@mantine/core";

const Login = () => {
  const BASE_API_URL = import.meta.env.BASE_URL;

  const handleLogin = () => {
    window.location.href = `f{BASE_API_URL}`;
  };

  return <Button onClick={handleLogin}>Login with Spotify</Button>;
};

export default Login;