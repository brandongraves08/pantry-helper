import { useEffect, useState } from 'react';
import { AlertTriangle, Droplet, ShieldCheck, Sprout } from 'lucide-react';

const STORAGE_KEY = 'pantry-helper-emergency-plan-v1';

const foods = [
  ['food-rice', 'Long-grain white rice or basmati', '100 lb dry', '165,000'],
  ['food-oats', 'Rolled or quick oats', '35 lb dry', '59,500'],
  ['food-pasta', 'Egg-free dry pasta', '40 lb', '64,000'],
  ['food-flour', 'All-purpose flour or plain masa harina', '30 lb', '48,000'],
  ['food-beans', 'Dry pinto and black beans', '40 lb', '60,000'],
  ['food-oil', 'Neutral cooking oil', '5 gal total in smaller bottles', '76,800'],
  ['food-butter', 'Peanut butter or tolerated seed butter', '24 × 16 oz', '63,600'],
  ['food-nuts', 'Tolerated nuts or seeds', '16 lb', '43,200'],
  ['food-fruit', 'Raisins or other dried fruit', '16 lb', '20,800'],
  ['food-crackers', 'Milk- and egg-free crackers', '20 lb', '38,000'],
  ['food-canned-beans', 'Ready-to-eat canned beans', '100 × 15 oz', '33,000'],
  ['food-meat', 'Canned beef and pork', '60 × 12 oz', '15,600'],
  ['food-fish', 'Canned salmon, sardines, or other tolerated fish', '84 × 5 oz', '15,120'],
  ['food-vegetables', 'Canned vegetables, diced tomatoes, and plain tomato sauce', '96 × 14–15 oz', '9,600'],
  ['food-canned-fruit', 'Canned fruit', '72 × 14–15 oz', '17,280'],
  ['food-beverage', 'Shelf-stable fortified oat or soy beverage, as tolerated', '36 × 32 fl oz', '14,400'],
  ['food-cereal', 'Milk- and egg-free ready-to-eat cereal', '12 × 16 oz', '19,200'],
  ['food-potatoes', 'Plain instant potato flakes', '24 × 4 oz', '8,400'],
  ['food-seasonings', 'Iodized salt, baking powder, spices, vinegar, and verified vegetable or beef bouillon', '1 working supply and 1 backup per staple seasoning', '—'],
];

const checklist = [
  ['task-subtract-stock', 'Subtract usable food already on hand from each shopping target. Write the actual package calories and best-by dates on the inventory.'],
  ['task-verify-tally', 'Verify the final tally against the household target. Confirm weekly protein, varied fruit and vegetables, and reliable calcium and vitamin D sources; check actual fortification labels.'],
  ['task-labels', 'Recheck ingredients on every purchase, especially crackers, pasta, instant potatoes, cereal, bouillon, and canned meals. Check for whey, casein, albumen, allergen statements, and cross-contact when needed.'],
  ['water-store', 'Store unopened bottled water or sanitized food-grade containers with tight lids. Date home-filled water and replace every six months; follow commercial bottle dates. Store away from heat, sunlight, and chemicals.'],
  ['water-sources', 'Identify a primary refill source and a backup, fill and carry containers, check transport, and sign up for water-provider alerts.'],
  ['water-treat', 'Follow utility advisories. When local instructions call for boiling, bring clear water to a rolling boil for one minute in Celina. Use bottled water or another safe source if fuel or chemical contamination is suspected. Keep printed treatment instructions with the kit.'],
  ['safety-storage', 'Keep the pantry cool and dry. Use sturdy shelving, heavy containers low, sealed food-grade dry-good containers, labels, dates, first-in/first-out rotation, and discard damaged cans.'],
  ['safety-leftovers', 'Keep a manual can opener and shelf-stable meals accessible. Refrigerate opened foods and cooked leftovers promptly at 40°F or below; use single-meal packages or discard leftovers without safe refrigeration.'],
  ['safety-outage', 'Keep appliance doors closed. Refrigerator: generally up to four hours unopened; discard perishables after four hours without power unless held at 40°F or below. Full freezer: about 48 hours; half full: 24 hours. Never taste food to check safety.'],
  ['safety-cooking', 'Use a Jetboil or approved camp stove outdoors, away from openings, on a stable surface, with approved fuel. Never use a stove, grill, or generator indoors or in a garage. Keep generators at least 20 feet from doors, windows, and vents; check battery-backed CO alarms.'],
  ['safety-test', 'Test a week of cooking and log fuel and water. Favor quick oats, pasta, canned beans, and instant potatoes when fuel is limited. Follow dry-bean directions and use potable water; verify portable power capacity before relying on it.'],
  ['task-monthly', 'Monthly, move the oldest packages forward and replace what the family used.'],
  ['task-refresh', 'After each practice week or outage, update quantities from actual consumption and refresh used stock.'],
];

const stages = [
  ['stage-1', '1 · 14 days', '112,000 kcal', 'Build the ready-to-eat tier first. Buy a manual can opener and work from 12 to 56 gal of stored water.'],
  ['stage-2', '2 · 30 days', '240,000 kcal', 'Add rice, pasta, dry beans, oil, canned vegetables, and fortified plant beverage. Set up indoor shelving, label dry goods, and document water refill options.'],
  ['stage-3', '3 · 60 days', '480,000 kcal', 'Add protein variety, canned fruit and vegetables, and the next round of staples. Run a pantry-only week and measure portions, fuel, and water use.'],
  ['stage-4', '4 · 90 days', '720,000 kcal', 'Close gaps using package calories. Verify the 14-day no-cook reserve, water replenishment, and outdoor cooking setup. Schedule inventory and water checks.'],
];

const rotation = [
  ['Monday', 'Oatmeal with dried fruit', 'Peanut butter, crackers, and canned fruit', 'Beef and bean chili over rice'],
  ['Tuesday', 'Peanut butter on skillet flatbread', 'Salmon, crackers, and fruit', 'Pasta with tomato sauce and canned beef'],
  ['Wednesday', 'Cinnamon oatmeal with nuts', 'Pinto bean and tomato salad with crackers', 'Black bean and rice burrito bowls with corn'],
  ['Thursday', 'Cereal with shelf-stable oat beverage', 'Peanut butter, crackers, and dried fruit', 'Canned salmon with mashed potatoes and green beans'],
  ['Friday', 'Peanut butter, canned fruit, and crackers', 'Mashed bean flatbread', 'Bean and vegetable soup with flatbread'],
  ['Saturday', 'Oatmeal with nuts and raisins', 'Sardines, crackers, and canned fruit', 'Pork and vegetable rice skillet'],
  ['Sunday', 'Milk- and egg-free skillet pancakes', 'Bean and corn salad with crackers', 'Pasta with vegetables and tomato sauce'],
];

const waterMilestones = [
  ['3 days', '12 gal', 'First purchase. Keep some in easy-to-carry containers.'],
  ['7 days', '28 gal', 'Add 16 gal and confirm indoor storage space.'],
  ['14 days', '56 gal', 'Add 28 gal. Use this as the initial stored-water target.'],
  ['30 days', '120 gal', 'Arrange another 64 gal beyond the 14-day reserve.'],
  ['60 days', '240 gal', 'Plan for 184 gal beyond the reserve over this period.'],
  ['90 days', '360 gal', 'Plan for 304 gal beyond the reserve. Storing all 360 gal would weigh about 3,000 lb before containers.'],
];

const knownIds = new Set([...foods.map(([id]) => id), ...checklist.map(([id]) => id), ...stages.map(([id]) => id), 'task-no-cook']);
function readProgress() {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '[]');
    return new Set(Array.isArray(parsed) ? parsed.filter((id) => typeof id === 'string' && knownIds.has(id)) : []);
  } catch {
    return new Set();
  }
}

function Check({ id, checked, onChange, children, className = '', layout = 'flex' }) {
  return <label className={`${layout} items-start gap-3 cursor-pointer rounded-lg focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2 ${className}`}>
    <input type="checkbox" checked={checked} onChange={() => onChange(id)} className="mt-1 h-4 w-4 shrink-0 accent-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600" />
    <span className={layout === 'grid' ? 'min-w-0' : 'min-w-0 flex-1'}>{children}</span>
  </label>;
}

function Card({ children, className = '' }) {
  return <section className={`rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-6 ${className}`}>{children}</section>;
}

function SectionTitle({ icon: Icon, children, eyebrow }) {
  return <div className="mb-4 flex items-start gap-3"><div className="rounded-xl bg-indigo-50 p-2 text-indigo-700"><Icon aria-hidden="true" size={20} /></div><div><p className="text-xs font-semibold uppercase tracking-wider text-indigo-700">{eyebrow}</p><h2 className="text-xl font-bold text-gray-900">{children}</h2></div></div>;
}

export default function EmergencyPlan() {
  const [checked, setChecked] = useState(readProgress);
  useEffect(() => {
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify([...checked])); } catch { /* Browser storage may be unavailable; plan remains usable in memory. */ }
  }, [checked]);
  const toggle = (id) => setChecked((previous) => {
    const next = new Set(previous);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });

  return <div className="mx-auto max-w-6xl space-y-6 text-gray-800">
    <header className="rounded-3xl bg-gradient-to-br from-indigo-700 to-indigo-900 p-6 text-white shadow-sm sm:p-8">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-3xl"><p className="mb-2 text-sm font-semibold uppercase tracking-widest text-indigo-200">Preparedness guide · estimate</p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">90-Day Emergency Food Supply Plan</h1>
          <p className="mt-3 text-indigo-100">Family of four · Celina, Texas. A standalone planning checklist — it does not change your pantry inventory or shopping list.</p>
        </div>
        <div className="rounded-2xl bg-white/10 p-4 sm:min-w-48"><p className="text-sm text-indigo-100">Checklist progress</p><p className="mt-1 text-2xl font-bold">{checked.size} <span className="text-base font-medium text-indigo-100">{checked.size === 1 ? 'item' : 'items'} complete</span></p></div>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-white/10 p-4"><p className="text-sm text-indigo-100">Minimum food target</p><p className="text-xl font-bold">720,000 kcal</p><p className="text-sm text-indigo-100">90 days · 8,000/day household</p></div>
        <div className="rounded-xl bg-white/10 p-4"><p className="text-sm text-indigo-100">Estimated food total</p><p className="text-xl font-bold">771,500 kcal</p><p className="text-sm text-indigo-100">About 96 household days</p></div>
        <div className="rounded-xl bg-white/10 p-4"><p className="text-sm text-indigo-100">Stored water target</p><p className="text-xl font-bold">56 gal</p><p className="text-sm text-indigo-100">14 days · replenish separately</p></div>
      </div>
    </header>

    <Card><SectionTitle icon={AlertTriangle} eyebrow="Start with the assumptions">Planning assumptions & dietary exclusions</SectionTitle>
      <ul className="grid gap-3 text-sm leading-6 md:grid-cols-2">
        <li className="rounded-xl bg-gray-50 p-4"><strong>360 person-days.</strong> At a planning average of 2,000 calories per person per day, budget <strong>8,000 calories per household day</strong> and <strong>720,000 calories for 90 days</strong>. Adjust for actual ages, appetites, activity, and dietary needs before buying in bulk.</li>
        <li className="rounded-xl bg-gray-50 p-4"><strong>Shared meals are milk-free and egg-free.</strong> Exclude lentils and jasmine rice, and avoid chicken and turkey, including broths and stocks. Use plain long-grain white rice or basmati, plus pinto, black, or other tolerated beans.</li>
        <li className="rounded-xl bg-gray-50 p-4"><strong>Hybrid pantry.</strong> Aim for roughly 70% familiar foods rotated through normal meals and 30% dedicated reserve. The food plan covers 90 days, with a 14-day stored water goal and a separate replenishment plan.</li>
        <li className="rounded-xl bg-gray-50 p-4"><strong>Limited refrigeration and cooking during outages.</strong> Keep a two-week reserve of foods that can be eaten without heating, including a first three days requiring minimal prep water. Count these foods within the inventory below.</li>
        <li className="rounded-xl bg-gray-50 p-4 md:col-span-2"><strong>Original budget placeholders:</strong> $750 economy, $1,500 balanced, $2,500 for more variety and convenience, and $4,000 premium. Price the actual cart locally and track water containers, shelving, and fuel separately.</li>
      </ul>
    </Card>

    <Card><SectionTitle icon={Sprout} eyebrow="Food reserve · estimates">90-day inventory targets</SectionTitle>
      <p className="mb-4 text-sm leading-6 text-gray-600">Household targets; package sizes and calorie densities are estimates. The original chat’s interactive quantities were unavailable, so this is a reconstructed inventory. Use actual package labels to tally packages × servings per package × calories per serving. Log calories separately for foods requiring heat and foods served straight from the package. These targets are not current pantry stock.</p>
      <div className="space-y-2">
        {foods.map(([id, item, target, kcal]) => <Check key={id} id={id} checked={checked.has(id)} onChange={toggle} layout="grid" className="grid-cols-[auto_minmax(0,1fr)] gap-x-3 border-b border-gray-100 px-2 py-3 last:border-0 sm:grid-cols-[auto_minmax(0,1fr)]">
          <div className="grid min-w-0 gap-1 sm:grid-cols-[minmax(0,1fr)_minmax(8rem,0.7fr)_6rem]"><span className="font-medium text-gray-900">{item}</span><span className="text-sm text-gray-600 sm:text-right">{target}</span><span className="text-sm font-semibold text-gray-900 sm:text-right">{kcal}{kcal === '—' ? '' : <> <span className="font-normal text-gray-500">kcal</span></>}</span></div>
        </Check>)}
      </div>
      <div className="mt-4 rounded-xl bg-indigo-50 p-4 sm:flex sm:items-center sm:justify-between"><strong className="text-gray-900">Estimated food total · about 96 household days at 8,000 kcal/day</strong><span className="text-lg font-bold text-indigo-800">771,500 kcal</span></div>
      <p className="mt-3 text-sm text-gray-600">The estimate leaves about <strong>51,500 kcal</strong> of margin. Confirm weekly portions provide enough protein, varied fruit and vegetables, and reliable calcium and vitamin D sources such as a suitable fortified plant beverage; check actual labels for fortification.</p>
      <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4"><Check id="task-no-cook" checked={checked.has('task-no-cook')} onChange={toggle}><strong>Set aside 112,000 kcal</strong> within the inventory for the 14-day no-cook tier. Starting allocation: 16 jars peanut butter, 11 lb crackers, 8 lb nuts or seeds, 6 lb dried fruit, 30 cans beans, 24 cans fish, 20 cans fruit, and 20 cans vegetables. The table estimates this at about <strong>113,720 kcal</strong>. Check labels, divide into 14 household-day portions, and swap ingredients as needed for variety and tolerance.</Check></div>
      <div className="mt-4 text-sm leading-6 text-gray-600"><Check id="task-labels" checked={checked.has('task-labels')} onChange={toggle}>Recheck ingredients on every purchase, especially crackers, pasta, instant potatoes, cereal, bouillon, and canned meals. Check for milk ingredients such as whey and casein and egg ingredients such as albumen. Read full ingredient lists and allergen statements. If avoidance is allergy-related, verify manufacturer cross-contact guidance as needed; use clean prep surfaces and utensils. <SourceLink href="https://www.fda.gov/food/food-allergensgluten-free-guidance-documents-regulatory-information/frequently-asked-questions-food-allergen-labeling-guidance-industry">FDA allergen labeling guidance</SourceLink></Check></div>
    </Card>

    <Card><SectionTitle icon={Sprout} eyebrow="Familiar meals">Sample weekly meal rotation</SectionTitle>
      <p className="mb-4 text-sm text-gray-600">Use verified ingredients throughout. Make flatbread from flour or masa, water, oil, and salt. Use small packages or serve the full package at a meal when refrigeration is unavailable.</p>
      <div className="space-y-3">{rotation.map(([day, breakfast, lunch, dinner]) => <article key={day} className="rounded-xl border border-gray-200 p-4"><h3 className="font-bold text-indigo-800">{day}</h3><dl className="mt-2 grid gap-2 text-sm sm:grid-cols-3"><Meal label="Breakfast" value={breakfast}/><Meal label="Lunch" value={lunch}/><Meal label="Dinner" value={dinner}/></dl></article>)}</div>
      <p className="mt-4 text-sm leading-6 text-gray-600">Use nuts, dried fruit, crackers, or canned fruit for snacks and add oil, rice, beans, or peanut butter to meals as needed to meet portions. Repeat with substitutions the family already eats. Without safe cooking, use the no-cook bin: peanut butter and crackers with fruit for breakfast, fish and crackers at lunch, and ready-to-eat canned beans and vegetables at dinner, with nuts and dried fruit to fill out portions.</p>
    </Card>

    <Card><SectionTitle icon={Droplet} eyebrow="Stored water + replenishment">Water milestones</SectionTitle>
      <p className="mb-4 text-sm leading-6 text-gray-600">Use <strong>1 gallon per person per day</strong> as a starting allowance for drinking, food preparation, and basic hygiene. For four people, that is <strong>4 gallons daily</strong>. Allow extra for hot weather, pets, illness, and meals using a lot of water. <SourceLink href="https://www.cdc.gov/water-emergency/about/how-to-create-and-store-an-emergency-water-supply.html">CDC emergency water supply guidance</SourceLink></p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{waterMilestones.map(([coverage, gallons, plan]) => <div key={coverage} className="rounded-xl bg-sky-50 p-4"><p className="text-sm font-semibold text-sky-900">{coverage}</p><p className="text-2xl font-bold text-sky-950">{gallons}</p><p className="mt-1 text-sm leading-5 text-gray-700">{plan}</p></div>)}</div>
      <div className="mt-4 space-y-3 text-sm leading-6 text-gray-700">{checklist.slice(3, 6).map(([id, text]) => <Check key={id} id={id} checked={checked.has(id)} onChange={toggle}>{text}{id === 'water-sources' && <> <SourceLink href="https://www.celina-tx.gov/notifyme">City of Celina notifications</SourceLink></>}{id === 'water-treat' && <> <SourceLink href="https://www.cdc.gov/water-emergency/about/">CDC emergency water treatment guidance</SourceLink></>}</Check>)}</div>
    </Card>

    <Card><SectionTitle icon={ShieldCheck} eyebrow="Protect the food + household">Storage and cooking safety</SectionTitle>
      <div className="space-y-3 text-sm leading-6 text-gray-700">{checklist.slice(6, 11).map(([id, text]) => <Check key={id} id={id} checked={checked.has(id)} onChange={toggle}>{text}{id === 'safety-storage' && <> <SourceLink href="https://ask.fsis.usda.gov/article/Will-commercially-canned-foods-last-forever">USDA canned food storage guidance</SourceLink></>}{id === 'safety-outage' && <> <SourceLink href="https://www.foodsafety.gov/food-safety-charts/food-safety-during-power-outage">FoodSafety.gov outage chart</SourceLink></>}{id === 'safety-cooking' && <> <SourceLink href="https://www.cdc.gov/winter-weather/safety/stay-safe-during-after-a-winter-storm-safety.html">CDC winter storm safety guidance</SourceLink></>}</Check>)}</div>
    </Card>

    <Card><SectionTitle icon={Sprout} eyebrow="Cumulative build · 8,000 kcal/day">Four phases to 90 days</SectionTitle>
      <p className="mb-4 text-sm text-gray-600">Targets are cumulative; food and calorie quantities are estimates to confirm against package labels.</p>
      <div className="space-y-3">{stages.map(([id, stage, total, action]) => <Check key={id} id={id} checked={checked.has(id)} onChange={toggle} className="rounded-xl border border-gray-200 p-4"><div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"><strong className="text-gray-900">{stage}</strong><strong className="text-indigo-800">{total}</strong></div><p className="mt-2 text-sm leading-6 text-gray-600">{action}</p></Check>)}</div>
      <div className="mt-4 space-y-3 text-sm leading-6 text-gray-700">{checklist.slice(11).map(([id, text]) => <Check key={id} id={id} checked={checked.has(id)} onChange={toggle}>{text}</Check>)}</div>
    </Card>

    <footer className="rounded-xl border border-gray-200 bg-white p-4 text-xs leading-5 text-gray-500">Planning estimates are not medical or food-safety advice. Adjust quantities and dietary choices to the household; follow local utility guidance and product instructions. Checklist progress is saved in this browser only.</footer>
  </div>;
}

function Meal({ label, value }) { return <div><dt className="font-semibold text-gray-500">{label}</dt><dd className="mt-0.5 text-gray-800">{value}</dd></div>; }
function SourceLink({ href, children }) { return <a className="font-medium text-indigo-700 underline decoration-indigo-300 underline-offset-2 hover:text-indigo-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600" href={href} target="_blank" rel="noreferrer">{children}</a>; }
