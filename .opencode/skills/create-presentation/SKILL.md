---
name: create-presentation
description: Create polished, self-contained HTML slide decks with Tailwind CSS, keyboard navigation, and a clean light aesthetic. Use when the user asks for a presentation, deck, slides, or slideshow. Generates a single HTML file with arrow-key navigation, progress dots, and no build step.
---

# Create Presentation

Generate self-contained HTML slide decks. No build step. No external assets.
Open the file in any browser.

## What You Create

A single HTML file containing:

1. **Slides** — full-viewport `<div class="slide">` elements, one per screen
2. **Navigation** — arrow keys, space, prev/next buttons, progress dots
3. **Styling** — Tailwind CSS via CDN + Google Fonts (Inter + JetBrains Mono)
4. **Zero dependencies** beyond two CDN links

## Design Principles

**CRITICAL**: Match the taste. This is a clean, light, content-first aesthetic.

- **Backgrounds**: white (`bg-white`) and slate-50 (`bg-slate-50`), alternating for rhythm. Section dividers use `bg-slate-100`.
- **Typography**: Inter for body, JetBrains Mono for code/identifiers. Headings are bold, not decorative.
- **Color as semantics, not decoration**: green = good, blue = info, amber = warning, rose = bad, purple = special. Never use color randomly.
- **Cards**: rounded corners (`rounded-xl`, `rounded-2xl`), colored top borders (`border-t-4` or `border-t-8`), subtle backgrounds (`bg-green-50`, `bg-blue-50`, etc.)
- **Whitespace**: generous padding (`p-6` to `p-16`), gaps between elements (`gap-6`, `gap-8`)
- **No dark themes** unless the user explicitly asks. Light and airy is the default.
- **No branding assets**: no logos, no capsules, no company-specific images. Content speaks for itself.
- **No animations** beyond the slide transition itself.
- **Scannable**: short bullets, one idea per slide, visual hierarchy through size and weight.

## Color System

Use these exact classes consistently:

| Meaning | Card bg | Top border | Text accent | Tailwind border class |
|---|---|---|---|---|
| Good / pass | `bg-green-50` | green | `green-accent` (#16A34A) | `border-green-400` |
| Info / neutral | `bg-blue-50` | blue | `blue-accent` (#2563EB) | `border-blue-400` |
| Warning | `bg-amber-50` | amber | `amber-accent` (#D97706) | `border-amber-400` |
| Bad / fail | `bg-rose-50` | rose | `rose-accent` (#E11D48) | `border-rose-400` |
| Special | `bg-purple-50` | purple | `purple-accent` (#7C3AED) | `border-purple-300` |
| Neutral / slate | `bg-slate-50` or `bg-white` | slate | `ink` (#0F172A) | `border-slate-200` |

Text utility classes (defined in the style block):
- `ink` — primary text (#0F172A)
- `ink-light` — secondary text (#475569)
- `ink-muted` — tertiary text (#94A3B8)
- `mono` — monospace font

## Slide Templates

### Title Slide (centered)

```html
<div class="slide active flex flex-col justify-center items-center p-12 bg-white relative">
    <p class="text-sm ink-muted uppercase tracking-widest mb-8">Section Label</p>
    <h1 class="text-5xl font-black ink text-center max-w-4xl leading-tight mb-4">Title Here</h1>
    <p class="text-xl ink-light text-center max-w-3xl mb-12">Subtitle here</p>
    <div class="flex gap-6">
        <div class="bg-slate-50 px-8 py-5 rounded-2xl border-t-4 border-slate-300 text-center">
            <div class="text-3xl font-black ink">VALUE</div>
            <div class="text-sm ink-muted uppercase tracking-wider mt-1">LABEL</div>
        </div>
    </div>
</div>
```

### Content Slide (white)

```html
<div class="slide inactive flex flex-col justify-center p-16 bg-white relative">
    <h1 class="text-3xl font-bold ink mb-3">Slide Title</h1>
    <p class="ink-light mb-10 max-w-3xl">One-line context for what this slide shows.</p>
    <!-- Content here: cards, grids, tables, code blocks -->
</div>
```

### Content Slide (slate-50, alternating)

```html
<div class="slide inactive flex flex-col justify-center p-16 bg-slate-50 relative">
    <h1 class="text-3xl font-bold ink mb-3">Slide Title</h1>
    <p class="ink-light mb-10 max-w-3xl">Context line.</p>
    <!-- Content here -->
</div>
```

### Section Divider (centered, slate-100)

```html
<div class="slide inactive flex flex-col justify-center items-center p-16 bg-slate-100 relative">
    <h1 class="text-4xl font-black ink text-center mb-4">Section Title</h1>
    <p class="text-xl ink-muted text-center">Optional subtitle</p>
</div>
```

### Closing Slide (slate-900)

```html
<div class="slide inactive flex flex-col justify-center items-center p-16 bg-slate-900 relative">
    <h1 class="text-4xl font-black text-white text-center mb-6 max-w-3xl leading-tight">
        Closing statement
    </h1>
    <p class="text-xl text-slate-400 text-center mb-12">Supporting line</p>
    <p class="mono text-sm text-slate-600 mt-8">link or reference</p>
</div>
```

## Component Patterns

### Stat Cards Row

```html
<div class="flex gap-6">
    <div class="bg-blue-50 px-8 py-5 rounded-2xl border-t-4 border-blue-400 text-center">
        <div class="text-3xl font-black blue-accent">95%</div>
        <div class="text-sm ink-muted uppercase tracking-wider mt-1">Label</div>
    </div>
    <!-- Repeat with different colors -->
</div>
```

### Info Card (left border accent)

```html
<div class="bg-green-50 p-7 rounded-2xl border-l-8 border-green-400">
    <p class="text-lg font-bold ink">Card title</p>
    <p class="text-slate-700 text-sm mt-2 leading-relaxed">Card content</p>
</div>
```

### Top-border Card Grid

```html
<div class="grid grid-cols-3 gap-6 max-w-5xl mx-auto w-full">
    <div class="bg-green-50 p-7 rounded-2xl border-t-8 border-green-400">
        <h3 class="text-lg font-black green-accent uppercase tracking-wide mb-4">Good</h3>
        <ul class="space-y-3 text-slate-700 text-sm">
            <li>Item one</li>
            <li>Item two</li>
        </ul>
    </div>
    <!-- More cards with different colors -->
</div>
```

### Two-Column Comparison

```html
<div class="grid grid-cols-2 gap-8 max-w-5xl mx-auto w-full">
    <div class="bg-green-50 p-7 rounded-2xl border-t-8 border-green-400">
        <h3 class="text-lg font-black green-accent mb-4">Left Side</h3>
        <p class="text-slate-700 text-sm">Content</p>
    </div>
    <div class="bg-rose-50 p-7 rounded-2xl border-t-8 border-rose-400">
        <h3 class="text-lg font-black rose-accent mb-4">Right Side</h3>
        <p class="text-slate-700 text-sm">Content</p>
    </div>
</div>
```

### Case Study Slide (consistent structure)

For before/after, good/poor, or example breakdowns:

```html
<div class="slide inactive flex flex-col justify-center p-16 bg-white relative">
    <div class="flex items-center gap-3 mb-4">
        <span class="bg-green-100 text-green-700 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Good</span>
        <h1 class="text-2xl font-bold mono ink">case_name</h1>
    </div>
    <p class="ink-light mb-8">One-line task description.</p>
    <div class="space-y-4 max-w-4xl">
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <p class="text-xs font-bold ink-muted uppercase tracking-wide mb-2">Visible test</p>
            <p class="text-sm text-slate-700">What was tested</p>
        </div>
        <div class="bg-green-50 p-4 rounded-xl border border-green-200">
            <p class="text-xs font-bold green-accent uppercase tracking-wide mb-2">What happened</p>
            <p class="text-sm text-slate-700">What the subject did</p>
        </div>
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <p class="text-xs font-bold ink-muted uppercase tracking-wide mb-2">Hidden test</p>
            <p class="text-sm text-slate-700">What was actually checked</p>
        </div>
        <div class="bg-blue-50 p-4 rounded-xl border border-blue-200">
            <p class="text-xs font-bold blue-accent uppercase tracking-wide mb-2">Why it worked / went wrong</p>
            <p class="text-sm text-slate-700">The lesson</p>
        </div>
    </div>
</div>
```

### Data Table

```html
<table class="w-full text-left">
    <thead>
        <tr class="border-b-2 border-slate-200">
            <th class="py-3 px-4 text-xs uppercase tracking-wider ink-muted font-bold">Column</th>
            <th class="py-3 px-4 text-xs uppercase tracking-wider ink-muted font-bold text-right">Value</th>
        </tr>
    </thead>
    <tbody class="text-base">
        <tr class="border-b border-slate-100">
            <td class="py-3 px-4 mono ink">label</td>
            <td class="py-3 px-4 text-right mono green-accent font-bold">100%</td>
        </tr>
    </tbody>
</table>
```

### Code Block (dark)

```html
<div class="bg-slate-900 p-6 rounded-2xl mb-6">
    <p class="mono text-xs text-slate-400 mb-2"># comment</p>
    <p class="mono text-sm text-slate-300">code_line = "value"</p>
</div>
```

### Inline Code

```html
<span class="mono text-sm bg-slate-100 px-2 py-0.5 rounded">code_here</span>
```

### Badge / Tag

```html
<span class="bg-green-100 text-green-700 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Good</span>
<span class="bg-rose-100 text-rose-700 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">False-Green</span>
```

### Blockquote

```html
<div class="bg-blue-50 p-8 rounded-2xl border-l-8 border-blue-400 mb-10">
    <p class="text-2xl ink font-bold italic">The key insight, stated plainly.</p>
</div>
```

### Explainer Box (blue, italic)

For plain-language translations of jargon:

```html
<div class="bg-blue-50 p-6 rounded-2xl border border-blue-200 max-w-3xl mx-auto w-full">
    <p class="text-sm text-slate-700 leading-relaxed">
        Plain explanation of a technical concept.
    </p>
</div>
```

### Example Callout (orange)

For real examples threaded through a flow:

```html
<div class="bg-fff7ed border border-fed7aa rounded-xl p-4" style="background:#fff7ed;border-color:#fed7aa;">
    <p class="text-xs font-bold uppercase tracking-wide mb-2" style="color:#c2410c;">Example</p>
    <p class="text-sm" style="color:#9a3412;">What actually happened in this case.</p>
</div>
```

## Full HTML Scaffold

Use this exact structure. The first slide is `active`, all others are `inactive`.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presentation Title</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #ffffff; margin: 0; overflow: hidden; }
        .mono { font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; }
        .slide { transition: opacity 0.4s ease-in-out, transform 0.4s ease-in-out; }
        .slide.inactive { opacity: 0; pointer-events: none; transform: scale(0.98); position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
        .slide.active { opacity: 1; pointer-events: auto; transform: scale(1); position: relative; width: 100%; height: 100vh; z-index: 10; }
        .ink { color: #0F172A; }
        .ink-light { color: #475569; }
        .ink-muted { color: #94A3B8; }
        .blue-accent { color: #2563EB; }
        .green-accent { color: #16A34A; }
        .amber-accent { color: #D97706; }
        .rose-accent { color: #E11D48; }
        .purple-accent { color: #7C3AED; }
    </style>
</head>
<body class="text-slate-800 selection:bg-blue-200">
    <div id="deck" class="w-full h-screen relative flex flex-col">

        <!-- SLIDES HERE -->

        <!-- Navigation -->
        <div class="absolute bottom-0 w-full h-16 flex items-center justify-between px-8 z-50 pointer-events-none">
            <div class="flex space-x-2" id="dots"></div>
            <div class="text-slate-400 mono text-sm pointer-events-auto flex items-center space-x-4 bg-white/80 px-4 py-2 rounded-full shadow-sm border border-slate-200">
                <button id="prevBtn" class="hover:text-slate-800 transition-colors px-2 py-1">&larr; Prev</button>
                <span class="opacity-50">|</span>
                <span class="text-xs tracking-widest uppercase">Arrow Keys</span>
                <span class="opacity-50">|</span>
                <button id="nextBtn" class="hover:text-slate-800 transition-colors px-2 py-1">Next &rarr;</button>
            </div>
        </div>
        <div class="absolute top-8 right-8 z-50 ink-muted mono font-bold">
            <span id="currentSlideNum">1</span> / <span id="totalSlidesNum">N</span>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const slides = document.querySelectorAll('.slide');
            const dotsContainer = document.getElementById('dots');
            const currentSlideEl = document.getElementById('currentSlideNum');
            const totalSlidesEl = document.getElementById('totalSlidesNum');
            let currentIdx = 0;

            totalSlidesEl.textContent = slides.length;

            slides.forEach((_, i) => {
                const dot = document.createElement('div');
                dot.className = `w-2 h-2 rounded-full transition-all duration-300 ${i === 0 ? 'bg-blue-500 w-6' : 'bg-slate-300'}`;
                dotsContainer.appendChild(dot);
            });

            const dots = dotsContainer.querySelectorAll('div');

            function showSlide(index) {
                if (index < 0) index = 0;
                if (index >= slides.length) index = slides.length - 1;
                slides[currentIdx].classList.remove('active');
                slides[currentIdx].classList.add('inactive');
                slides[index].classList.remove('inactive');
                slides[index].classList.add('active');
                dots[currentIdx].classList.remove('bg-blue-500', 'w-6');
                dots[currentIdx].classList.add('bg-slate-300', 'w-2');
                dots[index].classList.remove('bg-slate-300', 'w-2');
                dots[index].classList.add('bg-blue-500', 'w-6');
                currentSlideEl.textContent = index + 1;
                currentIdx = index;
            }

            document.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowRight' || e.key === ' ') {
                    e.preventDefault();
                    showSlide(currentIdx + 1);
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    showSlide(currentIdx - 1);
                }
            });

            document.getElementById('prevBtn').addEventListener('click', () => showSlide(currentIdx - 1));
            document.getElementById('nextBtn').addEventListener('click', () => showSlide(currentIdx + 1));
        });
    </script>
</body>
</html>
```

## Workflow

### Step 1: Understand the Content

Before writing any HTML, ask yourself:

1. What is this presentation about? What tone does it suggest?
2. How many slides are needed? (3-20 recommended)
3. Which slides are section dividers vs content slides?
4. What real examples or data can ground each slide?

### Step 2: Plan the Structure

Determine slide order. Good rhythm:
- Title slide (centered, stats or subtitle)
- Context / problem slides (build tension)
- How it works (1-2 slides, simplified)
- Data / findings (tables, stat cards)
- Cases (good examples, then poor examples — same structure each)
- The pattern / takeaway
- Honest limits (what this can and can't tell you)
- Closing / deployment policy

Alternate `bg-white` and `bg-slate-50` for visual rhythm. Use `bg-slate-100` for
section dividers. Use `bg-slate-900` for the closing slide only.

### Step 3: Write the HTML

**IMPORTANT**: Use the Edit tool to fill in slides incrementally — one or a few
slides at a time. Do NOT rewrite the entire HTML file with the Write tool after
the initial scaffold. Write the full file once, then edit sections if needed.

### Step 4: Verify

After generating, open the file in a browser and check:
- Every slide fits in the viewport (no scrolling needed)
- Text is readable (strong contrast, appropriate size)
- Colors are consistent (same meaning = same color throughout)
- Navigation works (arrow keys, space, prev/next buttons, dots)
- Slide counter shows correct total

## Do

- Alternate white and slate-50 backgrounds for rhythm
- Use color as semantics (green=good, rose=bad, blue=info, amber=warning)
- Keep text scannable: short bullets, one idea per slide
- Use `mono` class for code, identifiers, file paths, function names
- Use stat cards for headline numbers
- Use case study structure (visible → action → hidden → lesson) for examples
- Include an honest "what this can't tell you" section when presenting findings
- Close with a dark slide for contrast

## Don't

- Don't use dark themes (unless explicitly asked)
- Don't add logos, branding assets, or company-specific images
- Don't use animations beyond the slide transition
- Don't put more than ~150 words on a slide
- Don't use more than 3-4 colors per slide
- Don't make slides taller than viewport
- Don't overstate findings — include limits honestly
- Don't use em, rem, or px for font sizes inside Tailwind (Tailwind handles sizing)
- Don't create separate CSS files — everything is inline in the `<style>` block
