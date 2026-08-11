import { rmSync, cpSync, readFileSync, writeFileSync } from "node:fs";

rmSync("frontend", { recursive: true, force: true });
cpSync("backend/app/static", "frontend", { recursive: true });

const apiBase = (process.env.PARAKH_API_BASE || "").trim();
if (apiBase) {
  // Point the built site at the deployed API engine (e.g. https://parakh-ai.onrender.com).
  // Works alongside the ?api=<url> query-param override on any page.
  const snippet =
    `<script>\n  window.PARAKH_API_BASE = window.PARAKH_API_BASE || ${JSON.stringify(apiBase)};\n</script>`;
  for (const page of ["index.html", "dashboard.html"]) {
    const p = `frontend/${page}`;
    writeFileSync(p, readFileSync(p, "utf8").replace("</head>", snippet + "</head>"));
  }
  console.log(`frontend/ rebuilt — PARAKH_API_BASE=${apiBase}`);
} else {
  console.log("frontend/ rebuilt — set PARAKH_API_BASE env var to embed the engine URL");
}