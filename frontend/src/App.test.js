import { render, screen, waitFor, within, fireEvent, act } from '@testing-library/react';
import App from './App';

beforeEach(() => { window.history.replaceState({}, '', '/'); global.fetch = jest.fn(); });
afterEach(() => { jest.restoreAllMocks(); });

test('shows count and capacity minus count', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ timeStamp: '2026-09-29T20:00:00', numOfCarsParked: 7 }) });
  render(<App />);
  await waitFor(() => expect(screen.getByText('7')).toBeInTheDocument());
  expect(screen.getByText('12')).toBeInTheDocument();
  expect(screen.getByText('5')).toBeInTheDocument();
});
test('does not fabricate vacancies or a timestamp before the first update', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ timeStamp: null, numOfCarsParked: null }) });
  render(<App />);
  await screen.findByText('Last confirmed check: N/A');
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

test('requests detection on click without background polling', async () => {
 fetch.mockResolvedValue({ok:true,json:async()=>({timeStamp:null,numOfCarsParked:null})});
 render(<App />);
 const button=await screen.findByText('Refresh parking status');
 expect(fetch).toHaveBeenCalledTimes(1);
 fireEvent.click(button);
 await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(2));
 expect(fetch.mock.calls[1][0]).toMatch(/parking\/refresh$/);
 expect(fetch.mock.calls[1][1].method).toBe('POST');
});
test('rate limit retains previous count and disables refresh', async () => {
 fetch.mockResolvedValueOnce({ok:true,json:async()=>({timeStamp:'2026-10-12T20:00:00',numOfCarsParked:7})});
 render(<App />);
 const button=await screen.findByText('Refresh parking status');
 fetch.mockResolvedValueOnce({ok:false,status:429,headers:{get:()=> '60'}});
 fireEvent.click(button);
 await screen.findByText('Request limit reached. Try again in 60 seconds.');
 expect(screen.getByText('7')).toBeInTheDocument();
 expect(button).toBeDisabled();
});

test('does not poll after time passes and ignores repeated clicks during a request', async () => {
 jest.useFakeTimers();
 try {
  fetch.mockResolvedValueOnce({ok:true,json:async()=>({timeStamp:null,numOfCarsParked:null})});
  render(<App />);
  await act(async()=>{});
  act(()=>jest.advanceTimersByTime(10000));
  expect(fetch).toHaveBeenCalledTimes(1);
  let finish;
  fetch.mockImplementationOnce(()=>new Promise(resolve=>{finish=resolve;}));
  const button=screen.getByText('Refresh parking status');
  fireEvent.click(button);
  fireEvent.click(button);
  expect(button).toBeDisabled();
  expect(fetch).toHaveBeenCalledTimes(2);
  await act(async()=>finish({ok:true,json:async()=>({timeStamp:null,numOfCarsParked:2})}));
  expect(button).toBeEnabled();
 } finally { jest.useRealTimers(); }
});
