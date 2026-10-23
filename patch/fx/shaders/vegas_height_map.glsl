precision highp float;

uniform sampler2D uTexSampler;
uniform float uWidth;
uniform float uHeight;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;
varying vec2 vTexSamplingCoord;

vec2 wrappedCoord(vec2 uv) {
    if (uv.x < 0.0 || uv.x > 1.0) uv.x = fract(uv.x);
    if (uv.y < 0.0 || uv.y > 1.0) uv.y = fract(uv.y);
    return clamp(uv, 0.0, 1.0);
}

float heightAt(vec2 uv) {
    vec3 rgb = texture2D(uTexSampler, wrappedCoord(uv)).rgb;
    float h = (rgb.r + rgb.g + rgb.b) / 3.0;
    if (uControl7 > 1.5) h = rgb.b;
    else if (uControl7 > 1.0) h = rgb.g;
    else if (uControl7 > 0.5) h = rgb.r;
    return uControl6 > 0.5 ? 1.0 - h : h;
}

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    float widthPx = max(uWidth, 1.0);
    float heightPx = max(uHeight, 1.0);
    float radiusPx = max(1.0, (31.0 * exp2(uControl5) - 1.0) * 0.5);
    vec2 stepUV = vec2(radiusPx / widthPx, radiusPx / heightPx);

    float topLeft = heightAt(uv + vec2(-stepUV.x, stepUV.y));
    float topMid = heightAt(uv + vec2(0.0, stepUV.y));
    float topRight = heightAt(uv + stepUV);
    float midLeft = heightAt(uv - vec2(stepUV.x, 0.0));
    float midRight = heightAt(uv + vec2(stepUV.x, 0.0));
    float bottomLeft = heightAt(uv - stepUV);
    float bottomMid = heightAt(uv - vec2(0.0, stepUV.y));
    float bottomRight = heightAt(uv + vec2(stepUV.x, -stepUV.y));

    vec2 slope = vec2(topRight + 2.0 * midRight + bottomRight
                      - topLeft - 2.0 * midLeft - bottomLeft,
                      topLeft + 2.0 * topMid + topRight
                      - bottomLeft - 2.0 * bottomMid - bottomRight) * 0.125;
    float amplitude = exp2(uControl2);
    float elevation = max(0.0, 1.0 + 0.5 * uControl3);
    float heightScale = exp2(uControl4);
    vec2 offset = slope * (2.0 * radiusPx * amplitude * elevation
                           * heightScale) / vec2(widthPx, heightPx);
    vec4 displaced = texture2D(uTexSampler, wrappedCoord(uv + offset));
    gl_FragColor = clamp(mix(original, displaced,
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
