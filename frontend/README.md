# SatQuery AI Frontend v3

ChatGPT-style React/Vite/Tailwind frontend for SIH26167.

## v3 additions
- Satellite image workspace appears after upload
- Image preview with zoom controls
- Map view using React Leaflet
- Optical / SAR / detected-region / change overlay layer controls
- Demo spatial regions on image and map
- GeoTIFF-friendly placeholder explaining backend-rendered preview
- Existing settings, Light/Dark appearance selection, delete recent analyses and Google Fonts retained

## Run

```bash
npm install
npm run dev
```

## Backend integration

The current AI response is mock data. Replace the mock `sendQuery()` implementation in `src/main.jsx` with your backend API call.

For real satellite imagery, the backend can return:
- rendered image/tile URL
- GeoJSON region geometries
- map center/bounds
- optical/SAR layer URLs
- change-detection mask URL

The frontend viewer is already structured to display those results.
