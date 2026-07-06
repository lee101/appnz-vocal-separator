# appnz-vocal-separator

[![Deploy to app.nz](https://app.nz/deploy-button.svg)](https://app.nz/deploy?image=ghcr.io/lee101/appnz-vocal-separator:latest&name=vocal-separator&vram=8)

Music source separation with [Demucs](https://github.com/facebookresearch/demucs)
(htdemucs) packaged as an [app.nz cog](https://app.nz): a tiny HTTP contract on
port 5000 with `POST /predictions` in and MP3 stems out as data URIs. Runs on
CPU; automatically uses CUDA when a GPU is present. Model weights are baked
into the image so cold starts are fast.

## Inputs

| name | type | notes |
|---|---|---|
| `audio` | audio | https URL or `data:` URI of the track |
| `stems` | enum | `two` (default) = vocals + instrumental, `four` = vocals/drums/bass/other |

Output: JSON dict of stem name to `data:audio/mpeg;base64,...` MP3.

## Run locally

```bash
docker run -p 5000:5000 ghcr.io/lee101/appnz-vocal-separator:latest

curl -s http://localhost:5000/health-check

curl -s http://localhost:5000/predictions -X POST \
  -H 'Content-Type: application/json' \
  -d '{"input": {"audio": "https://example.com/song.mp3", "stems": "two"}}'

curl -s http://localhost:5000/predictions -X POST \
  -H 'Content-Type: application/json' \
  -d '{"input": {"audio": "https://example.com/song.mp3", "stems": "four"}}' \
  | python3 -c 'import sys,json,base64; o=json.load(sys.stdin)["output"]; [open(k+".mp3","wb").write(base64.b64decode(v.split(",",1)[1])) for k,v in o.items()]'
```

## One-click deploy on app.nz

Click the badge above, or open
`https://app.nz/deploy?image=ghcr.io/lee101/appnz-vocal-separator:latest&name=vocal-separator&vram=8`.

## Build

```bash
docker build -t ghcr.io/lee101/appnz-vocal-separator:latest .
```

GitHub Actions builds and pushes `ghcr.io/lee101/appnz-vocal-separator:latest`
on every push to `main`.

## License

MIT
