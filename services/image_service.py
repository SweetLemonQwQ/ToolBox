from pathlib import Path

from PIL import Image


def convert_image(image: Image.Image, input_path: str, output_path: str, out_format: str) -> str:
    source = Path(input_path)
    target_dir = Path(output_path) if output_path else source.parent
    target_path = target_dir / f"{source.stem}.{out_format}"

    image_to_save = image
    if image_to_save.format == 'PNG' and out_format in ('jpg', 'jpeg'):
        image_to_save = image_to_save.convert('RGB')

    save_kwargs = {}
    if out_format == 'ico':
        save_kwargs['format'] = 'ICO'

    image_to_save.save(str(target_path), **save_kwargs)
    return str(target_path)
