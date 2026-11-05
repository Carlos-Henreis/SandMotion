"""Generate a transparent example PNG for SandMotion."""
from pathlib import Path
from PIL import Image, ImageDraw

target = Path(__file__).with_name("demo.png")
image = Image.new("RGBA", (480, 480), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.ellipse((35, 35, 445, 445), fill=(255, 194, 48, 255))
draw.ellipse((135, 150, 175, 190), fill=(28, 28, 40, 255))
draw.ellipse((305, 150, 345, 190), fill=(28, 28, 40, 255))
draw.arc((125, 140, 355, 355), 15, 165, fill=(28, 28, 40, 255), width=18)
image.save(target)
print(target)
