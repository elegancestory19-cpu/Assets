"""Cover-crop each image to 48.5x33 cm landscape at 300 dpi, convert to CMYK, assemble one PDF."""
import io, sys, os
from PIL import Image, ImageCms
U = '/root/.claude/uploads/4db11465-5abb-5bb8-b712-1f11bd4281a8/'
IMGS = ['0c9ab1b6-image.webp', '02380d43-image.webp', 'c9c6b591-image.webp', 'e3876d89-image.webp',
        '0f55ff1d-image.jpg', '1bcf94db-image.jpg', 'bddfb53c-image.jpg', 'b6eeebb3-image.jpg', '9827c52f-image.jpg',
        '30aa6ff2-image.jpg', 'cb6834a5-image.jpg', 'dc1caefc-image.jpg', 'ea6a9dfa-image.jpg']
DPI = 300
W, H = round(48.5 / 2.54 * DPI), round(33 / 2.54 * DPI)
srgb = ImageCms.createProfile('sRGB')
cmyk_path = '/usr/share/color/icc/ghostscript/default_cmyk.icc'
xf = ImageCms.buildTransform(srgb, cmyk_path, 'RGB', 'CMYK', renderingIntent=ImageCms.Intent.PERCEPTUAL)
icc = open(cmyk_path, 'rb').read()
pages = []
os.makedirs('pages', exist_ok=True)
for i, f in enumerate(IMGS, 1):
    im = Image.open(U + f).convert('RGB')
    s = max(W / im.width, H / im.height)
    nw, nh = round(im.width * s), round(im.height * s)
    im = im.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - W) // 2, (nh - H) // 2
    im = im.crop((l, t, l + W, t + H))
    c = ImageCms.applyTransform(im, xf)
    c.save(f'pages/{i:02d}.jpg', quality=95, dpi=(DPI, DPI), icc_profile=icc)
    eff = round(DPI / s)
    print(f'{i:02d} {f} src={Image.open(U+f).size} effective_dpi={eff}')
    pages.append(Image.open(f'pages/{i:02d}.jpg'))
pages[0].save('prints-48.5x33cm-CMYK.pdf', save_all=True, append_images=pages[1:], resolution=DPI)
print(W, H)
