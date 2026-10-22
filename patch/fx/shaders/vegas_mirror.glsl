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

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    float turns = 0.5 * uControl2;
    float angle = turns * 6.28318530718;
    vec2 normal = vec2(-sin(angle), cos(angle));
    vec2 center = vec2(0.5 + 0.25 * uControl3,
                       0.5 + 0.25 * uControl4);
    float side = dot(uv - center, normal);
    vec2 reflected = uv;
    if (side < 0.0) {
        reflected -= 2.0 * side * normal;
    }
    float inside = step(0.0, reflected.x) * step(reflected.x, 1.0) *
                   step(0.0, reflected.y) * step(reflected.y, 1.0);
    vec3 background = clamp(vec3(uControl5, uControl6, uControl7), 0.0, 1.0);
    vec3 sampled = texture2D(uTexSampler, clamp(reflected, 0.0, 1.0)).rgb;
    vec3 effected = mix(background, sampled, inside);
    gl_FragColor = clamp(vec4(mix(original.rgb, effected,
                                   clamp(uControl1, 0.0, 1.0)), original.a),
                         0.0, 1.0);
}
