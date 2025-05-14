import qrcode

# Replace with your actual IP address
local_ip = "110.221.44.93"
url = f"http://{local_ip}:5500"

# Generate QR code
img = qrcode.make(url)
img.save("friday_qr.png")
print(f"✅ QR code saved as 'friday_qr.png' — scan it with your phone!")
