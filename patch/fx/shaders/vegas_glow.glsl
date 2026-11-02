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
varying vec2 vTexSamplingCoord;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    float radius = clamp((exp2(uControl2) - 1.0) / 3.0, 0.0, 1.0);
    float intensity = clamp(20.0 * (exp2(uControl3) - 1.0) / 3.0,
                            0.0, 20.0);
    float suppression = clamp(0.5 * uControl4, 0.0, 1.0);
    float widthPx = max(uWidth, 1.0);
    float heightPx = max(uHeight, 1.0);
    vec2 reach = radius * min(widthPx, heightPx)
                 / vec2(widthPx, heightPx);
    vec3 blur = 4.0 * original.rgb;
    for (int i = 0; i < 12; ++i) {
        float angle = 6.28318530718 * (float(i) + 0.5) / 12.0;
        vec2 direction = vec2(cos(angle), sin(angle)) * reach;
        blur += 2.0 * texture2D(uTexSampler,
                                clamp(uv + 0.5 * direction, 0.0, 1.0)).rgb;
        blur += texture2D(uTexSampler,
                          clamp(uv + direction, 0.0, 1.0)).rgb;
    }
    blur *= 0.025;
    float weight = clamp((dot(blur, vec3(0.3333333333)) - suppression)
                         * intensity, 0.0, 1.0);
    vec3 tint = clamp(vec3(1.0) + 0.5 * vec3(uControl5,
                                             uControl6,
                                             uControl7), 0.0, 1.0);
    vec4 effected = mix(original, vec4(tint, 1.0), weight);
    gl_FragColor = clamp(mix(original, effected,
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
