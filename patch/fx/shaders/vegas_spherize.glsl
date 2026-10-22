precision highp float;

uniform sampler2D uTexSampler;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;
varying vec2 vTexSamplingCoord;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    float amount = clamp(1.0 + uControl2, -1.0, 1.0);
    vec2 center = vec2(0.5) + 0.5 * vec2(uControl3, uControl4);
    float scaleX = min(exp2(uControl5), 1.0);
    float scaleY = uControl7 > 0.5 ? min(exp2(uControl6), 1.0) : scaleX;
    vec2 offset = uv - center;
    float radius = length(2.0 * offset / (vec2(scaleX, scaleY) + vec2(0.0001)));
    vec2 sourceUv = uv;
    if (radius < 1.0) {
        float factor = 1.0 - 0.8 * amount * cos(1.57079632679 * radius);
        sourceUv = center + offset * factor;
    }
    vec4 warped = texture2D(uTexSampler, clamp(sourceUv, 0.0, 1.0));
    gl_FragColor = clamp(mix(original, warped, clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
