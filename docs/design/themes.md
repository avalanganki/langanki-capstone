# Themes for Patterns

## Purpose and Feel

Soft, calm, and reflective. Patterns is a wind-down tool for biohackers, used at night on a phone, so the design should lower the pace rather than add to it. The screen should feel like closing the day, not checking a dashboard. Claude's voice is clearly marked as AI, but the product should not look like a chatbot. It should look like a quiet journal with data attached.

Design principles:
- Dark and low-glare at night, light only for daytime review.
- Few elements per screen. One question at a time.
- Data is shown plainly and never used to judge the user.
- Serif means Claude is speaking. Sans means the user or the data.

## Colors

The palette is warm charcoal and dusty rose. It was chosen from five original options and is not copied from the Oura app. It is the least blue of the options, which keeps Patterns feeling like a journal rather than a health tracker.

| Token | Hex | Role |
|---|---|---|
| Night Charcoal | #1A1618 | Dark screen background |
| Cocoa Card | #2A2326 | Cards and answer fields on dark. Main text on cream. |
| Dusty Mauve | #7A4A5A | Primary accent: buttons, tags, ring tracks, first bar color |
| Rose Glow | #E6B8C4 | Secondary accent: ring fills, small labels on dark |
| Amber Caution | #F0A35E | Caution only (see rules below) |
| Cream Rose | #F5EDE6 | Light screen background (insights) |
| Soft Blush | #F3ECEE | Main text on dark |
| White | #FFFFFF | Cards on cream |

Derived tones:
- Sky bands (dark to light): #1A1618, #211c1f, #2A2326, #4a2f3b, #7A4A5A
- Claude's follow-up replies on dark (slightly dimmer than main text): #D9CDD2
- Placeholder text on dark: #9A8D92
- Dividers and borders on cream: #E6D9D2
- Second bar color on cream: #C48B9F (needs to be clearly different from Dusty Mauve)

Usage rules:
- **Two modes by task.** Dark for the nightly reflection. Cream for reviewing insights. Do not show the cream screen at bedtime.
- **Amber means caution.** Use it for low energy tags, small-sample warnings, and errors. Do not use it for routine tags, or it stops signaling anything.
- **Amber is never text on cream.** The contrast is too low. Use it as a dot or a fill there.
- **Text on dark** is Soft Blush, never pure white, to reduce glare.
- **Background on dark** is Night Charcoal, never pure black.
- **Contrast.** I estimated the main text pairings above 4.5:1, but these colors were picked by eye. Verify each pairing with a contrast checker before shipping, especially Rose Glow labels on dark and the two bar colors on cream.

## Typography

**Families**
- Fraunces (soft axis at 100, weight 400): screen titles, Claude's questions, Claude's replies
- Nunito Sans: everything else (your answers, scores, tags, buttons, labels, charts)
- Rule: serif means Claude is speaking, sans means you or the data
- Fallbacks: Georgia for Fraunces, system sans for Nunito Sans

**Sizes**

| Element | Size | Notes |
|---|---|---|
| Screen title | about 26px | Fraunces |
| Claude's main question | 19 to 20px | Line height 1.55 |
| Claude's follow-up replies | 17px | Line height 1.6, slightly dimmer (#D9CDD2) |
| Your answer and input text | 16px minimum | Line height 1.6. Below 16px, iPhones zoom in on tap. |
| Score numbers | about 20px | Weight 500, tabular numbers |
| Buttons | 15px | Weight 500 |
| Tags | 13px | |
| Labels and date | 12 to 13px | |
| Minimum for anything | 12px | |

**Rules**
- Two weights only: 400 and 500. Light text on dark already looks thinner than it is.
- Tabular numbers on scores and charts (`font-variant-numeric: tabular-nums`).
- Sentence case for all labels and buttons.
- Size in rem so text follows the phone's system text size.
- Keep Claude's insight summaries in Fraunces, but keep numbers and charts in Nunito Sans so data does not read as opinion.

## Spacing and Layout

Phone first. Design for a 360px wide screen.

**Screen**
- Full width, no centered column.
- 16 to 20px side padding, plus safe-area padding for the notch and home bar.
- Dark screen: a night-sky header runs edge to edge at the top, then content below.

**Rhythm**
- 20 to 24px between sections.
- 10 to 12px between cards.
- 12 to 14px inside cards.

**Shapes**
- Cards, inputs, and buttons are rectangular with 4px corners. This keeps the app from looking like a chat product.
- Tags are pills. They are the one soft shape and are meant to feel like labels, not buttons.
- Readiness and sleep scores are circular rings, with the number inside and the label below. Ring track is Dusty Mauve at reduced opacity, ring fill is Rose Glow.
- Average HRV is shown as the number and label only, with no ring, on the same card background. HRV has no natural maximum, so a ring would suggest a scale that doesn't exist.
- The user's answers sit in a Cocoa Card with 4px corners, so they read apart from Claude's questions.

**Input**
- Pinned at the bottom above the keyboard so the question stays visible while typing.
- 44px tall. Text 16px or larger.

**Tap targets**
- At least 44px tall for Send, Done, and any editable tag.

**Line length**
- 35 to 45 characters per line is normal on a phone. Short lines are fine.

**Dark screen order (top to bottom)**
1. Night sky with date and title
2. Score rings in one card
3. Claude's question
4. The user's answer
5. Claude's follow-up
6. Tags found tonight
7. Input and Send

**Cream screen order**
1. Label ("Last 12 nights") and title
2. One plain-language summary from Claude
3. Data cards with the number of nights shown
4. Caution note
5. Edit tags and Done

## Imagery

- The night sky is a flat illustration: stacked dusk bands in the palette, a few stars, a crescent moon, and two hill silhouettes. No gradients or photos in the first version.
- Wind-down photography from other apps should not be copied. If real photography is added later, use my own photos or a license-free source, and keep the lower third dark so the title stays readable.
- Icons, if needed, are simple outline icons. No illustrations on the cream screen.

## Voice and Tone

Questions are brief, neutral, and never judgmental (from the PRD).

- Ask one question at a time.
- Use plain words. Avoid biohacking jargon unless the user used it first.
- Do not praise or scold. No streak guilt, no "you should".
- Describe patterns, not causes. Use "tended to" and "pattern, not proof".
- Always show how many nights a pattern is based on.
- Do not give medical advice.
- Sentence case. Contractions are fine. No exclamation marks in system text.
- Claude's text may say "you". System text (buttons, labels, errors) never says "I".

| Instead of | Write |
|---|---|
| "You slept badly because of your coffee." | "On nights after late caffeine, your HRV tended to run lower." |
| "Great job logging 5 days in a row!" | "Logged tonight." |
| "Why did you drink so much caffeine?" | "How did your energy feel this afternoon?" |
| "Error: failed to sync." | "Couldn't reach Oura. Try again." |

## Motion

Slow and quiet. Motion should never wake the user up.

- Transitions are 200 to 300ms, ease-out.
- A new question fades in. It does not slide or bounce.
- Rings fill once on load over about 600 to 800ms.
- No confetti, celebration animations, or bouncing elements.
- Optional: very slow star twinkle in the sky header. Off by default.
- Respect `prefers-reduced-motion`. When set, turn off all motion except plain fades.
- While Claude is writing a question, show a slow, subtle indicator or nothing.

## Accessibility

- Body text and inputs at 16px or larger.
- Tap targets at least 44px.
- Text contrast at least 4.5:1 (verify, see Colors).
- Color is never the only signal. Amber cautions also have words, not just a color.
- Rings include a text label and number, so they are readable without seeing the fill.
- Support the system text size setting and reduced motion.

## Dos and Don'ts

Do:
- Keep one question on screen at a time.
- Show the sample size next to every correlation.
- Keep amber rare.

Don't:
- Use pure black or pure white on the dark screen.
- Put the serif font on data, or the sans font on Claude's words.
- Round every corner. Rectangles for containers, pills for tags only.
- Use bright light backgrounds at bedtime.

## Open Questions

1. **HRV ring.** Resolved Oct 1 (`docs/notes.md`): no ring for HRV, just the number. Readiness and sleep are scored 0 to 100, so a full ring means something, but HRV has no natural maximum.
2. **Oura developer terms.** Skim the terms agreed to when registering the app at cloud.ouraring.com, since Patterns connects to their API.
3. **Fonts at small sizes.** Test Fraunces on a real phone in a dark room before committing.
4. **Platform.** Streamlit gives less control over fonts, bottom-pinned input, and phone spacing than a simple custom web page. Browser versus installed home-screen app also changes how much of this layout is controllable.
5. **Rose Glow labels.** Check small Rose Glow text on dark on an actual phone.
6. **Bar colors on cream.** Confirm the two bar colors are clearly distinguishable on the cream screen.