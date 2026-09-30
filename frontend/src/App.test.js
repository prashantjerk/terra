import { render, screen, waitFor, within } from '@testing-library/react';
import App from './App';

beforeEach(() => { window.history.replaceState({}, '', '/'); global.fetch = jest.fn(); });
afterEach(() => { jest.restoreAllMocks(); });

test('shows count and capacity minus count', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ timeStamp: '2026-09-29T20:00:00', numOfCarsParked: 7 }) });
  render(<App />);
  await waitFor(() => expect(screen.getByText('7')).toBeInTheDocument());
  expect(screen.getByText('11')).toBeInTheDocument();
  expect(screen.getByText('4')).toBeInTheDocument();
});
test('does not fabricate vacancies or a timestamp before the first update', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ timeStamp: null, numOfCarsParked: null }) });
  render(<App />);
  await screen.findByText('Last sensor update: N/A');
  expect(screen.getAllByText('—')).toHaveLength(2);
});
test('shows the saved demo photo and refreshes its URL with the timestamp', async () => {
  window.history.replaceState({}, '', '/?demo=14_58_01');
  const stamp = '2026-09-29T20:00:00';
  fetch.mockResolvedValue({ ok: true, json: async () => ({ timeStamp: stamp, numOfCarsParked: 11 }) });
  render(<App />);
  await waitFor(() => expect(screen.getByAltText('Parking lot used for the 14:58:01 saved-photo demo').src).toContain(encodeURIComponent(stamp)));
  expect(screen.getByText(/Saved image, not a live camera feed/)).toBeInTheDocument();
  expect(within(screen.getByText('Available').closest('.stat-card')).getByText('0')).toBeInTheDocument();
});
