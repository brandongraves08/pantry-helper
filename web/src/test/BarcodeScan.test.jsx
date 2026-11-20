import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BarcodeScan from '../pages/BarcodeScan';
import * as api from '../api/client';

vi.mock('../api/client', () => ({
  lookupBarcode: vi.fn(),
  linkBarcodeToItem: vi.fn(),
  addBarcodeToInventory: vi.fn(),
  createBarcodeLabel: vi.fn(),
}));

const createdLabel = {
  barcode: 'PH-0123456789abcdef0123456789abcdef',
  item_id: 'rice-id',
  item_name: 'White rice',
  package_description: '1 lb bag',
  quantity_estimate: 1,
  label_created_at: '2026-11-20T20:00:00Z',
};

describe('Barcode Scanner custom pantry labels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'print').mockImplementation(() => {});
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('creates a Code 128 label from the entered item and package count', async () => {
    const user = userEvent.setup();
    api.createBarcodeLabel.mockResolvedValue(createdLabel);
    render(<BarcodeScan />);

    await user.click(screen.getByRole('button', { name: /make a pantry label/i }));
    await user.type(screen.getByRole('textbox', { name: /item name/i }), 'White rice');
    await user.type(screen.getByRole('textbox', { name: /package description/i }), '1 lb bag');
    await user.clear(screen.getByRole('spinbutton', { name: /packages/i }));
    await user.type(screen.getByRole('spinbutton', { name: /packages/i }), '1');
    await user.click(screen.getByRole('button', { name: /^create label$/i }));

    await waitFor(() => expect(api.createBarcodeLabel).toHaveBeenCalledWith({
      product_name: 'White rice',
      package_description: '1 lb bag',
      quantity_estimate: 1,
    }));
    expect(await screen.findByRole('img', { name: /code 128 barcode/i })).toBeTruthy();
    expect(screen.getByText(createdLabel.barcode)).toBeTruthy();
    expect(screen.getByText('White rice')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: /print label/i }));
    expect(window.print).toHaveBeenCalledOnce();
  });

  it('shows API failures without hiding the label form', async () => {
    const user = userEvent.setup();
    api.createBarcodeLabel.mockRejectedValue({ response: { data: { detail: 'Could not save pantry label' } } });
    render(<BarcodeScan />);

    await user.click(screen.getByRole('button', { name: /make a pantry label/i }));
    await user.type(screen.getByRole('textbox', { name: /item name/i }), 'White rice');
    await user.click(screen.getByRole('button', { name: /^create label$/i }));

    expect(await screen.findByText('Could not save pantry label')).toBeTruthy();
    expect(screen.getByRole('textbox', { name: /item name/i })).toBeTruthy();
  });

  it('keeps existing manual barcode lookup working', async () => {
    const user = userEvent.setup();
    api.lookupBarcode.mockResolvedValue({ barcode: '12345678', found: false });
    render(<BarcodeScan />);

    await user.type(screen.getByPlaceholderText('Enter barcode number...'), '12345678');
    await user.click(screen.getByRole('button', { name: /look up/i }));

    await waitFor(() => expect(api.lookupBarcode).toHaveBeenCalledWith('12345678'));
    expect(await screen.findByText(/barcode not found/i)).toBeTruthy();
  });
});
