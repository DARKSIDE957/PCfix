from PIL import Image, ImageDraw, ImageFont

def create_icon():
    # Size for standard ICO
    size = (256, 256)
    
    # Create a dark background image (RGBA)
    image = Image.new("RGBA", size, (20, 20, 20, 255))
    draw = ImageDraw.Draw(image)
    
    # Draw a "Shield" shape or a border
    # Simple rounded rectangle border in blood red
    border_color = (180, 0, 0, 255) # Deep red
    draw.rounded_rectangle([(10, 10), (246, 246)], radius=40, outline=border_color, width=15)
    
    # Draw "PF" text in the center
    # Since we might not have a custom font, we'll draw simple block letters manually or use default
    # Let's draw a cross/plus sign for "Fix" in the background
    
    # Draw a stylized cross
    cross_color = (40, 40, 40, 255)
    center = 128
    width = 40
    length = 160
    # Vertical bar
    draw.rectangle([(center - width/2, center - length/2), (center + width/2, center + length/2)], fill=cross_color)
    # Horizontal bar
    draw.rectangle([(center - length/2, center - width/2), (center + length/2, center + width/2)], fill=cross_color)

    # Draw "PF" text (attempting simple vector drawing for robustness)
    text_color = (220, 220, 220, 255)
    
    # P
    draw.rectangle([(60, 70), (80, 190)], fill=text_color) # Vertical
    draw.rectangle([(60, 70), (120, 90)], fill=text_color) # Top
    draw.rectangle([(100, 70), (120, 130)], fill=text_color) # Right curve
    draw.rectangle([(60, 110), (120, 130)], fill=text_color) # Middle
    
    # F
    draw.rectangle([(140, 70), (160, 190)], fill=text_color) # Vertical
    draw.rectangle([(140, 70), (200, 90)], fill=text_color) # Top
    draw.rectangle([(140, 120), (190, 140)], fill=text_color) # Middle
    
    # Save as ICO
    image.save("icon.ico", format="ICO", sizes=[(256, 256)])
    print("Icon 'icon.ico' created successfully.")

if __name__ == "__main__":
    create_icon()
