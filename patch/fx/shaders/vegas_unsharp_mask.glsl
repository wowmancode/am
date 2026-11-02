precision highp float;

uniform sampler2D uTexSampler;
uniform float uWidth;
uniform float uHeight;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
varying vec2 vTexSamplingCoord;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    float amount = 2.0 * uControl2;
    float radius = clamp((exp2(3.0 * uControl3) - 1.0) / 63.0, 0.0, 1.0);
    float threshold = clamp(0.5 * uControl4, 0.0, 1.0);
    if (abs(amount) < 0.000001 || radius < 0.000001 || threshold >= 1.0) {
        gl_FragColor = clamp(original, 0.0, 1.0);
        return;
    }
    float width = max(uWidth, 1.0);
    float height = max(uHeight, 1.0);
    float radiusPixels = radius * max(width, height);
    vec2 sampleStep = 0.5 * radiusPixels / vec2(width, height);
    vec4 blur = vec4(0.0);
    for (int y = -2; y <= 2; y++) {
        float ay = abs(float(y));
        float wy = ay < 0.5 ? 6.0 : (ay < 1.5 ? 4.0 : 1.0);
        for (int x = -2; x <= 2; x++) {
            float ax = abs(float(x));
            float wx = ax < 0.5 ? 6.0 : (ax < 1.5 ? 4.0 : 1.0);
            vec2 tapUv = clamp(uv + vec2(float(x), float(y)) * sampleStep, 0.0, 1.0);
            blur += wx * wy * texture2D(uTexSampler, tapUv);
        }
    }
    blur *= 1.0 / 256.0;
    vec4 candidate = clamp(original + amount * (original - blur), 0.0, 1.0);
    vec4 candidateByte = floor(candidate * 255.0 + 0.00001);
    vec4 blurByte = floor(blur * 255.0 + 0.00001);
    float thresholdByte = floor(threshold * 255.0 + 0.5);
    vec4 delta = abs(candidateByte - blurByte);
    vec4 selected = vec4(delta.r > thresholdByte ? 1.0 : 0.0,
                         delta.g > thresholdByte ? 1.0 : 0.0,
                         delta.b > thresholdByte ? 1.0 : 0.0,
                         delta.a > thresholdByte ? 1.0 : 0.0);
    vec4 effected = mix(original, candidateByte / 255.0, selected);
    gl_FragColor = clamp(mix(original, effected, clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
