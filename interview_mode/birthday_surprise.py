import os
import time
import random

# Function to clear terminal screen
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# Heart frames with 'Payal' in the center
heart_frames = [
    r"""
     **     **
   ****** ******  
  *************** 
  *****PAYAL***** 
   *************  
     *********    
       *****      
         *        
""",
    r"""
      **   **   
    ***********  
  **** PAYAL **** 
  *************** 
   *************  
    ***********   
      *******     
        ***       
         *        
""",
    r"""
     **     **    
   ***       ***  
  ***  *** ***  ***
  ***   PAYAL   ***
   ***   ***   ***
    ***       ***  
      ***   ***   
        *****     
          *       
"""
]

# Random firework spark generator
def generate_fireworks(width=40, height=10, count=25):
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    for _ in range(count):
        x = random.randint(0, height - 1)
        y = random.randint(0, width - 1)
        grid[x][y] = random.choice(['*', '+', '.', 'x', '✨', '🎇'])
    return "\n".join("".join(row) for row in grid)

# Birthday message box
def birthday_box(name: str, message: str) -> str:
    return f"""
╔══════════════════════════════════════════════╗
║            🎉 HAPPY BIRTHDAY 🎉              ║
╠══════════════════════════════════════════════╣
║ Dear {name},                                      ║
║                                                ║
║ {message}            ║
║                                                ║
║ May your heart always smile and your dreams  ║
║ come true today and always. ❤️               ║
╚══════════════════════════════════════════════╝
"""

# Typing animation
def type_out(text, delay=0.015):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

# Animate heart with name
def animate_heart(repeat=4, delay=0.3):
    for _ in range(repeat):
        for frame in heart_frames:
            clear()
            print(frame)
            time.sleep(delay)

# Fireworks then birthday message
def animate_fireworks_then_message(name, message):
    for _ in range(10):
        clear()
        print(generate_fireworks())
        time.sleep(0.2)
    clear()
    type_out(birthday_box(name, message))

# Customize below
wife_name = "Payal"
custom_message = "You're my heartbeat, my everything. Happy Birthday! 💖"

# Run the show
if __name__ == "__main__":
    animate_heart()
    animate_fireworks_then_message(wife_name, custom_message)
