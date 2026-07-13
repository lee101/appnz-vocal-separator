# appnz-vocal-separator

[![Deploy to app.nz](https://app.nz/deploy-button.svg)](https://app.nz/deploy?image=ghcr.io/lee101/appnz-vocal-separator:latest&name=vocal-separator&hardware=gpu-rtx3090)

A GPU-ready [Cog](https://github.com/replicate/cog) wrapper around
[Demucs](https://github.com/facebookresearch/demucs). It returns a ZIP with
either vocals + instrumental or the full drums/bass/vocals/other stem set. The
default `htdemucs` checkpoint is cached into the image for predictable cold
starts.

## Run on your own GPU

```bash
cog run -i audio=@song.wav -i stems=two -i format=mp3 -o stems.zip
cog run -i audio=@song.wav -i stems=four -i format=wav -o stems.zip
```

The CUDA 12.8 / PyTorch 2.7 build supports Ampere, Ada, and Blackwell. CPU is a
functional fallback but is much slower for full-length songs.

```bash
cog build -t appnz-vocal-separator
docker run --rm --gpus all -p 5000:5000 appnz-vocal-separator
```

## Scale-to-zero Cog + subdomain

```bash
app cogs deploy vocal-separator
app apps deploy demo --app stems-demo
app apps open stems-demo
```

This serves the static frontend at `https://stems-demo.app.nz` while the model
container scales independently. Change the demo manifest name for a custom
subdomain.

## Test

```bash
python -m unittest discover -s tests -v
python -m json.tool appnz.schema.json >/dev/null
```

The adapter and Demucs are MIT licensed. See [THIRD_PARTY.md](THIRD_PARTY.md)
for dependency and weight provenance.
