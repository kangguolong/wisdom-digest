# Email Template Spec

This document defines the V1 email rendering requirements.

## 1. Design Goal

The digest email should feel calm, readable, and high-signal.

It should not look like a marketing newsletter.

Design principles:

- Minimal.
- Mobile-friendly.
- HTML first, plain-text fallback required.
- No tracking pixels.
- No external images in V1.
- No remote fonts in V1.
- No JavaScript.

## 2. Subject Format

Recommended subject:

```text
Wisdom Digest · {Slot Label} · {YYYY-MM-DD}
```

Examples:

```text
Wisdom Digest · Morning · 2026-06-06
Wisdom Digest · Noon · 2026-06-06
Wisdom Digest · Evening · 2026-06-06
```

## 3. Required Template Variables

```text
slot_label
send_date
recipient_name
wisdom_text
author
source
category
reflection_prompt
```

Optional variables:

```text
tags
footer_text
```

## 4. HTML Structure

Recommended structure:

```text
body
  outer container
    card
      meta label
      wisdom text
      attribution
      category/tags metadata
      reflection section
    footer
```

## 5. HTML Template Requirements

The implementation should use Jinja2 and store the template at:

```text
src/templates/digest.html
```

Template rules:

- Use inline CSS for email client compatibility.
- Escape all variables by default.
- Do not inject raw HTML from Notion fields.
- Do not include external images.
- Do not include remote CSS.
- Do not include JavaScript.
- Do not include tracking links.
- Keep width around 640px.
- Use readable font stack such as Arial, Helvetica, sans-serif.

## 6. Suggested HTML Template

```html
<!DOCTYPE html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f6f4ef;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:640px;margin:0 auto;padding:32px 20px;">
      <div style="background:#ffffff;border-radius:16px;padding:32px;border:1px solid #e8e2d8;">
        <p style="font-size:13px;letter-spacing:0.03em;color:#8a7f70;margin:0 0 16px;">
          Wisdom Digest · {{ slot_label }} · {{ send_date }}
        </p>

        <div style="font-size:24px;line-height:1.45;color:#222222;margin-bottom:24px;">
          {{ wisdom_text }}
        </div>

        {% if author or source %}
        <p style="font-size:14px;line-height:1.5;color:#6f675d;margin:0 0 24px;">
          {% if author %}— {{ author }}{% endif %}{% if source %}{% if author %}, {% endif %}{{ source }}{% endif %}
        </p>
        {% endif %}

        {% if category %}
        <p style="font-size:13px;color:#8a7f70;margin:0 0 24px;">
          Category: {{ category }}
        </p>
        {% endif %}

        <div style="border-top:1px solid #eeeeee;padding-top:20px;">
          <p style="font-size:13px;letter-spacing:0.03em;color:#8a7f70;margin:0 0 8px;">
            Reflection
          </p>
          <p style="font-size:16px;line-height:1.6;color:#333333;margin:0;">
            {{ reflection_prompt }}
          </p>
        </div>
      </div>

      <p style="text-align:center;font-size:12px;color:#aaaaaa;margin-top:20px;">
        Sent by Wisdom Digest
      </p>
    </div>
  </body>
</html>
```

## 7. Plain-Text Fallback

Every email must include a plain-text version.

Suggested format:

```text
Wisdom Digest · {Slot Label} · {YYYY-MM-DD}

{wisdom_text}

{author/source line}

Category: {category}

Reflection:
{reflection_prompt}

Sent by Wisdom Digest
```

## 8. Default Reflection Prompt

If the wisdom item does not define a custom reflection prompt, use:

```text
What does this remind me to notice, improve, or act on today?
```

## 9. Deliverability Rules

V1 should not include:

- Tracking pixels.
- Marketing-style unsubscribe links unless a real unsubscribe workflow exists.
- Large images.
- Attachments.
- Remote JavaScript.
- External CSS.

For small trusted recipients, pausing delivery is handled by setting recipient `Status` to `paused` in Notion.

## 10. Tests

Template tests should verify:

- HTML renders with required variables.
- Missing optional fields do not break rendering.
- Plain-text fallback renders.
- User-provided content is escaped.
- No external image or script tags are introduced.
