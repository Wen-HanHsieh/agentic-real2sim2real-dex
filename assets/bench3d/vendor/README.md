# Vendored three.js

- `three.module.min.js` and `OrbitControls.js` from three@0.160.0 (npm, `build/three.module.min.js` and
  `examples/jsm/controls/OrbitControls.js`), MIT licence (`LICENSE`).
- One change: `OrbitControls.js` imports from `./three.module.min.js` instead of the bare specifier `three`, so no import map
  or CDN is needed at runtime.
