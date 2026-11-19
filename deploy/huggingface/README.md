---
title: CivicSignal
emoji: 📣
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
short_description: Campus complaints, sorted by multilingual AI
---

# CivicSignal

Students report campus problems in English, Hindi or Hinglish. A multilingual AI model
sorts each complaint into a category, supervisors review and update it, and students track
it until it is resolved.

This Space runs the app (FastAPI backend + React website) in one container.
It contains code only: no datasets, no secrets. Configuration is set in the Space settings.

Full source, tests and documentation: https://github.com/mishraasakshi/civicsignal
