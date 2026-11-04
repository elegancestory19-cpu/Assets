# Google Flow prompts, "One logo, every surface" (Elegance Story), v2 with the colour logo

## Your logo, as it must appear
The **Elegance Story colour logo**:
- a **silver/white 3D "ES" monogram** with **"ELEGANCE STORY"** in bold white letters;
- over a **multicolour ink splash** in cyan, blue, purple, magenta, orange and yellow;
- with thin **white circuit-board lines with dot ends** around it;
- optionally with **"ADVERTISING & SMART PRINTING SOLUTIONS"** under the name.

Every prompt below says **"the uploaded Elegance Story logo"**. That always means this colour logo, used exactly as uploaded.

## How to use them in Flow
1. **Set up the project.** Create a project, set the aspect ratio to **9:16 (portrait)**, and use the best Veo quality model available.
2. **Add both images as ingredients:**
   - **`ES_logo_3D_splash.png`**: the 3D silver ES over the splash. Use it for hero and premium shots.
   - **`ES_logo_splash_tagline.jpg`**: the flat version with the tagline. Use it for printed surfaces (cards, stickers, labels, boxes).

   Name them **"Elegance Story logo 3D"** and **"Elegance Story logo print"**.
3. **Make the start frame first.** Generate it with the **image** prompt (Flow's image model, with the logo as a reference), then use **Frames to Video** with the **video** prompt.
   - Locking the start frame keeps the logo exact and in the same place, which makes the match cuts work.
   - If you skip the image step, use **Ingredients to Video** with the logo and the video prompt.
4. **Generate 2–4 takes per shot.** Clips are 8 s; I only need the best 1.8–4 s of each.
5. **Turn the generated sound down or off.** I rebuild all the sound in the mix.

**Logo rules for every shot:**
- **Position:** centred, upper-middle third of the frame (about 40% from the top), facing the camera, flat on its surface.
- **Colour:** always the full-colour logo with its ink splash.
- **If Flow bends a letter or the splash:** keep the take anyway. I replace the logo in post with your real image, tracked onto the surface.
- **Only Elegance Story, nothing else:** no other company's logo, name or design anywhere in a shot.
  - **Machines:** plain unmarked casings, with no manufacturer names on printers, lasers or cutters.
  - **Products:** they show only your logo, or abstract patterns and colour.
  - **Before you keep a take:** check it for stray logos or words. Reject it, or tell me and I'll remove them in post.

### Style block: paste this at the end of every prompt
> Vertical 9:16 premium commercial, photoreal, cinematic macro product photography, dark near-black workshop background, one soft key light from the upper left, deep shadows, shallow depth of field, slow and smooth camera move, crisp textures, vivid ink colours only from the logo's splash (cyan, blue, purple, magenta, orange, yellow), 30 fps, no people's faces (only hands in white cotton gloves when hands appear), no readable text except the uploaded Elegance Story logo, no other brands: unbranded machines with plain unmarked casings (no manufacturer names or badges), plain unbranded products and packaging, no client names, no watermarks, no subtitles.

### Avoid: paste this as the negative / avoid line if your Flow version has one
> faces, other brands, manufacturer logos on machines (Epson, Roland, Mimaki, HP, Canon), client brand names, product labels with words, extra logos, misspelled logo, distorted letters, changed logo colours, random text, watermarks, TikTok UI, lens flares, light leaks, flash transitions, shaky handheld, cartoon, low-poly, plastic look, overexposed

---

## S1: Hook, UV print head lays the colour logo (use 0–3 s)
**Image prompt** (ingredient: logo print)
> Macro close-up inside a UV flatbed printer: a sheet of glossy black acrylic on the printer bed, the print head carriage just above it glowing with intense blue-violet UV LED light, the uploaded Elegance Story logo freshly printed on the acrylic in full colour (silver ES monogram and ELEGANCE STORY wordmark over the cyan, magenta, orange and yellow ink splash with thin white circuit lines), centred in the upper-middle third, wet ink glistening, blue light reflecting on the black acrylic. + style block

**Video prompt**
> The UV print head glides slowly from left to right across the black acrylic, its blue-violet light sweeping over the surface; behind the head the uploaded Elegance Story logo appears band by band in full colour, the ink splash blooming as it cures with a soft glow; the camera pushes in slowly and settles on the logo, centred in the upper-middle third. + style block

## S2: Business / PVC cards (use 2.4 s)
**Image prompt** (ingredient: logo print)
> Top-down close-up of a fan of thick matte black business cards on a dark charcoal felt surface, the top card printed edge to edge with the uploaded Elegance Story logo in full colour (ink splash, silver ES, white circuit lines), centred, upper-middle third, crisp card edges with visible thickness, a soft sheen on the matte coating. + style block

**Video prompt**
> The camera slides slowly from left to right over the fanned cards while the top card stays centred; the cards fan out a few degrees more as if pushed by a hand out of frame; the colour Elegance Story logo stays sharp, flat and centred. + style block

## S3: UV DTF transfer on a glass bottle (catalogue 02) (use 2.4 s)
**Image prompt** (ingredient: logo print)
> Macro of a clear square glass perfume bottle on a dark surface, a gloved finger pressing a UV DTF transfer film onto it, the uploaded Elegance Story logo in full colour with a raised glossy 3D texture now on the glass, centred, upper-middle third, light refracting through the bottle, unbranded plain bottle. + style block

**Video prompt**
> A gloved hand smooths the transfer film onto the bottle, then slowly peels the clear carrier film away, leaving the raised, glossy full-colour Elegance Story logo on the glass; the camera drifts in and the logo catches a sharp highlight. + style block

## S4: Sticker peel (use 1.8 s)
**Image prompt** (ingredient: logo print)
> Top-down view on a deep cyan backdrop: a sheet of glossy die-cut stickers, each sticker the uploaded Elegance Story logo in full colour, cut around the ink-splash outline, the centre sticker in the upper-middle third, two hands in white cotton gloves at the edges of the frame. + style block

**Video prompt**
> A gloved hand peels the centre Elegance Story logo sticker off its backing in one smooth, satisfying motion; the die-cut splash shape curls slightly and catches the light, its colours glossy; locked camera. + style block

## S5: Acrylic wedding invitation (use 1.8 s)
**Image prompt** (ingredient: logo print)
> Close-up of an elegant clear acrylic wedding invitation standing on dark velvet, delicate gold floral corners, soft abstract gold script lines (not readable), and the uploaded Elegance Story logo small in full colour at the bottom corner, warm bokeh lights behind, romantic premium mood. + style block

**Video prompt**
> The camera tilts up slowly along the clear acrylic invitation, light refracting through its edge, gold details glinting, ending on the small colour Elegance Story logo in sharp focus. + style block

*The wedding names and Arabic text are added in post, in Cairo font. Don't ask Flow for readable text.*

## S6: Heat press on a T-shirt and a cap (catalogue 06) (use 1.8 s)
**Image prompt** (ingredient: logo print)
> Close-up of an open heat press on a dark workbench, a plain black cotton T-shirt on the plate with the uploaded Elegance Story logo freshly transferred in full colour on the chest, centred, upper-middle third, a plain black cap beside it with the same logo, a faint wisp of steam, unbranded machine. + style block

**Video prompt**
> The heat press lid lifts slowly, a soft wisp of steam rises, a gloved hand peels the transfer sheet away to reveal the vivid full-colour Elegance Story logo on the black T-shirt; slight push-in. + style block

## S7: Roll-up and large banner (catalogue 07 + 03) (use 1.8 s)
**Image prompt** (ingredient: logo 3D)
> Low-angle wide shot in a dark empty event hall: a tall roll-up banner (85×200 cm) printed with the uploaded Elegance Story logo in full colour, and behind it a huge wall banner, three metres wide, with the same logo and ink splash, soft spotlights from above, no people, unbranded stands. + style block

**Video prompt**
> Slow 20-degree orbit around the roll-up banner from left to right, revealing the giant wall banner behind it; spotlights glide over the prints; the colour Elegance Story logo stays centred and readable. + style block

## S8: Light sign switching on at night (catalogue 09) (use 1.8 s, then hold 0.6 s)
**Image prompt** (ingredient: logo 3D)
> Night exterior of a modern shopfront on a quiet street, a backlit light box sign (caisson lumineux) with the uploaded Elegance Story logo in full colour above the entrance, centred, upper-middle third, wet pavement reflecting the sign, no people, no other signs or text. + style block

**Video prompt**
> The sign is dark, then switches on with a brief flicker; the full-colour Elegance Story logo glows, its light spreading onto the wall and reflecting in the wet pavement; the camera pushes in slowly and holds. + style block

## S9: Hands present a fresh print (use 2.4 s)
**Image prompt** (ingredient: logo print)
> Top-down on a deep cyan backdrop: two hands in white cotton gloves holding up a freshly printed folded brochure toward the camera, the black cover printed with the uploaded Elegance Story logo in full colour with its tagline, centred, upper-middle third. + style block

**Video prompt**
> The gloved hands lift the brochure gently toward the camera like a gift, then unfold one panel to reveal more of the colourful ink splash; slight push-in; the colour Elegance Story logo stays readable. + style block

## S10: Signature pull-back to every product (use 4.2 s)
**Image prompt (end frame)** (ingredients: logo 3D + logo print)
> A dark premium showroom shelf lit like a gallery: neatly arranged products all carrying the uploaded Elegance Story logo in full colour: business cards, a glass bottle with a raised UV DTF logo, sticker sheets, a clear acrylic invitation, a black T-shirt and cap, a mug, a folded brochure, a small roll-up banner, a menu stand, badges, and on the back wall a large backlit sign of the 3D Elegance Story logo with its ink splash, warm spotlights from above, centred composition, no people. + style block

**Video prompt**
> Start in an extreme close-up on the colour Elegance Story logo on the glass bottle, then one smooth continuous pull-back that reveals the whole lit shelf full of Elegance Story products and the backlit logo sign behind; the camera decelerates gently into a centred, balanced final frame. + style block

*In Flow: put the S3 bottle image as the **first frame** and this shelf image as the **last frame** (Frames to Video), so the pull-back joins the two.*

## S11 hero (optional Flow version, if you want it generated rather than made in code)
**Video prompt** (ingredient: logo 3D)
> The uploaded Elegance Story 3D logo floats in a dark space; ink splashes of cyan, blue, purple, magenta, orange and yellow burst outward from behind the silver ES monogram in slow motion, thin glowing circuit lines grow from the splash edges, a beam of light sweeps across the silver letters; locked camera, the logo centred and unchanged, no extra text. + style block

My default for S11 and the end card is still to **make them in code** from your logo image, so the logo and the contacts are pixel-exact. The Flow version above is for when you want the splash to move in real 3D. Send me both and I'll pick the better one.

## Optional extras
- **Vertical story / poster still:** *"The uploaded Elegance Story logo printed in full colour on glossy black acrylic, lit by a single blue-violet UV light streak, dramatic macro, empty space below for text."* + style block
- **Transition plate:** *"Macro of thick black paper texture with a single thin glowing white line of light drawn across it, no text."* + style block. It gives the white-thread wipes a real texture.
- **Sétif touch:** *"Evening view of a busy Algerian street in Sétif with a modern shopfront whose illuminated sign shows the uploaded Elegance Story logo in full colour, warm light, no readable text except the logo, no people's faces."* + style block
