precision highp float;
uniform sampler2D uTexSampler;
varying vec2 vTexSamplingCoord;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    vec2 center = vec2(0.5 + 0.25 * uControl3,
                       0.5 + 0.25 * uControl4);
    vec2 delta = uv - center;
    float distanceToCenter = max(length(delta), 0.00001);
    float strength = clamp(0.12 + 0.08 * uControl2, 0.0, 0.4);
    vec2 span = delta * strength;
    if (uControl5 > 0.5) {
        span = delta / distanceToCenter * strength * 0.25;
    }
    vec4 sum = vec4(0.0);
    for (int i = 0; i < 13; ++i) {
        float t = float(i) / 12.0;
        vec2 p = clamp(uv - span * t, 0.0, 1.0);
        sum += texture2D(uTexSampler, p);
    }
    vec4 effected = sum / 13.0;
    gl_FragColor = clamp(mix(original, effected,
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
