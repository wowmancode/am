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
    if (abs(uControl2) < 0.000001) {
        gl_FragColor = clamp(original, 0.0, 1.0);
        return;
    }
    vec2 center = clamp(vec2(0.5) + 0.25 * vec2(uControl3, uControl4),
                        0.0, 1.0);
    float scaleX = exp2(uControl5);
    float scaleY = uControl7 > 0.5 ? exp2(uControl6) : scaleX;
    vec2 offset = (uv - center) / vec2(scaleX, scaleY);
    float radius = length(offset) * 2.0;
    vec2 sourceUv = uv;
    if (radius < 1.0) {
        float angle = 15.0 * clamp(0.5 * uControl2, -1.0, 1.0)
                      * (1.0 - radius)
                      * (1.0 - radius);
        float cs = cos(angle);
        float sn = sin(angle);
        vec2 turned = vec2(cs * offset.x - sn * offset.y,
                           sn * offset.x + cs * offset.y);
        sourceUv = center + turned * vec2(scaleX, scaleY);
    }
    vec4 effected = texture2D(uTexSampler, clamp(sourceUv, 0.0, 1.0));
    gl_FragColor = clamp(mix(original, effected, clamp(uControl1, 0.0, 1.0)),
                         0.0, 1.0);
}
