import Button from "./ui/Button";

interface LoginButtonProps {
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  children?: React.ReactNode;
}

const LoginButton = ({
  variant = "primary",
  size = "md",
  fullWidth = false,
  children = "Login",
}: LoginButtonProps) => {
  return (
    <Button variant={variant} size={size} fullWidth={fullWidth} type="submit">
      {children}
    </Button>
  );
};

export default LoginButton;
