from PIL import Image, ImageDraw




def mask_generate(size=300, output_filename="mask_300.png"):
	# Create a fully transparent image
	mask = Image.new("RGBA", (size, size), (0, 0, 0, 0))

	# Draw a solid white circle
	draw = ImageDraw.Draw(mask)
	draw.ellipse((0, 0, size, size), fill=(255, 255, 255, 255))

	# Save the image
	mask.save(output_filename)


if __name__ == '__main__':
	mask_generate()