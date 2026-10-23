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
    float amount = exp2(uControl2);
    vec2 q = uv - vec2(0.5);
    float sx = q.x < 0.0 ? uControl3 : uControl4;
    float sy = q.y > 0.0 ? uControl5 : uControl6;
    q.x *= exp2(0.5 * amount * sx);
    q.y *= exp2(0.5 * amount * sy);
    vec2 sheared = vec2(q.x + 0.25 * amount * uControl7 * q.y,
                        q.y + 0.25 * amount * uControl8 * q.x);
    vec2 mapped = sheared + vec2(0.5);
    float inside = step(0.0, mapped.x) * step(mapped.x, 1.0) *
                   step(0.0, mapped.y) * step(mapped.y, 1.0);
    vec4 sampled = texture2D(uTexSampler, clamp(mapped, 0.0, 1.0));
    vec4 effected = sampled * inside;
    gl_FragColor = clamp(mix(original, effected,
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
