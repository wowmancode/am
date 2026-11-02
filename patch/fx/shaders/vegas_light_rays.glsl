precision highp float;
uniform sampler2D uTexSampler;
varying vec2 vTexSamplingCoord;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;
uniform float uControl8;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    vec2 light = vec2(0.5 + 0.25 * uControl4,
                      0.5 + 0.25 * uControl5);
    vec2 radius = vec2(0.2 * exp2(uControl6),
                       0.2 * exp2(uControl7));
    float sensitivity = clamp(0.6 + 0.2 * uControl3, 0.0, 1.0);
    float threshold = 1.0 - sensitivity;
    float power = clamp(0.6 + 0.2 * uControl2, 0.0, 1.5);
    float blend = clamp(0.5 + 0.25 * uControl8, 0.0, 1.0);
    vec4 rays = vec4(0.0);
    for (int i = 0; i < 12; ++i) {
        float t = float(i) / 12.0;
        vec2 p = mix(uv, light, t);
        vec4 sampleColor = texture2D(uTexSampler, clamp(p, 0.0, 1.0));
        float level = max(max(sampleColor.r, sampleColor.g), sampleColor.b);
        float bright = max(level - threshold, 0.0) /
                       max(1.0 - threshold, 0.0001);
        float bound = clamp(1.0 - length((p - light) / radius), 0.0, 1.0);
        rays += sampleColor * bright * bound * (1.0 - 0.5 * t);
    }
    vec4 glow = clamp(rays * (power / 12.0), 0.0, 1.0);
    vec4 lit = 1.0 - (1.0 - original) * (1.0 - glow);
    vec4 effected = mix(original, lit, blend);
    gl_FragColor = clamp(mix(original, effected,
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
