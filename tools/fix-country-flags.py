from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
flags = root / 'gfx/flags'
count = 0
for source in sorted((flags / 'source').glob('koch_B*.png')):
    tag = source.stem.removeprefix('koch_')
    image = Image.open(source).convert('RGBA')
    image.putalpha(255)
    for folder, size in [('', (82,52)), ('medium', (41,26)), ('small', (10,7))]:
        resized = image.resize(size, Image.Resampling.LANCZOS)
        for suffix in ('', '_democratic', '_fascism', '_communism', '_neutrality'):
            path = flags / folder / f'{tag}{suffix}.tga'
            resized.save(path, compression=None)
            data = path.read_bytes()
            assert data[2] == 2 and data[16] == 32, path
            check = Image.open(path)
            check.load()
            assert check.size == size and check.mode == 'RGBA', path
            count += 1
    print(tag, 'all sizes and ideology variants verified')
print(count, 'uncompressed 32-bit flags verified')
