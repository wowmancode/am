precision highp float;

uniform sampler2D uTexSampler;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
varying vec2 vTexSamplingCoord;

float decodeSrgb(float x) {
    return x <= 0.04045 ? x / 12.92 : pow((x + 0.055) / 1.055, 2.4);
}

float encodeSrgb(float x) {
    x = max(x, 0.0);
    return x <= 0.0031308 ? 12.92 * x : 1.055 * pow(x, 1.0 / 2.4) - 0.055;
}

float labF(float x) {
    return x > 0.008856452 ? pow(x, 1.0 / 3.0) : 7.787037 * x + 0.137931034;
}

float labInvF(float x) {
    return x > 0.206896552 ? x * x * x : (x - 0.137931034) / 7.787037;
}

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 original = texture2D(uTexSampler, uv);
    float strength = clamp(uControl1, 0.0, 1.0);
    if (abs(uControl2) + abs(uControl3) + abs(uControl4)
        + abs(uControl5) + abs(uControl6) < 0.000001) {
        gl_FragColor = clamp(original, 0.0, 1.0);
        return;
    }
    vec3 linearRgb = vec3(decodeSrgb(original.r),
                          decodeSrgb(original.g),
                          decodeSrgb(original.b));
    vec3 xyz = vec3(dot(linearRgb, vec3(0.4124564, 0.3575761, 0.1804375)),
                    dot(linearRgb, vec3(0.2126729, 0.7151522, 0.0721750)),
                    dot(linearRgb, vec3(0.0193339, 0.1191920, 0.9503041)));
    float fx = labF(xyz.x / 0.95047);
    float fy = labF(xyz.y);
    float fz = labF(xyz.z / 1.08883);
    float lightness = (116.0 * fy - 16.0)
                      * clamp(exp2(uControl2), 0.0, 2.0);
    float axisA = 500.0 * (fx - fy) + 50.0 * uControl3;
    float axisB = 200.0 * (fy - fz) + 50.0 * uControl4;
    if (uControl5 > 0.5) lightness = 100.0 - lightness;
    float chromaScale = 1.0 - clamp(0.5 * uControl6, 0.0, 1.0);
    axisA *= chromaScale;
    axisB *= chromaScale;
    fy = (lightness + 16.0) / 116.0;
    fx = fy + axisA / 500.0;
    fz = fy - axisB / 200.0;
    xyz = vec3(0.95047 * labInvF(fx),
               labInvF(fy),
               1.08883 * labInvF(fz));
    linearRgb = vec3(dot(xyz, vec3(3.2404542, -1.5371385, -0.4985314)),
                     dot(xyz, vec3(-0.9692660, 1.8760108, 0.0415560)),
                     dot(xyz, vec3(0.0556434, -0.2040259, 1.0572252)));
    vec3 effected = vec3(encodeSrgb(linearRgb.r),
                         encodeSrgb(linearRgb.g),
                         encodeSrgb(linearRgb.b));
    gl_FragColor = clamp(vec4(mix(original.rgb, effected, strength), original.a),
                         0.0, 1.0);
}
