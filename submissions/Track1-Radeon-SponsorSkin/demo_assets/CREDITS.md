# Demo Asset Credits

The real-world targets below were selected and visually reviewed on
2026-07-30. Pexels permits free use and modification under the
[Pexels License](https://www.pexels.com/license/). Attribution is included for
provenance even though the license does not require it.

| Committed target | Photographer | Source |
|---|---|---|
| `real_inputs/porsche-911.jpg` | Dante Juhasz | [Pexels photo 13990526](https://www.pexels.com/photo/side-of-a-modern-sports-car-13990526/) |
| `real_inputs/city-bus.jpg` | Алёна Жигарева | [Pexels photo 9006627](https://www.pexels.com/photo/white-and-blue-bus-under-blue-sky-9006627/) |
| `real_inputs/delivery-truck.jpg` | Michael Lee | [Pexels photo 28158703](https://www.pexels.com/photo/a-white-truck-is-parked-on-the-side-of-the-road-28158703/) |
| `real_inputs/blank-hoodie.jpg` | cottonbro studio | [Pexels photo 5840464](https://www.pexels.com/photo/men-wearing-blank-hoodies-5840464/) |
| `real_inputs/workshop-cap.jpg` | Yaroslav Shuraev | [Pexels photo 4888594](https://www.pexels.com/photo/a-close-up-shot-of-a-cap-on-a-wooden-table-4888594/) |
| `real_inputs/street-billboard.jpg` | Peter Dyllong | [Pexels photo 36519146](https://www.pexels.com/photo/blank-billboard-in-urban-street-setting-36519146/) |
| `real_inputs/bus-shelter.jpg` | Tembela Bohle | [Pexels photo 5655660](https://www.pexels.com/photo/a-bus-shelter-with-billboards-illuminated-at-night-5655660/) |

The committed targets are resized crops of the originals. The hoodie output is
a fictional campaign concept; it does not imply endorsement by the pictured
people. Third-party photographs remain governed by the Pexels License and are
not relicensed under the project Apache-2.0 license.

| Project-owned asset group | License | Notes |
|---|---|---|
| `logos/*.png` | Apache-2.0 | Fictional NOVA GRID, APEX ZERO, and KINETIQ wordmarks |
| `real_previews/**` | Mixed derivative | Deterministic placement of project-owned logos over the credited Pexels targets |
| `inputs/*.png` | Apache-2.0 | Procedural regression fixtures retained for CPU-safe tests |
| `local_previews/**` | Apache-2.0 | Deterministic outputs from the procedural regression fixtures |

The local previews are development evidence only. They do not contain
generative-model output and do not demonstrate Radeon performance. Cloud
refinements, if committed later, must retain their run manifest and measured
ROCm evidence alongside this file.
