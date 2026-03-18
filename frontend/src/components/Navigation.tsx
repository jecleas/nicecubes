import { FlexLayout, Button, Text } from "@salt-ds/core";
import { DarkIcon, LightIcon } from "@salt-ds/icons";
import { useAuth } from "../context/AuthContext";
import type { Page } from "../App";
import logoLight from "../assets/logo-light.svg";
import logoDark from "../assets/logo-dark.svg";

interface NavigationProps {
  mode: "light" | "dark";
  toggleMode: () => void;
  username?: string;
  page?: Page;
  onNavigate?: (page: Page) => void;
}

export function Navigation({ mode, toggleMode, username, page, onNavigate }: NavigationProps) {
  const { logout } = useAuth();

  return (
    <header className="appHeader">
      <FlexLayout align="center" className="appHeader__inner" justify="space-between">
        <FlexLayout align="center">
          <img
            src={mode === "light" ? logoLight : logoDark}
            alt="NiceCubes"
            height={40}
            style={{ display: "block" }}
          />
        </FlexLayout>

        <FlexLayout align="center" gap={1}>
          {username ? (
            <>
              <Text styleAs="label">{username}</Text>
              <Button
                variant="secondary"
                onClick={() => onNavigate?.("home")}
                aria-current={page === "home" ? "page" : undefined}
              >
                Home
              </Button>
              <Button
                variant="secondary"
                onClick={() => onNavigate?.("leaderboard")}
                aria-current={page === "leaderboard" ? "page" : undefined}
              >
                Leaderboard
              </Button>
              <Button variant="secondary" onClick={logout}>
                Logout
              </Button>
            </>
          ) : null}
          <Button variant="secondary" onClick={toggleMode} aria-label="Toggle Theme">
            {mode === "light" ? <DarkIcon aria-hidden /> : <LightIcon aria-hidden />}
          </Button>
        </FlexLayout>
      </FlexLayout>
    </header>
  );
}
