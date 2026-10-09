#!/usr/bin/env python3
"""Generate paired IN/OUT AMV transitions as editable native shader effects."""

from pathlib import Path
from xml.sax.saxutils import escape


# Each look is one effect that combines its visual components. The common
# parameters remain editable in Alight Motion's normal effect settings.
LOOKS = {
    "beat-zoom": ("Beat Zoom", "Punch zoom with a chromatic rim", """
        vec2 p = uv - 0.5;
        vec2 z = p / (1.0 + 0.45 * k) + 0.5;
        vec2 split = normalize(p + vec2(0.0001)) * 0.012 * k;
        fx = texture2D(inputImg.texture, clamp(z, 0.0, 1.0));
        fx.r = texture2D(inputImg.texture, clamp(z + split, 0.0, 1.0)).r;
        fx.b = texture2D(inputImg.texture, clamp(z - split, 0.0, 1.0)).b;
    """),
    "whip-pan": ("Whip Pan", "Fast directional sweep with sampled motion blur", """
        vec2 shift = dir * k * 0.65;
        fx = vec4(0.0);
        for (int i = 0; i < 7; i++) {
            float x = float(i) / 6.0;
            fx += texture2D(inputImg.texture, clamp(uv + shift * (1.0 - x), 0.0, 1.0)) / 7.0;
        }
    """),
    "rgb-split": ("RGB Split", "Chromatic separation and high contrast", """
        vec2 offset = dir * 0.055 * k;
        fx.r = texture2D(inputImg.texture, clamp(uv + offset, 0.0, 1.0)).r;
        fx.b = texture2D(inputImg.texture, clamp(uv - offset, 0.0, 1.0)).b;
        fx.rgb = clamp((fx.rgb - 0.5 * fx.a) * (1.0 + 0.45 * k) + 0.5 * fx.a, 0.0, fx.a);
    """),
    "glitch-tear": ("Glitch Tear", "Broken scanlines, jitter, and color shift", """
        float row = floor(uv.y * (24.0 + 30.0 * speed));
        float tick = floor(acTime * (12.0 + 20.0 * speed));
        float gate = step(0.72, hash(vec2(row, tick)));
        vec2 offset = vec2((hash(vec2(row, tick + 9.0)) - 0.5) * 0.18 * k * gate, 0.0);
        vec2 pos = clamp(uv + offset, 0.0, 1.0);
        fx = texture2D(inputImg.texture, pos);
        fx.r = texture2D(inputImg.texture, clamp(pos + vec2(0.014 * k, 0.0), 0.0, 1.0)).r;
        fx.b = texture2D(inputImg.texture, clamp(pos - vec2(0.014 * k, 0.0), 0.0, 1.0)).b;
    """),
    "spin-burst": ("Spin Burst", "Rotating punch zoom with trailing samples", """
        vec2 p = uv - 0.5;
        fx = vec4(0.0);
        for (int i = 0; i < 5; i++) {
            float phase = float(i) / 4.0;
            float a = k * (0.65 + phase * 0.25);
            mat2 turn = mat2(cos(a), -sin(a), sin(a), cos(a));
            vec2 pos = turn * p / (1.0 + k * (0.3 + phase * 0.12)) + 0.5;
            fx += texture2D(inputImg.texture, clamp(pos, 0.0, 1.0)) / 5.0;
        }
    """),
    "shake-impact": ("Shake Impact", "Camera hit with chromatic offset", """
        float tick = floor(acTime * (18.0 + speed * 14.0));
        vec2 jitter = (vec2(hash(vec2(tick, 1.0)), hash(vec2(tick, 2.0))) - 0.5) * 0.11 * k;
        vec2 pos = clamp(uv + jitter, 0.0, 1.0);
        fx = texture2D(inputImg.texture, pos);
        fx.r = texture2D(inputImg.texture, clamp(pos + jitter * 0.35, 0.0, 1.0)).r;
        fx.b = texture2D(inputImg.texture, clamp(pos - jitter * 0.35, 0.0, 1.0)).b;
    """),
    "fisheye-punch": ("Fisheye Punch", "Lens bulge with edge color fringing", """
        vec2 p = uv - 0.5;
        float r = length(p);
        float warp = 1.0 + k * 1.7 * (1.0 - smoothstep(0.0, 0.7, r));
        vec2 pos = clamp(p / warp + 0.5, 0.0, 1.0);
        vec2 split = p * 0.025 * k;
        fx = texture2D(inputImg.texture, pos);
        fx.r = texture2D(inputImg.texture, clamp(pos + split, 0.0, 1.0)).r;
        fx.b = texture2D(inputImg.texture, clamp(pos - split, 0.0, 1.0)).b;
    """),
    "pixel-burst": ("Pixel Burst", "Mosaic blocks with random displacement", """
        float blockSize = 1.0 + floor(55.0 * k);
        vec2 blocks = max(acScreenSize / blockSize, vec2(1.0));
        vec2 cell = floor(uv * blocks);
        vec2 jump = (vec2(hash(cell + floor(acTime * speed * 15.0)),
                          hash(cell + floor(acTime * speed * 15.0) + 7.0)) - 0.5) * 0.045 * k;
        vec2 pos = clamp((cell + 0.5) / blocks + jump, 0.0, 1.0);
        fx = texture2D(inputImg.texture, pos);
    """),
    "mirror-swipe": ("Mirror Swipe", "Sliding mirrored slices", """
        float bands = 4.0 + floor(speed * 4.0);
        float row = floor(uv.y * bands);
        vec2 pos = uv;
        pos.x += (mod(row, 2.0) * 2.0 - 1.0) * k * 0.36;
        if (mod(row, 2.0) > 0.5) pos.x = 1.0 - pos.x;
        vec4 mirrored = texture2D(inputImg.texture, clamp(pos, 0.0, 1.0));
        fx = mix(src, mirrored, clamp(k, 0.0, 1.0));
    """),
    "radial-blur": ("Radial Blur", "Speed lines from the center", """
        vec2 p = uv - 0.5;
        fx = vec4(0.0);
        for (int i = 0; i < 9; i++) {
            float x = float(i) / 8.0;
            fx += texture2D(inputImg.texture, clamp(0.5 + p * (1.0 - x * 0.55 * k), 0.0, 1.0)) / 9.0;
        }
    """),
    "flash-cut": ("Flash Cut", "Bright white beat hit with crunchy contrast", """
        float hit = clamp(k, 0.0, 1.0);
        fx.rgb = clamp((src.rgb - 0.5 * src.a) * (1.0 + hit * 1.5) + 0.5 * src.a, 0.0, src.a);
        fx.rgb = mix(fx.rgb, vec3(src.a), hit * 0.8);
    """),
    "vortex": ("Vortex Twist", "Swirl and zoom into the cut", """
        vec2 p = uv - 0.5;
        float r = length(p);
        float a = (1.0 - smoothstep(0.0, 0.72, r)) * k * 3.2;
        mat2 turn = mat2(cos(a), -sin(a), sin(a), cos(a));
        vec2 pos = clamp(0.5 + turn * p / (1.0 + 0.22 * k), 0.0, 1.0);
        fx = texture2D(inputImg.texture, pos);
    """),
}

SHADER = """
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void main() {
    vec2 uv = acScreenNorm;
{direction_vector}
    float edge = mode == 0 ? acTime - acStartTime : acEndTime - acTime;
    float pulse = 1.0 - smoothstep(0.0, 1.0, clamp(edge / max(duration, 0.01), 0.0, 1.0));
    float k = pulse * strength;
    vec4 src = texture2D(inputImg.texture, uv);
    vec4 fx = src;
{look}
    fx.rgb = mix(fx.rgb, vec3(fx.a), clamp(flash * pulse, 0.0, 1.0));
    fx.a *= 1.0 - clamp(fade * pulse, 0.0, 1.0);
    gl_FragColor = fx;
}
"""

TEMPLATE = """<?xml version='1.0' encoding='UTF-8' ?>
<effect id="com.wowmancode.transitions.{slug}.{direction}" name="@string/name" desc="@string/desc" category="distort" tags="custom,transition,amv,distort,color">
    <strings><locale lang="en">
        <string name="name">AMV {name} {title}</string>
        <string name="desc">{desc}. Starts at the {edge} of the layer.</string>
        <string name="mode">Edge</string><string name="in">In</string><string name="out">Out</string>
        <string name="duration">Duration (seconds)</string>
        <string name="strength">Strength</string><string name="speed">Motion Speed</string>
        <string name="angle">Direction</string><string name="flash">Flash</string><string name="fade">Fade to transparent</string>
    </locale></strings>
    <params>
        <texture id="inputImg" srcType="content" />
        <selector id="mode" default="{mode}" style="dropdown" label="@string/mode">
            <choice label="@string/in" value="0" /><choice label="@string/out" value="1" />
        </selector>
        <spinner id="duration" default="0.35" min="0.08" max="2.0" step="0.01" label="@string/duration" />
        <spinner id="strength" default="1.0" min="0.0" max="2.0" step="0.01" label="@string/strength" />
{extra_params}
        <spinner id="flash" default="0.0" min="0.0" max="1.0" step="0.01" label="@string/flash" type="percent" />
        <spinner id="fade" default="0.0" min="0.0" max="1.0" step="0.01" label="@string/fade" type="percent" />
    </params>
    <shader type="fragment" precision="high"><![CDATA[{shader}    ]]></shader>
</effect>
"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for slug, (name, desc, look) in LOOKS.items():
        uses_angle = "dir *" in look
        uses_speed = "speed" in look
        extras = []
        if uses_speed:
            extras.append('        <spinner id="speed" default="1.0" min="0.0" max="4.0" step="0.05" label="@string/speed" />')
        if uses_angle:
            extras.append('        <spinner id="angle" default="0.0" min="-180.0" max="180.0" step="1.0" label="@string/angle" />')
        shader = SHADER.replace("{look}", look).replace(
            "{direction_vector}",
            "    vec2 dir = vec2(cos(radians(angle)), sin(radians(angle)));" if uses_angle else "",
        )
        for direction, mode, edge in (("in", 0, "beginning"), ("out", 1, "end")):
            xml = TEMPLATE.format(
                slug=slug.replace("-", ""), direction=direction,
                name=escape(name), desc=escape(desc), title=direction.title(),
                edge=edge, mode=mode, shader=shader, extra_params="\n".join(extras),
            )
            (args.output / f"amv-{slug}-{direction}.xml").write_text(xml)
    print(f"Generated {len(LOOKS) * 2} configurable AMV transitions")


if __name__ == "__main__":
    main()
