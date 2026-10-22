import { useEffect, useState } from "react";

function SettingsPanel({ open, onClose, hasSavedKey, onSave, onClear }) {
  const [draftKey, setDraftKey] = useState("");

  useEffect(() => {
    if (!open) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [open, onClose]);

  if (!open) return null;

  const submit = (event) => {
    event.preventDefault();
    const key = draftKey.trim();
    if (!key) return;
    onSave(key);
    setDraftKey("");
  };

  return (
    <div className="settings-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section className="settings-panel" role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <div className="settings-heading">
          <div>
            <p className="simulation-eyebrow">PECTEN PREFERENCES</p>
            <h2 id="settings-title">Settings</h2>
          </div>
          <button type="button" className="settings-close" onClick={onClose} aria-label="Close settings">×</button>
        </div>
        <form onSubmit={submit}>
          <label className="settings-key-label" htmlFor="gemini-api-key">Your Gemini API key</label>
          <input id="gemini-api-key" className="settings-key-input" type="password" value={draftKey}
            onChange={(event) => setDraftKey(event.target.value)} placeholder={hasSavedKey ? "A key is saved for this tab" : "Paste your Gemini API key"}
            autoComplete="new-password" spellCheck="false" />
          <p className="settings-help">Your key is kept in this browser tab's session and sent only with circuit-analysis requests. It is not saved by PECTEN's backend.</p>
          {hasSavedKey && <p className="settings-saved" role="status">A personal key is active for this tab.</p>}
          <div className="settings-actions">
            {hasSavedKey && <button type="button" className="settings-clear" onClick={onClear}>Remove saved key</button>}
            <button type="submit" className="btn-primary" disabled={!draftKey.trim()}>Save key</button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default SettingsPanel;
