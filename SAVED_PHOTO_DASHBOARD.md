# Saved photos in the Terra dashboard

The Pi runs the same nine-space check as the batch command. Put only photos
with the same framing as image2.jpg into the folder served by the Pi.
Keep the live detector separate (port 8090). This service uses port 8091.

## Pi terminal

```bash
cd ~/terra
git switch feature/yolo-roi
git pull --ff-only origin feature/yolo-roi
cd computer-vision
read -rsp 'Shared Terra token: ' TERRA_PI_TOKEN; echo
export TERRA_PI_TOKEN
.venv-photos/bin/python src/photo_server.py --host 127.0.0.1 \
  --photos-dir "$HOME/terra-photos/terraPhotos"
```

Enter the same token as the laptop backend's existing `TERRA_PI_TOKEN`.
Keep the terminal open. The server uses the existing ONNX model and
`roi.straight-9.json`.

## Windows PowerShell

Leave this SSH tunnel running in its own window. If the Pi IP has changed,
replace it with the current address from `hostname -I` on the Pi.

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8091:127.0.0.1:8091 karkip685@10.200.69.79
```

Pull the branch in the repository on Windows. Add
`TERRA_PHOTO_PI_URL=http://127.0.0.1:8091` to the backend's existing
`terra-backend/.env`. Start PostgreSQL as usual. With Java 25 selected,
rebuild and restart the backend:

```powershell
cd "$HOME\Desktop\codish\terra"
git switch feature/yolo-roi
git pull --ff-only origin feature/yolo-roi
cd terra-backend
.\mvnw.cmd clean package
.\run-backend.ps1
```

In another window, run `npm start` from the existing frontend folder
(run `npm ci` first if dependencies aren't installed).
Open http://localhost:3000/?mode=photos, pick an image, and click **Check photo**.

Each successful request inserts one row into PostgreSQL. The preview is
returned to the dashboard for that check; it is not saved in the database.
The timestamp records analysis time, not when the photo was taken.

```sql
SELECT photo_id, checked_at, capacity, occupied,
       capacity - occupied AS available, occupied_spaces
FROM parking_photo_results
ORDER BY id DESC;
```
