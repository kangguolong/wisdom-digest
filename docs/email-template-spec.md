# Email Template Spec

This document defines the V1 email rendering requirements.

## 1. Design Goal

The digest email should feel calm, readable, and high-signal.

It should not look like a marketing newsletter.

Design principles:

- Minimal.
- Editorial calm: refined reading-card layout, not a product newsletter.
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
      header with brand and slot/date
      short accent divider
      wisdom text as the visual focus
      attribution
      category/tags metadata chips
      reflection section
    footer
```

## 5. HTML Template Requirements

The implementation should use Jinja2 and store the template at:

```text
src/wisdom_digest/templates/digest.html
```

Template rules:

- Use inline CSS for email client compatibility.
- Escape all variables by default.
- Load the template from the `wisdom_digest/templates` package path.
- Do not inject raw HTML from Notion fields.
- Do not include external images.
- Do not include remote CSS.
- Do not include JavaScript.
- Do not include tracking links.
- Keep width around 640px.
- Use readable font stack such as Arial, Helvetica, sans-serif.
- Use email-safe table layout where needed for horizontal header alignment.
- Render category and tags as subtle inline chips when present.

## 6. Suggested HTML Template

```html
<!DOCTYPE html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f7f5f0;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:620px;margin:0 auto;padding:28px 18px;">
      <div style="background:#fffdf8;border-radius:14px;padding:34px 34px 30px;border:1px solid #e6dfd3;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <tr>
            <td style="font-size:13px;line-height:1.4;font-weight:700;color:#7b7165;margin:0;">
              Wisdom Digest
            </td>
            <td align="right" style="font-size:13px;line-height:1.4;color:#9a9185;margin:0;">
              {{ slot_label }} · {{ send_date }}
            </td>
          </tr>
        </table>

        <div style="width:28px;height:2px;background:#b89b68;margin:28px 0 26px;font-size:0;line-height:0;">
          &nbsp;
        </div>

        <div style="font-size:28px;line-height:1.38;color:#252321;font-weight:600;margin:0;">
          {{ wisdom_text }}
        </div>

        {% if author or source %}
        <p style="font-size:14px;line-height:1.6;color:#776f66;margin:22px 0 0;">
          {% if author %}- {{ author }}{% endif %}{% if source %}{% if author %}, {% endif %}{{ source }}{% endif %}
        </p>
        {% endif %}

        {% if category or tags %}
        <div style="margin-top:24px;">
          {% if category %}
          <span style="display:inline-block;font-size:12px;line-height:1.3;color:#7c7164;background:#f1ece3;border:1px solid #e4dccf;border-radius:999px;padding:5px 9px;margin:0 6px 6px 0;">
            {{ category }}
          </span>
          {% endif %}
          {% for tag in tags %}
          <span style="display:inline-block;font-size:12px;line-height:1.3;color:#7c7164;background:#f1ece3;border:1px solid #e4dccf;border-radius:999px;padding:5px 9px;margin:0 6px 6px 0;">
            {{ tag }}
          </span>
          {% endfor %}
        </div>
        {% endif %}

        <div style="border-top:1px solid #ebe5dc;margin-top:30px;padding-top:24px;">
          <p style="font-size:12px;line-height:1.4;letter-spacing:0.08em;text-transform:uppercase;color:#9a9185;margin:0 0 10px;">
            Reflection
          </p>
          <p style="font-size:18px;line-height:1.55;color:#2f2d2a;margin:0;">
            {{ reflection_prompt }}
          </p>
        </div>
      </div>

      <p style="text-align:center;font-size:12px;line-height:1.5;color:#aaa39a;margin:18px 0 0;">
        {{ footer_text }}
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
- Category and tags render as subtle metadata chips.
- No external image or script tags are introduced.
