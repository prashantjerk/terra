import { fireEvent, render, screen } from "@testing-library/react";
import SavedPhotos from "./SavedPhotos";

test("checks the selected photo and clears its result when switching photos", async () => {
  global.fetch = jest.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ["one.jpg", "two.jpg"] })
    .mockResolvedValueOnce({ ok: true, json: async () => ({
      photo: "two.jpg", checkedAt: "2026-11-16T19:00:00Z", capacity: 9,
      occupied: 8, available: 1, spaces: { P06: "available" }, previewJpeg: "abc",
    }) });
  render(<SavedPhotos apiBase="http://localhost:8080" />);
  await screen.findByRole("option", { name: "two.jpg" });
  const select = screen.getByLabelText("Parking photo");
  fireEvent.change(select, { target: { value: "two.jpg" } });
  fireEvent.click(screen.getByRole("button", { name: "Check photo" }));
  expect(await screen.findByText("P06: available")).toBeInTheDocument();
  expect(fetch).toHaveBeenLastCalledWith("http://localhost:8080/api/v1/parking/photos/check",
    expect.objectContaining({ method: "POST", body: '{"photo":"two.jpg"}' }));
  fireEvent.change(select, { target: { value: "one.jpg" } });
  expect(screen.queryByText("P06: available")).not.toBeInTheDocument();
});
