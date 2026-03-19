import { useState, useEffect } from "react";
import { FlexLayout, Button, Text } from "@salt-ds/core";
import { DarkIcon, LightIcon, MenuIcon, CloseIcon } from "@salt-ds/icons";
import { useAuth } from "../context/AuthContext";
import type { Page } from "../App";
import logoLight from "../assets/logo-light.svg";
import logoDark from "../assets/logo-dark.svg";
import "./Navigation.css";

interface NavigationProps {
  mode: "light" | "dark";
  toggleMode: () => void;
  username?: string;
  page?: Page;
  onNavigate?: (page: Page) => void;
}

export function Navigation({ mode, toggleMode, username, page, onNavigate }: NavigationProps) {
  const { logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  // Close mobile menu on resize to desktop
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 641px)");
    const handler = () => { if (mq.matches) setMenuOpen(false); };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const handleNavigate = (p: Page) => {
    onNavigate?.(p);
    setMenuOpen(false);
  };

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
  };

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

        {/* Desktop nav */}
        <FlexLayout align="center" gap={1} className="appNav--desktop">
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

        {/* Mobile hamburger */}
        <div className="appNav--mobileToggle">
          <Button variant="secondary" onClick={toggleMode} aria-label="Toggle Theme">
            {mode === "light" ? <DarkIcon aria-hidden /> : <LightIcon aria-hidden />}
          </Button>
          {username && (
            <Button
              variant="secondary"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
            >
              {menuOpen ? <CloseIcon aria-hidden /> : <MenuIcon aria-hidden />}
            </Button>
          )}
        </div>
      </FlexLayout>

      {/* Mobile dropdown */}
      {menuOpen && username && (
        <nav className="appNav--mobileMenu">
          <Text styleAs="label" className="appNav--mobileUser">{username}</Text>
          <Button
            variant="secondary"
            onClick={() => handleNavigate("home")}
            aria-current={page === "home" ? "page" : undefined}
          >
            Home
          </Button>
          <Button
            variant="secondary"
            onClick={() => handleNavigate("leaderboard")}
            aria-current={page === "leaderboard" ? "page" : undefined}
          >
            Leaderboard
          </Button>
          <Button variant="secondary" onClick={handleLogout}>
            Logout
          </Button>
        </nav>
      )}
    </header>
  );
}
