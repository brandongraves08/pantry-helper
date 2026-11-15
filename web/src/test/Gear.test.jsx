import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';
import * as api from '../api/client';

vi.mock('../api/client', () => ({
  listInventory: vi.fn(),
  listGear: vi.fn(),
  createGear: vi.fn(),
  updateGear: vi.fn(),
  deleteGear: vi.fn(),
}));

const stove = { id: 'g1', name: 'Camp stove', category: 'Stove', quantity: 1, unit: 'stove', location: 'Truck bin', condition: 'Good', notes: '' };
function renderGear() {
  return render(<MemoryRouter initialEntries={['/gear']}><App /></MemoryRouter>);
}

describe('Prepping Gear', () => {
  beforeEach(() => {
    api.listGear.mockResolvedValue({ items: [stove], total: 1 });
    api.createGear.mockImplementation(async (payload) => ({ ...payload, id: 'g2' }));
    api.updateGear.mockImplementation(async (id, payload) => ({ ...stove, ...payload, id }));
    api.deleteGear.mockResolvedValue();
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it('lists saved gear and exposes its dedicated navigation route', async () => {
    renderGear();
    expect(await screen.findByText('Camp stove')).toBeInTheDocument();
    expect(screen.getByText('Truck bin')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /prepping gear/i })).toHaveAttribute('href', '/gear');
  });

  it('labels the notes shown on a gear record', async () => {
    api.listGear.mockResolvedValue({ items: [{ ...stove, notes: 'Backpacking kit' }], total: 1 });
    renderGear();
    expect(await screen.findByText('Backpacking kit')).toBeInTheDocument();
    expect(screen.getByText('Notes:')).toBeInTheDocument();
  });

  it('keeps the rendered gear route limited to register actions, without excluded feature actions', async () => {
    renderGear();
    const gearScreen = screen.getByRole('region', { name: /prepping gear/i });
    expect(await within(gearScreen).findByRole('searchbox', { name: /search gear/i })).toBeInTheDocument();
    expect(within(gearScreen).getByRole('button', { name: /add gear/i })).toBeInTheDocument();
    expect(within(gearScreen).getByRole('button', { name: /edit camp stove/i })).toBeInTheDocument();
    expect(within(gearScreen).getByRole('button', { name: /delete camp stove/i })).toBeInTheDocument();

    const excludedActions = /power\s*\/\s*fuel calculations?|calculate (?:power|fuel)|maintenance reminders?|expiry reminders?|alerts?|barcode|image recognition/i;
    expect(within(gearScreen).queryByText(excludedActions)).not.toBeInTheDocument();
    expect(within(gearScreen).queryByRole('button', { name: excludedActions })).not.toBeInTheDocument();
    expect(within(gearScreen).queryByRole('link', { name: excludedActions })).not.toBeInTheDocument();
  });

  it('creates, edits, and deletes gear through the API', async () => {
    const user = userEvent.setup();
    api.listGear.mockResolvedValueOnce({ items: [], total: 0 }).mockResolvedValue({ items: [stove], total: 1 });
    renderGear();
    expect(await screen.findByText(/no gear added yet/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /add gear/i }));
    await user.type(screen.getByLabelText(/item name/i), 'Solar panel');
    await user.type(screen.getByLabelText(/category/i), 'Solar');
    const quantity = screen.getByLabelText(/quantity/i);
    await user.clear(quantity);
    await user.type(quantity, '2');
    await user.type(screen.getByLabelText(/unit/i), 'panels');
    await user.click(screen.getByRole('button', { name: /save gear/i }));
    await waitFor(() => expect(api.createGear).toHaveBeenCalledWith(expect.objectContaining({ name: 'Solar panel', category: 'Solar', quantity: 2, unit: 'panels' })));

    await screen.findByText('Camp stove');
    await user.click(screen.getByRole('button', { name: /edit camp stove/i }));
    await user.clear(screen.getByLabelText(/item name/i));
    await user.type(screen.getByLabelText(/item name/i), 'Two-burner camp stove');
    await user.click(screen.getByRole('button', { name: /save gear/i }));
    await waitFor(() => expect(api.updateGear).toHaveBeenCalledWith('g1', expect.objectContaining({ name: 'Two-burner camp stove' })));

    vi.spyOn(window, 'confirm').mockReturnValue(true);
    await user.click(screen.getByRole('button', { name: /delete camp stove/i }));
    await waitFor(() => expect(api.deleteGear).toHaveBeenCalledWith('g1'));
  });

  it('keeps gear CRUD isolated from food APIs and the browser-local emergency checklist', async () => {
    const user = userEvent.setup();
    const checklistKey = 'pantry-helper-emergency-plan-v1';
    window.localStorage.setItem(checklistKey, JSON.stringify(['task-labels']));
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    const removeItem = vi.spyOn(Storage.prototype, 'removeItem');
    const checklistBefore = window.localStorage.getItem(checklistKey);

    api.listGear.mockResolvedValueOnce({ items: [], total: 0 }).mockResolvedValue({ items: [stove], total: 1 });
    renderGear();
    await screen.findByText(/no gear added yet/i);
    await user.click(screen.getByRole('button', { name: /add gear/i }));
    await user.type(screen.getByLabelText(/item name/i), 'Solar panel');
    await user.type(screen.getByLabelText(/category/i), 'Solar');
    await user.click(screen.getByRole('button', { name: /save gear/i }));
    await waitFor(() => expect(api.createGear).toHaveBeenCalled());

    await screen.findByText('Camp stove');
    await user.click(screen.getByRole('button', { name: /edit camp stove/i }));
    await user.click(screen.getByRole('button', { name: /save gear/i }));
    await waitFor(() => expect(api.updateGear).toHaveBeenCalledWith('g1', expect.any(Object)));

    vi.spyOn(window, 'confirm').mockReturnValue(true);
    await user.click(screen.getByRole('button', { name: /delete camp stove/i }));
    await waitFor(() => expect(api.deleteGear).toHaveBeenCalledWith('g1'));

    expect(api.listInventory).not.toHaveBeenCalled();
    expect(setItem.mock.calls.filter(([key]) => key === checklistKey)).toEqual([]);
    expect(removeItem.mock.calls.filter(([key]) => key === checklistKey)).toEqual([]);
    expect(window.localStorage.getItem(checklistKey)).toBe(checklistBefore);
    setItem.mockRestore();
    removeItem.mockRestore();
    window.localStorage.removeItem(checklistKey);
  });

  it('filters saved gear by name, category, location, and notes', async () => {
    const user = userEvent.setup();
    api.listGear.mockResolvedValue({ items: [stove, { ...stove, id: 'g2', name: 'Solar panel', category: 'Solar', location: 'Shed', notes: 'Backup supplies' }], total: 2 });
    renderGear();
    expect(await screen.findByText('Camp stove')).toBeInTheDocument();
    const search = screen.getByRole('searchbox', { name: /search gear/i });
    await user.type(search, 'Shed');
    expect(screen.getByText('Solar panel')).toBeInTheDocument();
    expect(screen.queryByText('Camp stove')).not.toBeInTheDocument();
    await user.clear(search);
    await user.type(search, 'Solar');
    expect(screen.getByText('Solar panel')).toBeInTheDocument();
    expect(screen.queryByText('Camp stove')).not.toBeInTheDocument();
    await user.clear(search);
    await user.type(search, 'Camp stove');
    expect(screen.getByText('Camp stove')).toBeInTheDocument();
    expect(screen.queryByText('Solar panel')).not.toBeInTheDocument();
    await user.clear(search);
    await user.type(search, 'Backup supplies');
    expect(screen.getByText('Solar panel')).toBeInTheDocument();
    await user.clear(search);
    await user.type(search, 'unmatched');
    expect(screen.getByText(/no matching gear/i)).toBeInTheDocument();
  });

  it('moves focus into the form and restores it to the opening control when closed', async () => {
    const user = userEvent.setup();
    renderGear();
    const addButton = await screen.findByRole('button', { name: /add gear/i });
    await user.click(addButton);
    expect(screen.getByLabelText(/item name/i)).toHaveFocus();
    await user.click(screen.getByRole('button', { name: /close gear form/i }));
    expect(addButton).toHaveFocus();

    const editButton = screen.getByRole('button', { name: /edit camp stove/i });
    await user.click(editButton);
    expect(screen.getByLabelText(/item name/i)).toHaveFocus();
    await user.click(screen.getByRole('button', { name: /cancel/i }));
    expect(editButton).toHaveFocus();
  });

  it('shows an error when a gear save fails', async () => {
    const user = userEvent.setup();
    api.createGear.mockRejectedValueOnce(new Error('offline'));
    renderGear();
    await screen.findByText('Camp stove');
    await user.click(screen.getByRole('button', { name: /add gear/i }));
    await user.type(screen.getByLabelText(/item name/i), 'Solar panel');
    await user.type(screen.getByLabelText(/category/i), 'Solar');
    await user.click(screen.getByRole('button', { name: /save gear/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't save gear/i);
  });

  it('validates a required name and reports load errors with retry', async () => {
    const user = userEvent.setup();
    api.listGear.mockRejectedValueOnce(new Error('offline')).mockResolvedValue({ items: [], total: 0 });
    renderGear();
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't load gear/i);
    await user.click(screen.getByRole('button', { name: /retry/i }));
    expect(await screen.findByText(/no gear added yet/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /add gear/i }));
    await user.click(screen.getByRole('button', { name: /save gear/i }));
    expect(screen.getByLabelText(/item name/i)).toBeRequired();
    expect(api.createGear).not.toHaveBeenCalled();
  });
});
