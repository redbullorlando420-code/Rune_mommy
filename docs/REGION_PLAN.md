# Florida region plan

This is an implementation backlog, not a road map or a claim that the game
matches any place exactly. Real places are used as broad visual and gameplay
references; fictionalized names and compressed layouts should be used in-game.

## 1. West Clermont — Sanctuary / US-27 hub

Starting reference: the Sanctuary Drive neighborhood around the user-supplied
3449 Sanctuary Dr address. Keep the existing home as a fictionalized block;
do not reproduce a private residence.

- **Lake Louisa wildlands** — rolling sandhill trails, oak hammocks, three-lake
  canoe route, trailhead ranger and wildlife encounter loop.
- **Lake Hiawatha preserve** — boardwalk / wetland micro-zone, bird calls and
  fishing or foraging nodes.
- **Lake Minneola waterfront** — pier, lakefront path, small marina, sunset
  market and a water-reflection showcase scene.
- **US-27 / Hwy 50 corridor** — motels, fuel, roadside produce, service lanes
  and the existing neon commercial row.

## 2. Orlando — four distinct arrival districts

- **Downtown / Lake Eola** — swan-lake loop, skyline, brick streets, civic
  plaza and evening event lighting.
- **International Drive** — dense hotel, attraction and convention-strip
  driving zone with elevated signs and a landmark observation wheel silhouette.
- **Mills 50** — murals, small restaurants, night market and a pedestrian-first
  side-quest district.
- **Lake Nona** — brighter, contemporary lakeside / tech-campus zone suited to
  delivery, vehicle and social missions.

## 3. Kissimmee — lakefront and old roadside entertainment

- **Lake Tohopekaliga / Kissimmee Lakefront Park** — marina, fishing pier,
  splash-pad silhouette and airboat launch gameplay.
- **Historic downtown** — rail-side storefronts, public-square events and
  nightlife pedestrians.
- **Old Town-inspired strip** — fictionalized neon midway, classic-car meet and
  arcade mini-games; no real-business branding.
- **Shingle Creek** — shaded trail, cypress waterway and wildlife collecting.

## 4. Tampa — waterfront, channel and historic grid

- **Riverwalk** — connected waterfront path, museum facades, event lighting,
  bridges and water-taxi movement.
- **Channel District** — port cranes, arena-adjacent plaza and industrial
  delivery missions.
- **Ybor-inspired historic district** — brick warehouses, cigar-history motifs,
  murals and a streetcar route.

## 5. Miami — high-contrast coastal finale

- **South Beach-inspired art-deco strip** — pastel hotels, palms, ocean glare
  and night neon.
- **Wynwood-inspired mural grid** — dense art walls, galleries and collectible
  photo/paint quests.
- **Little Havana-inspired main street** — music, domino tables, food stalls and
  warm evening lighting.
- **Downtown / Biscayne Bay** — towers, elevated transit silhouette, marina and
  a stormy waterfront event.

## 6. Tokyo — vertical night district collection

- **Asakusa-inspired old-town river edge** — temple-gate silhouette, lantern
  market, compact alleys and a Sumida-style water route.
- **Akihabara-inspired electric grid** — stacked shopfronts, arcade light,
  electronics quests and dense pedestrian navigation.
- **Shibuya-inspired crossing** — controlled crowd simulation, rooftop signs,
  fashion storefronts and a timed delivery loop.
- **Odaiba-inspired bay** — elevated transit silhouette, broad waterfront,
  plaza-scale public art and a night reflection showcase.

## 7. Rome — layered history and walkability

- **Colosseum / Forum-inspired archaeological zone** — fictionalized ruins,
  daylight shadow study, guided-history quests and protected walking paths.
- **Trastevere-inspired lane network** — warm stucco, tiny plazas, restaurant
  exteriors and evening social events.
- **Tiber riverbank** — bridges, embankment path, street musicians and seasonal
  market props.
- **Modern transit arrival** — a clean travel hub that connects the historical
  zones without pretending to recreate protected sites exactly.

## Implementation order

1. Finish the current Clermont hub's environment, lighting and interaction
   polish.
2. Build Lake Louisa / Lake Minneola as one streamed Clermont exterior.
3. Add Kissimmee lakefront as the first travel destination and prove the travel
   gate/save/load flow.
4. Add Orlando as a denser, vehicle-focused city district.
5. Add Tampa and Miami only after the region streaming, LOD and mission
   contracts are stable.
6. Use Tokyo and Rome as later vertical-density and historical-material test
   cases after the Florida travel framework is proven.

## Visual sources used for direction

- Florida State Parks, Lake Louisa State Park — `floridastateparks.org/parks-and-trails/lake-louisa-state-park`
- City of Kissimmee, parks — `kissimmee.gov/Parks`
- Visit Orlando, neighborhoods and International Drive — `visitorlando.com/plan/get-to-know-orlando/`
- Visit Tampa Bay, Riverwalk — `visittampabay.com/things-to-do/riverwalk/`
- Greater Miami & Miami Beach, pocket guide — `miamiandbeaches.com`
- GO TOKYO official guide — `gotokyo.org/en/`
- Parco archeologico del Colosseo / Turismo Roma — `colosseo.it/en/`, `turismoroma.it/en`
