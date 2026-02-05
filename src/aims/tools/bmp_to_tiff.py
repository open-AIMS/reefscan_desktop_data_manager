import os

from PIL import Image


def bmp_to_tiff(bmp_file, output_path):
    # Open the BMP image
    img = Image.open(bmp_file)
    base_filename = os.path.splitext(os.path.basename(bmp_file))[0]
    tiff_filename = output_path + "/" + base_filename + ".tif"

    # Convert to RGB mode if necessary (TIFF generally works well with RGB)
    # Some BMPs might be grayscale or indexed, converting to RGB ensures compatibility
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Save as TIFF with LZW compression (a common lossless compression for TIFF)
    # Other compression options like 'packbits' or 'tiff_deflate' can also be used.
    img.save(tiff_filename, format='TIFF', compression='tiff_lzw')

