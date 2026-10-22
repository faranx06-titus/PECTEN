# PECTEN frontend

React 19 and Vite client for the PECTEN circuit-analysis prototype. It handles PDF page rendering/cropping, uploads, topology review, editable circuit values, source-page and analyzed-image views, current-flow overlays, and solved component readings. Solving is performed by the FastAPI backend; Gemini is only used for image interpretation. From this directory:

```sh
npm install
npm run dev
```

The app expects the FastAPI backend at `http://127.0.0.1:8000`. Set `VITE_API_URL` in `.env.local` to point it elsewhere. A user's optional Gemini key is held in tab-scoped `sessionStorage` and sent only with image-analysis requests. The flow animation is an illustrative encoding of solved current; bulb glow is a qualitative response to solved power. For supported circuit types, physics boundaries, and backend setup, see the [root README](../README.md) and [architecture](../docs/architecture.md).
