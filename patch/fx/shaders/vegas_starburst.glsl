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
uniform float uControl8;
varying vec2 vTexSamplingCoord;
const float aspect = 1.0;
const float softenEdges = 0.0;
const float reduceFlicker = 0.0;
const float effectOnly = 0.0;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    float strength = clamp(50.0 * uControl4, 0.0, 100.0) * 0.01;
    if (strength < 0.000001) {
        gl_FragColor = clamp(original, 0.0, 1.0);
        return;
    }
    float threshold = clamp(50.0 * uControl2, 0.0, 100.0) * 0.01;
    float brilliance = clamp(878.39 * exp2(uControl3), 100.0, 2000.0);
    float radius = clamp(16.63 * exp2(uControl5), 2.0, 30.0) * 0.01;
    float points = clamp(floor(4.0 + uControl6 + 0.5), 2.0, 6.0);
    float centerBurst = clamp(50.0 * uControl7, 0.0, 100.0) * 0.01;
    float orientation = (0.125 + 0.5 * uControl8) * 6.28318530718;
    float width = max(uWidth, 1.0);
    float height = max(uHeight, 1.0);
    float pixelRadius = radius * min(width, height);
    vec4 rays = vec4(0.0);
    float totalWeight = 0.0;
    for (int point = 0; point < 6; point++) {
        if (float(point) < points) {
            float angle = orientation + 6.28318530718 * float(point) / points;
            vec2 direction = vec2(cos(angle), sin(angle) * aspect);
            for (int tap = 1; tap <= 8; tap++) {
                float travel = float(tap) * 0.125;
                float weight = pow(1.0 - travel + 0.125, 1.0 + softenEdges * 3.0);
                vec2 sampleUv = clamp(uv + direction * (travel * pixelRadius) / vec2(width, height), 0.0, 1.0);
                vec4 bright = texture2D(uTexSampler, sampleUv);
                bright *= step(vec4(threshold), bright);
                rays += bright * weight;
                totalWeight += weight;
            }
        }
    }
    rays /= max(totalWeight, 0.000001);
    vec4 centerLight = original * step(vec4(threshold), original);
    rays = mix(rays, max(rays, centerLight), centerBurst);
    vec4 composite = mix(original, vec4(0.0), effectOnly) + rays * (brilliance / 878.39) * strength;
    gl_FragColor = clamp(mix(original, composite, clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
