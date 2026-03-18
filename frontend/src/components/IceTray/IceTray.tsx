import { useCallback, useEffect, useMemo, useState, type CSSProperties, type KeyboardEvent } from "react";
import { Button, InteractableCard } from "@salt-ds/core";
import "./IceTray.css";

export interface TrayDefinition {
  id: string;
  label: string;
  cubeCount: number;
  columns?: number;
}

interface TrayState {
  active_cubes: number[];
  is_frozen: boolean;
  expires_at: string | null;
}

interface IceTrayProps {
  trays: TrayDefinition[];
  apiBasePath?: string;
  pollIntervalMs?: number;
}

const EMPTY_TRAY_STATE: TrayState = {
  active_cubes: [],
  is_frozen: false,
  expires_at: null,
};

function buildApiUrl(apiBasePath: string, path: string) {
  if (!apiBasePath) {
    return path;
  }

  const normalizedBasePath = apiBasePath.endsWith("/") ? apiBasePath.slice(0, -1) : apiBasePath;
  return `${normalizedBasePath}${path}`;
}

function normalizeTrayState(state?: Partial<TrayState>): TrayState {
  return {
    active_cubes: Array.isArray(state?.active_cubes)
      ? state.active_cubes.filter((cubeIndex): cubeIndex is number => Number.isInteger(cubeIndex))
      : [],
    is_frozen: Boolean(state?.is_frozen),
    expires_at: typeof state?.expires_at === "string" ? state.expires_at : null,
  };
}

function getDefaultColumnCount(cubeCount: number) {
  return Math.max(1, Math.ceil(Math.sqrt(cubeCount)));
}

export function IceTray({ trays, apiBasePath = "", pollIntervalMs = 2000 }: IceTrayProps) {
  const [trayStates, setTrayStates] = useState<Record<string, TrayState>>(() =>
    Object.fromEntries(trays.map((tray) => [tray.id, EMPTY_TRAY_STATE])),
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [freezingTrayIds, setFreezingTrayIds] = useState<string[]>([]);
  const [pendingCubeKeys, setPendingCubeKeys] = useState<string[]>([]);

  useEffect(() => {
    setTrayStates((currentStates) => {
      const nextStates: Record<string, TrayState> = {};

      trays.forEach((tray) => {
        nextStates[tray.id] = currentStates[tray.id] ?? EMPTY_TRAY_STATE;
      });

      return nextStates;
    });
  }, [trays]);

  const trayIds = useMemo(() => trays.map((tray) => tray.id), [trays]);

  const syncTrayStates = useCallback(
    async (options?: { silent?: boolean }) => {
      const silent = options?.silent ?? false;

      try {
        const response = await fetch(buildApiUrl(apiBasePath, "/api/tray-states"));

        if (!response.ok) {
          throw new Error(`Unable to fetch tray states (${response.status})`);
        }

        const payload = (await response.json()) as Record<string, Partial<TrayState>>;

        setTrayStates((currentStates) => {
          const nextStates: Record<string, TrayState> = {};

          trayIds.forEach((trayId) => {
            nextStates[trayId] = normalizeTrayState(payload[trayId] ?? currentStates[trayId]);
          });

          return nextStates;
        });
        setErrorMessage(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to synchronize tray states.";
        setErrorMessage(message);
      } finally {
        if (!silent) {
          setIsLoading(false);
        }
      }
    },
    [apiBasePath, trayIds],
  );

  useEffect(() => {
    let isDisposed = false;

    setIsLoading(true);
    void syncTrayStates();

    const intervalId = window.setInterval(() => {
      if (!isDisposed) {
        void syncTrayStates({ silent: true });
      }
    }, pollIntervalMs);

    return () => {
      isDisposed = true;
      window.clearInterval(intervalId);
    };
  }, [pollIntervalMs, syncTrayStates]);

  const toggleCube = useCallback(
    async (trayId: string, cubeIndex: number) => {
      const cubeKey = `${trayId}:${cubeIndex}`;

      setPendingCubeKeys((currentKeys) => [...currentKeys, cubeKey]);

      try {
        const response = await fetch(buildApiUrl(apiBasePath, "/api/toggle-cube"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ trayId, cubeIndex }),
        });

        if (!response.ok) {
          throw new Error(`Unable to toggle cube (${response.status})`);
        }

        const payload = (await response.json()) as Partial<TrayState>;

        setTrayStates((currentStates) => ({
          ...currentStates,
          [trayId]: normalizeTrayState({
            ...currentStates[trayId],
            ...payload,
          }),
        }));
        setErrorMessage(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to toggle the selected cube.";
        setErrorMessage(message);
      } finally {
        setPendingCubeKeys((currentKeys) => currentKeys.filter((currentKey) => currentKey !== cubeKey));
      }
    },
    [apiBasePath],
  );

  const freezeTray = useCallback(
    async (trayId: string) => {
      setFreezingTrayIds((currentIds) => [...currentIds, trayId]);

      try {
        const response = await fetch(buildApiUrl(apiBasePath, "/api/freeze-tray"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ trayId }),
        });

        if (!response.ok) {
          throw new Error(`Unable to freeze tray (${response.status})`);
        }

        const payload = (await response.json()) as Partial<TrayState>;

        setTrayStates((currentStates) => ({
          ...currentStates,
          [trayId]: normalizeTrayState({
            ...currentStates[trayId],
            ...payload,
          }),
        }));
        setErrorMessage(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to freeze the tray.";
        setErrorMessage(message);
      } finally {
        setFreezingTrayIds((currentIds) => currentIds.filter((currentId) => currentId !== trayId));
      }
    },
    [apiBasePath],
  );

  const handleCubeKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>, trayId: string, cubeIndex: number, disabled: boolean) => {
      if (disabled) {
        return;
      }

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        void toggleCube(trayId, cubeIndex);
      }
    },
    [toggleCube],
  );

  return (
    <section className="iceTrayBoard" aria-busy={isLoading}>
      {errorMessage ? (
        <div className="iceTrayBoard__alert" role="alert">
          {errorMessage}
        </div>
      ) : null}

      <div className="iceTrayBoard__grid">
        {trays.map((tray) => {
          const trayState = trayStates[tray.id] ?? EMPTY_TRAY_STATE;
          const activeCubeIndexes = new Set(trayState.active_cubes);
          const isFreezing = freezingTrayIds.includes(tray.id);
          const cubeColumns = tray.columns ?? getDefaultColumnCount(tray.cubeCount);
          const trayStyle = {
            "--ice-tray-columns": String(cubeColumns),
          } as CSSProperties;

          return (
            <article className="iceTrayBoard__section" key={tray.id}>
              <div className="iceTrayBoard__traySurface" style={trayStyle}>
                {Array.from({ length: tray.cubeCount }, (_, cubeIndex) => {
                  const cubeKey = `${tray.id}:${cubeIndex}`;
                  const isPending = pendingCubeKeys.includes(cubeKey);
                  const isActive = activeCubeIndexes.has(cubeIndex);
                  const isDisabled = trayState.is_frozen || isPending;

                  return (
                    <InteractableCard
                      key={cubeKey}
                      aria-disabled={isDisabled}
                      aria-label={`${tray.label} cube ${cubeIndex + 1}`}
                      aria-pressed={isActive}
                      className={`iceTrayBoard__cube${isActive ? " iceTrayBoard__cube--active" : ""}${trayState.is_frozen ? " iceTrayBoard__cube--frozen" : ""}${isDisabled ? " iceTrayBoard__cube--disabled" : ""}`}
                      disabled={isDisabled}
                      onClick={() => {
                        if (!isDisabled) {
                          void toggleCube(tray.id, cubeIndex);
                        }
                      }}
                      onKeyDown={(event) => handleCubeKeyDown(event, tray.id, cubeIndex, isDisabled)}
                      role="button"
                      tabIndex={isDisabled ? -1 : 0}
                      variant={isActive ? "primary" : "secondary"}
                    />
                  );
                })}
              </div>

              <div className="iceTrayBoard__actions">
                <Button
                  disabled={isFreezing || trayState.is_frozen}
                  onClick={() => {
                    void freezeTray(tray.id);
                  }}
                >
                  {isFreezing ? "Freezing..." : trayState.is_frozen ? "Tray Frozen" : `Freeze ${tray.label}`}
                </Button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}