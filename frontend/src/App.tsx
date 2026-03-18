import { useMemo, useState } from 'react';
import { SaltProvider } from "@salt-ds/core"
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Navigation } from "./components/Navigation";
import { LoginScreen } from "./components/LoginScreen";
import { Leaderboard } from "./components/Leaderboard";
import { IceTray, type TrayDefinition } from "./components/IceTray";
import './App.css'

export type Page = "home" | "leaderboard";

function AppContent() {
  const [mode, setMode] = useState<"light" | "dark">("light");
  const [page, setPage] = useState<Page>("home");
  const { user, isLoading } = useAuth();

  const homepageTrays = useMemo<TrayDefinition[]>(
    () => [
      { id: "tray1", label: "Tray 1", cubeCount: 12, columns: 6 },
      { id: "tray2", label: "Tray 2", cubeCount: 12, columns: 6 },
    ],
    [],
  );

  const toggleMode = () => {
    setMode((prev) => (prev === "light" ? "dark" : "light"));
  };

  if (isLoading) {
    return (
      <SaltProvider mode={mode}>
        <div className="appShell" />
      </SaltProvider>
    );
  }

  if (!user) {
    return (
      <SaltProvider mode={mode}>
        <LoginScreen />
      </SaltProvider>
    );
  }

  return (
    <SaltProvider mode={mode}>
      <div className="appShell">
        <Navigation mode={mode} toggleMode={toggleMode} username={user.username} page={page} onNavigate={setPage} />

        <main className="appMain">
          {page === "leaderboard" ? (
            <>
              <section className="appHero">
                <p className="appHero__eyebrow">Nice Cubes</p>
                <h1 className="appHero__title">Leaderboard</h1>
              </section>
              <Leaderboard />
            </>
          ) : (
            <>
              <section className="appHero">
                <p className="appHero__eyebrow">Nice Cubes</p>
                <h1 className="appHero__title">Ice Cube Trays</h1>
              </section>
              <IceTray trays={homepageTrays} />
            </>
          )}
        </main>
      </div>
    </SaltProvider>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App
