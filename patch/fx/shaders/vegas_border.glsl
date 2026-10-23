precision highp float;
uniform sampler2D uTexSampler;
varying vec2 vTexSamplingCoord;
uniform float uWidth;
uniform float uHeight;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 source = texture2D(uTexSampler, uv);
    vec2 dimensions = vec2(max(uWidth, 1.0), max(uHeight, 1.0));
    float size = 0.05 * exp2(uControl2);
    vec2 inset = min(vec2(0.49),
                     vec2(size * max(dimensions.x, dimensions.y) * 0.5) / dimensions);
    vec2 inner = max(vec2(1.0) - 2.0 * inset, vec2(0.001));
    vec2 mapped = (uv - inset) / inner;
    float inside = step(0.0, mapped.x) * step(mapped.x, 1.0) *
                   step(0.0, mapped.y) * step(mapped.y, 1.0);
    vec4 borderColor = vec4(clamp(vec3(1.0 + 0.5 * uControl4,
                                        1.0 + 0.5 * uControl5,
                                        1.0 + 0.5 * uControl6), 0.0, 1.0), 1.0);
    if (uControl7 > 0.5) {
        float angle = 3.14159265359 * uControl3;
        vec2 light = vec2(cos(angle), sin(angle));
        vec2 edge = min(uv, 1.0 - uv) / max(inset, vec2(0.0001));
        vec2 normal = vec2(uv.x < 0.5 ? -1.0 : 1.0,
                           uv.y < 0.5 ? -1.0 : 1.0);
        float shade = 0.7 + 0.3 * dot(normal, light) * (1.0 - min(edge.x, edge.y));
        borderColor.rgb *= clamp(shade, 0.0, 1.0);
    }
    vec4 scaled = texture2D(uTexSampler, clamp(mapped, 0.0, 1.0));
    vec4 effected = mix(borderColor, scaled, inside);
    gl_FragColor = clamp(mix(source, effected, clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
