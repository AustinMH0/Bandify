import { Button } from "@mantine/core";

const Login = () => {
  const baseURL = import.meta.env.VITE_SEARCHRESULTS_API;

  const handleLogin = () => {
    window.location.href = `${baseURL}/get_playlists`;
  };

  return <Button onClick={handleLogin}>Login with Spotify</Button>;
};

export default Login;