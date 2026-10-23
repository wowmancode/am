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
    float verticalCycles = 5.4 * exp2(uControl2);
    float horizontalCycles = 5.4 * exp2(uControl3);
    float verticalAmplitude = 0.05 * exp2(uControl4);
    float horizontalAmplitude = 0.05 * exp2(uControl5);
    float verticalPhase = 0.5 * uControl6;
    float horizontalPhase = 0.5 * uControl7;
    vec2 sourceUv = uv + vec2(
        horizontalAmplitude * sin(6.28318530718 * (horizontalCycles * uv.y + horizontalPhase)),
        verticalAmplitude * sin(6.28318530718 * (verticalCycles * uv.x + verticalPhase))
    );
    vec4 warped = texture2D(uTexSampler, clamp(sourceUv, 0.0, 1.0));
    gl_FragColor = clamp(mix(original, warped, clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
