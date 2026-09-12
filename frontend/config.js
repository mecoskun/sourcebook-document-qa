// For GitHub Pages, set this to the HTTPS origin of your deployed Python backend.
// This is public configuration. Never put credentials here.
window.SOURCEBOOK_API = ["localhost", "127.0.0.1"].includes(location.hostname) && location.port === "4173"
  ? "http://127.0.0.1:8000" : "";
