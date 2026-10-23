precision highp float;

uniform sampler2D uTexSampler;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;
uniform float uControl8;
varying vec2 vTexSamplingCoord;

void main() {
    vec4 source = texture2D(uTexSampler, clamp(vTexSamplingCoord, 0.0, 1.0));
    float y = dot(source.rgb, vec3(0.299, 0.587, 0.114));
    vec2 chroma = vec2(0.492 * (source.b - y),
                       0.877 * (source.r - y));
    float center = fract(0.5 + 0.5 * uControl2);
    float width = clamp(1.0 + 0.5 * uControl3, 0.0, 1.0);
    float hue = fract(atan(chroma.y, chroma.x) / 6.28318530718 + 1.0);
    float distance = abs(fract(hue - center + 0.5) - 0.5);
    float mask = width > 0.999999 ? 1.0 : step(distance, 0.5 * width);
    float angle = 6.28318530718 * (0.5 * uControl4);
    vec2 turned = vec2(cos(angle) * chroma.x - sin(angle) * chroma.y,
                       sin(angle) * chroma.x + cos(angle) * chroma.y);
    turned *= exp2(uControl5);
    float gamma = exp2(uControl6);
    y = pow(max(y, 0.0), 1.0 / gamma) * exp2(uControl7) + 0.25 * uControl8;
    vec3 effect = vec3(y + 1.1402509212 * turned.y,
                       y - 0.3947313428 * turned.x - 0.5808091760 * turned.y,
                       y + 2.0325202942 * turned.x);
    vec3 rgb = mix(source.rgb, effect, mask);
    float adjustment = abs(uControl4) + abs(uControl5) + abs(uControl6) +
                       abs(uControl7) + abs(uControl8);
    if (adjustment < 0.000001) rgb = source.rgb;
    gl_FragColor = clamp(mix(source, vec4(rgb, source.a),
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
