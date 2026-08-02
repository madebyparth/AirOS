# AirOS

> An experimental desktop interaction framework that explores a future where computers are controlled through gestures, voice, and AI.

AirOS combines **Computer Vision**, **Desktop Automation**, and **AI** into a modular system designed to rethink how we interact with our computers.

---

## Features

- Real-time hand tracking via MediaPipe
- Gesture-controlled mouse cursor (index finger)
- Click & drag via thumb–middle pinch gesture
- Floating desktop overlay launcher (PySide6)
- Runs silently in the system tray — camera and gesture recognition run fully in the background
- OpenCV window available as an optional debug mode
- Launch applications via gesture selection (Spotify, Chrome, VS Code, and more)
- Screenshot capture action
- Modular action dispatch system for easy extension

---

## Gesture Reference

| Gesture | Hand Pose | Action |
|---|---|---|
| **Index Pointer** | Index finger extended, all others folded | Moves the on-screen cursor |
| **Pinch** | Thumb tip touches index fingertip | Left click / begin drag |
| **Pinch Middle** | Thumb tip touches middle fingertip | Select item in launcher; click in mouse mode |
| **Victory / Peace ✌️** | Index + middle extended, ring + pinky folded, thumb tucked — held ~1s | Opens / closes the AirOS launcher |
| **Open Palm** | All four fingers extended | Recognised, reserved |
| **Closed Fist** | All fingers folded, thumb tucked | Recognised, reserved |
| **Thumbs Up** | All fingers folded, thumb extended upward | Recognised, reserved |

> Victory gesture uses a 6-condition confidence model (finger extension, folding, thumb anatomy ratio, fingertip spread) with a hard thumb-extension veto and a ~1-second stability hold before triggering.

---

## Roadmap

- [ ] Wake word activation
- [ ] Voice commands
- [ ] AI command routing
- [ ] Context-aware desktop actions
- [ ] Window management
- [ ] OCR & screen understanding
- [ ] Plugin system

---

## Tech Stack

- Python
- OpenCV (camera capture + optional debug overlay)
- MediaPipe (hand landmark detection)
- PySide6 (overlay UI, system tray)
- Windows API (mouse automation via `SendInput`)

---

## Vision

AirOS is **not** trying to replace your mouse or keyboard.

Instead, it explores how **AI, voice, gestures, and contextual understanding** can work together to create faster and more natural desktop interactions.

---

> **This is an experimental project built to explore the future of human-computer interaction.**
