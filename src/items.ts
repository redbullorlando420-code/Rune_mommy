export type Buff = {
  id: string; label: string; ms: number;
  speed?: number; power?: number; armor?: number;
};
export type ItemDef = {
  id: string; name: string; examine: string;
  kind: "shake" | "food" | "forage" | "loot" | "tool";
  stack: boolean; heal?: number; energy?: number;
  buff?: Buff; value: number; glyph: string; color: string;
};
const I = (
  id: string, name: string, examine: string, kind: ItemDef["kind"],
  extra: Partial<ItemDef> & { value: number; glyph: string; color: string }
): ItemDef => ({ id, name, examine, kind, stack: true, ...extra });

export const ITEMS: Record<string, ItemDef> = {
  cool_down: I("cool_down","The Cool Down","Signature vanilla-mint shake from The Shake Bar, 2545 E Hwy 50. Best-seller.","shake",{heal:42,energy:28,buff:{id:"cool",label:"Cool Down",ms:20000,armor:4},value:21,glyph:"C",color:"#7ef0d8"}),
  creamy_dream: I("creamy_dream","Creamy Dream","Oreo milkshake from The Shake Bar. Cookies all the way down.","shake",{heal:36,energy:16,value:14,glyph:"O",color:"#f5f0e6"}),
  biscoff_max: I("biscoff_max","Biscoff Max","Cookie-butter shake from The Shake Bar.","shake",{heal:22,energy:40,buff:{id:"max",label:"Biscoff Max",ms:18000,power:5},value:18,glyph:"B",color:"#c47a3a"}),
  coco_loco: I("coco_loco","CoCo-Loco","Coconut-chocolate shake. Slightly unhinged, in a helpful way.","shake",{heal:18,energy:36,buff:{id:"loco",label:"CoCo-Loco",ms:15000,speed:0.28},value:16,glyph:"L",color:"#6b3a2a"}),
  diner_vanilla: I("diner_vanilla","Diner Vanilla","Steak n Shake vanilla. Same lot as The Shake Bar.","shake",{heal:24,energy:12,value:11,glyph:"V",color:"#fff6d6"}),
  diner_chocolate: I("diner_chocolate","Diner Chocolate","Steak n Shake chocolate diner shake.","shake",{heal:28,energy:10,value:11,glyph:"H",color:"#4a2c22"}),
  vanilla_custard: I("vanilla_custard","Vanilla Custard","Ritter's frozen custard, 2560 E Hwy 50.","shake",{heal:26,energy:14,value:12,glyph:"RC",color:"#fff3c4"}),
  chocolate_custard: I("chocolate_custard","Chocolate Custard","Ritter's chocolate custard.","shake",{heal:30,energy:12,value:12,glyph:"RK",color:"#5c3317"}),
  cookie_dough_scoop: I("cookie_dough_scoop","Cookie Dough Scoop","Bruster's, 2450 E Hwy 50 Bldg H.","food",{heal:20,energy:18,value:10,glyph:"BH",color:"#d2a679"}),
  birthday_cake_scoop: I("birthday_cake_scoop","Birthday Cake Scoop","Bruster's Building H. Sprinkles for morale.","food",{heal:18,energy:22,value:10,glyph:"BB",color:"#ffb3d9"}),
  bacon_milkshake: I("bacon_milkshake","Bacon Milkshake","Five Guys custom shake, 1600 N Hancock Rd. A dare in a cup.","shake",{heal:26,energy:22,buff:{id:"bacon",label:"Bacon Power",ms:16000,power:3},value:19,glyph:"FG",color:"#c45c48"}),
  peanut_butter_shake: I("peanut_butter_shake","Peanut Butter Shake","Five Guys. The hug, not the dare.","shake",{heal:32,energy:14,value:15,glyph:"PB",color:"#c4a574"}),
  gold_medal_ribbon: I("gold_medal_ribbon","Gold Medal Ribbon","Baskin-Robbins, 1110 E Hwy 50.","food",{heal:22,energy:14,value:9,glyph:"31",color:"#e6c35c"}),
  moment_31: I("moment_31","31 Moment","Mystery scoop. Tess will not name the flavor.","food",{heal:28,energy:20,value:12,glyph:"??",color:"#c084fc"}),
  butterscotch_concrete: I("butterscotch_concrete","Butterscotch Concrete","Culver's, 1431 Johns Lake Rd. Eat it upside down.","shake",{heal:34,energy:20,value:17,glyph:"BC",color:"#e0a84a"}),
  mint_oreo_concrete: I("mint_oreo_concrete","Mint Oreo Concrete","Culver's concrete mixer.","shake",{heal:30,energy:24,buff:{id:"mint",label:"Mint Wake",ms:14000,speed:0.15},value:17,glyph:"MO",color:"#7dcea0"}),
  oreo_blizzard: I("oreo_blizzard","Oreo Blizzard","Dairy Queen, 860 US Hwy 27 (34714). They will flip it.","shake",{heal:32,energy:22,value:18,glyph:"OB",color:"#3d2b1f"}),
  reeses_blizzard: I("reeses_blizzard","Reese's Blizzard","DQ Blizzard. Peanut butter cups in a snowstorm.","shake",{heal:34,energy:18,value:18,glyph:"RB",color:"#d4a017"}),
  m_chocolate_shake: I("m_chocolate_shake","Window Chocolate Shake","McDonald's Clermont. Machine is, for once, on.","shake",{heal:20,energy:10,value:8,glyph:"MC",color:"#5c3317"}),
  m_vanilla_shake: I("m_vanilla_shake","Window Vanilla Shake","McDonald's Clermont vanilla.","shake",{heal:16,energy:14,value:8,glyph:"MV",color:"#fff6d6"}),
  chocolate_frosty: I("chocolate_frosty","Chocolate Frosty","Wendy's Clermont. Spoon or straw, we do not take sides.","shake",{heal:22,energy:12,value:9,glyph:"CF",color:"#4a2c22"}),
  vanilla_frosty: I("vanilla_frosty","Vanilla Frosty","Wendy's vanilla Frosty. A little speed in the slush.","shake",{heal:16,energy:18,buff:{id:"frosty",label:"Frosty Step",ms:12000,speed:0.18},value:9,glyph:"VF",color:"#f3efe6"}),
  moon_berry: I("moon_berry","Moon Berry","Wilds berry that only looks silver at dusk.","forage",{heal:8,energy:6,value:3,glyph:"mb",color:"#b388ff"}),
  wild_mint: I("wild_mint","Wild Mint","Grows along the Hwy 50 treeline.","forage",{energy:12,value:2,glyph:"wm",color:"#81c784"}),
  honeycomb: I("honeycomb","Honeycomb","Sticky. The bees have opinions.","forage",{heal:14,energy:10,value:8,glyph:"hc",color:"#ffd54f"}),
  dusk_mushroom: I("dusk_mushroom","Dusk Mushroom","Forest floor, after the neon fades.","forage",{heal:6,energy:16,value:4,glyph:"dm",color:"#ce93d8"}),
  sun_petal: I("sun_petal","Sun Petal","Bright enough to remember noon.","forage",{energy:8,value:3,glyph:"sp",color:"#ffcc80"}),
  pine_resin: I("pine_resin","Pine Resin","Tacky sap from the north wilds.","forage",{value:5,glyph:"pr",color:"#a1887f"}),
  raccoon_pelt: I("raccoon_pelt","Raccoon Pelt","Loot. Still a little bandit-shaped.","loot",{value:12,glyph:"rp",color:"#6d4c41"}),
  gremlin_bolt: I("gremlin_bolt","Gremlin Bolt","Hwy gremlin hardware. Do not swallow.","loot",{value:9,glyph:"gb",color:"#90a4ae"}),
  boar_bristle: I("boar_bristle","Boar Bristle","Stiff. Good for brushes and bad decisions.","loot",{value:11,glyph:"bb",color:"#8d6e63"}),
  crow_feather: I("crow_feather","Crow Feather","From the ruins flock.","loot",{value:6,glyph:"cf",color:"#37474f"}),
  moss_agate: I("moss_agate","Moss Agate","Mine-adjacent pebble with ideas of grandeur.","loot",{value:15,glyph:"ma",color:"#4db6ac"}),
  lucky_cap: I("lucky_cap","Lucky Bottlecap","Someone on US 27 dropped a wish.","loot",{value:7,glyph:"lc",color:"#ffd54f"}),
  copper_knife: I("copper_knife","Copper Knife","A starter blade. More picnic than raid.","tool",{stack:false,value:8,glyph:"ck",color:"#bcaaa4"}),
  berry_basket: I("berry_basket","Berry Basket","Foraging goes faster when berries have a home.","tool",{stack:false,value:10,glyph:"bk",color:"#a1887f"}),
  empty_cup: I("empty_cup","Empty Cup","The Shake Bar will not refill this. You have to buy.","tool",{value:1,glyph:"ec",color:"#eeeeee"}),
  travel_lantern: I("travel_lantern","Travel Lantern","Helps you look prepared in the wilds.","tool",{stack:false,value:14,glyph:"tl",color:"#ffb74d"}),
  picnic_cloth: I("picnic_cloth","Picnic Cloth","Clermont grass is nicer with a square of fabric.","tool",{stack:false,value:6,glyph:"pc",color:"#ef9a9a"}),
};

export function item(id: string): ItemDef | undefined { return ITEMS[id]; }
