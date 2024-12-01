import cv2
import numpy as np
import random
import winsound  # For sound effects (Windows only)
import time  # For tracking elapsed time

# Load Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize video capture
cap = cv2.VideoCapture(0)

# Game settings
screen_width, screen_height = 640, 480
catcher_width = 100
catcher_height = 20
catcher_x = screen_width // 2
score = 0
high_score = 0
falling_objects = []
particles = []
falling_object_types = ['catch', 'lose']  # Types of falling objects
initial_speed = 5  # Initial falling speed
max_speed = 20  # Maximum falling speed
game_duration = 25  # Time limit in seconds
minimum_spawn_distance = 50  # Minimum distance between falling objects
safe_zone = 30  # Prevent objects spawning too far left or right


# Function to create a new falling object
def create_falling_object(speed):
    while True:
        x = random.randint(safe_zone, screen_width - safe_zone - 20)  # Random x-position within safe zone
        object_type = random.choice(falling_object_types)
        size = random.randint(10, 30)  # Random size for variety

        # Ensure no overlap with existing objects
        if all(abs(x - obj[0]) > minimum_spawn_distance for obj in falling_objects):
            return [x, 0, object_type, size, speed]  # Valid position found


# Function to draw the catcher as a rectangle
def draw_catcher(frame, x, y, width, height, color=(255, 255, 255)):
    cv2.rectangle(frame, (x, y), (x + width, y + height), color, -1)


# Function to reset the game
def reset_game():
    global score, falling_objects, start_time
    score = 0
    falling_objects.clear()
    falling_objects.append(create_falling_object(initial_speed))
    start_time = time.time()


# Add the first falling object
falling_objects.append(create_falling_object(initial_speed))

# Reset the game to start
reset_game()

# Game loop
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally to correct mirroring
    frame = cv2.flip(frame, 1)

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    # Position the catcher based on detected face
    for (x, y, w, h) in faces:
        catcher_x = (x + w // 2) - (catcher_width // 2)
        catcher_x = max(0, min(screen_width - catcher_width, catcher_x))  # Keep catcher within screen bounds

    # Draw the catcher
    draw_catcher(frame, catcher_x, screen_height - catcher_height, catcher_width, catcher_height, color=(0, 255, 0))

    # Calculate elapsed time and time remaining
    elapsed_time = time.time() - start_time
    time_remaining = max(0, game_duration - int(elapsed_time))

    # Stop the game when time runs out
    if time_remaining == 0:
        high_score = max(high_score, score)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (screen_width, screen_height), (0, 0, 0), -1)  # Full-screen black overlay
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)  # Combine overlay and original frame

        # Display Game Over text
        cv2.putText(frame, 'GAME OVER', (screen_width // 6, screen_height // 3), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4, cv2.LINE_AA)
        cv2.putText(frame, f'Score: {score}', (screen_width // 4, screen_height // 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, f'High Score: {high_score}', (screen_width // 4 - 40, screen_height // 2 + 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, 'Press R to Replay or Q to Quit', (screen_width // 8, screen_height // 2 + 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Show the game over screen
        cv2.imshow('Face-Catcher Game', frame)
        key = cv2.waitKey(0)
        if key == ord('r'):
            reset_game()
        elif key == ord('q'):
            break
        continue

    # Gradually increase the falling speed
    current_speed = min(initial_speed + int(elapsed_time // 5), max_speed)

    # Update falling objects
    for obj in falling_objects[:]:
        obj[1] += current_speed  # Update position based on current speed

        # Check for collision with the catcher
        if obj[1] >= screen_height - catcher_height and catcher_x < obj[0] < catcher_x + catcher_width:
            if obj[2] == 'catch':
                score += 1  # Increase score
                winsound.Beep(1000, 200)  # Sound effect for catching
                for _ in range(10):  # Create particles
                    particles.append({
                        'x': obj[0] + 10,
                        'y': obj[1],
                        'dx': random.uniform(-3, 3),
                        'dy': random.uniform(-3, 3),
                        'lifetime': 20
                    })
            elif obj[2] == 'lose':
                score -= 1  # Decrease score
                winsound.Beep(500, 200)  # Sound effect for losing points
            falling_objects.remove(obj)
            falling_objects.append(create_falling_object(current_speed))  # Add a new object

        # Remove objects that have fallen below the screen
        elif obj[1] > screen_height:
            falling_objects.remove(obj)
            falling_objects.append(create_falling_object(current_speed))

    # Add new objects as time progresses
    if len(falling_objects) < 5 + (elapsed_time // 5):
        falling_objects.append(create_falling_object(current_speed))

    # Draw falling objects
    for obj in falling_objects:
        color = (0, 255, 0) if obj[2] == 'catch' else (0, 0, 255)
        cv2.circle(frame, (obj[0] + 10, obj[1]), obj[3], color, -1)

    # Update and draw particles
    for particle in particles[:]:
        particle['x'] += particle['dx']
        particle['y'] += particle['dy']
        particle['lifetime'] -= 1
        if particle['lifetime'] <= 0:
            particles.remove(particle)
        else:
            cv2.circle(frame, (int(particle['x']), int(particle['y'])), 3, (0, 255, 255), -1)

    # Display the score and time remaining
    cv2.putText(frame, f'Score: {score}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f'Time: {time_remaining}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Show the resulting frame
    cv2.imshow('Face-Catcher Game', frame)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture
cap.release()
cv2.destroyAllWindows()
