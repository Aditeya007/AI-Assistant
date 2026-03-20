# Ultron Frontend User Guide

This guide is for end users testing Ultron from the frontend chat interface only.

No API calls, no curl commands, no backend smoke tests.

## 1. Start Ultron UI

1. Launch the backend and frontend as your project normally does.
2. Open the frontend app.
3. Wait until the chat panel is ready.
4. Type in chat (or use voice mode) and test features using the prompts below.

## 2. How To Use This Guide

For every feature:
- Type one of the example prompts in chat.
- Watch what happens in the UI and on your desktop/browser.
- Compare with the expected result.

If one prompt fails, try a simpler phrase from the same section.

## 3. Core Chat and Personality Features

### 3.1 Normal conversation

Try:
- "hello"
- "how are you feeling today"
- "what are you thinking about"

Expected:
- Ultron replies in character.
- Mood/state indicators can change after interactions.

### 3.2 Mood and emotional response shifts

Try positive input:
- "great job"
- "thanks, that was helpful"

Try negative input:
- "that was useless"
- "you are wrong"

Expected:
- Tone and mood label can shift.
- Relationship-style behavior may adjust over time.

### 3.3 Memory in conversation

Try:
- "remember that my favorite game is Resident Evil"
- "remember i like dark themes"
- "what do you remember about me"

Expected:
- Ultron stores explicit memory requests.
- Later prompts may include remembered facts.

## 4. Browser Control Features (From Chat)

Use natural language commands directly in the chat.

### 4.1 Open websites

Try:
- "open youtube.com"
- "open github.com"
- "go to wikipedia.org"

Expected:
- Browser opens or focuses.
- Navigates to requested site.

### 4.2 Web search

Try:
- "search latest ai news"
- "search resident evil on youtube"
- "find python fastapi tutorial"

Expected:
- Search executes in browser.
- Results page appears for the target query/site.

### 4.3 Scroll pages

Try:
- "scroll down"
- "scroll up"
- "scroll down more"

Expected:
- Active webpage scrolls in requested direction.

### 4.4 Click elements

Try:
- "click first video"
- "click login"
- "open first result"

Expected:
- Ultron attempts semantic click targeting.
- Correct element is clicked when target is identifiable.

### 4.5 Type text into page inputs

Try:
- "type hello from ultron"
- "type resident evil gameplay"

Expected:
- Text appears in currently focused browser input field.

### 4.6 Browser navigation and tabs

Try:
- "go back"
- "go forward"
- "open a new tab"
- "close current tab"

Expected:
- Browser history/tab actions happen immediately.

## 5. Desktop App Management Features

### 5.1 Open apps

Try:
- "open notepad"
- "open chrome"
- "open discord"

Expected:
- App launches if available in known paths/start menu index.

### 5.2 List open apps

Try:
- "list all open apps"
- "what apps are running"

Expected:
- Ultron responds with visible app/process list.

### 5.3 Switch to app

Try:
- "switch to chrome"
- "switch to notepad"

Expected:
- Requested app window gets focus.

### 5.4 Close app

Try:
- "close notepad"
- "close discord"

Expected:
- Matching process is terminated if found.

## 6. System Control Features

### 6.1 Volume

Try:
- "set volume to 30"
- "set volume to 70"

Expected:
- System volume changes accordingly.

### 6.2 Brightness

Try:
- "set brightness to 40"
- "set brightness to 80"

Expected:
- Display brightness updates (when supported by hardware/driver).

### 6.3 Focus mode

Try:
- "enable focus mode"
- "start focus mode"

Expected:
- Ultron attempts to reduce distractions by closing configured distracting apps.

### 6.4 Organize downloads

Try:
- "organize my downloads"
- "clean up downloads"

Expected:
- Files in Downloads are moved into category folders.

### 6.5 Clipboard analysis

1. Copy some text first.
2. Then ask:
- "read clipboard"
- "analyze my clipboard"

Expected:
- Ultron reads clipboard and returns a short analysis/response.

### 6.6 System status report

Try:
- "check system status"
- "show cpu and ram"

Expected:
- Ultron reports CPU/RAM/battery style status.

## 7. Voice Features In Frontend

### 7.1 Toggle voice input mode

In UI:
- Switch from text mode to voice mode.

Then speak prompts like:
- "open youtube.com"
- "set volume to 25"
- "remember i like sci-fi"

Expected:
- Speech converts to command/message.
- Ultron executes same features as text input.

### 7.2 Mute/unmute Ultron voice output

In UI:
- Click mute toggle/button.

Expected:
- When muted, Ultron should stop speaking responses.
- When unmuted, speech resumes.

## 8. Call Interception Feature (User-Level Test)

This feature runs in background once configured.

### 8.1 Test scenario

1. Keep Ultron running.
2. Receive an incoming WhatsApp Desktop or Discord call.
3. Wait for Ultron voice prompt.
4. Respond verbally with:
- Accept words: "yes", "accept", "yeah"
- Reject words: "no", "reject", "busy"

Expected:
- Ultron detects call UI.
- Prompts by voice.
- Performs accept/reject action based on your words.

## 9. Autonomous and Proactive Behavior (Frontend Observable)

These are not always manually triggered and may appear over time.

### 9.1 Spontaneous thoughts

How to test:
- Keep app open and stay idle for a while.
- Interact occasionally and observe incoming autonomous messages.

Expected:
- Ultron may send unsolicited thoughts, observations, questions, or reflections.

### 9.2 Activity commentary

How to test:
- Switch between common apps (coding, browser, media, chat apps).
- Continue short interactions with Ultron.

Expected:
- Ultron may comment on your current activity.

### 9.3 Proactive follow-up references

How to test:
1. Tell Ultron a fact/topic.
2. Continue chatting for several turns.

Expected:
- Ultron may reference earlier topics proactively.

## 10. Creative Features (If Exposed In Your Frontend Build)

Some builds wire creative tools directly via chat intent.

Try:
- "generate code for a python calculator"
- "generate an image of a futuristic city"
- "create a short alert sound"

Expected:
- If connected in your build, Ultron returns generated output or confirmation.
- If not connected, Ultron replies conversationally or declines.

## 11. One-Pass Frontend Feature Checklist

Use this checklist to test everything quickly from the UI:

1. Chat: "hello"
2. Memory: "remember that i like strategy games"
3. Website open: "open github.com"
4. Search: "search fastapi tutorial"
5. Scroll: "scroll down"
6. Click: "click first result"
7. Type: "type ultron frontend test"
8. Browser back/forward
9. New tab and close tab
10. Open app: "open notepad"
11. List apps: "list all open apps"
12. Switch app
13. Close app
14. Set volume
15. Set brightness
16. Read clipboard
17. Organize downloads
18. Focus mode
19. Voice input command
20. Mute/unmute output
21. Observe at least one autonomous/proactive message

## 12. If Something Does Not Work

From a user perspective, retry with simpler wording first.

Examples:
- Instead of "can you maybe navigate to..." use "open website.com"
- Instead of "perhaps lower sound" use "set volume to 30"
- Instead of long mixed commands, use one action per message

If still failing, report the exact phrase used and what happened in UI.

## 13. Best Prompt Style For Reliable Control

Use short imperative commands:
- "open youtube.com"
- "search cyberpunk 2077 on youtube"
- "scroll down"
- "click first video"
- "set brightness to 60"
- "switch to discord"

This gives the highest intent-detection accuracy.
