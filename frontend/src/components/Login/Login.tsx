import { Button } from "@mantine/core";

const Login = () => {
  const handleLogin = () => {
    window.location.href = "https://b1eq0t3rh0.execute-api.us-west-1.amazonaws.com/Prod";
  };

  return <Button onClick={handleLogin}>Login with Spotify</Button>;
};

export default Login;