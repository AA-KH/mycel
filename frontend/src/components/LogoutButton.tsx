import { useAuth } from "../contexts/AuthContext";
import Button from "./ui/Button";

interface LogoutButtonProps {
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  children?: React.ReactNode;
}

const LogoutButton = ({
  variant = "secondary",
  size = "md",
  fullWidth = false,
  children = "Log Out",
}: LogoutButtonProps) => {
  const { logout } = useAuth();

  return (
    <Button
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      onClick={() => logout()}
    >
      {children}
    </Button>
  );
};

export default LogoutButton;
