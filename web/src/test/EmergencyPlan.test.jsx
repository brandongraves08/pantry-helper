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

  it('preserves the approved calorie and water milestones and source caveats', () => {
    renderPlan();
    const text = document.body.textContent;
    for (const value of ['720,000 kcal', '771,500', 'About 96 household days', '112,000 kcal', '113,720 kcal', '240,000 kcal', '480,000 kcal', '165,000 kcal', '59,500 kcal', '64,000 kcal', '48,000 kcal', '60,000 kcal', '76,800 kcal', '63,600 kcal', '43,200 kcal', '20,800 kcal', '38,000 kcal', '33,000 kcal', '15,600 kcal', '15,120 kcal', '9,600 kcal', '17,280 kcal', '14,400 kcal', '19,200 kcal', '8,400 kcal', '16 jars', '12 gal', '28 gal', '56 gal', '120 gal', '240 gal', '360 gal']) {
      expect(text).toContain(value);
    }
    expect(text).toMatch(/estimat/i);
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
});
