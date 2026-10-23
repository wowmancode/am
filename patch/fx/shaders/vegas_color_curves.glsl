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

float spline(float a, float b, float c, float d, float t) {
    float t2 = t * t;
    float t3 = t2 * t;
    return 0.5 * (2.0 * b + (c - a) * t +
                  (2.0 * a - 5.0 * b + 4.0 * c - d) * t2 +
                  (3.0 * b - a - 3.0 * c + d) * t3);
}

float applyCurve(float inputValue, float shadow, float middle, float highlight) {
    float x = clamp(inputValue, 0.0, 1.0) * 4.0;
    if (x < 1.0) return spline(-shadow, 0.0, shadow, middle, x);
    if (x < 2.0) return spline(0.0, shadow, middle, highlight, x - 1.0);
    if (x < 3.0) return spline(shadow, middle, highlight, 1.0, x - 2.0);
    return spline(middle, highlight, 1.0, 2.0 - highlight, x - 3.0);
}

void main() {
    vec4 source = texture2D(uTexSampler, clamp(vTexSamplingCoord, 0.0, 1.0));
    float neutral = abs(uControl2) + abs(uControl3) + abs(uControl4) +
                    abs(uControl5) + abs(uControl6) + abs(uControl7) +
                    abs(uControl8);
    if (neutral < 0.000001) {
        gl_FragColor = clamp(source, 0.0, 1.0);
        return;
    }
    float masterShadow = 0.25 + 0.125 * (uControl2 - uControl8);
    float masterMiddle = 0.5 + 0.125 * uControl3;
    float masterHighlight = 0.75 + 0.125 * (uControl4 + uControl8);
    vec3 master = vec3(applyCurve(source.r, masterShadow, masterMiddle, masterHighlight),
                       applyCurve(source.g, masterShadow, masterMiddle, masterHighlight),
                       applyCurve(source.b, masterShadow, masterMiddle, masterHighlight));
    vec3 effect = vec3(applyCurve(master.r, 0.25, 0.5 + 0.125 * uControl5, 0.75),
                       applyCurve(master.g, 0.25, 0.5 + 0.125 * uControl6, 0.75),
                       applyCurve(master.b, 0.25, 0.5 + 0.125 * uControl7, 0.75));
    gl_FragColor = clamp(mix(source, vec4(effect, source.a),
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
