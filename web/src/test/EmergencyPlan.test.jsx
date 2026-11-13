import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

const STORAGE_KEY = 'pantry-helper-emergency-plan-v1';

function renderPlan() {
  window.history.replaceState({}, '', '/emergency-plan');
  return render(<MemoryRouter initialEntries={['/emergency-plan']}><App /></MemoryRouter>);
}

describe('Emergency Plan', () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it('shows the separate emergency plan with all checklist items initially unchecked and without inventory writes', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    renderPlan();
    expect(screen.getByRole('heading', { name: /90-day emergency food supply plan/i })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Emergency Plan' }).getAttribute('href')).toBe('/emergency-plan');
    const boxes = screen.getAllByRole('checkbox');
    expect(boxes.length).toBeGreaterThan(10);
    expect(boxes.every((box) => !box.checked)).toBe(true);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem(STORAGE_KEY)).toBe('[]');
    expect(Object.keys(localStorage)).toEqual([STORAGE_KEY]);
  });

  it('keeps the desktop navigation and page in a horizontal app layout', () => {
    renderPlan();
    const root = screen.getByRole('main').parentElement.parentElement;
    expect(root.className.split(/\s+/)).toContain('lg:flex');
  });

  it('persists a selected checklist item across a page reload', async () => {
    const user = userEvent.setup();
    const { unmount } = renderPlan();
    const target = screen.getByRole('checkbox', { name: /long-grain white rice or basmati/i });
    await user.click(target);
    expect(target.checked).toBe(true);
    expect(screen.getByText('Checklist progress').parentElement.textContent).toContain('1 item complete');
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    expect(saved).toContain('food-rice');
    unmount();
    renderPlan();
    expect(screen.getByRole('checkbox', { name: /long-grain white rice or basmati/i }).checked).toBe(true);
    expect(screen.getAllByRole('checkbox').filter((box) => box.checked)).toHaveLength(1);
  });

  it('falls back to unchecked when saved JSON is malformed', () => {
    localStorage.setItem(STORAGE_KEY, '{bad json');
    renderPlan();
    expect(screen.getAllByRole('checkbox').every((box) => !box.checked)).toBe(true);
  });

  it('ignores stale and unknown saved checkbox IDs', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(['food-rice', 'unknown-id', null]));
    renderPlan();
    expect(screen.getByRole('checkbox', { name: /long-grain white rice or basmati/i }).checked).toBe(true);
    expect(screen.getAllByRole('checkbox').filter((box) => box.checked)).toHaveLength(1);
  });

  it('preserves dietary exclusions in assumptions without reintroducing excluded foods in the meal rotation', () => {
    renderPlan();
    const assumptions = screen.getByRole('heading', { name: /planning assumptions & dietary exclusions/i }).closest('section').textContent.toLowerCase();
    const rotation = screen.getByRole('heading', { name: /sample weekly meal rotation/i }).closest('section').textContent.toLowerCase();
    for (const excluded of ['lentils', 'jasmine rice', 'chicken', 'turkey', 'milk-free', 'egg-free']) expect(assumptions).toContain(excluded);
    for (const excluded of ['lentils', 'jasmine rice', 'chicken', 'turkey']) expect(rotation).not.toContain(excluded);
  });

  it('renders the household planning basis and estimated 90-day target', () => {
    renderPlan();
    const text = document.body.textContent;
    expect(text).toContain('Family of four');
    expect(text).toContain('360 person-days');
    expect(text).toContain('2,000 calories per person per day');
    expect(text).toContain('8,000 calories per household day');
    expect(text).toContain('90 days');
    expect(text).toContain('720,000 calories for 90 days');
    expect(text).toContain('720,000 kcal');
    expect(text).toContain('771,500 kcal');
    expect(text).toContain('About 96 household days');
    for (const calories of ['165,000 kcal', '59,500 kcal', '64,000 kcal', '48,000 kcal', '60,000 kcal', '76,800 kcal', '63,600 kcal', '43,200 kcal', '20,800 kcal', '38,000 kcal', '33,000 kcal', '15,600 kcal', '15,120 kcal', '9,600 kcal', '17,280 kcal', '14,400 kcal', '19,200 kcal', '8,400 kcal']) expect(text).toContain(calories);
  });

  it('renders the complete 14-day no-cook allocation and both target and estimate', () => {
    renderPlan();
    const reserve = screen.getByText(/Set aside 112,000 kcal/i).closest('label').textContent;
    for (const item of [
      '16 jars peanut butter', '11 lb crackers', '8 lb nuts or seeds', '6 lb dried fruit',
      '30 cans beans', '24 cans fish', '20 cans fruit', '20 cans vegetables',
    ]) expect(reserve).toContain(item);
    expect(reserve).toContain('112,000 kcal');
    expect(reserve).toContain('113,720 kcal');
    expect(reserve).toContain('14 household-day portions');
  });

  it('renders all cumulative phase labels and their exact totals', () => {
    renderPlan();
    const phases = screen.getByRole('heading', { name: /four phases to 90 days/i }).closest('section').textContent;
    for (const [label, total] of [
      ['1 · 14 days', '112,000 kcal'], ['2 · 30 days', '240,000 kcal'],
      ['3 · 60 days', '480,000 kcal'], ['4 · 90 days', '720,000 kcal'],
    ]) {
      expect(phases).toContain(label);
      expect(phases).toContain(total);
    }
    expect(phases).toMatch(/Targets are cumulative/i);
  });

  it('distinguishes the stored-water reserve from ongoing replenishment', () => {
    renderPlan();
    const water = screen.getByRole('heading', { name: /water milestones/i }).closest('section').textContent;
    for (const [coverage, gallons] of [['3 days', '12 gal'], ['7 days', '28 gal'], ['14 days', '56 gal'], ['30 days', '120 gal'], ['60 days', '240 gal'], ['90 days', '360 gal']]) {
      expect(water).toContain(coverage);
      expect(water).toContain(gallons);
    }
    expect(water).toContain('initial stored-water target');
    expect(water).toContain('Add 28 gal');
    expect(water).toContain('another 64 gal beyond the 14-day reserve');
    expect(water).toContain('184 gal beyond the reserve');
    expect(water).toContain('304 gal beyond the reserve');
    expect(water).toContain('Storing all 360 gal would weigh about 3,000 lb');
    expect(screen.getByText(/14 days · replenish separately/i)).toBeTruthy();
  });

  it('renders dietary assumptions, allergy and cross-contact guidance, and source citations', () => {
    renderPlan();
    const assumptions = screen.getByRole('heading', { name: /planning assumptions & dietary exclusions/i }).closest('section').textContent;
    for (const phrase of ['milk-free and egg-free', 'Exclude lentils and jasmine rice', 'avoid chicken and turkey', 'roughly 70% familiar foods', '30% dedicated reserve', 'two-week reserve', 'first three days requiring minimal prep water']) expect(assumptions).toContain(phrase);
    const labels = screen.getByRole('link', { name: /fda allergen labeling guidance/i }).closest('label').textContent;
    for (const phrase of ['whey', 'casein', 'albumen', 'allergen statements', 'manufacturer cross-contact guidance', 'clean prep surfaces and utensils']) expect(labels).toContain(phrase);
    const citationUrls = [
      'https://www.fda.gov/food/food-allergensgluten-free-guidance-documents-regulatory-information/frequently-asked-questions-food-allergen-labeling-guidance-industry',
      'https://www.cdc.gov/water-emergency/about/how-to-create-and-store-an-emergency-water-supply.html',
      'https://www.celina-tx.gov/notifyme',
      'https://www.cdc.gov/water-emergency/about/',
      'https://ask.fsis.usda.gov/article/Will-commercially-canned-foods-last-forever',
      'https://www.foodsafety.gov/food-safety-charts/food-safety-during-power-outage',
      'https://www.cdc.gov/winter-weather/safety/stay-safe-during-after-a-winter-storm-safety.html',
    ];
    const renderedLinks = [...document.querySelectorAll('a')].map((link) => link.href);
    for (const url of citationUrls) expect(renderedLinks).toContain(url);
  });

  it('renders water storage, refill and treatment instructions', () => {
    renderPlan();
    const water = screen.getByRole('heading', { name: /water milestones/i }).closest('section').textContent;
    for (const phrase of ['1 gallon per person per day', '4 gallons daily', 'sanitized food-grade containers', 'tight lids', 'replace every six months', 'away from heat, sunlight, and chemicals', 'primary refill source and a backup', 'fill and carry containers', 'water-provider alerts', 'Follow utility advisories', 'rolling boil for one minute in Celina', 'chemical contamination', 'printed treatment instructions']) expect(water).toContain(phrase);
  });

  it('renders food storage, outage and safe-cooking guidance', () => {
    renderPlan();
    const safety = screen.getByRole('heading', { name: /storage and cooking safety/i }).closest('section').textContent;
    for (const phrase of ['cool and dry', 'food-grade dry-good containers', 'first-in/first-out rotation', 'discard damaged cans', 'manual can opener', '40°F or below', 'four hours without power', 'Full freezer: about 48 hours', 'Never taste food', 'approved camp stove outdoors', 'Never use a stove, grill, or generator indoors', '20 feet from doors, windows, and vents', 'Test a week of cooking']) expect(safety).toContain(phrase);
  });
});
