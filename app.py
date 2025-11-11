import cv2
import mediapipe as mp
import numpy as np
import time
import webbrowser
import urllib.parse

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
WIDTH, HEIGHT = 1200, 800
FINGER_TIP_ID = 8

# Professional keyboard layout
keys = [
    ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Back"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
    ["Caps", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
    ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift"],
    ["Ctrl", "Win", "Alt", "Space", "Alt", "Menu", "Ctrl"]
]

shifted_keys = [
    ["~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "Back"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "{", "}", "|"],
    ["Caps", "A", "S", "D", "F", "G", "H", "J", "K", "L", ":", "\"", "Enter"],
    ["Shift", "Z", "X", "C", "V", "B", "N", "M", "<", ">", "?", "Shift"],
    ["Ctrl", "Win", "Alt", "Space", "Alt", "Menu", "Ctrl"]
]

def draw_keys(img, key_set, caps_lock=False, shift_active=False):
    key_coords = []
    x_start, y_start = 40, 250
    key_w, key_h = 65, 65
    offset = 6
    
    for row_idx, row in enumerate(key_set):
        total_row_width = len(row) * key_w + (len(row) - 1) * offset
        x_start_row = (WIDTH - total_row_width) // 2
        
        for col_idx, key in enumerate(row):
            x = x_start_row + col_idx * (key_w + offset)
            y = y_start + row_idx * (key_h + offset)
            
            # Adjust width for special keys
            w = key_w
            if key == "Back":
                w = key_w * 1.8
            elif key == "Tab":
                w = key_w * 1.5
            elif key == "Caps":
                w = key_w * 1.7
            elif key == "Enter":
                w = key_w * 1.8
            elif key == "Shift":
                w = key_w * 2.2
            elif key == "Space":
                w = key_w * 5
            elif key in ["Ctrl", "Win", "Alt", "Menu"]:
                w = key_w * 1.3
            elif key == "\\":
                w = key_w * 1.5
                
            key_text = key
            
            # Professional color scheme
            if key in ["Shift", "Caps", "Ctrl", "Alt", "Tab"]:
                color = (80, 120, 200)  # Blue for modifier keys
            elif key == "Space":
                color = (100, 180, 100)  # Green for space
            elif key == "Enter":
                color = (200, 100, 80)  # Orange for enter (search)
            elif key == "Back":
                color = (200, 80, 80)  # Red for backspace
            elif key in ["Win", "Menu"]:
                color = (150, 150, 150)  # Gray for Windows keys
            else:
                color = (60, 60, 70)  # Dark gray for regular keys
                
            # Highlight active modifier keys
            if (key == "Shift" and shift_active) or (key == "Caps" and caps_lock):
                color = (100, 160, 255)  # Bright blue for active modifiers
                
            cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + key_h)), color, -1)
            cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + key_h)), (40, 40, 40), 2)
            
            # Draw key text
            font_scale = 0.45 if len(key_text) <= 2 else 0.35
            text_size = cv2.getTextSize(key_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)[0]
            text_x = x + (w - text_size[0]) // 2
            text_y = y + (key_h + text_size[1]) // 2
            cv2.putText(img, key_text, (int(text_x), int(text_y)), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1)
            
            key_coords.append((key, x, y, w, key_h))
            
    return img, key_coords

def search_google(query):
    """Open Google search in default browser"""
    if query.strip():
        encoded_query = urllib.parse.quote_plus(query)
        google_url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(google_url)
        return True
    return False

def show_notification(img, message, duration=2.0):
    """Show temporary notification"""
    notification_bg = (50, 50, 70)
    text_color = (255, 255, 255)
    
    text_size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    text_x = (WIDTH - text_size[0]) // 2
    text_y = 220
    
    cv2.rectangle(img, (text_x - 20, text_y - 35), (text_x + text_size[0] + 20, text_y + 10), notification_bg, -1)
    cv2.rectangle(img, (text_x - 20, text_y - 35), (text_x + text_size[0] + 20, text_y + 10), (100, 100, 120), 2)
    cv2.putText(img, message, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
    
    return time.time() + duration

# Initialize variables
hover_start_time = None
last_key_hovered = None
output_text = ""
trigger_delay = 1.2  # Slightly longer for more precision
caps_lock = False
shift_active = False
last_cursor_time = time.time()
cursor_visible = True
current_key_set = keys
last_backspace_time = 0
backspace_initial_delay = 0.6
backspace_repeat_delay = 0.15
last_enter_time = 0
enter_initial_delay = 1.0
enter_repeat_delay = 0.3
notification_end_time = 0
search_initiated = False

cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

print("Professional Virtual Keyboard Started!")
print("Instructions:")
print("- Hover over keys for 1.2 seconds to type")
print("- Press Enter to search on Google")
print("- Press ESC to exit")

while True:
    success, img = cap.read()
    if not success:
        break
        
    img = cv2.flip(img, 1)
    # Professional dark theme background
    screen = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    screen[:] = (30, 30, 35)  # Dark gray background
    
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    
    # Draw keyboard
    screen, key_boxes = draw_keys(screen, current_key_set, caps_lock, shift_active)
    current_time = time.time()
    
    # Blinking cursor logic
    if current_time - last_cursor_time > 0.5:
        cursor_visible = not cursor_visible
        last_cursor_time = current_time
    
    # Hand detection and key interaction
    finger_position = None
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm_list = []
            for id, lm in enumerate(hand_landmarks.landmark):
                h, w, c = screen.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))

            if lm_list:
                x_tip, y_tip = lm_list[FINGER_TIP_ID][1], lm_list[FINGER_TIP_ID][2]
                finger_position = (x_tip, y_tip)
                cv2.circle(screen, (x_tip, y_tip), 10, (0, 255, 100), cv2.FILLED)
                cv2.circle(screen, (x_tip, y_tip), 12, (255, 255, 255), 2)
                
                hovered_key = None
                for key, x, y, w, h in key_boxes:
                    if x < x_tip < x + w and y < y_tip < y + h:
                        hovered_key = key
                        # Professional hover effect
                        cv2.rectangle(screen, (int(x), int(y)), (int(x + w), int(y + h)), (50, 150, 255), -1)
                        cv2.rectangle(screen, (int(x), int(y)), (int(x + w), int(y + h)), (255, 255, 255), 2)
                        
                        # Show hover time progress
                        if hovered_key == last_key_hovered and hover_start_time:
                            progress = min(1.0, (current_time - hover_start_time) / trigger_delay)
                            bar_width = int(w * progress)
                            cv2.rectangle(screen, (int(x), int(y - 8)), (int(x + bar_width), int(y - 3)), (0, 255, 0), -1)
                        
                        # Display key label above with better visibility
                        cv2.putText(screen, key, (int(x + (w - 30) // 2), int(y - 15)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                        break

                if hovered_key:
                    if hovered_key == last_key_hovered:
                        time_hovered = current_time - hover_start_time
                        
                        # Special handling for Backspace
                        if hovered_key == "Back":
                            if time_hovered > backspace_initial_delay:
                                if current_time - last_backspace_time > backspace_repeat_delay:
                                    output_text = output_text[:-1]
                                    last_backspace_time = current_time
                        
                        # Special handling for Enter (Google Search)
                        elif hovered_key == "Enter":
                            if time_hovered > enter_initial_delay:
                                if current_time - last_enter_time > enter_repeat_delay:
                                    if output_text.strip() and not search_initiated:
                                        # Perform Google search
                                        search_success = search_google(output_text)
                                        if search_success:
                                            notification_end_time = show_notification(screen, f"Searching: {output_text}")
                                            search_initiated = True
                                            # Optional: Clear text after search
                                            # output_text = ""
                                    last_enter_time = current_time
                        
                        elif time_hovered > trigger_delay:
                            if hovered_key == "Space":
                                output_text += " "
                            elif hovered_key == "Shift":
                                shift_active = not shift_active
                                current_key_set = shifted_keys if shift_active else keys
                            elif hovered_key == "Caps":
                                caps_lock = not caps_lock
                            elif hovered_key in ["Ctrl", "Alt", "Win", "Menu", "Tab"]:
                                # System keys - no text output
                                pass
                            elif hovered_key not in ["Enter", "Back", "Shift"]:
                                # Handle regular character keys
                                if caps_lock or shift_active:
                                    output_text += hovered_key
                                else:
                                    # Convert to lowercase for letters
                                    if hovered_key.isalpha() and len(hovered_key) == 1:
                                        output_text += hovered_key.lower()
                                    else:
                                        output_text += hovered_key
                                
                                # If shift was active (not caps lock), revert to normal
                                if shift_active and not caps_lock:
                                    shift_active = False
                                    current_key_set = keys
                            
                            hover_start_time = current_time  # Reset timer after action
                            search_initiated = False  # Reset search flag
                    else:
                        last_key_hovered = hovered_key
                        hover_start_time = current_time
                        last_backspace_time = 0
                        last_enter_time = 0
                        search_initiated = False
                else:
                    last_key_hovered = None
                    hover_start_time = None
                    search_initiated = False

    # Professional text display area
    cv2.rectangle(screen, (40, 40), (WIDTH - 40, 120), (50, 50, 55), -1)
    cv2.rectangle(screen, (40, 40), (WIDTH - 40, 120), (100, 100, 120), 2)
    
    # Display the text with word wrapping
    text_x = 55
    text_y = 85
    max_width = WIDTH - 100
    
    # Split text into lines
    lines = []
    current_line = ""
    for char in output_text:
        if char == '\n':
            lines.append(current_line)
            current_line = ""
        elif cv2.getTextSize(current_line + char, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0][0] > max_width:
            lines.append(current_line)
            current_line = char
        else:
            current_line += char
    if current_line:
        lines.append(current_line)
    
    # Display only the last few lines
    max_lines = 2
    start_line = max(0, len(lines) - max_lines)
    for i, line in enumerate(lines[start_line:]):
        y_pos = text_y + i * 30
        cv2.putText(screen, line, (text_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    
    # Draw blinking cursor at end of text
    if cursor_visible and not search_initiated:
        if lines:
            last_line = lines[-1]
            text_width = cv2.getTextSize(last_line, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0][0]
            cursor_x = text_x + text_width + 2
            cursor_y = text_y + (len(lines) - 1 - start_line) * 30
            cv2.line(screen, (cursor_x, cursor_y - 20), (cursor_x, cursor_y + 5), (255, 255, 255), 2)

    # Status bar
    status_bg = (40, 40, 45)
    cv2.rectangle(screen, (0, HEIGHT - 30), (WIDTH, HEIGHT), status_bg, -1)
    
    status_text = f"CAPS: {'ON' if caps_lock else 'OFF'} | SHIFT: {'ON' if shift_active else 'OFF'} | TEXT: {len(output_text)} chars"
    cv2.putText(screen, status_text, (20, HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    # Instructions
    instruction = "Hover over keys (1.2s) to type | Enter to Google Search | ESC to exit"
    cv2.putText(screen, instruction, (WIDTH - 600, HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 200), 1)

    # Show notification if active
    if current_time < notification_end_time:
        pass  # Notification is handled in the function
    
    # Display frame rate
    fps = cap.get(cv2.CAP_PROP_FPS)
    cv2.putText(screen, f"FPS: {int(fps)}", (WIDTH - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 100), 1)

    cv2.imshow("Professional Virtual Keyboard - Google Search Enabled", screen)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC key
        break
    elif key == ord('c'):  # Manual clear (for testing)
        output_text = ""

cap.release()
cv2.destroyAllWindows()