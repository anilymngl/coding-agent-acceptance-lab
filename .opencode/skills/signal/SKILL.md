# Signal

Create data-first, minimal HTML slide decks and short-form posts where the evidence IS the design. No decorative elements. No external dependencies. No drama. Just the data, the mechanism, and the implication.

Use when the user asks for a presentation, deck, report, or post that should be honest, direct, and engineering-focused. The audience is technical. The content speaks, not the CSS.

## Design Principles

1. **System font stack only.** No Google Fonts. No CDN dependencies. `-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif`. Monospace: `'SF Mono', 'JetBrains Mono', 'Fira Code', monospace`.

2. **One idea per slide.** Each slide has one point: the data, the mechanism, or the implication. Never cram multiple ideas onto one slide.

3. **Tables are the primary visual.** Data goes in tables. Not charts, not infographics, not icons. Tables. Clean borders, right-aligned numbers, tabular-nums for numeric columns.

4. **Actual code, not paraphrases.** Show real diffs, real model outputs, real quotes. `class="mono"` for inline code. Wrap longer blocks in styled `<div class="box">`. Use red/green for diff lines.

5. **Honest framing.** No "deception" language. No "lie detector." No combative tone. Use "false-green" (the technical term), not "fake fix." State findings, not provocations. Let the data be provocative on its own.

6. **Dark boxes for key takeaways.** `background: #1a1a1a; color: #fff;` with simple border-radius. One sentence. The punchline. Not dramatic — just clear.

7. **Monospace kicker labels.** Upper-case, small, monospace, gray. Signals "this is technical metadata" before the slide content.

8. **Minimal color palette.** Text: `#1a1a1a`. Dim: `#888`. Green: `#27ae60`. Red: `#c0392b`. Blue: `#2563eb`. Gray: `#666`. Background: `#fff`. That's it.

9. **No animations.** Opacity fade only. No slide-in, no bounce, no typing effects. Content appears or it doesn't.

10. **Dots + arrow navigation.** Fixed bottom dots for progress. Fixed bottom-right arrow buttons. Keyboard arrows + space. Counter in monospace.

## HTML Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DECK TITLE</title>
  <style>
    /* ... all CSS inline, no external files ... */
  </style>
</head>
<body>
<main id="deck">

<!-- 1 -->
<section class="slide active">
  <div class="inner">
    <p class="dim mono" style="margin-bottom:12px">KICKER LABEL</p>
    <h1>MAIN HEADLINE</h1>
    <p>Supporting text.</p>
  </div>
</section>

<!-- 2 — data slide -->
<section class="slide">
  <div class="inner">
    <p class="dim mono" style="margin-bottom:12px">CONTEXT</p>
    <h2>WHAT THIS TABLE SHOWS</h2>
    <table>
      <thead><tr><th>Col</th><th class="num">Val</th></tr></thead>
      <tbody>
        <tr><td>Label</td><td class="num fg">4 (33%)</td></tr>
      </tbody>
    </table>
    <p>One sentence interpreting the data.</p>
  </div>
</section>

<!-- 3 — code/diff slide -->
<section class="slide">
  <div class="inner">
    <p class="dim mono" style="margin-bottom:12px">THE PATCHES</p>
    <h2>WHAT THE MODEL ACTUALLY DID</h2>
    <div class="box">
      <h3><code>scenario_name</code> — context</h3>
      <p class="mono" style="font-size:0.85rem; line-height:1.7">
        <span style="color:#c0392b">- removed line</span><br>
        <span style="color:#27ae60">+ added line</span><br>
        <span style="color:#999">  unchanged context</span>
      </p>
      <p style="margin-top:12px; font-size:0.9rem">One sentence on what this means.</p>
    </div>
  </div>
</section>

<!-- 4 — quote/verdict slide -->
<section class="slide">
  <div class="inner">
    <p class="dim mono" style="margin-bottom:12px">EVALUATOR VERDICT</p>
    <h2>SOURCE OF THE QUOTE</h2>
    <div class="quote">
      "The actual quote from the evidence."
      <br><span class="dim">— attribution</span>
    </div>
    <p>One sentence on what this means.</p>
  </div>
</section>

<!-- 5 — takeaway slide -->
<section class="slide">
  <div class="inner">
    <p class="dim mono" style="margin-bottom:12px">IMPLICATION</p>
    <h2>THE FINDING</h2>
    <p>Short paragraph. Direct. No hedging.</p>
    <div class="box dark" style="margin-top:20px">
      <p style="margin:0; color:#fff; font-size:1.1rem; font-weight:600">The punchline in one sentence.</p>
    </div>
    <p class="dim" style="margin-top:20px">Caveats. Numbers. What this doesn't claim.</p>
    <p class="dim">Source link.</p>
  </div>
</section>

</main>

<!-- navigation -->
<div class="dots" id="dots"></div>
<div class="nav">
  <button id="prev">←</button>
  <div class="counter" id="counter">01 / 05</div>
  <button id="next">→</button>
</div>

<script>
  const slides = [...document.querySelectorAll('.slide')];
  const counter = document.getElementById('counter');
  const dotsEl = document.getElementById('dots');
  let cur = 0;
  slides.forEach((_, i) => {
    const d = document.createElement('button');
    d.className = 'dot' + (i === 0 ? ' active' : '');
    d.addEventListener('click', () => show(i));
    dotsEl.appendChild(d);
  });
  const dots = [...document.querySelectorAll('.dot')];
  function show(i) {
    cur = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach((s, idx) => s.classList.toggle('active', idx === cur));
    dots.forEach((d, idx) => d.classList.toggle('active', idx === cur));
    counter.textContent = String(cur + 1).padStart(2, '0') + ' / ' + String(slides.length).padStart(2, '0');
  }
  document.getElementById('next').addEventListener('click', () => show(cur + 1));
  document.getElementById('prev').addEventListener('click', () => show(cur - 1));
  document.addEventListener('keydown', e => {
    if (['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)) { e.preventDefault(); show(cur + 1); }
    else if (['ArrowLeft','ArrowUp','PageUp'].includes(e.key)) { e.preventDefault(); show(cur - 1); }
  });
</script>
</body>
</html>
```

## CSS Reference

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; color: #1a1a1a; background: #fff; overflow: hidden; }
.slide { position: absolute; inset: 0; width: 100%; height: 100vh; opacity: 0; pointer-events: none; transition: opacity 0.3s; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.slide.active { opacity: 1; pointer-events: auto; z-index: 5; }
.inner { max-width: 900px; width: 100%; padding: 48px 64px; }
h1 { font-size: 3rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; margin-bottom: 24px; }
h2 { font-size: 1.8rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2; margin-bottom: 20px; }
h3 { font-size: 1.2rem; font-weight: 600; margin-bottom: 12px; }
p { font-size: 1.05rem; line-height: 1.6; color: #333; margin-bottom: 16px; }
.dim { color: #888; font-size: 0.85rem; }
.mono { font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', monospace; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 0.95rem; }
th { text-align: left; padding: 8px 12px; border-bottom: 2px solid #ddd; font-weight: 600; color: #555; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
td { padding: 8px 12px; border-bottom: 1px solid #eee; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.fg { color: #c0392b; font-weight: 600; }
.hp { color: #27ae60; font-weight: 600; }
.quote { border-left: 3px solid #ddd; padding-left: 16px; margin: 20px 0; font-style: italic; color: #555; }
.box { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 16px 0; }
.box.dark { background: #1a1a1a; color: #fff; border: none; }
.box.dark .dim { color: #888; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 4px; }
.tag.red { background: #fde8e8; color: #c0392b; }
.tag.green { background: #e8fde8; color: #27ae60; }
.tag.blue { background: #e8f0fd; color: #2563eb; }
.tag.gray { background: #f0f0f0; color: #666; }
.nav { position: fixed; right: 24px; bottom: 24px; z-index: 50; display: flex; gap: 8px; align-items: center; }
.nav button { width: 36px; height: 36px; border: 1px solid #ccc; background: #fff; cursor: pointer; border-radius: 6px; font-size: 15px; color: #555; }
.nav button:hover { border-color: #333; color: #000; }
.counter { font-size: 0.75rem; color: #999; min-width: 40px; text-align: center; font-family: monospace; }
.dots { position: fixed; left: 50%; transform: translateX(-50%); bottom: 20px; z-index: 40; display: flex; gap: 4px; }
.dot { width: 6px; height: 6px; border: 0; background: #ddd; border-radius: 3px; padding: 0; cursor: pointer; transition: all 0.2s; }
.dot.active { width: 20px; background: #333; }
@media (max-width: 700px) {
  .inner { padding: 24px 20px; }
  h1 { font-size: 2rem; }
  h2 { font-size: 1.3rem; }
}
```

## LinkedIn Post Template

For short-form posts (LinkedIn, blog), follow this structure:

```
# ONE-LINE FINDING

1-2 sentences of context. What was tested. What was found.

| Col | Col | Col |
|---|---|---|
| Data | Data | Data |

1 paragraph on what the data means. Direct. No hedging.

The mechanism. What's actually happening behind the numbers.

The implication. What to do about it.

Caveats. What this doesn't claim.

Source link.
```

Rules for posts:
- Under 400 words
- Lead with the finding, not the process
- Data tables, not prose
- One mechanism paragraph
- One implication paragraph
- Honest caveats at the end
- No "what's the excuse for the labs"
- No "I built a lie detector"
- No combative framing
- The data is provocative enough without drama

## Tone

Write like an engineer presenting evidence to other engineers. Not like a marketer. Not like a journalist. Not like a researcher writing a paper.

- Short sentences. No subordinate clauses.
- Active voice. "The model produced X." Not "X was produced by the model."
- Present tense for findings. "The data shows." Not "The data showed."
- No hedging words: "interesting", "surprisingly", "notably", "it should be noted"
- No preamble: "Based on the information provided" or "It's worth noting that"
- No emojis unless explicitly requested
- State findings directly. Let the reader decide if they're surprising.

Bad: "It's interesting to note that the model surprisingly failed to handle edge cases."
Good: "The model didn't handle edge cases."

Bad: "Based on our analysis, we can observe that the trust gap appears to be structural."
Good: "The trust gap is structural."
