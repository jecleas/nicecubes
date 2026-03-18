import { useState, type FormEvent } from "react";
import { Button, Input, FormField, FormFieldLabel } from "@salt-ds/core";
import { useAuth } from "../../context/AuthContext";
import "./LoginScreen.css";

/** Mirror the backend format_name logic for a live preview. */
function formatName(raw: string): string {
  const cleaned = raw.replace(/\s+/g, "");
  if (!cleaned) return "";
  return cleaned[0].toUpperCase() + cleaned.slice(1).toLowerCase();
}

export function LoginScreen() {
  const { login } = useAuth();
  const [rawName, setRawName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const preview = formatName(rawName);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!preview) {
      setError("Please enter your name.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    const result = await login(rawName);
    setIsSubmitting(false);
    if (result.error) {
      setError(result.error);
    }
  };

  return (
    <div className="loginScreen">
      <div className="loginScreen__card">
        <div className="loginScreen__header">
          <p className="loginScreen__eyebrow">Nice Cubes</p>
          <h1 className="loginScreen__title">Welcome</h1>
        </div>

        <form className="loginScreen__form" onSubmit={handleSubmit}>
          <FormField>
            <FormFieldLabel>Your name</FormFieldLabel>
            <Input
              value={rawName}
              inputProps={{
                onChange: (e) => {
                  setRawName(e.target.value);
                  setError(null);
                },
                autoFocus: true,
                autoComplete: "off",
              }}
              placeholder="e.g. Jeremy"
            />
          </FormField>

          {preview ? (
            <div className="loginScreen__preview">
              You'll appear as{" "}
              <span className="loginScreen__previewName">{preview}</span>
            </div>
          ) : null}

          {error ? (
            <div className="loginScreen__error" role="alert">
              {error}
            </div>
          ) : null}

          <Button type="submit" disabled={isSubmitting || !preview}>
            {isSubmitting ? "Entering…" : "Enter"}
          </Button>
        </form>
      </div>
    </div>
  );
}
